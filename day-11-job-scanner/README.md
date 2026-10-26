# Day 11: Job Scanner and Filter

Week 3, Day 1 of the AI engineering sprint. Step 1 of the staging-only
overnight job agent.

## What it does

Takes a JSON list of roles and splits it into keep, review, bridge
review, below floor, and rejected buckets, using Hasan's standing rules:

- Geography: remote anywhere in the US, plus hybrid roles in Illinois
  only. Fully on-site and hybrid outside Illinois are rejected.
- Pay floor: $70,000 is the lowest he will take. Hourly pay is
  converted at 2080 hours per year. A role fully below the floor is
  flagged, not silently kept.
- Drift: pure sales, pure project management, support-only, customer
  success, and QA titles are rejected. Pre-sales is a bridge flag for a
  per-role decision, not an automatic keep or reject.
- Pay unknown: never floor-checked, never assumed. "Up to $X" is shown
  as up to, with no minimum stated.

## What it does NOT do

No applying, no tailoring, no cover letters, no recruiter messages, no
submitting, no attestations. Those are later steps, each with Hasan's
own per-role go.

## Run it

```bash
python3 scanner.py roles_day11_test.json output
```

Output: `output/scanned.json` and `output/morning_list.md`.

## Verified test, Oct 26, 2026

10 roles scanned in the VM: keep=1, review=5, bridge_review=1,
below_floor=1, rejected=2.

- Keep: Ashby Mid-Market Implementation Specialist, Remote USA,
  $140,000-$159,000.
- Below floor: OnPay Implementation Analyst, $25-$30/hr, converted to
  $52,000-$62,400/yr.
- Bridge review: Vyas Consulting Pre-Sales Solution Consultant,
  Chicago hybrid/remote, pay unverified.
- Review: Infinite (up to $90,000, no minimum stated), Buildout
  ($65,000-$70,000), MeridianLink ($58,700-$82,800), Urbint (pay
  unknown), Ashby Senior Strategic ($170,000-$200,000, senior stretch).
- Rejected: both test controls, an Account Executive drift title and a
  fully on-site role, even though both passed on pay.

No role was applied to, and no message was sent, in this build.
