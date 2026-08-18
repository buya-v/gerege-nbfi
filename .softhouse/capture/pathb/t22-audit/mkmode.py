#!/usr/bin/env python3
"""T22 INDEPENDENT AUDIT — build the tenant-rounding-mode discrimination probe.

Input selected by t22_findmode.py: principal 1,163,000 MNT, 12 monthly,
21.6 % p.a., installmentAmountInMultiplesOf = 1. At that input the scale-0
divide inside Money.roundToMultiplesOf (Money.java:167) lands on an exact .5
tie, so HALF_UP and HALF_EVEN must diverge. The same product+request is put to
BOTH tenants; only the tenant's rounding mode differs.
"""
import collections
import json
import os

W = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb'
OUT = os.path.join(W, 't22-audit', 'req')

p = json.load(open(os.path.join(W, 'req', 'product-2-multiplesof100.json')),
              object_pairs_hook=collections.OrderedDict)
p['name'] = 'T22 mode probe mult1'
p['shortName'] = 'TM1'
p['installmentAmountInMultiplesOf'] = 1
p['principal'] = 1163000
json.dump(p, open(os.path.join(OUT, 'pmode-mult1.json'), 'w'), indent=1)

c = json.load(open(os.path.join(W, 'req', 'calc-B-01-baseline.json')),
              object_pairs_hook=collections.OrderedDict)
c['principal'] = 1163000
for tenant, pid in (('gerege', 10), ('default', 9)):
    o = collections.OrderedDict(c)
    o['productId'] = pid
    json.dump(o, open(os.path.join(OUT, 'calc-pmode-%s.json' % tenant), 'w'), indent=1)
print('wrote pmode-mult1.json, calc-pmode-gerege.json, calc-pmode-default.json')
