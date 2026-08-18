#!/usr/bin/env python3
"""
T21 AUDIT PROBE — independent property-invariant check on every capture.
Integer minor units only (Decimal parsed then scaled by 10^decimalPlaces to int).
No tolerance is applied anywhere.

The six invariants (as specified in the T21 brief) are I1..I6.
X1 and X2 below are the AUTHOR'S OWN ADDITIONS — they are NOT part of the six,
and a failure of one of them does not contradict any claim about the six.

 I1 principal amortizes to exactly zero (final REPAYMENT balance == 0)
 I2 sum(principal) == totalDisbursedAmount
 I3 sum(interest)  == totalInterestAmount
 I4 sum(total)     == totalRepaymentAmount
 I5 per period: principal + interest == total
 I6 totalDisbursedAmount + totalInterestAmount == totalRepaymentAmount
Plus two extra checks OF THE AUTHOR'S OWN (not among the six invariants):
 X1 DISBURSEMENT principal sum == totalDisbursedAmount
 X2 POSITION-AWARE balance roll-forward. CORRECTED by the T21 independent audit
    (T21-v2), 2026-08-18 — see `.softhouse/reviews/T21-capture-pass3-audit.md`
    §6.1. The original X2 seeded the running balance at `disbursed` and subtracted
    each REPAYMENT principal; that formulation is INVALID for P-03, whose first
    emitted REPAYMENT row is a pre-disbursement snapshot (balance 0.00) emitted
    BEFORE the DISBURSEMENT row, so it reported a spurious FAIL. This is the
    audit's position-aware version (`A3` in
    `.softhouse/reviews/t21v2/t21v2-invariants.py`): walk periods in emitted
    order; a DISBURSEMENT row ADDS to the running balance, a REPAYMENT row
    SUBTRACTS and must then equal that row's `balance`. It holds on all twelve
    captures, P-03 included.
"""
from decimal import Decimal
import json, sys


def minor(s, dp):
    return int((Decimal(s) * (10 ** dp)).to_integral_value())


def main():
    data = json.load(open(sys.argv[1]))
    rc = 0
    print(f"{'capture':<14} {'I1':>3} {'I2':>3} {'I3':>3} {'I4':>3} {'I5':>3} {'I6':>3} {'X1':>3} {'X2':>3}   verdict")
    for c in data["captures"]:
        o = c["observed"]
        if o is None:
            print(f"{c['id']:<14} {'-':>3}*8   NO OBSERVED (error capture)")
            rc = 1
            continue
        dp = int(c["inputs"]["currencyDecimalPlaces"])
        rep = [p for p in o["periods"] if p["type"] == "REPAYMENT"]
        dis = [p for p in o["periods"] if p["type"] == "DISBURSEMENT"]
        disbursed = minor(o["totalDisbursedAmount"], dp)
        tot_int = minor(o["totalInterestAmount"], dp)
        tot_rep = minor(o["totalRepaymentAmount"], dp)
        sp = sum(minor(p["principal"], dp) for p in rep)
        si = sum(minor(p["interest"], dp) for p in rep)
        st = sum(minor(p["total"], dp) for p in rep)
        i1 = minor(rep[-1]["balance"], dp) == 0
        i2 = sp == disbursed
        i3 = si == tot_int
        i4 = st == tot_rep
        i5 = all(minor(p["principal"], dp) + minor(p["interest"], dp) == minor(p["total"], dp) for p in rep)
        i6 = disbursed + tot_int == tot_rep
        x1 = sum(minor(p["principal"], dp) for p in dis) == disbursed
        # X2 (CORRECTED): position-aware roll-forward — DISBURSEMENT adds, REPAYMENT
        # subtracts and must equal that row's balance. Walk periods in emitted order.
        bal = 0
        x2 = True
        for p in o["periods"]:
            if p["type"] == "DISBURSEMENT":
                bal += minor(p["principal"], dp)
            else:
                bal -= minor(p["principal"], dp)
                if bal != minor(p["balance"], dp):
                    x2 = False
                    break
        res = [i1, i2, i3, i4, i5, i6, x1, x2]
        allok = all(res)
        if not allok:
            rc = 1
        cells = "  ".join("OK" if r else "!!" for r in res)
        print(f"{c['id']:<14} {cells}   {'PASS' if allok else 'FAIL'}")
    print("\nALL PASS" if rc == 0 else "\nFAILURES PRESENT")
    sys.exit(rc)


if __name__ == "__main__":
    main()
