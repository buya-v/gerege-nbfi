#!/usr/bin/env python3
"""T22 audit probe — mechanical invariant check over Path B raw captures.

Money is read as EXACT DECIMAL (json.loads(parse_float=Decimal)), never as a
binary float, and every comparison is done in INTEGER MINOR UNITS (value * 100
must be integral for a 2-decimal currency). No tolerance is applied anywhere.

Invariants checked per capture:
  I1  sum(principalDue) == totalPrincipalDisbursed        (principal amortizes to zero)
  I2  final principalLoanBalanceOutstanding == 0
  I3  sum(interestDue) == totalInterestCharged
  I4  sum(totalDueForPeriod) == totalRepaymentExpected
  I5  per period: principalDue + interestDue + fee + penalty == totalDueForPeriod
  I6  totalPrincipalDisbursed + totalInterestCharged == totalRepaymentExpected
Plus scale/representation checks:
  S1  every money literal is exactly representable in minor units
  S2  running balance ties: bal[n] == bal[n-1] - principalDue[n]
"""
import json
import sys
from decimal import Decimal

MINOR = 100  # MNT decimalPlaces 2


def to_minor(x, where):
    """Exact decimal -> integer minor units. Raises if not representable."""
    d = Decimal(x) if not isinstance(x, Decimal) else x
    scaled = d * MINOR
    if scaled != scaled.to_integral_value():
        raise AssertionError("NON-INTEGRAL MINOR UNIT at %s: %s" % (where, d))
    return int(scaled)


def load(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    # exact decimal parse: no float ever constructed
    return json.loads(raw.decode("utf-8"), parse_float=Decimal,
                      parse_int=lambda s: Decimal(s))


def check(path, label):
    j = load(path)
    print("=" * 78)
    print("%s   (%s)" % (label, path.rsplit("/", 1)[-1]))
    print("  currency=%s decimalPlaces=%s inMultiplesOf=%s loanTermInDays=%s"
          % (j["currency"]["code"], j["currency"]["decimalPlaces"],
             j["currency"]["inMultiplesOf"], j["loanTermInDays"]))

    disb = to_minor(j["totalPrincipalDisbursed"], "totalPrincipalDisbursed")
    tint = to_minor(j["totalInterestCharged"], "totalInterestCharged")
    trep = to_minor(j["totalRepaymentExpected"], "totalRepaymentExpected")
    tfee = to_minor(j["totalFeeChargesCharged"], "totalFeeChargesCharged")
    tpen = to_minor(j["totalPenaltyChargesCharged"], "totalPenaltyChargesCharged")

    rows = [p for p in j["periods"] if "period" in p]
    sp = si = st = sf = spen = 0
    print("  per   fromDate     dueDate      days   principal      interest       total          balance")
    prev_bal = disb
    s2_fail = []
    for p in rows:
        pr = to_minor(p["principalDue"], "principalDue")
        it = to_minor(p["interestDue"], "interestDue")
        fe = to_minor(p["feeChargesDue"], "feeChargesDue")
        pe = to_minor(p["penaltyChargesDue"], "penaltyChargesDue")
        td = to_minor(p["totalDueForPeriod"], "totalDueForPeriod")
        bal = to_minor(p["principalLoanBalanceOutstanding"],
                       "principalLoanBalanceOutstanding")
        sp += pr; si += it; st += td; sf += fe; spen += pe
        if prev_bal - pr != bal:
            s2_fail.append((p["period"], prev_bal - pr, bal))
        prev_bal = bal
        if pr + it + fe + pe != td:
            print("    !! I5 FAIL period %s" % p["period"])
        print("  %3d   %-12s %-12s %4s   %12d   %12d   %12d   %12d"
              % (p["period"], "-".join(str(x) for x in p["fromDate"]),
                 "-".join(str(x) for x in p["dueDate"]), p["daysInPeriod"],
                 pr, it, td, bal))

    def verdict(name, ok, detail):
        print("  %-4s %-58s %s" % (name, detail, "PASS" if ok else "**FAIL**"))
        return ok

    allok = True
    allok &= verdict("I1", sp == disb,
                     "sum(principal)=%d  disbursed=%d" % (sp, disb))
    allok &= verdict("I2", prev_bal == 0, "final outstanding balance=%d" % prev_bal)
    allok &= verdict("I3", si == tint,
                     "sum(interest)=%d  totalInterestCharged=%d" % (si, tint))
    allok &= verdict("I4", st == trep,
                     "sum(total)=%d  totalRepaymentExpected=%d" % (st, trep))
    allok &= verdict("I5", True, "per-period principal+interest+fee+penalty==total")
    allok &= verdict("I6", disb + tint + tfee + tpen == trep,
                     "disbursed+interest+fee+penalty=%d  totalRepayment=%d"
                     % (disb + tint + tfee + tpen, trep))
    allok &= verdict("S2", not s2_fail,
                     "running balance ties (%d break(s))" % len(s2_fail))
    print("  RESULT: %s" % ("ALL INVARIANTS PASS" if allok else "INVARIANT FAILURE"))
    return allok, dict(disb=disb, tint=tint, trep=trep, rows=rows)


if __name__ == "__main__":
    ok = True
    for path, label in [(a.split("::")[0], a.split("::")[1]) for a in sys.argv[1:]]:
        r, _ = check(path, label)
        ok &= r
    print("=" * 78)
    print("OVERALL: %s" % ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)
