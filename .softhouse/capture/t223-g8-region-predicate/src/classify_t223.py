#!/usr/bin/env python3
"""
T223 — grade the OBSERVED capture against the REGISTERED prediction, and check the two rig
calibrations against pass 3g's committed capture cell for cell.

Reads only the raw capture and ../prediction.json. Integer minor units everywhere; no float (P-25).
The classification is done here, after the fact; the harness classified nothing.
"""
import json
import os
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def minor(s, d=2):
    return int((Decimal(s) * (10 ** d)).to_integral_exact())


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"))


def main():
    cap_path = sys.argv[1]
    cap = json.load(open(cap_path))
    pred = json.load(open(os.path.join(HERE, "..", "prediction.json")))
    ref3g = json.load(open(os.path.join(REPO, ".softhouse/capture/out/capture-prod3g-raw.json")))
    ref = {c["id"]: c for c in ref3g["captures"]}
    got = {c["id"]: c for c in cap["captures"]}

    result = {"calibrations": [], "cells": [], "summary": {}}

    # ---- rig calibrations: whole observed block must equal pass 3g's, byte for byte ----
    for cal in pred["calibrations"]:
        mine = got[cal["id"]]
        theirs = ref[cal["mustReproduce"]]
        same_inputs = [k for k in mine["inputs"]
                       if k != "tenantId" and mine["inputs"].get(k) != theirs["inputs"].get(k)]
        ok = canon(mine.get("observed")) == canon(theirs.get("observed"))
        result["calibrations"].append({"id": cal["id"], "reproduces": cal["mustReproduce"],
                                       "observedIdentical": ok, "inputDiffs": same_inputs})

    n_agree = n_disagree = n_threw = 0
    for c in pred["cells"]:
        case = got[c["id"]]
        obs = case.get("observed")
        if obs is None:
            n_threw += 1
            result["cells"].append({"id": c["id"], "outcome": "THREW",
                                    "error": case.get("error"),
                                    "errorStackTop": case.get("errorStackTop")})
            continue
        reps = [p for p in obs["periods"] if p["type"] == "REPAYMENT"]
        disb = sum(minor(p["principal"]) for p in obs["periods"] if p["type"] == "DISBURSEMENT")
        repaid = sum(minor(p["principal"]) for p in reps)
        observed_family_b = repaid != disb
        observed_emi = minor(reps[0]["total"])
        nonzero_principal_rows = sum(1 for p in reps if minor(p["principal"]) != 0)
        balances = sorted({minor(p["balance"]) for p in reps})
        row = {
            "id": c["id"], "annualRate": c["annualRate"], "n": c["n"], "bMinor": c["bMinor"],
            "rowCount": len(reps), "rowCountMatchesN": len(reps) == c["n"],
            "disbursedMinor": disb, "repaidMinor": repaid,
            "totalPrincipalAmount": obs["totalPrincipalAmount"],
            "totalInterestAmount": obs["totalInterestAmount"],
            "totalOutstandingAmount": obs["totalOutstandingAmount"],
            "observedPeriod1InstalmentMinor": observed_emi,
            "predictedEmiQuantizedMinor": c["predictedEmiQuantizedMinor"],
            "instalmentMatchesPrediction": observed_emi == c["predictedEmiQuantizedMinor"],
            "nonZeroPrincipalRows": nonzero_principal_rows,
            "distinctBalanceValuesMinor": balances,
            "lastRowInterest": reps[-1]["interest"],
            "lastRowPrincipal": reps[-1]["principal"],
            "observedFamilyB": observed_family_b,
            "predictedFamilyB": c["predictedFamilyB"],
            "verdict": "AGREES" if observed_family_b == c["predictedFamilyB"] else "REFUTES",
        }
        if observed_family_b == c["predictedFamilyB"]:
            n_agree += 1
        else:
            n_disagree += 1
        result["cells"].append(row)

    result["summary"] = {"agree": n_agree, "refute": n_disagree, "threw": n_threw,
                         "calibrationsIdentical": all(c["observedIdentical"]
                                                      for c in result["calibrations"])}
    outdir = os.path.join(HERE, "..", "out")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "classify-t223.json"), "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)

    for c in result["calibrations"]:
        print("CAL %-10s reproduces %-10s observedIdentical=%s inputDiffs=%s"
              % (c["id"], c["reproduces"], c["observedIdentical"], c["inputDiffs"]))
    print()
    for r in result["cells"]:
        if r.get("outcome") == "THREW":
            print("%-24s THREW %s" % (r["id"], r["error"]))
            continue
        print("%-24s rate=%-6s n=%-5d B=%-5d rows=%-5d instalment obs=%-4d pred=%-4d %s | "
              "repaid=%-6d of %-6d totP=%-8s | nonZeroPrincRows=%-4d | famB obs=%-5s pred=%-5s -> %s"
              % (r["id"], r["annualRate"], r["n"], r["bMinor"], r["rowCount"],
                 r["observedPeriod1InstalmentMinor"], r["predictedEmiQuantizedMinor"],
                 "OK " if r["instalmentMatchesPrediction"] else "MISS",
                 r["repaidMinor"], r["disbursedMinor"], r["totalPrincipalAmount"],
                 r["nonZeroPrincipalRows"], r["observedFamilyB"], r["predictedFamilyB"],
                 r["verdict"]))
    print()
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
