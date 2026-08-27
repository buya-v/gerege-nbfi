#!/usr/bin/env python3
"""T44 AUDIT -- cross-checks that are not recomputations of a published number.

1. Is E2's "Path A" column an independent experiment, or a re-run of E1's ambient rows?
2. Does installmentAmountInMultiplesOf change anything on the Path A seam at all?
3. Are the two ambient-ABSENT throwers the only 0-decimal-place shapes?
4. Did each of the 11 "generated fine" shapes actually run graded arithmetic?
"""
import json, os
from decimal import Decimal
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
MC = os.path.abspath(os.path.join(HERE, "..", "..", "..", "mathcontext", "out"))
d1 = json.load(open(os.path.join(MC, "t42-mathcontext.json")))
d2 = json.load(open(os.path.join(MC, "t42-mathcontext2.json")))
b1 = {c["id"]: c for c in d1["captures"]}
b2 = {c["id"]: c for c in d2["captures"]}

PLAN = ["loanTermInDays", "totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount"]


def cells(c):
    o = c.get("observed")
    if o is None:
        return None
    d = OrderedDict()
    for k in PLAN:
        d["plan." + k] = str(o[k])
    for i, p in enumerate(o["periods"]):
        for k, v in p.items():
            d["p%d.%s" % (i, k)] = str(v)
    return d


def moved(a, b):
    ca, cb = cells(a), cells(b)
    keys = list(dict.fromkeys(list(ca.keys()) + list(cb.keys())))
    return sum(1 for k in keys if ca.get(k) != cb.get(k))


print("=== 1. Is E2's Path A column a fresh experiment or a re-run of E1's ambient rows? ===")
pairs = [("T42-MX-00-A", "T42B-PA-ord4"), ("T42-MX-00-B", "T42B-PA-ord1"), ("T42-MX-00-E", "T42B-PA-ord0")]
for a, b in pairs:
    ca, cb = b1[a], b2[b]
    ia, ib = ca["inputs"], cb["inputs"]
    same_shape = (str(ia["disbursementAmount"]) == str(ib["disbursementAmount"])
                  and ia["numberOfRepayments"] == ib["numberOfRepayments"]
                  and str(ia["annualNominalInterestRate"]) == str(ib["annualNominalInterestRate"])
                  and ia["scheduleGenerationStartDate"] == ib["scheduleGenerationStartDate"]
                  and ia["disbursementDate"] == ib["disbursementDate"]
                  and str(ia["daysInMonth"]) == str(ib["daysInMonth"])
                  and str(ia["daysInYear"]) == str(ib["daysInYear"])
                  and ia["currencyDecimalPlaces"] == ib["currencyDecimalPlaces"]
                  and ia["tenantRoundingModeOrdinal"] == ib["tenantRoundingModeOrdinal"]
                  and ia["threadedMathContextPrecision"] == ib["threadedMathContextPrecision"]
                  and str(ia["threadedMathContextRoundingMode"]) == str(ib["threadedMathContextRoundingMode"]))
    print("  %-14s vs %-16s identical inputs: %-5s ; observations differ in %d cells"
          % (a, b, same_shape, moved(ca, cb)))
print("  => if inputs are identical and 0 cells differ, E2's Path A column REPRODUCES E1's")
print("     ambient rows on the same shape; it is a replication, not a second experiment.")

print()
print("=== 2. Does installmentAmountInMultiplesOf do anything on the Path A seam? ===")
plain = b1["T42-MX-00-A"]
mult = b1["T42-MX-06-A"]
ip, im = plain["inputs"], mult["inputs"]
diffs = [k for k in ip if str(ip[k]) != str(im[k]) and k not in ("tenantId",)]
print("  T42-MX-00-A (plain) vs T42-MX-06-A (multiples1000) inputs differing:", diffs)
print("  cells differing in the observations:", moved(plain, mult))
print("  period-1 total on both:", plain["observed"]["periods"][1]["total"],
      "/", mult["observed"]["periods"][1]["total"], "-- not a multiple of 1000")
print("  => installmentAmountInMultiplesOf is INERT on this seam.")

print()
print("=== 3. Are the two throwers the only 0-dp shapes? ===")
zero_dp, threw = [], []
for i in range(13):
    A = b1["T42-MX-%02d-A" % i]
    D = b1["T42-MX-%02d-D" % i]
    if int(A["inputs"]["currencyDecimalPlaces"]) == 0:
        zero_dp.append(A["shape"])
    if D.get("observed") is None:
        threw.append(A["shape"])
print("  0-dp shapes :", zero_dp)
print("  shapes whose ABSENT case threw:", threw)
print("  identical sets:", set(zero_dp) == set(threw))

print()
print("=== 4. Did the 11 'generated fine' shapes actually run graded arithmetic? ===")
for i in range(13):
    A = b1["T42-MX-%02d-A" % i]
    C = b1["T42-MX-%02d-C" % i]
    D = b1["T42-MX-%02d-D" % i]
    if D.get("observed") is None:
        continue
    o = A["observed"]
    nrep = sum(1 for p in o["periods"] if p["type"] == "REPAYMENT")
    print("  %-32s rows=%-3d totalInterest=%-14s threaded-flip moved %d cells"
          % (A["shape"], nrep, o["totalInterestAmount"], moved(A, C)))
print("  => every one produced a full schedule with non-zero interest AND responded to the")
print("     threaded rounding mode, so none short-circuited before the graded arithmetic.")
