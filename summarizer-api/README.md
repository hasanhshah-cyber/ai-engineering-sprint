# Summarizer API (Day 2)

Text in, summary out. A tiny HTTP API: you POST text, Claude reads it, you get back a short plain-language summary.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:8000/docs for the interactive docs, or:

```bash
curl -X POST http://127.0.0.1:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "paste anything long here", "sentences": 3}'
```

## How it works

1. FastAPI takes the POST and validates the body (`text`, optional `sentences`).
2. The text goes to Claude with a system prompt: summarize in N short sentences, plain language.
3. The summary comes back as JSON: `{"summary": "..."}`.

## Config

- `SUMMARIZER_MODEL` — env var to swap the Claude model (default: `claude-opus-4-6`).

## Why this exists

Day 2 of the sprint: a real API with a real product shape. Day 1 taught retrieval; this one teaches the request/response loop every AI product is built on.
