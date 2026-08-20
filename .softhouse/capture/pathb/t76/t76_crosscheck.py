#!/usr/bin/env python3
"""T76 - independent cross-checks, in EXACT INTEGER MINOR UNITS, no float anywhere.

1. Does the Path B capture B-01 carry the same money, cell for cell, as the ALREADY
   PROMOTED Path A parity vector P-MNT-1M2?  If it does, B-01 grades nothing the store
   does not already grade, which is the load-bearing reason not to promote it.
2. How far apart are B-01 and B-02 (installmentAmountInMultiplesOf 100), and B-03 and
   B-04 (daysInYearCustomStrategy)?  Reported in minor units, not asserted from a report.

Every value is read as exact Decimal from the wire text and scaled by 100.  Nothing here
authors an expected value: both sides of every comparison are observed artefacts.

Run from .softhouse/capture/pathb/ (paths are resolved from this file's location).
"""
import decimal
import json
import os
import sys

D = decimal.Decimal
HERE = os.path.dirname(os.path.abspath(__file__))
PATHB = os.path.normpath(os.path.join(HERE, os.pardir))
SOFTHOUSE = os.path.normpath(os.path.join(PATHB, os.pardir, os.pardir))
REC = os.path.join(HERE, 'out', 'recapture-gerege')


def load(path):
    with open(path, 'rb') as fh:
        return json.loads(fh.read().decode('utf-8'), parse_float=D, parse_int=D)


def m(v):
    x = D(v) * 100
    assert x == x.to_integral_value(), 'not minor-unit representable: %s' % v
    return int(x)


def pathb_rows(doc):
    out = []
    for p in doc['periods']:
        if p.get('period') is None:
            continue
        out.append((int(p['period']), m(p['principalDue']), m(p['interestDue']),
                    m(p['totalDueForPeriod']), m(p['principalLoanBalanceOutstanding'])))
    return out


def totals(doc):
    return (m(doc['totalPrincipalDisbursed']), m(doc['totalInterestCharged']),
            m(doc['totalRepaymentExpected']))


B01 = load(os.path.join(REC, 'B-01-baseline-raw.json'))
B02 = load(os.path.join(REC, 'B-02-multiplesof100-raw.json'))
B03 = load(os.path.join(REC, 'B-03-diycs-fullleapyear-raw.json'))
B04 = load(os.path.join(REC, 'B-04-diycs-feb29only-raw.json'))

print('=== 1. B-01 (Path B, gerege 19/HALF_UP) vs PROMOTED vector P-MNT-1M2 (Path A) ===')
vec = load(os.path.join(SOFTHOUSE, 'vectors', 'loanschedule',
                        'P-MNT-1M2-12x21pt6pct.json'))
vrows = {int(p['installment_number']): p for p in vec['expect']['periods']
         if p['kind'] == 'REPAYMENT'}
bad = 0
for n, prin, intr, tot, bal in pathb_rows(B01):
    v = vrows[n]
    vp, vi = int(v['principal_minor']), int(v['interest_minor'])
    vt = int(v['observed_total_due_minor'])
    same = (vp, vi, vt) == (prin, intr, tot)
    bad += 0 if same else 1
    print('  per %2d  B-01 %9d/%8d/%9d   P-MNT-1M2 %9d/%8d/%9d  %s'
          % (n, prin, intr, tot, vp, vi, vt, 'ok' if same else '**DIFFERS**'))
d, i, r = totals(B01)
vi_tot = int(vec['expect']['observed_total_interest_minor'])
print('  totals  B-01 disbursed=%d interest=%d repayment=%d ; vector interest=%d  %s'
      % (d, i, r, vi_tot, 'ok' if i == vi_tot else '**DIFFERS**'))
bad += 0 if i == vi_tot else 1
print('  VERDICT: %s\n' % ('IDENTICAL money in every graded cell - B-01 adds no new grading power'
                           if bad == 0 else '%d cell(s) DIFFER' % bad))

for label, a, b, what in (('B-01 vs B-02', B01, B02, 'installmentAmountInMultiplesOf = 100'),
                          ('B-03 vs B-04', B03, B04, 'daysInYearCustomStrategy')):
    print('=== 2. %s  (%s) ===' % (label, what))
    ar, br = pathb_rows(a), pathb_rows(b)
    moved = 0
    for (n, p1, i1, t1, _), (_, p2, i2, t2, _) in zip(ar, br):
        if (p1, i1, t1) != (p2, i2, t2):
            moved += 1
        print('  per %2d  %9d/%8d/%9d -> %9d/%8d/%9d   dTotal=%+d'
              % (n, p1, i1, t1, p2, i2, t2, t2 - t1))
    ta, tb = totals(a), totals(b)
    print('  periods differing: %d of %d ; total interest %d -> %d (%+d minor units);'
          ' total repayment %d -> %d (%+d)'
          % (moved, len(ar), ta[1], tb[1], tb[1] - ta[1], ta[2], tb[2], tb[2] - ta[2]))
    print()
sys.exit(1 if bad else 0)
