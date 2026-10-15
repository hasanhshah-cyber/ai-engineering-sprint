# Day 5 — Agent That Talks to a Real App (GitHub)

Day 3's agent could only use its own two tools. Day 4's agent could
remember. Day 5's agent talks to a real app: GitHub.

Ask it about a GitHub user or repo, and it calls the **public GitHub API**
(no login, no token) and answers from live data. Same Claude tool-use
pattern as Day 3, same JSON-file memory as Day 4.

## What it does

Three tools, one agent:

- `search_docs` — Day 1 retrieval. Searches the sprint docs.
- `summarize_text` — Day 2 summarizer. Claude-written summary.
- `github_lookup` — **NEW.** Looks up a real GitHub user, or one of their
  repos. Returns live facts: bio, repo list, languages, stars,
  descriptions, license, topics.

Memory works the same as Day 4: recent conversation is remembered
across runs, and `remember that ...` saves a fact for later.

If the GitHub API call fails, the agent says so honestly. It never
invents repo data. If a user or repo does not exist, it says "not found"
instead of guessing.

## How to run it on a Mac

You need Python 3 (already on every Mac) and an Anthropic API key.
The key is only for Claude. The GitHub lookup needs no key at all.

1. Open Terminal and go to this folder:
   `cd ai-engineering-sprint/day-5-github-agent`

2. Check Python:
   `python3 --version`
   (Any Python 3.9 or newer works. Nothing to install — standard
   library only.)

3. Set your API key as an environment variable. Never paste your key
   into chat, a file, or the repo:
   `export ANTHROPIC_API_KEY='your-key-here'`

   To keep it for every new Terminal window, add that same line to
   `~/.zshrc` once, then restart Terminal.

4. Ask it something:
   `python3 agent.py "what repos does hasanhshah-cyber have?"`
   `python3 agent.py "what is in the ai-engineering-sprint repo?"`
   `python3 agent.py "remember that my favorite tool is the GitHub lookup"`

5. First run creates `memory.json` next to the script. It is in
   `.gitignore`, so it never gets committed.

## Example conversation (real output)

The trace below is what the terminal shows. The `RESULT` lines are the
real output of the GitHub tool, run live against the public GitHub API
on Oct 15, 2026. (Repo stats change over time, so your numbers may
differ slightly.)

```
$ python3 agent.py "what repos does hasanhshah-cyber have?"

Q: what repos does hasanhshah-cyber have?

TOOL: github_lookup({"username": "hasanhshah-cyber"})

RESULT: User: hasanhshah-cyber (Hasan Shah)
Bio: Management Information Systems Graduate | Client-Facing Technical Delivery & Data Accuracy | SQL, Python, Applied Databa...
Public repos: 5 | Followers: 0 | Following: 0 | Account created: 2026-08-03T03:18:25Z

Most recently updated repos:
- ai-engineering-sprint | Python | stars: 0 | no description
- Dealer-Network-Analytics- | Python | stars: 0 | SQL analysis of a synthetic auto dealer network — market share, dealer ranking, YoY growth, and expansion (whitespace) a...
- client-performance-database | Python | stars: 0 | SQL + Python data project modeling a lead-gen agency's client, campaign, and lead performance data — includes schema des...
- uds-diagnostic-simulator | Python | stars: 0 | Python simulation of a UDS (ISO 14229) diagnostic session between a tester and an ECU — session control, security access...
- robotframework-api-testing | RobotFramework | stars: 0 | Keyword-driven API test suite built with Robot Framework, demonstrating positive/negative testing and reusable keyword a...

ANSWER: (Claude answers from the tool result — e.g. a short plain list
of the 5 repos with their languages.)
```

And for one specific repo:

```
$ python3 agent.py "what is in the ai-engineering-sprint repo?"

TOOL: github_lookup({"username": "hasanhshah-cyber", "repo": "ai-engineering-sprint"})

RESULT: Repo: hasanhshah-cyber/ai-engineering-sprint
Description: no description
Language: Python | Stars: 0 | Forks: 0 | Open issues: 0
License: none listed | Topics: none
Created: 2026-10-11T12:55:45Z | Updated: 2026-10-14T20:47:53Z
URL: https://github.com/hasanhshah-cyber/ai-engineering-sprint
```

When something does not exist, it says so instead of guessing:

```
$ python3 agent.py "what repos does this-user-definitely-does-not-exist-xyz123 have?"
RESULT: Not found on GitHub (404). Check the username or repo spelling.
```

## How it works (the simple version)

Like a kid asking a librarian a question, except the librarian is
allowed to use the phone. You ask a question. Claude decides which tool
answers it. If the question is about GitHub, Claude calls
`github_lookup`, the code fetches live data from `api.github.com`,
Claude reads the result, and you get a short plain answer.

## Limits to know

- The public GitHub API allows 60 requests per hour without a login.
  If you hit it, the tool says so. Wait a bit and try again.
- The agent only reads public GitHub data. It cannot see private repos,
  and it cannot change anything on GitHub.
- `memory.json` is local to your machine. Deleting it wipes the
  agent's memory.

## Files

- `agent.py` — the agent loop (Claude tool use + memory).
- `tools.py` — the three tools: search, summarize, GitHub lookup.
- `memory.py` — short-term + long-term memory in `memory.json`.
- `docs/sprint-overview.md` — small doc set so `search_docs` works.
- `requirements.txt` — none needed (Python standard library only).
- `.gitignore` — keeps `memory.json`, caches, and secrets out of git.
