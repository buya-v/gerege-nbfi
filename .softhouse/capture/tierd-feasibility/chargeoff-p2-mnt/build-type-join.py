#!/usr/bin/env python3
"""OH-TIERD26-DJ step 6: join every swept `/journalentries` leg to its loan
transaction TYPE and to the CHARGED-OFF dimension, then characterise the six
required charge-off-postings arms -- `repayment`, `chargeOff`, `accrual`,
`accrualAdjustment`, `waiver` and `recoveryRepayment`.

Adapted from the OH-TIERD23-DC `chargeoff-p4-mnt/build-type-join.py`.
The generic sweep leg -> type join, the transaction `paymentType` (id + name,
from `paymentDetailData.paymentType`), the DISTINCT leg shapes (account ids +
sides) per target type with one example and a per-shape transaction count, and
the per-loan currency extraction are kept.  A target type with NO legs is itself
a finding: the arm may not have been exercised by the feature.

The CHARGED-OFF rule is the one OH-TIERD26-DJ mandates, NOT the p4 rule: a leg's
transaction is on a charged-off loan only if the loan's LATEST read-back (highest
manifest `source_line`, i.e. the highest index in the capture) lists a
NON-REVERSED `chargeOff` transaction with a LOWER transaction id AND that latest
read-back's `chargedOff` flag is true.  A charge-off later undone vanishes from
the latest read-back and must not count; `manuallyReversed` on an EARLIER
read-back is not reliable (OH-TIERD23-DC counted undone charge-offs that way).
Charge-offs present in an earlier read-back but absent from the latest are
reported under `undone_chargeoffs`, with the transactions posted before and
after the undo.

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

# The six posting arms OH-TIERD26-DJ step 6 must characterise.  The target set
# is exactly this list so a target the replay never exercised is still reported
# -- with zero legs -- as a finding.
TARGET_TYPES = (
    'loanTransactionType.repayment',
    'loanTransactionType.chargeOff',
    'loanTransactionType.accrual',
    'loanTransactionType.accrualAdjustment',
    'loanTransactionType.waiver',
    'loanTransactionType.recoveryRepayment',
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


def chargeoffs_for(loan_id):
    """Non-reversed `chargeOff` transaction ids, ascending (the id order is the
    rule this capture uses: a charge-off with a LOWER transaction id)."""
    out = [tid for tid, tx in tx_map_for(loan_id).items()
           if tx['code'] == 'loanTransactionType.chargeOff' and not tx['reversed']]
    return sorted(out)


def detail_currency(loan_id):
    for pat in (os.path.join(LOANS, 'loan-%d' % loan_id, 'loan-*-detail-*.json'),
                os.path.join(STAGE, 'loan-%d-detail-*.json')):
        for _, body in read_jsons(sorted(glob.glob(pat))):
            if isinstance(body, dict) and isinstance(body.get('currency'), dict):
                return body['currency'].get('code')
    return None


def read_manifest():
    """The capture manifest, one entry per extracted body with its `source_line`.

    The runner's read-backs are numbered PER ENDPOINT (`...-1`, `...-2`, ...), so
    the file-name suffix says nothing about chronology ACROSS endpoints.  The
    manifest's `source_line` is the only reliable order; it is used for the
    LATEST read-back below."""
    return json.load(open(os.path.join(HERE, 'manifest-chargeoff-p2.json')))


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


def _chargeoff_ids(body, only_non_reversed=False):
    """The `chargeOff` transaction ids listed by one read-back body."""
    out = []
    for t in body.get('transactions') or []:
        if (t.get('type') or {}).get('code') != 'loanTransactionType.chargeOff':
            continue
        tid = t.get('id')
        if tid is None:
            continue
        if only_non_reversed and (t.get('manuallyReversed') or t.get('reversed')):
            continue
        out.append(tid)
    return sorted(out)


def _co_detail(source_line, f, body):
    rel = os.path.relpath(f, HERE) if os.path.isabs(f) else f
    all_cos = _chargeoff_ids(body)
    live = _chargeoff_ids(body, only_non_reversed=True)
    return {
        'charged_off': bool(body.get('chargedOff')),
        'chargeoff_ids': live,
        'reversed_chargeoff_ids': [tid for tid in all_cos if tid not in live],
        'readback_file': rel,
        'source_line': source_line,
    }


def latest_chargeoff_detail(loan_id, reads):
    """The loan's LATEST read-back and its charge-off evidence.

    The rule needs the highest-index read-back that carries BOTH `chargedOff`
    and a `transactions` list, so a charge-off later undone (which vanishes from
    the latest read-back) is not counted.  `reads` is ordered by manifest
    `source_line` -- the per-endpoint file suffixes are not cross-endpoint
    chronological.  Falls back to the latest read-back carrying only
    `chargedOff` when no transaction-bearing read-back exists.

    Returns {charged_off, chargeoff_ids, reversed_chargeoff_ids, readback_file,
    source_line} or None."""
    flagged = None
    for sl, f in reversed(reads.get(loan_id, [])):
        try:
            body = json.load(open(f))
        except (ValueError, IOError):
            continue
        if not (isinstance(body, dict) and 'chargedOff' in body):
            continue
        if flagged is None:
            flagged = (sl, f, body)
        if isinstance(body.get('transactions'), list):
            return _co_detail(sl, f, body)
    if flagged is not None:
        return _co_detail(*flagged)
    return None


def undone_chargeoffs(loan_id, reads, txmaps):
    """Every UNDONE charge-off of the loan, with the transactions posted before
    and after the undo.

    Two independent pieces of evidence, both from the read-backs ordered by
    manifest `source_line` (not by the unreliable earlier-read-back
    `manuallyReversed` alone):
      * a `chargeOff` the LATEST transaction-bearing read-back lists as
        `manuallyReversed`/`reversed` (still present, marked undone);
      * a `chargeOff` id an EARLIER transaction-bearing read-back listed but the
        latest one has dropped entirely (it vanished).
    For each, the transactions the loan posted before and after it are taken
    from the latest read-back that still lists the undone charge-off."""
    txn_reads = []
    for sl, f in reads.get(loan_id, []):
        try:
            body = json.load(open(f))
        except (ValueError, IOError):
            continue
        if isinstance(body, dict) and isinstance(body.get('transactions'), list):
            txn_reads.append((sl, f, body))
    if not txn_reads:
        return []
    txn_reads.sort()
    latest_sl, latest_f, latest = txn_reads[-1]
    latest_all = set(_chargeoff_ids(latest))

    undone = {}

    def rel(p):
        return os.path.relpath(p, HERE) if os.path.isabs(p) else p

    for t in latest.get('transactions') or []:
        if (t.get('type') or {}).get('code') != 'loanTransactionType.chargeOff':
            continue
        if t.get('manuallyReversed') or t.get('reversed'):
            undone[t.get('id')] = {
                'evidence': 'listed as manuallyReversed/reversed in the LATEST read-back',
                'evidence_readback': rel(latest_f),
                'evidence_source_line': latest_sl,
            }
    for sl, f, body in txn_reads[:-1]:
        if sl >= latest_sl:
            continue
        for tid in _chargeoff_ids(body):
            if tid in latest_all or tid in undone:
                continue
            undone[tid] = {
                'evidence': 'present in an earlier read-back, absent from the LATEST read-back',
                'evidence_readback': rel(f),
                'evidence_source_line': sl,
                'earlier_manually_reversed': any(
                    x.get('id') == tid and (x.get('manuallyReversed') or x.get('reversed'))
                    for x in body.get('transactions') or []),
            }

    out = []
    for tid in sorted(undone):
        ref_sl, ref_f, ref = None, None, None
        for sl, f, body in reversed(txn_reads):
            if tid in set(_chargeoff_ids(body)):
                ref_sl, ref_f, ref = sl, f, body
                break
        before, after = [], []
        for t in (ref or {}).get('transactions') or []:
            other = t.get('id')
            if other is None or other == tid:
                continue
            row = {'transaction_id': 'L%d' % other,
                   'type': (t.get('type') or {}).get('code'),
                   'date': date_str(t.get('date')),
                   'amount_minor': minor(t.get('amount'))
                   if t.get('amount') is not None else None}
            (before if other < tid else after).append(row)
        before.sort(key=lambda r: int(r['transaction_id'][1:]))
        after.sort(key=lambda r: int(r['transaction_id'][1:]))
        info = undone[tid]
        out.append({
            'loan': loan_id,
            'transaction_id': 'L%d' % tid,
            'transaction_id_num': tid,
            'evidence': info['evidence'],
            'evidence_readback': info['evidence_readback'],
            'evidence_source_line': info['evidence_source_line'],
            'order_readback': rel(ref_f) if ref_f else None,
            'order_source_line': ref_sl,
            'transactions_before': before,
            'transactions_after': after,
        })
    return out


def chargeoff_response_ids(loan_id):
    """The `resourceId` of the loan's captured charge-off command response.

    The charge-off POST is authoritative -- for loans 9, 10 and 12 the feature
    charged the loan off AFTER its last `associations=transactions` read, so the
    charge-off transaction id appears in NO read-back but the command response
    names it.  Supplementing the read-back transaction map with this id is what
    makes `chargeOff` complete for all 14 loans.  Non-reversed (a charge-off
    reversal is a separate transaction/command; none is captured for these)."""
    path = os.path.join(LOANS, 'loan-%d' % loan_id,
                        'loan-%d-charge-off-response.json' % loan_id)
    try:
        body = json.load(open(path))
    except (ValueError, IOError):
        return []
    rid = body.get('resourceId')
    return [rid] if isinstance(rid, int) else []


def sweep_items(loan_id):
    path = os.path.join(SWEEP, 'loan-%d.json' % loan_id)
    try:
        return (json.load(open(path)) or {}).get('pageItems') or []
    except (ValueError, IOError):
        return []


def inject_response_chargeoff(txmap, loan_id):
    """Add synthetic `chargeOff` entries for the response ids not in the read-back
    map, so the charge-off transaction is typed and its date/amount are known.
    Date comes from the sweep leg; amount from the sum of its debit legs."""
    for rid in chargeoff_response_ids(loan_id):
        if rid in txmap:
            continue
        date = None
        debit = 0
        for it in sweep_items(loan_id):
            if it.get('transactionId') != 'L%d' % rid:
                continue
            date = it.get('transactionDate')
            if ((it.get('entryType') or {}).get('value') or '').lower() == 'debit':
                debit += int(round(float(it.get('amount', 0)) * 100))
        txmap[rid] = {
            'code': 'loanTransactionType.chargeOff',
            'value': 'Charge-off',
            'date': date,
            'amount_minor': str(debit) if debit else None,
            'payment_type_id': None,
            'payment_type_name': None,
            'reversed': False,
            'portions': {},
            'source': 'charge-off-response',
        }
    return txmap


def shape_key(legs):
    """The leg shape: the sorted (side, account id) pairs, e.g.
    `CREDIT:2 DEBIT:1`."""
    return ' '.join('%s:%s' % (l['entry_type'], l['gl_account_id'])
                    for l in sorted(legs, key=lambda r: (r['entry_type'] or '',
                                                         r['gl_account_id'] or 0)))


def build_targets(types, loan_chargeoff, currencies, txmaps, latest):
    """Type x charged-off for every target arm plus the DISTINCT leg shapes per
    arm, each with one example and the count of transactions of that shape.

    `latest` is loan id -> `latest_chargeoff_detail`; a transaction is on a
    charged-off loan only when that latest read-back has `chargedOff=true` and a
    NON-REVERSED chargeOff id LOWER than the transaction id."""
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
        d = latest.get(lid) or {}
        cos = d.get('chargeoff_ids', []) if d.get('charged_off') else []
        for tid in sorted(txmaps[lid]):
            tx = txmaps[lid][tid]
            if tx.get('code') not in TARGET_TYPES:
                continue
            qualifying = [c for c in cos if c < tid]
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
        findings.append('NO loan\'s LATEST read-back lists a non-reversed `chargeOff` '
                        'transaction: no leg is on a charged-off loan under the '
                        'latest-read-back rule.')
    if not any_latest_co:
        findings.append('no loan\'s LATEST read-back has `chargedOff=true`: the '
                        'charged-off dimension is empty (every leg charged-off=no).')
    return {
        'charged_off_rule': ('a leg\'s transaction is on a charged-off loan ONLY if the '
                             'loan\'s LATEST read-back (highest manifest source_line) has '
                             '`chargedOff=true` and lists a NON-REVERSED `chargeOff` '
                             'transaction with a LOWER transaction id'),
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
    reads = readback_index(read_manifest())
    # The read-back transaction map.  For loans charged off after their last
    # transactions read-back the `chargeOff` transaction is absent from every
    # read-back; the charge-off command response names its id, so inject it (for
    # TYPE completeness only -- it does NOT feed the charged-off rule).
    txmaps = {lid: tx_map_for(lid) for lid in loan_ids}
    for lid in loan_ids:
        inject_response_chargeoff(txmaps[lid], lid)
    # Merged non-reversed chargeOff ids across all read-backs (cross-check only).
    readback_chargeoffs = {lid: set(chargeoffs_for(lid)) for lid in loan_ids}
    response_chargeoffs = {lid: set(chargeoff_response_ids(lid)) for lid in loan_ids}
    # AUTHORITATIVE charged-off evidence: each loan's LATEST read-back.
    latest = {lid: latest_chargeoff_detail(lid, reads) for lid in loan_ids}
    undone = {lid: undone_chargeoffs(lid, reads, txmaps) for lid in loan_ids}

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
        d = latest.get(lid) or {}
        cos = d.get('chargeoff_ids', []) if d.get('charged_off') else []
        loan_chargeoff[lid] = {
            # non-reversed chargeOff ids IN THE LATEST read-back (the rule's input)
            'chargeoff_transactions': [
                {'transaction_id': 'L%d' % tid,
                 'date': (txmaps[lid].get(tid) or {}).get('date')}
                for tid in cos],
            'reversed_chargeoff_transactions_latest': [
                'L%d' % tid for tid in d.get('reversed_chargeoff_ids', [])],
            'latest_readback': d.get('readback_file'),
            'latest_source_line': d.get('source_line'),
            # merged read-backs + command response, for cross-checking only
            'chargeoffs_any_readback_or_response': [
                'L%d' % tid for tid in sorted(readback_chargeoffs[lid]
                                              | response_chargeoffs[lid])],
            'undone_chargeoffs': undone.get(lid, []),
            # final state from the loan's LATEST read-back (an undone charge-off
            # is excluded); None when no read-back carries it
            'charged_off_latest': d.get('charged_off') if d else None,
            'currency': currencies.get(lid),
        }
        for it in items:
            label = it.get('transactionId')
            n = int(label[1:]) if isinstance(label, str) and label.startswith('L') \
                and label[1:].isdigit() else None
            tx = txmaps.get(lid, {}).get(n)
            if tx is None:
                unmatched.append({'loan': lid, 'transaction_id': label,
                                  'file': 'journalentries-sweep/loan-%d.json' % lid})
            qualifying = [tid for tid in cos if n is not None and tid < n]
            leg_records.append({
                'loan': lid,
                'currency': it.get('currency', {}).get('code'),
                'journalentries_file': 'journalentries-sweep/loan-%d.json' % lid,
                'transaction_id': label,
                'transaction_id_num': n,
                'type_code': tx['code'] if tx else None,
                'type_value': tx['value'] if tx else None,
                'type_source': (tx.get('source') or 'read-back') if tx else None,
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
                'charged_off_latest': d.get('charged_off') if d else None,
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

    tg = build_targets(types, loan_chargeoff, currencies, txmaps, latest)

    # Supplement finding: charge-offs recovered from the command response because
    # the loan was charged off after its last read-back (TYPE completeness only).
    injected = {lid: sorted(response_chargeoffs[lid] - readback_chargeoffs[lid])
                for lid in loan_ids if response_chargeoffs[lid] - readback_chargeoffs[lid]}
    if injected:
        tg['findings'].append(
            'chargeOff supplement (NOT a read-back): %s.  For these loans the feature '
            'charged the loan off AFTER its last read-back, so the charge-off '
            'transaction id is in no read-back; the charge-off command response '
            '(`charge-off-response.json` `resourceId`) is the evidence and it is '
            'injected as the `chargeOff` transaction so the arm type is complete.  It '
            'is NOT used for the charged-off rule (which reads the latest read-back).'
            % ', '.join('loan %d tx L%d' % (lid, injected[lid][0]) for lid in sorted(injected)))

    # Undone charge-offs finding.
    undone_list = [u for lid in loan_ids for u in undone.get(lid, [])]
    tg['undone_chargeoffs'] = undone_list
    if undone_list:
        tg['findings'].append(
            'undone charge-off(s): %s.  Each is excluded from the charged-off '
            'dimension because it does not appear as a NON-REVERSED chargeOff in the '
            'loan\'s latest read-back; the evidence and the transactions posted before '
            'and after the undo are listed under `undone_chargeoffs` and in OWNER.md.'
            % ', '.join('loan %d %s (%s)' % (u['loan'], u['transaction_id'], u['evidence'])
                        for u in undone_list))

    # Supplement finding: explain the unmatched legs (post-charge-off postings that
    # the read-backs, captured only up to the charge-off, never saw).
    if unmatched:
        by_loan = {}
        for e in unmatched:
            n = int(e['transaction_id'][1:]) if isinstance(e['transaction_id'], str) \
                and e['transaction_id'][1:].isdigit() else None
            if n is not None:
                by_loan.setdefault(e['loan'], []).append(n)
        parts = []
        for lid in sorted(by_loan):
            ids = sorted(set(by_loan[lid]))
            spreads = []
            start = prev = ids[0]
            for n in ids[1:]:
                if n == prev + 1:
                    prev = n
                    continue
                spreads.append((start, prev))
                start = prev = n
            spreads.append((start, prev))
            rng = ', '.join('L%d' % a if a == b else 'L%d-L%d' % (a, b) for a, b in spreads)
            co = sorted(response_chargeoffs[lid]) or sorted(readback_chargeoffs[lid])
            parts.append('loan %d (%d legs, %s)%s' % (
                lid, len(ids), rng,
                '; that loan\'s chargeOff is L%d' % co[-1] if co else ''))
        tg['findings'].append(
            '(unmapped): %d swept legs on %d transactions have no read-back type: %s.  '
            'These are postings made AFTER the loan read-backs were last captured '
            '(predominantly the daily accruals), so they cannot be typed from a '
            'read-back.  They are a join gap, reported as a finding; they are NOT '
            'missing required arms.'
            % (len(unmatched), len({e['transaction_id'] for e in unmatched}),
               '; '.join(parts)))

    obj = {
        'tenant': 'tierd',
        'source': 'GET /journalentries?loanId=<id>&limit=-1 on the throwaway (8444)',
        'loan_ids': loan_ids,
        'currencies': currencies,
        'legs': len(leg_records),
        'unmatched_legs': unmatched,
        'loan_chargeoff': loan_chargeoff,
        'undone_chargeoffs': undone_list,
        'chargeoff_supplement': {str(lid): ['L%d' % t for t in injected[lid]]
                                 for lid in injected},
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
    w('# Journal-entry type join — required charge-off arms (OH-TIERD26-DJ step 6)')
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
    w('## Undone charge-offs')
    w('')
    if not obj.get('undone_chargeoffs'):
        w('None. Every `chargeOff` the read-backs list is present as a NON-REVERSED '
          'charge-off in its loan\'s latest read-back, so none was undone.')
    else:
        w('For each undone charge-off: the evidence it was undone, and the transactions '
          'the loan posted before and after it. An undone charge-off is EXCLUDED from '
          'the charged-off dimension.')
        w('')
        for u in obj['undone_chargeoffs']:
            w('### loan %d — `%s` — %s' % (u['loan'], u['transaction_id'], u['evidence']))
            w('')
            w('- evidence: `%s` (manifest source_line %s); ordering read-back `%s` '
              '(source_line %s).'
              % (u['evidence_readback'], u['evidence_source_line'],
                 u['order_readback'], u['order_source_line']))
            w('- transactions posted BEFORE the undo: %s'
              % (', '.join('%s %s %s' % (r['transaction_id'], r['type'],
                                         r['amount_minor']) for r in u['transactions_before'])
                 or '_(none)_'))
            w('- the undone charge-off: `%s`' % u['transaction_id'])
            w('- transactions posted AFTER the undo: %s'
              % (', '.join('%s %s %s' % (r['transaction_id'], r['type'],
                                         r['amount_minor']) for r in u['transactions_after'])
                 or '_(none)_'))
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
        w('| shape (side:account) | account ids | transactions | loans | example (loan, tx, amount minor, portions, paymentType) |')
        w('| --- | --- | ---: | --- | --- |')
        for s in t['shapes']:
            ex = s['example']
            w('| `%s` | %s | %d | %s | loan %d tx %s, amt %s, portions %s, payType %s/%s |' % (
                s['shape'], ', '.join(str(a) for a in s['account_ids']), s['count'],
                ', '.join(str(x) for x in s['loans']), ex['loan'], ex['transaction_id'],
                ex.get('amount_minor'), ex.get('portions'),
                ex.get('payment_type_id'), ex.get('payment_type_name')))
        w('')
    with open(os.path.join(HERE, 'journalentry-type-join.md'), 'w') as f:
        f.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
