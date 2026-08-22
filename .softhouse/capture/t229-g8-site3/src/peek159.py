#!/usr/bin/env python3
"""T229 — read-only peek at a committed raw capture. Exact arithmetic only (int minor units)."""
import gzip, json, sys

path = sys.argv[1]
want = sys.argv[2] if len(sys.argv) > 2 else None
d = json.load(gzip.open(path))
caps = d['captures']
print('captures:', len(caps))
ids = [c.get('id') for c in caps]
if want is None:
    for i in ids:
        print(i)
    sys.exit(0)
sel = [c for c in caps if c.get('id') == want]
if not sel:
    print('NOT FOUND. ids containing the fragment:')
    for i in ids:
        if want.split('-')[-1] in str(i):
            print('  ', i)
    sys.exit(1)
c = sel[0]
print('top-level keys:', list(c.keys()))
for k, v in c.items():
    if k in ('observed',):
        continue
    print(k, '=', json.dumps(v)[:400])
