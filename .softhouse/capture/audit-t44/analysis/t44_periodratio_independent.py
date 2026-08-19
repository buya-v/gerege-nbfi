#!/usr/bin/env python3
"""
T44 AUDIT - INDEPENDENT re-derivation of the periodRatio reading.

This file was written from the PINNED FINERACT SOURCE ONLY, read at:
  ProgressiveEMICalculator.java:1404-1413  (the graded call site: multiplier = periodRatio, daysInMonth = 30)
  ProgressiveEMICalculator.java:1419-1458  (calculatePeriodRatio)
  ProgressiveEMICalculator.java:1461-1479  (calculateSeedDate)
  ProgressiveEMICalculator.java:1598-1611  (calculateRateFactorPerPeriodBasedOnRepaymentFrequency)
  ProgressiveEMICalculator.java:1922-1927  (rateFactorByRepaymentEveryMonth - the argument swap)
  ProgressiveEMICalculator.java:1950-1963  (rateFactorByRepaymentPeriod; :1962 setScale(precision-as-SCALE))
  ProgressiveEMICalculator.java:1536-1537  (the OTHER call site: multiplier = repaymentEvery)

It DOES NOT import, copy or read T39's analysis/ (readings.py, t34_model.py, t34_periodratio.py).
NO FLOAT anywhere: Decimal only, exact strings, money compared as exact 2-dp Decimal text.
"""
import json, sys
from decimal import Decimal, Context, ROUND_HALF_UP, localcontext
from datetime import date


# ---- java.time-equivalent date helpers -------------------------------------
def month_len(y, m):
    nxt = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    return nxt.toordinal() - date(y, m, 1).toordinal()


def last_day_of_month(d):
    """TemporalAdjusters.lastDayOfMonth()"""
    return date(d.year, d.month, month_len(d.year, d.month))


def plus_months(d, n):
    """java.time.LocalDate.plusMonths - clamps the day to the target month's length."""
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, month_len(y, m)))


def months_between_packed(a, b):
    """ChronoUnit.MONTHS.between(a, b) == LocalDate.monthsUntil(b), the PACKED rule:
         packed = prolepticMonth * 32 + dayOfMonth;  return (packed_b - packed_a) / 32
       [java.time.LocalDate.monthsUntil]. This is what DateUtils.getExactDifference
       resolves to [DateUtils.java:312, :315-317]. Integer division truncates toward zero."""
    pa = (a.year * 12 + a.month - 1) * 32 + a.day
    pb = (b.year * 12 + b.month - 1) * 32 + b.day
    d = pb - pa
    return -((-d) // 32) if d < 0 else d // 32


def months_between_naive(a, b):
    """The OBVIOUS mis-port: count calendar months, then step back if plusMonths overshoots.
       Differs from the packed rule exactly at month-end clamping - e.g.
       (2024-01-31 -> 2024-02-29) is 0 packed but 1 naive."""
    total = (b.year - a.year) * 12 + (b.month - a.month)
    if total > 0 and plus_months(a, total) > b:
        total -= 1
    elif total < 0 and plus_months(a, total) < b:
        total += 1
    return total


months_between = months_between_packed


def days_between(a, b):
    return b.toordinal() - a.toordinal()


def D(s):
    return date(*(int(x) for x in s.split('-')))


# ---- calculateSeedDate  [ProgressiveEMICalculator.java:1461-1479] ----------
def calculate_seed_date(start_date, from_date, due_date, repay_every):
    seed = start_date
    multiplicator = 1
    while True:
        calculated = plus_months(seed, multiplicator)
        multiplicator += 1
        if not (calculated < due_date):
            break
    if calculated == due_date and plus_months(calculated, -repay_every) == from_date:
        return seed
    return from_date


# ---- calculatePeriodRatio  [ProgressiveEMICalculator.java:1419-1458] -------
def calculate_period_ratio(start_date, from_date, due_date, repay_every, mc,
                           month_end_case=True, mb=months_between_packed):
    seed = calculate_seed_date(start_date, from_date, due_date, repay_every)
    seed_day = seed.day
    target_day = from_date.day
    target_last_day = last_day_of_month(from_date).day
    # the month-end special case: ProgressiveEMICalculator.java:1432-1433
    if month_end_case and target_last_day == target_day and seed_day > target_day:
        n = mb(seed, date.fromordinal(from_date.toordinal() + 1))
    else:
        n = mb(seed, from_date)
    multiplicator = n + 1
    cur = from_date
    while cur < due_date:
        cur = plus_months(seed, multiplicator)
        if not (cur > due_date):
            multiplicator += 1
        else:
            full_period_date = cur
            multiplicator = multiplicator - n - 1
            cur = plus_months(seed, multiplicator)
            diff = days_between(cur, due_date)
            full_diff = days_between(cur, full_period_date)
            with localcontext(mc):
                return Decimal(diff) / Decimal(full_diff) + Decimal(multiplicator)
    multiplicator = multiplicator - n - 1
    return Decimal(multiplicator)


# ---- rate factor [:1950-1963], reached via [:1922-1927] and [:1598-1611] ---
def rate_factor(interest_rate, multiplier, days_in_year, actual_days, calculated_days, mc):
    """`multiplier` occupies the repaymentEvery slot; daysInMonth (=30) lands in
    repaymentPeriodMultiplierInDays because of the argument swap at :1925-1926."""
    if calculated_days == 0:
        return Decimal(0)
    with localcontext(mc):
        frac = Decimal(30) * multiplier
        frac = frac / Decimal(days_in_year)
        r = interest_rate * frac
        r = r * Decimal(actual_days)
        r = r / Decimal(calculated_days)
    # .setScale(mc.getPrecision(), mc.getRoundingMode())  -- PRECISION USED AS A SCALE [:1962]
    return r.quantize(Decimal(1).scaleb(-mc.prec), rounding=mc.rounding)


def money(x):
    return x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


# ---- the audit ------------------------------------------------------------
def audit(path):
    doc = json.load(open(path), parse_float=Decimal)
    rows = []
    for c in doc['captures']:
        i, o = c['inputs'], c['observed']
        mc = Context(prec=i['mathContextPrecision'],
                     rounding={'HALF_UP': ROUND_HALF_UP}[i['mathContextRoundingMode']])
        start, disb = D(i['scheduleGenerationStartDate']), D(i['disbursementDate'])
        rate = Decimal(i['annualNominalInterestRate']) / Decimal(100)
        assert i['daysInYear'] == 'DAYS_360' and i['daysInMonth'] == 'DAYS_30', c['id']
        diy = 360
        reps = [p for p in o['periods'] if p['type'] == 'REPAYMENT']
        bal = Decimal(o['totalDisbursedAmount'])
        ok = {'r1': 0, 'r2': 0, 'r3': 0, 'r4': 0}
        ratios = []
        for p in reps:
            f, d = D(p['fromDate']), D(p['dueDate'])
            calc_days = days_between(f, d)
            act_days = days_between(max(f, disb), d)   # pre-disbursement sub-period carries a 0 balance
            ev = i['repaymentEvery']
            pr2 = calculate_period_ratio(start, f, d, ev, mc, True, months_between_packed)
            pr3 = calculate_period_ratio(start, f, d, ev, mc, False, months_between_packed)
            # R4: the DOUBLE mis-port - special case omitted AND whole-months done the naive way
            pr4 = calculate_period_ratio(start, f, d, ev, mc, False, months_between_naive)
            ratios.append(str(pr2))
            for tag, mult in (('r2', pr2), ('r1', Decimal(ev)), ('r3', pr3), ('r4', pr4)):
                rf = rate_factor(rate, mult, diy, act_days, calc_days, mc)
                if money(bal * rf) == Decimal(p['interest']):
                    ok[tag] += 1
            bal = Decimal(p['balance'])
        rows.append((c['id'], len(reps), ok['r2'], ok['r1'], ok['r3'], ok['r4'], ratios))
    return rows


if __name__ == '__main__':
    rows = audit(sys.argv[1])
    print("INDEPENDENT RE-DERIVATION OF THE INTEREST COLUMN - T44 audit of T39")
    print("Model built from the pinned source only; T39's analysis/ was never read.")
    print()
    print("R1 = multiplier is RepaymentEvery (what DEC-1 rev6 said)")
    print("R2 = periodRatio, packed whole-months, month-end case PRESENT (the pinned source)")
    print("R3 = periodRatio, packed whole-months, month-end case OMITTED")
    print("R4 = periodRatio, month-end case OMITTED *and* naive whole-months (the double mis-port)")
    print()
    print(f"{'capture':16}{'cells':>6}{'R2':>5}{'R1':>5}{'R3':>5}{'R4':>5}   verdict")
    tot = [0, 0, 0, 0, 0]
    for cid, n, r2, r1, r3, r4, ratios in rows:
        v = ["R2 reproduces ALL"] if r2 == n else [f"R2 MISSES {n - r2}"]
        for tag, val in (('R1', r1), ('R3', r3), ('R4', r4)):
            v.append(f"{tag} separates on {n - val}" if val < n else f"{tag} INDISTINGUISHABLE")
        print(f"{cid:16}{n:>6}{r2:>5}{r1:>5}{r3:>5}{r4:>5}   {'; '.join(v)}")
        tot[0] += n; tot[1] += r2; tot[2] += r1; tot[3] += r3; tot[4] += r4
    print()
    print(f"TOTAL interest cells {tot[0]}: R2 reproduces {tot[1]}, R1 {tot[2]}, "
          f"R3 {tot[3]}, R4 {tot[4]}")
    print()
    print("Per-capture periodRatio arrays (R2), re-derived independently:")
    for cid, n, r2, r1, r3, r4, ratios in rows:
        print(f"  {cid:16}{ratios}")
