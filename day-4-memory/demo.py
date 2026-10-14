"""Day 4 demo — runs 4 questions end to end, proving memory works.

Q1 asks about Day 2 (tool use, like Day 3).
Q2 is a follow-up ("summarize that") — only works with short-term memory.
Q3 stores a long-term fact ("remember that ...").
Q4 recalls that fact — only works with long-term memory.

Output is kept clean for screen recording.
"""
import os
import sys

from agent import run_agent

HERE = os.path.dirname(os.path.abspath(__file__))

QUESTIONS = [
    "What did we build on Day 2 of the sprint?",
    "Summarize that in 1 sentence.",
    "Remember that my favorite tool is the summarizer.",
    "What is my favorite tool?",
]


def main():
    # Fresh memory for a clean demo recording.
    mem_file = os.path.join(HERE, "memory.json")
    if os.path.exists(mem_file):
        os.remove(mem_file)
    try:
        for i, q in enumerate(QUESTIONS, 1):
            print(f"\n{'=' * 60}")
            print(f"DEMO {i}/{len(QUESTIONS)}")
            print(f"{'=' * 60}\n")
            run_agent(q)
        print(f"\n{'=' * 60}")
        print("DEMO DONE — memory works: follow-up + fact recall both landed.")
        print(f"{'=' * 60}")
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
