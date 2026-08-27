#!/usr/bin/env python3
"""
T223 — validate the mechanism-derived predicate against EVERY observed cell in the seven committed
raw captures, before it is used to predict anything unswept.

This is a VALIDATION, not a fit: `emi_mechanism.predict` has no free parameter. It either
reproduces the oracle's classification on the committed corpus or it does not.

Reads only the RAW .gz / .json captures (STANDING RULE item 5). Integer minor units and Fractions
throughout; no float anywhere (P-25).
"""

import gzip
import json
import os
import sys
from decimal import Decimal
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from predicate import classify as predict  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))

CAPTURES = [
    ("t117", ".softhouse/capture/t117-familyb/out/capture-t117-raw.json.gz"),
    ("t117p2", ".softhouse/capture/t117-familyb/out/capture-t117p2-raw.json.gz"),
    ("t159", ".softhouse/capture/t159-review-t117/out/capture-t159-raw.json.gz"),
    ("t83", ".softhouse/capture/t83-nonamortizing/out/capture-t83-raw.json"),
    ("t84", ".softhouse/reviews/T84-evidence/out/capture-t84-raw.json.gz"),
    ("t84b", ".softhouse/reviews/T84-evidence/out/capture-t84b-raw.json.gz"),
    ("t100", ".softhouse/capture/t100-g8-rescope/out/capture-t100-raw.json"),
    ("t116", ".softhouse/capture/t116-familyb-promotion/out/capture-t116-raw.json"),
]

# The one shape the predicate is derived for. Any cell outside it is reported as OUT-OF-SHAPE and
# is NOT counted for or against the predicate.
REQUIRED = {
    "repaymentFrequency": 1,
    "repaymentFrequencyType": "MONTHS",
    "daysInMonth": "DAYS_30",
    "daysInYear": "DAYS_360",
    "daysInYearCustomStrategy": None,
    "downPaymentEnabled": False,
    "currencyInMultiplesOf": None,
    "installmentAmountInMultiplesOf": None,
    "fixedLength": None,
    "interestRecognitionOnDisbursementDate": False,
    "interestMethod": "DECLINING_BALANCE",
    "mathContextPrecision": 19,
    "mathContextRoundingMode": "HALF_UP",
    "currencyDecimalPlaces": 2,
    "scheduleGenerationStartDate": "2024-01-01",
    "disbursementDate": "2024-01-01",
}


def minor(s, digits=2):
    """Decimal string -> integer minor units, exactly. No float."""
    return int((Decimal(s) * (10 ** digits)).to_integral_exact())


def main():
    rows = []
    counts = {"observed": 0, "errored": 0, "out_of_shape": 0, "agree": 0, "disagree": 0}
    disagreements = []
    for tag, rel in CAPTURES:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            print("MISSING (skipped, recorded):", rel)
            continue
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt") as fh:
            doc = json.load(fh)
        for case in doc["captures"]:
            cid = case["id"]
            inp = case["inputs"]
            obs = case.get("observed")
            if obs is None:
                counts["errored"] += 1
                rows.append({"capture": tag, "id": cid, "outcome": "ERRORED",
                             "error": case.get("error")})
                continue
            counts["observed"] += 1
            bad = [k for k, v in REQUIRED.items() if inp.get(k) != v]
            if bad:
                counts["out_of_shape"] += 1
                rows.append({"capture": tag, "id": cid, "outcome": "OUT-OF-SHAPE",
                             "fields": bad})
                continue
            b_minor = minor(inp["disbursementAmount"])
            n = int(inp["numberOfRepayments"])
            rate = str(inp["annualNominalInterestRate"])
            # observed classification: family B <=> REPAYMENT principal column does not sum to the
            # disbursed amount (G-8's own discriminator).
            repaid = sum(minor(p["principal"]) for p in obs["periods"] if p["type"] == "REPAYMENT")
            disbursed = sum(minor(p["principal"]) for p in obs["periods"] if p["type"] == "DISBURSEMENT")
            observed_family_b = repaid != disbursed
            pred = predict(rate, n, b_minor)
            agree = bool(pred["familyB"]) == observed_family_b
            counts["agree" if agree else "disagree"] += 1
            row = {"capture": tag, "id": cid, "rate": rate, "n": n, "bMinor": b_minor,
                   "disbursedMinor": disbursed, "repaidMinor": repaid,
                   "observedFamilyB": observed_family_b,
                   "predictedFamilyB": bool(pred["familyB"]),
                   "emiQuantizedMinor": pred["emiQuantizedMinor"],
                   "i1Exact": pred["i1ExactMinorStr"],
                   "margin": pred["marginMinorStr"],
                   "agree": agree}
            rows.append(row)
            if not agree:
                disagreements.append(row)

    out = {"counts": counts, "disagreements": disagreements, "rows": rows}
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "validate-predicate.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(json.dumps(counts, sort_keys=True))
    if disagreements:
        print("DISAGREEMENTS:", len(disagreements))
        for d in disagreements[:40]:
            print("  ", d["id"], "rate", d["rate"], "n", d["n"], "B", d["bMinor"],
                  "observedFamB", d["observedFamilyB"], "predFamB", d["predictedFamilyB"],
                  "emi_q", d["emiQuantizedMinor"], "I1", d["i1Exact"])
    return 0 if not disagreements else 1


if __name__ == "__main__":
    sys.exit(main())
