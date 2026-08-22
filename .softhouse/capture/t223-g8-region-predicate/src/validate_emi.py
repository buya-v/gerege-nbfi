#!/usr/bin/env python3
"""
T223 step 1 — validate the ARITHMETIC EMULATION alone, before any classification rule is attached.

The oracle's period-1 row carries `total` = interest + principal = the EMI (period 1 is never the
last period for any n >= 2, so no last-period fallback has touched it). So the emulator's quantized
EMI must equal the observed period-1 `total` in integer minor units, on EVERY observed cell of the
committed corpus. This test has no free parameter and nothing to tune.

Exact arithmetic only (P-25): integer minor units and Decimal. No float.
"""

import gzip
import json
import os
import sys
from collections import Counter
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emi_mechanism import predict  # noqa: E402
from validate_predicate import CAPTURES, REQUIRED, REPO, minor  # noqa: E402


def main():
    counts = Counter()
    mismatches = []
    for tag, rel in CAPTURES:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            print("MISSING (recorded, skipped):", rel)
            continue
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt") as fh:
            doc = json.load(fh)
        for case in doc["captures"]:
            obs = case.get("observed")
            if obs is None:
                counts["errored"] += 1
                continue
            inp = case["inputs"]
            if any(inp.get(k) != v for k, v in REQUIRED.items()):
                counts["out_of_shape"] += 1
                continue
            n = int(inp["numberOfRepayments"])
            if n < 2:
                counts["n_lt_2_skipped"] += 1
                continue
            b_minor = minor(inp["disbursementAmount"])
            rate = str(inp["annualNominalInterestRate"])
            reps = [p for p in obs["periods"] if p["type"] == "REPAYMENT"]
            observed_emi_minor = minor(reps[0]["total"])
            pred = predict(rate, n, b_minor)
            counts["compared"] += 1
            if pred["emiQuantizedMinor"] == observed_emi_minor:
                counts["emi_match"] += 1
            else:
                counts["emi_mismatch"] += 1
                mismatches.append({"capture": tag, "id": case["id"], "rate": rate, "n": n,
                                   "bMinor": b_minor, "observedEmiMinor": observed_emi_minor,
                                   "predictedEmiMinor": pred["emiQuantizedMinor"],
                                   "emiRaw": pred["emiRaw"]})
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "validate-emi.json"), "w") as fh:
        json.dump({"counts": dict(counts), "mismatches": mismatches}, fh, indent=1, sort_keys=True)
    print(json.dumps(dict(counts), sort_keys=True))
    for m in mismatches[:30]:
        print("  MISMATCH", m["id"], "obs", m["observedEmiMinor"], "pred", m["predictedEmiMinor"],
              "raw", m["emiRaw"])
    print("total mismatches:", len(mismatches))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
