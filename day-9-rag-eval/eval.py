#!/usr/bin/env python3
"""Day 9: evaluation harness for the Day 8 on-prem RAG.

Day 8 proved the system runs. Day 9 proves it works, with numbers a
recruiter can check. This measures retrieval only, on purpose: retrieval
is the part that decides whether an answer can be grounded at all. The
80M local model is thin, so generation quality is judged by a human
reading the answer against its sources, not by an automatic score that
would pretend otherwise.

What it measures, from tests.json:
  - Retrieval accuracy: in-scope questions where the top retrieved
    chunk comes from the expected document.
  - Refusal rate: out-of-scope questions where the top score falls
    below MIN_SCORE, so Day 8 would honestly say the documents do not
    contain an answer, instead of guessing.
  - Overall pass rate: both groups together.

Usage (on Hasan's Mac, from inside this folder):
    python3 -m venv venv && source venv/bin/activate
    pip install --only-binary=:all: -r requirements.txt
    python eval.py
    python eval.py docs tests.json   # explicit docs and test files

No API key, no cloud, no model download. Retrieval is TF-IDF in plain
numpy, exactly like Day 1 and Day 8, so this runs anywhere Day 8 runs.
"""

import json
import re
import sys
from pathlib import Path

import numpy as np

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 3
MIN_SCORE = 0.05  # same threshold as Day 8: below this, refuse

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "do", "does", "did", "done", "can", "could", "will", "would", "should",
    "and", "or", "but", "if", "then", "than", "of", "to", "in", "on", "at",
    "by", "for", "with", "from", "as", "it", "its", "this", "that", "these",
    "those", "i", "you", "he", "she", "we", "they", "my", "your", "his",
    "her", "our", "their", "not", "no", "so", "very", "just", "me", "him",
}


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


def retrieve(question, chunks, mat, vocab, idf, k=TOP_K):
    qv = embed_query(question, vocab, idf)
    scores = mat @ qv
    top = np.argsort(scores)[::-1][:k]
    return [(chunks[i], float(scores[i])) for i in top]


def main():
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"
    tests_path = sys.argv[2] if len(sys.argv) > 2 else "tests.json"
    chunks = load_docs(docs_dir)
    mat, vocab, idf = tfidf_vectors(chunks)
    tests = json.loads(Path(tests_path).read_text())
    print(f"Day 9 eval: {len(chunks)} chunks, {len(tests)} test cases\n")

    passed = 0
    in_scope_total = in_scope_pass = 0
    out_scope_total = out_scope_pass = 0
    for t in tests:
        hits = retrieve(t["question"], chunks, mat, vocab, idf)
        top_source, top_score = hits[0][0]["source"], hits[0][1]
        if t["kind"] == "in_scope":
            in_scope_total += 1
            ok = top_source == t["expected_source"]
            in_scope_pass += ok
            verdict = "PASS" if ok else "FAIL"
            print(f"[{verdict}] {t['question']}")
            print(f"       top: {top_source} [{top_score:.2f}], expected: {t['expected_source']}")
        else:
            out_scope_total += 1
            ok = top_score < MIN_SCORE
            out_scope_pass += ok
            verdict = "PASS" if ok else "FAIL"
            print(f"[{verdict}] {t['question']}")
            print(f"       top: {top_source} [{top_score:.2f}], expected: refusal (score < {MIN_SCORE})")
        passed += ok

    print("\nResults:")
    print(f"  Retrieval accuracy: {in_scope_pass}/{in_scope_total}")
    print(f"  Refusal rate:       {out_scope_pass}/{out_scope_total}")
    print(f"  Overall:            {passed}/{len(tests)}")
    if passed < len(tests):
        print("\nNote: a FAIL here is useful, not hidden. It names the exact")
        print("question and document, so the next fix is a docs or threshold")
        print("change, not a guess.")


if __name__ == "__main__":
    main()
