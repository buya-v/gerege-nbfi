#!/usr/bin/env python3
"""T149 — close T76's `[UNVERIFIED]` on interestCalculationPeriodMethod.

DEC-1 pins six oracle inputs, one of them "interestCalculationPeriodMethod is left
unset, which the seam's assembler never populates". Path B CANNOT leave it unset: the
running server always persists a value, and every Path B request in this program carries
`interestCalculationPeriodType: 1` (SAME_AS_REPAYMENT_PERIOD). T76 therefore refused to
promote any Path B capture and recorded the residual question as UNVERIFIED:

    "Whether SARP is behaviourally identical to unset is [UNVERIFIED] -- I did not test
     it, and no capture in this set can."

T76 could not test it because its only Path B capture on this shape (B-01) ran an
ACTUAL/ACTUAL product, so a comparison against a 30/360 Path A vector confounded TWO
settings. Product 9 (`T22 probe p09-sarp-360-30`) is SARP + fixed 30/360, which controls
the day count and leaves the interest-calculation-period method as the ONLY difference
against the promoted Path A vector P-MNT-1M2.

This script compares, in exact integer minor units:

  Path B  T149-CTRL-P9-1M2  product 9, SARP + 30/360, MNT 1,200,000, 12 x 21.6%
  Path A  P-MNT-1M2         ICPM unset + 30/360,      MNT 1,200,000, 12 x 21.6%   (PROMOTED)

    python3 crosscheck-vs-patha.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
PATHB = os.path.join(HERE, 'out', 'gerege', 'T149-CTRL-P9-1M2-raw.json')
PATHA = os.path.join(REPO, '.softhouse', 'vectors', 'loanschedule',
                     'P-MNT-1M2-12x21pt6pct.json')


def minor(text, digits=2):
    t = str(text)
    neg = t.startswith('-')
    if neg:
        t = t[1:]
    whole, _, frac = t.partition('.')
    if len(frac) > digits:
        if frac[digits:].strip('0'):
            raise ValueError(text)
        frac = frac[:digits]
    frac = frac.ljust(digits, '0')
    v = ((whole or '0') + frac).lstrip('0') or '0'
    return -int(v) if neg else int(v)


def main():
    b = json.load(open(PATHB), parse_float=str)
    a = json.load(open(PATHA), parse_float=str)
    arows = [p for p in a['expect']['periods'] if p['kind'] == 'REPAYMENT']
    brows = [p for p in b['periods'] if 'period' in p]
    print('Path A vector : %s   (seam %s, day_count %s)'
          % (a['case_id'], a['oracle']['seam'], a['request']['day_count']))
    print('Path B capture: T149-CTRL-P9-1M2  (product 9, SARP + fixed 30/360)')
    print('rows: Path A %d   Path B %d' % (len(arows), len(brows)))
    if len(arows) != len(brows):
        sys.exit('ROW COUNT DIFFERS — not comparable')
    bad = 0
    for ar, br in zip(arows, brows):
        cells = [
            ('principal',   int(ar['principal_minor']),               minor(br['principalOriginalDue'])),
            ('interest',    int(ar['interest_minor']),                minor(br['interestOriginalDue'])),
            ('outstanding', int(ar['outstanding_principal_minor']),   minor(br['principalLoanBalanceOutstanding'])),
            ('total_due',   int(ar['observed_total_due_minor']),      minor(br['totalOriginalDueForPeriod'])),
        ]
        diffs = ['%s %d vs %d' % (n, x, y) for n, x, y in cells if x != y]
        bad += len(diffs)
        print('  period %-3d %s' % (ar['installment_number'],
                                    'ok' if not diffs else 'DIFFERS: ' + '; '.join(diffs)))
    ai = int(a['expect']['observed_total_interest_minor'])
    bi = minor(b['totalInterestCharged'])
    print('  total interest  Path A %d   Path B %d   %s' % (ai, bi, 'ok' if ai == bi else 'DIFFERS'))
    if ai != bi:
        bad += 1
    print()
    if bad == 0:
        print('RESULT: %d of %d rows and the total agree in EVERY compared minor unit.'
              % (len(arows), len(arows)))
        print('        With the day count controlled at fixed 30/360, the only remaining')
        print('        difference between the two observations is interestCalculationPeriodMethod')
        print('        (SAME_AS_REPAYMENT_PERIOD on Path B, unset on Path A). It moves NOTHING on')
        print('        this shape. T76\'s [UNVERIFIED] is closed BY MEASUREMENT, on this shape only.')
    else:
        print('RESULT: %d cells differ. SARP is NOT inert on this shape.' % bad)
        sys.exit(1)


if __name__ == '__main__':
    main()
