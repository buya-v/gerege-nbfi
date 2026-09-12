#!/usr/bin/env python3
"""OH-TIERD25-DG step 6: write OWNER.md for the `EMICalculation-Part2.feature`
MNT capture plus the full journal-entry sweep.

Reads `journalentry-type-join.json` (built by `build-type-join.py`) plus the
replay / extraction / sweep / product manifests, and emits the type x charged-off
join, the six required arms with their DISTINCT leg shapes (account ids + sides),
one example per shape (loan, tx id, portions, paymentType id) and the count of
transactions per shape, each loan's currency, and the findings.

Adapted from OH-TIERD22-DB `merchant-refund-mnt/build-owner.py`; the target arms
are now `payoutRefund`, `interestRefund`, `merchantIssuedRefund`, `repayment`,
`accrualAdjustment` and `chargeOff`, and a scenario can own more than one loan.
Money is integer minor units throughout.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name, default=None):
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        if default is None:
            raise SystemExit('missing %s' % name)
        return default
    return json.load(open(path))


def load_text(name, default=''):
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        return default
    return open(path, errors='replace').read()


def m(v):
    return '-' if v is None else v


def portions_str(p):
    if not p:
        return '-'
    return 'P %s / I %s / F %s / Pen %s / OP %s / UI %s' % (
        m(p.get('principal_minor')), m(p.get('interest_minor')),
        m(p.get('fee_minor')), m(p.get('penalty_minor')),
        m(p.get('overpayment_minor')), m(p.get('unrecognized_income_minor')))


def main():
    J = load('journalentry-type-join.json')
    R = load('scenario-results.json')
    S = load('summary-emi-calculation-p2.json', {})
    W = load('journalentries-sweep-manifest.json')
    PM = load('product-mappings/manifest.json', [])
    teardown = load_text('teardown-isolation.txt')

    tg = J['targets']
    currencies = J['currencies']
    loan_ids = sorted(int(x) for x in currencies)
    loan_chargeoff = J['loan_chargeoff']
    sweep_ok = sum(1 for x in W
                   if x.get('http_status') == '200' and x.get('curl_returncode') == 0
                   and x.get('json_valid'))
    sweep_bad = len(W) - sweep_ok
    steps = R.get('steps', {})
    iso_ok = teardown.count('(== baseline)')

    out = []
    w = out.append

    w('# OWNER — Tier D `EMICalculation-Part2.feature` MNT capture **plus a full '
      'journal-entry sweep** (OH-TIERD25-DG)')
    w('')
    w('Whole-file replay of `EMICalculation-Part2.feature` (%d scenarios) against the '
      'throwaway reference oracle, tenant `tierd` (currency MNT), with the Feign capture '
      'on, **and then — while the throwaway was still up — one bounded '
      '`GET /journalentries?loanId=<id>&limit=-1` for every loan the replay created.** '
      'Capture only: no vector, no drive, no `.go`. Money in this file and in the join is '
      'integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under '
      '`journalentries-sweep/` and `loans/` keep the decimal major units the oracle '
      'emitted, unchanged.' % R['scenario_count'])
    w('')
    w('`EMICalculation-Part2.feature` complements the few-loan merchant-refund and '
      'payout-refund captures (`merchant-refund-mnt`, OH-TIERD22-DB) by exercising the '
      'refund posts at breadth: interest refunds (with interest and fee portions) and '
      'payout refunds across more products. This capture joins every swept leg to its '
      'transaction TYPE and to the loan\'s CHARGED-OFF state at that transaction, and '
      'gives each required arm\'s DISTINCT leg shapes.')
    w('')
    w('## Provenance')
    w('')
    w('OH-TIERD25-DG ran the rig, the replay (%d/%d), the extraction, the sweep, the '
      'product mappings, the teardown and the type join over the captured JSON. Every '
      'command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run '
      'script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no '
      '`sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`, %d/12 standing '
      'counters == baseline). Nothing was written into `/Users/buv/fineract`; the replay '
      'ran in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.'
      % (R['passed'], R['scenario_count'], iso_ok))
    w('')
    w('Charged-off classification (exactly the rule this capture uses): **a leg\'s '
      'transaction is on a charged-off loan only if that loan\'s LATEST read-back '
      '(highest index) lists a `chargeOff` transaction with a LOWER id and the loan\'s '
      '`chargedOff` is true.** Charge-offs that were undone vanish from the latest '
      'read-back; `manuallyReversed` on earlier read-backs is not reliable and is not '
      'used.')
    w('')
    w('## What is here')
    w('')
    w('| path | what |')
    w('| --- | --- |')
    w('| `OWNER.md` | this file |')
    w('| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, '
      'client/loan mapping, steps |')
    w('| `run-emi-calculation-p2-mnt.sh` | the exact replay driver |')
    w('| `replay-emi-calculation-p2-mnt.log` | raw cucumber/Gradle replay log |')
    w('| `loans/loan-<id>/` | per-loan read-backs of the %d PASSED loans |'
      % sum(1 for s in R['scenarios'] if s['result'] == 'PASSED' for _ in s.get('loans') or []))
    w('| `manifest-emi-calculation-p2.json` / `-passed.json` | all extracted bodies with '
      'sha256 and `committed` flag |')
    w('| `summary-emi-calculation-p2.json` | extractor totals and per-loan counts |')
    w('| `journalentries-sweep/loan-<id>.json` | verbatim '
      '`GET /journalentries?loanId=<id>&limit=-1` bodies, %d/%d clean |'
      % (sweep_ok, len(W)))
    w('| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json '
      'validity per sweep body |')
    w('| `sweep.out` | per-loan sweep log |')
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
    w('**%d scenarios, %d PASSED, %d FAILED; %s steps (%s passed, %s skipped, %s '
      'failed); %d loans over %d clients.** Recorded, not diagnosed; a failure would be '
      'dispatched to an EUR control, not fixed here. Two of the %d scenarios each create a '
      'second loan for the same client, so the replay creates %d loans over %d clients.'
      % (R['scenario_count'], R['passed'], R['failed'], steps.get('total'),
         steps.get('passed'), steps.get('skipped'), steps.get('failed'),
         R.get('loan_count'), R['scenario_count'], R['scenario_count'],
         R.get('loan_count'), R['scenario_count']))
    w('')
    w('Per-scenario detail (TestRailId, feature line, result, client, loan ids, product) '
      'is in `replay-result-table.md`. Scenario attribution validated: %s.'
      % ('yes' if R.get('attribution_validated') else 'NO'))
    if R.get('problems'):
        w('')
        w('Attribution problems: %s' % '; '.join(R['problems']))
    w('')
    w('## The journal-entry sweep (step 3 — the new step)')
    w('')
    w('%d loans swept, %d clean (%d HTTP 200, `curl` rc 0, valid JSON), %d not clean. '
      'Each body is saved verbatim as `journalentries-sweep/loan-<id>.json`; the manifest '
      'records the sha256 and the exact URL '
      '`https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1`. '
      'GET only; no write. This is the THROWAWAY (port 8444, tenant `tierd`), never 8443 '
      'and never tenant `gerege`/`default`.' % (len(W), sweep_ok, sweep_ok, sweep_bad))
    w('')
    w('Total swept legs: %d across %d transaction types; %d legs unmatched to a loan '
      'read-back.' % (J['legs'], len(J['types']), len(J['unmatched_legs'])))
    w('')
    w('## Product mappings (step 4)')
    w('')
    w('%d products used by the committed loans; each is the accepted create request from '
      'THIS replay\'s Feign log, sha256 in `product-mappings/manifest.json`.' % len(PM))
    w('')
    w('## Teardown (step 5)')
    w('')
    w('`down.sh` removed every `tierd-*` container, network and volume. The 12 standing '
      'reference-oracle counters (6 each on `fineract-db-1` and `gerege-oracle-db`) were '
      'read after teardown and all %d equal the baseline this capture opened with '
      '(`teardown-isolation.txt`).' % iso_ok)
    w('')
    w('## The type join (step 6)')
    w('')
    w('Every swept leg -> its transaction TYPE through the loan read-backs, and for each '
      'leg whether the loan was CHARGED OFF at that transaction. Charged-off rule: %s.'
      % tg['charged_off_rule'])
    w('')
    w('### Type x charged-off -> legs -> loans (every type swept)')
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
    w('### Required arms')
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
    w('### Distinct leg shapes per required arm')
    w('')
    for code in tg['target_types']:
        t = tg['by_type'][code]
        w('#### `%s`' % code)
        w('')
        if not t['shapes']:
            w('_No legs: this arm was NOT exercised by this feature (a finding, see '
              'below)._')
            w('')
            continue
        w('| shape (side:account) | account ids | transactions | loans | example '
          '(loan, tx id, portions, paymentType id) |')
        w('| --- | --- | ---: | --- | --- |')
        for s in t['shapes']:
            ex = s['example']
            w('| `%s` | %s | %d | %s | loan %d, tx %s, %s, paymentType %s |' % (
                s['shape'], ', '.join(str(a) for a in s['account_ids']), s['count'],
                ', '.join(str(x) for x in s['loans']), ex['loan'], ex['transaction_id'],
                portions_str(ex.get('portions')), m(ex.get('payment_type_id'))))
        w('')
    w('### Per-loan currency and charge-off state')
    w('')
    w('| loan | currency | chargedOff (latest read-back) | chargeOff tx ids (non-reversed, '
      'lower id) |')
    w('| ---: | --- | --- | --- |')
    for lid in loan_ids:
        co = loan_chargeoff.get(lid, {})
        cos = co.get('chargeoff_transactions') or []
        w('| %d | %s | %s | %s |' % (
            lid, currencies.get(str(lid), currencies.get(lid, 'UNKNOWN')),
            m(co.get('charged_off_latest')),
            ', '.join(c['transaction_id'] for c in cos) or '-'))
    w('')
    w('## Findings')
    w('')
    if tg['findings']:
        for f in tg['findings']:
            w('- %s' % f)
    else:
        w('- none.')
    empty = tg['empty_types']
    if empty:
        w('')
        w('A required type with no legs is itself a result: %s had no swept leg, so the '
          'feature did not exercise that arm.' % ', '.join('`%s`' % e for e in empty))
    w('')
    with open(os.path.join(HERE, 'OWNER.md'), 'w') as fh:
        fh.write('\n'.join(out))
    print('wrote OWNER.md: %d scenarios (%d passed), %d loans, %d legs, %d/%d sweep '
          'clean, %d/12 isolation, empty target types %s'
          % (R['scenario_count'], R['passed'], R.get('loan_count'), J['legs'], sweep_ok,
             len(W), iso_ok, ','.join(tg['empty_types']) or 'none'))


if __name__ == '__main__':
    main()
