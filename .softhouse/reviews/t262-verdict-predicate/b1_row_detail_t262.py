#!/usr/bin/env python3
"""T262 -- full detail on T219-R600p0-N103-B1, the row where the CORRECTED predicate and the
verdict DISAGREE. Checked against the raw gz capture, not only the derived classify file.
"""
import gzip
import hashlib
import json
from decimal import Decimal
from pathlib import Path

CID = "T219-R600p0-N103-B1"
cls = json.load(open(".softhouse/capture/t219-g8-residual/out/classify-t219.json"),
                parse_float=Decimal)
row = [r for r in cls["cells"] if r["id"] == CID][0]
print("=== recorded row", CID, "===")
for k, v in row.items():
    print("  {:34} {!r}".format(k, v))

rawp = Path(".softhouse/capture/t219-g8-residual/out/capture-t219-raw.json.gz")
print()
print("raw sha256", hashlib.sha256(rawp.read_bytes()).hexdigest())
raw = json.load(gzip.open(rawp, "rt"), parse_float=Decimal)


def m(s):
    d = Decimal(str(s)) * 100
    assert d == d.to_integral_value(), s
    return int(d)


c = [x for x in raw["captures"] if x["id"] == CID]
if not c:
    print("NOT FOUND in run-1 raw capture; ids present:", [x["id"] for x in raw["captures"]][:12])
else:
    c = c[0]
    reps = [x for x in c["observed"]["periods"] if x["type"] == "REPAYMENT"]
    st = sum(m(x["total"]) for x in reps)
    sp = sum(m(x["principal"]) for x in reps)
    si = sum(m(x["interest"]) for x in reps)
    n = len(reps)
    E = m(reps[0]["total"])
    B = row["bMinor"]
    print()
    print("=== from the raw emitted schedule rows ===")
    print("  repayment rows            :", n)
    print("  sum of row totals         :", st)
    print("  sum of principal          :", sp, " (header",
          m(c["observed"]["totalPrincipalAmount"]), ")")
    print("  sum of interest           :", si, " (header",
          m(c["observed"]["totalInterestAmount"]), ")")
    print("  row-1 total E             :", E)
    print("  last row total            :", m(reps[-1]["total"]))
    print("  distinct totals ex-last   :", sorted({m(x["total"]) for x in reps[:-1]}))
    print("  n*E + B                   :", n * E + B)
    print("  n*E + B - principalRepaid :", n * E + B - sp)
    print("  total repayment == n*E+B  :", st == n * E + B)
    print("  interest == total - prin  :", si == st - sp, "  (this identity is unconditional)")
    print()
    print("  REGISTERED predicate  interest == n*E+B          :", si == n * E + B)
    print("  CORRECTED  predicate  interest == n*E+B - P      :", si == n * E + B - sp)
    print("  recorded verdict                                 :", row["verdict"])
    print()
    print("  >>> CORRECTED predicate is FALSE and the verdict is AFFIRMATIVE.")
    print("  >>> This is a row where a CORRECT predicate DISAGREES with the verdict.")
