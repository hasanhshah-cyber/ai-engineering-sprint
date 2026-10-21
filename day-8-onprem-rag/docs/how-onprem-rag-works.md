# How on-prem RAG works

On-prem RAG is a question-answering system that runs entirely on a company's
own machines. Nothing is sent to the cloud, and no outside API is ever called.
The system has four layers, and each one runs inside the building.

First, gather. Internal documents are collected into one organized store on
the company's own servers. The documents are split into overlapping chunks so
each piece is small enough for the system to work with. This is the
streamlining step: scattered files become one clean source.

Second, retrieve. When someone asks a question, the system compares the
question against every chunk and picks the most relevant passages. This build
uses TF-IDF vectors in plain numpy: it counts which words appear in each chunk
and in the question, weights rare words higher, and scores each chunk by
cosine similarity. No model and no API key are needed for this step.

Third, model. An open model that was downloaded once runs on the company's
own hardware and reads only the retrieved passages. It answers from those
passages and nothing else. If the passages do not contain the answer, the
system says so honestly instead of guessing.

Fourth, ship. Staff get a simple internal tool: type a question, get an
answer, and see receipts showing which document each fact came from. Every
answer can be traced back to its source.
