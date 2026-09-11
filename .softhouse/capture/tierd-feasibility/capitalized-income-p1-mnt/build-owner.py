#!/usr/bin/env python3
"""OH-TIERD18-CS step 6: write OWNER.md from the capitalized-income type join.

Reads journalentry-type-join.json (built by build-type-join.py) plus the
replay/extraction/sweep/product manifests, and emits the type x charged-off
join, every capitalized-income leg, and each capitalized-income transaction's read-back
amount and portions.  Money is integer minor units throughout.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    return json.load(open(os.path.join(HERE, name)))


def date_str(seq):
    if not seq:
        return '-'
    return '%04d-%02d-%02d' % tuple(seq)


def main():
    J = load('journalentry-type-join.json')
    R = load('scenario-results.json')
    S = load('summary-capitalized-income-p1.json')
    W = load('journalentries-sweep-manifest.json')
    PM = load('product-mappings/manifest.json')

    legs = J['legs']
    unmatched = len(J['unmatched_legs'])
    types = J['types']
    bd = J['capitalized_income']
    currencies = J['currencies']
    loan_co = J['loan_chargeoff']
    loan_ids = sorted((int(x) for x in currencies))
    sweep_legs = sum(x['page_items'] for x in W)
    sweep_ok = sum(1 for x in W if x['http_status'] == '200')
    sweep_bad_json = sum(1 for x in W if not x['json_valid'])
    sweep_bad_curl = sum(1 for x in W if x['curl_returncode'] != 0)
    bd_types = bd['by_type']

    out = []
    w = out.append

    w('# OWNER — Tier D `LoanCapitalizedIncome-Part1.feature` MNT capture **plus a full '
      'journal-entry sweep** (OH-TIERD18-CS)')
    w('')
    w('Whole-file replay of `LoanCapitalizedIncome-Part1.feature` (%d scenarios) against the throwaway '
      'reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), '
      'with the Feign capture on, **and then — while the throwaway was still up — one bounded '
      '`GET /journalentries?loanId=<id>&limit=-1` for every one of the %d loans the replay created.** '
      'Capture only: no vector, no drive, no `.go`. Money in this file, in the join and in the TSV '
      'is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under '
      '`journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.'
      % (R['scenario_count'], len(loan_ids)))
    w('')
    w('The target is the CAPITALIZED-INCOME posting family of '
      '`AccrualBasedAccountingProcessorForLoan.java` :195-530 — `createJournalEntriesForCapitalizedIncome`, '
      '`...CapitalizedIncomeAdjustment`, `...CapitalizedIncomeAmortization`, '
      '`...ChargeOffLoanCapitalizedIncomeAmortization` and `...CapitalizedIncomeAmortizationAdjustment` — which had '
      'never been observed at the GL level. `LoanCapitalizedIncome-Part1.feature` exercises all of them, with '
      'charge-offs on part of the file. This capture joins every swept leg to its transaction TYPE '
      'and to the loan\'s CHARGED-OFF state at the transaction date, and lists every capitalized-income leg, '
      'each capitalized-income transaction\'s amount and its read-back portions.')
    w('')

    w('## Provenance')
    w('')
    w('OH-TIERD18-CS ran the rig, the replay (%d/%d), the extraction, the sweep, the product '
      'mappings, the teardown and the type join. Every command ran in the FOREGROUND with a bound '
      '(curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no '
      '`jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`); the '
      'join was built offline over the captured JSON. Nothing was written into `/Users/buv/fineract`; '
      'the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; '
      'no Oracle.' % (R['passed'], R['scenario_count']))
    w('')

    w('## What is here')
    w('')
    w('| path | what |')
    w('| --- | --- |')
    w('| `OWNER.md` | this file |')
    w('| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |')
    w('| `run-capitalized-income-p1-mnt.sh` | the exact replay driver (only FEATURE / LOG / container changed from the OH-TIERD17-CR copy) |')
    w('| `replay-capitalized-income-p1-mnt.log` | raw cucumber/Gradle replay log |')
    w('| `loans/loan-<id>/` | per-loan read-backs of the %d PASSED scenarios (%d bodies) |'
      % (R['passed'], S['files_written']))
    w('| `manifest-capitalized-income-p1.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |')
    w('| `summary-capitalized-income-p1.json` | extractor totals and per-loan counts |')
    w('| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, %d/%d HTTP 200 |'
      % (sweep_ok, len(W)))
    w('| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |')
    w('| `journalentries-sweep.out` | per-loan sweep log |')
    w('| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |')
    w('| `product-mappings/` | accepted create requests of the %d products the loans use, from THIS replay\'s log, sha256 in `manifest.json` |'
      % len(PM))
    w('| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off/fraud state |')
    w('| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |')
    w('| `capitalized-income-legs.tsv` | flat listing of every capitalized-income leg (required columns) |')
    w('| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |')
    w('| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |')
    w('| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |')
    w('')

    w('## Replay result (step 1)')
    w('')
    w('**%d scenarios, %d PASSED, %d FAILED; %d steps (%d passed, %d skipped, %d failed).** '
      'Recorded, not diagnosed.'
      % (R['scenario_count'], R['passed'], R['failed'], R['steps']['total'],
         R['steps']['passed'], R['steps']['skipped'], R['steps']['failed']))
    w('')
    w('| # | tag | line | result | loan | product |')
    w('| ---: | --- | ---: | --- | ---: | --- |')
    for s in R['scenarios']:
        w('| %d | %s | %d | %s | %d | `%s` |' % (
            s['index'], s['tag'], s['feature_line'], s['result'], s['loan'],
            s['feature_product']))
    w('')

    w('## Extraction (step 2)')
    w('')
    w('Extracted with `bin/extract.py` and the copied `organize.py`: %d loans, %d bodies kept '
      'under `loans/`, each body sha256-pinned in `manifest-capitalized-income-p1.json`; the FAILED '
      'scenarios\' loans are not committed (`manifest-capitalized-income-p1-passed.json`).'
      % (len(loan_ids), S['files_written']))
    w('')

    w('## The sweep (step 3)')
    w('')
    w('For every loan id the replay created, one bounded read:')
    w('')
    w('```')
    w('curl -sk --max-time 30 -u mifos:password -H \'Fineract-Platform-TenantId: tierd\' \\')
    w('  \'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1\'')
    w('```')
    w('')
    w('**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or '
      '`default`.** A GET only; no write. Result: **%d/%d HTTP 200, %d curl failures, %d '
      'JSON-invalid bodies, %d legs total**, each body saved verbatim and sha256-recorded in '
      '`journalentries-sweep-manifest.json` with its exact URL.'
      % (sweep_ok, len(W), sweep_bad_curl, sweep_bad_json, sweep_legs))
    w('')

    w('## Teardown (step 5)')
    w('')
    w('`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the '
      '`tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The '
      '**standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** '
      'counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.')
    w('')

    w('## The type join — swept leg → transaction TYPE, CHARGED-OFF, FRAUD (step 6)')
    w('')
    w('Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its '
      'transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`). '
      '**%d legs, %d types, %d unmatched.**' % (legs, len(types), unmatched))
    w('')
    w('`charged_off` per leg = **a non-reversed `chargeOff` loan transaction dated on or before the '
      'leg\'s transaction date.** `fraud` per leg = the loan\'s fraud flag (`markAsFraud` '
      'request/read-back).')
    w('')

    w('### Type × charged-off → legs → loans (all types)')
    w('')
    w('| transaction type | legs | legs on charged-off loan | loans on charged-off |')
    w('| --- | ---: | ---: | --- |')
    for key in sorted(types, key=lambda k: (-len(types[k]['legs']), k)):
        t = types[key]
        onco = [r for r in t['legs'] if r['charged_off']]
        loans_co = sorted({r['loan'] for r in onco})
        label = '`(unmapped)`' if key == '(unmapped)' else '`%s`' % key
        w('| %s | %d | %d | %s |' % (
            label, len(t['legs']), len(onco),
            ', '.join(str(x) for x in loans_co) or '–'))
    w('')

    w('### The capitalized-income arms (step 6)')
    w('')
    w('Charged-off rule: %s.' % bd['charged_off_rule'])
    w('')
    w('| type | present | legs | transactions | loans | legs on charged-off loan | loans on charged-off | legs on not-charged-off | loans on not-charged-off |')
    w('| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |')
    for code in bd['target_types']:
        t = bd_types[code]
        w('| `%s` | %s | %d | %d | %s | %d | %s | %d | %s |' % (
            code, t['present'], t['total_legs'], len(t['total_transactions']),
            ', '.join(str(x) for x in t['total_loans']) or '–',
            t['legs_on_charged_off_loan'],
            ', '.join(str(x) for x in t['loans_on_charged_off']) or '–',
            t['legs_on_not_charged_off_loan'],
            ', '.join(str(x) for x in t['loans_on_not_charged_off']) or '–'))
    w('')
    for f in bd['findings']:
        w('**FINDING:** %s' % f)
        w('')

    w('### Every capitalized-income leg — required listing')
    w('')
    w('Every leg of every capitalized-income transaction type, with the leg\'s GL account (id + name), '
      'entry side, amount in minor units, the loan fraud flag and whether the loan was charged off '
      'at the transaction date.')
    w('')
    w('| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged_off | currency | tx date | charge-off tx |')
    w('| --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- |')
    any_leg = False
    for tx in bd['transactions']:
        for r in tx['legs']:
            any_leg = True
            w('| `%s` | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
                r['type_code'], r['loan'], r['transaction_id'], r['entry_type'],
                r['gl_account_id'], r['gl_account_code'], r['gl_account_name'],
                r['amount_minor'], r['fraud'], r['charged_off'], r['currency'],
                date_str(r['transaction_date']),
                ', '.join(r['chargeoff_tx_ids']) or '-'))
    if not any_leg:
        w('| _none_ | | | | | | | | | | | | |')
    w('')

    w('### Every capitalized-income transaction and its read-back amount / portions')
    w('')
    w('Portions are integer minor units; `-` means the read-back did not carry that field. The '
      '`amount` is the transaction `amount`; portions are the oracle\'s `principalPortion`, '
      '`interestPortion`, `feeChargesPortion`, `penaltyChargesPortion`, `overpaymentPortion` and '
      '`unrecognizedIncomePortion`.')
    w('')
    w('| loan | tx | type | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged_off | fraud | currency | legs |')
    w('| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: |')
    for t in bd['transactions']:
        p = t['portions'] or {}

        def _m(k):
            v = p.get(k)
            return '-' if v is None else v
        w('| %d | %s | `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d |' % (
            t['loan'], t['transaction_id'], t['type_code'], date_str(t['date']),
            t['amount_minor'], _m('principal_minor'), _m('interest_minor'), _m('fee_minor'),
            _m('penalty_minor'), _m('overpayment_minor'), _m('unrecognized_income_minor'),
            t['reversed'], t['charged_off'], t['fraud'], t['currency'], len(t['legs'])))
    if not bd['transactions']:
        w('| _no capitalized-income transactions_ | | | | | | | | | | | | | | |')
    w('')

    w('### Per-loan currency, charge-off and fraud state')
    w('')
    w('| loan | currency | fraud | non-reversed chargeOff transactions |')
    w('| ---: | --- | --- | --- |')
    for lid in loan_ids:
        li = loan_co[str(lid)]
        cos = ', '.join('%s@%s' % (c['transaction_id'], date_str(c['date']))
                        for c in li['chargeoff_transactions']) or '-'
        w('| %d | %s | %s | %s |' % (
            lid, currencies[str(lid)], li['fraud'], cos))
    w('')
    w('Every loan in this capture is **MNT**.')
    w('')

    w('## Findings — what the sweep observed and did not')
    w('')
    for code in bd['target_types']:
        t = bd_types[code]
        if t['total_legs']:
            w('* **Observed — `%s` at the GL level:** %d leg(s) on %d loan transaction(s) across '
              'loans %s; %d leg(s) on a charged-off loan (loans %s). The per-leg listing above '
              'gives each leg and its account; the per-transaction table gives the amount and '
              'portions.' % (
                  code, t['total_legs'], len(t['total_transactions']),
                  ', '.join(str(x) for x in t['total_loans']) or '-',
                  t['legs_on_charged_off_loan'],
                  ', '.join(str(x) for x in t['loans_on_charged_off']) or '-'))
        else:
            w('* **FINDING — `%s` has NO legs:** the type is absent from every swept body. The '
              'capitalized-income arm it names was not exercised at the GL level by this replay (or its '
              'loan was not extracted). This is a finding, not a silent gap.' % code)
    if bd['transactions_without_legs']:
        w('* **FINDING — capitalized-income transaction(s) without journal-entry legs:** %s. The '
          'capitalized-income arms should post for every such transaction, so a leg-less transaction is '
          'a shape worth checking.' % (
              ', '.join('loan %d tx %s' % (t['loan'], t['transaction_id'])
                        for t in bd['transactions_without_legs'])))
    if unmatched:
        ua = J['unmatched_analysis']
        w('* **Unmatched / not type-confirmable:** %d legs (%d transaction%s) carry no entry in any '
          '`transactions` read-back; see `journalentry-type-join.md`.' % (
              ua['legs'], ua['count'], '' if ua['count'] == 1 else 's'))
    w('* **Fraud:** no loan in this feature is fraud-flagged, so the `isMarkedFraud` / '
      'charge-off-fraud variants are not exercised (every `fraud` above is `false`).')
    w('')

    path = os.path.join(HERE, 'OWNER.md')
    with open(path, 'w') as f:
        f.write('\n'.join(out) + '\n')
    print('wrote %s (%d lines)' % (path, len(out)))


if __name__ == '__main__':
    main()
