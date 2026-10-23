# Day 10: MCP Server for the On-Prem RAG

Day 8 built the system. Day 9 measured it. Day 10 makes it callable by any AI app, over MCP.

## What MCP is, in plain terms

MCP is the Model Context Protocol: a standard way for an AI app to call tools. The app sends a JSON message over stdio, the server runs the tool locally, and sends the result back as JSON. No API key, no cloud, no vendor lock in. The server here is implemented in plain Python with no MCP SDK, so the whole protocol is readable in `mcp_server.py`.

## Tools

- `retrieve_docs`: TF-IDF retrieval over the local docs, with scores, sources, and an honest refusal when nothing matches. Same threshold as Day 8 and Day 9: below 0.05, refuse.
- `ask_docs`: retrieve first, refuse when nothing matches, then answer with the Day 6 local model when it is available. If the model packages are not installed in this environment, it returns the retrieved passages instead of pretending to generate an answer.

## How to run the demo (Mac)

```bash
python3 -m venv venv && source venv/bin/activate
pip install --only-binary=:all: -r requirements.txt
python mcp_client_demo.py
```

The demo spawns the server, lists its tools, calls `retrieve_docs` in scope and out of scope, and prints PASS when both behave correctly. No model download is needed for the demo, because it only calls `retrieve_docs`.

## How to connect from an MCP client

Example Claude Desktop config, with the path replaced by your own checkout:

```json
{
  "mcpServers": {
    "onprem-rag": {
      "command": "python3",
      "args": ["/path/to/day-10-mcp-rag/mcp_server.py"],
      "cwd": "/path/to/day-10-mcp-rag"
    }
  }
}
```

Run it from this folder so it finds `docs/`. The Day 6 model is already downloaded on this Mac, so `ask_docs` can generate there. On a fresh machine, `retrieve_docs` works first, and `ask_docs` falls back to passages until the model packages are installed.

## Sprint README row

| Day 10 | MCP server for on-prem RAG: retrieve_docs and ask_docs over stdio, demo client proves both calls, no API key, no cloud. |
