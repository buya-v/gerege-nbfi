#!/usr/bin/env python3
"""T153 — re-derive T149-PATHB-TIE's WHOLE schedule from first principles.

An independent reviewer does not confirm a vector by re-reading it. This script
rebuilds every money cell of `T149-PATHB-TIE` in EXACT RATIONAL arithmetic
(`fractions.Fraction` — no float appears anywhere, including intermediates) from
nothing but the four declared inputs:

    principal   116_250_250 minor units (MNT 1,162,502.50)
    rate        27/125 per annum / 12   ==  0.018 per month, EXACT
    n           12 monthly repayments
    quantization  HALF_UP at 2 minor digits (the ratified tenant mode)

and compares the result against the promoted vector's `expect` block. It is a
re-derivation, not a transcription check: `verify-transcription.py` is the one
that checks the vector against the raw capture bytes.

    python3 rederive-schedule-exact.py
"""
from fractions import Fraction as F
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
VEC = os.path.join(REPO, '.softhouse', 'vectors', 'loanschedule',
                   'T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json')

PRINCIPAL_MINOR = 116250250          # MNT 1,162,502.50
ANNUAL_RATE = F(27, 125)             # 21.6 % p.a., exact
PERIODS = 12


def half_up(x):
    """Fraction -> int, HALF_UP. The ratified tenant rounding mode."""
    sign = -1 if x < 0 else 1
    x = abs(x)
    whole = x.numerator // x.denominator
    if x - whole >= F(1, 2):
        whole += 1
    return sign * whole


def main():
    p = F(PRINCIPAL_MINOR)
    r = ANNUAL_RATE / 12                     # exactly 9/500 = 0.018
    growth = (1 + r) ** PERIODS
    emi = half_up(p * r * growth / (growth - 1))

    rows, bal = [], p
    for k in range(1, PERIODS + 1):
        interest = half_up(bal * r)
        principal = emi - interest if k < PERIODS else int(bal)
        bal -= principal
        rows.append((k, interest, principal, int(bal), interest + principal))

    vec = json.load(open(VEC))
    expect = [e for e in vec['expect']['periods'] if e['kind'] == 'REPAYMENT']
    if len(expect) != len(rows):
        sys.exit('ROW COUNT DIFFERS: vector %d, re-derivation %d' % (len(expect), len(rows)))

    bad = 0
    print('EMI (HALF_UP of the exact rational annuity) = %d minor units' % emi)
    for (k, i, pr, b, tot), e in zip(rows, expect):
        cells = [('interest', i, e['interest_minor']),
                 ('principal', pr, e['principal_minor']),
                 ('outstanding', b, e['outstanding_principal_minor']),
                 ('total_due', tot, e['observed_total_due_minor'])]
        diffs = ['%s %d vs %s' % (n, mine, theirs) for n, mine, theirs in cells
                 if str(mine) != str(theirs)]
        bad += len(diffs)
        print('  period %-3d %s' % (k, 'ok' if not diffs else 'DIFFERS: ' + '; '.join(diffs)))

    total = sum(x[1] for x in rows)
    if str(total) != vec['expect']['observed_total_interest_minor']:
        print('  total interest DIFFERS: %d vs %s'
              % (total, vec['expect']['observed_total_interest_minor']))
        bad += 1
    else:
        print('  total interest  %d   ok' % total)

    tie = F(PRINCIPAL_MINOR * ANNUAL_RATE.numerator, 12 * ANNUAL_RATE.denominator)
    print()
    print('THE TIE, in exact integers: %d x 27/1500 = %s   -> HALF_UP %d, HALF_EVEN %d'
          % (PRINCIPAL_MINOR, tie, half_up(tie), tie.numerator // tie.denominator))

    if bad:
        sys.exit('RE-DERIVATION DISAGREES with the vector in %d cells.' % bad)
    print()
    print('RE-DERIVATION AGREES with the vector in every money cell, from the four')
    print('declared inputs alone, in exact rational arithmetic.')


if __name__ == '__main__':
    main()
