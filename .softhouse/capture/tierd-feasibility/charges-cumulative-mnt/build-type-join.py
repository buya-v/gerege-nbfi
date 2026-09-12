#!/usr/bin/env python3
"""OH-TIERD19-CW step 6: join every swept `/journalentries` leg to its loan
transaction TYPE, and to the CHARGED-OFF and FRAUD dimensions, then isolate the
charge-adjustment posting arms of `AccrualBasedAccountingProcessorForLoan.java`
:997-1214 -- `createJournalEntriesForChargeAdjustment`, `...ForLoanChargeAdjustment`,
`...ForChargeOffLoanChargeAdjustment` -- plus every other charge-related
`loanTransactionType` the loan read-backs carry.

Adapted from OH-TIERD17-CR `build-type-join.py` (itself from OH-TIERD12-CE):
the generic sweep leg -> type join, the CHARGED-OFF rule (a NON-REVERSED
`chargeOff` loan transaction dated on or before the leg's transaction date), the
charged-off state from each loan's LATEST read-back, and the FRAUD flag are
unchanged.  The target set is the charge-related `loanTransactionType` codes the
loan read-backs carry.  Each such loan transaction is reported with its read-back
amount and portions (principal / interest / fee / penalty / overpayment /
unrecognized income), and a charge-related transaction with NO journal-entry legs
is reported as a finding.

The sweep is flat (`journalentries-sweep/loan-<id>.json`, one paged body per
loan), unlike the runner's per-transaction `journalentries/`.
"""
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SWEEP = os.path.join(HERE, 'journalentries-sweep')
LOANS = os.path.join(HERE, 'loans')
STAGE = os.path.join(HERE, 'stage')
SEQ_RE = re.compile(r'-(\d+)\.json$')

# The charge-related transaction type codes the read-backs carry.  `chargeAdjustment`
# is the primary target (the OH-TIERD19-CW charge-adjustment posting arms); the rest
# are the remaining charge/refund-family types this feature exercises.
CHARGE_ADJUSTMENT_TYPE = 'loanTransactionType.chargeAdjustment'
CHARGE_RELATED_TYPES = (
    CHARGE_ADJUSTMENT_TYPE,
    'loanTransactionType.waiveCharges',
    'loanTransactionType.chargeback',
    'loanTransactionType.goodwillCredit',
    'loanTransactionType.payoutRefund',
    'loanTransactionType.creditBalanceRefund',
)
TARGET_TYPES = CHARGE_RELATED_TYPES


def minor(amount):
    """Decimal major units -> integer minor units string (2 ISO 4217 digits)."""
    return str(int(round(float(amount) * 100)))


def read_jsons(paths):
    for f in paths:
        try:
            yield f, json.load(open(f))
        except ValueError:
            continue


def tx_readbacks(loan_id):
    """Every transaction read-back for the loan, committed first then stage.

    Both the `transactions` association snapshots and the `all` snapshots carry
    the loan's `transactions` array; a transaction can appear in one and not the
    other (e.g. a `creditBalanceRefund` only in `all`), so read both."""
    pats = [
        os.path.join(LOANS, 'loan-%d' % loan_id,
                     'loan-%d-detail-associations-transactions-*.json' % loan_id),
        os.path.join(LOANS, 'loan-%d' % loan_id,
                     'loan-%d-detail-associations-all-*.json' % loan_id),
        os.path.join(STAGE, 'loan-%d-detail-associations-transactions-*.json' % loan_id),
        os.path.join(STAGE, 'loan-%d-detail-associations-all-*.json' % loan_id),
    ]
    seen = []
    for pat in pats:
        seen.extend(glob.glob(pat))
    return sorted(seen, key=lambda p: int(SEQ_RE.search(p).group(1))
                  if SEQ_RE.search(p) else 0)


def tx_map_for(loan_id):
    """loanTransactionId -> {code, value, date, amount_minor, reversed, portions}.

    Merged over every transaction read-back of the loan; the type of an id is
    stable across reads (asserted)."""
    out = {}
    for f, body in read_jsons(tx_readbacks(loan_id)):
        if not isinstance(body, dict):
            continue
        for t in body.get('transactions') or []:
            tid = t.get('id')
            typ = t.get('type') or {}
            code = typ.get('code')
            if tid is None:
                continue
            prev = out.get(tid)
            if prev and code and prev['code'] and prev['code'] != code:
                raise SystemExit('type instability loan %d tx %s: %s vs %s'
                                 % (loan_id, tid, prev['code'], code))
            out[tid] = {'code': code, 'value': typ.get('value'),
                        'date': t.get('date'),
                        'amount_minor': minor(t.get('amount'))
                        if t.get('amount') is not None else None,
                        # the read-back carries the transaction's portion split;
                        # keep it beside the type so every charge-related leg can be
                        # reported with the transaction's amount and portions.
                        'portions': {
                            'principal_minor': minor(t.get('principalPortion'))
                            if t.get('principalPortion') is not None else None,
                            'interest_minor': minor(t.get('interestPortion'))
                            if t.get('interestPortion') is not None else None,
                            'fee_minor': minor(t.get('feeChargesPortion'))
                            if t.get('feeChargesPortion') is not None else None,
                            'penalty_minor': minor(t.get('penaltyChargesPortion'))
                            if t.get('penaltyChargesPortion') is not None else None,
                            'overpayment_minor': minor(t.get('overpaymentPortion'))
                            if t.get('overpaymentPortion') is not None else None,
                            'unrecognized_income_minor': minor(t.get('unrecognizedIncomePortion'))
                            if t.get('unrecognizedIncomePortion') is not None else None,
                        },
                        # loan read-backs expose `manuallyReversed`; the
                        # journal-entry legs use `reversed`.  Treat either as
                        # reversed, and keep it sticky (once reversed, always).
                        'reversed': (bool(prev.get('reversed')) if prev else False)
                        or bool(t.get('manuallyReversed')) or bool(t.get('reversed'))}
    return out


def chargeoffs_for(loan_id):
    """Non-reversed `chargeOff` transactions: [(date_list, tx_id), ...]."""
    out = []
    for tid, tx in tx_map_for(loan_id).items():
        if tx['code'] == 'loanTransactionType.chargeOff' and not tx['reversed']:
            out.append((tx['date'], tid))
    out.sort(key=lambda p: (p[0] or [], p[1]))
    return out


def loan_fraud(loan_id):
    """Loan-level fraud flag: True if the loan was ever marked fraud."""
    pats = (os.path.join(LOANS, 'loan-%d' % loan_id, 'loan-*-markAsFraud-request.json'),
            os.path.join(STAGE, 'loan-%d-markAsFraud-request.json'))
    for pat in pats:
        for _, body in read_jsons(sorted(glob.glob(pat))):
            if isinstance(body, dict) and body.get('fraud') is True:
                return True
    pats = (os.path.join(LOANS, 'loan-%d' % loan_id, 'loan-*-detail-*.json'),
            os.path.join(STAGE, 'loan-%d-detail-*.json'))
    for pat in pats:
        for _, body in read_jsons(sorted(glob.glob(pat))):
            if isinstance(body, dict) and body.get('fraud') is True:
                return True
    return False


def classify_unmatched(leg_records):
    """Group the legs whose loan transaction is NOT in any read-back and infer
    their type from the posting shape alone (never from a read-back type)."""
    grouped = {}
    for r in leg_records:
        if r['type_code'] is None:
            grouped.setdefault((r['loan'], r['transaction_id']), []).append(r)
    txns = []
    for (lid, label), legs in sorted(grouped.items()):
        amounts = {}
        for l in legs:
            key = (l['entry_type'], l['amount_minor'])
            amounts[key] = amounts.get(key, 0) + 1

        def opposite(e):
            return {'DEBIT': 'CREDIT', 'CREDIT': 'DEBIT'}.get(e, e)
        net_zero = all(amounts.get((opposite(e), a), 0) == c
                       for (e, a), c in amounts.items())
        accts = sorted({l['gl_account_id'] for l in legs})
        shape = 'accrual' if (len(legs) == 4 and net_zero and len(accts) == 2) else 'unknown'
        txns.append({'loan': lid, 'transaction_id': label, 'legs': len(legs),
                     'gl_account_ids': accts, 'net_zero': net_zero,
                     'inferred_type': 'loanTransactionType.' + shape if shape != 'unknown' else None,
                     'legs_detail': legs})
    inferred = sorted({t['inferred_type'] for t in txns if t['inferred_type']})
    return {'count': len(txns), 'legs': sum(t['legs'] for t in txns),
            'inferred_types': inferred, 'reason': (
                'net-zero 4-leg interest accrual + exact reversal; loan transaction '
                'absent from every `transactions` read-back (superseded/reverted by the '
                'accrual-activity replay).  Type inferred from posting shape, NOT confirmed '
                'by read-back.'),
            'transactions': txns}


def detail_currency(loan_id):
    for pat in (os.path.join(LOANS, 'loan-%d' % loan_id, 'loan-*-detail-*.json'),
                os.path.join(STAGE, 'loan-%d-detail-*.json')):
        for _, body in read_jsons(sorted(glob.glob(pat))):
            if isinstance(body, dict) and isinstance(body.get('currency'), dict):
                return body['currency'].get('code')
    return None


def detail_charged_off(loan_id):
    """The loan-level charged-off state from the loan's LATEST read-back.

    A charge-off later undone must not count, so take `chargedOff` from the
    highest-sequence `detail-associations-all-*` read-back; fall back to any
    detail/read-back that carries the field.  Returns None when absent."""
    pats = (os.path.join(LOANS, 'loan-%d' % loan_id,
                         'loan-%d-detail-associations-all-*.json' % loan_id),
            os.path.join(LOANS, 'loan-%d' % loan_id, 'loan-*-detail-*.json'),
            os.path.join(STAGE, 'loan-%d-detail-*.json'))
    for pat in pats:
        files = sorted(glob.glob(pat),
                       key=lambda p: int(SEQ_RE.search(p).group(1))
                       if SEQ_RE.search(p) else 0)
        for f in reversed(files):
            try:
                body = json.load(open(f))
            except ValueError:
                continue
            if isinstance(body, dict) and 'chargedOff' in body:
                return bool(body.get('chargedOff'))
    return None


def build_charge_related(types, loan_chargeoff, currencies, txmaps, chargeoffs):
    """Type x charged-off for each charge-related arm, the required per-leg listing,
    and each charge-related transaction's read-back amount and portions.

    A charge-related transaction with NO journal-entry legs is itself a finding:
    the charge-related arms must post for every such transaction, so an empty leg
    set is reported rather than silently dropped.  A target type with no legs at
    all is a finding too.
    """
    by_type = {}
    all_legs = []
    for code in TARGET_TYPES:
        t = types.get(code)
        legs = list(t['legs']) if t else []
        all_legs.extend(legs)
        on_co = [r for r in legs if r['charged_off']]
        off_co = [r for r in legs if not r['charged_off']]
        by_type[code] = {
            'present': t is not None,
            'total_legs': len(legs),
            'total_transactions': sorted({r['transaction_id'] for r in legs}),
            'total_loans': sorted({r['loan'] for r in legs}),
            'legs_on_charged_off_loan': len(on_co),
            'loans_on_charged_off': sorted({r['loan'] for r in on_co}),
            'legs_on_not_charged_off_loan': len(off_co),
            'loans_on_not_charged_off': sorted({r['loan'] for r in off_co}),
            'on_charged_off_legs': on_co,
            'all_legs': legs,
        }

    # Every charge-related transaction the read-backs expose, with its amount and
    # portions, whether or not the sweep found legs for it.
    bd_transactions = []
    for lid in sorted(txmaps):
        cos = chargeoffs.get(lid, [])
        for tid in sorted(txmaps[lid]):
            tx = txmaps[lid][tid]
            if tx.get('code') not in TARGET_TYPES:
                continue
            tx_date = tx.get('date')
            qualifying = [c for c in cos
                          if c[0] is not None and tx_date is not None and c[0] <= tx_date]
            bd_transactions.append({
                'loan': lid,
                'transaction_id': 'L%d' % tid,
                'transaction_id_num': tid,
                'type_code': tx.get('code'),
                'type_value': tx.get('value'),
                'date': tx_date,
                'amount_minor': tx.get('amount_minor'),
                'reversed': tx.get('reversed'),
                'charged_off': bool(qualifying),
                'charged_off_latest': loan_chargeoff.get(lid, {}).get('charged_off_latest'),
                'chargeoff_tx_ids': ['L%d' % c[1] for c in qualifying],
                'fraud': loan_chargeoff.get(lid, {}).get('fraud', False),
                'currency': currencies.get(lid, 'UNKNOWN'),
                'portions': tx.get('portions'),
                'legs': [],
            })
    bd_by_key = {(t['loan'], t['transaction_id_num']): t for t in bd_transactions}
    for r in all_legs:
        key = (r['loan'], r['transaction_id_num'])
        if key in bd_by_key:
            bd_by_key[key]['legs'].append(r)
    for t in bd_transactions:
        t['legs'].sort(key=lambda r: (0 if r['entry_type'] == 'DEBIT' else 1,
                                      r['gl_account_id'] or 0))
    bd_transactions.sort(key=lambda t: (t['loan'], t['transaction_id_num']))

    empty_types = [c for c in TARGET_TYPES if not by_type[c]['total_legs']]
    no_legs = [t for t in bd_transactions if not t['legs']]
    findings = []
    if empty_types:
        findings.append('charge-related transaction type(s) with NO legs at all: %s.'
                        % ', '.join(empty_types))
    if not bd_transactions:
        findings.append('no charge-related transaction appears in ANY loan read-back '
                        'under `loans/` -- the replay produced none (or its loan was '
                        'not extracted), so the charge-related arms were never exercised.')
    elif no_legs:
        findings.append('%d charge-related transaction(s) in the read-backs have NO '
                        'journal-entry legs: %s.'
                        % (len(no_legs),
                           ', '.join('loan %d tx %s' % (t['loan'], t['transaction_id'])
                                     for t in no_legs)))
    any_chargeoff_tx = any(loan_chargeoff.get(lid, {}).get('chargeoff_transactions')
                           for lid in loan_chargeoff)
    any_latest_co = any(loan_chargeoff.get(lid, {}).get('charged_off_latest')
                        for lid in loan_chargeoff)
    if not any_chargeoff_tx:
        findings.append('no non-reversed `chargeOff` loan transaction appears in ANY '
                        'read-back: no leg is on a charged-off loan, so the '
                        '`...ForChargeOffLoanChargeAdjustment` arm is NOT exercised '
                        'by this feature.')
    if not any_latest_co:
        findings.append('no loan\'s LATEST read-back has `chargedOff=true`: the '
                        'charged-off dimension is empty (every leg charged-off=no).')
    return {
        'charged_off_rule': ('a NON-REVERSED chargeOff loan transaction dated on '
                             'or before the transaction/leg date'),
        'charge_off_coverage': {
            'any_chargeoff_transaction': any_chargeoff_tx,
            'any_latest_charged_off': any_latest_co,
        },
        'target_types': list(TARGET_TYPES),
        'by_type': by_type,
        'currencies': currencies,
        'loans': loan_chargeoff,
        'total_legs': len(all_legs),
        'total_transactions': len(bd_transactions),
        'total_loans': sorted({r['loan'] for r in all_legs}),
        'transactions': bd_transactions,
        'transactions_without_legs': no_legs,
        'empty_types': empty_types,
        'findings': findings,
    }


def date_str(seq):
    if not seq:
        return '-'
    return '%04d-%02d-%02d' % tuple(seq)


def main():
    manifest = json.load(open(os.path.join(HERE, 'journalentries-sweep-manifest.json')))
    loan_ids = sorted(m['loan_id'] for m in manifest)
    txmaps = {lid: tx_map_for(lid) for lid in loan_ids}
    chargeoffs = {lid: chargeoffs_for(lid) for lid in loan_ids}
    frauds = {lid: loan_fraud(lid) for lid in loan_ids}
    latest_co = {lid: detail_charged_off(lid) for lid in loan_ids}

    currencies = {}
    leg_records = []
    unmatched = []
    loan_chargeoff = {}
    for lid in loan_ids:
        path = os.path.join(SWEEP, 'loan-%d.json' % lid)
        if not os.path.exists(path):
            continue
        body = json.load(open(path))
        items = body.get('pageItems') or []
        if not currencies.get(lid):
            cur = next((it.get('currency', {}).get('code') for it in items
                        if it.get('currency')), None)
            currencies[lid] = cur or detail_currency(lid) or 'UNKNOWN'
        cos = chargeoffs.get(lid, [])
        loan_chargeoff[lid] = {
            'fraud': frauds.get(lid, False),
            # state as of each transaction date (non-reversed chargeOff <= date)
            'chargeoff_transactions': [{'transaction_id': 'L%d' % tid,
                                        'date': d} for d, tid in cos],
            # final state from the loan's LATEST read-back (undone charge-off excluded)
            'charged_off_latest': latest_co.get(lid),
        }
        for it in items:
            label = it.get('transactionId')
            n = int(label[1:]) if isinstance(label, str) and label.startswith('L') \
                and label[1:].isdigit() else None
            tx = txmaps.get(lid, {}).get(n)
            if tx is None:
                unmatched.append({'loan': lid, 'transaction_id': label,
                                  'file': 'journalentries-sweep/loan-%d.json' % lid})
            tx_date = tx['date'] if tx else it.get('transactionDate')
            qualifying = [tid for d, tid in cos
                          if d is not None and tx_date is not None and d <= tx_date]
            leg_records.append({
                'loan': lid,
                'currency': it.get('currency', {}).get('code'),
                'journalentries_file': 'journalentries-sweep/loan-%d.json' % lid,
                'transaction_id': label,
                'transaction_id_num': n,
                'type_code': tx['code'] if tx else None,
                'type_value': tx['value'] if tx else None,
                'transaction_date': tx_date,
                'entry_type': (it.get('entryType') or {}).get('value'),
                'gl_account_id': it.get('glAccountId'),
                'gl_account_code': it.get('glAccountCode'),
                'gl_account_name': it.get('glAccountName'),
                'amount_minor': minor(it.get('amount')),
                'reversed': it.get('reversed'),
                'charged_off': bool(qualifying),
                'charged_off_latest': latest_co.get(lid),
                'chargeoff_tx_ids': ['L%d' % tid for tid in qualifying],
                'fraud': frauds.get(lid, False),
            })

    unmatched_analysis = classify_unmatched(leg_records)

    types = {}
    for r in leg_records:
        key = r['type_code'] or '(unmapped)'
        t = types.setdefault(key, {'type_code': r['type_code'],
                                   'type_value': r['type_value'],
                                   'loans': [], 'transactions': [], 'legs': []})
        if r['loan'] not in t['loans']:
            t['loans'].append(r['loan'])
        if r['transaction_id'] not in t['transactions']:
            t['transactions'].append(r['transaction_id'])
        t['legs'].append(r)
    for t in types.values():
        t['loans'].sort()
        t['transactions'].sort(key=lambda s: int(s[1:]) if s and s[1:].isdigit() else 0)
        t['legs'].sort(key=lambda r: (r['loan'], r['transaction_id_num'] or 0))

    bd = build_charge_related(types, loan_chargeoff, currencies, txmaps, chargeoffs)
    obj = {
        'tenant': 'tierd',
        'source': 'GET /journalentries?loanId=<id>&limit=-1 on the throwaway (8444)',
        'loan_ids': loan_ids,
        'currencies': currencies,
        'legs': len(leg_records),
        'unmatched_legs': unmatched,
        'unmatched_analysis': unmatched_analysis,
        'loan_chargeoff': loan_chargeoff,
        'charge_related': bd,
        'types': types,
    }
    with open(os.path.join(HERE, 'journalentry-type-join.json'), 'w') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write('\n')
    write_md(obj)
    write_tsv(obj)
    print('joined %d legs across %d types; %d unmatched; charge-related legs %d on %d '
          'transactions / %d loans; empty types %s'
          % (len(leg_records), len(types), len(unmatched),
             bd['total_legs'], bd['total_transactions'], len(bd['total_loans']),
             ','.join(bd['empty_types']) or 'none'))


def write_md(obj):
    bd = obj['charge_related']
    legs = obj['legs']
    out = []
    w = out.append
    w('# Journal-entry type join — charge-related arms (OH-TIERD19-CW step 6)')
    w('')
    w('%d swept legs across %d transaction types; %d legs unmatched to a read-back.'
      % (legs, len(obj['types']), len(obj['unmatched_legs'])))
    w('')
    w('Charged-off rule: %s.  Fraud per leg = the loan fraud flag.' % bd['charged_off_rule'])
    w('')
    w('## Type × charged-off → legs → loans (every type)')
    w('')
    w('| transaction type | legs | legs on charged-off loan | loans on charged-off |')
    w('| --- | ---: | ---: | --- |')
    for key in sorted(obj['types'], key=lambda k: (-len(obj['types'][k]['legs']), k)):
        t = obj['types'][key]
        onco = [r for r in t['legs'] if r['charged_off']]
        label = '`(unmapped)`' if key == '(unmapped)' else '`%s`' % key
        w('| %s | %d | %d | %s |' % (
            label, len(t['legs']), len(onco),
            ', '.join(str(x) for x in sorted({r['loan'] for r in onco})) or '–'))
    w('')
    w('## Charge-related arms')
    w('')
    w('| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |')
    w('| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |')
    for code in bd['target_types']:
        t = bd['by_type'][code]
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
    w('## Every charge-related leg — required listing')
    w('')
    w('`charged-off at tx date` = a NON-REVERSED chargeOff dated on or before the '
      'leg\'s transaction date.  `charged-off latest` = the loan `chargedOff` flag '
      'in its LATEST read-back, so a charge-off later undone does not count.')
    w('')
    w('| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged-off at tx date | charged-off latest | currency | tx date | charge-off tx |')
    w('| --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |')
    any_leg = False
    for tx in bd['transactions']:
        for r in tx['legs']:
            any_leg = True
            w('| `%s` | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
                r['type_code'], r['loan'], r['transaction_id'], r['entry_type'],
                r['gl_account_id'], r['gl_account_code'], r['gl_account_name'],
                r['amount_minor'], r['fraud'], r['charged_off'],
                r.get('charged_off_latest'), r['currency'],
                date_str(r['transaction_date']),
                ', '.join(r['chargeoff_tx_ids']) or '-'))
    if not any_leg:
        w('| _none_ | | | | | | | | | | | | | |')
    w('')
    w('## Every charge-related transaction and its read-back amount / portions')
    w('')
    w('Portions are integer minor units; `-` means the read-back did not carry that field.')
    w('')
    w('| loan | tx | type | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged-off at date | charged-off latest | fraud | currency | legs |')
    w('| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | ---: |')
    for t in bd['transactions']:
        p = t['portions'] or {}

        def _m(k):
            v = p.get(k)
            return '-' if v is None else v
        w('| %d | %s | `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d |' % (
            t['loan'], t['transaction_id'], t['type_code'], date_str(t['date']),
            t['amount_minor'], _m('principal_minor'), _m('interest_minor'), _m('fee_minor'),
            _m('penalty_minor'), _m('overpayment_minor'), _m('unrecognized_income_minor'),
            t['reversed'], t['charged_off'], t.get('charged_off_latest'),
            t['fraud'], t['currency'], len(t['legs'])))
    if not bd['transactions']:
        w('| _no charge-related transactions_ | | | | | | | | | | | | | | | | |')
    w('')
    w('## Per-loan currency, charge-off and fraud state')
    w('')
    w('| loan | currency | fraud | charged-off latest read-back | non-reversed chargeOff transactions |')
    w('| ---: | --- | --- | --- | --- |')
    for lid in sorted(obj['loan_ids']):
        li = obj['loan_chargeoff'][lid]
        cos = ', '.join('%s@%s' % (c['transaction_id'], date_str(c['date']))
                        for c in li['chargeoff_transactions']) or '-'
        w('| %d | %s | %s | %s | %s |' % (
            lid, obj['currencies'][lid], li['fraud'], li.get('charged_off_latest'), cos))
    w('')
    with open(os.path.join(HERE, 'journalentry-type-join.md'), 'w') as f:
        f.write('\n'.join(out) + '\n')


def write_tsv(obj):
    bd = obj['charge_related']
    cols = ('type_code', 'loan', 'currency', 'transaction_id', 'transaction_date',
            'entry_type', 'gl_account_id', 'gl_account_code', 'gl_account_name',
            'amount_minor', 'fraud', 'charged_off', 'charged_off_latest', 'chargeoff_tx_ids')
    with open(os.path.join(HERE, 'charge-related-legs.tsv'), 'w') as f:
        f.write('\t'.join(cols) + '\n')
        for tx in bd['transactions']:
            for r in tx['legs']:
                row = []
                for c in cols:
                    v = r[c]
                    if c == 'transaction_date':
                        v = date_str(v)
                    elif c == 'chargeoff_tx_ids':
                        v = ','.join(v) or '-'
                    row.append('' if v is None else str(v))
                f.write('\t'.join(row) + '\n')


if __name__ == '__main__':
    main()
