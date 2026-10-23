# Day 9: Evaluation for the On-Prem RAG

Day 8 proved the system runs. Day 9 proves it works, with numbers.

## What it measures

From `tests.json`, 12 cases, 9 in scope and 3 out of scope:

- Retrieval accuracy: in-scope questions where the top retrieved chunk comes from the expected document.
- Refusal rate: out-of-scope questions where the top score falls below 0.05, so Day 8 would honestly say the documents do not contain an answer instead of guessing.
- Overall pass rate: both groups together.

This measures retrieval only, on purpose. Retrieval decides whether an answer can be grounded at all. The 80M local model is thin, so generation quality is judged by a human reading the answer against its sources, not by an automatic score that would pretend otherwise.

## How to run (Mac)

```bash
python3 -m venv venv && source venv/bin/activate
pip install --only-binary=:all: -r requirements.txt
python eval.py
```

No API key, no cloud, no model download. Retrieval is TF-IDF in plain numpy, exactly like Day 1 and Day 8.

## How to read a FAIL

A FAIL is useful, not hidden. It names the exact question, the document retrieved, and the document expected, so the next fix is a docs change or a threshold change, not a guess. Add a test case to `tests.json` whenever a real question fails in use, so the harness grows with the system.

## Sprint README row

| Day 9 | Evaluation harness for on-prem RAG: 12 test cases, retrieval accuracy and honest refusal rate, no API key, no cloud. |
