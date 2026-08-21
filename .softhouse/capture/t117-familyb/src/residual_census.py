#!/usr/bin/env python3
"""T117 — census of the UNAMORTIZED RESIDUAL, in integer minor units, over both passes.

WHY THIS EXISTS, and it is a correction of T117's own metric. `classify_t117.py` emits
`failing_principal_minor`, and on a non-clean cell it sets that to the cell's **disbursement**.
That was written when every family-B cell known to the program had a principal column summing to
exactly zero, so "the failing principal" and "the disbursement" were the same number. **Pass 2
refuted that**: at B = 11, n ∈ {108, 121, 150} the principal column sums to 5, 4 and 2 minor units
against an 11-minor-unit disbursement — a PARTIAL shortfall. On those cells
`failing_principal_minor` OVERSTATES the residual, and the committed
`out/t117-classified.json` / `out/t117p2-classified.json` carry that overstatement.

`classify_t117.py` is not edited (T114's standing ruling — it produced committed evidence). This
script re-derives both quantities separately from the raw captures:

    disbursed_minor          the DISBURSEMENT row's principal
    amortized_minor          sum of the REPAYMENT rows' principal
    unamortized_residual     disbursed_minor - amortized_minor      <- THE money number
    final_balance_minor      the last REPAYMENT row's balance

All in INTEGER MINOR UNITS. json.load uses parse_float=Decimal. No float on any decision path
(P-25). Every case is counted; nothing is skipped and there is no bare except (P-40).
"""
import collections
import gzip
import json
import sys
from decimal import Decimal

from classify_t117 import minor, classify


def load(path):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt') as fh:
        return json.load(fh, parse_float=Decimal)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: residual_census.py <capture.json[.gz]> [<capture> ...]")
    rows, errored = [], []
    for path in sys.argv[1:]:
        for cap in load(path)['captures']:
            if cap.get('observed') is None:
                errored.append({'source': path, 'id': cap['id']})
                continue
            inp = cap['inputs']
            dp = int(inp['currencyDecimalPlaces'])
            disb = None
            amort = 0
            final_bal = None
            for p in cap['observed']['periods']:
                if p['type'] == 'DISBURSEMENT':
                    disb = minor(p['principal'], dp)
                else:
                    amort += minor(p['principal'], dp)
                    final_bal = minor(p['balance'], dp)
            fam = classify(cap)['family']
            rows.append({
                'source': path.split('/')[-1], 'id': cap['id'],
                'rate': inp['annualNominalInterestRate'], 'n': int(inp['numberOfRepayments']),
                'family': fam,
                'disbursed_minor': disb,
                'amortized_minor': amort,
                'unamortized_residual_minor': disb - amort,
                'final_balance_minor': final_bal,
                'residual_equals_final_balance': (disb - amort) == final_bal,
                'partial': (fam == 'B' and 0 < amort < disb),
            })

    famB = [r for r in rows if r['family'] == 'B']
    partial = [r for r in famB if r['partial']]
    worst = max(rows, key=lambda r: r['unamortized_residual_minor']) if rows else None
    out = {
        'sources': sys.argv[1:],
        'casesRead': len(rows),
        'erroredCases': errored,
        'tally': dict(collections.Counter(r['family'] for r in rows)),
        'familyB': {
            'cells': len(famB),
            'principalColumnSumsToZero': sum(1 for r in famB if r['amortized_minor'] == 0),
            'PARTIAL_shortfall_cells': len(partial),
            'partialCells': partial,
        },
        'residualEqualsFinalBalanceOnEveryCase':
            all(r['residual_equals_final_balance'] for r in rows),
        'largestUnamortizedResidual_minor': (worst['unamortized_residual_minor'] if worst else None),
        'largestUnamortizedResidual_case': (worst if worst else None),
        'largestFailingDisbursement_minor': max((r['disbursed_minor'] for r in famB), default=None),
        'distinctFamilyBDisbursements_minor': sorted({r['disbursed_minor'] for r in famB}),
        'rows': rows,
    }
    json.dump(out, sys.stdout, indent=1, default=str)
    print()
    return 0 if not errored else 1


if __name__ == '__main__':
    sys.exit(main())
