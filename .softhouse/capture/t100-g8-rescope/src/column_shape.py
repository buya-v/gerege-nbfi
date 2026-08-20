#!/usr/bin/env python3
"""T100 — the per-column shape of each case: is the balance column constant? what does the last
row carry? Integer minor units only."""
import json, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from classify_two_families import minor, load, classify   # noqa: E402

rows = []
for path in sys.argv[1:]:
    for cap in load(path)['captures']:
        r = classify(cap)
        dp = r['dp']
        reps = [p for p in cap['observed']['periods'] if p['type'] == 'REPAYMENT']
        bals = [minor(p['balance'], dp) for p in reps]
        ints = [minor(p['interest'], dp) for p in reps]
        prins = [minor(p['principal'], dp) for p in reps]
        rows.append(dict(id=r['id'], family=r['family'], disb=r['disbursed_minor'],
                         balance_constant_at_disbursed=(set(bals) == {r['disbursed_minor']}),
                         distinct_balances=len(set(bals)),
                         last_balance=bals[-1], last_interest=ints[-1], last_principal=prins[-1],
                         interest_sum=sum(ints), principal_sum=sum(prins),
                         nonzero_principal_rows=sum(1 for p in prins if p != 0),
                         total_outstanding_amount=r['total_outstanding_amount_minor']))
print('%-32s %-7s %-6s %-9s %-9s %-9s %-9s %-9s %s'
      % ('id', 'family', 'disb', 'balConst', 'distBal', 'lastBal', 'lastInt', 'lastPrin', 'nonzeroPrinRows'))
for r in rows:
    print('%-32s %-7s %-6d %-9s %-9d %-9d %-9d %-9d %d'
          % (r['id'], r['family'], r['disb'], r['balance_constant_at_disbursed'], r['distinct_balances'],
             r['last_balance'], r['last_interest'], r['last_principal'], r['nonzero_principal_rows']))
json.dump(rows, open(__file__.replace('/src/', '/out/').replace('column_shape.py', 'column-shape.json'),
                     'w'), indent=1)
