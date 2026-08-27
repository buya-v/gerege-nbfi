#!/usr/bin/env python3
# T246 — ADJACENT-STALENESS sweep.
#
# The third-site sweep for the *I-5 reversal* falsehood came back with exactly two sites.
# This second instrument asks the neighbouring question the same defect class implies:
# DEC-2 revision 5 was ratified BEFORE `A2-15` promoted the first six ledger vectors, so every
# sentence in it that says "no ledger vector exists / is expressible / there is no ledger PASS"
# was TRUE at ratification and may be FALSE now (P-69). Site 1 sits INSIDE such a table.
#
# ENGINE: python3 re only (P-53 / P-75). Calibrated on a known positive and a known negative.
# Fail-CLOSED: assertions raise.
import os, re, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEC2 = os.path.join(REPO, "docs", "adr", "DEC-2-gl-accounting-adapter.md")
assert os.path.isfile(DEC2), "FATAL: DEC-2 unreachable"
lines = open(DEC2, encoding="utf-8").read().splitlines()
print(f"DEC-2: {DEC2}  lines={len(lines)}")
print(f"engine: python3 {sys.version.split()[0]} re")
print()

PATTERNS = [
    ("no-ledger-vector-expressible", r"no\s+`?ledger`?\s+vector[^.]{0,80}(?:expressible|exists?)"),
    ("no-admissible-vector-money-cell", r"no\s+admissible\s+vector[^.]{0,120}"),
    ("none-graded-today", r"none\s+of\s+them\s+can\s+be\s+graded\s+today"),
    ("every-row-answer-NO", r"every\s+row\s+in\s+this\s+table\s+the\s+answer\s+is\s+\*\*NO\*\*"),
    ("no-such-PASS", r"(?:no|there is no)\s+(?:such\s+)?(?:`?ledger`?\s+)?(?:conformance\s+)?PASS"),
    ("nothing-is-graded", r"(?:grades?|graded)\s+(?:nothing|none)\b[^.]{0,80}"),
    ("KNOWN-NEGATIVE", r"ZZZ-NOSUCH-T246-ADJACENT"),
    ("KNOWN-POSITIVE", r"The A2 corpus contains no reversal"),
]

for name, pat in PATTERNS:
    rx = re.compile(pat, re.I)
    hits = [(i + 1, l) for i, l in enumerate(lines) if rx.search(l)]
    print(f"[{name}]  lines: {len(hits)}")
    for n, l in hits:
        m = rx.search(l)
        a, b = max(0, m.start() - 150), min(len(l), m.end() + 200)
        print(f"   L{n:<5} …{l[a:b]}…")
    print()

neg = [i for i, l in enumerate(lines) if "ZZZ-NOSUCH-T246-ADJACENT" in l]
pos = [i for i, l in enumerate(lines) if "The A2 corpus contains no reversal" in l]
assert neg == [], "CALIBRATION FAILED: known negative matched"
assert pos, "CALIBRATION FAILED: known positive missed"
print("=== calibration OK (known negative 0, known positive found) ===")
