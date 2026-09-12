#!/usr/bin/env python3
"""OH-TIERD27-DL step 6: join every swept `/journalentries` leg to its loan
transaction TYPE and to the CHARGED-OFF dimension, then characterise the six
required posting arms -- `refund` (the REFUND on an ACTIVE loan,
`createJournalEntriesForRefundForActiveLoan`), `repayment`, `merchantIssuedRefund`,
`payoutRefund`, `creditBalanceRefund` and `interestRefund`.

Adapted from the OH-TIERD26-DJ `chargeoff-p2-mnt/build-type-join.py` and the
OH-TIERD22-DB `merchant-refund-mnt/build-type-join.py`.  Kept: the generic sweep
leg -> type join (a leg's `transactionId` is `L<loanTransactionId>`), the
transaction `paymentType` (id + name, from `paymentDetailData.paymentType`), the
money in integer minor units, the per-loan currency, and the DISTINCT leg shapes
(account ids + sides) per target type, each with ONE example and the count of
transactions of that shape.  A target type with NO legs is itself a finding.

CHARGED-OFF RULE (OH-TIERD27-DL brief, `Charged-off classification`, the rule as
corrected by OH-TIERD26-DJ -- DATE order, NOT id order): a leg's transaction is on
a charged-off loan only if the loan's LATEST read-back (highest manifest
`source_line`) has `chargedOff` true and lists a NON-REVERSED `chargeOff`
transaction with an EARLIER transaction DATE than the leg's transaction, or the
SAME date and a LOWER transaction id.  The runner numbers read-backs PER ENDPOINT
(`...-1`, `...-2`, ...), so the file-name suffix says nothing about chronology
across endpoints; the manifest `source_line` is the only reliable order.  A
charge-off that was undone vanishes from the latest read-back and does not count.

This feature has NO charge-off and no USD product, so every leg should join to a
not-charged-off loan; a non-empty charged-off arm would itself be a finding.
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

# The six posting arms OH-TIERD27-DL step 6 must characterise, as friendly types.
# The target set is exactly this list so a target the replay never exercised is
# still reported -- with zero legs -- as a finding.  `refund` is resolved to the
# exact observed code (the brief: "name the exact type code you see"), with the
# known aliases below.
TARGET_TYPES = (
    'loanTransactionType.refund',
    'loanTransactionType.repayment',
    'loanTransactionType.merchantIssuedRefund',
    'loanTransactionType.payoutRefund',
    'loanTransactionType.creditBalanceRefund',
    'loanTransactionType.interestRefund',
)
REFUND_ALIASES = (
    'loanTransactionType.refund',
    'loanTransactionType.refundByCash',
    'loanTransactionType.refundbycash',
)


def minor(amount):
    """Decimal major units -> integer minor units string (2 ISO 4217 digits)."""
    return str(int(round(float(amount) * 100)))


def date_str(seq):
    if not seq:
        return '-'
    return '%04d-%02d-%02d' % tuple(seq)


def date_key(seq):
    """A sortable/comparable key for a [y, m, d] transaction date; None stays None."""
    if isinstance(seq, (list, tuple)) and len(seq) == 3:
        return tuple(int(x) for x in seq)
    return None


def read_jsons(paths):
    for f in paths:
        try:
            yield f, json.load(open(f))
        except ValueError:
            continue
        except IOError:
            continue


def read_manifest():
    """The capture manifest, one entry per extracted body with its `source_line`."""
    path = os.path.join(HERE, 'manifest-loan-p3.json')
    if os.path.exists(path):
        return json.load(open(path))
    return []


def readback_index(manifest):
    """loan id -> [(source_line, absolute file), ...] ascending, for every GET."""
    out = {}
    for e in manifest:
        if e.get('method') != 'GET' or not e.get('loan_id'):
            continue
        f = e['file']
        if not os.path.isabs(f):
            f = os.path.join(HERE, f)
        out.setdefault(e['loan_id'], []).append((e.get('source_line') or 0, f))
    for lid in out:
        out[lid].sort()
    return out


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
    pdd = t.get('paymentDetailData')
    if isinstance(pdd, dict):
        pt = pdd.get('paymentType')
        if isinstance(pt, dict):
            return pt.get('id'), pt.get('name')
    return None, None


def tx_map_for(loan_id):
    """loanTransactionId -> {code, value, date, amount_minor, payment_type_id,
    payment_type_name, reversed, portions}.  Merged over every read-back; the code
    of an id is stable across reads (asserted)."""
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
                'type_id': typ.get('id'),
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
                'reversed': (bool(prev.get('reversed')) if prev else False)
                or bool(t.get('manuallyReversed')) or bool(t.get('reversed')),
                'date_key': date_key(t.get('date')),
            }
    return out


def _chargeoff_txns(body, only_non_reversed=False):
    """The `chargeOff` transactions a read-back lists, as {id, date}."""
    out = []
    for t in body.get('transactions') or []:
        if (t.get('type') or {}).get('code') != 'loanTransactionType.chargeOff':
            continue
        if t.get('id') is None:
            continue
        if only_non_reversed and (t.get('manuallyReversed') or t.get('reversed')):
            continue
        out.append({'id': t['id'], 'date': t.get('date'),
                    'date_key': date_key(t.get('date')),
                    'reversed': bool(t.get('manuallyReversed') or t.get('reversed'))})
    return sorted(out, key=lambda x: x['id'])


def _latest_body(reads, loan_id, predicate):
    """The highest-`source_line` read-back of the loan satisfying `predicate`."""
    for sl, f in reversed(reads.get(loan_id, [])):
        try:
            body = json.load(open(f))
        except (ValueError, IOError):
            continue
        if isinstance(body, dict) and predicate(body):
            return sl, f, body
    return None


def chargeoff_detail(loan_id, reads):
    """The loan's LATEST read-back and its charge-off evidence under the DATE rule.

    The `chargedOff` FLAG comes from the loan's latest read-back (highest manifest
    `source_line`) that carries the field; a charge-off that was undone must vanish
    from that latest read-back and so does not count (OH-TIERD23-DC).  The charge-off
    transactions (for the DATE / id comparison) are read from the latest read-back
    that lists transactions.

    Returns {charged_off, latest_source_line, latest_file, chargeoffs, readback_file,
    source_line} or None when no read-back carries `chargedOff`."""
    flagged = _latest_body(reads, loan_id, lambda b: 'chargedOff' in b)
    if flagged is None:
        return None
    sl, f, body = flagged
    charged_off = bool(body.get('chargedOff'))
    txb = _latest_body(reads, loan_id,
                       lambda b: isinstance(b.get('transactions'), list))
    source = txb[2] if (charged_off and txb is not None) else body
    live = _chargeoff_txns(source, only_non_reversed=True) if charged_off else []
    return {
        'charged_off': charged_off,
        'latest_source_line': sl,
        'latest_file': os.path.relpath(f, HERE) if os.path.isabs(f) else f,
        'readback_file': (os.path.relpath(txb[1], HERE) if txb and os.path.isabs(txb[1])
                          else (txb[1] if txb else None)),
        'source_line': (txb[0] if txb else None),
        'chargeoffs': live,
        'reversed_chargeoffs_present': bool(charged_off) and any(
            x['reversed'] for x in _chargeoff_txns(source)),
    }


def qualifying_chargeoffs(leg_id, leg_date, detail):
    """The chargeOff transactions that make this leg 'on a charged-off loan'.

    DATE rule: an EARLIER date than the leg, or the SAME date and a LOWER id."""
    if not detail or not detail.get('charged_off'):
        return []
    lk = date_key(leg_date)
    out = []
    for c in detail.get('chargeoffs') or []:
        ck = c.get('date_key')
        if lk is None or ck is None:
            continue
        if ck < lk or (ck == lk and c['id'] < leg_id):
            out.append(c)
    return out


def shape_key(legs):
    """The leg shape: the sorted (side, account id) pairs, e.g. `CREDIT:2 DEBIT:1`."""
    return ' '.join('%s:%s' % (l['entry_type'], l['gl_account_id'])
                    for l in sorted(legs, key=lambda r: (r['entry_type'] or '',
                                                         r['gl_account_id'] or 0)))


def detail_currency(loan_id):
    for pat in (os.path.join(LOANS, 'loan-%d' % loan_id, 'loan-*-detail-*.json'),
                os.path.join(STAGE, 'loan-%d-detail-*.json')):
        for _, body in read_jsons(sorted(glob.glob(pat))):
            if isinstance(body, dict) and isinstance(body.get('currency'), dict):
                return body['currency'].get('code')
    return None


def resolve_targets(observed):
    """Map each fixed target code to the exact observed code (naming the code seen)."""
    resolved = {}
    for code in TARGET_TYPES:
        if code in observed:
            resolved[code] = code
            continue
        aliases = REFUND_ALIASES if code == 'loanTransactionType.refund' else (code,)
        hit = next((a for a in aliases if a in observed), None)
        if hit is None:
            leaf = code.split('.')[-1].lower()
            hit = next((k for k in observed
                        if k.split('.')[-1].lower() == leaf
                        and 'refund' not in leaf), None)
            if code.endswith('.refund'):
                hit = next((k for k in observed
                            if k.split('.')[-1].lower() in ('refund', 'refundbycash')), None)
        resolved[code] = hit
    return resolved


def build_targets(types, loan_chargeoff, currencies, txmaps, resolved):
    """Type x charged-off for every target arm plus the DISTINCT leg shapes per arm,
    each with ONE example (loan, tx id, portions, paymentType id) and the count of
    transactions of that shape."""
    by_type = {}
    all_legs = []
    for code in TARGET_TYPES:
        obs = resolved.get(code)
        t = types.get(obs) if obs else None
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
            'observed_code': obs,
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

    target_transactions = []
    for lid in sorted(txmaps):
        d = loan_chargeoff.get(lid) or {}
        for tid in sorted(txmaps[lid]):
            tx = txmaps[lid][tid]
            obs = {resolved.get(k) for k in TARGET_TYPES}
            if tx.get('code') not in obs:
                continue
            qualifying = qualifying_chargeoffs(tid, tx.get('date'), d)
            target_transactions.append({
                'loan': lid,
                'transaction_id': 'L%d' % tid,
                'transaction_id_num': tid,
                'type_code': tx.get('code'),
                'type_id': tx.get('type_id'),
                'type_value': tx.get('value'),
                'date': tx.get('date'),
                'amount_minor': tx.get('amount_minor'),
                'reversed': tx.get('reversed'),
                'payment_type_id': tx.get('payment_type_id'),
                'payment_type_name': tx.get('payment_type_name'),
                'charged_off': bool(qualifying),
                'charged_off_latest': (d or {}).get('charged_off'),
                'chargeoff_tx_ids': ['L%d' % c['id'] for c in qualifying],
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
        findings.append('target type(s) with NO journal-entry legs at all: %s.  '
                        'The arm was NOT exercised by this feature (a finding).'
                        % ', '.join(empty))
    no_legs = [t for t in target_transactions if not t['legs']]
    if no_legs:
        findings.append('%d target transaction(s) in the read-backs have NO '
                        'journal-entry legs: %s.'
                        % (len(no_legs),
                           ', '.join('loan %d tx %s' % (t['loan'], t['transaction_id'])
                                     for t in no_legs)))
    any_co_tx = any(d.get('chargeoffs') for d in loan_chargeoff.values())
    any_latest_co = any(d.get('charged_off') for d in loan_chargeoff.values())
    if not any_co_tx:
        findings.append('no non-reversed `chargeOff` loan transaction appears in ANY '
                        'read-back: no leg is on a charged-off loan.')
    if not any_latest_co:
        findings.append('no loan\'s LATEST read-back has `chargedOff=true`: the '
                        'charged-off dimension is empty (every leg charged-off=no).')
    return {
        'charged_off_rule': ('a leg is on a charged-off loan only if the loan\'s LATEST '
                             'read-back (highest manifest source_line) has chargedOff=true '
                             'and lists a NON-REVERSED chargeOff transaction with an EARLIER '
                             'transaction DATE than the leg, or the SAME date and a LOWER id '
                             '(DATE order, not id order -- OH-TIERD26-DJ)'),
        'target_types': list(TARGET_TYPES),
        'resolved_codes': resolved,
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
    manifest = read_manifest()
    reads = readback_index(manifest)
    # Every loan the replay created is the sweep's loan list, so no swept leg is
    # silently dropped just because its loan has no committed read-back.
    sweep = os.path.join(HERE, 'journalentries-sweep-manifest.json')
    loan_ids = sorted({int(m['loan_id']) for m in json.load(open(sweep))})
    txmaps = {lid: tx_map_for(lid) for lid in loan_ids}
    details = {lid: chargeoff_detail(lid, reads) for lid in loan_ids}
    observed = set()
    for lid in loan_ids:
        observed.update(tx.get('code') for tx in txmaps[lid].values() if tx.get('code'))
    resolved = resolve_targets(observed)

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
        d = details.get(lid) or {}
        loan_chargeoff[lid] = {
            'charged_off': d.get('charged_off'),
            'chargeoffs': [{'transaction_id': 'L%d' % c['id'],
                            'date': date_str(c.get('date'))}
                           for c in d.get('chargeoffs') or []],
            'latest_readback_file': d.get('latest_file'),
            'latest_source_line': d.get('latest_source_line'),
        }
        for it in items:
            label = it.get('transactionId')
            n = int(label[1:]) if isinstance(label, str) and label.startswith('L') \
                and label[1:].isdigit() else None
            tx = txmaps.get(lid, {}).get(n)
            if tx is None:
                unmatched.append({'loan': lid, 'transaction_id': label,
                                  'file': 'journalentries-sweep/loan-%d.json' % lid})
            leg_date = tx.get('date') if tx else it.get('transactionDate')
            qualifying = qualifying_chargeoffs(n, leg_date, d) if n is not None else []
            leg_records.append({
                'loan': lid,
                'currency': it.get('currency', {}).get('code'),
                'journalentries_file': 'journalentries-sweep/loan-%d.json' % lid,
                'transaction_id': label,
                'transaction_id_num': n,
                'type_code': tx['code'] if tx else None,
                'type_value': tx['value'] if tx else None,
                'transaction_date': leg_date,
                'entry_type': (it.get('entryType') or {}).get('value'),
                'gl_account_id': it.get('glAccountId'),
                'gl_account_code': it.get('glAccountCode'),
                'gl_account_name': it.get('glAccountName'),
                'amount_minor': minor(it.get('amount')),
                'reversed': it.get('reversed'),
                'payment_type_id': tx.get('payment_type_id') if tx else None,
                'payment_type_name': tx.get('payment_type_name') if tx else None,
                'charged_off': bool(qualifying),
                'charged_off_latest': d.get('charged_off'),
                'chargeoff_tx_ids': ['L%d' % c['id'] for c in qualifying],
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

    tg = build_targets(types, loan_chargeoff, currencies, txmaps, resolved)
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
    print('resolved codes: %s' % json.dumps(tg['resolved_codes'], sort_keys=True))


def _portions_str(p):
    if not isinstance(p, dict):
        return '-'
    keys = ('principal_minor', 'interest_minor', 'fee_minor', 'penalty_minor',
            'overpayment_minor', 'unrecognized_income_minor')
    return ', '.join('%s=%s' % (k, p.get(k)) for k in keys)


def write_md(obj):
    tg = obj['targets']
    out = []
    w = out.append
    w('# Journal-entry type join — OH-TIERD27-DL step 6 (`Loan-Part3`)')
    w('')
    w('%d swept legs across %d transaction types; %d legs unmatched to a read-back.'
      % (obj['legs'], len(obj['types']), len(obj['unmatched_legs'])))
    w('')
    w('Charged-off rule: %s.' % tg['charged_off_rule'])
    w('')
    w('Resolved target codes (the exact code seen in this capture): %s.'
      % ', '.join('`%s` -> `%s`' % (k, tg['resolved_codes'].get(k))
                  for k in tg['target_types']))
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
    w('| target | exact code | present | legs | transactions | loans | legs on charged-off | '
      'loans on charged-off | legs not charged-off | loans not charged-off |')
    w('| --- | --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |')
    for code in tg['target_types']:
        t = tg['by_type'][code]
        w('| `%s` | `%s` | %s | %d | %d | %s | %d | %s | %d | %s |' % (
            code, t['observed_code'], t['present'], t['total_legs'],
            len(t['total_transactions']),
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
    w('Each shape lists the GL account ids and sides, the count of transactions of '
      'that shape, and ONE example (loan, tx id, portions in integer minor units, '
      'paymentType id).')
    w('')
    for code in tg['target_types']:
        t = tg['by_type'][code]
        w('### `%s` (exact code `%s`)' % (code, t['observed_code']))
        w('')
        if not t['shapes']:
            w('_no legs._')
            w('')
            continue
        w('| shape (SIDE:account) | account ids | transactions | loans | example loan | '
          'example tx | example portions (minor units) | paymentType id |')
        w('| --- | --- | ---: | --- | ---: | --- | --- | --- |')
        for s in t['shapes']:
            ex = s['example']
            w('| `%s` | %s | %d | %s | %d | %s | %s | %s |' % (
                s['shape'], ', '.join(str(a) for a in s['account_ids']), s['count'],
                ', '.join(str(x) for x in s['loans']), ex['loan'], ex['transaction_id'],
                _portions_str(ex['portions']), ex['payment_type_id']))
        w('')
    with open(os.path.join(HERE, 'journalentry-type-join.md'), 'w') as f:
        f.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
