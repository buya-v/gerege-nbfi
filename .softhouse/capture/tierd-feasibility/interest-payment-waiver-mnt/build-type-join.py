#!/usr/bin/env python3
"""OH-TIERD12-CE step 6 / OH-TIERD13-CI step 6: join every swept
`/journalentries` leg to its loan transaction TYPE, and (TIERD13) to the
CHARGED-OFF dimension and the loan's FRAUD flag.

The join is the capture's point: a journal-entry leg carries only
`transactionId` = `L<loanTransactionId>`; the *type* of that loan transaction
(disbursement / accrual / accrualActivity / accrualAdjustment / chargeOff / ...)
lives only in the loan read-backs under `loans/loan-<id>/*-transactions-*.json`
(or `stage/` for a failed scenario's loan).  This script reads both and emits,
per type, the legs and the loans that produced them.

OH-TIERD13-CI adds two read-back-derived dimensions to every leg:

* `charged_off` -- whether a NON-REVERSED `chargeOff` transaction is dated on
  or before the leg's transaction date.  This mirrors the accounting dispatch:
  the backdated merchant refunds on loans 45/46 (dated 13 April, before the
  14 April charge-off) post through the NON-charged-off arm (Loans Receivable /
  Interest/Fee Receivable), while loans 48/49/50 (refunds dated 15 April, after
  the 14 April charge-off) post through
  `createJournalEntriesForRepaymentWhenLoanIsChargedOff` (Credit Loss/Bad Debt /
  Interest Income Charge Off).
* `fraud` -- the loan-level fraud flag (`markAsFraud` read-back/request), which
  selects `CHARGE_OFF_FRAUD_EXPENSE` over `CHARGE_OFF_EXPENSE` in the
  merchantIssuedRefund / payoutRefund principal arm.

It writes `journalentry-type-join.json` and `journalentry-type-join.md`.  Amounts
are integer minor units (2 ISO 4217 digits); the raw sweep bodies keep the decimal
major units the oracle emitted.

The sweep is flat (`journalentries-sweep/loan-<id>.json`, one paged body per
loan), unlike the runner's per-transaction `journalentries/`; hence this is a new
script, not a copy of writeoff-mnt/build-type-join.py.
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

    rg = build_refund_goodwill(types, loan_chargeoff, currencies)
    obj = {
        'tenant': 'tierd',
        'source': 'GET /journalentries?loanId=<id>&limit=-1 on the throwaway (8444)',
        'loan_ids': loan_ids,
        'currencies': currencies,
        'legs': len(leg_records),
        'unmatched_legs': unmatched,
        'unmatched_analysis': unmatched_analysis,
        'loan_chargeoff': loan_chargeoff,
        'refund_goodwill': rg,
        'types': types,
    }
    with open(os.path.join(HERE, 'journalentry-type-join.json'), 'w') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write('\n')
    write_md(obj)
    write_accrual_tsv(obj)
    write_refund_goodwill_tsv(obj)
    accrual = sorted(k for k in types if 'accrual' in k.lower())
    print('joined %d legs across %d types; %d unmatched (%d inferred %s); accrual types %s'
          % (len(leg_records), len(types), len(unmatched),
             unmatched_analysis['count'],
             ','.join(unmatched_analysis['inferred_types']) or '?', accrual))


TARGET_TYPES = ('loanTransactionType.merchantIssuedRefund',
                'loanTransactionType.payoutRefund',
                'loanTransactionType.goodwillCredit')


def build_refund_goodwill(types, loan_chargeoff, currencies):
    """Type x charged-off for the three refund/goodwill arms, and the required
    per-leg listing for the legs that posted on a CHARGED-OFF loan."""
    by_type = {}
    for code in TARGET_TYPES:
        t = types.get(code)
        legs = list(t['legs']) if t else []
        on_co = [r for r in legs if r['charged_off']]
        off_co = [r for r in legs if not r['charged_off']]
        by_type[code] = {
            'present': t is not None,
            'total_legs': len(legs),
            'total_loans': sorted({r['loan'] for r in legs}),
            'legs_on_charged_off_loan': len(on_co),
            'loans_on_charged_off': sorted({r['loan'] for r in on_co}),
            'legs_on_not_charged_off_loan': len(off_co),
            'loans_on_not_charged_off': sorted({r['loan'] for r in off_co}),
            'on_charged_off_legs': on_co,
        }
    return {
        'charged_off_rule': ('a NON-REVERSED chargeOff loan transaction dated on '
                             'or before the leg transaction date'),
        'target_types': list(TARGET_TYPES),
        'by_type': by_type,
        'currencies': currencies,
        'loans': loan_chargeoff,
        'payout_refund_observed': any(
            types.get(c, {}).get('legs') for c in
            ('loanTransactionType.payoutRefund',)),
    }


def write_refund_goodwill_tsv(obj):
    """Flat listing of every merchantIssuedRefund / payoutRefund / goodwillCredit
    leg that posted while the loan was charged off (the required columns)."""
    cols = ['type', 'loan', 'tx', 'entry', 'gl_account_id', 'gl_account_name',
            'amount_minor', 'fraud', 'currency', 'transaction_date',
            'chargeoff_tx_id']
    rows = []
    rg = obj['refund_goodwill']['by_type']
    for code in TARGET_TYPES:
        for r in rg[code]['on_charged_off_legs']:
            rows.append([code, str(r['loan']), r['transaction_id'], r['entry_type'],
                         str(r['gl_account_id']), r['gl_account_name'],
                         str(r['amount_minor']), str(r['fraud']), r['currency'],
                         '-'.join('%02d' % x for x in (r['transaction_date'] or [])),
                         ','.join(r['chargeoff_tx_ids'])])
    rows.sort(key=lambda x: (x[1] and int(x[1]), x[2] and int(x[2][1:]),
                             0 if x[3] == 'DEBIT' else 1))
    with open(os.path.join(HERE, 'chargedoff-refund-goodwill.tsv'), 'w') as fh:
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


def write_refund_goodwill_md(obj, w):
    """Type x charged-off summary + the required leg listing (OWNER step 6)."""
    rg = obj['refund_goodwill']
    w('## Type x charged-off -- refund / goodwill arms (OH-TIERD13-CI step 6)')
    w('')
    w('Charged-off rule: %s.' % rg['charged_off_rule'])
    w('')
    w('| type | present | legs | loans | legs on charged-off loan | loans on charged-off |')
    w('| --- | --- | ---: | --- | ---: | --- |')
    for code in rg['target_types']:
        t = rg['by_type'][code]
        w('| `%s` | %s | %d | %s | %d | %s |' % (
            code, t['present'], t['total_legs'],
            ', '.join(str(x) for x in t['total_loans']) or '-',
            t['legs_on_charged_off_loan'],
            ', '.join(str(x) for x in t['loans_on_charged_off']) or '-'))
    w('')
    if not rg['payout_refund_observed']:
        w('`payoutRefund`: **no legs observed** in this replay (the type is present in')
        w('the processor but no Part-3 scenario issues one).')
        w('')
    w('### Legs on a CHARGED-OFF loan -- required listing')
    w('')
    w('| type | loan | tx | entry | account id | account name | amount (minor) | fraud | currency |')
    w('| --- | --- | --- | --- | --- | --- | ---: | --- | --- |')
    any_leg = False
    for code in rg['target_types']:
        for r in rg['by_type'][code]['on_charged_off_legs']:
            any_leg = True
            w('| `%s` | %d | %s | %s | %s | %s | %s | %s | %s |' % (
                code, r['loan'], r['transaction_id'], r['entry_type'],
                r['gl_account_id'], r['gl_account_name'], r['amount_minor'],
                r['fraud'], r['currency']))
    if not any_leg:
        w('| _none_ | | | | | | | | |')
    w('')
    w('### Per-loan charge-off / fraud state')
    w('')
    w('| loan | currency | fraud | non-reversed chargeOff transactions |')
    w('| --- | --- | --- | --- |')
    for lid in sorted(rg['loans']):
        li = rg['loans'][lid]
        cos = ', '.join('%s@%s' % (c['transaction_id'],
                                   '-'.join('%02d' % x for x in (c['date'] or [])))
                        for c in li['chargeoff_transactions']) or '-'
        w('| %d | %s | %s | %s |' % (
            lid, rg['currencies'].get(lid, 'UNKNOWN'), li['fraud'], cos))
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
    write_refund_goodwill_md(obj, w)
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
