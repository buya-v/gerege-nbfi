#!/usr/bin/env python3
"""T223 scratch: read committed raw captures and print row shapes. Exact arithmetic only
(no float anywhere on a money path); this script only prints strings from the capture."""
import gzip
import json
import sys

path = sys.argv[1]
ids = sys.argv[2:]
opener = gzip.open if path.endswith('.gz') else open
d = json.load(opener(path))
cs = {x['id']: x for x in d['captures']}
if not ids:
    for k in cs:
        print(k)
    sys.exit(0)
for cid in ids:
    x = cs[cid]
    o = x.get('observed')
    if o is None:
        print('===', cid, 'NO observed; error =', x.get('error'))
        continue
    ps = o['periods']
    print('===', cid, 'B=', x['inputs']['disbursementAmount'], 'n=', x['inputs']['numberOfRepayments'],
          'rate=', x['inputs']['annualNominalInterestRate'])
    print('    totalPrincipal', o['totalPrincipalAmount'], 'totalInterest', o['totalInterestAmount'],
          'totalOutstanding', o['totalOutstandingAmount'])
    print('    row keys:', sorted(ps[1].keys()))
    for p in ps[:3] + ps[-2:]:
        print('   ', json.dumps(p, sort_keys=True))
