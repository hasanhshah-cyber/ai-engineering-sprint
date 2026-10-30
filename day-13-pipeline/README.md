# Day 13: Pipeline Runner

Week 3, Day 3 of the AI engineering sprint. Step 3 of the staging-only
overnight job agent, after Day 11's scanner and Day 12's tailor.

## What it does

Chains the two tools already built, in order, into one morning report:

1. Day 11 scanner splits roles into keep, review, bridge review,
   below floor, and rejected.
2. Day 12 tailor stages every keep, review, and bridge review role
   from verified evidence only.
3. This runner collects those staging reports into
   `output/pipeline_report.md` and `output/pipeline.json`.

Below-floor and rejected roles are listed as skipped, never staged.

## What it does NOT do

No applying, no submitting, no accounts, no attestations, no recruiter
messages, no emails. A real role still needs Hasan's own per-role go
before anything beyond a staging report is built or submitted.

## Run it

```bash
python3 pipeline.py roles_test.json evidence.json output
```

Plain Python 3 stdlib only, no venv, no extra packages. The scanner
and tailor paths default to the Day 11 and Day 12 folders in this
repo; pass them as extra arguments to point elsewhere.

## Verified test, Oct 29, 2026

Synthetic test roles only, not real applications. Run in the VM:
3 roles scanned (keep=1, bridge review=1, rejected=1), 2 staged.
The rejected drift role was not staged. The keep role matched 2
keywords, with 6 gaps and 2 do-not-claim flags (GoHighLevel, Java).
Nothing was submitted, and no message was sent, in this build.
