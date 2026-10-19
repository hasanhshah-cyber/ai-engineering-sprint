# AI Engineering Sprint

![Day 1](https://img.shields.io/badge/day-1-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Status](https://img.shields.io/badge/status-building-orange)

One month. Real builds. No tutorials. I'm an implementation analyst going deep on AI engineering in public — so the things I build hit harder.

## The Builds

| Day | Project | What it does | Stack |
|-----|---------|--------------|-------|
| 1 | [ask-my-docs](./rag-demo) | RAG chatbot over my own docs — asks, retrieves, shows receipts | Python, TF-IDF, cosine similarity, Claude API |
| 2 | [summarizer-api](./summarizer-api) | HTTP API — POST text, get back a Claude-written summary | Python, FastAPI, Claude API |
| 3 | [day-3-agent](./day-3-agent) | Tool-using agent — asks, picks the right tool, calls it, answers | Python, Claude API tool use |
| 4 | [day-4-memory](./day-4-memory) | Agent with memory - remembers past conversation and facts, recalls them in later answers | Python, Claude API, JSON file store |
| 5 | [day-5-github-agent](./day-5-github-agent) | Agent talks to a real app - asks GitHub for live repo data, answers from it | Python, Claude API, GitHub API |
| 6 | [day-6-local-model](./day-6-local-model) | Small HuggingFace model downloaded once, then running locally with no API key | Python, HuggingFace, ONNX Runtime |

*More shipping weekly. Each build gets its own folder and README.*

## Why

Proof over promises. Every project here is real, runnable, and mine. Recruiters welcome — start with `rag-demo`.
