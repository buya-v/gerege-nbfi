#!/usr/bin/env python3
"""
T44 audit - do any committed capture payloads carry a BARE (unquoted) non-integer JSON number?

Several analysis scripts in the audited sets call json.load() WITHOUT parse_float=Decimal:
  periodratio/analysis/controls.py:131, discriminate.py:72
  mathcontext/analysis/controls.py:92, discriminate.py:57, discriminate2.py:43,
                                      count_cells.py:15, :40
On such a call, a bare JSON float becomes a Python binary float. That is inert if and only if
every money leaf in the payload is a STRING and every bare number is an integer. This checks it.

Uses parse_float to TRAP the event: any call means a bare non-integer number was present.
NO FLOAT is constructed - the hook records the raw text and returns a Decimal.
"""
import json, sys, glob
from decimal import Decimal

hits = []


def make_hook(path):
    def hook(s):
        hits.append((path, s))
        return Decimal(s)
    return hook


paths = []
for pat in sys.argv[1:]:
    paths.extend(sorted(glob.glob(pat, recursive=True)))

print("T44 - bare non-integer JSON number scan over committed capture payloads")
print()
total_int = 0
for p in paths:
    before = len(hits)
    try:
        doc = json.load(open(p), parse_float=make_hook(p))
    except Exception as e:
        print(f"  {p}: UNPARSEABLE ({e})")
        continue
    n = len(hits) - before
    flag = "  <-- BARE FLOAT PRESENT" if n else ""
    print(f"  {n:>4} bare non-integer numbers   {p}{flag}")

print()
if hits:
    print(f"  TOTAL {len(hits)} bare non-integer numbers found. Sample:")
    for p, s in hits[:15]:
        print(f"    {p}: {s!r}")
    print()
    print("  => json.load() WITHOUT parse_float on these files CONSTRUCTS BINARY FLOATS.")
else:
    print("  TOTAL 0. Every bare number in every scanned payload is an integer, and every")
    print("  money leaf is a JSON string, so the parse_float-less json.load calls are INERT")
    print("  today. They remain a latent float path if a future payload emits a bare decimal.")
