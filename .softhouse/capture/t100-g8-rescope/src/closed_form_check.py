#!/usr/bin/env python3
"""T100 — independent test of T83's closed form against the committed captures.

The closed form, as recorded in .softhouse/gates.md by T83:
    a cell FAILS to amortize iff  B_minor * a(r, n) < 1/2,
    where a(r, n) = r / (1 - (1 + r)^-n)  and  r = annual / 100 / 12.

This script evaluates it in EXACT RATIONAL arithmetic (fractions.Fraction — no float, no
Decimal rounding) over every non-calibration case in whichever raw captures are passed, and
compares the prediction against the measured last-row balance. It is written for T100 and
shares no code with T83's check-prediction.py or T84's eval-probe*.py.

NOTE ON `float`: every DECISION here is made in exact rational arithmetic (`gap < 0`). The single
`float(gap)` below is a DISPLAY conversion of a dimensionless residual `B*a - 1/2`, used only to
print an order of magnitude; no money value is ever converted to float, and no comparison reads the
float. Money itself is parsed as integer minor units by `minor()`.
"""
import json, gzip, sys, collections
from fractions import Fraction


def minor(s, dp):
    s = str(s).strip()
    neg = s.startswith('-')
    if neg:
        s = s[1:]
    whole, _, frac = s.partition('.')
    if len(frac) > dp:
        assert not frac[dp:].strip('0'), s
        frac = frac[:dp]
    frac = (frac + '0' * dp)[:dp]
    v = int(whole or '0') * 10 ** dp + int(frac or '0')
    return -v if neg else v


def annuity(rate_str, n):
    r = Fraction(rate_str) / 100 / 12
    if r == 0:
        return Fraction(1, n)
    return r / (1 - (1 + r) ** -n)


def load(p):
    return json.load(gzip.open(p)) if p.endswith('.gz') else json.load(open(p))


rows = []
for path in sys.argv[1:]:
    for c in load(path)['captures']:
        if c['id'].startswith('P-CAL'):
            continue           # rig calibrations, not sweep cells
        i, o = c['inputs'], c['observed']
        dp = int(i['currencyDecimalPlaces'])
        B = minor(i['disbursementAmount'], dp)
        n = int(i['numberOfRepayments'])
        rate = str(i['annualNominalInterestRate'])
        reps = [p for p in o['periods'] if p['type'] == 'REPAYMENT']
        fails = minor(reps[-1]['balance'], dp) != 0
        psum = sum(minor(p['principal'], dp) for p in reps)
        a = annuity(rate, n)
        gap = B * a - Fraction(1, 2)        # exact rational
        pred_fail = gap < 0
        rows.append(dict(id=c['id'], src=path.split('/')[-1], rate=rate, n=n, B=B,
                         measured_fail=fails, predicted_fail=pred_fail,
                         tie=(gap == 0), gap_float=float(gap),
                         principal_sums=(psum == B),
                         agree=(fails == pred_fail)))

refuted = [r for r in rows if not r['agree']]
ties = [r for r in rows if r['tie']]
print('cells evaluated (calibrations excluded): %d' % len(rows))
print('closed form HELD : %d' % sum(1 for r in rows if r['agree']))
print('closed form REFUTED: %d' % len(refuted))
print('exact ties (gap == 0): %d' % len(ties))
by = collections.Counter((r['rate'], r['B'], r['measured_fail'], r['predicted_fail']) for r in refuted)
for k, v in sorted(by.items()):
    print('  refuted group rate=%s B=%d measured_fail=%s predicted_fail=%s : %d cells'
          % (k[0], k[1], k[2], k[3], v))
print('refuted n values: %s' % sorted(r['n'] for r in refuted))
print('refuted, principal column sums to disbursed: %s'
      % collections.Counter(r['principal_sums'] for r in refuted))
print('smallest |gap| among refuted: %.3e   largest: %.3e'
      % (min(abs(r['gap_float']) for r in refuted), max(abs(r['gap_float']) for r in refuted)))
print('tie cells: %s' % [(r['id'], r['measured_fail']) for r in ties])
json.dump(rows, open(sys.argv[0].replace('/src/', '/out/').replace('closed_form_check.py',
          'closed-form-check.json'), 'w'), indent=1)
