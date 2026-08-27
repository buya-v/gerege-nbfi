#!/usr/bin/env python3
"""T229 — read-only peek at the observed rows of one committed capture cell.
Exact arithmetic only: every money figure is parsed to INTEGER MINOR UNITS via Decimal
scaled by 100 and checked to be integral. No float anywhere."""
import gzip, json, sys
from decimal import Decimal

def minor(s):
    d = Decimal(str(s)) * 100
    assert d == d.to_integral_value(), s
    return int(d)

path, want = sys.argv[1], sys.argv[2]
d = json.load(gzip.open(path))
c = [c for c in d['captures'] if c.get('id') == want][0]
obs = c['observed']
print('observed keys:', list(obs.keys()) if isinstance(obs, dict) else type(obs))
if isinstance(obs, dict):
    for k, v in obs.items():
        if isinstance(v, list):
            print(k, ': list len', len(v))
            if v:
                print('   [0]', json.dumps(v[0])[:500])
                print('   [1]', json.dumps(v[1])[:500] if len(v) > 1 else '')
                print('   [-1]', json.dumps(v[-1])[:500])
        else:
            print(k, '=', json.dumps(v)[:300])
