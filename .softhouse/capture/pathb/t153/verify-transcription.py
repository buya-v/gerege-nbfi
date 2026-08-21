#!/usr/bin/env python3
"""T153 — check every `expect` cell of T149-PATHB-TIE against T153's OWN capture.

The reviewer did not take T149's capture on report. `out/t153-gerege-p9-raw.json`
is a request this task issued itself against the running reference oracle on tenant
`gerege`, and it came back byte-identical to T149's committed
`t149/out/gerege/T149-TIE-P9-raw.json`
(sha256 `39f56dc2c94a6da59235af7d0ecb7d51548bcf3f4d52730a94c864d7f65a3d25`).

This script asserts, cell by cell, that:

  * every recorded cell in the vector is the EXACT TEXT of a value present in that
    response, scaled major -> minor by integer/string arithmetic only (no float,
    `parse_float=str` throughout);
  * every cell the vector lists in `unrecorded_fields` really is ABSENT from the
    response — a withdrawal of a cell the oracle did emit would be a hidden
    ungraded cell, which is the whole hazard the field exists to make visible;
  * `from_date` in particular is withdrawn on the disbursement row because Path B
    emits no `fromDate` there, not because it was inconvenient.

    python3 verify-transcription.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
VEC = os.path.join(REPO, '.softhouse', 'vectors', 'loanschedule',
                   'T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json')
RAW = os.path.join(HERE, 'out', 't153-gerege-p9-raw.json')


def minor(text, digits=2):
    """Exact major-unit decimal TEXT -> integer minor-unit string. Never float."""
    t = str(text)
    neg = t.startswith('-')
    t = t.lstrip('-')
    whole, _, frac = t.partition('.')
    if len(frac) > digits and frac[digits:].strip('0'):
        raise ValueError('more precision than the currency has: %r' % text)
    frac = frac[:digits].ljust(digits, '0')
    s = ((whole or '0') + frac).lstrip('0') or '0'
    return ('-' if neg else '') + s


def date_of(d):
    return [d['year'], d['month'], d['day']]


def main():
    vec = json.load(open(VEC), parse_float=str)
    raw = json.load(open(RAW), parse_float=str)
    expect, periods = vec['expect']['periods'], raw['periods']
    print('vector rows %d   response rows %d' % (len(expect), len(periods)))
    if len(expect) != len(periods):
        sys.exit('ROW COUNT DIFFERS')

    bad = []
    for i, (e, x) in enumerate(zip(expect, periods)):
        withdrawn = set(e.get('unrecorded_fields') or [])

        if date_of(e['due_date']) != x['dueDate']:
            bad.append((i, 'due_date', e['due_date'], x['dueDate']))

        if 'from_date' in withdrawn:
            if 'fromDate' in x:
                bad.append((i, 'from_date', 'WITHDRAWN but the oracle emitted it', x['fromDate']))
        elif 'fromDate' not in x:
            bad.append((i, 'from_date', 'recorded but ABSENT from the response', None))
        elif date_of(e['from_date']) != x['fromDate']:
            bad.append((i, 'from_date', e['from_date'], x['fromDate']))

        praw = x.get('principalDisbursed') if e['kind'] == 'DISBURSEMENT' else x.get('principalOriginalDue')
        if e['principal_minor'] != minor(praw):
            bad.append((i, 'principal_minor', e['principal_minor'], praw))
        if e.get('principal_major_text') and str(praw) != e['principal_major_text']:
            bad.append((i, 'principal_major_text', e['principal_major_text'], praw))

        if 'interest_minor' in withdrawn:
            if x.get('interestOriginalDue') is not None:
                bad.append((i, 'interest_minor', 'WITHDRAWN but the oracle emitted it',
                            x['interestOriginalDue']))
        else:
            iraw = x.get('interestOriginalDue')
            if e['interest_minor'] != minor(iraw):
                bad.append((i, 'interest_minor', e['interest_minor'], iraw))
            if e.get('interest_major_text') and str(iraw) != e['interest_major_text']:
                bad.append((i, 'interest_major_text', e['interest_major_text'], iraw))

        oraw = x.get('principalLoanBalanceOutstanding')
        if e['outstanding_principal_minor'] != minor(oraw):
            bad.append((i, 'outstanding_principal_minor', e['outstanding_principal_minor'], oraw))
        if e.get('outstanding_principal_major_text') and str(oraw) != e['outstanding_principal_major_text']:
            bad.append((i, 'outstanding_principal_major_text',
                        e['outstanding_principal_major_text'], oraw))

        if e.get('observed_total_due_minor') is not None:
            traw = x.get('totalOriginalDueForPeriod')
            if e['observed_total_due_minor'] != minor(traw):
                bad.append((i, 'observed_total_due_minor', e['observed_total_due_minor'], traw))

        if 'installment_number' in withdrawn:
            if 'period' in x:
                bad.append((i, 'installment_number', 'WITHDRAWN but the oracle emitted it', x['period']))
        elif e['installment_number'] != x.get('period'):
            bad.append((i, 'installment_number', e['installment_number'], x.get('period')))

    ti = vec['expect']['observed_total_interest_minor']
    if ti != minor(raw['totalInterestCharged']):
        bad.append(('-', 'observed_total_interest_minor', ti, raw['totalInterestCharged']))

    print('MISMATCHES: %d' % len(bad))
    for b in bad:
        print('  ', b)
    if bad:
        sys.exit(1)

    reps = [e for e in expect if e['kind'] == 'REPAYMENT']
    print('invariants re-derived from the vector alone:')
    print('  sum(principal_minor)        = %d   disbursed = %s'
          % (sum(int(e['principal_minor']) for e in reps), expect[0]['principal_minor']))
    print('  sum(interest_minor)         = %d   declared total = %s'
          % (sum(int(e['interest_minor']) for e in reps), ti))
    print('  final outstanding_principal = %s' % reps[-1]['outstanding_principal_minor'])
    off = [e['installment_number'] for e in reps
           if int(e['principal_minor']) + int(e['interest_minor']) != int(e['observed_total_due_minor'])]
    print('  rows where principal + interest != total_due: %s' % (off or 'none'))
    print()
    print('EVERY recorded cell is the exact text the oracle emitted, and every withdrawn')
    print('cell is genuinely absent from the response.')


if __name__ == '__main__':
    main()
