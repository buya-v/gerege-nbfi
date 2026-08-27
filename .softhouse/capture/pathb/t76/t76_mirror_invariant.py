#!/usr/bin/env python3
"""T76 — invariant I7: on an UNPAID schedule the mirror columns must equal the DUE columns.

WHY THIS EXISTS.  T22's ten invariants (t22-audit/t22_invariants.py) tie the DUE columns,
the running balance and the totals, and they are genuinely failable: a one-minor-unit change
to `principalDue` trips I1/I5/S2 and one to `totalDueForPeriod` trips I4/I5 (transcripts in
t76/out/mutation/).  But a one-minor-unit change to `totalOriginalDueForPeriod` trips NOTHING —
that column, and its `*Original*` / `*Outstanding*` siblings, is never read.  A Go port that
emitted a wrong ORIGINAL column would pass every existing property check.

WHAT IT ASSERTS, per repayment period, in EXACT INTEGER MINOR UNITS (no float anywhere;
JSON numbers are decoded with parse_float=Decimal and converted by exact scaling):

  I7a  principalOriginalDue == principalDue == principalOutstanding
  I7b  interestOriginalDue  == interestDue  == interestOutstanding
  I7c  feeChargesDue        == feeChargesOutstanding
  I7d  penaltyChargesDue    == penaltyChargesOutstanding
  I7e  totalOriginalDueForPeriod == totalDueForPeriod == totalOutstandingForPeriod
                                 == totalInstallmentAmountForPeriod
  I7f  every one of those literals is exactly representable in minor units

I7e's last equality holds ONLY because nothing in this capture set is paid and no charge is
attached; it is asserted, not assumed, and it is the column pair that carries
installmentAmountInMultiplesOf (B-02) — so a port that rounds the installment but forgets to
carry the rounded value into the ORIGINAL column is caught here and nowhere else.

Usage:  t76_mirror_invariant.py <capture.json>[::label] ...
Exit 0 iff every assertion holds on every file.
"""
import decimal
import json
import sys

D = decimal.Decimal
HUNDRED = D(100)


def minor(v, where, bad):
    """Exact minor units from a decimal wire literal. No float is ever constructed."""
    scaled = D(v) * HUNDRED
    if scaled != scaled.to_integral_value():
        bad.append('%s = %s is not representable in minor units' % (where, v))
        return None
    return int(scaled)


def check(path, label):
    with open(path, 'rb') as fh:
        doc = json.loads(fh.read().decode('utf-8'), parse_float=D, parse_int=D)
    bad = []
    periods = [p for p in doc['periods'] if p.get('period') is not None]
    for p in periods:
        n = int(p['period'])
        g = lambda k: minor(p[k], '%s period %d %s' % (label, n, k), bad) if k in p else None

        trip = [('principal', ['principalOriginalDue', 'principalDue', 'principalOutstanding']),
                ('interest', ['interestOriginalDue', 'interestDue', 'interestOutstanding']),
                ('fee', ['feeChargesDue', 'feeChargesOutstanding']),
                ('penalty', ['penaltyChargesDue', 'penaltyChargesOutstanding']),
                ('total', ['totalOriginalDueForPeriod', 'totalDueForPeriod',
                           'totalOutstandingForPeriod', 'totalInstallmentAmountForPeriod'])]
        for name, keys in trip:
            vals = [(k, g(k)) for k in keys if k in p]
            distinct = {v for _, v in vals if v is not None}
            if len(distinct) > 1:
                bad.append('%s period %d: %s columns disagree: %s'
                           % (label, n, name, ', '.join('%s=%d' % (k, v) for k, v in vals)))
    print('  %-52s periods=%d  %s' % (label, len(periods), 'PASS' if not bad else '**FAIL**'))
    for b in bad:
        print('      %s' % b)
    return not bad


ok = True
for arg in sys.argv[1:]:
    path, _, label = arg.partition('::')
    ok = check(path, label or path) and ok
print('I7 OVERALL: %s' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
