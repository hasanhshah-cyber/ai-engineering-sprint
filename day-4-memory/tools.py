"""Day 3 tools — Day 1 retrieval + Day 2 summarizer, reused as agent tools.

search_docs: same TF-IDF + cosine retrieval algorithm as Day 1 (rag-demo),
rewritten in stdlib-only Python so Day 3 runs with zero pip installs.
summarize_text: same Claude-written summary as Day 2 (summarizer-api).
"""
import json
import math
import os
import re
import sys
import urllib.request
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = os.environ.get("AGENT_MODEL", "claude-opus-4-6")

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 2


# --- search_docs (Day 1 retrieval) ------------------------------------------

def _tokenize(s):
    return re.findall(r"[a-z0-9]+", s.lower())


def _chunk_text(text, source):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append({"text": text[start:start + CHUNK_SIZE], "source": source})
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _build_index(docs_dir):
    """Index every .md file under docs_dir. Returns (chunks, idf)."""
    chunks = []
    for p in sorted(Path(docs_dir).glob("**/*.md")):
        text = p.read_text(errors="ignore")
        if len(text) < 200:
            continue
        chunks.extend(_chunk_text(text, p.name))
    # document frequency -> idf
    n = len(chunks)
    df = {}
    for c in chunks:
        for t in set(_tokenize(c["text"])):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log((1 + n) / (1 + d)) + 1.0 for t, d in df.items()}
    return chunks, idf


def _vector(text, idf):
    toks = _tokenize(text)
    tf = {}
    for t in toks:
        tf[t] = tf.get(t, 0) + 1
    vec = {t: (c / len(toks)) * idf[t] for t, c in tf.items() if t in idf}
    norm = math.sqrt(sum(v * v for v in vec.values())) + 1e-9
    return {t: v / norm for t, v in vec.items()}


def search_docs(query, docs_dir):
    """Return the TOP_K most relevant excerpts for the query."""
    chunks, idf = _build_index(docs_dir)
    if not chunks:
        return "No documents found."
    qv = _vector(query, idf)
    scored = []
    for c in chunks:
        cv = _vector(c["text"], idf)
        score = sum(qv.get(t, 0.0) * cv.get(t, 0.0) for t in qv)
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:TOP_K]
    header = "Retrieved: " + ", ".join(c["source"] for _, c in top)
    parts = [header]
    for score, c in top:
        parts.append(f"[from {c['source']}]\n{c['text'].strip()}")
    return "\n\n---\n\n".join(parts)


# --- summarize_text (Day 2 summarizer) --------------------------------------

def summarize_text(text, sentences=3):
    """Return a Claude-written summary of text in exactly `sentences` sentences."""
    sentences = max(1, min(5, int(sentences)))
    body = {
        "model": MODEL,
        "max_tokens": 300,
        "system": (
            f"Summarize the user's text in exactly {sentences} short sentences. "
            "Plain language, no fluff, no bullet points."
        ),
        "messages": [{"role": "user", "content": text}],
    }
    if not API_KEY:
        raise RuntimeError("Set the ANTHROPIC_API_KEY environment variable first.")
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return "".join(
        block["text"] for block in data["content"] if block["type"] == "text"
    ).strip()
