#!/usr/bin/env python3
"""OH-TIERD30-DR: organise the flat `stage/` extraction into the committed
`loans/loan-<id>/` layout and emit the manifests and summary.

Copy of OH-TIERD22-DB `merchant-refund-mnt/organize.py`; only the manifest and summary
file names changed for this feature.  Only the passing scenarios' loans are committed;
the failed-loan branch is kept for reuse.  `stage/` is git-ignored; this script
copies (never moves) so it is idempotent and can be re-run after extraction.
"""
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.join(HERE, 'stage')
LOANS = os.path.join(HERE, 'loans')
RESULTS = os.path.join(HERE, 'scenario-results.json')

# bin/extract.py routes loan traffic by the numeric id in the URL.  A command sent
# to `/loans/external-id/<uuid>/...` has no numeric id, so it falls through to the
# bare `POST /loans` branch and is keyed by the response `resourceId` -- a
# TRANSACTION id, not a loan id.  Those bodies do not belong to the loan directory
# they land in; they are recorded here with `committed: false` and a `note`, and
# never copied (same convention as charges-installment-fee-mnt/OWNER.md).
EXTERNAL_ID_RE = re.compile(r'/loans/external-id/([^/]+)/')
CREATE_RE = re.compile(r'^loan-(\d+)-')


def external_id_owner(extid):
    """True loan id carrying `extid`, read from the loan-keyed read-backs."""
    for fn in sorted(os.listdir(STAGE)):
        m = CREATE_RE.match(fn)
        if not m:
            continue
        path = os.path.join(STAGE, fn)
        try:
            if os.path.getsize(path) > 16_000_000:
                continue
            with open(path, 'rb') as fh:
                if extid.encode('ascii') in fh.read():
                    return int(m.group(1))
        except OSError:
            continue
    return None


def main():
    scen = json.load(open(RESULTS))
    committed_loans = {s['loan'] for s in scen['scenarios'] if s['result'] == 'PASSED'}
    loan_scenario = {s['loan']: s['index'] for s in scen['scenarios']}

    manifest = json.load(open(os.path.join(STAGE, 'manifest.json')))
    miskeyed = set()
    miskeyed_notes = {}
    for e in manifest:
        m = EXTERNAL_ID_RE.search(e.get('url', ''))
        if not m:
            continue
        miskeyed.add(e['file'])
        owner = external_id_owner(m.group(1))
        miskeyed_notes[e['file']] = {
            'external_id': m.group(1),
            'keyed_loan': e['loan_id'],
            'owner_loan': owner,
        }

    if os.path.isdir(LOANS):
        shutil.rmtree(LOANS)
    os.makedirs(LOANS)

    copied = 0
    for fn in sorted(os.listdir(STAGE)):
        if not fn.endswith('.json') or fn in ('manifest.json', 'summary.json'):
            continue
        if fn in miskeyed:
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
    print('copied %d body files into loans/loan-*/ (%d committed loans); skipped %d '
          'mis-keyed external-id bodies' % (copied, len(committed_loans), len(miskeyed)))

    for e in manifest:
        lid = e['loan_id']
        base = os.path.basename(e['file'])
        e['file'] = 'loans/loan-%d/%s' % (lid, base)
        e['committed'] = lid in committed_loans and base not in miskeyed
        e['scenario'] = loan_scenario.get(lid)
        if base in miskeyed:
            info = miskeyed_notes[base]
            e['note'] = ('mis-keyed by bin/extract.py: external-id route for externalId '
                         '%s; keyed here to loan %s by the response resourceId (a '
                         'transaction id), but the owning loan is %s (see OWNER.md)'
                         % (info['external_id'], info['keyed_loan'], info['owner_loan']))
    manifest.sort(key=lambda e: (e['loan_id'], e['source_line'], e['file']))

    with open(os.path.join(HERE, 'manifest-reamortization-p1.json'), 'w') as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write('\n')
    passed = [e for e in manifest if e['committed']]
    with open(os.path.join(HERE, 'manifest-reamortization-p1-passed.json'), 'w') as fh:
        json.dump(passed, fh, indent=1, sort_keys=True)
        fh.write('\n')

    summary = json.load(open(os.path.join(STAGE, 'summary.json')))
    extracted_ids = sorted(int(k) for k in summary['loans'])
    summary['committed_loans'] = sorted(committed_loans)
    summary['failed_scenarios'] = sorted(s['index'] for s in scen['scenarios']
                                         if s['result'] == 'FAILED')
    summary['unattributed_loan_ids'] = [i for i in extracted_ids if i not in loan_scenario]
    summary['mis_keyed_external_id_bodies'] = sorted(
        (dict({'stage_file': f}, **miskeyed_notes[f]) for f in miskeyed),
        key=lambda d: d['stage_file'])
    with open(os.path.join(HERE, 'summary-reamortization-p1.json'), 'w') as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
        fh.write('\n')

    print('manifest entries: %d; committed: %d; loans: %d; unattributed: %s' % (
        len(manifest), len(passed), len(summary['loans']),
        summary['unattributed_loan_ids']))
    print('kept_body_bytes: %d of committed files: %d' % (
        summary['kept_body_bytes'], sum(e['bytes'] for e in passed)))
    print('mis-keyed external-id bodies: %s' % summary['mis_keyed_external_id_bodies'])


if __name__ == '__main__':
    main()
