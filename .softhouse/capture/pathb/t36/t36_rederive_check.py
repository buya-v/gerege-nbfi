#!/usr/bin/env python3
"""T36 — does the PRODUCTION-SETTINGS re-capture still reproduce T30's from-source
re-derivation of B-03 / B-04?

T30 rebuilt both schedules from the pinned Fineract source (DAILY / ACTUAL-ACTUAL arm,
including the cross-year partial-period branch) and matched the committed captures
digit-for-digit at both (19, HALF_EVEN) and (19, HALF_UP).  A contradiction here — a
capture taken on a tenant that really is at (19, HALF_UP) diverging from that model —
would be a major finding.

This imports T30's checker UNCHANGED (it is outside this task's write scope and must
stay so) and re-points it at the T36 re-captures.  No expected value is authored here.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
T30 = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'reviews', 't30-probe',
                                    't30_rederive_b03_b04.py'))
R = os.path.join(HERE, 'out', 'recapture-gerege')

spec = importlib.util.spec_from_file_location('t30', T30)
t30 = importlib.util.module_from_spec(spec)
sys.modules['t30'] = t30
spec.loader.exec_module(t30)

results = {}
for mode in ('HALF_UP', 'HALF_EVEN'):
    results[('B-03', mode)] = t30.compare(
        os.path.join(R, 'B-03-diycs-fullleapyear-raw.json'),
        'T36 re-capture B-03 FULL_LEAP_YEAR (gerege, 19/HALF_UP)', 'FULL_LEAP_YEAR', mode)
    results[('B-04', mode)] = t30.compare(
        os.path.join(R, 'B-04-diycs-feb29only-raw.json'),
        'T36 re-capture B-04 FEB_29_PERIOD_ONLY (gerege, 19/HALF_UP)', 'FEB_29_PERIOD_ONLY', mode)

print('=' * 100)
for k in sorted(results):
    print('  %-6s model-mode %-10s : %s' % (k[0], k[1], 'CONSISTENT' if results[k] else 'INCONSISTENT'))
allok = all(results.values())
print('OVERALL: %s' % ('PASS — the (19, HALF_UP) re-captures are CONSISTENT with T30\'s from-source '
                       're-derivation' if allok else 'FAIL — CONTRADICTION, this is a major finding'))
sys.exit(0 if allok else 1)
