#!/usr/bin/env python3
"""T46 -- the charge property suite with C5 RELABELLED, closing T44 finding A-4.

A-4: "C5 is a discrimination probe, not an invariant; carried forward it becomes an assertion
DEC-1 section 9 forbids.  A correct Go port, discarding totalRepaymentExpected per ratified
decision C-1, would FAIL C5 on 15 of 21."

So this suite splits T40's ten checks in two:

  INVARIANTS  C1 C2 C3 C4 C6 C7 C8 C9 C10 -- relations between cells of the SAME observed
              document.  A failure here is a statement about the reference oracle.  These are
              the only checks that contribute to the exit code.

  PROBE  P5   (was C5) `totalRepaymentExpected - sum(totalDueForPeriod)`, reported as a SIGNED
              DELTA in integer minor units, never as a pass/fail.  It is a MEASUREMENT of
              D-1's asymmetry, and it is deliberately NOT an assertion: DEC-1 revision 8's
              ratified decision C-1 says no adapter, harness or conformance check may assert
              `totalRepaymentExpected` equals the sum of the rows.  A conformance harness that
              asserted P5 would reject a CORRECT port.

Exact Decimal in integer minor units throughout; no float is constructed at any point.

`--negative` re-runs the invariants with one leaf perturbed IN MEMORY (nothing on disk is
touched) so the suite can be watched to fail.  An assertion suite that has never failed has
not been tested (.softhouse/patterns.md).
"""
import json
import os
import pathlib
import sys
from decimal import Decimal

CH = pathlib.Path(os.environ.get("T40_WORKTREE",
                                 str(pathlib.Path(__file__).resolve().parents[4]))) \
    / ".softhouse" / "capture" / "charges"
Z = Decimal(0)

# every directory of raw captures this suite reads
SETS = [("T40 fc", CH / "out" / "fc"),
        ("T46 A-3/A-5", CH / "out" / "t46")]


def load(p):
    with open(p) as f:
        return json.load(f, parse_float=Decimal, parse_int=Decimal)


def m(v):
    """Exact integer MINOR UNITS.  Refuses anything finer than a minor unit."""
    if v is None:
        return None
    q = v * 100
    assert q == q.to_integral_value(), f"sub-minor-unit value {v}"
    return int(q)


def g(p, k):
    v = p.get(k)
    return Z if v is None else v


def invariants(d, ctrl):
    ps = d["periods"]
    res = {}
    res["C1"] = m(sum(g(p, "feeChargesDue") for p in ps)) == m(g(d, "totalFeeChargesCharged"))
    res["C2"] = m(sum(g(p, "penaltyChargesDue") for p in ps)) == m(g(d, "totalPenaltyChargesCharged"))
    res["C3"] = all(
        m(g(p, "totalDueForPeriod")) ==
        m(g(p, "principalDue") + g(p, "interestDue") + g(p, "feeChargesDue") + g(p, "penaltyChargesDue"))
        for p in ps if "period" in p)
    res["C4"] = all(m(g(p, "feeChargesOutstanding")) == m(g(p, "feeChargesDue"))
                    and m(g(p, "penaltyChargesOutstanding")) == m(g(p, "penaltyChargesDue"))
                    for p in ps if "period" in p)
    res["C6"] = m(sum(g(p, "principalDue") for p in ps)) == m(g(d, "totalPrincipalExpected"))
    res["C7"] = m(sum(g(p, "interestDue") for p in ps)) == m(g(d, "totalInterestCharged"))
    res["C8"] = all(
        m(g(a, k)) == m(g(b, k))
        for a, b in zip(ctrl["periods"], ps)
        for k in ("principalDue", "principalOriginalDue", "interestDue",
                  "principalLoanBalanceOutstanding"))
    res["C9"] = all(m(g(a, "totalInstallmentAmountForPeriod")) == m(g(b, "totalInstallmentAmountForPeriod"))
                    for a, b in zip(ctrl["periods"], ps))
    res["C10"] = all(m(g(p, k)) >= 0 for p in ps
                     for k in ("principalDue", "interestDue", "feeChargesDue",
                               "penaltyChargesDue", "totalDueForPeriod",
                               "principalLoanBalanceOutstanding"))
    return res


def p5_delta(d):
    """SIGNED delta, integer minor units: totalRepaymentExpected - sum(totalDueForPeriod)."""
    ps = d["periods"]
    return m(g(d, "totalRepaymentExpected")) - m(sum(g(p, "totalDueForPeriod") for p in ps))


KEYS = ["C1", "C2", "C3", "C4", "C6", "C7", "C8", "C9", "C10"]


def main():
    negative = "--negative" in sys.argv
    ctrl = load(CH / "out" / "control" / "B-01-baseline-raw.json")

    docs = []
    for label, d in SETS:
        if not d.is_dir():
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith("-raw.json"):
                docs.append((label, f[: -len("-raw.json")], load(d / f)))

    if negative:
        # perturb ONE leaf in memory so the suite can be watched to fail
        lbl, cid, doc = docs[0]
        doc["periods"][1]["interestDue"] = doc["periods"][1]["interestDue"] + Decimal("0.01")
        print(f"NEGATIVE RUN: {cid} period-1 interestDue perturbed by +0.01 IN MEMORY "
              "(nothing on disk is touched)")
        print()

    fails = 0
    print("## INVARIANTS -- a failure here is a statement about the reference oracle")
    print()
    print("| set | capture | " + " | ".join(KEYS) + " |")
    print("|---" * (len(KEYS) + 2) + "|")
    for lbl, cid, doc in docs:
        res = invariants(doc, ctrl)
        fails += sum(1 for v in res.values() if not v)
        print(f"| {lbl} | {cid} | " + " | ".join("PASS" if res[k] else "**FAIL**" for k in KEYS) + " |")

    print()
    print("## PROBE P5 (was C5) -- NOT AN INVARIANT, NOT A CONFORMANCE ASSERTION")
    print()
    print("`totalRepaymentExpected - sum(totalDueForPeriod)`, signed, in integer MINOR UNITS.")
    print("A **correct** Go port discards `totalRepaymentExpected` per DEC-1 revision 8's ratified")
    print("decision C-1, so a non-zero delta here is the ORACLE's behaviour, never a port defect.")
    print()
    print("| set | capture | delta (minor units) | reads as |")
    print("|---|---|---:|---|")
    nonzero = 0
    for lbl, cid, doc in docs:
        delta = p5_delta(doc)
        if delta:
            nonzero += 1
        reads = ("rows and total AGREE" if delta == 0
                 else "total OMITS charge money present in the rows")
        print(f"| {lbl} | {cid} | {delta} | {reads} |")

    print()
    print(f"P5: {nonzero} of {len(docs)} captures show a non-zero delta. "
          "That count is a MEASUREMENT, not a verdict.")
    print()
    print(f"INVARIANT failures: {fails}")
    if fails:
        print("SUITE FAILED")
        return 1
    print("SUITE PASSED (C5 is not among these checks, by design -- see T44 finding A-4)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
