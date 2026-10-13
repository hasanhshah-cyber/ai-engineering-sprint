"""Day 3 demo — runs 2 example questions end to end.

Each question exercises the full loop: the agent searches the docs, and
summarizes what it found. Output is kept clean for screen recording.
"""
import sys

from agent import run_agent

QUESTIONS = [
    "What did we build on Day 2 of the sprint? Summarize it in 2 sentences.",
    "How does the Day 1 RAG chatbot work? Summarize it in 2 sentences.",
]


def main():
    try:
        for i, q in enumerate(QUESTIONS, 1):
            print(f"\n{'=' * 60}")
            print(f"DEMO {i}/2")
            print(f"{'=' * 60}\n")
            run_agent(q)
        print(f"\n{'=' * 60}")
        print("DEMO DONE — both questions answered.")
        print(f"{'=' * 60}")
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
