# Day 7: The Summarizer API, Deployed With a Live Link

Day 2 built the Summarizer API. Day 7 puts it on the internet. This is
the last item on the sprint roadmap: a link anyone can click.

## What changed from Day 2

One thing, and it is the whole point. Day 2 read the Anthropic key from
a credential helper that only exists on one machine. A public host does
not have that. Day 7 reads the key from the `ANTHROPIC_API_KEY`
environment variable, set as a secret on the host. Nothing secret lives
in this repo, ever. The API itself is unchanged: POST text, get back a
short plain-language summary.

## Deploy it (Render, free tier)

1. Push this folder to the sprint repo (same commit routine as every
   other day).
2. On render.com, New, Web Service, connect the repo. Set the Root
   Directory to `day-7-deployed-api`. The `render.yaml` here fills in
   the rest: free plan, Docker, health check on `/health`.
3. In the Render dashboard, add the secret environment variable
   `ANTHROPIC_API_KEY` with a fresh key. Never paste a key into code,
   a chat, or a screenshot.
4. Deploy. Render gives you a public URL. Open it: `/` explains the
   API, `/docs` is a page where anyone can try it in the browser.

## Run it locally

```bash
cd day-7-deployed-api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ANTHROPIC_API_KEY=your-key-here python app.py
```

Then open http://127.0.0.1:8000/docs, or:

```bash
curl -X POST http://127.0.0.1:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "paste anything long here", "sentences": 3}'
```

## Honest notes

- Render's free tier sleeps after inactivity, so the first request
  after a quiet stretch takes a while to wake up. That is the price of
  free.
- This endpoint is public. Anyone with the link can call it, and calls
  bill against the key. Keep an eye on usage in the Anthropic console,
  and rotate the key if it ever leaks.
- The model is set with `SUMMARIZER_MODEL` (default `claude-opus-4-6`).
