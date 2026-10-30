#!/usr/bin/env python3
"""Day 13: pipeline runner, staging only.

Step 3 of the staging-only overnight job agent. It chains the tools
already built, it does not replace them:

1. Day 11 scanner: roles -> keep / review / bridge_review /
   below_floor / rejected.
2. Day 12 tailor: every keep, review, and bridge_review role is
   staged individually, from verified evidence only.
3. This runner: collects those staging reports into one morning
   pipeline report.

Below-floor and rejected roles are listed as skipped, never staged.

What it does NOT do, by design:
- No applying, no submitting, no accounts, no attestations.
- No recruiter messages, no emails.
- No fabricated experience, metrics, or tool claims.
- A real role still needs Hasan's own per-role go before anything
  beyond a staging report is built or submitted.

Usage:
    python3 pipeline.py roles.json evidence.json output_dir
    python3 pipeline.py roles_test.json evidence.json output
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DEFAULT_SCANNER = ROOT / "sprint-day11" / "day-11-job-scanner" / "scanner.py"
DEFAULT_TAILOR = ROOT / "sprint-day12" / "day-12-tailor" / "tailor.py"
STAGED_BUCKETS = ("keep", "review", "bridge_review")


def slug(text):
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"failed: {' '.join(str(c) for c in cmd)}")
    return result.stdout


def main():
    if len(sys.argv) not in (4, 6):
        print("usage: python3 pipeline.py roles.json evidence.json output_dir "
              "[scanner.py tailor.py]", file=sys.stderr)
        return 2
    roles_path, evidence_path, out_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    scanner = Path(sys.argv[4]) if len(sys.argv) == 6 else DEFAULT_SCANNER
    tailor = Path(sys.argv[5]) if len(sys.argv) == 6 else DEFAULT_TAILOR
    if not scanner.exists():
        print(f"scanner not found: {scanner}", file=sys.stderr)
        return 2
    if not tailor.exists():
        print(f"tailor not found: {tailor}", file=sys.stderr)
        return 2

    roles = json.loads(roles_path.read_text())
    by_key = {(r["title"], r["company"]): r for r in roles}
    out = out_path
    out.mkdir(parents=True, exist_ok=True)

    scan_out = out / "scan"
    run([sys.executable, str(scanner), str(roles_path), str(scan_out)])
    scanned = json.loads((scan_out / "scanned.json").read_text())

    staged = []
    for bucket in STAGED_BUCKETS:
        for item in scanned.get(bucket, []):
            original = by_key.get((item["title"], item["company"]))
            if original is None:
                continue
            role = {
                "title": original["title"],
                "company": original["company"],
                "location": original["location"],
                "pay_min": original.get("pay_min"),
                "pay_max": original.get("pay_max"),
                "pay_text": item["pay"],
                "keywords": original.get("keywords", []),
            }
            role_path = out / f"role-{slug(original['title'])}-{slug(original['company'])}.json"
            role_path.write_text(json.dumps(role, indent=2))
            stage_dir = out / "staged" / f"{slug(original['title'])}-{slug(original['company'])}"
            run([sys.executable, str(tailor), str(role_path), str(evidence_path), str(stage_dir)])
            report = json.loads((stage_dir / "staged.json").read_text())
            report["bucket"] = bucket
            staged.append(report)

    counts = {k: len(v) for k, v in scanned.items()}
    summary = {
        "scanned": counts,
        "staged_roles": len(staged),
        "skipped_buckets": ["below_floor", "rejected"],
        "gate": "STOP. Staging only. No submit, no attestation, no message. "
                "A real role needs Hasan's per-role go first.",
    }
    (out / "pipeline.json").write_text(json.dumps(summary, indent=2))

    lines = ["# Day 13 pipeline report", ""]
    lines.append(f"Scanned: {counts.get('keep', 0)} keep, "
                 f"{counts.get('review', 0)} review, "
                 f"{counts.get('bridge_review', 0)} bridge review, "
                 f"{counts.get('below_floor', 0)} below floor, "
                 f"{counts.get('rejected', 0)} rejected.")
    lines.append(f"Staged: {len(staged)} roles. "
                 "Below-floor and rejected roles were not staged.")
    lines.append("")
    for report in staged:
        lines.append(f"## {report['role']} at {report['company']} "
                     f"({report['bucket']})")
        lines.append(f"Location: {report['location']} - {report['geo_status']}")
        lines.append(f"Pay: {report['pay']} - {report['pay_status']}")
        lines.append(f"Matched: {', '.join(report['matched_keywords']) or 'none'}")
        lines.append(f"Gaps, learn not claim: "
                     f"{', '.join(report['gaps_to_learn_not_claim']) or 'none'}")
        lines.append(f"Do NOT claim: "
                     f"{', '.join(report['do_not_claim_flags']) or 'none'}")
        lines.append("")
    lines.append("## Gate")
    lines.append(summary["gate"])
    (out / "pipeline_report.md").write_text("\n".join(lines) + "\n")

    print(f"Scanned: {counts}")
    print(f"Staged: {len(staged)} roles")
    print("STOP: staging only, nothing submitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
