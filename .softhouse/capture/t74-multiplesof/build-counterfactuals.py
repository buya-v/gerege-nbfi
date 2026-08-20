#!/usr/bin/env python3
"""Measure the MATHCONTEXT-PRECISION-12 counterfactual for pass 3i's group E — task T74.

    python3 build-counterfactuals.py <capture-prod3i-raw.json> <out.json>

WHAT MAKES THIS DIFFERENT FROM EVERY OTHER COUNTERFACTUAL IN THIS STORE. T58, T61
and T64 measured their counterfactuals by MUTATING THE GO PORT and re-running it,
and each had to prove the unmutated model reproduced the oracle before its margin
meant anything. This one has no model in it at all: **both arms are observations
of the reference oracle**, taken in the same run, from the same seam, with the
same rig calibrations in front of them, and differing in exactly one input —
the threaded `MathContext` precision, 19 against 12.

So the counterfactual named is: *an implementation that runs its intermediate
arithmetic at 12 significant digits instead of the ratified 19, everything else
faithful.* Its output is not modelled. It is what the oracle itself returns when
asked to do that.

WHAT IT DOES NOT ESTABLISH, stated here so no reader has to infer it: it does not
predict where a port with some OTHER precision defect lands, and it is not a claim
about the rounding MODE, which is HALF_UP on both arms.

Money is compared as integer minor units by exact string arithmetic. No float.
"""
import json
import sys

PAIRS = [("T74-E-P4", "T74-E-P4-p12"), ("T74-E-P59", "T74-E-P59-p12"),
         ("T74-E-P72", "T74-E-P72-p12"), ("T74-E-P340", "T74-E-P340-p12"),
         ("T74-E-P426", "T74-E-P426-p12"), ("T74-E-P6940", "T74-E-P6940-p12")]

# The three per-period money columns a vector actually GRADES, and the vector-schema
# name of each. `total` is recorded by the store as observed_total_due_minor and is
# graded, so it is included; the capture's totalOutstandingBalance is NOT promoted by
# this store at all and is therefore not counted here.
COLUMNS = [("principal", "principal_minor"),
           ("interest", "interest_minor"),
           ("balance", "outstanding_principal_minor"),
           ("total", "observed_total_due_minor")]


def minor(text, digits):
    t = str(text).strip()
    neg = t.startswith('-')
    if neg:
        t = t[1:]
    if 'e' in t or 'E' in t:
        raise SystemExit("exponent in money string %r" % text)
    ip, _, fp = t.partition('.')
    if len(fp) > digits:
        if fp[digits:].strip('0'):
            raise SystemExit("%r carries a significant digit beyond scale %d" % (text, digits))
        fp = fp[:digits]
    fp = fp.ljust(digits, '0')
    v = int((ip or '0') + fp) if digits else int(ip or '0')
    return -v if neg else v


def main(capture_path, out_path):
    doc = json.load(open(capture_path, encoding='utf-8'))
    caps = {c['id']: c for c in doc['captures']}
    report = []

    for base, probe in PAIRS:
        a, b = caps[base], caps[probe]
        ia, ib = a['inputs'], b['inputs']

        # The two arms must differ in the MathContext precision and in NOTHING else.
        # A counterfactual measured across two requests that differ in a second field is
        # measuring both, and would be worthless.
        varying = {k for k in set(ia) | set(ib)
                   if ia.get(k) != ib.get(k)}
        allowed = {"mathContextPrecision", "tenantId"}
        if not varying <= allowed:
            raise SystemExit("%s vs %s differ in more than the precision: %r"
                             % (base, probe, sorted(varying - allowed)))
        if ia["mathContextPrecision"] != 19 or ib["mathContextPrecision"] != 12:
            raise SystemExit("%s/%s are not a 19-vs-12 pair" % (base, probe))
        # CORRECTED BY T82 (T75 follow-up E-3). This stood as the Python CHAINED COMPARISON
        #
        #     if ia[...] != ib[...] != "HALF_UP":
        #
        # which Python expands to `(ia != ib) and (ib != "HALF_UP")`. Both conjuncts had to hold for
        # the guard to fire, so it PASSED whenever the two arms SHARED a mode — including when both
        # shared a NON-ratified one, which is exactly the case the `varying` check above cannot see,
        # because a value common to both arms does not vary. Worse, the only case the chained form
        # could in principle have caught (the two arms differing) is unreachable here: differing
        # modes put `mathContextRoundingMode` into `varying`, which is not in `allowed`, so the run
        # already died two checks earlier. The guard was therefore dead in BOTH directions.
        #
        # Stated positively instead, with no chaining: EACH arm must be at the ratified HALF_UP.
        # The ratified production setting is MathContext(19, HALF_UP) — CLAUDE.md, and
        # MoneyHelper.PRECISION = 19 is a compile-time constant.
        off_mode = {arm: m for arm, m in ((base, ia["mathContextRoundingMode"]),
                                          (probe, ib["mathContextRoundingMode"]))
                    if m != "HALF_UP"}
        if off_mode:
            raise SystemExit("%s/%s: %r is not the ratified HALF_UP rounding mode. A counterfactual "
                             "measured at a mode production never runs describes a port defect "
                             "nobody has, and this pair's whole claim is that the ONLY difference "
                             "between its arms is precision 19 against 12." % (base, probe, off_mode))
        digits = ia["currencyDecimalPlaces"]

        pa, pb = a['observed']['periods'], b['observed']['periods']
        if len(pa) != len(pb):
            raise SystemExit("%s/%s differ in period count" % (base, probe))

        cells = 0
        divergent = []
        for idx, (ra, rb) in enumerate(zip(pa, pb)):
            for capkey, veckey in COLUMNS:
                if ra.get(capkey) is None or rb.get(capkey) is None:
                    continue
                cells += 1
                va, vb = minor(ra[capkey], digits), minor(rb[capkey], digits)
                if va != vb:
                    divergent.append({"row": idx, "field": veckey,
                                      "observed": va, "counterfactual": vb,
                                      "delta": abs(va - vb)})
        report.append({
            "case": base,
            "counterfactualCase": probe,
            "counterfactualId": "MATHCONTEXT-PRECISION-12-INSTEAD-OF-RATIFIED-19",
            "bothArmsAreOracleObservations": True,
            "cells": cells,
            "divergentCellCount": len(divergent),
            "divergent": divergent,
            "widest": max(divergent, key=lambda c: c["delta"]) if divergent else None,
            "observedTotalInterest": a['observed']['totalInterestAmount'],
            "counterfactualTotalInterest": b['observed']['totalInterestAmount'],
        })
        w = report[-1]["widest"]
        print("%-12s %2d/%2d graded cells diverge; widest %s minor at period[%s].%s "
              "(observed %s vs %s); total interest %s vs %s"
              % (base, len(divergent), cells,
                 w["delta"] if w else 0, w["row"] if w else '-', w["field"] if w else '-',
                 w["observed"] if w else '-', w["counterfactual"] if w else '-',
                 a['observed']['totalInterestAmount'], b['observed']['totalInterestAmount']))

    json.dump(report, open(out_path, 'w', encoding='utf-8'), indent=1)
    print("\nwrote %s" % out_path)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
