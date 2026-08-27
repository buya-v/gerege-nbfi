#!/usr/bin/env python3
"""T83 — check the REGISTERED prediction against the MEASURED boundary. Exits 1 if
any registered prediction is refuted, and prints every refutation in full.

Reads:
  predicted-boundary.json    committed in the PREDICTION commit, before any probe ran
  out/measured-boundary.json produced by classify-boundary.py from the capture
  out/capture-t83-raw.json   for the cell-level predictions P2 and P8

It never edits either file. A prediction that is refuted is reported, not amended.
"""
import json
import sys


def minor(s):
    s = s.strip()
    whole, _, frac = s.partition('.')
    frac = (frac + '00')[:2]
    return int(whole or '0') * 100 + int(frac or '0')


def main(predp, measp, rawp):
    pred = json.load(open(predp))
    meas = json.load(open(measp))
    doc = json.load(open(rawp))
    caps = {c['id']: c for c in doc['captures']}

    held, refuted = [], []

    def check(name, ok, detail):
        (held if ok else refuted).append("%s: %s" % (name, detail))

    # ---- P3 / P4 / P6: the boundary table, row by row -------------------------------------
    mb = {(b['ratePct'], b['numberOfRepayments']): b for b in meas['boundary']}
    for row in pred['rows']:
        key = (row['annualRatePct'], row['numberOfRepayments'])
        m = mb.get(key)
        if m is None:
            check('P3', False, "rate %s n %s was predicted but not measured" % key)
            continue
        want_fail = row['predictedLargestFailingMinor']
        got_fail = m['largestFailingMinor']
        want_fail_norm = None if want_fail == 0 else want_fail
        ok = (got_fail == want_fail_norm)
        check('P3', ok, "rate %s n %s: predicted largest failing %s, measured %s"
              % (key[0], key[1], want_fail_norm if want_fail_norm is not None else 'none',
                 got_fail if got_fail is not None else 'none'))
        want_clean = row['predictedSmallestCleanMinor']
        ok2 = (m['smallestCleanMinor'] == want_clean)
        check('P3-clean', ok2, "rate %s n %s: predicted smallest clean %s, measured %s"
              % (key[0], key[1], want_clean, m['smallestCleanMinor']))

    # P4 — n = 2 carries no failing principal at any rate
    for (rate, n), m in mb.items():
        if n == 2:
            check('P4', m['largestFailingMinor'] is None,
                  "rate %s n 2: largest failing measured %r (predicted: none)" % (rate, m['largestFailingMinor']))

    # P5 — contiguity
    for (rate, n), m in mb.items():
        check('P5', m['failingSetIsContiguousPrefix'],
              "rate %s n %s: failing set contiguous prefix = %s" % (rate, n, m['failingSetIsContiguousPrefix']))

    # P6 — the region exists at rates other than 21.6
    for rate in ('7.0', '16.8', '36.0'):
        any_fail = any(m['largestFailingMinor'] for (r, n), m in mb.items() if r == rate)
        check('P6', bool(any_fail), "rate %s: region non-empty = %s" % (rate, bool(any_fail)))

    # ---- P2 — T75's headline shape, cell for cell ------------------------------------------
    c = caps.get('T83-SW-R21p6-N6-B1')
    if c is None:
        check('P2', False, "T83-SW-R21p6-N6-B1 absent from the capture")
    else:
        o = c['observed']
        rows = [p for p in o['periods'] if p['type'] == 'REPAYMENT']
        want = [('0.00', '0.00', '0.00', '0.01')] * 5 + [('0.01', '0.00', '0.01', '0.01')]
        got = [(p['principal'], p['interest'], p['total'], p['balance']) for p in rows]
        check('P2', got == want, "MNT 0.01/6x21.6%% rows (principal,interest,total,balance): %r" % (got,))
        check('P2-totals', o['totalInterestAmount'] == '0.00' and o['totalOutstandingAmount'] == '0',
              "totalInterestAmount=%r totalOutstandingAmount=%r"
              % (o['totalInterestAmount'], o['totalOutstandingAmount']))

    # ---- P8 — the shape of EVERY failing schedule -------------------------------------------
    shape_bad = []
    for case in meas['cases']:
        if case['amortizes']:
            continue
        B = case['principalMinor']
        cap = caps[case['id']]
        periods = cap['observed']['periods']
        reps = [p for p in periods if p['type'] == 'REPAYMENT']
        if any(minor(p['balance']) != B for p in periods):
            shape_bad.append("%s: not every row's balance == principal %d" % (case['id'], B))
        if any(minor(p['principal']) != 0 or minor(p['total']) != 0 for p in reps[:-1]):
            shape_bad.append("%s: a non-final repayment row is non-zero" % case['id'])
        if minor(reps[-1]['principal']) != B or minor(reps[-1]['total']) != B:
            shape_bad.append("%s: final row principal/total is not %d" % (case['id'], B))
        if any(minor(p['interest']) != 0 for p in reps):
            shape_bad.append("%s: an interest cell is non-zero" % case['id'])
    check('P8', not shape_bad, "failing-schedule shape deviations: %d%s"
          % (len(shape_bad), (" e.g. " + shape_bad[0]) if shape_bad else ""))

    print("PREDICTIONS HELD:   %d" % len(held))
    print("PREDICTIONS REFUTED: %d" % len(refuted))
    for r in refuted:
        print("  REFUTED  " + r)
    if refuted:
        return 1
    for h in held[:6]:
        print("  held     " + h)
    print("  ... and %d more held" % max(0, len(held) - 6))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
