#!/usr/bin/env python3
"""
T44 audit - is the month-end special case DISTINGUISHABLE from its absence, once the
port's whole-months function is the obvious (naive) one rather than Java's packed rule?

R2 = periodRatio, packed whole-months  [ChronoUnit.MONTHS.between], month-end case PRESENT
     -> the pinned source: ProgressiveEMICalculator.java:1432-1433 + DateUtils.java:312
R4 = periodRatio, naive whole-months, month-end case ABSENT
     -> the double mis-port

Sweeps every (scheduleStartDate, period) pair a monthly progressive loan can produce over
a multi-year window and counts the periodRatio values on which R2 and R4 differ.
Pure integer / Decimal arithmetic; NO FLOAT.
"""
import sys
from decimal import Decimal, Context, ROUND_HALF_UP
from datetime import date, timedelta

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from t44_periodratio_independent import (calculate_period_ratio, calculate_seed_date,
                                         plus_months, months_between_packed,
                                         months_between_naive)

MC = Context(prec=19, rounding=ROUND_HALF_UP)

start_day = date(2023, 1, 1)
n_days = 365 * 3            # every schedule start date across 2023-2025
terms = (6, 12, 36)
repay_every = 1

pairs = 0
mb_differ = 0
ratio_differ = 0
special_fires = 0
examples = []

for off in range(n_days):
    start = start_day + timedelta(days=off)
    for n in terms:
        boundaries = [plus_months(start, k) for k in range(n + 1)]
        for k in range(n):
            f, d = boundaries[k], boundaries[k + 1]
            pairs += 1
            r2 = calculate_period_ratio(start, f, d, repay_every, MC, True, months_between_packed)
            r4 = calculate_period_ratio(start, f, d, repay_every, MC, False, months_between_naive)
            # does the special case fire on this period?
            seed = calculate_seed_date(start, f, d, repay_every)
            tld = (date(f.year + 1, 1, 1) if f.month == 12 else date(f.year, f.month + 1, 1))
            tld = (tld - timedelta(days=1)).day
            fires = (tld == f.day and seed.day > f.day)
            if fires:
                special_fires += 1
            if months_between_packed(seed, f) != months_between_naive(seed, f):
                mb_differ += 1
            if r2 != r4:
                ratio_differ += 1
                if len(examples) < 10:
                    examples.append((start, f, d, seed, str(r2), str(r4)))

print("T44 AUDIT - R2 vs R4 over the swept monthly-progressive date space")
print(f"  schedule start dates : {n_days} (2023-01-01 .. {start_day + timedelta(days=n_days-1)})")
print(f"  terms                : {terms}, RepaymentEvery=1, MONTHS")
print(f"  (start, period) pairs: {pairs}")
print()
print(f"  periods on which the MONTH-END SPECIAL CASE FIRES        : {special_fires}")
print(f"  periods where packed and naive whole-months DISAGREE     : {mb_differ}")
print(f"  periods where periodRatio(R2) != periodRatio(R4)         : {ratio_differ}")
print()
if ratio_differ == 0:
    print("  => R2 and R4 are the SAME FUNCTION on this entire domain.")
    print("     The month-end special case is exactly a compensation for the packed rule's")
    print("     month-end undercount, so a port that omits the special case AND computes")
    print("     whole-months the obvious way is INDISTINGUISHABLE from the oracle here.")
else:
    print("  => separating periods exist; first examples:")
    for e in examples:
        print("    ", e)
