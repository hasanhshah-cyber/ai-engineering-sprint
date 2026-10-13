# Day 3 — Tool-using agent

Day 1 retrieved. Day 2 summarized. Day 3 decides.

This is a small agent that takes a question, picks a tool, calls it, and
answers — with the trace printed so you can watch it think:

```
Q: What did we build on Day 2? Summarize it in 2 sentences.

THINKING: I need to find what Day 2 built, then summarize it.
TOOL: search_docs({"query": "Day 2 build"})
RESULT: [from day-2-summarizer.md] Day 2 built a Summarizer API...
TOOL: summarize_text({"text": "...", "sentences": 2})
RESULT: Day 2 built a small API that turns text into a short summary.
ANSWER: Day 2 built a small API that turns text into a short summary.
```

## The loop

ReAct-style, using Anthropic native tool use — the model decides which tool
to call, not a hardcoded router:

1. The question goes to Claude with two tools attached.
2. Claude returns either text (thinking) or a `tool_use` block.
3. The agent executes the tool, feeds the result back, and repeats.
4. When Claude answers without a tool call, that is the final answer.

Max 5 steps per question. If it hits the limit, it says so instead of
looping forever.

## Tools

| Tool | From | What it does |
|------|------|--------------|
| `search_docs` | Day 1 | TF-IDF + cosine retrieval over `docs/` |
| `summarize_text` | Day 2 | Claude-written summary, N sentences |

The retrieval code is the same algorithm as Day 1, rewritten in
stdlib-only Python (no numpy) so Day 3 runs with zero installs. The
summarizer is the same Claude call as Day 2.

## Run it

No dependencies. No pip install. Python 3.10+.

```bash
cd day-3-agent
python agent.py "your question"
python demo.py        # 2 example questions, end to end
```

API access uses the same stored-credential pattern as Day 2. No API key
in code, README, or logs.

## Honest limits

- **Retrieval is keyword matching.** TF-IDF misses synonyms and paraphrases.
  The agent can only answer what the docs contain, and says so when they
  don't.
- **The model picks the tools.** Sometimes it answers from a single search
  without summarizing, or summarizes without searching. That is the agent
  deciding, not a bug — but it means the trace varies run to run.
- **Small docs, small brain.** `docs/` holds three short files about the
  sprint. Point it at a bigger folder and it works the same way, but
  retrieval quality stays TF-IDF-level.
- **No memory, no planning.** Each question starts fresh. It does not
  remember past questions or break big goals into subtasks.
