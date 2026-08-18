#!/usr/bin/env python3
"""T22 INDEPENDENT AUDIT — second tenant-rounding-mode probe.

The first probe (pmode, multiplesOf=1) was absorbed by the EMI re-adjust loop
(ProgressiveEMICalculator.java:1258-1308), so it did NOT discriminate. This one
puts the tie one level lower, in the per-period interest rounding
(InterestPeriod.java:145-157 -> RepaymentPeriod.java:251-257 -> Money.java:52,
setScale(2, tenant rounding mode)), which the EMI loop does not touch.

Chosen input: principal 1,162,502.50 MNT. Period-1 interest is
1,162,502.50 * 0.018 = 20,925.045 exactly -> an exact half-cent tie at scale 2.
HALF_UP must give 20,925.05, HALF_EVEN must give 20,925.04.
No multiplesOf, so the EMI itself is identical under both modes.
"""
import collections
import json
import os

W = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb'
OUT = os.path.join(W, 't22-audit', 'req')

p = json.load(open(os.path.join(W, 'req', 'product-1-baseline.json')),
              object_pairs_hook=collections.OrderedDict)
p['name'] = 'T22 mode probe halfcent'
p['shortName'] = 'TM2'
p['principal'] = 1162502.50
json.dump(p, open(os.path.join(OUT, 'pmode2-halfcent.json'), 'w'), indent=1)

c = json.load(open(os.path.join(W, 'req', 'calc-B-01-baseline.json')),
              object_pairs_hook=collections.OrderedDict)
c['principal'] = 1162502.50
for tenant, pid in (('gerege', 11), ('default', 10)):
    o = collections.OrderedDict(c)
    o['productId'] = pid
    json.dump(o, open(os.path.join(OUT, 'calc-pmode2-%s.json' % tenant), 'w'), indent=1)
print('wrote pmode2 payloads')
