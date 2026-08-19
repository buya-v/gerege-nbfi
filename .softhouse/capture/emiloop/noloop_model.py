#!/usr/bin/env python3
"""The NO-LOOP counterfactual: Fineract's progressive schedule with
`checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` OMITTED.

This is a model of a WRONG PORT, never of the oracle. It exists to derive
(a) the value of the EmiAdjustment guard on the pre-adjustment model -- the state the
oracle actually evaluates it on, since the loop is called AFTER
calculateLastUnpaidRepaymentPeriodEMI (ProgressiveEMICalculator.java:747-749) -- and
(b) the minor-unit margin between the oracle's observed schedule and this counterfactual.

Every step is transcribed from source at the pinned commit 426a2354:
  rate factor      ProgressiveEMICalculator.java:1950-1963  (setScale(19, HALF_UP) at the end)
  rateFactorPlus1N :1816-1820   fold acc.multiply(1+r_i, mc)  -- not pow
  fnResult         :1822-1828 + fnValue :1988-1990  fold over skip(1): fn = 1 + fn_prev*(1+r_i)
  EMI              :1838-1841  rateFactorPlus1N * balance / fnResult
  EMI -> Money     Money.java:40-53  setScale(2, HALF_UP)
  per-period int   InterestPeriod.java:145-158, Money-wrapped RepaymentPeriod.java:252-265
  principal        RepaymentPeriod.java:345-350  EMI - dueInterest, via Money
  last-period EMI  :1176-1210  absorbs disbursed + dueInterest - sum(EMI)
  guard            EmiAdjustment.java:31-36  |lastEMI - penultEMI| * 100 > floor(n/2) currency units

NO FLOAT IS CONSTRUCTED ANYWHERE. Decimal only, at MathContext(19, ROUND_HALF_UP).
"""
from decimal import Decimal, Context, ROUND_HALF_UP

MC = Context(prec=19, rounding=ROUND_HALF_UP)
WIDE = Context(prec=60, rounding=ROUND_HALF_UP)


def q19(x):
    """BigDecimal.setScale(19, HALF_UP) -- a SCALE, 19 places after the point."""
    return x.quantize(Decimal(1).scaleb(-19), rounding=ROUND_HALF_UP, context=WIDE)


def money(x):
    """Money.of(...): setScale(currency.getDecimalPlaces()=2, mc.getRoundingMode()=HALF_UP)."""
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP, context=WIDE)


def rate_factor(annual_rate_percent, repayment_every=1, days_in_year=360, mult_days=30,
                actual_days=None, calculated_days=None):
    """rateFactorByRepaymentPeriod. Whole monthly periods under DAYS_30/DAYS_360 have
    actualDaysInPeriod == calculatedDaysInPeriod, so the ratio is exactly 1."""
    ir = MC.divide(Decimal(annual_rate_percent), Decimal(100))   # calcNominalInterestRatePercentage
    frac = MC.divide(MC.multiply(Decimal(mult_days), Decimal(repayment_every)), Decimal(days_in_year))
    ad = Decimal(actual_days if actual_days is not None else mult_days * repayment_every)
    cd = Decimal(calculated_days if calculated_days is not None else mult_days * repayment_every)
    v = MC.divide(MC.multiply(MC.multiply(ir, frac), ad), cd)
    return q19(v)


def emi_raw(principal, n, r):
    """calculateRateFactorPlus1NForEmi x balance / calculateFnResultForEmi, then Money."""
    rp1 = Decimal(1) + r
    acc = Decimal(1)
    for _ in range(n):
        acc = MC.multiply(acc, rp1)
    fn = Decimal(1)
    for _ in range(n - 1):                       # .skip(1): n-1 elements
        fn = MC.add(Decimal(1), MC.multiply(fn, rp1))
    return money(MC.divide(MC.multiply(acc, Decimal(principal)), fn)), acc, fn


def noloop_schedule(principal, n, annual_rate_percent):
    """The full pre-smoothing-loop schedule: raw EMI, per-period split, last-period balancing."""
    P = Decimal(principal)
    r = rate_factor(annual_rate_percent)
    emi, rp1n, fn = emi_raw(P, n, r)

    bal = P
    rows = []
    for _ in range(n):
        interest = money(MC.multiply(bal, r))    # single interest period: rateFactorTillDue == r
        prin = money(emi - interest)
        bal = bal - prin
        rows.append({"emi": emi, "interest": interest, "principal": prin, "closing": bal})

    # calculateLastUnpaidRepaymentPeriodEMI :1196-1204
    total_due_interest = sum((x["interest"] for x in rows), Decimal(0))
    total_emi = emi * n
    diff = P + total_due_interest - total_emi
    last_emi = rows[-1]["emi"] + diff

    # re-split the last row at the adjusted EMI
    opening_last = rows[-2]["closing"] if n > 1 else P
    rows[-1]["emi"] = last_emi
    rows[-1]["principal"] = money(last_emi - rows[-1]["interest"])
    rows[-1]["closing"] = opening_last - rows[-1]["principal"]
    return {"r": r, "emi": emi, "rateFactorPlus1N": rp1n, "fnResult": fn,
            "rows": rows, "lastEmi": last_emi,
            "penultEmi": rows[-2]["emi"] if n > 1 else None,
            "totalInterest": sum((x["interest"] for x in rows), Decimal(0))}


def guard(n, last_emi, penult_emi):
    """EmiAdjustment.shouldBeAdjusted (EmiAdjustment.java:31-36).
    Money.copy(double) REPLACES the amount (Money.java:220-222), so the threshold is
    floor(n/2) CURRENCY UNITS flat. |diff| * 100 > floor(n/2) is exactly
    |diff in minor units| > floor(n/2)."""
    lower_half = n // 2
    diff = last_emi - penult_emi
    lhs = abs(diff) * 100
    return {
        "n": n, "lowerHalfOfRelatedPeriods": lower_half,
        "lastEmi": last_emi, "penultimateEmi": penult_emi,
        "emiDifference": diff,
        "absDiffMinorUnits": int(abs(diff) * 100),
        "lhs_absDiffTimes100": lhs, "rhs_threshold": Decimal(lower_half),
        "trips": lower_half > 0 and diff != 0 and lhs > Decimal(lower_half),
    }
