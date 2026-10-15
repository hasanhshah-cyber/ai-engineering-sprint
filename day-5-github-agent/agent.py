"""Day 5 — tool-using agent WITH MEMORY, now talking to a REAL app: GitHub.

Day 4's agent, plus one new tool:
  github_lookup  Call the PUBLIC GitHub API (no login, no token) and
                 answer questions about real users and repos.

Tools (Day 1 + Day 2 + Day 5):
  search_docs    Day 1 retrieval (TF-IDF over the docs/ folder)
  summarize_text Day 2 summarizer (Claude-written summary)
  github_lookup  Day 5 GitHub lookup (live public API data)

Memory (Day 4 pattern):
  Short-term: recent conversation, so follow-ups like "summarize that"
  work without repeating yourself.
  Long-term:  facts saved with "remember that ...", kept across runs.

Usage:
    python agent.py "your question"
    python agent.py "remember that my favorite tool is the GitHub lookup"
    python agent.py "what repos does hasanhshah-cyber have?"
    python agent.py "what is in the ai-engineering-sprint repo?"
"""
import json
import os
import sys
import urllib.request

import memory as memory_store
from tools import github_lookup, search_docs, summarize_text

API_URL = "https://api.anthropic.com/v1/messages"
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = os.environ.get("AGENT_MODEL", "claude-opus-4-6")
MAX_STEPS = 5

SYSTEM_PROMPT = (
    "You are a small tool-using agent with memory. You have three tools: "
    "search_docs (search Hasan's sprint documents), "
    "summarize_text (summarize a block of text into a few sentences), and "
    "github_lookup (look up real GitHub users and repos via the public API). "
    "Use search_docs when the question is about the sprint, past builds, "
    "or anything in the docs. Use summarize_text when the user asks for "
    "a summary, a shorter version, or a specific number of sentences. "
    "Use github_lookup when the user asks about a GitHub user or repo: "
    "pass the username, and pass repo as well when they name a specific repo. "
    "If the question mentions GitHub, a username, or repos, use github_lookup "
    "FIRST, before search_docs. If search_docs returns 'No documents found', "
    "try github_lookup before giving up. Never say you have no information "
    "about a GitHub user without calling github_lookup first. "
    "Use the conversation history below to answer follow-ups: when the "
    "user says 'that', 'it', or 'summarize that', they mean the previous "
    "question and answer. Use the facts list for things the user told "
    "you to remember. Answer from tool results and conversation history. "
    "If the tools and history do not contain the answer, say so honestly. "
    "Keep the final answer short and plain."
)

TOOLS = [
    {
        "name": "search_docs",
        "description": (
            "Search Hasan's sprint documents for information. Use this when "
            "the question is about the sprint, past builds, or anything in "
            "the docs. Returns the most relevant excerpts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "summarize_text",
        "description": (
            "Summarize a block of text into a short summary. Use this when "
            "the user asks for a summary, a shorter version, or a specific "
            "number of sentences."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to summarize"},
                "sentences": {
                    "type": "integer",
                    "description": "Number of sentences in the summary (1-5)",
                },
            },
            "required": ["text", "sentences"],
        },
    },
    {
        "name": "github_lookup",
        "description": (
            "ALWAYS use this for questions about GitHub users, usernames, "
            "repos, or repositories. "
            "Look up a real GitHub user or repo via the public GitHub API. "
            "Use this when the user asks about a GitHub username, what repos "
            "someone has, or details of a specific repo. Returns live facts: "
            "bio, repo list, languages, stars, descriptions. No login needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "GitHub username, e.g. hasanhshah-cyber",
                },
                "repo": {
                    "type": "string",
                    "description": (
                        "Optional repo name, e.g. ai-engineering-sprint. "
                        "Leave out to list the user's repos."
                    ),
                },
            },
            "required": ["username"],
        },
    },
]


def call_claude(messages, system):
    """One Messages API call with tools. Returns the parsed response dict."""
    body = {
        "model": MODEL,
        "max_tokens": 600,
        "system": system,
        "tools": TOOLS,
        "messages": messages,
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
        return json.loads(resp.read().decode("utf-8"))


def _short(text, limit=400):
    """Truncate for clean terminal output (display only, full text is used)."""
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "..."


def run_agent(question, docs_dir=None):
    """Run the agent loop. Returns the final answer string."""
    if docs_dir is None:
        # Reuse the Day 3 docs when this folder sits next to day-3-agent,
        # otherwise fall back to the local docs/ copy.
        day3_docs = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "day-3-agent", "docs"
        )
        local_docs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
        docs_dir = day3_docs if os.path.isdir(day3_docs) else local_docs

    mem = memory_store.load()

    # Long-term fact, no API call needed.
    if question.strip().lower().startswith("remember that "):
        fact = question.strip()[len("remember that "):]
        memory_store.remember_fact(mem, fact)
        print(f"REMEMBERED: {fact}")
        return f"Got it, I will remember that {fact}."

    context = memory_store.format_context(mem)
    system = SYSTEM_PROMPT + ("\n\n" + context if context else "")
    if context:
        print("MEMORY LOADED: using past conversation and facts.")

    print(f"Q: {question}")
    messages = [{"role": "user", "content": question}]

    for _step in range(MAX_STEPS):
        data = call_claude(messages, system)
        assistant_blocks = data["content"]
        messages.append({"role": "assistant", "content": assistant_blocks})

        tool_results = []
        saw_tool_use = False
        for block in assistant_blocks:
            if block["type"] == "text" and block["text"].strip():
                print(f"\nTHINKING: {_short(block['text'], 300)}")
            elif block["type"] == "tool_use":
                saw_tool_use = True
                name = block["name"]
                args = block["input"]
                print(f"\nTOOL: {name}({json.dumps(args)})")
                if name == "search_docs":
                    result = search_docs(args["query"], docs_dir)
                elif name == "summarize_text":
                    result = summarize_text(args["text"], int(args.get("sentences", 3)))
                elif name == "github_lookup":
                    result = github_lookup(args["username"], args.get("repo"))
                else:
                    result = f"Unknown tool: {name}"
                print(f"RESULT: {_short(result)}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block["id"],
                    "content": result,
                })

        if not saw_tool_use:
            answer = " ".join(
                b["text"] for b in assistant_blocks if b["type"] == "text"
            ).strip()
            print(f"\nANSWER: {answer}")
            memory_store.remember(mem, question, answer)
            return answer

        messages.append({"role": "user", "content": tool_results})

    print("\nANSWER: I hit the step limit before finishing. Try a simpler question.")
    return ""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    question = " ".join(sys.argv[1:])
    try:
        run_agent(question)
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
