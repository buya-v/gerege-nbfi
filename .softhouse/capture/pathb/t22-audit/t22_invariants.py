#!/usr/bin/env python3
"""T22 INDEPENDENT AUDIT — mechanical invariant check over the Path B raw captures.

Written from scratch for the audit; it does not import or reuse the prior
worker's t22-probe/invariants.py (whose I5 verdict was hard-coded True).

Money is read as EXACT DECIMAL (json.loads(parse_float=Decimal, parse_int=Decimal)),
never as a binary float, and every comparison is performed in INTEGER MINOR UNITS.
No tolerance is applied anywhere.

Invariants:
  I1  sum(principalDue over repayment periods) == totalPrincipalDisbursed
  I2  final principalLoanBalanceOutstanding == 0
  I3  sum(interestDue) == totalInterestCharged
  I4  sum(totalDueForPeriod) == totalRepaymentExpected
  I5  per period: principalDue + interestDue + feeChargesDue + penaltyChargesDue
                  == totalDueForPeriod                      (splits sum to whole)
  I6  totalPrincipalDisbursed + totalInterestCharged
      + totalFeeChargesCharged + totalPenaltyChargesCharged == totalRepaymentExpected
  S1  every money literal in the document is exactly representable in minor units
  S2  running balance ties: bal[n] == bal[n-1] - principalDue[n]
  S3  disbursement pseudo-period: principalDisbursed == totalPrincipalDisbursed
  S4  loanTermInDays == (last dueDate - first fromDate) in days
                        and == sum(daysInPeriod)
"""
import datetime
import json
import sys
from decimal import Decimal

MONEY_KEYS_SKIP = {"period", "daysInPeriod", "dueDate", "fromDate",
                   "downPaymentPeriod", "decimalPlaces", "inMultiplesOf",
                   "loanTermInDays"}


def load(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"),
                          parse_float=Decimal, parse_int=Decimal)


def minor(d, scale, where):
    s = d * (10 ** scale)
    if s != s.to_integral_value():
        raise AssertionError("S1 NON-INTEGRAL MINOR UNIT at %s: %s" % (where, d))
    return int(s)


def walk_money(o, scale, path, bad):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in MONEY_KEYS_SKIP:
                continue
            walk_money(v, scale, path + "." + k, bad)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk_money(v, scale, "%s[%d]" % (path, i), bad)
    elif isinstance(o, Decimal):
        s = o * (10 ** scale)
        if s != s.to_integral_value():
            bad.append((path, str(o)))


def check(path, label):
    j = load(path)
    cur = j["currency"]
    scale = int(cur["decimalPlaces"])
    print("=" * 88)
    print("%s  (%s)" % (label, path.rsplit("/", 1)[-1]))
    print("  currency=%s scale=%d inMultiplesOf=%s loanTermInDays=%s"
          % (cur["code"], scale, cur["inMultiplesOf"], j["loanTermInDays"]))

    disb = minor(j["totalPrincipalDisbursed"], scale, "totalPrincipalDisbursed")
    tint = minor(j["totalInterestCharged"], scale, "totalInterestCharged")
    tfee = minor(j["totalFeeChargesCharged"], scale, "totalFeeChargesCharged")
    tpen = minor(j["totalPenaltyChargesCharged"], scale, "totalPenaltyChargesCharged")
    trep = minor(j["totalRepaymentExpected"], scale, "totalRepaymentExpected")

    disb_rows = [p for p in j["periods"] if "period" not in p]
    rows = [p for p in j["periods"] if "period" in p]

    sp = si = sf = spen = st = 0
    prev = disb
    s2 = []
    i5 = []
    sdays = 0
    print("  per fromDate    dueDate     days  principal    interest   total        balance")
    for p in rows:
        pr = minor(p["principalDue"], scale, "principalDue")
        it = minor(p["interestDue"], scale, "interestDue")
        fe = minor(p["feeChargesDue"], scale, "feeChargesDue")
        pe = minor(p["penaltyChargesDue"], scale, "penaltyChargesDue")
        td = minor(p["totalDueForPeriod"], scale, "totalDueForPeriod")
        bal = minor(p["principalLoanBalanceOutstanding"], scale, "balance")
        sp += pr; si += it; sf += fe; spen += pe; st += td
        sdays += int(p["daysInPeriod"])
        if pr + it + fe + pe != td:
            i5.append((int(p["period"]), pr + it + fe + pe, td))
        if prev - pr != bal:
            s2.append((int(p["period"]), prev - pr, bal))
        prev = bal
        print("  %3d %-11s %-11s %4d  %10d  %10d  %10d  %11d"
              % (int(p["period"]),
                 "-".join(str(int(x)) for x in p["fromDate"]),
                 "-".join(str(int(x)) for x in p["dueDate"]),
                 int(p["daysInPeriod"]), pr, it, td, bal))

    bad = []
    walk_money(j, scale, "$", bad)

    first_from = [int(x) for x in rows[0]["fromDate"]]
    last_due = [int(x) for x in rows[-1]["dueDate"]]
    span = (datetime.date(*last_due) - datetime.date(*first_from)).days

    res = []

    def v(name, ok, detail):
        res.append(ok)
        print("  %-4s %-64s %s" % (name, detail, "PASS" if ok else "**FAIL**"))

    v("I1", sp == disb, "sum(principal)=%d disbursed=%d" % (sp, disb))
    v("I2", prev == 0, "final outstanding=%d" % prev)
    v("I3", si == tint, "sum(interest)=%d totalInterestCharged=%d" % (si, tint))
    v("I4", st == trep, "sum(totalDue)=%d totalRepaymentExpected=%d" % (st, trep))
    v("I5", not i5, "splits sum to whole (%d break(s))%s"
      % (len(i5), "" if not i5 else " " + repr(i5)))
    v("I6", disb + tint + tfee + tpen == trep,
      "P+I+F+Pen=%d totalRepayment=%d" % (disb + tint + tfee + tpen, trep))
    v("S1", not bad, "all money literals integral in minor units (%d bad)%s"
      % (len(bad), "" if not bad else " " + repr(bad[:5])))
    v("S2", not s2, "running balance ties (%d break(s))%s"
      % (len(s2), "" if not s2 else " " + repr(s2)))
    v("S3", len(disb_rows) == 1
      and minor(disb_rows[0]["principalDisbursed"], scale, "d") == disb,
      "disbursement pseudo-period principal == totalPrincipalDisbursed")
    v("S4", span == int(j["loanTermInDays"]) == sdays,
      "loanTermInDays=%s span=%d sum(daysInPeriod)=%d"
      % (j["loanTermInDays"], span, sdays))

    ok = all(res)
    print("  RESULT: %s" % ("ALL PASS" if ok else "FAILURE"))
    return ok


if __name__ == "__main__":
    allok = True
    for arg in sys.argv[1:]:
        p, _, lab = arg.partition("::")
        allok &= check(p, lab or p)
    print("=" * 88)
    print("OVERALL: %s" % ("PASS" if allok else "FAIL"))
    sys.exit(0 if allok else 1)
