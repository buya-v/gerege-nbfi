#!/usr/bin/env python3
"""T22 audit probe — INDEPENDENT re-derivation of the Path B progressive schedule
from the pinned Fineract source, written from the algorithm, not from the output.

Source of every step (all paths relative to /Users/buv/fineract, commit 426a23544):

  rate factor, SAME_AS_REPAYMENT_PERIOD + MONTHLY short-circuit
      fineract-progressive-loan/.../calc/ProgressiveEMICalculator.java:1510-1516
  rateFactorByRepaymentPeriod formula
      ProgressiveEMICalculator.java:1950-1965
  interestRate = rate/100 at mc
      ProgressiveEMICalculator.java:1318
  rateFactorPlus1 = 1 + sum(interest period rate factors)  (EXACT add, no mc)
      calc/data/RepaymentPeriod.java:217
  rateFactorPlus1N = product over periods, each multiply(mc)
      ProgressiveEMICalculator.java:1816-1820
  fnResult = periods.skip(1) reduce fn = 1 + fn*rfp1 (mc)
      ProgressiveEMICalculator.java:1822-1827, fnValue at :1991-1993
  EMI = rateFactorPlus1N * balance / fnResult   (mc)
      ProgressiveEMICalculator.java:1838-1841, applied at :1730-1733
  Money.of -> stripTrailingZeros().setScale(decimalPlaces, mc.roundingMode)
      fineract-core/.../monetary/domain/Money.java:40-52
  applyInstallmentAmountInMultiplesOf / safeRoundingForEMI
      ProgressiveEMICalculator.java:1761-1776
  Money.roundToMultiplesOf: divide(multiple, scale 0, mc.roundingMode) * multiple
      Money.java:148-156 / :157-168
  per-period interest = balance * rateFactor, then Money.of -> 2dp
      calc/data/InterestPeriod.java:145-158 ; RepaymentPeriod.java:252-259
  duePrincipal = EMI - dueInterest
      RepaymentPeriod.java:345-350
  final-installment residual absorption:
      diff = totalDisbursed + totalDueInterest - totalEMI ; lastEmi += diff
      ProgressiveEMICalculator.java:1160-1218 (esp. :1200-1204)
  the schedule's MathContext is the TENANT's
      LoanScheduleAssembler.java:753  final MathContext mc = MoneyHelper.getMathContext();
      MoneyHelper.PRECISION = 19 (MoneyHelper.java:34); mode from c_configuration.rounding-mode
"""
import json
import sys
from decimal import Decimal, localcontext, ROUND_HALF_EVEN, ROUND_HALF_UP

PREC = 19
MODES = {"HALF_EVEN": ROUND_HALF_EVEN, "HALF_UP": ROUND_HALF_UP}


class MC:
    """A BigDecimal-style MathContext: `prec` significant digits, `mode` rounding."""

    def __init__(self, prec, mode):
        self.prec = prec
        self.mode = MODES[mode]
        self.name = mode

    def op(self, fn):
        with localcontext() as ctx:
            ctx.prec = self.prec
            ctx.rounding = self.mode
            return fn()

    def mul(self, a, b):
        return self.op(lambda: a * b)

    def div(self, a, b):
        return self.op(lambda: a / b)

    def add(self, a, b):
        return self.op(lambda: a + b)

    def set_scale(self, x, n):
        """BigDecimal.setScale(n, mode) — n DECIMAL PLACES, not significant digits."""
        with localcontext() as ctx:
            ctx.prec = 60
            ctx.rounding = self.mode
            return x.quantize(Decimal(1).scaleb(-n))

    def money(self, x, decimals=2):
        """Money.of(currency, x, mc) — Money.java:40-52."""
        return self.set_scale(x, decimals)

    def round_to_multiples_of(self, x, multiple):
        """Money.roundToMultiplesOf — Money.java:157-168."""
        q = self.set_scale(self.op(lambda: x / Decimal(multiple)), 0)
        with localcontext() as ctx:
            ctx.prec = 60
            return self.money(q * Decimal(multiple))


def rate_factor_same_as_repayment_monthly(annual_rate_pct, mc, repay_every=1, days=31):
    """ProgressiveEMICalculator.java:1510-1516 -> :1950-1965.

    daysInYear is the literal 12; actualDaysInPeriod == calculatedDaysInPeriod
    for a single interest period, so the trailing ratio is exactly 1 and the
    CALENDAR NEVER ENTERS. Neither daysInYearType, daysInMonthType nor
    daysInYearCustomStrategy is consulted on this branch."""
    interest_rate = mc.div(annual_rate_pct, Decimal(100))          # :1318
    fraction = mc.div(mc.mul(Decimal(1), Decimal(repay_every)), Decimal(12))
    v = mc.div(mc.mul(mc.mul(interest_rate, fraction), Decimal(days)), Decimal(days))
    return mc.set_scale(v, mc.prec)                                 # :1964


def rate_factor_days30_days360(annual_rate_pct, mc, repay_every=1, days=31):
    """Path A's configuration: DAYS_30 / DAYS_360, monthly.
    ProgressiveEMICalculator.java:1536-1537 -> :1922-1926 -> :1950-1965.
    Multiplier is daysInMonth=30, daysInYear=360."""
    interest_rate = mc.div(annual_rate_pct, Decimal(100))
    fraction = mc.div(mc.mul(Decimal(30), Decimal(repay_every)), Decimal(360))
    v = mc.div(mc.mul(mc.mul(interest_rate, fraction), Decimal(days)), Decimal(days))
    return mc.set_scale(v, mc.prec)


def schedule(principal, n, rate_factors, mc, multiples_of=None):
    """Full progressive declining-balance schedule."""
    rfp1 = [Decimal(1) + rf for rf in rate_factors]                 # RepaymentPeriod.java:217

    rate_factor_n = Decimal(1)                                      # :1816-1820
    for v in rfp1:
        rate_factor_n = mc.mul(rate_factor_n, v)
    fn = Decimal(1)                                                 # :1822-1827
    for v in rfp1[1:]:
        fn = mc.add(Decimal(1), mc.mul(fn, v))

    emi_raw = mc.div(mc.mul(rate_factor_n, principal), fn)          # :1838-1841
    emi = mc.money(emi_raw)                                         # Money.of
    emi_unrounded = emi
    if multiples_of:                                                # :1761-1776
        rounded = mc.round_to_multiples_of(emi, multiples_of)
        emi = emi_unrounded if (rounded == 0 and emi_unrounded > 0) else rounded

    def run(emi_all, emi_last):
        bal = principal
        rows = []
        for i in range(n):
            e = emi_last if i == n - 1 else emi_all
            interest = mc.money(mc.mul(bal, rate_factors[i]))       # InterestPeriod.java:151-158
            due_interest = min(interest, e)                         # RepaymentPeriod.java:272-286
            due_principal = e - due_interest                        # :345-350
            bal = bal - due_principal
            rows.append((due_principal, due_interest, e, bal))
        return rows

    rows = run(emi, emi)
    total_due_interest = sum((r[1] for r in rows), Decimal(0))
    total_emi = sum((r[2] for r in rows), Decimal(0))
    diff = principal + total_due_interest - total_emi               # :1200-1204
    emi_last = emi + diff
    rows = run(emi, emi_last)
    return dict(emi=emi, emi_unrounded=emi_unrounded, emi_last=emi_last,
                diff=diff, rows=rows, rate_factor=rate_factors[0],
                rate_factor_n=rate_factor_n, fn=fn, emi_raw=emi_raw)


def observed(path):
    with open(path, "rb") as fh:
        j = json.loads(fh.read().decode("utf-8"), parse_float=Decimal,
                       parse_int=lambda s: Decimal(s))
    rows = []
    for p in j["periods"]:
        if "period" not in p:
            continue
        rows.append((Decimal(p["principalDue"]), Decimal(p["interestDue"]),
                     Decimal(p["totalDueForPeriod"]),
                     Decimal(p["principalLoanBalanceOutstanding"]),
                     p["daysInPeriod"]))
    return j, rows


def compare(label, path, mc, multiples_of=None, rf_fn=rate_factor_same_as_repayment_monthly):
    j, obs = observed(path)
    days = [int(r[4]) for r in obs]
    rfs = [rf_fn(Decimal("21.6"), mc, 1, d) for d in days]
    d = schedule(Decimal(1200000), 12, rfs, mc, multiples_of)
    print("=" * 88)
    print("%s   mc=(%d, %s)  multiplesOf=%s" % (label, mc.prec, mc.name, multiples_of))
    print("  rateFactor(p1)   = %s" % d["rate_factor"])
    print("  rateFactorPlus1N = %s" % d["rate_factor_n"])
    print("  fnResult         = %s" % d["fn"])
    print("  EMI raw          = %s" % d["emi_raw"])
    print("  EMI (Money.of)   = %s   -> after multiplesOf: %s" % (d["emi_unrounded"], d["emi"]))
    print("  residual diff    = %s   -> final installment EMI %s" % (d["diff"], d["emi_last"]))
    print("  per  derived_principal derived_interest derived_total  |  observed  match")
    ok = True
    for i, (dp, di, dt, db) in enumerate(d["rows"]):
        op, oi, ot, ob, _ = obs[i]
        m = (dp == op and di == oi and dt == ot and db == ob)
        ok &= m
        print("  %3d  %15s %16s %13s  |  %s %s %s  %s"
              % (i + 1, dp, di, dt, op, oi, ot, "OK" if m else "**MISMATCH**"))
        if not m:
            print("       derived bal=%s observed bal=%s" % (db, ob))
    tot_i = sum((r[1] for r in d["rows"]), Decimal(0))
    tot_t = sum((r[2] for r in d["rows"]), Decimal(0))
    m1 = tot_i == Decimal(j["totalInterestCharged"])
    m2 = tot_t == Decimal(j["totalRepaymentExpected"])
    ok &= m1 and m2
    print("  totalInterest derived=%s observed=%s %s" % (tot_i, j["totalInterestCharged"], "OK" if m1 else "**MISMATCH**"))
    print("  totalRepay    derived=%s observed=%s %s" % (tot_t, j["totalRepaymentExpected"], "OK" if m2 else "**MISMATCH**"))
    print("  => %s" % ("REPRODUCED DIGIT-FOR-DIGIT" if ok else "DOES NOT REPRODUCE"))
    return ok


if __name__ == "__main__":
    W = sys.argv[1]
    he = MC(PREC, "HALF_EVEN")
    ok = True
    ok &= compare("B-01 baseline (server, SAME_AS_REPAYMENT_PERIOD, Actual/Actual)",
                  W + "/out/B-01-baseline-raw.json", he)
    ok &= compare("B-02 installmentAmountInMultiplesOf=100",
                  W + "/out/B-02-multiplesof100-raw.json", he, multiples_of=100)
    print("=" * 88)
    print("OVERALL: %s" % ("PASS" if ok else "FAIL"))
