#!/usr/bin/env python3
"""T145 -- WHERE CAN AN UNGUARDED json.load ACTUALLY CARRY MONEY?

A `json.load` with no parse_float= is only a MONEY hazard if the file it reads contains a
BARE JSON NUMBER carrying an amount.  A money value stored as a JSON STRING -- which is the
form this program's captures overwhelmingly use, e.g. `"emi": "1713.21"` -- is untouched by
parse_float, so adding parse_float there is churn, exactly as T207 found at
measure-other-sites.py:85,86.

This instrument therefore measures the CORPUS rather than arguing about the code: for every
tracked *.json under .softhouse/, it finds every leaf that was a bare JSON FLOAT token and
reports its key path.  A file with zero money-bearing float leaves cannot be the reason any
site is a hazard, whatever that site's source looks like.

NO MONEY IS COMPUTED HERE.  Floats are read back as Decimal via parse_float=Decimal purely so
that "was this token a float?" is decidable; the exact source text is recovered from the
Decimal and reprinted, never rounded, never summed.

Selector printed with every figure (P-67 / P-69).
"""
import json
import os
import re
import subprocess
import sys
from decimal import Decimal

# Broad, deliberately over-inclusive: this is a HAZARD screen, so a false positive costs a
# read and a false negative costs a money defect.
MONEY_RE = re.compile(
    r"amount|balance|principal|interest|fee|penalt|charge|due|paid|outstanding|repay|"
    r"emi|total|price|money|credit|debit|rate|factor|disburs|instal|overdue|arrear|"
    r"currency|minor|value|sum|cost|tax|accrual|posting|entry",
    re.I,
)


def tracked_json(root):
    out = subprocess.run(["git", "ls-files", "--", ".softhouse"], cwd=root,
                         capture_output=True, text=True, check=True).stdout.split("\n")
    return sorted(p for p in out if p.endswith(".json"))


def walk(node, path, sink):
    if isinstance(node, Decimal):
        sink.append((path, node))
    elif isinstance(node, dict):
        for k, v in node.items():
            walk(v, path + [str(k)], sink)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + ["[%d]" % i], sink)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    files = tracked_json(root)
    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                         capture_output=True, text=True).stdout.strip()

    print("SELECTOR (population): git ls-files -- .softhouse | grep '\\.json$'")
    print("SELECTOR (float leaf): json.load(parse_float=Decimal); any leaf whose parsed type")
    print("                       is Decimal WAS a bare JSON float token in the source.")
    print("SELECTOR (money-ish):  the leaf's key path matches /%s/i" % MONEY_RE.pattern[:60] + ".../")
    print("REV: %s" % rev)
    print()

    scanned = skipped = 0
    per_file = []
    for f in files:
        p = os.path.join(root, f)
        try:
            with open(p, encoding="utf-8") as fh:
                doc = json.load(fh, parse_float=Decimal)
        except Exception as e:
            skipped += 1
            print("SKIPPED (not loadable): %s -- %s" % (f, type(e).__name__))
            continue
        scanned += 1
        sink = []
        walk(doc, [], sink)
        if not sink:
            continue
        moneyish = [(pa, v) for pa, v in sink if MONEY_RE.search(".".join(pa))]
        per_file.append((f, len(sink), moneyish))

    print()
    print("JSON files scanned                                   : %d" % scanned)
    print("JSON files not loadable (excluded, stated not hidden) : %d" % skipped)
    print("JSON files containing >=1 BARE FLOAT token           : %d" % len(per_file))
    hz = [x for x in per_file if x[2]]
    print("JSON files where a bare float sits under a MONEY-ISH key: %d" % len(hz))
    print()
    print("==== THE HAZARD SET -- these are the only files an unguarded json.load can")
    print("==== turn into a binary double carrying an amount.")
    for f, n, moneyish in sorted(hz, key=lambda x: -len(x[2])):
        print("  %s   (%d float leaves, %d money-ish)" % (f, n, len(moneyish)))
        seen = set()
        for pa, v in moneyish:
            key = ".".join(pa[-2:])
            if key in seen:
                continue
            seen.add(key)
            print("        %-70s = %s" % (".".join(pa), v))
            if len(seen) >= 8:
                print("        ... (%d more money-ish leaves in this file)" % (len(moneyish) - 8))
                break
    print()
    print("==== float-bearing but NOT money-ish (recorded so 'not found' is a statement")
    print("==== about the SEARCH, not a claim of absence)")
    for f, n, moneyish in sorted(per_file, key=lambda x: x[0]):
        if not moneyish:
            print("  %s   (%d float leaves, none under a money-ish key)" % (f, n))
    return 0


sys.exit(main())
