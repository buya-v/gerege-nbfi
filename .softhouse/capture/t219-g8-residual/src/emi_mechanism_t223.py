#!/usr/bin/env python3
"""
T223 — G-8 region predicate, DERIVED FROM THE MECHANISM (T220's, driver-verified) rather than
fitted to the swept cells.

NO FLOATING POINT ANYWHERE (P-25). Every value on a decision path is `decimal.Decimal` under an
explicit Context, or `int` minor units, or `fractions.Fraction`. There is no `float()` call in this
file and no literal that becomes one.

WHAT THIS FILE IS
-----------------
A digit-for-digit re-execution, in Python `decimal`, of the arithmetic Fineract's
`ProgressiveEMICalculator` performs to produce the EMI for the ONE shape G-8 lives in:
MONTHS / repaymentEvery 1 / DECLINING_BALANCE / DAYS_30 / DAYS_360 / single disbursement on the
schedule start date / no down payment / no charges / both multiples-of null.

Sites re-verified BY CONTENT at pinned Fineract `426a23544e8426a38ae43ae404670a0a7e85b9eb`
(line numbers still hold, and are quoted because they were checked, not because they were copied):

  ProgressiveEMICalculator.java:1950-1963  rateFactorByRepaymentPeriod
      interestRate.multiply(interestFractionPerPeriod, mc).multiply(actualDaysInPeriod, mc)
                  .divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode())
      -> mc.getPrecision() = 19 is consumed as DECIMAL PLACES.  [VERIFIED]
  ProgressiveEMICalculator.java:1925       rateFactorByRepaymentEveryMonth passes
      (interestRate, daysInMonth=30, repaymentEvery, daysInYear=360, actualDays, calculatedDays)
  ProgressiveEMICalculator.java:1319       calcNominalInterestRatePercentage = rate.divide(100, mc)
  RepaymentPeriod.java:216-217             calculateRateFactorPlus1 =
      interestPeriods.stream().map(getRateFactor).reduce(BigDecimal.ONE, BigDecimal::add)
      -> the TWO-ARGUMENT add, NO MathContext.  [VERIFIED]
  ProgressiveEMICalculator.java:1816-1820  rateFactorN  = reduce(ONE, (a,v) -> a.multiply(v, mc))
  ProgressiveEMICalculator.java:1822-1828  fnResult     = skip(1).reduce(ONE, fnValue)
  ProgressiveEMICalculator.java:1991-1993  fnValue      = ONE.add(prev.multiply(rf, mc), mc)
  ProgressiveEMICalculator.java:1838-1841  calculateEMIValue = rfN.multiply(B, mc).divide(fn, mc)
  Money.java:40-53                         Money(..) = amount.stripTrailingZeros()
                                                       .setScale(currency.getDecimalPlaces(),
                                                                 getMc().getRoundingMode())
      -> the EMI is quantized to `minorUnitDigits` places with the TENANT rounding mode (HALF_UP).

THE PREDICATE (registered before any probe; see ../PREDICTION.md)
----------------------------------------------------------------
Let E_q  = the oracle's EMI after the Money quantization above, in integer minor units.
Let I_1  = B_minor * rateFactor_1, the EXACT first-period interest in minor units (a Fraction).

    FAMILY B (the loan never amortizes)  <=>  E_q <= I_1

Rationale, from the mechanism and not from the cells: the scheduled instalment is the only source of
principal, so principal can only be paid out of what is left of the instalment after the period's
interest. Exact annuity arithmetic guarantees E_exact = I_1 / (1 - (1+r)^-n) > I_1 strictly, for
every n. The excess is E_exact - I_1 = I_1 * (1+r)^-n / (1 - (1+r)^-n), which shrinks GEOMETRICALLY
in n. Once that excess falls inside the resolution of the oracle's own 19-significant-digit
arithmetic, the computed EMI can land on or below I_1 -- and then no period ever pays principal.
"""

import datetime
from decimal import Decimal, Context, ROUND_HALF_UP, ROUND_DOWN
from fractions import Fraction

# The production MathContext. MoneyHelper.PRECISION = 19 is a compile-time constant; the tenant is
# HALF_UP (RoundingMode ordinal 4). [CLAUDE.md ratified tenant parameters]
PRECISION = 19
MC = Context(prec=PRECISION, rounding=ROUND_HALF_UP)
# A context wide enough that the operations Fineract performs WITHOUT a MathContext (the two-arg
# BigDecimal.add, the setScale, the Money setScale) are exact here too.
WIDE = Context(prec=400, rounding=ROUND_HALF_UP)

SCALE_19 = Decimal(1).scaleb(-19)


def month_day_counts(start: datetime.date, n: int):
    """Actual calendar days in each of the n monthly repayment periods, first-of-month anchored.

    DefaultScheduledDateGenerator advances the due date by `repaymentEvery` months; every cell G-8
    lives in starts on the 1st, so the day count is just the length of the calendar month.
    """
    out = []
    y, m = start.year, start.month
    prev = start
    for _ in range(n):
        m += 1
        if m == 13:
            m = 1
            y += 1
        cur = datetime.date(y, m, start.day)
        out.append((cur - prev).days)
        prev = cur
    return out


def rate_factor(annual_pct: Decimal, actual_days: int, calc_days: int,
                days_in_month: int = 30, repayment_every: int = 1, days_in_year: int = 360) -> Decimal:
    """ProgressiveEMICalculator.rateFactorByRepaymentPeriod, digit for digit."""
    interest_rate = MC.divide(annual_pct, Decimal(100))                      # :1319
    frac = MC.divide(MC.multiply(Decimal(days_in_month), Decimal(repayment_every)),
                     Decimal(days_in_year))                                  # :1957-1958
    v = MC.multiply(interest_rate, frac)                                     # :1960-1961
    v = MC.multiply(v, Decimal(actual_days))
    v = MC.divide(v, Decimal(calc_days))
    # setScale(mc.getPrecision(), mc.getRoundingMode()) -- 19 DECIMAL PLACES, not 19 digits. :1962
    return WIDE.quantize(v, SCALE_19)


def emi_raw(annual_pct: Decimal, n: int, disbursed: Decimal, start=datetime.date(2024, 1, 1)):
    """Returns (emi_before_money_quantization, rate_factor_of_period_1, [rateFactorPlus1 per period])."""
    days = month_day_counts(start, n)
    rfs = [rate_factor(annual_pct, d, d) for d in days]
    # RepaymentPeriod.calculateRateFactorPlus1 :217 -- two-arg add, NO MathContext, so exact.
    rfp1 = [WIDE.add(Decimal(1), rf) for rf in rfs]

    acc = Decimal(1)
    for v in rfp1:                                                           # :1816-1820
        acc = MC.multiply(acc, v)
    rate_factor_n = acc

    fn = Decimal(1)
    for v in rfp1[1:]:                                                       # :1822-1828, :1991-1993
        fn = MC.add(Decimal(1), MC.multiply(fn, v))
    fn_result = fn

    emi = MC.divide(MC.multiply(rate_factor_n, disbursed), fn_result)        # :1838-1841
    return emi, rfs[0], rate_factor_n, fn_result


def predict(annual_pct_str: str, n: int, b_minor: int, minor_digits: int = 2,
            start=datetime.date(2024, 1, 1)):
    """The registered predicate. Returns a dict; `family_b` is the falsifiable bit."""
    annual = Decimal(annual_pct_str)
    disbursed = WIDE.quantize(Decimal(b_minor).scaleb(-minor_digits),
                              Decimal(1).scaleb(-minor_digits))
    emi, rf1, rfn, fnr = emi_raw(annual, n, disbursed, start)
    # Money(..) :40-53 -- setScale(decimalPlaces, tenant rounding mode = HALF_UP)
    emi_q = WIDE.quantize(emi, Decimal(1).scaleb(-minor_digits))  # WIDE rounds HALF_UP
    emi_q_minor = int(emi_q.scaleb(minor_digits).to_integral_value(rounding=ROUND_DOWN))
    # I_1 exactly, in minor units, as a Fraction -- no rounding at all.
    i1 = Fraction(b_minor) * Fraction(rf1)
    return {
        "annualRate": annual_pct_str,
        "n": n,
        "bMinor": b_minor,
        "minorDigits": minor_digits,
        "rateFactorPeriod1": str(rf1),
        "emiRaw": str(emi),
        "emiQuantizedMinor": emi_q_minor,
        "i1ExactMinorNum": i1.numerator,
        "i1ExactMinorDen": i1.denominator,
        "i1ExactMinorStr": str(i1),
        "familyB": emi_q_minor <= i1,
        "marginMinorStr": str(Fraction(emi_q_minor) - i1),
    }
