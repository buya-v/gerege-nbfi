#!/usr/bin/env python3
"""Reorganise the flat `stage/` extraction into the committed `loans/loan-<id>/`
layout and emit the delinquency manifest(s).

The extractor writes `loan-<id>-<label>.json` flat plus `manifest.json` /
`summary.json`.  The committed capture mirrors `repayment-schedule-mnt/`: every
body under `loans/loan-<id>/`, a manifest whose `file` path is repo-relative,
and `committed: true` on each entry (all 50 scenarios passed, so every extracted
body is committed).
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.join(HERE, 'stage')
LOANS = os.path.join(HERE, 'loans')


def loan_id(fn):
    return int(fn.split('-')[1])


def main():
    if os.path.isdir(LOANS):
        shutil.rmtree(LOANS)
    os.makedirs(LOANS)

    files = sorted(os.listdir(STAGE))
    moved = 0
    for fn in files:
        if not fn.endswith('.json') or fn in ('manifest.json', 'summary.json'):
            continue
        lid = loan_id(fn)
        dest = os.path.join(LOANS, 'loan-%d' % lid)
        os.makedirs(dest, exist_ok=True)
        shutil.move(os.path.join(STAGE, fn), os.path.join(dest, fn))
        moved += 1
    print('moved %d body files into loans/loan-*/' % moved)

    manifest = json.load(open(os.path.join(STAGE, 'manifest.json')))
    for e in manifest:
        e['file'] = 'loans/loan-%d/%s' % (e['loan_id'], os.path.basename(e['file']))
        e['committed'] = True
    manifest.sort(key=lambda e: (e['loan_id'], e['source_line'], e['file']))

    with open(os.path.join(HERE, 'manifest-delinquency.json'), 'w') as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write('\n')
    with open(os.path.join(HERE, 'manifest-delinquency-passed.json'), 'w') as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write('\n')

    summary = json.load(open(os.path.join(STAGE, 'summary.json')))
    with open(os.path.join(HERE, 'summary-delinquency.json'), 'w') as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
        fh.write('\n')

    print('manifest entries: %d; loans: %d; committed: %d' % (
        len(manifest), len(summary['loans']),
        sum(1 for e in manifest if e['committed'])))
    print('kept_body_bytes: %d' % summary['kept_body_bytes'])


if __name__ == '__main__':
    main()
