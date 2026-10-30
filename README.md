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
| 7 | [day-7-deployed-api](./day-7-deployed-api) | Summarizer API deployed with a live link, key as a host secret | Python, FastAPI, Docker, Render |
| 8 | [day-8-onprem-rag](./day-8-onprem-rag) | Fully on-prem RAG: Day 1 retrieval plus Day 6 local model, cloud call deleted. Answers from your own docs, receipts attached, no API key, no cloud | Python, TF-IDF, ONNX Runtime, HuggingFace |
| 9 | [day-9-rag-eval](./day-9-rag-eval) | Evaluation harness for on-prem RAG: 12 test cases, retrieval accuracy and honest refusal rate, no API key, no cloud | Python, TF-IDF, numpy |
| 10 | [day-10-mcp-rag](./day-10-mcp-rag) | MCP server for on-prem RAG: retrieve_docs and ask_docs over stdio, demo client proves both calls, no API key, no cloud | Python, MCP, TF-IDF, ONNX Runtime |
| 11 | [day-11-job-scanner](day-11-job-scanner) | Job scanner and filter: remote US or hybrid Illinois only, flags below $70,000 floor and drift roles, stops before applying | Python, JSON |
| 12 | [day-12-tailor](day-12-tailor) | Tailor and stage tool: verified evidence only, splits matched, gaps, and do not claim, checks pay and location, stops before submitting | Python, JSON |
| 13 | [day-13-pipeline](day-13-pipeline) | Pipeline runner: chains scanner and tailor into one morning report, staging only, stops before submitting | Python, JSON |
*More shipping weekly. Each build gets its own folder and README.*

## Why

Proof over promises. Every project here is real, runnable, and mine. Recruiters welcome — start with `rag-demo`.
