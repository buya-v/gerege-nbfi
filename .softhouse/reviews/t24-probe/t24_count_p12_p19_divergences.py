#!/usr/bin/env python3
"""
T24 / P1-1 — count the D-01 (precision 12) vs D-01-p19 (precision 19) divergences from the RAW
capture file, so the figure in DEC-1 §4.1 and in contract.go's Rounding.SignificantDigits doc is
read out of an observation instead of inherited.

Reads .softhouse/capture/out/capture-raw.json read-only (that directory is owned by T25 this fire;
this script never writes to it).
"""
import json

o = json.load(open(".softhouse/capture/out/capture-raw.json"))
by = {c["id"]: c for c in o["captures"]}
a = by["D-01"]["observed"]
b = by["D-01-p19"]["observed"]
ra = [p for p in a["periods"] if p["type"] == "REPAYMENT"]
rb = [p for p in b["periods"] if p["type"] == "REPAYMENT"]

print("D-01 inputs:      ", json.dumps(by["D-01"]["inputs"], sort_keys=True))
print("D-01-p19 inputs:  ", json.dumps(by["D-01-p19"]["inputs"], sort_keys=True))
print("repayment rows:", len(ra), len(rb))
print("row fields:", sorted(ra[0].keys()))

counts = {}
rows_differing = 0
for x, y in zip(ra, rb):
    d = [k for k in x if x[k] != y[k]]
    if d:
        rows_differing += 1
    for k in d:
        counts[k] = counts.get(k, 0) + 1

print()
print("repayment rows differing in at least one field: %d of %d" % (rows_differing, len(ra)))
for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
    print("   %-28s %d rows" % (k, v))
print()
print("top-level differences:")
for k in a:
    if k != "periods" and a[k] != b[k]:
        print("   %-28s %s -> %s" % (k, a[k], b[k]))
