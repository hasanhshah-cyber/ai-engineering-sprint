#!/usr/bin/env python3
"""Day 10: MCP server for the Day 8 on-prem RAG.

MCP is the Model Context Protocol: a standard way for an AI app to call
tools over stdio, with JSON-RPC messages, one per line. This server
exposes the Day 8 system as two tools, so any MCP client can use it
instead of only the command line script:

  - retrieve_docs: TF-IDF retrieval over the local docs, with scores,
    sources, and an honest refusal when nothing matches.
  - ask_docs: retrieve first, then answer with the Day 6 local model
    when it is available. If the model packages are not installed in
    this environment, it returns the retrieved passages instead of
    pretending to generate an answer.

No API key, no cloud, no SDK dependency. The protocol is implemented
here in plain Python so the whole server is readable and runnable on
an Intel Mac with only numpy. Logs go to stderr only: stdout is the
protocol, and anything else on stdout would break the client.

Usage:
    python mcp_server.py            # serves docs/ in this folder
    python mcp_server.py docs       # explicit docs folder

Connect from an MCP client (for example Claude Desktop) with a stdio
server command of: python /path/to/mcp_server.py, run from this folder
so it finds docs/. See README.md for the full config snippet.
"""

import json
import re
import sys
from pathlib import Path

import numpy as np

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
MIN_SCORE = 0.05  # same threshold as Day 8 and Day 9: below this, refuse

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "do", "does", "did", "done", "can", "could", "will", "would", "should",
    "and", "or", "but", "if", "then", "than", "of", "to", "in", "on", "at",
    "by", "for", "with", "from", "as", "it", "its", "this", "that", "these",
    "those", "i", "you", "he", "she", "we", "they", "my", "your", "his",
    "her", "our", "their", "not", "no", "so", "very", "just", "me", "him",
}


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def chunk_text(text, source):
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append({"text": text[start:end], "source": source})
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def load_docs(docs_dir):
    chunks = []
    for p in sorted(Path(docs_dir).glob("**/*.md")):
        text = p.read_text(errors="ignore")
        if len(text) < 200:
            continue
        chunks.extend(chunk_text(text, p.name))
    return chunks


def tokenize(s):
    return [t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in STOPWORDS]


def tfidf_vectors(chunks):
    docs = [tokenize(c["text"]) for c in chunks]
    vocab = {}
    for toks in docs:
        for t in set(toks):
            if t not in vocab:
                vocab[t] = len(vocab)
    n = len(docs)
    df = np.zeros(len(vocab))
    for toks in docs:
        for t in set(toks):
            df[vocab[t]] += 1
    idf = np.log((1 + n) / (1 + df)) + 1.0
    mat = np.zeros((n, len(vocab)))
    for i, toks in enumerate(docs):
        tf = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        for t, c in tf.items():
            if t in vocab:
                mat[i, vocab[t]] = (c / len(toks)) * idf[vocab[t]]
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9
    return mat / norms, vocab, idf


def embed_query(q, vocab, idf):
    toks = tokenize(q)
    v = np.zeros(len(vocab))
    tf = {}
    for t in toks:
        tf[t] = tf.get(t, 0) + 1
    for t, c in tf.items():
        if t in vocab:
            v[vocab[t]] = (c / len(toks)) * idf[vocab[t]]
    return v / (np.linalg.norm(v) + 1e-9)


class RagStore:
    def __init__(self, docs_dir):
        self.chunks = load_docs(docs_dir)
        self.mat, self.vocab, self.idf = tfidf_vectors(self.chunks)

    def retrieve(self, question, k=3):
        qv = embed_query(question, self.vocab, self.idf)
        scores = self.mat @ qv
        top = np.argsort(scores)[::-1][:k]
        hits = [
            {
                "source": self.chunks[i]["source"],
                "score": round(float(scores[i]), 2),
                "text": self.chunks[i]["text"].strip(),
            }
            for i in top
        ]
        refused = not hits or hits[0]["score"] < MIN_SCORE
        return {"question": question, "refused": refused, "hits": hits}


TOOLS = [
    {
        "name": "retrieve_docs",
        "description": "Retrieve the most relevant passages from the local on-prem docs for a question, with scores and sources. Refuses honestly when nothing matches.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "top_k": {"type": "integer", "default": 3},
            },
            "required": ["question"],
        },
    },
    {
        "name": "ask_docs",
        "description": "Answer a question from the local docs. Retrieves passages first, refuses when nothing matches, and generates with the local ONNX model when it is available. Otherwise returns the retrieved passages.",
        "inputSchema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
]


def call_tool(store, name, args):
    if name == "retrieve_docs":
        result = store.retrieve(args["question"], int(args.get("top_k", 3)))
        return result
    if name == "ask_docs":
        result = store.retrieve(args["question"], 3)
        if result["refused"]:
            result["answer"] = "The documents do not contain an answer to that question."
            return result
        try:
            # Lazy import: retrieval works without the model installed.
            # On Hasan's Mac the Day 6 model is already downloaded, so
            # this path is the one that runs there. Generation mirrors
            # Day 8 exactly: ONNX Runtime, greedy decoding, no torch.
            import os

            import onnxruntime as ort
            from huggingface_hub import snapshot_download
            from transformers import AutoTokenizer

            model_name = "Xenova/flan-t5-small"
            allow = [
                "config.json",
                "generation_config.json",
                "onnx/encoder_model.onnx",
                "onnx/decoder_model.onnx",
                "onnx/decoder_with_past_model.onnx",
                "special_tokens_map.json",
                "spiece.model",
                "tokenizer.json",
                "tokenizer_config.json",
            ]
            model_dir = (
                model_name
                if os.path.isdir(model_name)
                else snapshot_download(model_name, allow_patterns=allow)
            )
            tokenizer = AutoTokenizer.from_pretrained(model_dir)
            encoder = ort.InferenceSession(
                os.path.join(model_dir, "onnx", "encoder_model.onnx"),
                providers=["CPUExecutionProvider"],
            )
            decoder = ort.InferenceSession(
                os.path.join(model_dir, "onnx", "decoder_model.onnx"),
                providers=["CPUExecutionProvider"],
            )
            context = " ".join(h["text"] for h in result["hits"])
            prompt = "question: " + args["question"] + " context: " + context
            inputs = tokenizer(prompt, return_tensors="np")
            input_ids = inputs["input_ids"]
            attention_mask = inputs["attention_mask"]
            encoder_hidden = encoder.run(
                None,
                {"input_ids": input_ids, "attention_mask": attention_mask},
            )[0]
            start_id = (
                tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
            )
            eos_id = tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 1
            decoder_ids = np.array([[start_id]], dtype=np.int64)
            for _ in range(80):
                logits = decoder.run(
                    None,
                    {
                        "input_ids": decoder_ids,
                        "encoder_attention_mask": attention_mask,
                        "encoder_hidden_states": encoder_hidden,
                    },
                )[0]
                next_id = int(np.argmax(logits[0, -1]))
                if next_id == eos_id:
                    break
                decoder_ids = np.concatenate(
                    [decoder_ids, np.array([[next_id]], dtype=np.int64)], axis=1
                )
            result["answer"] = tokenizer.decode(
                decoder_ids[0], skip_special_tokens=True
            )
        except Exception:
            result["answer"] = (
                "Local model not available in this environment, so no "
                "generated answer is claimed. Use the retrieved passages above."
            )
        return result
    raise ValueError(f"unknown tool: {name}")


def main():
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"
    store = RagStore(docs_dir)
    log(f"onprem-rag MCP server ready: {len(store.chunks)} chunks from {docs_dir}")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = msg.get("method", "")
        msg_id = msg.get("id")

        # Notifications have no id and get no response.
        if method.startswith("notifications/"):
            continue

        if method == "initialize":
            result = {
                "protocolVersion": msg.get("params", {}).get(
                    "protocolVersion", "2024-11-05"
                ),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "onprem-rag", "version": "1.0.0"},
            }
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = msg.get("params", {})
            try:
                payload = call_tool(store, params.get("name"), params.get("arguments", {}))
                result = {
                    "content": [
                        {"type": "text", "text": json.dumps(payload, indent=2)}
                    ]
                }
            except Exception as e:
                result = {
                    "content": [{"type": "text", "text": f"error: {e}"}],
                    "isError": True,
                }
        elif method == "ping":
            result = {}
        else:
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"method not found: {method}"},
            }
            print(json.dumps(response), flush=True)
            continue

        response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
