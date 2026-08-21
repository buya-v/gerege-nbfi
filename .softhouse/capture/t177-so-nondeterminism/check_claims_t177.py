#!/usr/bin/env python3
"""T177 — mechanically re-derive the handful of handoff claims that are NOT printed verbatim by
analyze_t177.py, so no number in the handoff rests on hand arithmetic.

Zero claims checked is an ERROR (P-35).

Usage: check_claims_t177.py <repo-root>
"""
import glob
import json
import os
import sys
from collections import defaultdict

repo = sys.argv[1]
out = repo + '/.softhouse/capture/t177-so-nondeterminism/out'
DISPUTED = 'T177-PROBE-R600p0-N3000-B10001'

trials = []
for f in sorted(glob.glob(out + '/*/raw/*.stdout')):
    matrix = os.path.basename(os.path.dirname(os.path.dirname(f)))
    run = os.path.basename(f)[:-len('.stdout')]
    for ln in open(f, errors='replace'):
        ln = ln.strip()
        if not ln.startswith('{'):
            continue
        d = json.loads(ln)
        if d.get('kind') == 'trial':
            d['_proc'] = (matrix, run)
            trials.append(d)

checks = []


def check(name, got, want):
    checks.append((name, got, want, got == want))


probes = [t for t in trials if t.get('phase') == 'probe']
check('total trials of every kind emitted', len(trials), 348)
check('total probe trials', len(probes), 139)
check('probe trials of the DISPUTED cell', len([t for t in probes if t['cellId'] == DISPUTED]), 107)
check('java processes that emitted at least one trial', len({t['_proc'] for t in trials}), 75)
check('observed probes of the DISPUTED cell', len([t for t in probes
                                                   if t['cellId'] == DISPUTED and t['outcome'] == 'observed']), 31)

# every observed disputed probe carries the SAME totalInterestAmount
vals = {t['observed']['totalInterestAmount'] for t in probes
        if t['cellId'] == DISPUTED and t['outcome'] == 'observed'}
check('distinct totalInterestAmount over observed disputed probes', sorted(vals), ['846.70'])

# monotonicity: within one process, no observed is ever followed by a threw for the same cell
byproc = defaultdict(list)
for t in probes:
    byproc[(t['_proc'], t['cellId'])].append(t)
violations = 0
for k, ts in byproc.items():
    seen_observed = False
    for t in sorted(ts, key=lambda x: x['seq']):
        if t['outcome'] == 'observed':
            seen_observed = True
        elif seen_observed:
            violations += 1
check('processes where an observed probe was later followed by a throw (same cell)', violations, 0)

# every trial ran at the production MathContext
bad_mc = [t for t in trials if t.get('mathContextPrecision') != 19
          or t.get('mathContextRoundingMode') != 'HALF_UP'
          or t.get('ambientMoneyHelperMathContext') != 'precision=19 roundingMode=HALF_UP']
check('trials NOT at MathContext (19, HALF_UP) ambient and explicit', len(bad_mc), 0)

# no floating-point token anywhere in the emitted money fields
floaty = 0
for t in trials:
    o = t.get('observed') or {}
    for k, v in o.items():
        if isinstance(v, float):
            floaty += 1
check('emitted money fields that are JSON floats rather than strings', floaty, 0)

width = max(len(c[0]) for c in checks)
fails = 0
for name, got, want, ok in checks:
    print('  %-*s got %-22r want %-22r %s' % (width, name, got, want, 'OK' if ok else 'FAIL'))
    fails += 0 if ok else 1
print('CLAIM CHECK: %d claim(s) checked, %d FAILED' % (len(checks), fails))
if not checks:
    print('ERROR: zero claims checked (P-35)')
    sys.exit(1)
sys.exit(1 if fails else 0)
