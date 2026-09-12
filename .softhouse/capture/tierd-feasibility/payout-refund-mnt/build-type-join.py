#!/usr/bin/env python3
"""OH-TIERD24-DE step 6: join every swept `/journalentries` leg to its loan
transaction TYPE and to the CHARGED-OFF dimension, then characterise the six
required payout-refund posting arms -- `payoutRefund`, `interestRefund`,
`merchantIssuedRefund`, `repayment`, `accrualAdjustment` and `chargeOff`.

Adapted from the OH-TIERD22-DB `merchant-refund-mnt/build-type-join.py`.
The generic sweep leg -> type join, the transaction's `paymentType` (id + name,
from `paymentDetailData.paymentType`) and the DISTINCT leg shapes (account ids +
sides) per target type, with one example and a per-shape transaction count, are
kept.  A target type with NO legs is itself a finding: the arm may not have been
exercised by the feature.

CHARGED-OFF RULE (OH-TIERD24-DE, corrected): a leg's transaction is on a
charged-off loan ONLY if the loan's LATEST read-back (highest index) lists a
NON-REVERSED `chargeOff` transaction with a LOWER transaction id than the leg's
transaction AND that read-back's `chargedOff` is true.  Charge-offs the replay
undid vanish from the latest read-back; `manuallyReversed` on earlier read-backs
is NOT reliable (OH-TIERD23-DC counted undone charge-offs).

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

# The six posting arms OH-TIERD24-DE step 6 must characterise.  The target set
# is exactly this list so a target the replay never exercised is still reported
# -- with zero legs -- as a finding.
TARGET_TYPES = (
    'loanTransactionType.payoutRefund',
    'loanTransactionType.interestRefund',
    'loanTransactionType.merchantIssuedRefund',
    'loanTransactionType.repayment',
    'loanTransactionType.accrualAdjustment',
    'loanTransactionType.chargeOff',
)


def minor(amount):
    """Decimal major units -> integer minor units string (2 ISO 4217 digits)."""
    return str(int(round(float(amount) * 100)))


def date_str(seq):
    if not seq:
        return '-'
    return '%04d-%02d-%02d' % tuple(seq)


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


def payment_of(t):
    """(paymentType id, paymentType name) from a transaction read-back, or
    (None, None) for a leg that carries no payment detail."""
    pdd = t.get('paymentDetailData')
    if isinstance(pdd, dict):
        pt = pdd.get('paymentType')
        if isinstance(pt, dict):
            return pt.get('id'), pt.get('name')
    return None, None


def tx_map_for(loan_id):
    """loanTransactionId -> {code, value, date, amount_minor, payment_type_id,
    payment_type_name, reversed, portions}.

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
            pt_id, pt_name = payment_of(t)
            out[tid] = {
                'code': code,
                'value': typ.get('value'),
                'date': t.get('date'),
                'amount_minor': minor(t.get('amount'))
                if t.get('amount') is not None else None,
                'payment_type_id': pt_id,
                'payment_type_name': pt_name,
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
                # loan read-backs expose `manuallyReversed`; the journal-entry
                # legs use `reversed`.  Treat either as reversed, sticky.
                'reversed': (bool(prev.get('reversed')) if prev else False)
                or bool(t.get('manuallyReversed')) or bool(t.get('reversed')),
            }
    return out


def latest_readback(loan_id):
    """The loan's LATEST full read-back: the highest-sequence
    `detail-associations-all-*` body (committed first, then stage)."""
    pats = (os.path.join(LOANS, 'loan-%d' % loan_id,
                         'loan-%d-detail-associations-all-*.json' % loan_id),
            os.path.join(STAGE, 'loan-%d-detail-associations-all-*.json' % loan_id))
    for pat in pats:
        files = sorted(glob.glob(pat),
                       key=lambda p: int(SEQ_RE.search(p).group(1))
                       if SEQ_RE.search(p) else 0)
        for f in reversed(files):
            try:
                body = json.load(open(f))
            except ValueError:
                continue
            if isinstance(body, dict) and 'transactions' in body:
                return body
    return None


def latest_chargeoffs(loan_id):
    """(chargedOff flag, non-reversed `chargeOff` transaction ids) from the loan's
    LATEST read-back ONLY.

    A leg is on a charged-off loan only if the LATEST read-back lists a
    non-reversed chargeOff transaction with a LOWER id than the leg's transaction
    AND the read-back's `chargedOff` is true.  A charge-off the replay later undid
    vanishes from the latest read-back and therefore cannot count; `manuallyReversed`
    on an earlier read-back is not consulted."""
    body = latest_readback(loan_id)
    if not isinstance(body, dict):
        return None, []
    ids = []
    for tx in body.get('transactions') or []:
        code = (tx.get('type') or {}).get('code')
        if code == 'loanTransactionType.chargeOff' and not (
                tx.get('manuallyReversed') or tx.get('reversed')):
            if tx.get('id') is not None:
                ids.append(tx['id'])
    return bool(body.get('chargedOff')), sorted(ids)


def detail_currency(loan_id):
    for pat in (os.path.join(LOANS, 'loan-%d' % loan_id, 'loan-*-detail-*.json'),
                os.path.join(STAGE, 'loan-%d-detail-*.json')):
        for _, body in read_jsons(sorted(glob.glob(pat))):
            if isinstance(body, dict) and isinstance(body.get('currency'), dict):
                return body['currency'].get('code')
    return None


def shape_key(legs):
    """The leg shape: the sorted (side, account id) pairs, e.g.
    `CREDIT:2 DEBIT:1`."""
    return ' '.join('%s:%s' % (l['entry_type'], l['gl_account_id'])
                    for l in sorted(legs, key=lambda r: (r['entry_type'] or '',
                                                         r['gl_account_id'] or 0)))


def build_targets(types, loan_chargeoff, currencies, txmaps, chargeoffs):
    """Type x charged-off for every target arm plus the DISTINCT leg shapes per
    arm, each with one example and the count of transactions of that shape."""
    by_type = {}
    all_legs = []
    for code in TARGET_TYPES:
        t = types.get(code)
        legs = list(t['legs']) if t else []
        all_legs.extend(legs)
        on_co = [r for r in legs if r['charged_off']]
        off_co = [r for r in legs if not r['charged_off']]

        tx_groups = {}
        for r in legs:
            tx_groups.setdefault((r['loan'], r['transaction_id_num']), []).append(r)
        shapes = {}
        for (lid, n), group in tx_groups.items():
            key = shape_key(group)
            s = shapes.setdefault(key, {
                'shape': key,
                'account_ids': sorted({r['gl_account_id'] for r in group}),
                'sides': sorted({(r['entry_type'], r['gl_account_id']) for r in group},
                                key=lambda p: (p[0] or '', p[1] or 0)),
                'transactions': [],
                'legs': sorted(group, key=lambda r: (r['entry_type'] or '',
                                                      r['gl_account_id'] or 0)),
            })
            s['transactions'].append((lid, n))
        shape_list = []
        for key, s in shapes.items():
            s['transactions'].sort()
            s['count'] = len(s['transactions'])
            s['loans'] = sorted({lid for lid, _ in s['transactions']})
            lid, n = s['transactions'][0]
            tx = txmaps.get(lid, {}).get(n) or {}
            s['example'] = {
                'loan': lid,
                'transaction_id': 'L%d' % n,
                'transaction_id_num': n,
                'date': tx.get('date'),
                'amount_minor': tx.get('amount_minor'),
                'payment_type_id': tx.get('payment_type_id'),
                'payment_type_name': tx.get('payment_type_name'),
                'reversed': tx.get('reversed'),
                'portions': tx.get('portions'),
                'legs': s['legs'],
            }
            shape_list.append(s)
        shape_list.sort(key=lambda s: (-s['count'], s['shape']))

        by_type[code] = {
            'present': t is not None,
            'total_legs': len(legs),
            'total_transactions': sorted({r['transaction_id'] for r in legs},
                                         key=lambda s: int(s[1:]) if s and s[1:].isdigit() else 0),
            'total_loans': sorted({r['loan'] for r in legs}),
            'legs_on_charged_off_loan': len(on_co),
            'loans_on_charged_off': sorted({r['loan'] for r in on_co}),
            'legs_on_not_charged_off_loan': len(off_co),
            'loans_on_not_charged_off': sorted({r['loan'] for r in off_co}),
            'shapes': shape_list,
            'all_legs': legs,
        }

    # Every transaction of a target type the read-backs expose, with its amount,
    # portions, payment type and legs, whether or not the sweep found legs.
    target_transactions = []
    for lid in sorted(txmaps):
        cos = chargeoffs.get(lid, [])
        for tid in sorted(txmaps[lid]):
            tx = txmaps[lid][tid]
            if tx.get('code') not in TARGET_TYPES:
                continue
            qualifying = ([c for c in cos if c < tid]
                          if loan_chargeoff.get(lid, {}).get('charged_off_latest') else [])
            target_transactions.append({
                'loan': lid,
                'transaction_id': 'L%d' % tid,
                'transaction_id_num': tid,
                'type_code': tx.get('code'),
                'type_value': tx.get('value'),
                'date': tx.get('date'),
                'amount_minor': tx.get('amount_minor'),
                'reversed': tx.get('reversed'),
                'payment_type_id': tx.get('payment_type_id'),
                'payment_type_name': tx.get('payment_type_name'),
                'charged_off': bool(qualifying),
                'charged_off_latest': loan_chargeoff.get(lid, {}).get('charged_off_latest'),
                'chargeoff_tx_ids': ['L%d' % c for c in qualifying],
                'currency': currencies.get(lid, 'UNKNOWN'),
                'portions': tx.get('portions'),
                'legs': [],
            })
    by_key = {(t['loan'], t['transaction_id_num']): t for t in target_transactions}
    for r in all_legs:
        key = (r['loan'], r['transaction_id_num'])
        if key in by_key:
            by_key[key]['legs'].append(r)
    for t in target_transactions:
        t['legs'].sort(key=lambda r: (0 if r['entry_type'] == 'DEBIT' else 1,
                                      r['gl_account_id'] or 0))
    target_transactions.sort(key=lambda t: (t['loan'], t['transaction_id_num']))

    findings = []
    empty = [c for c in TARGET_TYPES if not by_type[c]['total_legs']]
    if empty:
        findings.append('target type(s) with NO journal-entry legs '
                        'at all: %s.  The arm was NOT exercised by this feature.'
                        % ', '.join(empty))
    no_legs = [t for t in target_transactions if not t['legs']]
    if no_legs:
        findings.append('%d target transaction(s) in the read-backs have NO '
                        'journal-entry legs: %s.'
                        % (len(no_legs),
                           ', '.join('loan %d tx %s' % (t['loan'], t['transaction_id'])
                                     for t in no_legs)))
    any_co_tx = any(loan_chargeoff.get(lid, {}).get('chargeoff_transactions')
                    for lid in loan_chargeoff)
    any_latest_co = any(loan_chargeoff.get(lid, {}).get('charged_off_latest')
                        for lid in loan_chargeoff)
    if not any_co_tx:
        findings.append('no non-reversed `chargeOff` loan transaction appears in ANY '
                        'read-back: no leg is on a charged-off loan.')
    if not any_latest_co:
        findings.append('no loan\'s LATEST read-back has `chargedOff=true`: the '
                        'charged-off dimension is empty (every leg charged-off=no).')
    return {
        'charged_off_rule': ('the loan\'s LATEST read-back (highest index) lists a '
                             'NON-REVERSED chargeOff transaction with a LOWER transaction '
                             'id than the leg\'s transaction AND its `chargedOff` is true'),
        'target_types': list(TARGET_TYPES),
        'by_type': by_type,
        'currencies': currencies,
        'loans': loan_chargeoff,
        'total_legs': len(all_legs),
        'total_transactions': len(target_transactions),
        'total_loans': sorted({r['loan'] for r in all_legs}),
        'transactions': target_transactions,
        'transactions_without_legs': no_legs,
        'empty_types': empty,
        'findings': findings,
    }


def main():
    manifest = json.load(open(os.path.join(HERE, 'journalentries-sweep-manifest.json')))
    loan_ids = sorted(m['loan_id'] for m in manifest)
    txmaps = {lid: tx_map_for(lid) for lid in loan_ids}
    latest = {lid: latest_chargeoffs(lid) for lid in loan_ids}
    chargeoffs = {lid: latest[lid][1] for lid in loan_ids}
    latest_co = {lid: latest[lid][0] for lid in loan_ids}

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
            'chargeoff_transactions': [{'transaction_id': 'L%d' % tid,
                                        'date': (txmaps[lid].get(tid) or {}).get('date')}
                                       for tid in cos],
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
            qualifying = ([tid for tid in cos if n is not None and tid < n]
                          if latest_co.get(lid) else [])
            leg_records.append({
                'loan': lid,
                'currency': it.get('currency', {}).get('code'),
                'journalentries_file': 'journalentries-sweep/loan-%d.json' % lid,
                'transaction_id': label,
                'transaction_id_num': n,
                'type_code': tx['code'] if tx else None,
                'type_value': tx['value'] if tx else None,
                'transaction_date': tx['date'] if tx else it.get('transactionDate'),
                'entry_type': (it.get('entryType') or {}).get('value'),
                'gl_account_id': it.get('glAccountId'),
                'gl_account_code': it.get('glAccountCode'),
                'gl_account_name': it.get('glAccountName'),
                'amount_minor': minor(it.get('amount')),
                'reversed': it.get('reversed'),
                'payment_type_id': tx.get('payment_type_id') if tx else None,
                'payment_type_name': tx.get('payment_type_name') if tx else None,
                'charged_off': bool(qualifying),
                'charged_off_latest': latest_co.get(lid),
                'chargeoff_tx_ids': ['L%d' % tid for tid in qualifying],
            })

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

    tg = build_targets(types, loan_chargeoff, currencies, txmaps, chargeoffs)
    obj = {
        'tenant': 'tierd',
        'source': 'GET /journalentries?loanId=<id>&limit=-1 on the throwaway (8444)',
        'loan_ids': loan_ids,
        'currencies': currencies,
        'legs': len(leg_records),
        'unmatched_legs': unmatched,
        'loan_chargeoff': loan_chargeoff,
        'targets': tg,
        'types': types,
    }
    with open(os.path.join(HERE, 'journalentry-type-join.json'), 'w') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write('\n')
    write_md(obj)
    print('joined %d legs across %d types; %d unmatched; target legs %d on %d '
          'transactions / %d loans; empty target types %s'
          % (len(leg_records), len(types), len(unmatched), tg['total_legs'],
             tg['total_transactions'], len(tg['total_loans']),
             ','.join(tg['empty_types']) or 'none'))


def write_md(obj):
    tg = obj['targets']
    out = []
    w = out.append
    w('# Journal-entry type join — required payout-refund arms (OH-TIERD24-DE step 6)')
    w('')
    w('%d swept legs across %d transaction types; %d legs unmatched to a read-back.'
      % (obj['legs'], len(obj['types']), len(obj['unmatched_legs'])))
    w('')
    w('Charged-off rule: %s.  Charged-off latest = the loan `chargedOff` flag in '
      'its LATEST read-back.' % tg['charged_off_rule'])
    w('')
    w('## Type x charged-off -> legs -> loans (every type)')
    w('')
    w('| transaction type | legs | legs on charged-off loan | loans on charged-off |')
    w('| --- | ---: | ---: | --- |')
    for key in sorted(obj['types'], key=lambda k: (-len(obj['types'][k]['legs']), k)):
        t = obj['types'][key]
        onco = [r for r in t['legs'] if r['charged_off']]
        label = '`(unmapped)`' if key == '(unmapped)' else '`%s`' % key
        w('| %s | %d | %d | %s |' % (
            label, len(t['legs']), len(onco),
            ', '.join(str(x) for x in sorted({r['loan'] for r in onco})) or '-'))
    w('')
    w('## Target arms (required)')
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
    for f in tg['findings']:
        w('**FINDING:** %s' % f)
        w('')
    w('## Distinct leg shapes per required arm')
    w('')
    for code in tg['target_types']:
        t = tg['by_type'][code]
        w('### `%s`' % code)
        w('')
        if not t['shapes']:
            w('_no legs._')
            w('')
            continue
        w('| shape (side:account) | account ids | transactions | loans | example |')
        w('| --- | --- | ---: | --- | --- |')
        for s in t['shapes']:
            ex = s['example']
            w('| `%s` | %s | %d | %s | loan %d tx %s |' % (
                s['shape'], ', '.join(str(a) for a in s['account_ids']), s['count'],
                ', '.join(str(x) for x in s['loans']), ex['loan'], ex['transaction_id']))
        w('')
    with open(os.path.join(HERE, 'journalentry-type-join.md'), 'w') as f:
        f.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
