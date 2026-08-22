#!/usr/bin/env python3
"""T219 — does the LIVE reference oracle still return, cell for cell, what the three PROMOTED
G-8 vectors say it returns?

READ-ONLY. This file opens `.softhouse/vectors/loanschedule/*.json` for reading and writes nothing
there. It compares T219's own run-1 observation (a fresh capture under NEW tenant ids) against the
committed `expect` block of each promoted vector, field by field.

THE FIELD MAP IS THE WHOLE POINT AND IT IS EXPLICIT (P-72). The raw capture and the vector do NOT
share field names: the capture emits the oracle's own decimal strings under `type` / `principal` /
`interest` / `balance`, the vector emits the frozen contract's INTEGER MINOR UNITS under `kind` /
`principal_minor` / `interest_minor` / `outstanding_principal_minor`. An earlier revision of this
file compared the two by name and reported "REPRODUCED" having compared ZERO cells. It is
calibrated below: a deliberate corruption of one observed cell MUST make the comparison fail, and
the script asserts that before it reports anything.

NO FLOATING POINT on any decision path: every money value is an integer number of minor units,
obtained through Decimal and asserted integral.

The oracle is the Fineract reference implementation at pinned commit 426a23544e…; Oracle Database
is a prohibited product and appears nowhere in this work.
"""
import copy
import json
import sys
from decimal import Decimal

CAP = sys.argv[1]
VDIR = sys.argv[2]

PAIRS = [
    ("T219-R600p0-N103-B1", "T116-G8-CLEAN-nonexempt-mnt0pt01-103x600pct.json"),
    ("T219-R600p0-N104-B1", "T116-G8-FAMB-nonamortizing-mnt0pt01-104x600pct.json"),
    ("T219-R600p0-N108-B1", "T116-G8-FAMB-nonamortizing-mnt0pt01-108x600pct.json"),
]

# vector field  <-  observed field, in integer minor units
ROW_MONEY = {
    "principal_minor": "principal",
    "interest_minor": "interest",
    "outstanding_principal_minor": "balance",
    "observed_total_due_minor": "total",
}


def minor(s):
    if s is None or s == "":
        return ""
    d = Decimal(str(s)) * 100
    assert d == d.to_integral_value(), s
    return str(int(d))


def ymd(d):
    return "%04d-%02d-%02d" % (d["year"], d["month"], d["day"])


def compare(vec, obs):
    """Return (cells_compared, [diffs])."""
    diffs = []
    n = 0
    exp, per = vec["expect"], obs["periods"]
    n += 1
    if minor(obs["totalInterestAmount"]) != exp["observed_total_interest_minor"]:
        diffs.append({"field": "observed_total_interest_minor",
                      "vector": exp["observed_total_interest_minor"],
                      "observed": minor(obs["totalInterestAmount"])})
    if len(exp["periods"]) != len(per):
        diffs.append({"field": "rowCount", "vector": len(exp["periods"]), "observed": len(per)})
        return n, diffs
    for i, (a, b) in enumerate(zip(exp["periods"], per)):
        n += 1
        if a["kind"] != b["type"]:
            diffs.append({"row": i, "field": "kind", "vector": a["kind"], "observed": b["type"]})
        n += 1
        if ymd(a["due_date"]) != b["dueDate"]:
            diffs.append({"row": i, "field": "due_date", "vector": ymd(a["due_date"]),
                          "observed": b["dueDate"]})
        n += 1
        if ymd(a["from_date"]) != b["periodFromDate"]:
            diffs.append({"row": i, "field": "from_date", "vector": ymd(a["from_date"]),
                          "observed": b["periodFromDate"]})
        for vk, ok in ROW_MONEY.items():
            if vk not in a:
                continue
            n += 1
            got = minor(b.get(ok))
            # The DISBURSEMENT row carries no `total`; the vector encodes that absence as JSON
            # null and the capture as a missing key. Both mean "the oracle emitted no value here",
            # so they are equal. This is an ENCODING normalisation, not a tolerance: it is applied
            # only when BOTH sides are the absent marker.
            if a[vk] is None and got == "":
                continue
            if a[vk] != got:
                diffs.append({"row": i, "field": vk, "vector": a[vk], "observed": got})
    return n, diffs


cap = json.load(open(CAP))
ci = {c["id"]: c for c in cap["captures"]}

# ---- CALIBRATION ON A KNOWN NEGATIVE (P-72): corrupt one minor unit, demand a diff -------------
_v = json.load(open(VDIR + "/" + PAIRS[1][1]))
_o = copy.deepcopy(ci[PAIRS[1][0]]["observed"])
_o["periods"][-1]["interest"] = "0.02"          # the real value is 0.01
_n, _d = compare(_v, _o)
assert _n > 100 and any(x.get("field") == "interest_minor" for x in _d), \
    "CALIBRATION FAILED: a corrupted cell did not produce a diff; this comparison proves nothing"
CALIBRATION = {"corruptedField": "last row interest 0.01 -> 0.02",
               "cellsCompared": _n, "diffsRaised": len(_d), "status": "DETECTED"}

report = {"calibration": CALIBRATION, "cells": []}
for cid, vf in PAIRS:
    v = json.load(open(VDIR + "/" + vf))
    n, diffs = compare(v, ci[cid]["observed"])
    report["cells"].append({
        "cell": cid, "vector": vf,
        "exemptions": [e.get("invariant") for e in v.get("invariant_exemptions", [])],
        "cellsCompared": n, "diffCount": len(diffs), "diffs": diffs[:20],
        "VERDICT": "REPRODUCED" if not diffs else "DIFFERS"})

json.dump(report, sys.stdout, indent=1)
print()
