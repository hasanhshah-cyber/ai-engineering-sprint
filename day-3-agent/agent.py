"""Day 3 — tool-using agent.

Takes a question, picks a tool, calls it, and answers — with the trace printed
so you can watch it think. The loop is Anthropic native tool use (the model
decides which tool to call), not a hardcoded if/else router.

Tools:
  search_docs    Day 1 retrieval (TF-IDF over the docs/ folder)
  summarize_text Day 2 summarizer (Claude-written summary)

Usage:
    python agent.py "your question"
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

from tools import search_docs, summarize_text

API_URL = "https://api.anthropic.com/v1/messages"
ALLOWED_HOSTS = ["api.anthropic.com"]
CREDENTIAL = "custom.anthropic"
MODEL = os.environ.get("AGENT_MODEL", "claude-opus-4-6")
MAX_STEPS = 5

SYSTEM_PROMPT = (
    "You are a small tool-using agent. You have two tools: "
    "search_docs (search Hasan's sprint documents) and "
    "summarize_text (summarize a block of text into a few sentences). "
    "Use search_docs when the question is about the sprint, past builds, "
    "or anything in the docs. Use summarize_text when the user asks for "
    "a summary, a shorter version, or a specific number of sentences. "
    "Answer from tool results, never from memory. If the tools do not "
    "contain the answer, say so honestly. Keep the final answer short "
    "and plain."
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
]


def call_claude(messages):
    """One Messages API call with tools. Returns the parsed response dict."""
    body = {
        "model": MODEL,
        "max_tokens": 600,
        "system": SYSTEM_PROMPT,
        "tools": TOOLS,
        "messages": messages,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
    )
    add_surrogate_to_request(req, CREDENTIAL, allowed_hosts=ALLOWED_HOSTS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return read_json_response(resp)


def _short(text, limit=400):
    """Truncate for clean terminal output (display only, full text is used)."""
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "..."


def run_agent(question, docs_dir=None):
    """Run the agent loop. Returns the final answer string."""
    if docs_dir is None:
        docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

    print(f"Q: {question}")
    messages = [{"role": "user", "content": question}]

    for _step in range(MAX_STEPS):
        data = call_claude(messages)
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
