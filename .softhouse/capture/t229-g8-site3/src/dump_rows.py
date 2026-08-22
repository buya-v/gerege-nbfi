#!/usr/bin/env python3
"""T229 — dump the observed rows of one cell, compressed by run-length. Integer minor units only."""
import gzip, json, sys
from decimal import Decimal

def minor(s):
    d = Decimal(str(s)) * 100
    assert d == d.to_integral_value(), s
    return int(d)

op = gzip.open if sys.argv[1].endswith('.gz') else open
raw = json.load(op(sys.argv[1]))
c = [c for c in raw['captures'] if c['id'] == sys.argv[2]][0]
o = c['observed']
print('totals: disb', minor(o['totalDisbursedAmount']), 'prin', minor(o['totalPrincipalAmount']),
      'int', minor(o['totalInterestAmount']), 'repay', minor(o['totalRepaymentAmount']))
reps = [r for r in o['periods'] if r['type'] == 'REPAYMENT']
prev = None
start = None
for i, r in enumerate(reps):
    k = (minor(r['principal']), minor(r['interest']), minor(r['total']), minor(r['balance']))
    if k != prev:
        if prev is not None:
            print('rows %d-%d  prin=%d int=%d total=%d bal=%d' % (start + 1, i, *prev))
        prev, start = k, i
print('rows %d-%d  prin=%d int=%d total=%d bal=%d' % (start + 1, len(reps), *prev))
