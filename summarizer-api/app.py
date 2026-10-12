"""Day 2 — Summarizer API.

POST /summarize with {"text": "..."} and get back a short Claude-written summary.
Text in, summary out. That's the whole product.
"""
import json
import os
import sys
import urllib.request

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

API_URL = "https://api.anthropic.com/v1/messages"
ALLOWED_HOSTS = ["api.anthropic.com"]
CREDENTIAL = "custom.anthropic"
MODEL = os.environ.get("SUMMARIZER_MODEL", "claude-opus-4-6")

app = FastAPI(title="Summarizer API", version="0.1.0")


class SummarizeRequest(BaseModel):
    text: str
    sentences: int = 3


class SummarizeResponse(BaseModel):
    summary: str


def summarize_with_claude(text: str, sentences: int) -> str:
    body = {
        "model": MODEL,
        "max_tokens": 300,
        "system": (
            f"Summarize the user's text in exactly {sentences} short sentences. "
            "Plain language, no fluff, no bullet points."
        ),
        "messages": [{"role": "user", "content": text}],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
    )
    add_surrogate_to_request(req, CREDENTIAL, allowed_hosts=ALLOWED_HOSTS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = read_json_response(resp)
    return "".join(
        block["text"] for block in data["content"] if block["type"] == "text"
    ).strip()


@app.get("/")
def index():
    return {
        "name": "Summarizer API",
        "usage": 'POST /summarize with {"text": "...", "sentences": 3}',
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    if not 1 <= req.sentences <= 10:
        raise HTTPException(status_code=400, detail="sentences must be 1-10")
    try:
        summary = summarize_with_claude(req.text, req.sentences)
    except Exception as exc:  # keep the API honest about upstream failures
        raise HTTPException(status_code=502, detail=f"summarizer failed: {exc}")
    return SummarizeResponse(summary=summary)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
