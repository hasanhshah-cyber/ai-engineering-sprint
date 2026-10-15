"""Day 5 — memory store for the agent.

Two kinds of memory:
  Short-term: the recent conversation (last few Q&As), loaded every run.
  Long-term:  facts the agent should keep across runs ("remember that ...").

Storage is one JSON file (memory.json) next to this script. No database,
no pip installs. The agent reads it at startup and writes back after
each answer, so memory survives between runs.
"""
import json
import os

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")
MAX_TURNS = 8  # keep the last 8 exchanges so the prompt stays small


def load():
    """Return the memory dict: {"history": [...], "facts": [...]}."""
    if not os.path.exists(MEMORY_FILE):
        return {"history": [], "facts": []}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("history", [])
        data.setdefault("facts", [])
        return data
    except (json.JSONDecodeError, OSError):
        return {"history": [], "facts": []}


def save(mem):
    """Write memory back to disk. Trims history to MAX_TURNS."""
    mem["history"] = mem["history"][-MAX_TURNS:]
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)


def remember(mem, question, answer):
    """Append one exchange to history and save."""
    mem["history"].append({"q": question, "a": answer})
    save(mem)


def remember_fact(mem, fact):
    """Store a long-term fact (no duplicates) and save."""
    fact = fact.strip().rstrip(".")
    if fact and fact not in mem["facts"]:
        mem["facts"].append(fact)
    save(mem)


def format_context(mem):
    """Render memory as text for the system prompt. Empty string if none."""
    parts = []
    if mem["facts"]:
        parts.append("Facts you know:\n" + "\n".join(f"- {f}" for f in mem["facts"]))
    if mem["history"]:
        lines = [f"User: {t['q']}\nYou: {t['a']}" for t in mem["history"]]
        parts.append("Recent conversation:\n" + "\n\n".join(lines))
    return "\n\n".join(parts)
