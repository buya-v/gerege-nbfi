"""
T34 (B): the `periodRatio` multiplier that DEC-1 revision 6 never mentions.

DEC-1 4.3.2 writes the rateFactorTillPeriodDueDate NORMATIVELY as

    rateFactorTillPeriodDueDate = setScale( (rate x 30 x RepaymentEvery / 360)
                                            x actualDaysInPeriod / calculatedDaysInPeriod,
                                            RateFactorScale )                       # :1961-1962

and 4.1.1 states the call chain as
    ":1355-1356 -> :1403-1412 -> rateFactorByRepaymentEveryMonth :1923-1927
     -> rateFactorByRepaymentPeriod :1950-1966, and :1486-1487 -> :1536 -> the same two."

The pinned checkout does NOT pass RepaymentEvery on the first of those chains.
`calculateRateFactorPerPeriodForInterest` computes

    BigDecimal periodRatio = switch (repaymentFrequency) { ...
        case MONTHS -> calculatePeriodRatio(scheduleModel, repaymentPeriod, ChronoUnit.MONTHS, mc); ... };
    return calculateRateFactorPerPeriodBasedOnRepaymentFrequency(interestRate, repaymentFrequency,
            periodRatio, BigDecimal.valueOf(30), daysInYear, actualDaysInPeriod, calculatedDaysInPeriod, mc);
                                                    [ProgressiveEMICalculator.java:1404-1413]

so the value landing in `rateFactorByRepaymentPeriod`'s `repaymentEvery` slot (:1951, used at
:1957) is `periodRatio`, NOT RepaymentEvery.  The recurrence's entry point
`calculateRateFactorPerPeriod` DOES pass `repaymentEvery` [:1536].

This file implements `calculatePeriodRatio` [:1419-1458] and `calculateSeedDate`
[:1460-1479] from the pinned checkout and measures where the two readings diverge
in money inside DEC-1 section 3.1's graded domain.

*** NO ORACLE WAS CONTACTED.  Every figure below is a RE-DERIVATION from the
*** pinned source, recorded as a CANDIDATE SHAPE TO CAPTURE, never an observation.
"""
from __future__ import annotations

import calendar
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t34_model import (Request, generate, totals, m2s, round_mc,
                       add_months_clamped, repayment_boundaries, MINOR)


def months_between(a: date, b: date) -> int:
    """java.time.ChronoUnit.MONTHS.between -- LocalDate.monthsUntil:
       packed = prolepticMonth * 32 + dayOfMonth; (packed2 - packed1) / 32
    with Java integer division (truncates toward zero)."""
    p1 = (a.year * 12 + a.month - 1) * 32 + a.day
    p2 = (b.year * 12 + b.month - 1) * 32 + b.day
    diff = p2 - p1
    q = abs(diff) // 32
    return q if diff >= 0 else -q


def minus_months_clamped(d: date, k: int) -> date:
    return add_months_clamped(d, -k)


def calculate_seed_date(schedule_start: date, rp_from: date, rp_due: date,
                        repay_every: int) -> date:
    """ProgressiveEMICalculator.calculateSeedDate, :1460-1479.
    seedDate starts at scheduleModel.getStartDate(), which is the FIRST repayment
    period's FromDate (ProgressiveLoanInterestScheduleModel.java:209-211) --
    i.e. GenerateRequest.ScheduleStartDate."""
    seed = schedule_start
    mult = 1
    while True:
        calculated = add_months_clamped(seed, mult)
        mult += 1
        if not (calculated < rp_due):
            break
    if calculated == rp_due and minus_months_clamped(calculated, repay_every) == rp_from:
        return seed
    return rp_from


def calculate_period_ratio(schedule_start: date, rp_from: date, rp_due: date,
                           repay_every: int) -> Decimal:
    """ProgressiveEMICalculator.calculatePeriodRatio, :1419-1458, MONTHS arm."""
    seed = calculate_seed_date(schedule_start, rp_from, rp_due, repay_every)

    seed_day = seed.day
    target_day = rp_from.day
    target_last_day = calendar.monthrange(rp_from.year, rp_from.month)[1]
    if target_last_day == target_day and seed_day > target_day:
        n = months_between(seed, rp_from + timedelta(days=1))
    else:
        n = months_between(seed, rp_from)

    mult = n + 1
    from_date = rp_from
    while from_date < rp_due:
        from_date = add_months_clamped(seed, mult)
        if not (from_date > rp_due):
            mult += 1
        else:
            full_period_date = from_date
            mult = mult - n - 1
            from_date = add_months_clamped(seed, mult)
            difference = (rp_due - from_date).days
            full_difference = (full_period_date - from_date).days
            return round_mc(Decimal(difference) / Decimal(full_difference)) + Decimal(mult)
    mult = mult - n - 1
    return Decimal(mult)


def period_ratios_for(req: Request) -> list[Decimal]:
    bounds = repayment_boundaries(req.start, req.disb, req.n, req.every)
    return [calculate_period_ratio(req.start, f, d, req.every) for f, d in bounds]


def both(req: Request):
    a = generate(req)                                       # DEC-1 as written
    b = generate(req, multipliers=period_ratios_for(req))   # the pinned source
    return a, b


def diverges(req: Request) -> bool:
    a, b = both(req)
    if totals(a) != totals(b):
        return True
    for x, y in zip(a, b):
        if (x.principal_minor, x.interest_minor, x.outstanding_minor,
                x.emi_minor) != (y.principal_minor, y.interest_minor,
                                 y.outstanding_minor, y.emi_minor):
            return True
    return False
