#!/usr/bin/env python3
"""T30 — re-derive Path B captures `B-03` and `B-04` FROM THE PINNED FINERACT
SOURCE, through the DAILY / ACTUAL-ACTUAL arm, including the cross-year
partial-period branch.  Closes T22 P1-14's first clause.

> **NOT RUN AGAINST A LIVE ORACLE.**  No Fineract instance and no PostgreSQL was
> reachable in the sandbox where this was written and run.  **No oracle value is
> synthesized, invented or extrapolated here.**  Every observed number is read
> from a capture already committed on `main`
> (`.softhouse/capture/pathb/out/B-0{3,4}-*-raw.json`); every rule is re-read
> from the pinned Fineract checkout at `/home/user/fineract`
> @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`.  This script *models* the oracle;
> it does not *observe* it.

T22 §3 re-derived `B-01` and `B-02` (SAME_AS_REPAYMENT_PERIOD + MONTHLY
short-circuit) digit-for-digit but explicitly did NOT re-derive `B-03`/`B-04`,
because those run a materially different arm: `interestCalculationPeriodType =
DAILY` (0), `daysInYearType = ACTUAL` (1), `daysInMonthType = ACTUAL` (1), over a
term that spans a year boundary (2024-01-01 → 2025-01-01) and 29 Feb 2024.
That hole is what this script fills.

Pinned-source citations implemented below (all in the PROGRESSIVE generator —
never the cumulative one; that misattribution is a known hazard, T19 item 5):

  ProgressiveEMICalculator.java:636-643   calculateRateFactorForRepaymentPeriod:
        interestPeriod.rateFactor              = calculateRateFactorPerPeriod(from, ipDue)
        interestPeriod.rateFactorTillPeriodDue = calculateRateFactorPerPeriodForInterest(from, rpDue)
  ProgressiveEMICalculator.java:1318-1320 calcNominalInterestRatePercentage = rate/100 (mc)
  ProgressiveEMICalculator.java:1346-1353 getNumberOfDays(daysInYearType, customStrategy, ...):
        n = daysInYearType.getNumberOfDays(interestPeriodFromDate)
        if n == 366 and customStrategy == FEB_29_PERIOD_ONLY:
            n = numberOfDaysFeb29PeriodOnly(rpFrom, rpDue)          (:1342-1344)
  DaysInYearType.java:81-86               ACTUAL -> referenceDate.lengthOfYear()
  ProgressiveEMICalculator.java:1330-1340 isPeriodContainsFeb29: leap-day in (rpFrom, rpDue]
  ProgressiveEMICalculator.java:1504-1507 partialPeriodCalculationNeeded =
        daysInYearType == ACTUAL
        AND (ipDue.year - ipFrom.year) > 0
        AND (customStrategy != FEB_29_PERIOD_ONLY OR isPeriodContainsFeb29(rpFrom, rpDue))
      (identical predicate in the interest variant at :1371-1374)
  ProgressiveEMICalculator.java:1526-1531 partial arm ->
        rateFactorByRepaymentPartialPeriod(rate, ONE, cumulatedPeriodFractions, ONE, ONE, mc)
      (identical call in the interest variant at :1393-1398)
  ProgressiveEMICalculator.java:1550-1568 calculatePeriodFractions:
        Σ over years  days(actualDate → fractionDue) / Year.of(actualYear).length()   (mc)
        fractionDue = interestPeriodDueDate in the final year, else end-of-year (:1578-1584)
  ProgressiveEMICalculator.java:1578-1584 getFractionPeriodDueDateForEndOfYear ->
        isInterestRecognitionOnDisbursementDate ? (year+1)-01-01 : year-12-31   (false here)
  ProgressiveEMICalculator.java:1533-1535 non-partial, daysInMonthType == ACTUAL ->
        rateFactorByRepaymentPeriod(rate, actualDaysInPeriod, ONE, daysInYear, ONE, ONE, mc)
      (identical call in the interest variant at :1400-1402)
  ProgressiveEMICalculator.java:1948-1962 rateFactorByRepaymentPeriod:
        ifpp = multiplier * repaymentEvery / daysInYear                 (mc)
        f    = rate * ifpp * actualDays / calcDays                      (mc)
        f    = f.setScale(mc.getPrecision(), mc.getRoundingMode())      <- DECIMAL PLACES
  ProgressiveEMICalculator.java:1965-1978 rateFactorByRepaymentPartialPeriod:
        ifpp = repaymentEvery * cumulatedPeriodRatio                    (EXACT multiply)
        f    = rate * ifpp * actualDays / calcDays                      (mc), setScale(19, mode)
  RepaymentPeriod.java:216-217            rateFactorPlus1 = 1 + Σ interest-period rateFactors (EXACT add)
  ProgressiveEMICalculator.java:1816-1820 rateFactorPlus1N = Π (1+f_i)                        (mc)
  ProgressiveEMICalculator.java:1822-1828 fnResult: fold over periods.skip(1): fn = 1 + fn*(1+f_i) (mc)
  ProgressiveEMICalculator.java:1836-1839 EMI = rateFactorPlus1N * balance / fnResult          (mc)
  Money.java:40-52                        Money.of -> setScale(decimalPlaces, tenant rounding mode)
  InterestPeriod.java:145-157             calculatedDueInterest =
        outstandingBalance * rateFactorTillPeriodDueDate / lengthTillDue * length              (mc)
  RepaymentPeriod.java:251-257            Money.of(Σ interest periods, mc)
  RepaymentPeriod.java:272-285            dueInterest  = min(calculatedDueInterest, emi)
  RepaymentPeriod.java:345-349            duePrincipal = max(0, emi - dueInterest)
  ProgressiveEMICalculator.java:1160-1219 calculateLastUnpaidRepaymentPeriodEMI:
        diff = totalDisbursed + totalCapitalizedIncome + totalCreditedPrincipal
               + Σ dueInterest − Σ EMI                                  (:1195-1203)
        lastPeriod.emi = lastPeriod.emi + diff                          (:1205)   [SIGNED]
  ProgressiveEMICalculator.java:1258-1308 checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods
        + EmiAdjustment.shouldBeAdjusted():
        |emiDifference| * 100 > originalEmi.copy(floor(n/2))
        Money.copy(double) REPLACES the amount (Money.java:220-222), so the RHS is
        Money(floor(n/2)) = Money(6), NOT emi*6.  Checked below; it does not fire.

Scope of the model: single disbursement on the first period's fromDate, no
charges, no payments, no down payment, no capitalized income, no grace,
DECLINING_BALANCE, exactly one interest period per repayment period.  That is the
shape of B-03 / B-04 (`req/calc-B-0{3,4}-*.json`, `req/product-{3,4}-*.json`).

Money is exact `Decimal` in every step; **no floating-point value is ever
constructed** (CLAUDE.md non-negotiable).  Integer-minor-unit comparison is used
for every verdict; no tolerance anywhere.
"""
import datetime
import json
import os
import sys
from decimal import Decimal, localcontext, ROUND_HALF_UP, ROUND_HALF_EVEN

PREC = 19  # MoneyHelper.java:35 — compile-time constant; NOT tenant-configurable
MODES = {'HALF_UP': ROUND_HALF_UP, 'HALF_EVEN': ROUND_HALF_EVEN}

HERE = os.path.dirname(os.path.abspath(__file__))
PATHB = os.path.normpath(os.path.join(HERE, '..', '..', 'capture', 'pathb'))


def q(x, places, rounding):
    """BigDecimal.setScale(places, rounding)."""
    return x.quantize(Decimal(1).scaleb(-places), rounding=rounding)


def is_leap(y):
    return (y % 4 == 0 and y % 100 != 0) or y % 400 == 0


def year_length(y):
    return 366 if is_leap(y) else 365


def contains_feb29(rp_from, rp_due):
    """ProgressiveEMICalculator.java:1330-1340 — leap day in (rpFrom, rpDue]."""
    for year in range(rp_from.year, rp_due.year + 1):
        if is_leap(year):
            leap = datetime.date(year, 2, 29)
            if rp_from < leap <= rp_due:
                return True
    return False


def days_in_year(ip_from, rp_from, rp_due, strategy):
    """ProgressiveEMICalculator.java:1346-1353 with DaysInYearType.ACTUAL
    (DaysInYearType.java:81-86 -> referenceDate.lengthOfYear())."""
    n = year_length(ip_from.year)
    if n == 366 and strategy == 'FEB_29_PERIOD_ONLY':
        n = 366 if contains_feb29(rp_from, rp_due) else 365  # :1342-1344
    return Decimal(n)


def period_fractions(ip_from, ip_due, rnd):
    """ProgressiveEMICalculator.java:1550-1568, with
    isInterestRecognitionOnDisbursementDate == false (:1578-1584 -> Dec 31)."""
    cumulated = Decimal(0)
    actual_year = ip_from.year
    end_year = ip_due.year
    actual_date = ip_from
    while actual_year <= end_year:
        fraction_due = ip_due if actual_year == end_year else datetime.date(actual_year, 12, 31)
        n_days_year = Decimal(year_length(actual_year))
        days = Decimal((fraction_due - actual_date).days)
        cumulated = cumulated + (days / n_days_year)      # both ops under mc (:1563)
        actual_date = fraction_due
        actual_year += 1
    return cumulated


def rate_factor(rate, ip_from, ip_due, rp_from, rp_due, strategy, rnd):
    """calculateRateFactorPerPeriod (:1486-1540) for
    interestCalculationPeriodType = DAILY, daysInYearType = ACTUAL,
    daysInMonthType = ACTUAL.  Identical result to the interest variant
    (:1355-1417) when the interest period spans the whole repayment period."""
    years_diff = ip_due.year - ip_from.year
    partial = (years_diff > 0 and
               (strategy != 'FEB_29_PERIOD_ONLY' or contains_feb29(rp_from, rp_due)))   # :1505-1507
    if partial:
        frac = period_fractions(ip_from, ip_due, rnd)      # :1527-1528
        ifpp = Decimal(1) * frac                           # :1974 EXACT multiply
        f = rate * ifpp                                    # :1975-1977 (mc)
        f = f * Decimal(1)
        f = f / Decimal(1)
    else:
        diy = days_in_year(ip_from, rp_from, rp_due, strategy)
        actual_days = Decimal((ip_due - ip_from).days)
        ifpp = (actual_days * Decimal(1)) / diy            # :1953-1955 (mc)
        f = rate * ifpp                                    # :1956-1958 (mc)
        f = f * Decimal(1)
        f = f / Decimal(1)
    return q(f, PREC, rnd), partial                        # :1962 / :1978 setScale(19, mode)


def derive(principal, due_dates, first_from, annual_rate_pct, strategy,
           decimals=2, mode='HALF_EVEN'):
    rnd = MODES[mode]
    with localcontext() as ctx:
        ctx.prec = PREC
        ctx.rounding = rnd

        rate = Decimal(annual_rate_pct) / Decimal(100)     # :1318-1320
        n = len(due_dates)
        froms = [first_from] + due_dates[:-1]

        rfs, partials = [], []
        for i in range(n):
            f, partial = rate_factor(rate, froms[i], due_dates[i], froms[i], due_dates[i],
                                     strategy, rnd)
            rfs.append(f)
            partials.append(partial)

        rfp1 = [Decimal(1) + f for f in rfs]               # RepaymentPeriod.java:216-217 EXACT

        rate_factor_n = Decimal(1)
        for v in rfp1:
            rate_factor_n = rate_factor_n * v              # :1816-1820 (mc)

        fn = Decimal(1)
        for v in rfp1[1:]:
            fn = Decimal(1) + fn * v                       # :1822-1828 (mc)

        emi_raw = rate_factor_n * Decimal(principal) / fn  # :1836-1839 (mc)
        emi = q(emi_raw, decimals, rnd)                    # Money.java:52
        # installmentAmountInMultiplesOf is NULL on products 3 and 4 -> :1761-1766 is a no-op.

        bal = Decimal(principal)
        rows = []
        for i in range(n):
            length = Decimal((due_dates[i] - froms[i]).days)
            # InterestPeriod.java:145-157 — one interest period per repayment period, so
            # lengthTillPeriodDueDate == length.
            calc = bal * rfs[i]
            calc = calc / length
            calc = calc * length
            calc = q(calc, decimals, rnd)                  # RepaymentPeriod.java:251-257
            due_int = min(calc, emi)                       # RepaymentPeriod.java:280
            due_pri = max(Decimal(0), emi - due_int)        # RepaymentPeriod.java:348
            bal = bal - due_pri
            rows.append({'emi': emi, 'interest': due_int, 'principal': due_pri,
                         'balance': bal, 'days': length, 'partial': partials[i],
                         'rf': rfs[i]})

        # --- final installment absorbs the whole signed residual (:1195-1205)
        total_due_interest = sum((r['interest'] for r in rows), Decimal(0))
        total_emi = sum((r['emi'] for r in rows), Decimal(0))
        diff = Decimal(principal) + total_due_interest - total_emi           # :1202-1203
        last = rows[-1]
        last['emi'] = last['emi'] + diff                                     # :1205
        last['interest'] = min(
            q((rows[-2]['balance'] * rfs[-1] / rows[-1]['days']) * rows[-1]['days'], decimals, rnd),
            last['emi'])
        last['principal'] = max(Decimal(0), last['emi'] - last['interest'])
        last['balance'] = rows[-2]['balance'] - last['principal']

        # --- EmiAdjustment.shouldBeAdjusted (:1258-1308 + EmiAdjustment.java:31-37):
        #     |emiDifference| * 100 > Money(floor(n/2))   [Money.copy(double) REPLACES]
        emi_difference = last['emi'] - rows[-2]['emi']
        lower_half = Decimal(n // 2)
        adjust_fires = abs(emi_difference) * Decimal(100) > lower_half

        return {'rows': rows, 'emi': rows[0]['emi'], 'residual': diff,
                'emi_difference': emi_difference, 'adjust_fires': adjust_fires,
                'total_interest': sum((r['interest'] for r in rows), Decimal(0)),
                'total_repayment': sum((r['emi'] for r in rows), Decimal(0))}


def load(path):
    return json.loads(open(path, 'rb').read().decode(), parse_float=Decimal, parse_int=Decimal)


def compare(path, label, strategy, mode):
    j = load(path)
    obs = [p for p in j['periods'] if 'period' in p]
    dates = [datetime.date(*[int(x) for x in p['dueDate']]) for p in obs]
    first_from = datetime.date(*[int(x) for x in obs[0]['fromDate']])
    d = derive(Decimal('1200000'), dates, first_from, Decimal('21.6'), strategy, mode=mode)

    print('=' * 100)
    print('%s   daysInYearCustomStrategy=%s   MathContext(%d, %s)' % (label, strategy, PREC, mode))
    print('  in: DAILY (interestCalculationPeriodType=0), daysInYearType=ACTUAL(1), daysInMonthType=ACTUAL(1)')
    print('  %3s %6s %5s  %-13s %13s %13s   %13s %13s   %13s %13s'
          % ('per', 'days', 'part', 'rateFactor', 'derived P', 'observed P',
             'derived I', 'observed I', 'derived T', 'observed T'))
    ok = True
    for i, (r, o) in enumerate(zip(d['rows'], obs), 1):
        op, oi = Decimal(o['principalDue']), Decimal(o['interestDue'])
        ot = Decimal(o['totalDueForPeriod'])
        m = (r['principal'] == op and r['interest'] == oi and r['emi'] == ot)
        ok &= m
        print('  %3d %6s %5s  %-13s %13s %13s   %13s %13s   %13s %13s  %s'
              % (i, r['days'], 'YES' if r['partial'] else '-', str(r['rf'])[:13],
                 r['principal'], op, r['interest'], oi, r['emi'], ot,
                 'ok' if m else '**MISMATCH**'))
    ti, tr = Decimal(j['totalInterestCharged']), Decimal(j['totalRepaymentExpected'])
    m1 = d['total_interest'] == ti
    m2 = d['total_repayment'] == tr
    ok &= m1 and m2
    print('  totalInterest   derived=%s  observed=%s  %s' % (d['total_interest'], ti, 'ok' if m1 else '**MISMATCH**'))
    print('  totalRepayment  derived=%s  observed=%s  %s' % (d['total_repayment'], tr, 'ok' if m2 else '**MISMATCH**'))
    print('  final-installment signed residual (:1202-1205) = %s' % d['residual'])
    print('  EmiAdjustment.shouldBeAdjusted -> %s  (|%s| * 100 > %d ?)'
          % (d['adjust_fires'], d['emi_difference'], len(d['rows']) // 2))
    print('  RESULT: %s' % ('RE-DERIVED DIGIT-FOR-DIGIT' if ok else 'MISMATCH'))
    return ok


if __name__ == '__main__':
    # The four Path B captures on record were taken on the `default` tenant at
    # (19, HALF_EVEN) — T22 §7(b), from the server's own log line.  They were
    # re-observed byte-identical on a (19, HALF_UP) tenant (t22-audit/out-fresh-tenant/).
    # Both modes are therefore re-derived here.
    results = {}
    for mode in ('HALF_EVEN', 'HALF_UP'):
        results[('B-03', mode)] = compare(
            os.path.join(PATHB, 'out', 'B-03-diycs-fullleapyear-raw.json'),
            'B-03  FULL_LEAP_YEAR', 'FULL_LEAP_YEAR', mode)
        results[('B-04', mode)] = compare(
            os.path.join(PATHB, 'out', 'B-04-diycs-feb29only-raw.json'),
            'B-04  FEB_29_PERIOD_ONLY', 'FEB_29_PERIOD_ONLY', mode)
    print('=' * 100)
    for k in sorted(results):
        print('  %-6s %-10s : %s' % (k[0], k[1], 'CONSISTENT' if results[k] else 'INCONSISTENT'))
    allok = all(results.values())
    print('OVERALL: %s' % ('PASS — the committed B-03/B-04 observations are CONSISTENT with the '
                           'from-source re-derivation' if allok else 'FAIL'))
    sys.exit(0 if allok else 1)
