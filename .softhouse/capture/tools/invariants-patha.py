#!/usr/bin/env python3
"""
T25 — property invariants for the Path A (embeddable seam) capture corpus.

Every check is in INTEGER MINOR UNITS. Money strings are parsed with `Decimal`, scaled by
10**currencyDecimalPlaces and converted to `int`; no binary float is constructed at any point and
NO TOLERANCE is applied anywhere. A tolerance in a money invariant is a bug, not a kindness.

Replaces the roll-forward check in `out/t21-probe-invariants.py`, whose `X2` is MALFORMED: it seeds
the running balance at the disbursed amount and then subtracts repayment principals, which is wrong
for any schedule whose first emitted row precedes the disbursement (`P-03`). See
`.softhouse/reviews/T21-capture-pass3-audit.md` §6.1 and `.softhouse/capture/RETRACTIONS.md`.

  I1  principal amortizes to exactly zero      (final REPAYMENT balance == 0)
  I2  sum(REPAYMENT principal) == totalDisbursedAmount
  I3  sum(interest)  == totalInterestAmount
  I4  sum(total)     == totalRepaymentAmount
  I5  splits sum to the whole, per period: principal + interest + fee + penalty == total
  I6  totalDisbursedAmount + totalInterestAmount + totalFeeAmount + totalPenaltyAmount
                                                                    == totalRepaymentAmount
  I7  sum(DISBURSEMENT principal) == totalDisbursedAmount
  I8  POSITION-AWARE balance roll-forward: walk the emitted rows in order; a DISBURSEMENT row ADDS
      to the running balance, a REPAYMENT/DOWN_PAYMENT row subtracts its principal; every row's
      emitted `balance` must equal the running balance at that point
  I9  totalOutstandingBalance roll-forward: it decreases by each row's `total` and ends at zero
  I10 every money string is plain (no exponent) and carries exactly currencyDecimalPlaces decimals
  I11 no negative money anywhere
  I12 totalPrincipalAmount == sum(REPAYMENT principal)

Usage:  python3 invariants-patha.py out/capture-prod-v2-raw.json
Exit 0 = all invariants hold on every capture.
"""
import json
import re
import sys
from decimal import Decimal

PLAIN = re.compile(r"^-?\d+(\.\d+)?$")


def minor(s, dp):
    if not PLAIN.match(s):
        raise ValueError(f"not a plain decimal string: {s!r}")
    return int((Decimal(s) * (10 ** dp)).to_integral_value())


def check(cap):
    dp = int(cap["inputs"]["currencyDecimalPlaces"])
    o = cap["observed"]
    if o is None:
        return {"ERROR": f"capture errored: {cap.get('error')}"}
    rows = o["periods"]

    def m(x):
        return minor(x, dp)

    res = {}
    reps = [r for r in rows if r["type"] in ("REPAYMENT", "DOWN_PAYMENT")]
    disb = [r for r in rows if r["type"] == "DISBURSEMENT"]

    res["I1"] = m(reps[-1]["balance"]) == 0
    res["I2"] = sum(m(r["principal"]) for r in reps) == m(o["totalDisbursedAmount"])
    res["I3"] = sum(m(r.get("interest", "0")) for r in reps) == m(o["totalInterestAmount"])
    res["I4"] = sum(m(r["total"]) for r in reps) == m(o["totalRepaymentAmount"])
    res["I5"] = all(
        m(r["principal"]) + m(r.get("interest", "0")) + m(r.get("fee", "0")) + m(r.get("penalty", "0"))
        == m(r["total"]) for r in reps)
    res["I6"] = (m(o["totalDisbursedAmount"]) + m(o["totalInterestAmount"])
                 + m(o.get("totalFeeAmount", "0")) + m(o.get("totalPenaltyAmount", "0"))
                 == m(o["totalRepaymentAmount"]))
    res["I7"] = sum(m(r["principal"]) for r in disb) == m(o["totalDisbursedAmount"])

    bal = 0
    ok8 = True
    for r in rows:
        if r["type"] == "DISBURSEMENT":
            bal += m(r["principal"])
        else:
            bal -= m(r["principal"])
        if "balance" in r and m(r["balance"]) != bal:
            ok8 = False
    res["I8"] = ok8 and bal == 0

    out = m(o["totalRepaymentAmount"])
    ok9 = True
    for r in rows:
        if r["type"] == "DISBURSEMENT":
            continue
        out -= m(r["total"])
        if m(r["totalOutstandingBalance"]) != out:
            ok9 = False
    res["I9"] = ok9 and out == 0

    monies = []
    for r in rows:
        for k, v in r.items():
            if k not in ("type", "periodNumber", "dueDate", "periodFromDate"):
                monies.append(v)
    for k in ("totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount"):
        monies.append(o[k])
    res["I10"] = all(PLAIN.match(v) and len(v.split(".")[1]) == dp if "." in v else False for v in monies)
    res["I11"] = all(m(v) >= 0 for v in monies)
    if "totalPrincipalAmount" in o:
        res["I12"] = m(o["totalPrincipalAmount"]) == sum(m(r["principal"]) for r in reps)
    return res


def main():
    data = json.load(open(sys.argv[1]))
    keys = ["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I10", "I11", "I12"]
    print(f"{'capture':<14} " + " ".join(f"{k:>4}" for k in keys) + "   verdict")
    rc = 0
    for cap in data["captures"]:
        r = check(cap)
        if "ERROR" in r:
            print(f"{cap['id']:<14} {r['ERROR']}")
            rc = 1
            continue
        cells = []
        for k in keys:
            if k not in r:
                cells.append("   -")
            else:
                cells.append("   ." if r[k] else "  !!")
        allok = all(v for v in r.values())
        if not allok:
            rc = 1
        print(f"{cap['id']:<14} " + " ".join(cells) + f"   {'PASS' if allok else 'FAIL'}")
    print()
    print("VERDICT:", "ALL PASS" if rc == 0 else "FAILURES PRESENT")
    print("Note: I10 asserts exactly currencyDecimalPlaces decimals; MNT and USD both run at 2.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
