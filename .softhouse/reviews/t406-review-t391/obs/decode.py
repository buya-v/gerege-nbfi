#!/usr/bin/env python3
# T406 independent re-derivation. Reads the raw oracle bytes with parse_float=str so
# nothing is ever decoded through a float. Minor units are computed by INTEGER string
# surgery on the two decimal places, never by multiplication of a float.
import json
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))


def to_minor(text):
    """major-unit decimal TEXT -> integer minor units, MNT minor_unit_digits=2.
    Pure integer/string work. Refuses any non-zero digit beyond the 2nd decimal."""
    neg = text.startswith('-')
    if neg:
        text = text[1:]
    if '.' in text:
        whole, frac = text.split('.', 1)
    else:
        whole, frac = text, ''
    tail = frac[2:]
    if tail.strip('0') != '':
        raise SystemExit('NON-ZERO THIRD DECIMAL in %r' % text)
    frac2 = (frac + '00')[:2]
    v = int(whole) * 100 + int(frac2)
    return -v if neg else v


for T in ('L29', 'L30', 'L32'):
    p = os.path.join(BASE, 'R02-je-%s.json' % T)
    d = json.load(open(p), parse_float=str, parse_int=str)
    items = d['pageItems'] if isinstance(d, dict) else d
    print('===', T, 'items', len(items))
    tot = {'DEBIT': 0, 'CREDIT': 0}
    for e in items:
        amt = e['amount']
        m = to_minor(amt)
        side = e['entryType']['value']
        tot[side] += m
        td = e.get('transactionDetails') or {}
        tt = (td.get('transactionType') or {}).get('id')
        print('  je=%s gl=%s code=%s side=%-6s amount_text=%r minor=%d manual=%s txType=%s glType=%s'
              % (e['id'], e['glAccountId'], e['glAccountCode'], side, amt, m,
                 e['manualEntry'], tt, e['glAccountType']['value']))
    print('  total_debits_minor=%d total_credits_minor=%d balanced=%s'
          % (tot['DEBIT'], tot['CREDIT'], tot['DEBIT'] == tot['CREDIT']))
