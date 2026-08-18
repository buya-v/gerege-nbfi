#!/usr/bin/env python3
"""T22 INDEPENDENT AUDIT — search for an input at which the TENANT ROUNDING MODE
must move the schedule, so the mode can be shown to be LIVE on Path B rather than
merely unasserted.

The model is t22_rederive.py's, which reproduces B-01 and B-02 digit-for-digit.
Nothing here is a vector: it only selects a candidate INPUT to put to the oracle.
"""
import datetime
import sys

sys.path.insert(0, '/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb/t22-audit')
from decimal import Decimal
from t22_rederive import derive

first_from = datetime.date(2026, 1, 1)
dues = [datetime.date(2026 + (m // 12), (m % 12) + 1, 1) for m in range(1, 13)]

found = []
for mult in (1, 100):
    for p in range(1000000, 1400001, 1000):
        P = Decimal(p)
        a = derive(P, 12, Decimal('21.6'), dues, first_from, multiples_of=mult, mode='HALF_UP')
        b = derive(P, 12, Decimal('21.6'), dues, first_from, multiples_of=mult, mode='HALF_EVEN')
        if a['total_repayment'] != b['total_repayment'] or a['emi'] != b['emi']:
            found.append((mult, p, a['emi'], b['emi'], a['total_repayment'], b['total_repayment']))
            if len(found) >= 6:
                break
    if len(found) >= 6:
        break

for f in found:
    print('multiplesOf=%-4s principal=%-9s HALF_UP emi=%-12s HALF_EVEN emi=%-12s  totalRep %s vs %s'
          % f)
print('candidates:', len(found))
