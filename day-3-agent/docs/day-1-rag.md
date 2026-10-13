# Day 1 — RAG chatbot over my own docs

Day 1 built ask-my-docs, a tiny RAG chatbot. It answers questions using only
your own documents, and shows its receipts.

How it works, in four steps. First, chunk: every document is split into
overlapping chunks of about 600 characters. Second, embed: each chunk becomes
a TF-IDF vector, a simple keyword-based embedding. Third, retrieve: the
question becomes a vector too, and cosine similarity picks the three most
relevant chunks. Fourth, generate: Claude answers using only those retrieved
excerpts, and cites the source file for each fact.

The honest limits: TF-IDF is keyword matching, not real understanding. It
misses synonyms and paraphrases. The upgrade path is a real embedding model.
