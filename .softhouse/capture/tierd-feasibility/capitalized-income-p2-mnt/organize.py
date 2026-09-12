#!/usr/bin/env python3
"""OH-TIERD29-DO: organise the flat `stage/` extraction into the committed
`loans/loan-<id>/` layout and emit the manifests and summary.

Copy of OH-TIERD23-DC `chargeoff-p4-mnt/organize.py`; the manifest and summary file
names are feature-specific.  Only the PASSED scenarios' loans are committed; the
failed-loan branch is kept for reuse.  The `@Skip` scenarios own no loan, so they
contribute no bodies and are recorded under `skipped_scenarios`.  `stage/` is
git-ignored; this script copies (never moves) so it is idempotent and can be re-run
after extraction.
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.join(HERE, 'stage')
LOANS = os.path.join(HERE, 'loans')
RESULTS = os.path.join(HERE, 'scenario-results.json')


def main():
    scen = json.load(open(RESULTS))
    committed_loans = {s['loan'] for s in scen['scenarios'] if s['result'] == 'PASSED'}
    loan_scenario = {s['loan']: s['index'] for s in scen['scenarios']}

    if os.path.isdir(LOANS):
        shutil.rmtree(LOANS)
    os.makedirs(LOANS)

    copied = 0
    for fn in sorted(os.listdir(STAGE)):
        if not fn.endswith('.json') or fn in ('manifest.json', 'summary.json'):
            continue
        try:
            lid = int(fn.split('-')[1])
        except (IndexError, ValueError):
            continue
        if lid not in committed_loans:
            continue
        dest = os.path.join(LOANS, 'loan-%d' % lid)
        os.makedirs(dest, exist_ok=True)
        shutil.copy2(os.path.join(STAGE, fn), os.path.join(dest, fn))
        copied += 1
    print('copied %d body files into loans/loan-*/ (%d committed loans)'
          % (copied, len(committed_loans)))

    manifest = json.load(open(os.path.join(STAGE, 'manifest.json')))
    for e in manifest:
        lid = e['loan_id']
        e['file'] = 'loans/loan-%d/%s' % (lid, os.path.basename(e['file']))
        e['committed'] = lid in committed_loans
        e['scenario'] = loan_scenario.get(lid)
    manifest.sort(key=lambda e: (e['loan_id'], e['source_line'], e['file']))

    with open(os.path.join(HERE, 'manifest-capitalized-income-p2.json'), 'w') as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write('\n')
    passed = [e for e in manifest if e['committed']]
    with open(os.path.join(HERE, 'manifest-capitalized-income-p2-passed.json'), 'w') as fh:
        json.dump(passed, fh, indent=1, sort_keys=True)
        fh.write('\n')

    summary = json.load(open(os.path.join(STAGE, 'summary.json')))
    extracted_ids = sorted(int(k) for k in summary['loans'])
    summary['committed_loans'] = sorted(committed_loans)
    summary['failed_scenarios'] = sorted(s['index'] for s in scen['scenarios']
                                         if s['result'] == 'FAILED')
    summary['skipped_scenarios'] = sorted(
        (s['index'], s['tag']) for s in scen['scenarios'] if s['result'] == 'SKIPPED')
    summary['skipped_loans'] = sorted(
        int(k) for k in summary['loans'] if int(k) not in committed_loans)
    summary['unattributed_loan_ids'] = [i for i in extracted_ids if i not in loan_scenario]
    with open(os.path.join(HERE, 'summary-capitalized-income-p2.json'), 'w') as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
        fh.write('\n')

    print('manifest entries: %d; committed: %d; loans: %d; unattributed: %s' % (
        len(manifest), len(passed), len(summary['loans']),
        summary['unattributed_loan_ids']))
    print('kept_body_bytes: %d of committed files: %d' % (
        summary['kept_body_bytes'], sum(e['bytes'] for e in passed)))


if __name__ == '__main__':
    main()
