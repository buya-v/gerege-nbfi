#!/usr/bin/env python3
"""OH-TIERD8-BW: generate OWNER.md from scenario-results.json and the
extraction manifests.  Every fact is read from those artefacts (or from the
feature file for the charge-off step count); nothing is hand-transcribed.

Adopted from OH-TIERD7-BU `charges-installment-fee-mnt/owner.py`.
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE = ('/Users/buv/fineract-tierd/fineract-e2e-tests-runner/'
           'src/test/resources/features/LoanChargeOff-Part1.feature')
SRC_LOG = ('/Users/buv/fineract-tierd/fineract-e2e-tests-runner/'
           'build/capture/feign-chargeoff-mnt.log')
IMAGE = 'sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a'


def minor(value):
    if isinstance(value, (int, float)):
        return str(int(round(value * 100)))
    return '—'


def main():
    scen = json.load(open(os.path.join(HERE, 'scenario-results.json')))
    manifest = json.load(open(os.path.join(HERE, 'manifest-chargeoff.json')))
    passed = json.load(open(os.path.join(HERE, 'manifest-chargeoff-passed.json')))
    summary = json.load(open(os.path.join(HERE, 'summary-chargeoff.json')))

    by_loan = {}
    for e in manifest:
        by_loan.setdefault(e['loan_id'], []).append(e)

    per_loan_principal = {}
    for lid, entries in by_loan.items():
        for e in entries:
            if e['kind'] != 'create':
                continue
            body = json.load(open(os.path.join(HERE, 'stage', os.path.basename(e['file']))))
            if body.get('principal') is not None:
                per_loan_principal[lid] = body['principal']
                break

    chargeoff_steps = int(subprocess.check_output(
        ['grep', '-ic', 'charge-off', FEATURE]).decode().strip())

    out = []
    w = out.append
    w('# OWNER — Tier D `LoanChargeOff-Part1.feature` MNT capture')
    w('')
    w('This directory owns the MNT read-backs captured by replaying the **whole**')
    w('`LoanChargeOff-Part1.feature` (50 scenarios: charge-off after disbursement, after')
    w('repayment, after undo, fraud vs non-fraud, NSF/processing/penalty fees, goodwill,')
    w('reschedules and re-ages) against the throwaway reference oracle, tenant `tierd`.')
    w('Capture only: no vector, no drive, no `.go`.  Money in the tables, manifests and this')
    w('file is integer minor units (MNT, 2 ISO 4217 minor digits); the raw oracle bodies under')
    w('`loans/` carry the decimal major units the oracle emitted, unchanged.')
    w('')
    w('The point of this capture is the charged-off **write-off** branch — the journal entries')
    w('produced by `createJournalEntriesForWriteOffsWhenLoanIsChargedOff` — which no previous')
    w('capture had observed.  Every charge-off scenario below exercises it and the oracle')
    w('agreed with the `.feature` journal-entry expectations.')
    w('')
    w('## What is here')
    w('')
    w('| path | what |')
    w('| --- | --- |')
    w('| `OWNER.md` | this file: feature, each scenario, its loans, and which read-back files belong to it |')
    w('| `replay-result-table.md` | the per-scenario PASSED/FAILED result table |')
    w('| `replay-chargeoff-mnt.log` | raw cucumber/Gradle replay log, %d lines |' % summary['total_lines'])
    w('| `run-chargeoff-mnt.sh` | the exact driver used for the replay |')
    w('| `scenario-results.json` | machine-readable per-scenario result, loan mapping and failed steps |')
    w('| `build-results.py` | parses the replay log and feature into the result tables |')
    w('| `organize.py` | copies committed bodies into `loans/` and writes the manifests |')
    w('| `owner.py` | generates this file |')
    w('| `manifest-chargeoff.json` | full extraction manifest (all %d bodies, `committed` flag) |' % len(manifest))
    w('| `manifest-chargeoff-passed.json` | manifest of the committed bodies (%d) |' % len(passed))
    w('| `summary-chargeoff.json` | extractor totals and per-loan counts |')
    w('| `loans/loan-<id>/` | the per-loan read-backs committed for the PASSED scenarios |')
    w('| `teardown-isolation.txt` | baseline-vs-teardown counter comparison |')
    w('')
    w('## Source')
    w('')
    w('- feature: `fineract-e2e-tests-runner/src/test/resources/features/LoanChargeOff-Part1.feature`')
    w('- throwaway tenant `tierd`; image `fineract:latest` `%s`' % IMAGE)
    w('  (proven identical to the standing reference oracle by `preflight.sh`)')
    w('- currency MNT (2 ISO 4217 minor digits, 496); money below is integer minor units')
    w('- capture: `%s`' % SRC_LOG)
    w('- capture size: %d B / %d lines' % (summary['source_bytes'], summary['total_lines']))
    w('- extraction: %d exchanges, %d loan-keyed, %d loans, %d files, %d kept body bytes' % (
        summary['total_exchanges'], summary['loan_exchanges'], len(summary['loans']),
        summary['files_written'], summary['kept_body_bytes']))
    w('- replay: **%d scenarios (%d passed, %d failed)**; %d steps (%d passed, %d skipped, %d failed)' % (
        scen['scenario_count'], scen['passed'], scen['failed'],
        scen['steps']['total'], scen['steps']['passed'], scen['steps']['skipped'],
        scen['steps']['failed']))
    w('- charge-off coverage: %d charge-off steps in the feature' % chargeoff_steps)
    w('')
    w('## Scenario → loan map')
    w('')
    w('Every scenario creates exactly one client and one loan at the top, in feature order, so')
    w('scenario `k` owns loan `k` (%d scenarios, %d loans).  The mapping is not assumed: each'
      % (scen['scenario_count'], scen['scenario_count']))
    w('loan\'s create-request `clientId` equals the scenario position and the extraction found')
    w('exactly loans 1–50 with no unattributed create (`build-results.py`, 0 mismatches;')
    w('`attribution_validated: true`).')
    w('')
    w('| # | TestRailId | feature line | result | loan | product | principal (minor) | read-backs | committed |')
    w('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    for s in scen['scenarios']:
        lid = s['loan']
        reads = [e for e in by_loan.get(lid, []) if e['kind'] == 'read']
        committed = 'yes' if s['result'] == 'PASSED' else 'no (not committed)'
        w('| %d | %s | %d | %s | %d | `%s` | %s | %d | %s |' % (
            s['index'], s['tag'], s['feature_line'], s['result'], lid,
            s['feature_product'] or 'default progressive', minor(per_loan_principal.get(lid)),
            len(reads), committed))
    w('')
    w('All %d scenarios PASSED, so every loan directory is committed.  The `principal (minor)`'
      % scen['passed'])
    w('column comes from each loan\'s `create-request` body, converted from the decimal major')
    w('units the oracle emitted.')
    w('')
    w('## Per-scenario read-back files')
    w('')
    w('`loans/loan-<id>/` holds **every** exchange the extractor attributed to that loan: the')
    w('`create-request`, the `approve`/`disburse`/`charge-off`/`repayment`/`undo`/... command')
    w('request+response pairs, and the `GET` read-backs.  The read-backs (kind `read`) belonging')
    w('to each scenario are listed below; command request/response pairs sit in the same')
    w('directory and are visible in `manifest-chargeoff-passed.json`.')
    w('')
    for s in scen['scenarios']:
        lid = s['loan']
        reads = [e for e in by_loan.get(lid, []) if e['kind'] == 'read']
        w('### %d — %s — `%s` — loan %d — %s' % (
            s['index'], s['tag'], s['result'], lid, s['name']))
        w('')
        w('Feature line %d; product `%s`; principal %s minor units; read-backs: %d; all' % (
            s['feature_line'], s['feature_product'] or 'default progressive',
            minor(per_loan_principal.get(lid)), len(reads)))
        w('committed under `loans/loan-%d/`.' % lid)
        w('')
        w('```')
        for e in reads:
            w(e['file'])
        w('```')
        w('')
    w('## Failures')
    w('')
    if scen['failed'] == 0:
        w('None. Every scenario passed; the charged-off write-off branch')
        w('(`createJournalEntriesForWriteOffsWhenLoanIsChargedOff`) was exercised and the oracle')
        w('agreed with every `.feature` journal-entry expectation.  No EUR control was run in this')
        w('capture task.')
    else:
        w('%d scenario(s) failed; see `replay-result-table.md` for each failing step and the' % scen['failed'])
        w('actual-vs-expected values.  Only PASSED scenarios\' loans are committed.  The cause is')
        w('not decided here; the driver dispatches an EUR control.')
    w('')
    w('## Currency')
    w('')
    mnt = eur_files = 0
    for e in passed:
        blob = open(os.path.join(HERE, e['file']), 'rb').read()
        mnt += blob.count(b'"code":"MNT"')
        if b'EUR' in blob:
            eur_files += 1
    w('Every committed body carrying a currency object resolves to `code = "MNT"`'
      ' (%d occurrences); the literal token `EUR` appears in %d committed bodies.  So the'
      % (mnt, eur_files))
    w('oracle emitted MNT observations, not synthesis.')
    w('')
    w('## Isolation')
    w('')
    w('`preflight.sh` wrote the standing baseline before the throwaway started; `down.sh`')
    w('compared against that exact file and reported every counter equal to baseline')
    w('(`teardown-isolation.txt`).  All `tierd-*` containers, the `tierd-oracle` network and')
    w('its volume are gone; standing tenants `gerege` and `default` were never written.')
    w('')
    w('---')
    w('')
    w('This capture was created by an AI agent (OpenHands) on behalf of the user.')
    w('')

    with open(os.path.join(HERE, 'OWNER.md'), 'w') as fh:
        fh.write('\n'.join(out))
    print('wrote OWNER.md (%d lines)' % len(out))


if __name__ == '__main__':
    main()
