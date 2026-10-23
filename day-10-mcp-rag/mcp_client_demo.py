#!/usr/bin/env python3
"""Day 10 demo client: proves the MCP server works end to end, without
needing Claude Desktop or any other MCP app.

It spawns mcp_server.py over stdio, sends initialize, lists tools, then
calls retrieve_docs twice: once in scope, once out of scope. It asserts
the in-scope call returns data-security-rules.md on top, and the
out-of-scope call is refused honestly, then prints PASS.

Usage (from inside this folder):
    python3 -m venv venv && source venv/bin/activate
    pip install --only-binary=:all: -r requirements.txt
    python mcp_client_demo.py

No API key, no cloud, no model download. This demo only calls
retrieve_docs, so it runs anywhere the server runs.
"""

import json
import subprocess
import sys


def send(proc, msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        raise RuntimeError("server closed stdout")
    return json.loads(line)


def main():
    proc = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        init = send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "day10-demo", "version": "1.0.0"},
                },
            },
        )
        print(f"Server: {init['result']['serverInfo']['name']} "
              f"{init['result']['serverInfo']['version']}")
        proc.stdin.write(
            json.dumps(
                {"jsonrpc": "2.0", "method": "notifications/initialized"}
            )
            + "\n"
        )
        proc.stdin.flush()

        tools = send(
            proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )
        names = [t["name"] for t in tools["result"]["tools"]]
        print(f"Tools: {', '.join(names)}")
        assert "retrieve_docs" in names and "ask_docs" in names

        def call(question):
            resp = send(
                proc,
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "retrieve_docs",
                        "arguments": {"question": question},
                    },
                },
            )
            return json.loads(resp["result"]["content"][0]["text"])

        in_scope = call("What are the data security rules?")
        print(f"\nIn scope: {in_scope['question']}")
        for h in in_scope["hits"]:
            print(f"  [{h['score']:.2f}] {h['source']}")
        assert not in_scope["refused"]
        assert in_scope["hits"][0]["source"] == "data-security-rules.md"

        out_scope = call("What is the capital of France?")
        print(f"\nOut of scope: {out_scope['question']}")
        print(f"  refused: {out_scope['refused']}, top score: {out_scope['hits'][0]['score']:.2f}")
        assert out_scope["refused"]

        print("\nPASS: MCP server answered both calls correctly.")
    finally:
        proc.stdin.close()
        proc.wait(timeout=10)


if __name__ == "__main__":
    main()
