#!/usr/bin/env python3
"""T219 (classifier inherited verbatim from T229 except for the THREW branch, which T229\nnever exercised because zero of its cells threw) — classify the observed capture against the REGISTERED prediction.

Reads only the emitted JSON. NO FLOATING POINT: every money figure is converted to INTEGER MINOR
UNITS through Decimal and asserted integral. This file does not know the mechanism; it compares
numbers.
"""
import gzip
import json
import sys
from decimal import Decimal


def minor(s):
    d = Decimal(str(s)) * 100
    assert d == d.to_integral_value(), s
    return int(d)


def load(path):
    op = gzip.open if path.endswith(".gz") else open
    return json.load(op(path))


raw = load(sys.argv[1])
pred = {p["id"]: p for p in json.load(open(sys.argv[2]))}
ref3g = load(sys.argv[3]) if len(sys.argv) > 3 else None

out = {"cells": [], "calibration": [], "throws": []}

if ref3g:
    ref = {c["id"]: c for c in ref3g["captures"]}
    pairs = {"P-CAL-ZPA": "T64-ZP-A", "P-CAL-ZPB": "T64-ZP-B"}
    for cal, tgt in pairs.items():
        mine = [c for c in raw["captures"] if c["id"] == cal]
        theirs = ref.get(tgt)
        if not mine or theirs is None:
            out["calibration"].append({"cal": cal, "target": tgt, "status": "MISSING"})
            continue
        same_inputs = mine[0]["inputs"] == theirs["inputs"]
        same_obs = mine[0].get("observed") == theirs.get("observed")
        # pass 3g predates T169's `outcome` key, so compare `threw` exactly as T229 did; the
        # `outcome` key is a rig field, not an observation, and is excluded from the calibration.
        same_threw = mine[0].get("threw") == theirs.get("threw")
        out["calibration"].append({"cal": cal, "target": tgt, "inputsIdentical": same_inputs,
                                   "observedIdentical": same_obs, "threwIdentical": same_threw,
                                   "status": "REPRODUCED" if (same_inputs and same_obs and same_threw)
                                   else "DIFFERS"})

for c in raw["captures"]:
    cid = c["id"]
    if cid not in pred:
        continue
    p = pred[cid]
    row = {"id": cid, "rate": p["rate"], "n": p["n"], "bMinor": p["bMinor"],
           "predictedOutcome": p["predictedOutcome"],
           "predictedPrincipalMinor": p["predictedTotalPrincipalMinor"],
           "predictedEmiMinor": p["emiMinorPredicted"],
           "predictedDelta": p["deltaMinor"], "aMinor": p["aMinor"],
           "t223RulePredictedRescue": p["t223Rule_rescues"]}
    if c.get("outcome") == "threw" or c.get("observed") is None:
        row["observed"] = "THREW"
        row["threw"] = {"errorClass": c.get("errorClass"),
                        "errorStackDepthTotal": c.get("errorStackDepthTotal"),
                        "errorStackTop0": (c.get("errorStackTop") or [None])[0]}
        out["throws"].append(cid)
        out["cells"].append(row)
        continue
    o = c["observed"]
    reps = [r for r in o["periods"] if r["type"] == "REPAYMENT"]
    row["observedRepaymentRows"] = len(reps)
    row["observedPrincipalMinor"] = minor(o["totalPrincipalAmount"])
    row["observedInterestMinor"] = minor(o["totalInterestAmount"])
    row["observedDisbursedMinor"] = minor(o["totalDisbursedAmount"])
    row["observedRow1TotalMinor"] = minor(reps[0]["total"])
    row["observedRow1InterestMinor"] = minor(reps[0]["interest"])
    row["observedLastTotalMinor"] = minor(reps[-1]["total"])
    row["observedEmiDifferenceMinor"] = row["observedLastTotalMinor"] - row["observedRow1TotalMinor"]
    distinct = sorted({minor(r["total"]) for r in reps[:-1]})
    row["observedDistinctTotalsExLast"] = distinct[:6]
    row["observedDistinctTotalsExLastCount"] = len(distinct)

    obs_delta = row["observedRow1InterestMinor"]
    # observed outcome, purely from the numbers
    if row["observedPrincipalMinor"] == 0:
        obs = "FAMILY_B_FULL"
    elif row["observedPrincipalMinor"] == row["observedDisbursedMinor"]:
        # full repayment: rescued (many distinct instalments / row-1 total > predicted E) vs
        # last-row-carries-all (row 1 total == predicted E and only the last row has principal)
        prin_rows = [r for r in reps if minor(r["principal"]) != 0]
        obs = "AMORTIZES_FULLY(last-row-only)" if len(prin_rows) == 1 else "AMORTIZES_FULLY(spread)"
    else:
        obs = "FAMILY_B_PARTIAL"
    row["observedOutcome"] = obs
    row["_obsDeltaFromRow1"] = obs_delta - row["observedRow1TotalMinor"]

    pp = p["predictedTotalPrincipalMinor"]
    if p["predictedOutcome"] == "RESCUED_BY_SITE3":
        row["verdict"] = "AS PREDICTED" if obs.startswith("AMORTIZES_FULLY") else "REFUTED"
    else:
        ok = (obs == p["predictedOutcome"] if p["predictedOutcome"].startswith("FAMILY_B")
              else obs.startswith("AMORTIZES_FULLY"))
        ok = ok and row["observedPrincipalMinor"] == pp
        row["verdict"] = "AS PREDICTED" if ok else "REFUTED"
    # P2: emiDifference == B  and  totalInterest == n*E + B, on unrescued cells only
    if p["predictedOutcome"] != "RESCUED_BY_SITE3":
        row["P2_emiDifferenceEqualsB"] = (row["observedEmiDifferenceMinor"] == p["bMinor"])
        row["P2_emiObservedEqualsPredicted"] = (row["observedRow1TotalMinor"] == p["emiMinorPredicted"])
        row["P2_totalInterestEqualsNEplusB"] = (
            row["observedInterestMinor"] == p["n"] * row["observedRow1TotalMinor"] + p["bMinor"])
    out["cells"].append(row)

json.dump(out, sys.stdout, indent=1)
print()
