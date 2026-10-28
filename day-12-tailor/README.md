# Day 12: Tailor and Stage Tool

Week 3, Day 2 of the AI engineering sprint. Step 2 of the staging-only
overnight job agent, after Day 11's scanner and filter.

## What it does

Takes one role (JSON) plus a verified-evidence list (JSON) and produces
a staging report, nothing more:

- Pay check: $70,000 floor, $95,000 preference. Pay unknown is never
  floor-checked or assumed.
- Geography check: remote US, or hybrid Illinois only.
- Keyword split: matched (verified evidence only), gaps (learn, do not
  claim), and do-not-claim flags (for example GoHighLevel, Java, C++).
- A cover-letter outline built only from verified evidence.
- A hard STOP gate in every output.

## What it does NOT do

No applying, no submitting, no accounts, no attestations, no recruiter
messages, no emails. A real role still needs Hasan's own per-role go
before anything beyond a staging report is built or submitted.

## Run it

```bash
python3 tailor.py role_test.json evidence.json output
```

Output: `output/staged.json` and `output/staging_report.md`.
Plain Python 3 stdlib only, no venv, no extra packages.

## Verified test, Oct 28, 2026

Synthetic test role only, not a real application: TEST Implementation
Specialist at TestCo, Remote US, $90,000-$110,000.
Result in the VM: matched=2, gaps=6, flags=2 (GoHighLevel, Java).
Pay: above floor, below $95,000 preference. Geo: pass, remote US.
Nothing was submitted, and no message was sent, in this build.
