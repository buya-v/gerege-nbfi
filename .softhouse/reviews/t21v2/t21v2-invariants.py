#!/usr/bin/env python3
"""T21-v2 INDEPENDENT invariant check. Written from scratch by the T21 auditor.
Integer minor units only; no tolerance anywhere; parse decimal strings to int minor units.

The six invariants PASS3-REPORT.md claims (its own wording, lines 43-46):
  R1 principal amortizes to exactly zero      -> final REPAYMENT `balance` == 0
  R2 sum(principal) == totalDisbursedAmount
  R3 sum(interest)  == totalInterestAmount
  R4 sum(total)     == totalRepaymentAmount
  R5 per period principal + interest == total
  R6 totalDisbursed + totalInterest == totalRepayment

Auditor's additional checks (NOT claimed by the report):
  A1 sum(DISBURSEMENT principals) == totalDisbursedAmount
  A2 NAIVE roll-forward (prior worker's X2): start at disbursed, subtract each repayment principal
  A3 POSITION-AWARE roll-forward: walk periods in emitted order; DISBURSEMENT adds, REPAYMENT subtracts
  A4 totalOutstandingBalance roll-forward: running total-due remaining == emitted totalOutstandingBalance
  A5 scale discipline: every money string is exactly currencyDecimalPlaces dp, plain (no exponent)
  A6 no negative money anywhere
"""
from decimal import Decimal
import json, sys, re

PLAIN = re.compile(r"^-?\d+\.\d+$|^-?\d+$")


def minor(s, dp):
    d = Decimal(s)
    scaled = d * (10 ** dp)
    if scaled != scaled.to_integral_value():
        raise ValueError("not representable in minor units: %s" % s)
    return int(scaled)


def scale_ok(s, dp):
    if not PLAIN.match(s):
        return False
    if "." not in s:
        return dp == 0
    return len(s.split(".")[1]) == dp


def main(path):
    data = json.load(open(path))
    rows = []
    for c in data["captures"]:
        o = c.get("observed")
        cid = c["id"]
        if o is None:
            rows.append((cid, ["ERR"] * 12, False))
            continue
        dp = int(c["inputs"]["currencyDecimalPlaces"])
        per = o["periods"]
        rep = [p for p in per if p["type"] == "REPAYMENT"]
        dis = [p for p in per if p["type"] == "DISBURSEMENT"]
        dwn = [p for p in per if p["type"] == "DOWN_PAYMENT"]
        assert not dwn, "down-payment periods present: extend the checker"
        D = minor(o["totalDisbursedAmount"], dp)
        I = minor(o["totalInterestAmount"], dp)
        T = minor(o["totalRepaymentAmount"], dp)
        r1 = minor(rep[-1]["balance"], dp) == 0
        r2 = sum(minor(p["principal"], dp) for p in rep) == D
        r3 = sum(minor(p["interest"], dp) for p in rep) == I
        r4 = sum(minor(p["total"], dp) for p in rep) == T
        r5 = all(minor(p["principal"], dp) + minor(p["interest"], dp) == minor(p["total"], dp) for p in rep)
        r6 = D + I == T
        a1 = sum(minor(p["principal"], dp) for p in dis) == D
        # A2 naive
        bal = D
        a2 = True
        for p in rep:
            bal -= minor(p["principal"], dp)
            if bal != minor(p["balance"], dp):
                a2 = False
                break
        # A3 position aware
        bal = 0
        a3 = True
        for p in per:
            if p["type"] == "DISBURSEMENT":
                bal += minor(p["principal"], dp)
            else:
                bal -= minor(p["principal"], dp)
                if bal != minor(p["balance"], dp):
                    a3 = False
                    break
        # A4 total outstanding roll-forward (position aware): remaining total due after this period
        rem = T
        a4 = True
        for p in per:
            if p["type"] == "DISBURSEMENT":
                continue
            rem -= minor(p["total"], dp)
            if rem != minor(p["totalOutstandingBalance"], dp):
                a4 = False
                break
        keys = ("principal", "interest", "total", "balance", "totalOutstandingBalance")
        vals = []
        for p in per:
            for k in keys:
                if k in p:
                    vals.append(p[k])
        vals += [o["totalDisbursedAmount"], o["totalInterestAmount"], o["totalRepaymentAmount"]]
        a5 = all(scale_ok(v, dp) for v in vals)
        a6 = all(Decimal(v) >= 0 for v in vals)
        res = [r1, r2, r3, r4, r5, r6, a1, a2, a3, a4, a5, a6]
        rows.append((cid, res, all(res)))

    hdr = ["R1", "R2", "R3", "R4", "R5", "R6", "A1", "A2", "A3", "A4", "A5", "A6"]
    print(f"{'capture':<14} " + " ".join(f"{h:>3}" for h in hdr) + "   six-claimed  all")
    for cid, res, allok in rows:
        cells = " ".join(("  ." if r is True else ("!!!" if r is False else r)).rjust(3) for r in res)
        six = all(res[:6])
        print(f"{cid:<14} {cells}   {'PASS' if six else 'FAIL':<11}  {'PASS' if allok else 'FAIL'}")
    print()
    print("legend: '.' = holds, '!!!' = violated")
    print("SIX-CLAIMED verdict:", "ALL PASS" if all(all(r[1][:6]) for r in rows) else "FAILURES")


main(sys.argv[1])
