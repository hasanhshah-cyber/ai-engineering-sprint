# Day 2 — Summarizer API

Day 2 built a Summarizer API. It is a small FastAPI service with one job:
POST text to /summarize and get back a short Claude-written summary.

The request is simple JSON: a text field and an optional sentences field
(default 3). The service sends the text to Claude with one instruction:
summarize it in exactly that many short sentences, plain language, no fluff,
no bullet points. The response is the summary as JSON.

Text in, summary out. That is the whole product. Keeping it to one job is
the point: a small API that does one thing well is easier to test, easier
to explain, and easier to reuse as a tool inside a bigger system.
