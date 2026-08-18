#!/usr/bin/env python3
"""T36 — did the EMI re-adjust loop actually FIRE on the oracle?

For each probe capture, compare the OBSERVED period-1..11 EMI against two from-source models:
  A. NO-LOOP model  — T22's audited re-derivation, which stops before
     checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods (ProgressiveEMICalculator.java:1258-1308).
  B. LOOP model     — the same walk plus the loop, implemented from the same source.

If observation == B and observation != A, the loop fired and the capture PINS it.
If observation == A == B, the shape does not discriminate.
If observation matches neither, that is a finding and is printed as such — no value is
adjusted to make it agree.

Money read as exact Decimal; every comparison in integer minor units; no tolerance.
"""
import json
import os
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t36_emiloop_search as S                                    # noqa: E402

OUT = os.path.join(HERE, 'out', 'emiloop')
PRINCIPALS = [1200000, 1200001, 1200004, 1200027, 1200033, 1200039, 1200045, 1200054, 1200189]


def load(p):
    with open(p, 'rb') as fh:
        return json.loads(fh.read().decode(), parse_float=Decimal, parse_int=Decimal)


def minor(x):
    v = x * 100
    assert v == v.to_integral_value(), 'not representable in minor units: %s' % x
    return int(v)


rows_out = []
fired, disagreements = [], []
for p in PRINCIPALS:
    path = os.path.join(OUT, 'emiloop-%d-raw.json' % p)
    j = load(path)
    periods = [q for q in j['periods'] if 'period' in q]
    obs_emi = {q['totalDueForPeriod'] for q in periods[:-1]}       # periods 1..11
    assert len(obs_emi) == 1, 'periods 1..11 are not a single EMI: %s' % obs_emi
    obs_emi = obs_emi.pop()
    obs_last = periods[-1]['totalDueForPeriod']
    obs_total = j['totalRepaymentExpected']

    P = Decimal(p)
    no_loop_emi = S.emi_for(P)
    _r, no_loop_res = S.walk(P, no_loop_emi, S.RFS)
    loop_emi, loop_res, trace = S.loop_prediction(P)

    match_noloop = minor(obs_emi) == minor(no_loop_emi)
    match_loop = minor(obs_emi) == minor(loop_emi)
    discriminates = minor(no_loop_emi) != minor(loop_emi)

    if match_loop and discriminates and not match_noloop:
        verdict = 'LOOP FIRED — observation matches the loop model and REFUTES the no-loop model'
        fired.append(p)
    elif match_loop and match_noloop:
        verdict = 'no discrimination (both models agree)'
    elif not match_loop and not match_noloop:
        verdict = '** OBSERVATION MATCHES NEITHER MODEL — FINDING **'
        disagreements.append(p)
    elif match_noloop and discriminates:
        verdict = '** LOOP DID NOT FIRE though the model predicted it would — FINDING **'
        disagreements.append(p)
    else:
        verdict = 'inconclusive'

    rows_out.append((p, no_loop_emi, no_loop_res, loop_emi, loop_res, obs_emi, obs_last,
                     obs_total, verdict))

print('%-10s %-12s %-8s %-12s %-8s %-12s %-12s' %
      ('principal', 'model EMI', 'resid', 'loop EMI', 'resid', 'OBSERVED EMI', 'OBS last'))
for r in rows_out:
    print('%-10s %-12s %-8s %-12s %-8s %-12s %-12s\n    -> %s'
          % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[8]))

print()
print('captures where the EMI re-adjust loop demonstrably FIRED: %s'
      % (', '.join(str(p) for p in fired) or 'NONE'))
print('captures where observation matched neither model: %s'
      % (', '.join(str(p) for p in disagreements) or 'NONE'))
sys.exit(1 if disagreements else 0)
