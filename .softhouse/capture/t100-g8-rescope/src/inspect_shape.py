#!/usr/bin/env python3
"""T100: inspect the structure of T84's committed captures before re-deriving from them."""
import json, gzip, sys

path = sys.argv[1]
d = json.load(gzip.open(path)) if path.endswith('.gz') else json.load(open(path))
print('top keys:', [k for k in d])
print('meta:', {k: v for k, v in d.items() if k not in ('captures', 'attestation')})
caps = d['captures']
print('captures:', len(caps))
e = caps[0]
print('capture keys:', list(e.keys()))
print(json.dumps(e, indent=1)[:2500])
