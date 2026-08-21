#!/usr/bin/env python3
"""T117 — check registered prediction P4, the EXACT ROW SHAPE of a family-B cell, cell by cell.

P4 (registered in ../PREDICTION.md before the run): for every B = 1, n >= 300 cell —
  totalPrincipalAmount "0.00", totalInterestAmount "0.01", totalRepaymentAmount "0.01",
  totalOutstandingAmount "0" (scale 0);
  REPAYMENT rows 1..n-1: principal "0.00", interest "0.00", total "0.00", balance "0.01",
                         totalOutstandingBalance "0.01";
  row n:                 interest "0.01", total "0.01", balance "0.01",
                         totalOutstandingBalance "0.00".

Money is INTEGER MINOR UNITS throughout (P-25); `totalOutstandingAmount`'s SCALE is checked on the
raw string because scale is the finding there, not value. json.load uses parse_float=Decimal.

Every deviation is COUNTED AND NAMED (P-40). Nothing is skipped; there is no bare except.
"""
import gzip
import json
import sys
from decimal import Decimal

from classify_t117 import minor, classify  # one definition of each, shared with the classifier


def load(path):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt') as fh:
        return json.load(fh, parse_float=Decimal)


def check(cap):
    """Return (matches_P4: bool, deviations: list[str]) for one capture."""
    inp, obs = cap['inputs'], cap['observed']
    dp = int(inp['currencyDecimalPlaces'])
    n = int(inp['numberOfRepayments'])
    dev = []
    if obs.get('totalPrincipalAmount') != '0.00':
        dev.append('totalPrincipalAmount=%r' % obs.get('totalPrincipalAmount'))
    if obs.get('totalInterestAmount') != '0.01':
        dev.append('totalInterestAmount=%r' % obs.get('totalInterestAmount'))
    if obs.get('totalRepaymentAmount') != '0.01':
        dev.append('totalRepaymentAmount=%r' % obs.get('totalRepaymentAmount'))
    if obs.get('totalOutstandingAmount') != '0':
        dev.append('totalOutstandingAmount=%r (scale-0 "0" expected)' % obs.get('totalOutstandingAmount'))
    reps = [p for p in obs['periods'] if p['type'] == 'REPAYMENT']
    if len(reps) != n:
        dev.append('%d REPAYMENT rows, expected %d' % (len(reps), n))
    for idx, p in enumerate(reps, start=1):
        last = (idx == len(reps))
        want = {'principal': 0, 'interest': (1 if last else 0), 'total': (1 if last else 0),
                'balance': 1, 'totalOutstandingBalance': (0 if last else 1)}
        for k, w in want.items():
            got = minor(p[k], dp)
            if got != w:
                dev.append('row %d %s = %d minor, expected %d' % (idx, k, got, w))
                if len(dev) > 40:
                    dev.append('... deviation list truncated at 40 for this case')
                    return False, dev
    return (not dev), dev


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: shape_check.py <capture.json[.gz]>")
    doc = load(sys.argv[1])
    scoped, matched, deviating, skipped_out_of_scope, errored = 0, 0, [], 0, []
    byfam = {'B': {'in': 0, 'matched': 0}, 'A': {'in': 0, 'matched': 0}, 'clean': {'in': 0, 'matched': 0}}
    for cap in doc['captures']:
        inp = cap.get('inputs', {})
        if cap.get('observed') is None:
            errored.append(cap['id'])
            continue
        b_minor = minor(inp['disbursementAmount'], int(inp['currencyDecimalPlaces']))
        n = int(inp['numberOfRepayments'])
        in_scope = (inp['annualNominalInterestRate'] == '600.0' and b_minor == 1 and n >= 300)
        if not in_scope:
            skipped_out_of_scope += 1
            continue
        scoped += 1
        fam = classify(cap)['family']
        byfam[fam]['in'] += 1
        ok, dev = check(cap)
        if ok:
            matched += 1
            byfam[fam]['matched'] += 1
        else:
            deviating.append({'id': cap['id'], 'n': n, 'observedFamily': fam,
                              'deviations': dev[:6],
                              'deviationCountTruncatedTo6': len(dev)})
    out = {
        'predictionUnderTest': 'P4 — exact row shape of a family-B cell at 600.0 % / B = 1 minor / n >= 300',
        'capturesInFile': len(doc['captures']),
        'inScope': scoped,
        'outOfScopeCountedNotDropped': skipped_out_of_scope,
        'erroredCases': errored,
        'matchedP4': matched,
        'deviatingCount': len(deviating),
        'byObservedFamily': byfam,
        'deviations': deviating,
    }
    json.dump(out, sys.stdout, indent=1, default=str)
    print()
    return 0 if (not deviating and not errored) else 1


if __name__ == '__main__':
    sys.exit(main())
