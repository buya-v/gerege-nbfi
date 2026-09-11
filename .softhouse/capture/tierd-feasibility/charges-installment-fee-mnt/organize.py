#!/usr/bin/env python3
"""OH-TIERD7-BU: organise the flat `stage/` extraction into the committed
`loans/loan-<id>/` layout and emit the manifests and summary.

The extractor writes `loan-<id>-<label>.json` flat plus `manifest.json` /
`summary.json`.  The committed capture mirrors `repayment-schedule-mnt/`:
every body under `loans/loan-<id>/`, a manifest whose `file` path is
repo-relative, and a `committed` flag on each entry.

Unlike the delinquency run, not every scenario passed here (15/28).  Only the
loans of PASSED scenarios are committed; the failed scenarios' bodies stay in
`stage/` (git-ignored) and appear in the full manifest with `committed: false`.

Files are copied, not moved, so this script is idempotent and can be re-run
after a fresh extraction without losing `stage/`.
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.join(HERE, 'stage')
LOANS = os.path.join(HERE, 'loans')
RESULTS = os.path.join(HERE, 'scenario-results.json')

# Extract of the external-id-keyed reAge command on loan 28: the extractor keys a
# loan from any POST /loans response `resourceId`, and a transaction command on a
# loan addressed by external id returns the *transaction* id (131) there.  It is
# not a loan; `loan-131-create-request.json` is loan 28's reAge request.
REAGE_ARTIFACT = 131


def main():
    scen = json.load(open(RESULTS))
    committed_loans = {s['loan'] for s in scen['scenarios'] if s['result'] == 'PASSED'}
    loan_scenario = {s['loan']: s['index'] for s in scen['scenarios']}

    if os.path.isdir(LOANS):
        shutil.rmtree(LOANS)
    os.makedirs(LOANS)

    copied = 0
    for fn in os.listdir(STAGE):
        if not fn.endswith('.json') or fn in ('manifest.json', 'summary.json'):
            continue
        lid = int(fn.split('-')[1])
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
        if lid == REAGE_ARTIFACT:
            e['committed'] = False
            e['scenario'] = None
            e['note'] = ('extractor artifact: POST .../loans/external-id/<uuid>/transactions'
                         '?command=reAge on loan 28; the response resourceId is a transaction'
                         ' id, not a loan id')
    manifest.sort(key=lambda e: (e['loan_id'], e['source_line'], e['file']))

    with open(os.path.join(HERE, 'manifest-installmentfee.json'), 'w') as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write('\n')
    passed = [e for e in manifest if e['committed']]
    with open(os.path.join(HERE, 'manifest-installmentfee-passed.json'), 'w') as fh:
        json.dump(passed, fh, indent=1, sort_keys=True)
        fh.write('\n')

    summary = json.load(open(os.path.join(STAGE, 'summary.json')))
    summary['unattributed_loan_ids'] = [REAGE_ARTIFACT]
    summary['unattributed_note'] = ('loan 131 is not a loan: it is the external-id-keyed reAge'
                                    ' transaction on loan 28 (scenario 28), mis-keyed by the'
                                    ' extractor because its response resourceId is a'
                                    ' transaction id')
    summary['committed_loans'] = sorted(committed_loans)
    summary['failed_loans'] = sorted(loan_scenario[l] for l in
                                     set(loan_scenario) - committed_loans)
    summary['failed_scenarios'] = sorted(s['index'] for s in scen['scenarios']
                                         if s['result'] == 'FAILED')
    with open(os.path.join(HERE, 'summary-installmentfee.json'), 'w') as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
        fh.write('\n')

    print('manifest entries: %d; committed: %d; loans: %d' % (
        len(manifest), len(passed), len(summary['loans'])))
    print('kept_body_bytes: %d of committed files: %d' % (
        summary['kept_body_bytes'], sum(e['bytes'] for e in passed)))


if __name__ == '__main__':
    main()
