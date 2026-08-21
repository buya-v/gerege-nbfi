#!/usr/bin/env python3
"""T117 — profile the emitted INTERMEDIATE-ROW INSTALLMENT against the exact limit B*r.

This is a DESCRIPTION of what the oracle emitted, not a claim about which internal quantity
rounded where. Family B's cause remains [UNVERIFIED] and this script does not look for it.

For each capture it reports, in INTEGER MINOR UNITS (P-25 — nothing here is a float):

  intermediate_totals   the distinct `total` values on REPAYMENT rows 1..n-1
  last_total            the `total` on row n
  intermediate_interest the distinct `interest` values on rows 1..n-1
  B_times_r_2x          2 * B * r as an INTEGER, where r = annual/100/12 as a Fraction, so that
                        "B*r is a half-integer" is the exact integer test `B_times_r_2x` is odd
  floor_B_times_r       floor(B*r) as an integer (exact, via Fraction floor division)

`B*r` is the n -> infinity limit of the annuity payment B*a(r,n) in minor units; at 600.0 %
p.a. r = 1/2 exactly, so B*r is a half-integer exactly when B is odd.
"""
import gzip
import json
import math
import sys
from decimal import Decimal
from fractions import Fraction

from classify_t117 import minor, classify


def load(path):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt') as fh:
        return json.load(fh, parse_float=Decimal)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: tie_profile.py <capture.json[.gz]>")
    doc = load(sys.argv[1])
    rows = []
    errored = []
    for cap in doc['captures']:
        if cap.get('observed') is None:
            errored.append(cap['id'])
            continue
        inp = cap['inputs']
        dp = int(inp['currencyDecimalPlaces'])
        b = minor(inp['disbursementAmount'], dp)
        r = Fraction(inp['annualNominalInterestRate']) / 100 / 12
        br = b * r
        reps = [p for p in cap['observed']['periods'] if p['type'] == 'REPAYMENT']
        inter = reps[:-1]
        rows.append({
            'id': cap['id'],
            'rate': inp['annualNominalInterestRate'],
            'n': int(inp['numberOfRepayments']),
            'B_minor': b,
            'family': classify(cap)['family'],
            'B_times_r_2x': int(2 * br) if (2 * br).denominator == 1 else None,
            'B_times_r_is_half_integer': ((2 * br).denominator == 1 and int(2 * br) % 2 == 1),
            'floor_B_times_r': math.floor(br),
            'intermediate_total_minor_distinct': sorted({minor(p['total'], dp) for p in inter}),
            'intermediate_interest_minor_distinct': sorted({minor(p['interest'], dp) for p in inter}),
            'last_total_minor': minor(reps[-1]['total'], dp),
            'last_interest_minor': minor(reps[-1]['interest'], dp),
        })

    famB = [r for r in rows if r['family'] == 'B']
    # observed correlation, stated as a count and never as a mechanism
    corr = {
        'familyB_cells': len(famB),
        'familyB_with_B_times_r_half_integer': sum(1 for r in famB if r['B_times_r_is_half_integer']),
        'familyB_whose_intermediate_total_equals_floor_B_times_r':
            sum(1 for r in famB
                if r['intermediate_total_minor_distinct'] == [r['floor_B_times_r']]),
        'nonFamilyB_cells': len(rows) - len(famB),
        'nonFamilyB_with_B_times_r_half_integer':
            sum(1 for r in rows if r['family'] != 'B' and r['B_times_r_is_half_integer']),
    }
    json.dump({'erroredCases': errored, 'observedCorrelation': corr, 'rows': rows},
              sys.stdout, indent=1, default=str)
    print()
    return 0 if not errored else 1


if __name__ == '__main__':
    sys.exit(main())
