#!/usr/bin/env python3
"""
T35 — checks over the columns pass 3b adds (T21 P0-3). These could not be run before, because the
columns did not exist.

The existing invariant checkers do NOT cover them: `t21v2-invariants.py`'s A5/A6 inspect exactly
{principal, interest, total, balance, totalOutstandingBalance} plus three plan totals
(`t21v2-invariants.py:96-101`), so a PASS there says nothing about feeAmount, penaltyAmount,
totalPrincipalAmount, totalFeeAmount, totalPenaltyAmount or totalOutstandingAmount.

  N1  periodFromDate contiguity — for consecutive REPAYMENT periods, fromDate[i] == dueDate[i-1].
      This is the boundary error the audit said no vector could catch without the column.
  N2  first REPAYMENT period's fromDate == the schedule generation start date.
  N3  fee and penalty scale discipline: every feeAmount/penaltyAmount is exactly
      currencyDecimalPlaces decimals, plain, and >= 0.
  N4  totalFeeAmount == sum(feeAmount); totalPenaltyAmount == sum(penaltyAmount) — integer minor units.
  N5  totalPrincipalAmount == sum(REPAYMENT principal) == totalDisbursedAmount.
  N6  scale REPORT for totalOutstandingAmount — reported, not asserted, because the observation is
      the point. No expected value is asserted for a field nobody has previously observed.

No floating point: every money value is parsed with decimal.Decimal and converted to integer minor
units before any comparison. No tolerance anywhere.
"""
import json
import re
import sys
from decimal import Decimal

PLAIN = re.compile(r"^-?\d+\.\d+$|^-?\d+$")


def minor(s, dp):
    d = Decimal(s)
    scaled = d * (10 ** dp)
    if scaled != scaled.to_integral_value():
        raise ValueError("value %r is finer than %d minor units" % (s, dp))
    return int(scaled)


def scale_ok(s, dp):
    if not PLAIN.match(s):
        return False
    if dp == 0:
        return "." not in s
    return "." in s and len(s.split(".")[1]) == dp


def main(path):
    doc = json.load(open(path, encoding="utf-8"))
    rows = []
    outstanding_scales = {}
    for c in doc["captures"]:
        o = c.get("observed")
        if o is None:
            continue
        i = c["inputs"]
        dp = i["currencyDecimalPlaces"]
        per = o["periods"]
        rep = [p for p in per if p["type"] == "REPAYMENT"]

        n1 = True
        prev_due = None
        for p in rep:
            if prev_due is not None and p["periodFromDate"] != prev_due:
                n1 = False
                break
            prev_due = p["dueDate"]
        n2 = rep[0]["periodFromDate"] == i["scheduleGenerationStartDate"]
        fees = [p["feeAmount"] for p in rep]
        pens = [p["penaltyAmount"] for p in rep]
        n3 = all(scale_ok(v, dp) and Decimal(v) >= 0 for v in fees + pens)
        n4 = (sum(minor(v, dp) for v in fees) == minor(o["totalFeeAmount"], dp)
              and sum(minor(v, dp) for v in pens) == minor(o["totalPenaltyAmount"], dp))
        n5 = (minor(o["totalPrincipalAmount"], dp) == sum(minor(p["principal"], dp) for p in rep)
              == minor(o["totalDisbursedAmount"], dp))
        outstanding_scales.setdefault(o["totalOutstandingAmount"], []).append(c["id"])
        rows.append((c["id"], [n1, n2, n3, n4, n5]))

    hdr = ["N1", "N2", "N3", "N4", "N5"]
    print(f"{'capture':<14} " + " ".join(f"{h:>3}" for h in hdr) + "   verdict")
    allok = True
    for cid, res in rows:
        cells = " ".join(("  ." if r else "!!!").rjust(3) for r in res)
        print(f"{cid:<14} {cells}   {'PASS' if all(res) else 'FAIL'}")
        allok = allok and all(res)
    print("\nlegend: '.' = holds, '!!!' = violated")
    print("N1-N5 verdict:", "ALL PASS" if allok else "FAILURES")

    print("\nN6 REPORT — totalOutstandingAmount as emitted (observation, not assertion):")
    for value, ids in sorted(outstanding_scales.items()):
        print("  %-8r on %d captures: %s" % (value, len(ids), ", ".join(sorted(ids))))

    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
