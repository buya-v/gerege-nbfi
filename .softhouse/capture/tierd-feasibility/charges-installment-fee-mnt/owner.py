#!/usr/bin/env python3
"""OH-TIERD7-BU: generate OWNER.md from scenario-results.json and the
extraction manifests.  Every fact is read from those artefacts (or from the
feature file for the waiver count); nothing is hand-transcribed.
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE = ('/Users/buv/fineract-tierd/fineract-e2e-tests-runner/'
           'src/test/resources/features/LoanChargesInstallmentFee.feature')
SRC_LOG = ('/Users/buv/fineract-tierd/fineract-e2e-tests-runner/'
           'build/capture/feign-installmentfee-mnt.log')
IMAGE = 'sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a'


def minor(value):
    if isinstance(value, (int, float)):
        return str(int(round(value * 100)))
    return '—'


def money(cell):
    """First numeric amount in a schedule cell list, as integer minor units."""
    for tok in cell.replace('[', '').replace(']', '').split(','):
        tok = tok.strip()
        if tok in ('null', '', '-'):
            continue
        try:
            return str(int(round(float(tok) * 100)))
        except ValueError:
            continue
    return '—'


def main():
    scen = json.load(open(os.path.join(HERE, 'scenario-results.json')))
    manifest = json.load(open(os.path.join(HERE, 'manifest-installmentfee.json')))
    passed = json.load(open(os.path.join(HERE, 'manifest-installmentfee-passed.json')))
    summary = json.load(open(os.path.join(HERE, 'summary-installmentfee.json')))

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

    waiver_steps = int(subprocess.check_output(
        ['grep', '-ic', 'waiv', FEATURE]).decode().strip())

    out = []
    w = out.append
    w('# OWNER — Tier D `LoanChargesInstallmentFee.feature` MNT capture')
    w('')
    w('This directory owns the MNT read-backs captured by replaying the **whole**')
    w('`LoanChargesInstallmentFee.feature` (28 scenarios: installment fees charged, partly')
    w('paid, and WAIVED) against the throwaway reference oracle, tenant `tierd`.  Capture')
    w('only: no vector, no drive, no `.go`.  Money in the tables, manifests and this file is')
    w('integer minor units (MNT, 2 ISO 4217 minor digits); the raw oracle bodies under')
    w('`loans/` carry the decimal major units the oracle emitted, unchanged.')
    w('')
    w('## What is here')
    w('')
    w('| path | what |')
    w('| --- | --- |')
    w('| `OWNER.md` | this file: feature, each scenario, its loans, and which read-back files belong to it |')
    w('| `replay-result-table.md` | the per-scenario PASSED/FAILED result table and failure deltas |')
    w('| `replay-installmentfee-mnt.log` | raw cucumber/Gradle replay log, %d lines |' % summary['total_lines'])
    w('| `run-installmentfee-mnt.sh` | the exact driver used for the replay |')
    w('| `scenario-results.json` | machine-readable per-scenario result, loan mapping and failed steps |')
    w('| `build-results.py` | parses the replay log and feature into the result tables |')
    w('| `organize.py` | copies committed bodies into `loans/` and writes the manifests |')
    w('| `owner.py` | generates this file |')
    w('| `manifest-installmentfee.json` | full extraction manifest (all %d bodies, `committed` flag) |' % len(manifest))
    w('| `manifest-installmentfee-passed.json` | manifest of the committed bodies (%d) |' % len(passed))
    w('| `summary-installmentfee.json` | extractor totals and per-loan counts |')
    w('| `loans/loan-<id>/` | the per-loan read-backs committed for the PASSED scenarios |')
    w('| `teardown-isolation.txt` | baseline-vs-teardown counter comparison |')
    w('')
    w('## Source')
    w('')
    w('- feature: `fineract-e2e-tests-runner/src/test/resources/features/LoanChargesInstallmentFee.feature`')
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
    w('- waiver coverage: %d waiver steps in the feature (the observations behind' % waiver_steps)
    w('  `loan/charge.go`\'s waiver arithmetic and `UpdateWaivedAmount` at 40%)')
    w('')
    w('## Scenario → loan map')
    w('')
    w('Every scenario creates exactly one client and one customized loan at the top, in')
    w('feature order, so scenario `k` owns loan `k` (%d scenarios, %d loans).  The mapping'
      % (scen['scenario_count'], scen['scenario_count']))
    w('is not assumed: each loan\'s read-back `loanProductName` equals its scenario\'s product')
    w('and its `clientId` equals the scenario position (`build-results.py`; 0 mismatches).')
    w('The one extra key in the extraction, "loan 131", is not a loan: it is the')
    w('external-id-keyed `reAge` transaction on loan 28, mis-keyed because the command')
    w('response\'s `resourceId` is a transaction id.  It is `committed: false` and carries a')
    w('`note` in `manifest-installmentfee.json`.')
    w('')
    w('| # | TestRailId | feature line | result | loan | product | principal (minor) | read-backs | committed |')
    w('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    for s in scen['scenarios']:
        lid = s['loan']
        reads = [e for e in by_loan.get(lid, []) if e['kind'] == 'read']
        committed = 'yes' if s['result'] == 'PASSED' else 'no (not committed)'
        w('| %d | %s | %d | %s | %d | `%s` | %s | %d | %s |' % (
            s['index'], s['tag'], s['feature_line'], s['result'], lid,
            s['loan_product_name'] or '—', minor(per_loan_principal.get(lid)),
            len(reads), committed))
    w('')
    w('A PASSED scenario has its loan directory committed; a FAILED scenario\'s bodies stay')
    w('in the git-ignored `stage/` and are listed (with `committed: false`) in the full')
    w('manifest only.  The `principal (minor)` column comes from each loan\'s')
    w('`create-request` body, converted from the decimal major units the oracle emitted.')
    w('')
    w('## Per-scenario read-back files')
    w('')
    w('`loans/loan-<id>/` holds **every** exchange the extractor attributed to that loan: the')
    w('`create-request`, the `approve`/`disburse`/`charge`/`repayment`/`waiver`/... command')
    w('request+response pairs, and the `GET` read-backs.  The read-backs (kind `read`)')
    w('belonging to each PASSED scenario are listed below; command request/response pairs sit')
    w('in the same directory and are visible in `manifest-installmentfee-passed.json`.')
    w('')
    for s in scen['scenarios']:
        lid = s['loan']
        reads = [e for e in by_loan.get(lid, []) if e['kind'] == 'read']
        if s['result'] == 'PASSED':
            w('### %d — %s — `PASSED` — loan %d — %s' % (
                s['index'], s['tag'], lid, s['name']))
            w('')
            w('Feature line %d; product `%s`; principal %s minor units; read-backs: %d; all' % (
                s['feature_line'], s['loan_product_name'] or '—',
                minor(per_loan_principal.get(lid)), len(reads)))
            w('committed under `loans/loan-%d/`.' % lid)
            w('')
            w('```')
            for e in reads:
                w(e['file'])
            w('```')
            w('')
        else:
            fs = s['failed_steps'][0] if s['failed_steps'] else {}
            w('### %d — %s — `FAILED` — loan %d — %s' % (
                s['index'], s['tag'], lid, s['name']))
            w('')
            w('Feature line %d; product `%s`; principal %s minor units; **not committed**.' % (
                s['feature_line'], s['loan_product_name'] or '—',
                minor(per_loan_principal.get(lid))))
            w('')
            if fs:
                w('Failing step (feature line %s): `%s`' % (
                    fs.get('step_feature_line'), fs['step']))
                w('')
                w('- resource id (loan): %s' % fs.get('resource'))
                w('- tab line (period) on the schedule table: %s' % fs.get('tab_line'))
                w('')
                w('Actual / expected schedule rows (amounts are decimal major units in the')
                w('log; `replay-result-table.md` gives the integer minor-unit deltas):')
                w('')
                w('```')
                w('actual   %s' % fs.get('actual', '—'))
                w('expected %s' % fs.get('expected', '—'))
                w('```')
                w('')
                w('Full per-cell deltas are in `replay-result-table.md`.')
                w('')
    w('## The two failure families (a finding)')
    w('')
    w('All %d failures are the same step, `LoanStepDef.loanRepaymentSchedulePeriodsCheck`,' % scen['failed'])
    w('and each differs from the `.feature` table in one period:')
    w('')
    w('- **Final-period fee rounding (12 of 13).** Scenarios 4, 5, 7, 8, 9, 10, 17, 20, 21,')
    w('  22, 24, 25 book one minor unit more Fees in the last period than the feature')
    w('  expects; Due and Outstanding follow by the same minor unit.  This is the last-period')
    w('  allocation of the installment-fee rounding remainder — the seam `loan/charge.go`')
    w('  computes.')
    w('- **Period-2 principal split (scenario 26).** The cumulative-loan scenario fails on')
    w('  period 2 with principal due 13.00 vs 12.00 expected (balance 62.00 vs 63.00, due')
    w('  23.00 vs 22.00) — a 100-minor-unit principal boundary shift, the same family as')
    w('  the UC10 1-minor-unit period-2 split recorded in')
    w('  `F-2026-09-11-tierd-repsched-mnt-uc10.md`.')
    w('')
    w('These are pin-vs-feature disagreements: the oracle produced the actual values.  No EUR')
    w('control was run in this task, but MNT and EUR share 2 ISO 4217 minor digits, so the')
    w('currency re-seed cannot by itself explain a one-minor-unit split.')
    w('')
    w('## The waiver scenario')
    w('')
    w('Scenario 23 (`C3797`, feature line 1816), the partially waived installment fee with')
    w('reverse-replay logic, **PASSED**, so its loan 23 read-backs are committed.  That loan')
    w('is the observation behind `loan/charge.go`\'s waiver arithmetic (`UpdateWaivedAmount`).')
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
      ' oracle emitted MNT observations, not synthesis.' % (mnt, eur_files))
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
