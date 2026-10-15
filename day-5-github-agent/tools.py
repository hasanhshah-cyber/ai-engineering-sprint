"""Day 5 tools — Day 1 retrieval + Day 2 summarizer + NEW Day 5 GitHub lookup.

search_docs: same TF-IDF + cosine retrieval algorithm as Day 1 (rag-demo),
rewritten in stdlib-only Python so the agent runs with zero pip installs.
summarize_text: same Claude-written summary as Day 2 (summarizer-api).
github_lookup: NEW — calls the PUBLIC GitHub API (no login, no token) to
answer real questions about real users and repos. If the network call
fails, it says so honestly instead of making anything up.
"""
import json
import math
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = os.environ.get("AGENT_MODEL", "claude-opus-4-6")

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 2

GITHUB_API = "https://api.github.com"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "ai-engineering-sprint-day5",
}
# GitHub usernames/repos: letters, numbers, dots, hyphens, underscores.
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


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


# --- github_lookup (Day 5 — NEW: talk to a real app) --------------------------

def _github_get(url):
    """One GET against the public GitHub API. Returns (data, error)."""
    req = urllib.request.Request(url, headers=GITHUB_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "Not found on GitHub (404). Check the username or repo spelling."
        if exc.code == 403:
            return None, (
                "GitHub rate limit hit. The public API allows 60 requests/hour "
                "without a login. Wait a bit and try again."
            )
        return None, f"GitHub API error: HTTP {exc.code}."
    except urllib.error.URLError:
        return None, "Could not reach the GitHub API. Check your internet connection."


def _short(text, limit=120):
    """One-line truncate for display."""
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[:limit] + "..."


def github_lookup(username, repo=None):
    """Look up a real GitHub user (and optionally one of their repos).

    username: GitHub username, e.g. "hasanhshah-cyber".
    repo:     optional repo name, e.g. "ai-engineering-sprint".
    Returns plain-text facts from the live public API. No login, no token.
    """
    username = (username or "").strip()
    if not _SAFE_NAME.match(username):
        return "That does not look like a valid GitHub username."

    if repo is not None:
        repo = repo.strip()
        if not _SAFE_NAME.match(repo):
            return "That does not look like a valid repo name."
        data, err = _github_get(f"{GITHUB_API}/repos/{username}/{repo}")
        if err:
            return err
        license_name = (data.get("license") or {}).get("spdx_id") or "none listed"
        topics = ", ".join(data.get("topics") or []) or "none"
        return (
            f"Repo: {data.get('full_name')}\n"
            f"Description: {_short(data.get('description') or 'no description')}\n"
            f"Language: {data.get('language') or 'not listed'} | "
            f"Stars: {data.get('stargazers_count')} | "
            f"Forks: {data.get('forks_count')} | "
            f"Open issues: {data.get('open_issues_count')}\n"
            f"License: {license_name} | Topics: {topics}\n"
            f"Created: {data.get('created_at')} | Updated: {data.get('updated_at')}\n"
            f"URL: {data.get('html_url')}"
        )

    profile, err = _github_get(f"{GITHUB_API}/users/{username}")
    if err:
        return err
    repos, err = _github_get(
        f"{GITHUB_API}/users/{username}/repos?per_page=100&sort=updated"
    )
    if err:
        return f"Found the user, but could not list their repos: {err}"

    lines = [
        f"User: {profile.get('login')} "
        f"({profile.get('name') or 'no display name'})",
        f"Bio: {_short(profile.get('bio') or 'no bio')}",
        f"Public repos: {profile.get('public_repos')} | "
        f"Followers: {profile.get('followers')} | "
        f"Following: {profile.get('following')} | "
        f"Account created: {profile.get('created_at')}",
        "",
        "Most recently updated repos:",
    ]
    for r in repos[:10]:
        lines.append(
            f"- {r.get('name')} | {r.get('language') or 'no language listed'} | "
            f"stars: {r.get('stargazers_count')} | "
            f"{_short(r.get('description') or 'no description')}"
        )
    if not repos:
        lines.append("- No public repos.")
    return "\n".join(lines)
