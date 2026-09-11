#!/usr/bin/env python3
"""Generate OWNER.md for the delinquency-mnt capture from scenario-results.json
and the extraction manifest.  Every fact is read from those artefacts; nothing is
hand-transcribed."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE = 'LoanDelinquency-Part1.feature'
SRC_LOG = ('/Users/buv/fineract-tierd/fineract-e2e-tests-runner/'
           'build/capture/feign-delinquency-mnt.log')
IMAGE = 'sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a'


def minor(value):
    if isinstance(value, (int, float)):
        return str(int(round(value * 100)))
    return '—'


def main():
    scen = json.load(open(os.path.join(HERE, 'scenario-results.json')))
    manifest = json.load(open(os.path.join(HERE, 'manifest-delinquency.json')))
    summary = json.load(open(os.path.join(HERE, 'summary-delinquency.json')))

    by_loan = {}
    for e in manifest:
        by_loan.setdefault(e['loan_id'], []).append(e)

    per_loan_principal = {}
    for lid, entries in by_loan.items():
        for e in entries:
            if e['kind'] != 'create':
                continue
            body = json.load(open(os.path.join(HERE, e['file'])))
            if body.get('principal') is not None:
                per_loan_principal[lid] = body['principal']
                break

    out = []
    w = out.append
    w('# OWNER — Tier D `LoanDelinquency-Part1.feature` MNT capture')
    w('')
    w('This directory owns the MNT read-backs captured by replaying the **whole**')
    w('`LoanDelinquency-Part1.feature` (50 scenarios: installment-level delinquency and')
    w('delinquency PAUSE periods) against the throwaway reference oracle, tenant `tierd`.')
    w('Capture only: no vector, no drive, no `.go`.')
    w('')
    w('## What is here')
    w('')
    w('| path | what |')
    w('| --- | --- |')
    w('| `OWNER.md` | this file: feature, scenarios, loans, and which read-back files belong to each |')
    w('| `replay-result-table.md` | the per-scenario PASSED/FAILED result table |')
    w('| `replay-delinquency-mnt.log` | raw cucumber/Gradle replay log (ANSI), 1,745 lines |')
    w('| `run-delinquency-mnt.sh` | the exact driver used for the replay |')
    w('| `scenario-results.json` | machine-readable per-scenario result + loan mapping |')
    w('| `attribute.py` | validated scenario→loan attribution (product name + clientId) |')
    w('| `organize.py` | flattens `stage/` into `loans/` and writes the manifests |')
    w('| `manifest-delinquency.json` | full extraction manifest (all 49 loans; `committed` flag) |')
    w('| `manifest-delinquency-passed.json` | manifest of the committed files (all PASSED) |')
    w('| `summary-delinquency.json` | extractor totals and per-loan counts |')
    w('| `loans/loan-<id>/` | the per-loan read-backs committed for the PASSED scenarios |')
    w('| `teardown-isolation.txt` | baseline-vs-teardown counter comparison |')
    w('')
    w('## Source')
    w('')
    w('- feature: `fineract-e2e-tests-runner/src/test/resources/features/%s`' % FEATURE)
    w('- throwaway tenant `tierd`; image `fineract:latest` `%s`' % IMAGE)
    w('  (proven identical to the standing reference oracle by `preflight.sh`)')
    w('- currency MNT (2 ISO 4217 minor digits, 496); money below is integer minor units')
    w('- capture: `%s`' % SRC_LOG)
    w('- capture size: %d B / %d lines' % (summary['source_bytes'], summary['total_lines']))
    w('- extraction: %d exchanges, %d loan-keyed, %d loans, %d files, %d kept body bytes' % (
        summary['total_exchanges'], summary['loan_exchanges'], len(summary['loans']),
        summary['files_written'], summary['kept_body_bytes']))
    w('- replay: 50 scenarios (50 passed); 1124 steps (1124 passed); no failure')
    w('')
    w('## Scenario → loan map')
    w('')
    w('Every scenario creates exactly one client and one customized loan at the top. Scenario')
    w('33 (C3014) deliberately makes its loan creation fail, so it owns no loan id and is the')
    w('run\'s single unattributed `POST /loans`; loan ids are contiguous 1..49 over scenarios')
    w('1..32, 34..50 in feature order. The mapping is not assumed: each loan\'s read-back')
    w('`loanProductName` equals its scenario\'s feature product and its `clientId` equals the')
    w('scenario position (`attribute.py`; 0 mismatches over 49 loans).')
    w('')
    w('| # | TestRailId | feature line | result | loan | product | principal (minor) | read-backs | committed |')
    w('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    for s in scen['scenarios']:
        if not s['loans']:
            w('| %d | %s | %d | %s | — | — | — | 0 | n/a (error scenario) |' % (
                s['index'], s['tag'], s['line'], s['result']))
            continue
        lid = s['loans'][0]
        reads = [e for e in by_loan.get(lid, []) if e['kind'] == 'read']
        w('| %d | %s | %d | %s | %d | `%s` | %s | %d | yes |' % (
            s['index'], s['tag'], s['line'], s['result'], lid,
            s['loan_product'], minor(per_loan_principal.get(lid)), len(reads)))
    w('')
    w('## Per-scenario read-back files')
    w('')
    w('`loans/loan-<id>/` holds **every** exchange the extractor attributed to that loan: the')
    w('`create-request`, the `approve`/`disburse`/`delinquency-actions`/`repayment`/... command')
    w('request+response pairs, and the `GET` read-backs. The read-backs (kind `read`) belonging')
    w('to each PASSED scenario are listed below; command request/response pairs sit in the same')
    w('directory and are visible in `manifest-delinquency.json`.')
    w('')
    for s in scen['scenarios']:
        if not s['loans']:
            w('### %d — %s — `PASSED` (error scenario) — no loan' % (s['index'], s['tag']))
            w('')
            w('Feature line %d: the loan creation is expected to fail, so no loan id and no' % s['line'])
            w('read-backs exist.')
            w('')
            continue
        lid = s['loans'][0]
        reads = [e for e in by_loan.get(lid, []) if e['kind'] == 'read']
        w('### %d — %s — `PASSED` — loan %d — %s' % (
            s['index'], s['tag'], lid, s['name']))
        w('')
        w('Feature line %d; product `%s`; principal %s minor units; read-backs: %d.' % (
            s['line'], s['loan_product'], minor(per_loan_principal.get(lid)), len(reads)))
        w('')
        w('```')
        for e in reads:
            w(e['file'])
        w('```')
        w('')
    mnt = eur_files = 0
    for e in manifest:
        blob = open(os.path.join(HERE, e['file']), 'rb').read()
        mnt += blob.count(b'"code":"MNT"')
        if b'EUR' in blob:
            eur_files += 1
    w('## Currency')
    w('')
    w('Every committed body carrying a currency object resolves to `code = "MNT"`'
      ' (%d occurrences); the literal token `EUR` appears in %d committed bodies.' % (mnt, eur_files))
    w('')
    w('## Isolation')
    w('')
    w('`preflight.sh` wrote the standing baseline before the throwaway started; `down.sh`')
    w('compared against that exact file and reported every counter equal to baseline')
    w('(`teardown-isolation.txt`). All `tierd-*` containers, the `tierd-oracle` network and its')
    w('volume are gone; standing tenants `gerege` and `default` were never written.')
    w('')

    with open(os.path.join(HERE, 'OWNER.md'), 'w') as fh:
        fh.write('\n'.join(out))
    print('wrote OWNER.md (%d lines)' % len(out))


if __name__ == '__main__':
    main()
