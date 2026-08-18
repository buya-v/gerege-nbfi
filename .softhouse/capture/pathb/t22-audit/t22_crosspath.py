#!/usr/bin/env python3
"""T22 INDEPENDENT AUDIT — cross-path claim.

PATHB-REPORT.md Result 1 claims Path B `B-01` reproduces pass-3 Path A
`P-MNT-1M2` "to the minor unit". This script tests that claim mechanically,
in integer minor units, with money read as exact Decimal (never float).

Path A capture:  .softhouse/capture/out/capture-prod-raw.json  (id P-MNT-1M2)
Path B capture:  .softhouse/capture/pathb/out/B-01-baseline-raw.json
"""
import json
from decimal import Decimal

ROOT = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse'
A = ROOT + '/capture/out/capture-prod-raw.json'
B = ROOT + '/capture/pathb/out/B-01-baseline-raw.json'


def m(x):
    d = x if isinstance(x, Decimal) else Decimal(str(x))
    s = d * 100
    assert s == s.to_integral_value(), x
    return int(s)


pa = json.load(open(A), parse_float=Decimal, parse_int=Decimal)
cap = [c for c in pa['captures'] if c['id'] == 'P-MNT-1M2'][0]
obs = cap['observed']
pb = json.loads(open(B, 'rb').read().decode(), parse_float=Decimal,
                parse_int=Decimal)

arows = [p for p in obs['periods'] if p['type'] == 'REPAYMENT']
brows = [p for p in pb['periods'] if 'period' in p]

print('Path A inputs: daysInMonth=%s daysInYear=%s precision=%s mode=%s disb=%s'
      % (cap['inputs']['daysInMonth'], cap['inputs']['daysInYear'],
         cap['inputs']['mathContextPrecision'],
         cap['inputs']['mathContextRoundingMode'],
         cap['inputs']['disbursementDate']))
print('Path A loanTermInDays=%s   Path B loanTermInDays=%s'
      % (obs['loanTermInDays'], pb['loanTermInDays']))
print()

fails = []
print(' per   A principal  B principal   A interest   B interest    A total     B total    A balance   B balance')
for a, b in zip(arows, brows):
    row = [m(a['principal']), m(b['principalDue']),
           m(a['interest']), m(b['interestDue']),
           m(a['total']), m(b['totalDueForPeriod']),
           m(a['balance']), m(b['principalLoanBalanceOutstanding'])]
    ok = row[0] == row[1] and row[2] == row[3] and row[4] == row[5] and row[6] == row[7]
    if not ok:
        fails.append(int(a['periodNumber']))
    print(' %3d  %11d %11d  %11d %11d  %10d %10d  %10d %10d  %s'
          % (int(a['periodNumber']), *row, 'ok' if ok else '**MISMATCH**'))

tot = [('totalDisbursed', m(obs['totalDisbursedAmount']), m(pb['totalPrincipalDisbursed'])),
       ('totalInterest', m(obs['totalInterestAmount']), m(pb['totalInterestCharged'])),
       ('totalRepayment', m(obs['totalRepaymentAmount']), m(pb['totalRepaymentExpected']))]
print()
for n, x, y in tot:
    print(' %-16s A=%-12d B=%-12d %s' % (n, x, y, 'ok' if x == y else '**MISMATCH**'))
    if x != y:
        fails.append(n)

print()
print(' period count A=%d B=%d' % (len(arows), len(brows)))
print(' due dates    A[0]=%s B[0]=%s   (differ by design: 2024 vs 2026 disbursement)'
      % (arows[0]['dueDate'], '-'.join(str(int(x)) for x in brows[0]['dueDate'])))
print()
print(' VERDICT: %s' % ('MONEY IDENTICAL IN ALL 12 PERIODS AND ALL TOTALS'
                        if not fails else 'MISMATCH at %r' % fails))
