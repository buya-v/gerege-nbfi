#!/usr/bin/env python3
"""T406: cross-check EVERY graded cell of each promoted vector against a LIVE
oracle observation taken by T406 itself, and against the LIVE acc_product_mapping.

Nothing here reads T391's capture artefacts. The oracle GET bodies were fetched by
T406 (obs/R02-je-*.json) and the mapping by T406 (obs/R04-product63-mapping.txt).
All decimals are handled as TEXT; minor units by integer string surgery.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REV = os.path.dirname(BASE)

# The slot -> name decode, transcribed BY HAND from the pinned Fineract source
# AccountingConstants.AccrualAccountsForLoan (426a23544, lines 95-122). Not from the port.
ACCRUAL = {
    1: 'FUND_SOURCE', 2: 'LOAN_PORTFOLIO', 3: 'INTEREST_ON_LOANS',
    4: 'INCOME_FROM_FEES', 5: 'INCOME_FROM_PENALTIES', 6: 'LOSSES_WRITTEN_OFF',
    7: 'INTEREST_RECEIVABLE', 8: 'FEES_RECEIVABLE', 9: 'PENALTIES_RECEIVABLE',
    10: 'TRANSFERS_SUSPENSE', 11: 'OVERPAYMENT', 12: 'INCOME_FROM_RECOVERY',
    13: 'GOODWILL_CREDIT',
}


def to_minor(text):
    neg = text.startswith('-')
    if neg:
        text = text[1:]
    whole, _, frac = text.partition('.')
    if frac[2:].strip('0'):
        raise SystemExit('NON-ZERO THIRD DECIMAL: %r' % text)
    v = int(whole) * 100 + int((frac + '00')[:2])
    return -v if neg else v


# live mapping, slot -> (account_id, gl_code)
mapping = {}
for line in open(os.path.join(BASE, 'R04-product63-mapping.txt')):
    line = line.rstrip('\n')
    if not line:
        continue
    f = line.split('|')
    mapping[int(f[2])] = (int(f[3]), f[4])

CASES = [
    ('LDG-ACC-01', 'L29'),
    ('LDG-ACC-02', 'L30'),
    ('LDG-ACC-03', 'L32'),
]

fails = 0
for name, txn in CASES:
    v = json.load(open(os.path.join(REV, 'vectors', name + '.json')),
                  parse_float=str, parse_int=str)
    o = json.load(open(os.path.join(BASE, 'R02-je-%s.json' % txn)),
                  parse_float=str, parse_int=str)
    items = o['pageItems']
    print('=' * 78)
    print(name, txn)

    # the request's mapping table must equal the LIVE mapping table, whole
    rq = {int(m['slot_code']): int(m['gl_account_id']) for m in v['request']['product_mappings']}
    live = {k: t[0] for k, t in mapping.items()}
    ok = rq == live
    print('  request.product_mappings == LIVE acc_product_mapping(63): %s (%d rows)'
          % (ok, len(rq)))
    fails += 0 if ok else 1

    rlegs = v['request']['legs']
    elegs = v['expect']['legs']
    assert len(rlegs) == len(elegs) == len(items), 'leg count'

    td = tc = 0
    for i, (rl, el, it) in enumerate(zip(rlegs, elegs, items)):
        slot = int(rl['slot_code'])
        acct_id_req = int(rl['gl_account_id'])
        # 1. request leg must carry a slot and NO account id
        c_noacct = (acct_id_req == 0 and slot != 0)
        # 2. amount text in the request must be the oracle's own characters
        c_amt_req = (rl['amount_major_text'] == it['amount'])
        # 3. side
        c_side = (rl['entry_side'] == it['entryType']['value'] == el['entry_side'])
        # 4. expected account id / code resolve from LIVE mapping by SLOT
        res_id, res_code = mapping[slot]
        c_res_id = (int(el['gl_account_id']) == res_id == int(it['glAccountId']))
        c_res_code = (el['gl_account_code'] == res_code == it['glAccountCode'])
        # 5. expected slot name from the HAND-TRANSCRIBED accrual enum
        c_slot = (el['slot_name'] == ACCRUAL[slot])
        # 6. money cell: minor units from the ORACLE characters
        m = to_minor(it['amount'])
        c_minor = (int(el['amount_minor']) == m)
        c_major = (el['amount_major_text'] == it['amount'])
        if el['entry_side'] == 'DEBIT':
            td += m
        else:
            tc += m
        allok = all([c_noacct, c_amt_req, c_side, c_res_id, c_res_code, c_slot,
                     c_minor, c_major])
        fails += 0 if allok else 1
        print('  leg[%d] slot=%-2d %-22s gl=%-3d %-9s %-6s %-14s minor=%-8d %s'
              % (i, slot, el['slot_name'], res_id, res_code, el['entry_side'],
                 it['amount'], m, 'OK' if allok else 'MISMATCH'))
        if not allok:
            print('      noacct=%s amtreq=%s side=%s resid=%s rescode=%s slot=%s minor=%s major=%s'
                  % (c_noacct, c_amt_req, c_side, c_res_id, c_res_code, c_slot,
                     c_minor, c_major))

    c_td = int(v['expect']['total_debits_minor']) == td
    c_tc = int(v['expect']['total_credits_minor']) == tc
    c_bal = td == tc
    fails += 0 if (c_td and c_tc and c_bal) else 1
    print('  total_debits_minor  vector=%s  T406=%d  %s'
          % (v['expect']['total_debits_minor'], td, 'OK' if c_td else 'MISMATCH'))
    print('  total_credits_minor vector=%s  T406=%d  %s'
          % (v['expect']['total_credits_minor'], tc, 'OK' if c_tc else 'MISMATCH'))
    print('  double-entry balanced: %s' % c_bal)
    # entry-level slot_code must be 0 where per-leg codes are used
    print('  request.slot_code (entry level) = %s (must be 0)' % v['request']['slot_code'])
    fails += 0 if str(v['request']['slot_code']) == '0' else 1

print('=' * 78)
print('T406 CROSS-CHECK MISMATCHES: %d' % fails)
sys.exit(1 if fails else 0)
