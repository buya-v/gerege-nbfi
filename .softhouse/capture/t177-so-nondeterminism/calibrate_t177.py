#!/usr/bin/env python3
"""T177 RIG CALIBRATION.

Proves that CaptureT177 calls the SAME seam, with the SAME inputs, and produces the SAME numbers as
every other capture rig in this program -- by reproducing the two committed pass-3g cells T64-ZP-A
and T64-ZP-B cell for cell, TOTALS AND EVERY PERIOD ROW. If this fails, nothing else T177 measures
is believable, because the harness would not be the same measurement apparatus.

It compares BY EXTRACTION from the committed JSON, never by a retyped literal (P-46).

Usage: calibrate_t177.py <repo-root> <calib-stdout-file>
Exit 0 only when the comparison is complete AND zero fields differ AND at least one field was
compared (a vacuous pass is an ERROR, P-35).
"""
import json
import sys

TOTALS = ['loanTermInDays', 'totalDisbursedAmount', 'totalPrincipalAmount', 'totalInterestAmount',
          'totalFeeAmount', 'totalPenaltyAmount', 'totalRepaymentAmount', 'totalOutstandingAmount']
PAIRS = [('P-CAL-ZPA', 'T64-ZP-A'), ('P-CAL-ZPB', 'T64-ZP-B')]


def main():
    repo, calib_file = sys.argv[1], sys.argv[2]
    ref_path = repo + '/.softhouse/capture/out/capture-prod3g-raw.json'
    ref = json.load(open(ref_path))
    refmap = {c['id']: c for c in ref['captures']}

    mine = {}
    for ln in open(calib_file):
        ln = ln.strip()
        if not ln.startswith('{'):
            continue
        d = json.loads(ln)
        if d.get('kind') == 'trial':
            mine[d['cellId']] = d

    compared = 0
    diffs = []
    for mid, rid in PAIRS:
        if mid not in mine:
            diffs.append('T177 calibration cell %s ABSENT from %s' % (mid, calib_file))
            continue
        if rid not in refmap:
            diffs.append('pass 3g cell %s ABSENT from %s' % (rid, ref_path))
            continue
        if mine[mid].get('outcome') != 'observed':
            diffs.append('%s outcome is %r, not observed' % (mid, mine[mid].get('outcome')))
            continue
        m, r = mine[mid]['observed'], refmap[rid]['observed']
        for k in TOTALS:
            compared += 1
            if str(m[k]) != str(r[k]):
                diffs.append('%s/%s %s: T177 %r vs pass3g %r' % (mid, rid, k, m[k], r[k]))
        mp, rp = m['periods'], r['periods']
        compared += 1
        if len(mp) != len(rp):
            diffs.append('%s/%s period count: T177 %d vs pass3g %d' % (mid, rid, len(mp), len(rp)))
        for i, (a, b) in enumerate(zip(mp, rp)):
            compared += 1
            if a != b:
                diffs.append('%s/%s period row %d: T177 %r vs pass3g %r' % (mid, rid, i, a, b))
        print('%s vs pass 3g %s: %d totals + %d period rows compared' % (mid, rid, len(TOTALS), len(mp)))

    print('CALIBRATION: %d fields/rows compared, %d differ' % (compared, len(diffs)))
    if compared == 0:
        print('ERROR: zero fields compared -- a calibration that inspects nothing is a FAILURE (P-35)')
        sys.exit(1)
    for d in diffs:
        print('  DIFF ' + d)
    if diffs:
        print('CALIBRATION FAILED')
        sys.exit(1)
    print('CALIBRATION PASSED -- CaptureT177 reproduces pass 3g cell for cell, so it is the same')
    print('measurement apparatus as the rigs whose disagreement T177 is investigating.')


if __name__ == '__main__':
    main()
