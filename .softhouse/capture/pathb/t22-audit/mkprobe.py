#!/usr/bin/env python3
"""T22 INDEPENDENT AUDIT — build the probe products that settle the orchestrator's
two explicit NON-claims (PATHB-REPORT.md, Result 3 "Honest caveat"):

  (i)  the ISOLATED effect of `daysInYearCustomStrategy` under
       interestCalculationPeriodType = SAME_AS_REPAYMENT_PERIOD;
  (ii) whether `daysInYearType` / `daysInMonthType` affect a PROGRESSIVE schedule.

Every payload is derived from the COMMITTED Path B product payloads by changing
only the named fields (plus name/shortName, which the server forces unique).
"""
import collections
import json
import os

W = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb'
OUT = os.path.join(W, 't22-audit', 'req')
os.makedirs(OUT, exist_ok=True)


def load(n):
    return json.load(open(os.path.join(W, 'req', n + '.json')),
                     object_pairs_hook=collections.OrderedDict)


def write(name, o):
    with open(os.path.join(OUT, name + '.json'), 'w') as fh:
        json.dump(o, fh, indent=1)
    print('wrote', name)


base = load('product-1-baseline')       # ICPT=1 (SAME_AS_REPAYMENT_PERIOD), Actual/Actual
daily = load('product-3-diycs-fullleapyear')  # ICPT=0 (DAILY), Actual/Actual, DIYCS set

# --- (i) DIYCS under SAME_AS_REPAYMENT_PERIOD ------------------------------
for tag, short, strat in (('p05-diycs-sarp-full', 'TP5', 'FULL_LEAP_YEAR'),
                          ('p06-diycs-sarp-feb29', 'TP6', 'FEB_29_PERIOD_ONLY')):
    o = collections.OrderedDict(base)
    o['name'] = 'T22 probe ' + tag
    o['shortName'] = short
    o['daysInYearCustomStrategy'] = strat
    write(tag, o)

# --- (ii) day-count under DAILY -------------------------------------------
o = collections.OrderedDict(daily)
o['name'] = 'T22 probe p07-daily-actact'
o['shortName'] = 'TP7'
del o['daysInYearCustomStrategy']
write('p07-daily-actact', o)

o = collections.OrderedDict(daily)
o['name'] = 'T22 probe p08-daily-360-30'
o['shortName'] = 'TP8'
del o['daysInYearCustomStrategy']
o['daysInYearType'] = 360
o['daysInMonthType'] = 30
write('p08-daily-360-30', o)

# --- (ii) day-count under SAME_AS_REPAYMENT_PERIOD -------------------------
o = collections.OrderedDict(base)
o['name'] = 'T22 probe p09-sarp-360-30'
o['shortName'] = 'TP9'
o['daysInYearType'] = 360
o['daysInMonthType'] = 30
write('p09-sarp-360-30', o)

# --- calc payloads ---------------------------------------------------------
# 2024 disbursement (client 2) for everything that must span 29 Feb 2024;
# probes 5/6 use the leap term because that is the only place DIYCS could bite.
calc2024 = load('calc-B-03-diycs-fullleapyear')   # clientId 2, 01 January 2024, ICPT 0
calc2026 = load('calc-B-01-baseline')             # clientId 1, 01 January 2026, ICPT 1

for pid, tag, src, icpt in ((5, 'p05', calc2024, 1), (6, 'p06', calc2024, 1),
                            (7, 'p07', calc2024, 0), (8, 'p08', calc2024, 0),
                            (9, 'p09', calc2026, 1)):
    o = collections.OrderedDict(src)
    o['productId'] = pid
    o['interestCalculationPeriodType'] = icpt
    write('calc-' + tag, o)
