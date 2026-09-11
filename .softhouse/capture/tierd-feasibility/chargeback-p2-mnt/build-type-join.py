#!/usr/bin/env python3
"""OH-TIERD15-CM step 6: join every swept `/journalentries` leg to its loan
transaction TYPE, and to the CHARGED-OFF and FRAUD dimensions, then isolate the
`chargeback` arm of `createJournalEntriesForChargeback`
[AccrualBasedAccountingProcessorForLoan.java:1215-1308] and each chargeback
transaction's read-back PORTIONS (principal / interest / fee / penalty /
overpayment / unrecognized income).

Adapted from OH-TIERD12-CE / OH-TIERD13-CI `build-type-join.py`: the generic sweep
leg -> type join, the CHARGED-OFF rule (a NON-REVERSED `chargeOff` loan transaction
dated on or before the leg's transaction date) and the FRAUD flag are unchanged.
The refund/goodwill target set is replaced by `loanTransactionType.chargeback`, the
loan read-backs now also carry the portion split, and a chargeback transaction that
appears in the read-backs but has NO journal-entry legs is reported as a finding.

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
    """Every transaction read-back for the loan, committed first then stage."""
    pats = [
        os.path.join(LOANS, 'loan-%d' % loan_id,
                     'loan-%d-detail-associations-transactions-*.json' % loan_id),
        os.path.join(STAGE, 'loan-%d-detail-associations-transactions-*.json' % loan_id),
    ]
    seen = []
    for pat in pats:
        seen.extend(glob.glob(pat))
    return sorted(seen, key=lambda p: int(SEQ_RE.search(p).group(1))
                  if SEQ_RE.search(p) else 0)


def tx_map_for(loan_id):
    """loanTransactionId -> {code, value, date, amount_minor, reversed}.

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
                        # OH-TIERD15-CM: the read-back carries the chargeback's
                        # portion split; keep it beside the type so the sweep legs
                        # can be reported with their principal/fee/penalty split.
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
    """Loan-level fraud flag: True if the loan was ever marked fraud.

    Observable as a `markAsFraud` request/read-back (`fraud: true`) under the
    loan's capture directory; falls back to any read-back carrying
    `fraud: true` at the top level.
    """
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
    their type from the posting shape alone (never from a read-back type).

    Observed shape: a net-zero 4-leg pair -- an interest accrual
    (DEBIT Interest/Fee Receivable / CREDIT Interest Income) followed by its
    exact reversal (CREDIT receivable / DEBIT income) -- i.e. a *reverted*
    accrual.  These are the original accrual transactions that the
    accrual-activity replay superseded and the `transactions` association no
    longer returns.  The label is INFERRED; the read-backs cannot confirm it.
    """
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


def main():
    manifest = json.load(open(os.path.join(HERE, 'journalentries-sweep-manifest.json')))
    loan_ids = sorted(m['loan_id'] for m in manifest)
    txmaps = {lid: tx_map_for(lid) for lid in loan_ids}
    chargeoffs = {lid: chargeoffs_for(lid) for lid in loan_ids}
    frauds = {lid: loan_fraud(lid) for lid in loan_ids}

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
            'chargeoff_transactions': [{'transaction_id': 'L%d' % tid,
                                        'date': d} for d, tid in cos],
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

    cb = build_chargeback(types, loan_chargeoff, currencies, txmaps, chargeoffs)
    paid_gt_credited = analyze_paid_gt_credited(cb['transactions'])
    portion_arms = analyze_portions(cb['transactions'])
    obj = {
        'tenant': 'tierd',
        'source': 'GET /journalentries?loanId=<id>&limit=-1 on the throwaway (8444)',
        'loan_ids': loan_ids,
        'currencies': currencies,
        'legs': len(leg_records),
        'unmatched_legs': unmatched,
        'unmatched_analysis': unmatched_analysis,
        'loan_chargeoff': loan_chargeoff,
        'chargeback': cb,
        'paid_gt_credited': paid_gt_credited,
        'portion_arms': portion_arms,
        'types': types,
    }
    with open(os.path.join(HERE, 'journalentry-type-join.json'), 'w') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write('\n')
    write_md(obj)
    write_accrual_tsv(obj)
    write_chargeback_tsv(obj)
    accrual = sorted(k for k in types if 'accrual' in k.lower())
    print('joined %d legs across %d types; %d unmatched (%d inferred %s); accrual types %s; '
          'chargeback legs %d on %d loans'
          % (len(leg_records), len(types), len(unmatched),
             unmatched_analysis['count'],
             ','.join(unmatched_analysis['inferred_types']) or '?', accrual,
             cb['total_legs'], len(cb['total_loans'])))


TARGET_TYPES = ('loanTransactionType.chargeback',)


def build_chargeback(types, loan_chargeoff, currencies, txmaps, chargeoffs):
    """Type x charged-off for the chargeback arm, the required per-leg listing, and
    each chargeback transaction's read-back portions.

    A chargeback transaction with NO journal-entry legs is itself a finding:
    `createJournalEntriesForChargeback` must post for every chargeback, so an empty
    leg set is reported rather than silently dropped.
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

    # Every chargeback transaction the read-backs expose, with its portion split,
    # whether or not the sweep found legs for it.
    cb_transactions = []
    for lid in sorted(txmaps):
        cos = chargeoffs.get(lid, [])
        for tid in sorted(txmaps[lid]):
            tx = txmaps[lid][tid]
            if tx.get('code') not in TARGET_TYPES:
                continue
            tx_date = tx.get('date')
            qualifying = [c for c in cos
                          if c[0] is not None and tx_date is not None and c[0] <= tx_date]
            cb_transactions.append({
                'loan': lid,
                'transaction_id': 'L%d' % tid,
                'transaction_id_num': tid,
                'date': tx_date,
                'amount_minor': tx.get('amount_minor'),
                'reversed': tx.get('reversed'),
                'charged_off': bool(qualifying),
                'chargeoff_tx_ids': ['L%d' % c[1] for c in qualifying],
                'fraud': loan_chargeoff.get(lid, {}).get('fraud', False),
                'currency': currencies.get(lid, 'UNKNOWN'),
                'portions': tx.get('portions'),
                'legs': [],
            })
    cb_by_key = {(t['loan'], t['transaction_id_num']): t for t in cb_transactions}
    for r in all_legs:
        key = (r['loan'], r['transaction_id_num'])
        if key in cb_by_key:
            cb_by_key[key]['legs'].append(r)
    for t in cb_transactions:
        t['legs'].sort(key=lambda r: (0 if r['entry_type'] == 'DEBIT' else 1,
                                      r['gl_account_id'] or 0))
    cb_transactions.sort(key=lambda t: (t['loan'], t['transaction_id_num']))
    no_legs = [t for t in cb_transactions if not t['legs']]
    if not cb_transactions:
        finding = ('no chargeback transaction appears in ANY loan read-back under '
                   '`loans/` -- the replay produced no chargeback (or its loan was not '
                   'extracted); `createJournalEntriesForChargeback` was never exercised.')
    elif no_legs:
        finding = ('%d chargeback transaction(s) in the read-backs have NO journal-entry '
                   'legs: %s.' % (len(no_legs),
                                  ', '.join('loan %d tx %s' % (t['loan'], t['transaction_id'])
                                            for t in no_legs)))
    else:
        finding = None
    return {
        'charged_off_rule': ('a NON-REVERSED chargeOff loan transaction dated on '
                             'or before the transaction/leg date'),
        'target_types': list(TARGET_TYPES),
        'by_type': by_type,
        'currencies': currencies,
        'loans': loan_chargeoff,
        'total_legs': len(all_legs),
        'total_transactions': len(cb_transactions),
        'total_loans': sorted({r['loan'] for r in all_legs}),
        'transactions': cb_transactions,
        'transactions_without_legs': no_legs,
        'no_legs_finding': finding,
    }


# `createJournalEntriesForChargeback` credits the fund source with `amount` before the
# principal / fee / penalty comparisons [AccrualBasedAccountingProcessorForLoan.java:1241-1273].
FUND_SOURCE_NAMES = ('Suspense/Clearing account',)


def analyze_paid_gt_credited(cb_transactions):
    """The `credited < paid` arm of `createJournalEntriesForChargeback`
    [AccrualBasedAccountingProcessorForLoan.java:1251-1273].

    When `principalCredited < principalPaid` (and the fee / penalty analogues), the
    processor CREDITs `getPrincipalAccount` / `getFeeAccount` / `getPenaltyAccount` with
    the small difference.  On a charged-off loan those resolve to the charge-off
    expense / charge-off income accounts.  The normal `credited > paid` arm DEBITs the
    same accounts, and the fund source (Suspense/Clearing) is CREDITed with `amount`;
    the overpayment account is only ever DEBITed.  So a candidate is any chargeback
    CREDIT leg whose account is not the fund source.

    A candidate that has a DEBIT leg with the SAME account and amount under the SAME
    `transactionId` is self-offsetting: a chargeback reversal/replay posts the exact
    opposite under the original id (neither marked `reversed` in the read-back), so it
    is NOT a `credited < paid` difference posting.  Only candidate legs with no such
    matching debit are genuine `paid > credited` legs.
    """
    candidates = []
    genuine = []
    self_offsetting = []
    for tx in cb_transactions:
        legs = tx['legs']
        for r in legs:
            if r['entry_type'] != 'CREDIT' or (r['gl_account_name'] or '') in FUND_SOURCE_NAMES:
                continue
            matching = any(d['entry_type'] == 'DEBIT'
                           and d['gl_account_id'] == r['gl_account_id']
                           and d['amount_minor'] == r['amount_minor']
                           for d in legs)
            rec = {
                'loan': tx['loan'], 'transaction_id': tx['transaction_id'],
                'account_id': r['gl_account_id'], 'account_code': r['gl_account_code'],
                'account_name': r['gl_account_name'], 'amount_minor': r['amount_minor'],
                'charged_off': r['charged_off'], 'fraud': r['fraud'],
                'currency': r['currency'], 'self_offsetting': matching,
            }
            candidates.append(rec)
            (self_offsetting if matching else genuine).append(rec)
    if genuine:
        finding = ('OBSERVED: %d genuine `paid > credited` leg(s) -- a CREDIT to a '
                   'principal/fee/penalty account with no matching debit under the same '
                   'transactionId.' % len(genuine))
    elif candidates:
        pairs = []
        for c in candidates:
            p = (c['loan'], c['transaction_id'])
            if p not in pairs:
                pairs.append(p)
        finding = ('FINDING -- no genuine `paid > credited` leg: the only CREDIT(s) to a '
                   'principal/fee/penalty account (%d leg(s) on %s) each have an equal '
                   'DEBIT under the same transactionId, i.e. a chargeback reversal/replay '
                   'pair, not the `credited < paid` difference posting.  The `paid > '
                   'credited` arm is NOT exercised in this replay.'
                   % (len(candidates),
                      ', '.join('loan %d tx %s' % (l, t) for l, t in pairs)))
    else:
        finding = ('FINDING -- no `paid > credited` leg at all: no chargeback CREDIT to a '
                   'principal/fee/penalty account appears in the sweep.')
    return {
        'rule': ('credited < paid -> CREDIT getPrincipalAccount/getFeeAccount/'
                 'getPenaltyAccount [AccrualBasedAccountingProcessorForLoan.java:1251-1273]'),
        'fund_source_account_names': list(FUND_SOURCE_NAMES),
        'candidates': candidates,
        'self_offsetting': self_offsetting,
        'genuine_paid_gt_credited': genuine,
        'finding': finding,
    }


def analyze_portions(cb_transactions):
    """FEE / PENALTY / overpayment / interest / unrecognized-income portion arms.

    Reports which read-back portion fields are non-zero on any chargeback transaction,
    with the loans and transactions that carry each, so the capture states explicitly
    whether `FEE` and `PENALTY` chargeback portions were exercised."""
    arms = {'principal': [], 'interest': [], 'fee': [], 'penalty': [],
            'overpayment': [], 'unrecognized_income': []}
    keymap = {'principal': 'principal_minor', 'interest': 'interest_minor',
              'fee': 'fee_minor', 'penalty': 'penalty_minor',
              'overpayment': 'overpayment_minor',
              'unrecognized_income': 'unrecognized_income_minor'}
    for t in cb_transactions:
        p = t['portions'] or {}
        for arm, key in keymap.items():
            v = p.get(key)
            if v is None:
                continue
            try:
                nonzero = int(v) != 0
            except (TypeError, ValueError):
                nonzero = False
            if nonzero:
                arms[arm].append({'loan': t['loan'], 'transaction_id': t['transaction_id'],
                                  'amount_minor': v})
    return arms


def write_chargeback_tsv(obj):
    """Flat listing of every chargeback leg (the required columns)."""
    cols = ['type', 'loan', 'tx', 'entry', 'gl_account_id', 'gl_account_code',
            'gl_account_name', 'amount_minor', 'fraud', 'charged_off', 'currency',
            'transaction_date', 'chargeoff_tx_id']
    rows = []
    for tx in obj['chargeback']['transactions']:
        for r in tx['legs']:
            rows.append([r['type_code'] or 'loanTransactionType.chargeback',
                         str(r['loan']), r['transaction_id'], r['entry_type'],
                         str(r['gl_account_id']), str(r['gl_account_code']),
                         r['gl_account_name'], str(r['amount_minor']), str(r['fraud']),
                         str(r['charged_off']), r['currency'],
                         '-'.join('%02d' % x for x in (r['transaction_date'] or [])),
                         ','.join(r['chargeoff_tx_ids'])])
    rows.sort(key=lambda x: (int(x[1]), int(x[2][1:]), 0 if x[3] == 'DEBIT' else 1))
    with open(os.path.join(HERE, 'chargeback-legs.tsv'), 'w') as fh:
        fh.write('\t'.join(cols) + '\n')
        for r in rows:
            fh.write('\t'.join(r) + '\n')


def write_accrual_tsv(obj):
    """Flat listing of every ACCRUAL-type leg (the capture's target) plus the
    inferred reverted-accrual legs, in the OWNER-required columns."""
    cols = ['loan', 'tx', 'type', 'inferred', 'entry', 'gl_account_id',
            'gl_account_code', 'gl_account_name', 'amount_minor', 'currency']
    rows = []

    def add(r, typ, inferred):
        # `typ` is None when an unmatched transaction's posting shape did not
        # match the inferred-reverted-accrual pattern; keep the row, label it.
        rows.append([str(r['loan']), r['transaction_id'], typ or 'unknown', str(inferred),
                     r['entry_type'], str(r['gl_account_id']), str(r['gl_account_code']),
                     r['gl_account_name'], str(r['amount_minor']), r['currency']])

    for key, t in obj['types'].items():
        if 'accrual' in (key or '').lower():
            for r in t['legs']:
                add(r, key, False)
    for t in (obj.get('unmatched_analysis') or {}).get('transactions', []):
        for r in t['legs_detail']:
            add(r, t['inferred_type'], True)
    rows.sort(key=lambda x: (int(x[0]), int(x[1][1:]), 0 if x[4] == 'DEBIT' else 1))
    with open(os.path.join(HERE, 'accrual-legs.tsv'), 'w') as fh:
        fh.write('\t'.join(cols) + '\n')
        for r in rows:
            fh.write('\t'.join(r) + '\n')


def write_chargeback_md(obj, w):
    """Type x charged-off summary, the every-leg listing, and each chargeback
    transaction's portions (OWNER step 6)."""
    cb = obj['chargeback']
    w('## Type x charged-off -- the `chargeback` arm (OH-TIERD15-CM step 6)')
    w('')
    w('Charged-off rule: %s.' % cb['charged_off_rule'])
    w('')
    w('| type | present | legs | transactions | loans | legs on charged-off loan | loans on charged-off | legs on not-charged-off | loans on not-charged-off |')
    w('| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |')
    for code in cb['target_types']:
        t = cb['by_type'][code]
        w('| `%s` | %s | %d | %d | %s | %d | %s | %d | %s |' % (
            code, t['present'], t['total_legs'], len(t['total_transactions']),
            ', '.join(str(x) for x in t['total_loans']) or '-',
            t['legs_on_charged_off_loan'],
            ', '.join(str(x) for x in t['loans_on_charged_off']) or '-',
            t['legs_on_not_charged_off_loan'],
            ', '.join(str(x) for x in t['loans_on_not_charged_off']) or '-'))
    w('')
    if cb['no_legs_finding']:
        w('**FINDING:** %s' % cb['no_legs_finding'])
        w('')
    w('### Every `chargeback` leg -- required listing')
    w('')
    w('| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged_off | currency |')
    w('| --- | --- | --- | --- | ---: | --- | --- | ---: | --- | --- | --- |')
    any_leg = False
    for tx in cb['transactions']:
        for r in tx['legs']:
            any_leg = True
            w('| `%s` | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
                r['type_code'] or 'loanTransactionType.chargeback', r['loan'],
                r['transaction_id'], r['entry_type'], r['gl_account_id'],
                r['gl_account_code'], r['gl_account_name'], r['amount_minor'],
                r['fraud'], r['charged_off'], r['currency']))
    if not any_leg:
        w('| _none_ | | | | | | | | | | |')
    w('')
    w('### Every chargeback loan transaction and its read-back portions')
    w('')
    w('Portions are integer minor units; `-` means the read-back did not carry that field.')
    w('')
    w('| loan | tx | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged_off | fraud | currency | legs |')
    w('| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: |')
    for t in cb['transactions']:
        p = t['portions'] or {}

        def _m(k):
            v = p.get(k)
            return '-' if v is None else v
        w('| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d |' % (
            t['loan'], t['transaction_id'],
            '-'.join('%02d' % x for x in (t['date'] or [])) or '-',
            t['amount_minor'], _m('principal_minor'), _m('interest_minor'), _m('fee_minor'),
            _m('penalty_minor'), _m('overpayment_minor'), _m('unrecognized_income_minor'),
            t['reversed'], t['charged_off'], t['fraud'], t['currency'], len(t['legs'])))
    if not cb['transactions']:
        w('| _no chargeback transactions_ | | | | | | | | | | | | | | |')
    w('')
    pgc = obj['paid_gt_credited']
    arms = obj['portion_arms']
    w('### Chargeback portion arms and the `paid > credited` branch')
    w('')
    w('Portion arms observed non-zero on a chargeback transaction (integer minor units):')
    w('')
    w('| portion arm | observed? | count | loans | transactions |')
    w('| --- | --- | ---: | --- | --- |')
    for arm in ('principal', 'interest', 'fee', 'penalty', 'overpayment', 'unrecognized_income'):
        hits = arms[arm]
        w('| %s | %s | %d | %s | %s |' % (
            arm, bool(hits), len(hits),
            ', '.join(str(x) for x in sorted({h['loan'] for h in hits})) or '-',
            ', '.join(h['transaction_id'] for h in hits) or '-'))
    w('')
    w('**FEE portions observed: %s. PENALTY portions observed: %s.**' % (
        bool(arms['fee']), bool(arms['penalty'])))
    w('')
    w('`paid > credited` rule: %s.' % pgc['rule'])
    w('')
    if pgc['genuine_paid_gt_credited']:
        w('Genuine `paid > credited` legs:')
        w('')
        w('| loan | tx | entry | account id | account code | account name | amount (minor) | charged_off | fraud | currency |')
        w('| ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- |')
        for c in pgc['genuine_paid_gt_credited']:
            w('| %d | %s | CREDIT | %s | %s | %s | %s | %s | %s | %s |' % (
                c['loan'], c['transaction_id'], c['account_id'], c['account_code'],
                c['account_name'], c['amount_minor'], c['charged_off'], c['fraud'], c['currency']))
        w('')
    if pgc['self_offsetting']:
        w('Self-offsetting CREDIT legs (equal DEBIT under the same `transactionId` -- '
          'chargeback reversal/replay, NOT a `credited < paid` difference posting):')
        w('')
        w('| loan | tx | entry | account id | account code | account name | amount (minor) | charged_off | currency |')
        w('| ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |')
        for c in pgc['self_offsetting']:
            w('| %d | %s | CREDIT | %s | %s | %s | %s | %s | %s |' % (
                c['loan'], c['transaction_id'], c['account_id'], c['account_code'],
                c['account_name'], c['amount_minor'], c['charged_off'], c['currency']))
        w('')
    w('**%s**' % pgc['finding'])
    w('')
    w('### Per-loan charge-off / fraud / currency state')
    w('')
    w('| loan | currency | fraud | non-reversed chargeOff transactions |')
    w('| --- | --- | --- | --- |')
    for lid in sorted(cb['loans']):
        li = cb['loans'][lid]
        cos = ', '.join('%s@%s' % (c['transaction_id'],
                                   '-'.join('%02d' % x for x in (c['date'] or [])))
                        for c in li['chargeoff_transactions']) or '-'
        w('| %d | %s | %s | %s |' % (
            lid, cb['currencies'].get(lid, 'UNKNOWN'), li['fraud'], cos))
    w('')

def write_md(obj):
    out = []
    w = out.append
    w('# Journal-entry leg -> loan transaction TYPE join (sweep)')
    w('')
    w('Every swept `/journalentries` leg carries only `transactionId` =')
    w('`L<loanTransactionId>`; the transaction **type** comes only from the loan')
    w('read-backs (`transactions[].id -> transactions[].type.code`).  Amounts are')
    w('integer minor units; the raw sweep bodies keep decimal major units.')
    w('')
    w('Legs joined: %d; unmatched by read-back: %d.' % (obj['legs'], len(obj['unmatched_legs'])))
    ua = obj.get('unmatched_analysis') or {}
    if ua.get('count'):
        w('')
        w('**%d unmatched legs (%d transactions, loans %s)** carry no type in the read-backs;'
          % (ua['legs'], ua['count'],
             ', '.join(str(t['loan']) for t in ua['transactions'])))
        w('their posting shape infers `%s` (see the section at the end).'
          % (', '.join(ua['inferred_types']) or 'unknown'))
    w('')
    w('| type | value | loans | transactions | legs |')
    w('| --- | --- | --- | --- | --- |')
    for key in sorted(obj['types'], key=lambda k: (k == '(unmapped)', k)):
        t = obj['types'][key]
        w('| `%s` | %s | %s | %s | %d |' % (
            t['type_code'], t['type_value'] or '',
            ', '.join(str(x) for x in t['loans']),
            ', '.join(t['transactions']), len(t['legs'])))
    w('')
    for key in sorted(obj['types'], key=lambda k: (k == '(unmapped)', k)):
        t = obj['types'][key]
        w('## `%s`%s' % (t['type_code'], '' if not t['type_value']
                         else ' — %s' % t['type_value']))
        w('')
        w('loans: %s; transactions: %s; legs: %d'
          % (', '.join(str(x) for x in t['loans']),
             ', '.join(t['transactions']), len(t['legs'])))
        w('')
        w('| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |')
        w('| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |')
        for r in t['legs']:
            w('| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
                r['loan'], r['transaction_id'], r['entry_type'], r['gl_account_id'],
                r['gl_account_code'], r['gl_account_name'], r['amount_minor'],
                r['currency'], r['reversed'], r['charged_off'], r['fraud']))
        w('')
    write_chargeback_md(obj, w)
    ua = obj.get('unmatched_analysis') or {}
    if ua.get('count'):
        w('## Unmatched legs -- inferred classification (NOT a read-back type)')
        w('')
        w('%d transactions / %d legs on loans %s have no entry in any `transactions`'
          % (ua['count'], ua['legs'],
             ', '.join(str(t['loan']) for t in ua['transactions'])))
        w('read-back.  Reason: %s' % ua['reason'])
        w('')
        w('Inferred type: %s' % (', '.join('`%s`' % t for t in ua['inferred_types']) or 'unknown'))
        w('')
        w('| loan | tx | legs | accounts | net-zero | inferred type |')
        w('| --- | --- | ---: | --- | --- | --- |')
        for t in ua['transactions']:
            w('| %d | %s | %d | %s | %s | `%s` |' % (
                t['loan'], t['transaction_id'], t['legs'],
                ', '.join(str(a) for a in t['gl_account_ids']),
                t['net_zero'], t['inferred_type']))
        w('')
    with open(os.path.join(HERE, 'journalentry-type-join.md'), 'w') as fh:
        fh.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
