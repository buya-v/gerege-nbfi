#!/usr/bin/env python3
"""T262 -- independent spot-check of T259's B-1 claim, READ-ONLY.

T259 claims .softhouse/capture/t219-g8-residual/out/classify-t219.json carries the SAME defect on
3 rows / 4 predicate-verdict pairs. Verified here from the bytes, in integer minor units, and the
corrected-predicate test is applied there too -- T259 explicitly declined to do that, warning that
B4499 (principal repaid 1499) must be re-derived rather than assumed.
"""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

P = Path(".softhouse/capture/t219-g8-residual/out/classify-t219.json")
print("file  ", P)
print("sha256", hashlib.sha256(P.read_bytes()).hexdigest())
doc = json.load(open(P), parse_float=Decimal)
print("top-level keys:", list(doc.keys()))

AFF = {"AS PREDICTED", "AS_PREDICTED", "PASS", "CONFIRMED", "REPRODUCED", "OK", "HELD"}
pairs = []
rows_total = 0
for ck, cv in doc.items():
    if not isinstance(cv, list):
        continue
    for i, row in enumerate(cv):
        if not isinstance(row, dict):
            continue
        rows_total += 1
        vk = [k for k, v in row.items() if ("verdict" in k.lower() or k.lower().endswith("status"))
              and isinstance(v, str)]
        aff = [k for k in vk if row[k].strip().upper() in AFF]
        fp = [k for k, v in row.items()
              if isinstance(v, bool) and v is False and k.startswith("P") and "_" in k
              and k.split("_", 1)[0][1:].isdigit()]
        if aff and fp:
            for k in fp:
                pairs.append((ck, i, row.get("id", "?"), k, {a: row[a] for a in aff}))

print("rows inspected:", rows_total)
print("DISAGREEING pairs found:", len(pairs))
print("distinct rows:", len({p[2] for p in pairs}))
for ck, i, rid, k, av in pairs:
    print("  {}[{}] {:28} {:34} verdict={}".format(ck, i, rid, k, av))

print()
print("Now the money: apply the CORRECTED conjunct to every carrier, integer minor units only.")
KEY = "P2_totalInterestEqualsNEplusB"
cells = doc.get("cells", [])
carriers = [r for r in cells if KEY in r]
print("cells:", len(cells), " carriers of", KEY + ":", len(carriers))
if carriers:
    print("  {:30} {:>6} {:>7} {:>7} {:>7} {:>9} {:>9} {:>9} {:>6} {:>6} {:>14} {:>7} {:>8}".format(
        "id", "n", "E_obs", "B", "P_rep", "nE+B", "nE+B-P", "int_obs", "REG", "CORR",
        "verdict", "agrREG", "agrCORR"))
aR = aC = 0
for r in carriers:
    n = r["n"]
    E = r.get("observedRow1TotalMinor")
    B = r["bMinor"]
    Pp = r.get("observedPrincipalMinor")
    I = r.get("observedInterestMinor")
    if None in (E, Pp, I):
        print("  {:30} SKIPPED -- missing a field: E={} P={} I={}".format(r.get("id"), E, Pp, I))
        continue
    for v in (n, E, B, Pp, I):
        assert type(v) is int, (r.get("id"), v, type(v))
    tot = n * E + B
    reg = (I == tot)
    corr = (I == tot - Pp)
    assert reg == r[KEY], ("recompute != recorded", r.get("id"), reg, r[KEY])
    vaff = str(r.get("verdict", "")).strip().upper() in AFF
    aR += (reg == vaff)
    aC += (corr == vaff)
    print("  {:30} {:6d} {:7d} {:7d} {:7d} {:9d} {:9d} {:9d} {:>6} {:>6} {:>14} {:>7} {:>8}".format(
        r["id"], n, E, B, Pp, tot, tot - Pp, I, str(reg), str(corr), r.get("verdict"),
        str(reg == vaff), str(corr == vaff)))
print()
print("  AGREEMENT under REGISTERED predicate : {} of {}".format(aR, len(carriers)))
print("  AGREEMENT under CORRECTED  predicate : {} of {}".format(aC, len(carriers)))
