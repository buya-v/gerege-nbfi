#!/usr/bin/env python3
"""T22 INDEPENDENT AUDIT — check PATHB-REPORT.md's quantitative claims, and
inventory the fields the endpoint actually emits (T18 P0-3 checklist)."""
import json
from decimal import Decimal

W = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb'
F = {'B-01': '/out/B-01-baseline-raw.json', 'B-02': '/out/B-02-multiplesof100-raw.json',
     'B-03': '/out/B-03-diycs-fullleapyear-raw.json', 'B-04': '/out/B-04-diycs-feb29only-raw.json'}


def load(k):
    return json.loads(open(W + F[k], 'rb').read().decode(), parse_float=Decimal,
                      parse_int=Decimal)


d = {k: load(k) for k in F}

print('--- emitted fields (T18 P0-3: fromDate / fee / penalty must be present)')
rows = [p for p in d['B-01']['periods'] if 'period' in p]
disb = [p for p in d['B-01']['periods'] if 'period' not in p]
print(' repayment period keys :', sorted(rows[0].keys()))
print(' disbursement row keys :', sorted(disb[0].keys()))
print(' top-level keys        :', sorted(d['B-01'].keys()))

for a, b, label in (('B-01', 'B-02', 'installmentAmountInMultiplesOf null vs 100'),
                    ('B-03', 'B-04', 'daysInYearCustomStrategy FULL vs FEB29')):
    ra = [p for p in d[a]['periods'] if 'period' in p]
    rb = [p for p in d[b]['periods'] if 'period' in p]
    n = sum(1 for x, y in zip(ra, rb)
            if (Decimal(x['principalDue']) != Decimal(y['principalDue'])
                or Decimal(x['interestDue']) != Decimal(y['interestDue'])
                or Decimal(x['totalDueForPeriod']) != Decimal(y['totalDueForPeriod'])))
    print('--- %s: %s  -> %d of %d periods differ' % (a + ' vs ' + b, label, n, len(ra)))
    print('    totalInterest  %s -> %s   delta %s'
          % (d[a]['totalInterestCharged'], d[b]['totalInterestCharged'],
             Decimal(d[b]['totalInterestCharged']) - Decimal(d[a]['totalInterestCharged'])))
    print('    EMI (period 1) %s -> %s'
          % (ra[0]['totalDueForPeriod'], rb[0]['totalDueForPeriod']))
    print('    final period   %s -> %s'
          % (ra[-1]['totalDueForPeriod'], rb[-1]['totalDueForPeriod']))

print('--- B-02: is the EMI held constant for periods 1-11 and residual absorbed in 12?')
r = [p for p in d['B-02']['periods'] if 'period' in p]
const = {str(x['totalDueForPeriod']) for x in r[:11]}
print('    periods 1-11 totalDue set:', const, ' period 12:', r[-1]['totalDueForPeriod'])

print('--- currency block per capture')
for k in F:
    print('   ', k, dict(d[k]['currency']))
