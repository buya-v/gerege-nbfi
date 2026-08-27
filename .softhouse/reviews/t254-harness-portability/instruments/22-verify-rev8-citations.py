#!/usr/bin/env python3
"""T254 reviewer instrument: are DEC-2 rev-8's conformance.sh citations LIVE
and CORRECT against conformance.sh as it stands on main today?

This is the load-bearing step for the citation-damage finding. A shifted line
number only matters if the number was RIGHT before the shift. So: resolve every
cited line, print what is actually there, and let the reader judge.

Then show what the SAME citation would point at after a +52 insertion at line
570 (the cloud diff's shape).

P-80: nothing is inferred from a grep exit code; lines are indexed out of an
enumerated list. Out-of-range is reported as OUT-OF-RANGE, never as empty.

Usage: 22-verify-rev8-citations.py <conformance.sh-at-main> <shift_from> <shift_by>
"""
import sys

conf_path, shift_from, shift_by = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
lines = open(conf_path, encoding="utf-8", errors="replace").read().splitlines()
N = len(lines)

# The citation set measured by instruments 20 + 21 at softhouse/T255-dec2-rev8
# (ed686d7). Ranges are given as (start, end); single lines as (n, n).
CITES = [
    ("DEC-2:96",   1152, 1187),
    ("DEC-2:428",  1254, 1254),   # prose form: "`conformance.sh`'s -context append 894 -> 1254"
    ("DEC-2:1059", 1152, 1187),
    ("DEC-2:1116", 1189, 1213),
    ("DEC-2:1773",  718,  718),
    ("DEC-2:2470", 1254, 1254),
    ("DEC-2:2769", 1152, 1187),
    ("DEC-2:2903", 1115, 1116),
    ("DEC-2:3207", 1115, 1116),
    ("DEC-2:3423", 1189, 1213),
]

def get(n):
    if 1 <= n <= N:
        return lines[n - 1]
    return "<OUT-OF-RANGE>"

print("=" * 78)
print("DEC-2 rev-8 conformance.sh citations, resolved against MAIN")
print(f"file: {conf_path}  ({N} lines)")
print(f"hypothetical: insert {shift_by:+d} lines at {shift_from} (the CLOUD diff shape)")
print("=" * 78)

seen = set()
for label, a, b in CITES:
    key = (a, b)
    print(f"\n### {label}  cites conformance.sh:{a}" + (f"-{b}" if b != a else ""))
    print(f"  NOW  {a}: {get(a).strip()[:110]}")
    if b != a:
        print(f"  NOW  {b}: {get(b).strip()[:110]}")
    a2, b2 = (a + shift_by if a >= shift_from else a), (b + shift_by if b >= shift_from else b)
    print(f"  AFTER CLOUD MERGE the same numbers {a}" + (f"-{b}" if b != a else "") +
          " would point at:")
    print(f"       {a}: {get(a).strip()[:110]}   <-- unchanged number, DIFFERENT code")
    print(f"  the cited code MOVED to {a2}" + (f"-{b2}" if b2 != a2 else ""))
    seen.add(key)

print()
print("=" * 78)
print(f"distinct cited RANGES: {len(seen)}   total citations: {len(CITES)}")
print("=" * 78)
