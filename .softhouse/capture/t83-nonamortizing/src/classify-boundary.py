#!/usr/bin/env python3
"""T83 — classify the committed sweep and emit the measured boundary. Gate G-8.

READS ONLY the emitted capture JSON. It computes no schedule, calls no oracle and
knows nothing about the prediction: the prediction is compared against this
output afterwards, by check-prediction.py, so that the classification cannot be
shaped by what was expected.

DEFINITIONS, stated so a reviewer can attack them:

  FAILS TO AMORTIZE   the LAST period row of the emitted schedule carries a
                      non-zero `balance` (outstanding principal). That is exactly
                      the cell the `principal_amortizes_to_zero` invariant reads
                      (invariants.go invPrincipalAmortizes: "the last row's
                      outstanding principal is exactly zero").
  CLEAN               the last row's `balance` is exactly 0.

Money is read as INTEGER MINOR UNITS throughout: every amount in the capture is a
plain decimal string at scale 2, parsed by removing the decimal point, never by
float. Nothing here constructs a float.

It also answers, per case, the four questions the driver asked in the mid-flight
note (each computed from the emitted rows only):

  principalColumnSumMinor        sum of `principal` over DOWN_PAYMENT+REPAYMENT rows
  disbursedMinor                 sum of `principal` over DISBURSEMENT rows
  principalColumnAmortizes       the two are equal
  totalOutstandingAmount         the oracle's OWN total, as emitted
  balanceColumnContradictsTotals the last row's balance is non-zero while the
                                 oracle's own totalOutstandingAmount reads zero
"""
import json
import sys
from collections import defaultdict


def minor(s):
    """'0.01' -> 1. Integer minor units. No float anywhere on this path."""
    if s is None:
        return None
    s = s.strip()
    neg = s.startswith('-')
    if neg:
        s = s[1:]
    if '.' in s:
        whole, frac = s.split('.', 1)
    else:
        whole, frac = s, ''
    frac = (frac + '00')[:2]
    v = int(whole or '0') * 100 + int(frac or '0')
    return -v if neg else v


def classify(cap):
    obs = cap['observed']
    periods = obs['periods']
    last = periods[-1]
    last_balance = minor(last.get('balance'))
    disbursed = sum(minor(p['principal']) for p in periods if p['type'] == 'DISBURSEMENT')
    repaid = sum(minor(p['principal']) for p in periods
                 if p['type'] in ('REPAYMENT', 'DOWN_PAYMENT'))
    total_out = minor(obs.get('totalOutstandingAmount'))
    interest_rows = [minor(p['interest']) for p in periods if p['type'] == 'REPAYMENT']
    emi_rows = [minor(p['total']) for p in periods if p['type'] == 'REPAYMENT']
    balances = [minor(p['balance']) for p in periods]
    i = cap['inputs']
    return {
        'id': cap['id'],
        'ratePct': i['annualNominalInterestRate'],
        'n': i['numberOfRepayments'],
        'principalMinor': minor(i['disbursementAmount']),
        'lastRowBalanceMinor': last_balance,
        'amortizes': last_balance == 0,
        'disbursedMinor': disbursed,
        'principalColumnSumMinor': repaid,
        'principalColumnAmortizes': disbursed == repaid,
        'totalOutstandingAmountMinor': total_out,
        'totalOutstandingAmountRaw': obs.get('totalOutstandingAmount'),
        'balanceColumnContradictsOwnTotals': last_balance != 0 and total_out == 0,
        'totalInterestMinor': minor(obs['totalInterestAmount']),
        'totalPrincipalMinor': minor(obs['totalPrincipalAmount']),
        'totalRepaymentMinor': minor(obs['totalRepaymentAmount']),
        'allInterestRowsZero': all(x == 0 for x in interest_rows),
        'allButLastEmiZero': len(emi_rows) > 0 and all(x == 0 for x in emi_rows[:-1]),
        'lastEmiMinor': emi_rows[-1] if emi_rows else None,
        'balanceColumnConstant': len(set(balances)) == 1,
        'distinctBalances': sorted(set(balances)),
    }


def main(path, outpath):
    doc = json.load(open(path))
    caps = [c for c in doc['captures'] if c['id'].startswith('T83-SW-')]
    rows = [classify(c) for c in caps]

    by_shape = defaultdict(list)
    for r in rows:
        by_shape[(r['ratePct'], r['n'])].append(r)

    boundary = []
    anomalies = []
    for (rate, n), rs in sorted(by_shape.items(), key=lambda kv: (float(kv[0][0]), kv[0][1])):
        rs.sort(key=lambda r: r['principalMinor'])
        failing = [r['principalMinor'] for r in rs if not r['amortizes']]
        clean = [r['principalMinor'] for r in rs if r['amortizes']]
        contiguous = (failing == list(range(1, len(failing) + 1))) if failing else True
        if not contiguous:
            anomalies.append("rate %s n %d: failing set is NOT the contiguous prefix: %r"
                             % (rate, n, failing))
        # the smallest clean principal ABOVE every failing one
        smallest_clean_above = None
        if clean:
            hi = max(failing) if failing else 0
            above = [c for c in clean if c > hi]
            smallest_clean_above = min(above) if above else None
        for r in rs:
            if not r['amortizes'] and not r['principalColumnAmortizes']:
                anomalies.append("%s: principal column does NOT sum to the disbursed amount "
                                 "(%d vs %d)" % (r['id'], r['principalColumnSumMinor'], r['disbursedMinor']))
        boundary.append({
            'ratePct': rate,
            'numberOfRepayments': n,
            'sweptMinorFrom': rs[0]['principalMinor'],
            'sweptMinorTo': rs[-1]['principalMinor'],
            'casesRun': len(rs),
            'failingMinorUnits': failing,
            'largestFailingMinor': max(failing) if failing else None,
            'smallestCleanMinor': smallest_clean_above,
            'failingSetIsContiguousPrefix': contiguous,
            'cleanMinorUnits': clean,
        })

    summary = {
        'source': path,
        'sweepCases': len(rows),
        'failingCases': sum(1 for r in rows if not r['amortizes']),
        'cleanCases': sum(1 for r in rows if r['amortizes']),
        'everyFailingCasePrincipalColumnAmortizes':
            all(r['principalColumnAmortizes'] for r in rows if not r['amortizes']),
        'everyCasePrincipalColumnAmortizes': all(r['principalColumnAmortizes'] for r in rows),
        'everyFailingCaseContradictsOwnTotals':
            all(r['balanceColumnContradictsOwnTotals'] for r in rows if not r['amortizes']),
        'everyFailingCaseBalanceColumnConstant':
            all(r['balanceColumnConstant'] for r in rows if not r['amortizes']),
        'everyFailingCaseAllInterestRowsZero':
            all(r['allInterestRowsZero'] for r in rows if not r['amortizes']),
        'everyFailingCaseAllButLastEmiZero':
            all(r['allButLastEmiZero'] for r in rows if not r['amortizes']),
        'anomalies': anomalies,
        'boundary': boundary,
        'cases': rows,
    }
    with open(outpath, 'w') as f:
        json.dump(summary, f, indent=1)
        f.write("\n")

    print("swept %d cases: %d fail to amortize, %d clean"
          % (summary['sweepCases'], summary['failingCases'], summary['cleanCases']))
    print("every failing case's PRINCIPAL column still sums to the disbursed amount: %s"
          % summary['everyFailingCasePrincipalColumnAmortizes'])
    print("every failing case contradicts the oracle's own totalOutstandingAmount: %s"
          % summary['everyFailingCaseContradictsOwnTotals'])
    print("every failing case's balance column is CONSTANT across all rows: %s"
          % summary['everyFailingCaseBalanceColumnConstant'])
    print("anomalies: %d" % len(anomalies))
    for a in anomalies[:20]:
        print("  " + a)
    print()
    print("| rate %% | n | swept | largest FAILING (minor) | smallest CLEAN (minor) | contiguous |")
    print("|---|---|---|---|---|---|")
    for b in boundary:
        print("| %s | %d | %d..%d | %s | %s | %s |"
              % (b['ratePct'], b['numberOfRepayments'], b['sweptMinorFrom'], b['sweptMinorTo'],
                 b['largestFailingMinor'] if b['largestFailingMinor'] is not None else 'none',
                 b['smallestCleanMinor'] if b['smallestCleanMinor'] is not None else 'none',
                 b['failingSetIsContiguousPrefix']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
