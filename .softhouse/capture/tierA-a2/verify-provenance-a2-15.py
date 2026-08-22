#!/usr/bin/env python3
"""A2-15 byte-provenance verification.

P-46: quote captures by EXTRACTION, and check every quoted string against the
cited capture. This re-opens each promoted vector, re-reads the artefact it
cites, and asserts that every promoted major-unit text is BYTE-PRESENT in those
bytes, and that every promoted minor-unit integer follows from that text by
exact string arithmetic.

It is an INDEPENDENT program from the one that wrote the vectors: it re-derives
rather than re-uses.
"""
import glob
import hashlib
import json
import os
import sys

ROOT = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-a698351e28b6ea99d'
bad = 0
rows = []

for p in sorted(glob.glob(os.path.join(ROOT, '.softhouse/vectors/ledger/*.json'))):
    v = json.load(open(p))
    cid = v['case_id']
    prov = v['provenance']
    for label, ref, want in (('response', prov['capture_ref'], prov['capture_sha256']),
                             ('request', prov['request_capture_ref'],
                              prov['request_capture_sha256'])):
        ap = os.path.join(ROOT, ref)
        if not os.path.isfile(ap):
            print('MISSING %s %s %s' % (cid, label, ref)); bad += 1; continue
        raw = open(ap, 'rb').read()
        got = hashlib.sha256(raw).hexdigest()
        if got != want:
            print('DIGEST MISMATCH %s %s %s' % (cid, label, ref)); bad += 1

    resp = open(os.path.join(ROOT, prov['capture_ref']), 'rb').read().decode('utf-8')
    req = open(os.path.join(ROOT, prov['request_capture_ref']), 'rb').read().decode('utf-8')

    # Every promoted money text must be byte-present in the RESPONSE artefact,
    # and every promoted minor-unit integer must follow from it exactly.
    for i, leg in enumerate(v['expect']['legs']):
        txt = leg['amount_major_text']
        if txt not in resp:
            print('NOT BYTE-PRESENT %s legs[%d] %r not in %s'
                  % (cid, i, txt, prov['capture_ref'])); bad += 1
        ip, _, fr = txt.partition('.')
        keep, rest = fr[:2], fr[2:]
        if rest.strip('0'):
            print('RESIDUE %s legs[%d] %r' % (cid, i, txt)); bad += 1
        expect_minor = str(int(ip + (keep + '00')[:2]))
        if expect_minor != leg['amount_minor']:
            print('MINOR MISMATCH %s legs[%d] %r -> %s, vector says %s'
                  % (cid, i, txt, expect_minor, leg['amount_minor'])); bad += 1
        if str(leg['gl_account_id']) not in resp:
            print('ACCOUNT ID NOT PRESENT %s legs[%d]' % (cid, i)); bad += 1
        if leg['gl_account_code'] not in resp:
            print('GL CODE NOT PRESENT %s legs[%d] %s' % (cid, i, leg['gl_account_code']))
            bad += 1

    # The requested transaction amount, where the vector carries one, must be
    # byte-present in the REQUEST artefact.
    tam = v['request'].get('transaction_amount_major_text', '')
    if tam and ('"transactionAmount": %s' % tam) not in req and tam not in req:
        print('TXN AMOUNT NOT PRESENT %s %r not in %s' % (cid, tam, prov['request_capture_ref']))
        bad += 1

    # A refusal's code and message must be byte-present in the response artefact.
    if v['expect']['kind'] == 'refusal':
        for field in ('code', 'message'):
            val = v['expect']['refusal'][field]
            if val not in resp:
                print('REFUSAL %s NOT PRESENT %s %r' % (field, cid, val)); bad += 1
        if ('"httpStatusCode":"%d"' % v['expect']['refusal']['http_status']) not in resp.replace(' ', ''):
            print('REFUSAL STATUS NOT PRESENT %s' % cid); bad += 1

    debits = [l for l in v['expect']['legs'] if l['entry_side'] == 'DEBIT']
    credits = [l for l in v['expect']['legs'] if l['entry_side'] == 'CREDIT']
    minor_units = sum(int(l['amount_minor']) for l in v['expect']['legs'])
    rows.append((cid, v['class'], v['oracle']['seam'], len(v['expect']['legs']),
                 len(debits), len(credits),
                 sum(1 for l in v['expect']['legs'] if int(l['amount_minor']) % 100 != 0),
                 prov['capture_ref'].split('/')[-1],
                 prov['request_capture_ref'].split('/')[-1]))

print()
print('%-48s %-15s %-20s %4s %3s %3s %6s' %
      ('case_id', 'class', 'seam', 'legs', 'DR', 'CR', 'minor'))
tot_legs = tot_minor = 0
for r in rows:
    print('%-48s %-15s %-20s %4d %3d %3d %6d' % r[:7])
    tot_legs += r[3]
    tot_minor += r[6]
print()
print('CENSUS: %d vectors, %d legs total, %d promoted money cells carry NON-ZERO MINOR UNITS'
      % (len(rows), tot_legs, tot_minor))
print('LEG-COUNT DISTRIBUTION of the promoted set: ' +
      ', '.join('%d legs x%d' % (n, sum(1 for r in rows if r[3] == n))
                for n in sorted({r[3] for r in rows})))
print()
print('%-48s %-42s %s' % ('case_id', 'response artefact', 'request artefact'))
for r in rows:
    print('%-48s %-42s %s' % (r[0], r[7], r[8]))
print()
print('BYTE-PROVENANCE FAILURES: %d' % bad)
sys.exit(1 if bad else 0)
