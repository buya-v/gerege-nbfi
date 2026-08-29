#!/usr/bin/env python3
"""T428 -- independent census of the ledger corpus: which vectors carry
`request.product_mappings` rows, i.e. which ones ledger-wrong-mapping-key-ignored
can possibly move, and which predate T391 and must therefore be INERT under it.

Decoded with parse_float=str / parse_int=str. Row counts are obtained with len(),
never by adding anything up.
"""
import json, os, sys

ROOT = sys.argv[1]
VDIR = os.path.join(ROOT, ".softhouse/vectors/ledger")

byclass = {}
rows = []
for name in sorted(os.listdir(VDIR)):
    if not name.endswith(".json"):
        continue
    with open(os.path.join(VDIR, name)) as fh:
        d = json.load(fh, parse_float=str, parse_int=str)
    cls = d.get("class") or d.get("kind") or "?"
    req = d.get("request") or {}
    pm = req.get("product_mappings") or []
    legs = req.get("legs") or []
    slotlegs = [l for l in legs if str(l.get("slot_code", "0")) not in ("0", "")]
    rows.append((d.get("case_id", name), cls, len(pm), len(legs), len(slotlegs)))
    byclass.setdefault(cls, []).append((name, len(pm)))

print("T428 LEDGER VECTOR CENSUS -- product_mappings rows per vector")
print("root:", ROOT)
print()
print("%-62s %-16s %5s %5s %5s" % ("CASE", "CLASS", "PMROW", "LEGS", "SLOT"))
for c, cls, pm, legs, sl in rows:
    print("%-62s %-16s %5d %5d %5d" % (c[:62], cls, pm, legs, sl))
print()
with_pm = [r for r in rows if r[2] > 0]
without = [r for r in rows if r[2] == 0]
print("VECTORS TOTAL              :", len(rows))
print("WITH product_mappings rows :", len(with_pm), [r[0] for r in with_pm])
print("WITHOUT (i.e. PRE-T391)    :", len(without))
print()
print("PRE-T391 BREAKDOWN BY CLASS:")
for cls in sorted(byclass):
    n = len([x for x in byclass[cls] if x[1] == 0])
    print("   %-18s %d" % (cls, n))
