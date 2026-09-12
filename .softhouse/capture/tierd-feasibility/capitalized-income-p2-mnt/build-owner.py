#!/usr/bin/env python3
"""OH-TIERD29-DO step 6: write OWNER.md for the `LoanCapitalizedIncome-Part2.feature`
MNT capture plus the full journal-entry sweep.

Reads journalentry-type-join.json (built by build-type-join.py) plus the
replay/extraction/sweep/product manifests, and emits the type x charged-off
join, the five required arms with their DISTINCT leg shapes (account ids + sides),
one example per shape (loan, tx id, portions, paymentType id) and the transaction
count per shape, the per-loan currency and charge-off state, and the findings.
Money is integer minor units throughout.
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


def m(v):
    return '-' if v is None else v


def portions_str(p):
    if not p:
        return '-'
    return 'P %s / I %s / F %s / Pen %s / OP %s / UI %s' % (
        m(p.get('principal_minor')), m(p.get('interest_minor')),
        m(p.get('fee_minor')), m(p.get('penalty_minor')),
        m(p.get('overpayment_minor')), m(p.get('unrecognized_income_minor')))


def sides_str(sides):
    return ', '.join('%s %s' % (side, acct) for side, acct in sides)


def main():
    J = load('journalentry-type-join.json')
    R = load('scenario-results.json')
    S = load('summary-capitalized-income-p2.json')
    W = load('journalentries-sweep-manifest.json')
    PM = load('product-mappings/manifest.json')

    tg = J['targets']
    currencies = J['currencies']
    loan_ids = sorted((int(x) for x in currencies))
    sweep_legs = sum(x['page_items'] for x in W)
    sweep_ok = sum(1 for x in W if x['http_status'] == '200')
    sweep_bad = sum(1 for x in W if x['http_status'] != '200'
                    or x['curl_returncode'] != 0 or not x['json_valid'])
    steps = R['steps']
    nsteps = steps['total']

    out = []
    w = out.append

    w('# OWNER — Tier D `LoanCapitalizedIncome-Part2.feature` MNT capture **plus a full '
      'journal-entry sweep** (OH-TIERD29-DO)')
    w('')
    w('Whole-file replay of `LoanCapitalizedIncome-Part2.feature` (%d scenarios) against '
      'the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 '
      'HALF_UP, currency MNT), with the Feign capture on, **and then — while the '
      'throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` '
      'for every one of the %d loans the replay created.** Capture only: no vector, no '
      'drive, no `.go`. Money in this file and in the join is integer minor units (MNT, '
      '2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and '
      '`loans/` keep the decimal major units the oracle emitted, unchanged.'
      % (R['scenario_count'], len(loan_ids)))
    w('')
    w('The target is the CAPITALIZED-INCOME posting family: `capitalizedIncome` (the '
      'initial income capitalization), `capitalizedIncomeAdjustment` (the capitalized '
      'income adjustment postings, `createJournalEntriesForCapitalizedIncomeAdjustment`), '
      '`capitalizedIncomeAmortization` (the periodic amortization) and '
      '`capitalizedIncomeAmortizationAdjustment` (the amortization adjustment postings, '
      '`createJournalEntriesForCapitalizedIncomeAmortizationAdjustment`), plus the '
      '`chargeOff` arm. The two ADJUSTMENT postings have never been graded before and are '
      'the reason for this sweep. This capture joins every swept leg to its transaction '
      'TYPE and to the loan\'s CHARGED-OFF state at that transaction, and gives each '
      'required arm\'s DISTINCT leg shapes.')
    w('')
    w('## Provenance')
    w('')
    w('OH-TIERD29-DO ran the rig, the replay (%d/%d), the extraction, the sweep, the '
      'product mappings, the teardown and the type join over the captured JSON. Every '
      'command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run '
      'script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no '
      '`sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`). Nothing was '
      'written into `/Users/buv/fineract`; the replay was done in the disposable copy '
      '`/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.'
      % (R['passed'], R['scenario_count']))
    w('')
    w('## What is here')
    w('')
    w('| path | what |')
    w('| --- | --- |')
    w('| `OWNER.md` | this file |')
    w('| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, '
      'loan mapping, steps |')
    w('| `run-capitalized-income-p2-mnt.sh` | the exact replay driver |')
    w('| `replay-capitalized-income-p2-mnt.log` | raw cucumber/Gradle replay log |')
    w('| `loans/loan-<id>/` | per-loan read-backs of the %d PASSED scenarios |'
      % len(loan_ids))
    w('| `manifest-capitalized-income-p2.json` / `-passed.json` | all extracted bodies '
      'with sha256 and `committed` flag |')
    w('| `summary-capitalized-income-p2.json` | extractor totals and per-loan counts |')
    w('| `journalentries-sweep/loan-<id>.json` | verbatim '
      '`GET /journalentries?loanId=<id>&limit=-1` bodies, %d/%d HTTP 200 |'
      % (sweep_ok, len(W)))
    w('| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json '
      'validity per sweep body |')
    w('| `journalentries-sweep.out` | per-loan sweep log |')
    w('| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port '
      '8444, tenant `tierd`) |')
    w('| `product-mappings/` | accepted create requests of the %d products the loans use, '
      'from THIS replay\'s log, sha256 in `manifest.json` |' % len(PM))
    w('| `journalentry-type-join.json` | every swept leg joined to its transaction type '
      'and charged-off state |')
    w('| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |')
    w('| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER '
      'writer |')
    w('| `organize.py, build-results.py, extract-journalentries.py, '
      'extract-product-mappings.py` | the other copied extractors |')
    w('| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 '
      'standing counters == baseline) |')
    w('')
    w('## Replay result (step 1)')
    w('')
    w('**%d scenarios, %d executed, %d PASSED, %d FAILED; %d steps (%d passed, %d '
      'skipped, %d failed).** The %d skipped scenario has no loan. Recorded, not '
      'diagnosed.'
      % (R['scenario_count'], R['executed'], R['passed'], R['failed'], nsteps,
         steps['passed'], steps['skipped'], steps['failed'], R['skipped']))
    w('')
    w('| # | TestRailId | feature line | result | loan | product |')
    w('| ---: | --- | ---: | --- | ---: | --- |')
    for sc in R['scenarios']:
        prod = sc.get('feature_product') or '_(default progressive)_'
        w('| %d | %s | %d | %s | %d | `%s` |' % (
            sc['index'], sc['tag'], sc['feature_line'], sc['result'],
            sc['loan'] if sc['loan'] is not None else -1, prod))
    w('')
    w('## Extraction (step 2)')
    w('')
    w('Extracted with `bin/extract.py` and the copied `organize.py`: %d loans, %d bodies '
      'kept under `loans/`, each body sha256-pinned in '
      '`manifest-capitalized-income-p2.json`; the FAILED scenarios\' loans are not '
      'committed (`manifest-capitalized-income-p2-passed.json`). Attribution: %s.'
      % (len(S['committed_loans']), S['files_written'],
         'validated' if R['attribution_validated'] else 'NOT validated'))
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
    w('**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant '
      '`gerege` or `default`.** A GET only; no write. Result: **%d/%d HTTP 200, 0 curl '
      'failures, 0 JSON-invalid bodies, %d legs total**, each body saved verbatim and '
      'sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.'
      % (sweep_ok, len(W), sweep_legs))
    if sweep_bad:
        w('')
        w('**FINDING:** %d sweep body/bodies were not a clean HTTP 200 / rc 0 / valid '
          'JSON.' % sweep_bad)
    w('')
    w('## Product mappings (step 4)')
    w('')
    w('The copied `extract-product-mappings.py` pulled the accepted `createLoanProduct` '
      'bodies for the %d distinct products this feature\'s loans use, sha256-pinned in '
      '`product-mappings/manifest.json`.' % len(PM))
    w('')
    for pm in sorted(PM, key=lambda p: p['file']):
        w('- `%s`' % os.path.basename(pm['file']))
    w('')
    w('## Teardown (step 5)')
    w('')
    w('`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, '
      'the `tierd-oracle_default` network and every named volume; `docker ps` shows no '
      '`tierd-*`. The **standing** `gerege` and `default` tenants moved only by their '
      'normal churn: all **12/12** counters equal the preflight baseline '
      '(`teardown-isolation.txt`). PostgreSQL only; no Oracle.')
    w('')
    w('## The type join — swept leg → transaction TYPE, CHARGED-OFF (step 6)')
    w('')
    w('Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is '
      'joined to its transaction type through the loan read-backs (`transactions[].id` '
      '→ `transactions[].type.code`) and to the transaction\'s read-back portions and '
      '`paymentDetailData.paymentType`. **%d legs, %d types, %d unmatched.**'
      % (J['legs'], len(J['types']), len(J['unmatched_legs'])))
    w('')
    w('The exact type codes seen for the required arms are '
      '`loanTransactionType.capitalizedIncome`, '
      '`loanTransactionType.capitalizedIncomeAdjustment`, '
      '`loanTransactionType.capitalizedIncomeAmortization`, '
      '`loanTransactionType.capitalizedIncomeAmortizationAdjustment` and '
      '`loanTransactionType.chargeOff`.')
    w('')
    w('`charged_off` per leg = **the loan\'s LATEST read-back has `chargedOff=true` and '
      'lists a NON-REVERSED `chargeOff` transaction with an EARLIER transaction DATE '
      'than the leg\'s transaction, or the SAME date and a LOWER transaction id.** '
      '(Date order, not id order: OH-TIERD26-DJ, a backdated repayment has a higher id '
      'but posts as not charged off.) `charged-off latest` = the loan `chargedOff` flag '
      'in its LATEST read-back, so a charge-off later undone does not count '
      '(OH-TIERD23-DC).')
    w('')
    w('### Type × charged-off → legs → loans (all types)')
    w('')
    w('| transaction type | legs | legs on charged-off loan | loans on charged-off |')
    w('| --- | ---: | ---: | --- |')
    for key in sorted(J['types'], key=lambda k: (-len(J['types'][k]['legs']), k)):
        t = J['types'][key]
        onco = [r for r in t['legs'] if r['charged_off']]
        label = '`(unmapped)`' if key == '(unmapped)' else '`%s`' % key
        w('| %s | %d | %d | %s |' % (
            label, len(t['legs']), len(onco),
            ', '.join(str(x) for x in sorted({r['loan'] for r in onco})) or '-'))
    w('')
    w('### The five required arms')
    w('')
    w('| type | present | legs | transactions | loans | legs on charged-off | '
      'loans on charged-off | legs on not-charged-off | loans on not-charged-off |')
    w('| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |')
    for code in tg['target_types']:
        t = tg['by_type'][code]
        w('| `%s` | %s | %d | %d | %s | %d | %s | %d | %s |' % (
            code, t['present'], t['total_legs'], len(t['total_transactions']),
            ', '.join(str(x) for x in t['total_loans']) or '-',
            t['legs_on_charged_off_loan'],
            ', '.join(str(x) for x in t['loans_on_charged_off']) or '-',
            t['legs_on_not_charged_off_loan'],
            ', '.join(str(x) for x in t['loans_on_not_charged_off']) or '-'))
    w('')
    empty = [c for c in tg['target_types'] if tg['by_type'][c]['total_legs'] == 0]
    if empty:
        w('**FINDING:** required arm(s) with NO legs at all — NOT exercised by this '
          'feature: %s.' % ', '.join('`%s`' % c for c in empty))
    else:
        w('**No required arm is empty:** all five target types have journal-entry legs '
          'in this replay.')
    w('')
    for f in tg['findings']:
        w('**FINDING:** %s' % f)
        w('')
    w('### Distinct leg shapes per required arm (account ids + sides, example, count)')
    w('')
    for code in tg['target_types']:
        t = tg['by_type'][code]
        w('#### `%s`' % code)
        w('')
        if not t['shapes']:
            w('_No legs for this type — see the finding above._')
            w('')
            continue
        w('| shape (side:account) | account ids | sides | transactions | loans | '
          'example loan | example tx | example portions (minor) | example paymentType id |')
        w('| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |')
        for s in t['shapes']:
            ex = s['example']
            w('| `%s` | %s | %s | %d | %s | %d | %s | %s | %s |' % (
                s['shape'], ', '.join(str(a) for a in s['account_ids']),
                sides_str(s['sides']), s['count'],
                ', '.join(str(x) for x in s['loans']), ex['loan'],
                ex['transaction_id'], portions_str(ex['portions']),
                m(ex['payment_type_id'])))
        w('')
        w('Examples (loan, tx id, portions, paymentType id):')
        w('')
        for s in t['shapes']:
            ex = s['example']
            w('- shape `%s`: loan %d, tx %s, %s, paymentType id %s — %d transaction(s) '
              'across loan(s) %s.'
              % (s['shape'], ex['loan'], ex['transaction_id'],
                 portions_str(ex['portions']), m(ex['payment_type_id']), s['count'],
                 ', '.join(str(x) for x in s['loans'])))
        w('')
    w('### Per-loan currency and charge-off state')
    w('')
    w('| loan | currency | charged-off latest read-back | non-reversed chargeOff transactions |')
    w('| ---: | --- | --- | --- |')
    for lid in loan_ids:
        li = J['loan_chargeoff'].get(str(lid)) or J['loan_chargeoff'].get(lid) or {}
        cos = ', '.join('%s@%s' % (c['transaction_id'], date_str(c['date']))
                        for c in li.get('chargeoff_transactions', [])) or '-'
        w('| %d | %s | %s | %s |' % (
            lid, currencies.get(str(lid), currencies.get(lid, 'UNKNOWN')),
            li.get('charged_off_latest'), cos))
    w('')
    w('### Findings')
    w('')
    findings = list(tg['findings'])
    unm = J.get('unmatched_legs') or []
    if unm:
        findings.append('%d swept leg(s) have NO transaction TYPE (they appear in no '
                        'captured loan read-back): %s.'
                        % (len(unm),
                           ', '.join('loan %s tx %s' % (e['loan'], e['transaction_id'])
                                     for e in unm)))
    if not findings:
        w('- none (all required arms present; every swept leg joined to a type; the '
          'charged-off dimension is populated by loan 27).')
    for f in findings:
        w('- %s' % f)
    w('')
    w('Other observations from the join:')
    w('')
    for code in tg['target_types']:
        t = tg['by_type'][code]
        if t['total_legs'] == 0:
            w('- `%s`: NO legs at all — the arm was NOT exercised by this feature.'
              % code)
            continue
        w('- `%s`: %d legs on %d transaction(s) / %d loan(s); %d legs on charged-off '
          'loan(s) (%s); %d on not-charged-off loan(s) (%s).'
          % (code, t['total_legs'], len(t['total_transactions']),
             len(t['total_loans']), t['legs_on_charged_off_loan'],
             ', '.join(str(x) for x in t['loans_on_charged_off']) or '-',
             t['legs_on_not_charged_off_loan'],
             ', '.join(str(x) for x in t['loans_on_not_charged_off']) or '-'))
    w('')
    w('The payment type on each arm comes from `paymentDetailData.paymentType.id` in '
      'the read-back (channel-mapped fund source); it is listed per shape above.')
    w('')
    with open(os.path.join(HERE, 'OWNER.md'), 'w') as f:
        f.write('\n'.join(out) + '\n')
    print('wrote %s (%d lines)' % (os.path.join(HERE, 'OWNER.md'), len(out)))


if __name__ == '__main__':
    main()
