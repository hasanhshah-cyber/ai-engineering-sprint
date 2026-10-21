#!/usr/bin/env python3
"""Day 8: fully on-prem RAG. Your documents, retrieved locally, answered by a
local model. No API key. No cloud call. Nothing leaves the machine.

This is Day 1 (retrieval chatbot) plus Day 6 (local ONNX model) joined together,
with the Claude call deleted. Day 1 retrieved with TF-IDF in plain numpy, which
never needed an API key. Day 6 ran Xenova/flan-t5-small through ONNX Runtime
directly, also with no API key. Day 8 wires the two together: retrieve the
relevant passages, hand them to the local model as context, print the answer
with receipts showing which document each fact came from.

Usage (on Hasan's Mac, where the Day 6 model is already downloaded):
    python3 -m venv venv && source venv/bin/activate
    pip install --only-binary:all: -r requirements.txt
    python onprem_rag.py docs "How does the data stay secure?"

    python onprem_rag.py docs "your question" --retrieve-only   # retrieval only, no model

If the top retrieved passage scores below the threshold, the script says the
documents do not contain an answer instead of letting the model guess. That
refusal is part of the design: a grounded answer or an honest no.

Model note: PyTorch no longer ships wheels for Intel Macs, and optimum depends
on torch, so this script talks to ONNX Runtime directly with plain numpy
arrays, exactly like Day 6. Same model, same approach, no heavy engine.
"""

import os
import re
import sys
import pickle
from pathlib import Path

import numpy as np

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 3
MIN_SCORE = 0.05  # below this, the docs do not contain an answer
CACHE = Path(__file__).parent / ".rag_cache.pkl"
MODEL_NAME = "Xenova/flan-t5-small"
ALLOW_PATTERNS = [
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


# --- 1. CHUNK (from Day 1) --------------------------------------------------
def chunk_text(text: str, source: str):
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append({"text": text[start:end], "source": source})
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def load_docs(docs_dir: str):
    chunks = []
    for p in sorted(Path(docs_dir).glob("**/*.md")):
        text = p.read_text(errors="ignore")
        if len(text) < 200:
            continue
        chunks.extend(chunk_text(text, p.name))
    return chunks


# --- 2. RETRIEVE (from Day 1: TF-IDF in plain numpy, no API, no model) ------
# Stopwords are dropped so common words (what, is, the) cannot fake a match.
# Without this, an unrelated question still scores against every document.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "do", "does", "did", "done", "can", "could", "will", "would", "should",
    "and", "or", "but", "if", "then", "than", "of", "to", "in", "on", "at",
    "by", "for", "with", "from", "as", "it", "its", "this", "that", "these",
    "those", "i", "you", "he", "she", "we", "they", "my", "your", "his",
    "her", "our", "their", "not", "no", "so", "very", "just", "me", "him",
}


def tokenize(s: str):
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


def embed_query(q: str, vocab, idf):
    toks = tokenize(q)
    v = np.zeros(len(vocab))
    tf = {}
    for t in toks:
        tf[t] = tf.get(t, 0) + 1
    for t, c in tf.items():
        if t in vocab:
            v[vocab[t]] = (c / len(toks)) * idf[vocab[t]]
    return v / (np.linalg.norm(v) + 1e-9)


def retrieve(question, chunks, mat, vocab, idf, k=TOP_K):
    qv = embed_query(question, vocab, idf)
    scores = mat @ qv
    top = np.argsort(scores)[::-1][:k]
    return [(chunks[i], float(scores[i])) for i in top]


# --- 3. GENERATE (from Day 6: local model, ONNX Runtime, no torch) ----------
def load_model():
    """Imports are lazy so retrieval works without the model installed."""
    import onnxruntime as ort
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer

    if os.path.isdir(MODEL_NAME):
        model_dir = MODEL_NAME
    else:
        model_dir = snapshot_download(MODEL_NAME, allow_patterns=ALLOW_PATTERNS)
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    encoder = ort.InferenceSession(
        os.path.join(model_dir, "onnx", "encoder_model.onnx"),
        providers=["CPUExecutionProvider"],
    )
    decoder = ort.InferenceSession(
        os.path.join(model_dir, "onnx", "decoder_model.onnx"),
        providers=["CPUExecutionProvider"],
    )
    return tokenizer, encoder, decoder


def run_local(tokenizer, encoder, decoder, prompt, max_length=80):
    """Greedy decoding through the local model, exactly like Day 6."""
    inputs = tokenizer(prompt, return_tensors="np")
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    encoder_hidden = encoder.run(
        None,
        {"input_ids": input_ids, "attention_mask": attention_mask},
    )[0]
    start_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    eos_id = tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 1
    decoder_ids = np.array([[start_id]], dtype=np.int64)
    for _ in range(max_length):
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
    return tokenizer.decode(decoder_ids[0], skip_special_tokens=True)


# --- main -------------------------------------------------------------------
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    retrieve_only = "--retrieve-only" in sys.argv
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    docs_dir, question = args[0], " ".join(args[1:])

    if CACHE.exists():
        chunks, mat, vocab, idf = pickle.loads(CACHE.read_bytes())
        print(f"(loaded {len(chunks)} cached chunks)")
    else:
        print("Indexing docs...", end=" ", flush=True)
        chunks = load_docs(docs_dir)
        mat, vocab, idf = tfidf_vectors(chunks)
        CACHE.write_bytes(pickle.dumps((chunks, mat, vocab, idf)))
        print(f"done: {len(chunks)} chunks.")

    hits = retrieve(question, chunks, mat, vocab, idf)
    print("\nRetrieved:")
    for (c, s) in hits:
        print(f"  [{s:.2f}] {c['source']}: {c['text'][:80].strip()}...")

    if hits[0][1] < MIN_SCORE:
        print("\nThe documents do not contain an answer to that question.")
        return
    if retrieve_only:
        return

    print("\nLoading local model (no API key, no cloud)...")
    tokenizer, encoder, decoder = load_model()
    context = " ".join(c["text"] for c, _ in hits)
    prompt = "question: " + question + " context: " + context
    answer = run_local(tokenizer, encoder, decoder, prompt)
    print("\nLocal model says:\n")
    print(answer)
    print("\nSources:")
    for (c, s) in hits:
        print(f"  - {c['source']}")


if __name__ == "__main__":
    main()
