#!/usr/bin/env python3
"""
ask-my-docs: a tiny RAG chatbot over your own documents.
Day-one build: chunk -> TF-IDF vectors -> cosine retrieval -> Claude answers.

Usage:
    pip install anthropic numpy
    export ANTHROPIC_API_KEY=sk-ant-...
    python rag.py /path/to/docs "your question"

Week-2 upgrade path: swap tfidf_vectors() for a real embedding model
(sentence-transformers) and watch retrieval get smarter. That's a whole
second LinkedIn post.
"""
import os
import re
import sys
import math
import pickle
from pathlib import Path

import numpy as np

CHUNK_SIZE = 600      # characters per chunk
CHUNK_OVERLAP = 100
TOP_K = 3            # chunks retrieved per question
CACHE = Path(__file__).parent / ".rag_cache.pkl"


# --- 1. CHUNK ---------------------------------------------------------------
def chunk_text(text: str, source: str):
    """Split text into overlapping chunks, tagged with their source file."""
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
        # skip tiny files
        if len(text) < 200:
            continue
        chunks.extend(chunk_text(text, p.name))
    return chunks


# --- 2. EMBED (TF-IDF; swap me for a real model later) -----------------------
def tokenize(s: str):
    return re.findall(r"[a-z0-9]+", s.lower())


def tfidf_vectors(chunks):
    """Return (matrix, vocab, idf): one TF-IDF vector per chunk."""
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
    # L2-normalize rows so cosine = dot product
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
    n = np.linalg.norm(v) + 1e-9
    return v / n


# --- 3. RETRIEVE ------------------------------------------------------------
def retrieve(question, chunks, mat, vocab, idf, k=TOP_K):
    qv = embed_query(question, vocab, idf)
    scores = mat @ qv
    top = np.argsort(scores)[::-1][:k]
    return [(chunks[i], float(scores[i])) for i in top]


# --- 4. GENERATE ------------------------------------------------------------
def ask_claude(question, context_chunks):
    import anthropic
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    context = "\n\n---\n\n".join(
        f"[from {c['source']}]\n{c['text']}" for c, _ in context_chunks
    )
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        system=(
            "You answer questions using ONLY the provided document excerpts. "
            "If the excerpts don't contain the answer, say so honestly. "
            "Cite the source file for each fact you use."
        ),
        messages=[{
            "role": "user",
            "content": f"DOCUMENT EXCERPTS:\n{context}\n\nQUESTION: {question}",
        }],
    )
    return msg.content[0].text


# --- main -------------------------------------------------------------------
def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    docs_dir, question = sys.argv[1], " ".join(sys.argv[2:])

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

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\nSet ANTHROPIC_API_KEY to get Claude's answer (retrieval works without it).")
        return
    print("\nClaude says:\n")
    print(ask_claude(question, hits))


if __name__ == "__main__":
    main()
