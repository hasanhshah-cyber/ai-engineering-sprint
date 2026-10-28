#!/usr/bin/env python3
"""Day 12: tailor / stage tool, staging only.

Takes one role (JSON) and Hasan's verified evidence (JSON) and produces
a staging report: matched keywords, gaps, do-not-claim flags, pay and
geography checks, and a cover-letter outline built only from verified
evidence.

What it does NOT do, by design:
- No applying, no submitting, no accounts, no attestations.
- No recruiter messages, no emails.
- No fabricated experience, metrics, or tool claims.
- A real role still needs Hasan's own per-role go before anything
  beyond this staging report is built or submitted.

Usage:
    python3 tailor.py role.json evidence.json output
    python3 tailor.py role_test.json evidence.json output
"""
import json
import sys
from pathlib import Path

FLOOR = 70000
PREFERENCE = 95000


def pay_status(role):
    low = role.get("pay_min")
    high = role.get("pay_max")
    if low is None:
        return "pay unknown: never floor-checked, never assumed"
    if high is not None and high < FLOOR:
        return "below floor: fully below $70,000"
    if low < FLOOR:
        return "partly below floor: range starts below $70,000"
    if low < PREFERENCE:
        return "above floor, below $95,000 preference"
    return "at or above $95,000 preference"


def geo_status(role):
    loc = (role.get("location") or "").lower()
    if "remote" in loc:
        return "pass: remote US"
    if "hybrid" in loc and "illinois" in loc:
        return "pass: hybrid Illinois"
    return "reject for staging: not remote US or hybrid Illinois"


def main():
    if len(sys.argv) != 4:
        print("usage: python3 tailor.py role.json evidence.json output_dir")
        return 2
    role = json.loads(Path(sys.argv[1]).read_text())
    evidence = json.loads(Path(sys.argv[2]).read_text())
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)

    verified = [e.lower() for e in evidence["verified"]]
    do_not_claim = [e.lower() for e in evidence["do_not_claim"]]

    matched, gaps, flags = [], [], []
    for kw in role.get("keywords", []):
        k = kw.lower()
        if k in do_not_claim:
            flags.append(kw)
        elif any(k in v or v in k for v in verified):
            matched.append(kw)
        else:
            gaps.append(kw)

    report = {
        "role": role.get("title"),
        "company": role.get("company"),
        "location": role.get("location"),
        "pay": role.get("pay_text", "unverified"),
        "pay_status": pay_status(role),
        "geo_status": geo_status(role),
        "matched_keywords": matched,
        "gaps_to_learn_not_claim": gaps,
        "do_not_claim_flags": flags,
        "verified_bullets_used": evidence["verified"],
        "gate": "STOP. Staging only. No submit, no attestation, no message. "
                "A real role needs Hasan's per-role go first.",
    }
    (out / "staged.json").write_text(json.dumps(report, indent=2))

    lines = [
        f"# Staging report: {role.get('title')} at {role.get('company')}",
        "",
        f"Location: {role.get('location')} - {report['geo_status']}",
        f"Pay: {report['pay']} - {report['pay_status']}",
        "",
        "## Matched keywords (verified evidence only)",
    ]
    lines += [f"- {m}" for m in matched] or ["- none"]
    lines += ["", "## Gaps: learn, do not claim"]
    lines += [f"- {g}" for g in gaps] or ["- none"]
    lines += ["", "## Do NOT claim"]
    lines += [f"- {f}" for f in flags] or ["- none"]
    lines += [
        "",
        "## Cover-letter outline (verified evidence only)",
        "- Finds the broken process, then builds and rolls out the fix.",
        "- One client rollout at Pinnacle Web Co., plus AI automation work",
        "  (voice agents, webhook pipelines, SMS booking flows) that can be",
        "  explained live.",
        "- No tool, year count, or metric is claimed unless it is in the",
        "  verified list above.",
        "",
        "## Gate",
        report["gate"],
    ]
    (out / "staging_report.md").write_text("\n".join(lines) + "\n")
    print(f"Staged {role.get('title')} at {role.get('company')}: "
          f"matched={len(matched)}, gaps={len(gaps)}, flags={len(flags)}")
    print(f"Pay: {report['pay_status']}")
    print(f"Geo: {report['geo_status']}")
    print("STOP: staging only, nothing submitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
