#!/usr/bin/env python3
"""OH-TIERD30-DR step 6: join every swept `/journalentries` leg to its loan
transaction TYPE and to the CHARGED-OFF dimension, then characterise the
re-amortization posting arms -- `reAmortize`, `repayment`, `accrual` and
`chargeOff` -- and inventory, per loan, the read-backs that carry a repayment
schedule (`repaymentSchedule.periods`) before and after each re-amortization.

Adapted from the OH-TIERD22-DB `merchant-refund-mnt/build-type-join.py`.  Two
things changed for this capture:

  * the charged-off rule is DATE-ordered, not id-ordered (OH-TIERD26-DJ): a leg
    is on a charged-off loan only if the loan's LATEST read-back has
    `chargedOff` true AND lists a chargeOff transaction with an EARLIER
    transaction DATE, or the SAME date and a LOWER id.  A backdated repayment
    with a higher id but an earlier date therefore posts as NOT charged off, and
    an undone charge-off (gone from the latest read-back) never counts.
  * the schedule dimension: for every loan, the read-back files that carry a
    `periods` array are listed and phased against each captured reAmortize call
    using the extractor's `source_line` (a true chronology), so a reader can see
    which schedule bodies were read before and after each re-amortization.

The sweep is flat (`journalentries-sweep/loan-<id>.json`, one paged body per
loan), unlike the runner's per-transaction `journalentries/`.
"""
import glob
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SWEEP = os.path.join(HERE, 'journalentries-sweep')
LOANS = os.path.join(HERE, 'loans')
STAGE = os.path.join(HERE, 'stage')
MANIFEST = os.path.join(HERE, 'manifest-reamortization-p1.json')

# The posting arms OH-TIERD30-DR step 6 must characterise.  `reAmortize` is the
# re-amortization transaction the feature drives; the other three are the legs
# the task calls out.  A target the replay never exercised is still reported --
# with zero legs -- as a finding.
TARGET_TYPES = (
    'loanTransactionType.reAmortize',
    'loanTransactionType.repayment',
    'loanTransactionType.accrual',
    'loanTransactionType.chargeOff',
)
REAMORT = 'loanTransactionType.reAmortize'


def minor(amount):
    """Decimal major units -> integer minor units string (2 ISO 4217 digits)."""
    return str(int(round(float(amount) * 100)))


def date_str(seq):
    if not seq:
        return '-'
    return '%04d-%02d-%02d' % tuple(seq)


def load_manifest_lines():
    """(loan_id, base name) -> source log line, for chronological ordering."""
    out = {}
    for e in json.load(open(MANIFEST)):
        out[(e['loan_id'], os.path.basename(e['file']))] = e['source_line']
    return out


def loan_files(loan_id):
    """All captured bodies for the loan, keyed by base name.  The committed
    `loans/loan-<id>/` copy is preferred; a FAILED scenario's loan only exists
    under `stage/`."""
    out = {}
    for f in glob.glob(os.path.join(LOANS, 'loan-%d' % loan_id, '*.json')):
        out[os.path.basename(f)] = f
    for f in sorted(glob.glob(os.path.join(STAGE, 'loan-%d-*.json' % loan_id))):
        out.setdefault(os.path.basename(f), f)
    return out


def readbacks(loan_id, lines):
    """[(source_line, relpath, body)] for every read-back of the loan, sorted by
    the extractor's source line (the true capture order)."""
    out = []
    for base, f in loan_files(loan_id).items():
        if not base.endswith('.json'):
            continue
        try:
            body = json.load(open(f))
        except ValueError:
            continue
        if not isinstance(body, dict):
            continue
        rel = os.path.relpath(f, HERE)
        out.append((lines.get((loan_id, base), 0), rel, body))
    return sorted(out, key=lambda r: (r[0], r[1]))


def payment_of(t):
    pdd = t.get('paymentDetailData')
    if isinstance(pdd, dict):
        pt = pdd.get('paymentType')
        if isinstance(pt, dict):
            return pt.get('id'), pt.get('name')
    return None, None


def tx_map_for(loan_id, lines):
    """loanTransactionId -> type/date/amount/portions/paymentType/reversed,
    merged over every transaction read-back of the loan."""
    out = {}
    for _, _, body in readbacks(loan_id, lines):
        for t in body.get('transactions') or []:
            tid = t.get('id')
            if tid is None:
                continue
            typ = t.get('type') or {}
            code = typ.get('code')
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
                'reversed': (bool(prev.get('reversed')) if prev else False)
                or bool(t.get('manuallyReversed')) or bool(t.get('reversed')),
            }
    return out


def latest_transaction_readback(loan_id, lines):
    """(line, relpath, body) for the loan's LATEST read-back that carries a
    `transactions` array (the highest source line), or None."""
    best = None
    for line, rel, body in readbacks(loan_id, lines):
        if body.get('transactions'):
            if best is None or line >= best[0]:
                best = (line, rel, body)
    return best


def charged_off_state(loan_id, lines):
    """Charged-off state from the loan's LATEST read-back.

    `charged_off_latest` = the `chargedOff` flag there; `chargeoffs` = the
    non-reversed `chargeOff` loan transactions listed THERE (an undone
    charge-off is gone from the latest read-back and so never counts).  A leg is
    charged off when the flag is true and the latest read-back lists a chargeOff
    with an EARLIER date, or the same date and a lower id.
    """
    latest = latest_transaction_readback(loan_id, lines)
    if latest is None:
        return {'charged_off_latest': None, 'chargeoffs': []}
    _, rel, body = latest
    cos = []
    for t in body.get('transactions') or []:
        if (t.get('type') or {}).get('code') != 'loanTransactionType.chargeOff':
            continue
        if bool(t.get('manuallyReversed')) or bool(t.get('reversed')):
            continue
        if t.get('id') is None:
            continue
        cos.append({'transaction_id': t.get('id'), 'date': t.get('date')})
    return {
        'charged_off_latest': bool(body.get('chargedOff')),
        'latest_readback': rel,
        'chargeoffs': sorted(cos, key=lambda c: c['transaction_id']),
    }


def is_charged_off(date, tx_id, state):
    if not state.get('charged_off_latest') or not date or tx_id is None:
        return False, []
    hit = []
    for c in state.get('chargeoffs', []):
        cd = c.get('date')
        cid = c.get('transaction_id')
        if cd and (list(cd) < list(date)
                   or (list(cd) == list(date) and cid < tx_id)):
            hit.append(cid)
    return bool(hit), hit


def reamortize_calls(loan_id, lines):
    """Captured reAmortize calls for the loan, split into SUCCESSFUL calls (the
    response carries a `resourceId`) and REJECTED attempts (a domain-rule
    response with `errors`, e.g. `error.msg.loan.reamortize.not.allowed.on.
    charged.off`).  Only a successful call rewrites the schedule, so only its
    source line is a phase boundary."""
    files = loan_files(loan_id)
    ok, rejected = [], []
    for base in sorted(files):
        if 'reAmortize' not in base or 'response' not in base or not base.endswith('.json'):
            continue
        path = files[base]
        try:
            body = json.load(open(path))
        except ValueError:
            continue
        rec = {'source_line': lines.get((loan_id, base), 0),
               'file': os.path.relpath(path, HERE)}
        if isinstance(body, dict) and isinstance(body.get('resourceId'), int) \
                and not body.get('errors'):
            rec['transaction_id'] = 'L%d' % body['resourceId']
            ok.append(rec)
        else:
            errs = []
            if isinstance(body, dict):
                for e in body.get('errors') or []:
                    errs.append(e.get('userMessageGlobalisationCode')
                                or e.get('developerMessage'))
                rec['http_status'] = body.get('httpStatusCode')
            rec['reason'] = '; '.join(x for x in errs if x) or 'no resourceId in response'
            rejected.append(rec)
    ok.sort(key=lambda r: (r['source_line'], r['file']))
    rejected.sort(key=lambda r: (r['source_line'], r['file']))
    return ok, rejected


def schedule_entries(loan_id, lines):
    """Every read-back of the loan that carries a `periods` array, with its
    source line, periods count, a sha256 of the periods array, and the phase
    relative to each SUCCESSFUL reAmortize call."""
    ok, _ = reamortize_calls(loan_id, lines)
    boundaries = sorted({r['source_line'] for r in ok})
    rows = []
    for line, rel, body in readbacks(loan_id, lines):
        rs = body.get('repaymentSchedule')
        if not isinstance(rs, dict) or not isinstance(rs.get('periods'), list):
            continue
        periods = rs['periods']
        raw = json.dumps(periods, sort_keys=True).encode()
        base = os.path.basename(rel)
        if 'detail-associations-all' in base:
            kind = 'associations-all'
        elif 'repaymentSchedule' in base:
            kind = 'associations-repaymentSchedule'
        else:
            kind = 'other'
        if not boundaries:
            phase = 'no-reAmortize'
        else:
            k = sum(1 for b in boundaries if b < line)
            phase = 'before-reAmortize' if k == 0 else 'after-reAmortize-%d' % k
        rows.append({
            'file': rel,
            'source_line': line,
            'kind': kind,
            'periods': len(periods),
            'periods_sha256': hashlib.sha256(raw).hexdigest(),
            'phase': phase,
        })
    rows.sort(key=lambda r: (r['source_line'], r['file']))
    return boundaries, rows


def detail_currency(loan_id, lines):
    for _, _, body in readbacks(loan_id, lines):
        if isinstance(body.get('currency'), dict):
            return body['currency'].get('code')
    return None


def shape_key(legs):
    return ' '.join('%s:%s' % (l['entry_type'], l['gl_account_id'])
                    for l in sorted(legs, key=lambda r: (r['entry_type'] or '',
                                                         r['gl_account_id'] or 0)))


def build_targets(types, txmaps, charged, currencies):
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
        state = charged.get(lid, {})
        for tid in sorted(txmaps[lid]):
            tx = txmaps[lid][tid]
            if tx.get('code') not in TARGET_TYPES:
                continue
            co, hits = is_charged_off(tx.get('date'), tid, state)
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
                'charged_off': co,
                'charged_off_latest': state.get('charged_off_latest'),
                'chargeoff_tx_ids': ['L%d' % c for c in hits],
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
        findings.append('target type(s) with NO journal-entry legs at all: %s.  The '
                        're-amortization command succeeds and rewrites the schedule, '
                        'but the reAmortize transaction itself posts no journal entry.'
                        % ', '.join(empty))
    no_legs = [t for t in target_transactions if not t['legs']]
    if no_legs:
        findings.append('%d target transaction(s) in the read-backs have NO '
                        'journal-entry legs: %s.'
                        % (len(no_legs),
                           ', '.join('loan %d tx %s' % (t['loan'], t['transaction_id'])
                                     for t in no_legs)))
    if not any(state.get('chargeoffs') for state in charged.values()):
        findings.append('no non-reversed `chargeOff` loan transaction appears in ANY '
                        "loan's LATEST read-back: no leg is on a charged-off loan.")
    if not any(state.get('charged_off_latest') for state in charged.values()):
        findings.append('no loan\'s LATEST read-back has `chargedOff=true`: the '
                        'charged-off dimension is empty (every leg charged-off=no).')
    return {
        'charged_off_rule': ('a NON-REVERSED chargeOff loan transaction, listed in the '
                             "loan's LATEST read-back, with an EARLIER transaction DATE "
                             "than the leg's transaction, or the SAME date and a LOWER id"),
        'target_types': list(TARGET_TYPES),
        'by_type': by_type,
        'currencies': currencies,
        'total_legs': len(all_legs),
        'total_transactions': len(target_transactions),
        'total_loans': sorted({r['loan'] for r in all_legs}),
        'transactions': target_transactions,
        'transactions_without_legs': no_legs,
        'empty_types': empty,
        'findings': findings,
    }


def write_md(obj):
    tg = obj['targets']
    out = []
    w = out.append
    w('# Journal-entry type join — re-amortization arms (OH-TIERD30-DR step 6)')
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
    w('## Repayment schedules before/after each re-amortization')
    w('')
    for lid in obj['loan_ids']:
        ev = obj['reamortize_events'].get(str(lid), {})
        w('### loan %d — %s' % (lid, obj['currencies'].get(str(lid), 'UNKNOWN')))
        w('')
        w('reAmortize calls (source line): %s; reAmortize transactions: %s'
          % (', '.join(str(x) for x in ev.get('command_source_lines', [])) or '-',
             ', '.join('%s@%s' % (t['transaction_id'], date_str(t['date']))
                       for t in ev.get('transactions', [])) or '-'))
        rej = ev.get('rejected_calls', [])
        if rej:
            w('')
            w('REJECTED reAmortize attempt(s): %s'
              % '; '.join('%s r%d (%s)' % (r['file'], r.get('http_status') or 0,
                                           r.get('reason'))
                          for r in rej))
        w('')
        rows = obj['schedules'].get(str(lid), [])
        if not rows:
            w('_no read-back carries a `periods` array._')
            w('')
            continue
        w('| read-back file | source line | kind | periods | periods sha256 | phase |')
        w('| --- | ---: | --- | ---: | --- | --- |')
        for r in rows:
            w('| `%s` | %d | %s | %d | `%s` | %s |' % (
                r['file'], r['source_line'], r['kind'], r['periods'],
                r['periods_sha256'][:16], r['phase']))
        w('')
    with open(os.path.join(HERE, 'journalentry-type-join.md'), 'w') as f:
        f.write('\n'.join(out) + '\n')


def main():
    lines = load_manifest_lines()
    manifest = json.load(open(os.path.join(HERE, 'journalentries-sweep-manifest.json')))
    loan_ids = sorted(m['loan_id'] for m in manifest)
    txmaps = {lid: tx_map_for(lid, lines) for lid in loan_ids}
    charged = {lid: charged_off_state(lid, lines) for lid in loan_ids}

    currencies = {}
    leg_records = []
    unmatched = []
    loan_chargeoff = {}
    schedules = {}
    reamort_events = {}
    for lid in loan_ids:
        state = charged[lid]
        loan_chargeoff[lid] = state
        ok_calls, rejected_calls = reamortize_calls(lid, lines)
        boundaries, rows = schedule_entries(lid, lines)
        schedules[lid] = rows
        reamort_events[lid] = {
            'command_source_lines': sorted({r['source_line'] for r in ok_calls}),
            'calls': ok_calls,
            'rejected_calls': rejected_calls,
            'transactions': [
                {'transaction_id': 'L%d' % tid, 'date': txmaps[lid][tid].get('date'),
                 'type_code': txmaps[lid][tid].get('code')}
                for tid in sorted(txmaps[lid])
                if txmaps[lid][tid].get('code') == REAMORT
            ],
        }

        path = os.path.join(SWEEP, 'loan-%d.json' % lid)
        if not os.path.exists(path):
            continue
        body = json.load(open(path))
        items = body.get('pageItems') or []
        cur = next((it.get('currency', {}).get('code') for it in items
                    if it.get('currency')), None)
        currencies[lid] = cur or detail_currency(lid, lines) or 'UNKNOWN'
        for it in items:
            label = it.get('transactionId')
            n = int(label[1:]) if isinstance(label, str) and label.startswith('L') \
                and label[1:].isdigit() else None
            tx = txmaps.get(lid, {}).get(n)
            if tx is None:
                unmatched.append({'loan': lid, 'transaction_id': label,
                                  'file': 'journalentries-sweep/loan-%d.json' % lid})
            co, hits = is_charged_off(tx.get('date') if tx else None, n, state)
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
                'charged_off': co,
                'charged_off_latest': state.get('charged_off_latest'),
                'chargeoff_tx_ids': ['L%d' % c for c in hits],
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

    tg = build_targets(types, txmaps, charged, currencies)
    obj = {
        'tenant': 'tierd',
        'source': 'GET /journalentries?loanId=<id>&limit=-1 on the throwaway (8444)',
        'loan_ids': loan_ids,
        'currencies': currencies,
        'legs': len(leg_records),
        'unmatched_legs': unmatched,
        'loan_chargeoff': loan_chargeoff,
        'schedules': schedules,
        'reamortize_events': reamort_events,
        'targets': tg,
        'types': types,
    }
    with open(os.path.join(HERE, 'journalentry-type-join.json'), 'w') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write('\n')
    write_md(obj)
    n_sched = sum(len(v) for v in schedules.values())
    print('joined %d legs across %d types; %d unmatched; target legs %d on %d '
          'transactions / %d loans; empty target types %s; schedule bodies %d'
          % (len(leg_records), len(types), len(unmatched), tg['total_legs'],
             tg['total_transactions'], len(tg['total_loans']),
             ','.join(tg['empty_types']) or 'none', n_sched))


if __name__ == '__main__':
    main()
