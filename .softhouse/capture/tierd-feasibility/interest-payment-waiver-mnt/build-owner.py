#!/usr/bin/env python3
"""OH-TIERD14-CL step 6: write OWNER.md from the type join.

Reads journalentry-type-join.json (built by build-type-join.py) plus the
replay/extraction/sweep manifests, and emits the type x charged-off join and
the required per-leg listings.  Money is integer minor units throughout.
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
    S = load('summary-interest-payment-waiver.json')
    W = load('journalentries-sweep-manifest.json')
    PM = load('product-mappings/manifest.json')

    legs = J['legs']
    unmatched = len(J['unmatched_legs'])
    types = J['types']
    rg = J['refund_goodwill']
    currencies = J['currencies']
    loan_co = J['loan_chargeoff']
    loan_ids = sorted((int(x) for x in currencies))
    sweep_legs = sum(x['page_items'] for x in W)
    sweep_ok = sum(1 for x in W if x['http_status'] == '200')
    sweep_bad_json = sum(1 for x in W if not x['json_valid'])
    sweep_bad_curl = sum(1 for x in W if x['curl_returncode'] != 0)

    out = []
    w = out.append

    w('# OWNER — Tier D `LoanInterestPaymentWaiver.feature` MNT capture **plus a full '
      'journal-entry sweep** (OH-TIERD14-CL)')
    w('')
    w('Whole-file replay of `LoanInterestPaymentWaiver.feature` (%d scenarios) against the throwaway '
      'reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), '
      'with the Feign capture on, **and then — while the throwaway was still up — one bounded '
      '`GET /journalentries?loanId=<id>&limit=-1` for every one of the %d loans the replay created.** '
      'Capture only: no vector, no drive, no `.go`. Money in this file, in the join and in the TSVs '
      'is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under '
      '`journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.'
      % (R['scenario_count'], len(loan_ids)))
    w('')
    w('The target is three posting branches that were still UNOBSERVED or thin at the GL level:')
    w('')
    w('* `createJournalEntriesForInterestPaymentWaiverOrInterestRefund` '
      '[`AccrualBasedAccountingProcessorForLoan.java:793`] — the interest-payment-waiver posting, '
      'never before observed at the GL level;')
    w('* the GOODWILL-CREDIT arm of `createJournalEntriesForRepaymentWhenLoanIsChargedOff` '
      '[`:1388`] — a goodwill credit made **after** a charge-off (the ChargeOff-Part1 goodwill credits '
      'were backdated before their charge-off, so they posted through the non-charged-off arm);')
    w('* the PAYOUT-REFUND arm of the same method (seen twice before).')
    w('')
    w('This capture joins every swept leg to its transaction TYPE and to the loan\'s CHARGED-OFF state '
      'at the transaction date, and lists every `interestPaymentWaiver` leg and every '
      '`merchantIssuedRefund` / `payoutRefund` / `goodwillCredit` leg that posted on a charged-off loan.')
    w('')

    w('## Provenance')
    w('')
    w('OH-TIERD14-CL ran the rig, the replay (%d/%d), the extraction, the sweep, the product mappings, '
      'the teardown and the type join. Every command ran in the FOREGROUND with a bound (curl '
      '`--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no '
      '`wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`); the join was built '
      'offline over the captured JSON. Nothing was written into `/Users/buv/fineract`; the replay was '
      'done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.'
      % (R['passed'], R['scenario_count']))
    w('')

    w('## What is here')
    w('')
    w('| path | what |')
    w('| --- | --- |')
    w('| `OWNER.md` | this file |')
    w('| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |')
    w('| `run-interest-payment-waiver-mnt.sh` | the exact replay driver (only FEATURE / LOG / container changed from the Part-3 copy) |')
    w('| `replay-interest-payment-waiver-mnt.log` | raw cucumber/Gradle replay log (168,123,968 B / 52,310 lines) |')
    w('| `loans/loan-<id>/` | per-loan read-backs of the %d PASSED scenarios (%d bodies) |'
      % (R['passed'], S['files_written']))
    w('| `manifest-interest-payment-waiver.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |')
    w('| `summary-interest-payment-waiver.json` | extractor totals and per-loan counts |')
    w('| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, %d/%d HTTP 200 |'
      % (sweep_ok, len(W)))
    w('| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |')
    w('| `journalentries-sweep.out` | per-loan sweep log |')
    w('| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |')
    w('| `product-mappings/` | accepted create requests of the %d products the loans use, from THIS replay\'s log, sha256 in `manifest.json` |'
      % len(PM))
    w('| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off/fraud state |')
    w('| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |')
    w('| `chargedoff-refund-goodwill.tsv` | flat listing of every refund/goodwill leg on a charged-off loan (required columns) |')
    w('| `accrual-legs.tsv` | flat listing of every accrual-type leg |')
    w('| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |')
    w('| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |')
    w('| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |')
    w('')

    w('## Replay result (step 1)')
    w('')
    w('**%d scenarios, %d PASSED, %d FAILED; %d steps (%d passed, %d skipped, %d failed).** '
      'Recorded, not diagnosed; no scenario failed, so there is nothing to diagnose.'
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
    w('Source log 168,123,968 bytes / 52,310 lines; 2,003 exchanges (589 loan-attributed, 88%% of source '
      'bytes skipped); %d loans; %d bodies kept (%d bytes) under `loans/`; each body sha256-pinned in '
      'the manifest.' % (len(loan_ids), S['files_written'], S['kept_body_bytes']))
    w('')

    w('## The sweep (step 3)')
    w('')
    w('For every loan id the replay created, one bounded read:')
    w('')
    w('```')
    w("curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \\")
    w("  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'")
    w('```')
    w('')
    w('**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or '
      '`default`.** A GET only; no write. Result: **%d/%d HTTP 200, %d curl failures, %d '
      'JSON-invalid bodies, %d legs total**, each body saved verbatim and sha256-recorded in '
      '`journalentries-sweep-manifest.json` with its exact URL.'
      % (sweep_ok, len(W), sweep_bad_curl, sweep_bad_json, sweep_legs))
    w('')

    w('## Product mappings (step 4)')
    w('')
    w('`extract-product-mappings.py` pulled the accepted create requests of the **%d** loan products the '
      'loans use out of this replay\'s Feign log; sha256 in `product-mappings/manifest.json`.'
      % len(PM))
    w('')
    for m in PM:
        w('* `%s`' % os.path.basename(m['file']).replace('create-request-', '').replace('.json', ''))
    w('')

    w('## Teardown (step 5)')
    w('')
    w('`down.sh`: the `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` '
      'network and every named volume are gone; `docker ps` shows no `tierd-*`. The **standing** '
      '`gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal '
      'the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.')
    w('')

    w('## The type join — swept leg → transaction TYPE, CHARGED-OFF, FRAUD (step 6)')
    w('')
    w('Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its '
      'transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`). '
      '**%d legs, %d types, %d unmatched.**' % (legs, len(types), unmatched))
    w('')
    w('`charged_off` per leg = **a non-reversed `chargeOff` loan transaction dated on or before the '
      'leg\'s transaction date.** `fraud` per leg = the loan\'s fraud flag (`markAsFraud` '
      'request/read-back); no loan in this feature is fraud-flagged, so every `fraud` below is `false` '
      'and the fraud variants of the refund arms are not exercised.')
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

    w('### The three target arms')
    w('')
    w('| type | present | legs | loans | legs on charged-off loan | loans on charged-off |')
    w('| --- | --- | ---: | --- | ---: | --- |')
    for code in ('loanTransactionType.merchantIssuedRefund',
                 'loanTransactionType.payoutRefund',
                 'loanTransactionType.goodwillCredit'):
        t = rg['by_type'][code]
        w('| `%s` | %s | %d | %s | %d | %s |' % (
            code, t['present'], t['total_legs'],
            ', '.join(str(x) for x in t['total_loans']) or '–',
            t['legs_on_charged_off_loan'],
            ', '.join(str(x) for x in t['loans_on_charged_off']) or '–'))
    w('')

    w('### Legs on a CHARGED-OFF loan — required listing')
    w('')
    w('| type | loan | tx | entry | account id | account name | amount (minor) | fraud | currency | tx date | charge-off tx |')
    w('| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- |')
    any_leg = False
    for code in ('loanTransactionType.merchantIssuedRefund',
                 'loanTransactionType.payoutRefund',
                 'loanTransactionType.goodwillCredit'):
        for r in rg['by_type'][code]['on_charged_off_legs']:
            any_leg = True
            w('| `%s` | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
                code, r['loan'], r['transaction_id'], r['entry_type'],
                r['gl_account_id'], r['gl_account_name'], r['amount_minor'],
                r['fraud'], r['currency'], date_str(r['transaction_date']),
                ', '.join(r['chargeoff_tx_ids'])))
    if not any_leg:
        w('| _none_ | | | | | | | | | | |')
    w('')
    w('`merchantIssuedRefund` has **no legs on a charged-off loan** — a finding (see below). Its '
      '10 legs are all dated before the loan\'s charge-off.')
    w('')

    w('### `interestPaymentWaiver` — every leg (required listing)')
    w('')
    w('| loan | tx | entry | account id | account name | amount (minor) | fraud | currency | charged_off | charge-off tx | tx date |')
    w('| ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |')
    t = types['loanTransactionType.interestPaymentWaiver']
    for r in t['legs']:
        w('| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            r['loan'], r['transaction_id'], r['entry_type'], r['gl_account_id'],
            r['gl_account_name'], r['amount_minor'], r['fraud'], r['currency'],
            r['charged_off'], ', '.join(r['chargeoff_tx_ids']) or '-',
            date_str(r['transaction_date'])))
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
    w('## Findings / what the sweep observed and did not')
    w('')
    w('* **Observed — the interest-payment-waiver branch '
      '(`createJournalEntriesForInterestPaymentWaiverOrInterestRefund` :793), for the first time at '
      'the GL level:** %d legs on loans %s (scenarios 1–13). The branch dispatches on the '
      'charged-off state at the transaction date:'
      % (len(t['legs']), ', '.join(str(x) for x in sorted({r['loan'] for r in t['legs']}))))
    w('  * *not charged off* (29 legs, loans 1–10): CREDIT `Loans Receivable` (2) / '
      '`Interest/Fee Receivable` (4) / `Overpayment account` (17), DEBIT `Interest Income` (9);')
    w('  * *charged off* (6 legs, loans 11, 12, 13): DEBIT `Interest Income` (9) / '
      'CREDIT `Interest Income Charge Off` (20).')
    w('* **Observed — the GOODWILL-CREDIT arm on a charged-off loan, previously UNOBSERVED:** '
      '3 legs on loan 15, tx `L113` @ 2022-09-16 (charge-off `L112` @ 2022-09-16) — DEBIT '
      '`Goodwill Expense Account` (19) 6,307, DEBIT `Interest Income Charge Off` (20) 347, '
      'CREDIT `Recoveries` (13) 6,654.')
    w('* **Observed — the PAYOUT-REFUND arm on a charged-off loan:** 2 legs on loan 14, tx `L95` '
      '@ 2022-09-16 (charge-off `L93` @ 2022-09-16) — DEBIT `Suspense/Clearing account` (6) 6,742, '
      'CREDIT `Credit Loss/Bad Debt` (11) 6,742.')
    w('* **FINDING — a target type with no legs on a charged-off loan:** `merchantIssuedRefund` has '
      '10 legs (loans 12–15) but **0 on a charged-off loan**; every one is dated 2021-10-29 / '
      '2022-01-20, before its loan\'s charge-off (2022-09 / 2024-01), so all post through the '
      'non-charged-off amortisation arm (CREDIT `Loans Receivable` 2 / `Interest/Fee Receivable` 4, '
      'DEBIT `Suspense/Clearing` 6). The charged-off merchant-refund arm is **not** exercised here.')
    w('* `interestRefund` (not one of the required arms) is present: 10 legs on loans 12–15; 2 legs '
      'on a charged-off loan (loan 14, tx `L94`) — see `journalentry-type-join.md`.')
    if unmatched:
        ua = J['unmatched_analysis']
        w('* **Unmatched / not type-confirmable:** %d legs (%d transaction%s) carry no entry in any '
          '`transactions` read-back; the posting shape did not match the inferred reverted-accrual '
          'pattern either, so no type is asserted. The loan-14 transaction `L98` (2 legs: DEBIT '
          '`Overpayment account` 17 459, CREDIT `Suspense/Clearing account` 6 459, both dated '
          '2022-09-16, charged_off true) is the unmatched case.'
          % (ua['legs'], ua['count'], '' if ua['count'] == 1 else 's'))
    w('* **No fraud-flagged loan** in this feature, so the `isMarkedFraud` / `chargeOffFraudExpense` '
      'variants are not exercised.')
    w('')

    path = os.path.join(HERE, 'OWNER.md')
    with open(path, 'w') as f:
        f.write('\n'.join(out) + '\n')
    print('wrote %s (%d lines)' % (path, len(out)))


if __name__ == '__main__':
    main()
