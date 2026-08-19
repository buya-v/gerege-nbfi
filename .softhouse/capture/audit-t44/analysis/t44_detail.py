#!/usr/bin/env python3
"""T44 audit - per-period detail for a named capture, all four readings."""
import json, sys
from decimal import Decimal, Context, ROUND_HALF_UP
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from t44_periodratio_independent import (D, days_between, rate_factor, money,
                                         calculate_period_ratio, calculate_seed_date,
                                         months_between_packed, months_between_naive)

doc = json.load(open(sys.argv[1]), parse_float=Decimal)
want = sys.argv[2:]
for c in doc['captures']:
    if want and c['id'] not in want:
        continue
    i, o = c['inputs'], c['observed']
    mc = Context(prec=i['mathContextPrecision'], rounding=ROUND_HALF_UP)
    start, disb = D(i['scheduleGenerationStartDate']), D(i['disbursementDate'])
    rate = Decimal(i['annualNominalInterestRate']) / Decimal(100)
    ev = i['repaymentEvery']
    print(f"\n=== {c['id']}  start={start} disb={disb} P={o['totalDisbursedAmount']} "
          f"rate={i['annualNominalInterestRate']} n={i['numberOfRepayments']} "
          f"mc=({mc.prec},{i['mathContextRoundingMode']}) ===")
    print(f"{'#':>3} {'from':11}{'due':11}{'seed':11}{'ratio(R2)':>22} {'obs int':>14}"
          f"{'R2':>14}{'R1':>14}{'R3':>14}{'R4':>14}")
    bal = Decimal(o['totalDisbursedAmount'])
    for k, p in enumerate([x for x in o['periods'] if x['type'] == 'REPAYMENT'], 1):
        f, d = D(p['fromDate']), D(p['dueDate'])
        cd, ad = days_between(f, d), days_between(max(f, disb), d)
        seed = calculate_seed_date(start, f, d, ev)
        rs = {
            'R2': calculate_period_ratio(start, f, d, ev, mc, True, months_between_packed),
            'R1': Decimal(ev),
            'R3': calculate_period_ratio(start, f, d, ev, mc, False, months_between_packed),
            'R4': calculate_period_ratio(start, f, d, ev, mc, False, months_between_naive),
        }
        pred = {t: money(bal * rate_factor(rate, m, 360, ad, cd, mc)) for t, m in rs.items()}
        obs = Decimal(p['interest'])
        mark = lambda t: ('=' if pred[t] == obs else '!')
        print(f"{k:>3} {f}  {d}  {seed}  {str(rs['R2']):>20} {obs:>14}"
              + "".join(f"{str(pred[t]):>13}{mark(t)}" for t in ('R2', 'R1', 'R3', 'R4')))
        bal = Decimal(p['balance'])
