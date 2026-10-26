#!/usr/bin/env python3
"""Day 11: job scanner and filter.

One job only: take a list of roles and split it into keep, review, and
reject buckets, using Hasan's standing rules.

Rules (standing, Oct 2026):
- Geography: remote anywhere in the US, plus hybrid roles in Illinois
  only. Fully on-site roles are rejected, as are hybrid roles outside
  Illinois.
- Pay floor: $70,000 is the lowest he will take. A role below that is
  flagged, not silently kept, and only wins as a get-in move with
  excellent fit or his explicit per-role exception.
- Drift: pure sales, pure project management, support-only, customer
  success, and QA titles are rejected as off the implementation arrow.
  Pre-sales is a bridge flag, not an automatic keep or reject.
- Pay unknown: kept for review, never floor-checked, never assumed.

Input: a JSON file, one array of role objects:
  {"title": str, "company": str, "location": str,
   "pay_min": number or null, "pay_max": number or null,
   "pay_unit": "year" or "hour", "link": str, "note": str}

Output: scanned.json (all buckets) and morning_list.md (readable list).
No applying, no tailoring, no messaging, no submitting. This is step 1
of the Week 3 staging agent only.
"""

import json
import re
import sys
from pathlib import Path

FLOOR = 70000
HOURS_PER_YEAR = 2080

ILLINOIS_MARKERS = ("illinois", "chicago", "naperville", "oswego", "aurora", " il")

# Titles that are drift on their own, not implementation work.
DRIFT_TITLES = (
    "account executive",
    "sales representative",
    "sales rep",
    "customer success",
    "support specialist",
    "support engineer",
    "quality assurance",
    "qa engineer",
)


def annual_pay(pay_min, pay_max, pay_unit):
    """Return (min, max) in annual dollars, or (None, None)."""
    if pay_min is None and pay_max is None:
        return None, None
    factor = HOURS_PER_YEAR if pay_unit == "hour" else 1
    lo = pay_min * factor if pay_min is not None else None
    hi = pay_max * factor if pay_max is not None else None
    return lo, hi


def geography(location):
    """Return ('keep', reason) or ('reject', reason) or ('review', reason)."""
    loc = location.lower()
    if "remote" in loc and ("canada" in loc or "us" in loc or "usa" in loc
                            or "united states" in loc or loc.strip() == "remote"):
        # Remote USA/Canada still covers remote US work.
        return "keep", "Remote US"
    if "hybrid" in loc:
        if any(m in loc for m in ILLINOIS_MARKERS):
            return "keep", "Hybrid Illinois"
        if "remote" in loc:
            # e.g. "Chicago, IL, Hybrid/Remote": the Illinois part keeps it.
            return "keep", "Hybrid Illinois"
        return "reject", "Hybrid outside Illinois"
    if "on-site" in loc or "onsite" in loc or "in office" in loc:
        return "reject", "Fully on-site"
    return "review", "Location unclear, check before pursuing"


def drift(title):
    """Return 'reject', 'bridge', 'senior', or None."""
    t = title.lower()
    if "pre-sales" in t or "presales" in t or "pre sales" in t:
        return "bridge"
    if any(d in t for d in DRIFT_TITLES):
        return "reject"
    if t.strip() == "project manager" or "project manager" in t and "implementation" not in t:
        return "reject"
    if t.startswith("senior") and ("strategic" in t or "director" in t):
        return "senior"
    return None


def scan_role(role):
    """Return (bucket, flags, annual_min, annual_max) for one role."""
    flags = []
    lo, hi = annual_pay(role.get("pay_min"), role.get("pay_max"),
                         role.get("pay_unit", "year"))
    if role.get("pay_unit") == "hour":
        flags.append("Hourly pay converted at 2080 hours/year")
    if lo is None:
        flags.append("Pay unverified, cannot floor-check")
    elif hi is not None and hi < FLOOR:
        flags.append("Below $70,000 floor")
    elif lo < FLOOR:
        flags.append("Range starts below $70,000 floor")

    geo, geo_reason = geography(role.get("location", ""))
    flags.append(geo_reason)
    if geo == "reject":
        return "rejected", flags, lo, hi

    d = drift(role.get("title", ""))
    if d == "reject":
        return "rejected", flags + ["Drift role, off implementation arrow"], lo, hi
    if d == "bridge":
        return "bridge_review", flags + ["Sales-facing bridge, review before pursuing"], lo, hi
    if d == "senior":
        return "review", flags + ["Senior stretch, review before pursuing"], lo, hi
    if geo == "review" or lo is None:
        return "review", flags, lo, hi
    if lo is not None and hi is not None and hi < FLOOR:
        return "below_floor", flags, lo, hi
    if lo is not None and lo < FLOOR:
        return "review", flags, lo, hi
    return "keep", flags, lo, hi


def pay_label(lo, hi, unit):
    if lo is None and hi is not None:
        return f"Up to ${hi:,.0f}/yr (no minimum stated)"
    if lo is None:
        return "Pay unknown"
    if hi is None:
        return f"${lo:,.0f}+/yr"
    if lo == hi:
        return f"${lo:,.0f}/yr"
    return f"${lo:,.0f}-${hi:,.0f}/yr"


def main(argv):
    if len(argv) != 3:
        print("Usage: scanner.py roles.json output_dir", file=sys.stderr)
        return 2
    roles = json.loads(Path(argv[1]).read_text())
    out_dir = Path(argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    buckets = {"keep": [], "review": [], "bridge_review": [],
               "below_floor": [], "rejected": []}
    for role in roles:
        bucket, flags, lo, hi = scan_role(role)
        buckets[bucket].append({
            "title": role["title"],
            "company": role["company"],
            "location": role["location"],
            "pay": pay_label(lo, hi, role.get("pay_unit", "year")),
            "pay_min_annual": lo,
            "link": role.get("link", ""),
            "note": role.get("note", ""),
            "flags": flags,
        })

    # Rank kept roles by known pay, highest first; unknown pay last.
    buckets["keep"].sort(key=lambda r: (r["pay_min_annual"] is None,
                                        -(r["pay_min_annual"] or 0)))

    (out_dir / "scanned.json").write_text(json.dumps(buckets, indent=2))

    lines = ["# Day 11 morning list", ""]
    for heading, key in [
        ("Keep", "keep"),
        ("Review (pay unknown, senior stretch, or range starts below floor)", "review"),
        ("Bridge review (sales-facing, decide per role)", "bridge_review"),
        ("Below floor (get-in move only, needs explicit exception)", "below_floor"),
        ("Rejected", "rejected"),
    ]:
        lines.append(f"## {heading}")
        if not buckets[key]:
            lines.append("- None")
        for r in buckets[key]:
            lines.append(f"- **{r['title']}**, {r['company']} ({r['location']}) "
                         f"- {r['pay']} - {'; '.join(r['flags'])}")
            if r["link"]:
                lines.append(f"  {r['link']}")
        lines.append("")
    (out_dir / "morning_list.md").write_text("\n".join(lines))

    counts = {k: len(v) for k, v in buckets.items()}
    print(f"Scanned {len(roles)} roles: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
