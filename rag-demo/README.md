# Ask-My-Docs — a RAG chatbot in one afternoon

You built a retrieval-augmented generation pipeline. That's Level 3 of the AI engineer stack, on day one.

## What it does
Point it at a folder of documents, ask a question in plain English. It:
1. **Chunks** your docs into bite-size pieces
2. **Embeds** each chunk as a TF-IDF vector (numbers the computer can compare)
3. **Retrieves** the 3 most relevant chunks by cosine similarity
4. **Generates** an answer with Claude, grounded only in those chunks

## Setup (Mac, 5 minutes)
```bash
pip install anthropic numpy
export ANTHROPIC_API_KEY=sk-ant-your-key-here   # from console.anthropic.com
```

## Run it
```bash
python rag.py /path/to/your/docs "who is the culprit in the study"
```

Try: "what's the art style?", "how does the accusation work?", "what did we decide about the HUD?"

## How it maps to the video
- **RAG** — this whole thing. Chunk → embed → retrieve → generate.
- **APIs** — you're calling Claude's API with your own system prompt (context engineering!).
- **Evaluation thinking** — the relevance scores ([0.31]) tell you how confident retrieval is.

## Week-2 upgrade (your next post)
Swap `tfidf_vectors()` for `sentence-transformers` (real neural embeddings) and compare the scores. Same pipeline, smarter vectors.
