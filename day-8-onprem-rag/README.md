# Day 8: Fully On-Prem RAG

Your documents, retrieved locally, answered by a local model. No API key.
No cloud call. Nothing leaves the machine.

## What this is

Day 1 retrieved with TF-IDF in plain numpy, which never needed an API key.
Day 6 ran a small open model locally with ONNX Runtime, which never needed
one either. Day 8 joins them and deletes the cloud call: retrieve the
relevant passages, hand them to the local model as context, print the
answer with receipts showing which document each fact came from.

If the retrieved passages do not match the question, the script says the
documents do not contain an answer instead of letting the model guess.
That refusal is part of the design: a grounded answer or an honest no.

## How to run (Mac)

The Day 6 model is already downloaded on this Mac, so there is nothing new
to fetch. From inside this folder:

```bash
python3 -m venv venv && source venv/bin/activate
pip install --only-binary:all: -r requirements.txt
python onprem_rag.py docs "What are the data security rules?"
python onprem_rag.py docs "How does the system work?" --retrieve-only
```

Try a question the docs cannot answer, and watch the honest refusal:

```bash
python onprem_rag.py docs "What is the capital of France?"
```

## How it works

1. Gather: markdown files in `docs/` are split into overlapping chunks.
2. Retrieve: TF-IDF vectors in plain numpy, cosine similarity, top 3 chunks.
   Stopwords are dropped so common words cannot fake a match.
3. Model: Xenova/flan-t5-small, the ONNX version of google/flan-t5-small,
   run through ONNX Runtime directly with plain numpy arrays. No torch, no
   optimum: PyTorch no longer ships Intel Mac wheels, and optimum depends
   on torch.
4. Ship: the answer prints with its sources, so every fact traces back to
   a document.

## Why this one matters

This is the Argonne system at small scale: internal data, retrieved
locally, answered on the company's own machines, receipts attached, and
nothing ever leaving the building. Swap the sample docs in `docs/` for
real internal documents and the shape of the system does not change.

## Sprint README row

| Day 8 | Fully on-prem RAG: Day 1 retrieval plus Day 6 local model, cloud call deleted. Answers from your own docs, receipts attached, no API key, no cloud. |
