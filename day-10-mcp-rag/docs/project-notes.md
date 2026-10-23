# Project notes: from the sprint to Day 8

Day 1 of the sprint was a retrieval chatbot. It chunked documents, built
TF-IDF vectors, retrieved the most relevant passages, and handed them to a
cloud API to write the answer. The retrieval was local. The answering was
not, and that was the gap.

Day 6 of the sprint was a local model. A small open model from HuggingFace,
flan-t5-small, was downloaded once and run locally with ONNX Runtime. No
API key, no cloud, no data leaving the machine. It summarized paragraphs
and answered questions from a short context. The model worked, but it had
no documents of its own to read.

Day 7 of the sprint was a deployed API. The summarizer service was
Dockerized and deployed with a public live link, and the API key was held
as a host secret, never in code. That proved the shipping step: a service
can go live and stay secure.

Day 8 joins Day 1 and Day 6. Retrieval from Day 1, generation from Day 6,
and the cloud call deleted. The result is a complete on-prem system at
small scale: documents in, grounded answers out, receipts attached, and
nothing ever leaving the machine.
