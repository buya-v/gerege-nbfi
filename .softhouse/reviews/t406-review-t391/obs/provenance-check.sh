#!/bin/bash
# T406: (1) every vector's provenance digests must match the artefacts it cites;
#       (2) the rig MANIFEST.sha256 must verify;
#       (3) each cited capture body must equal, cell for cell, what T406 fetched
#           LIVE from the oracle today -- so the artefact is not a stale snapshot;
#       (4) every amount token must occur TOKEN-BOUNDED in the cited artefact
#           (T397's matcher), checked directly and not only via the bar.
set -u
T=/tmp/t406-t391
cd "$T" || exit 1

echo "=== 1. provenance digests ==="
python3 - <<'PY'
import json, hashlib, os
T='/tmp/t406-t391'
for name in ('LDG-ACC-01-accrual-six-slots-runaccruals-trigger',
             'LDG-ACC-02-accrual-six-slots-minor-unit-residue',
             'LDG-ACC-03-accrual-six-slots-scheduled-job'):
    v=json.load(open(os.path.join(T,'.softhouse/vectors/ledger',name+'.json')),parse_float=str)
    p=v['provenance']
    for refk,shak in (('capture_ref','capture_sha256'),('request_capture_ref','request_capture_sha256')):
        ref=p.get(refk); want=p.get(shak)
        if not ref: continue
        got=hashlib.sha256(open(os.path.join(T,ref),'rb').read()).hexdigest()
        print('  %-14s %-58s %s' % (name[:14], os.path.basename(ref), 'MATCH' if got==want else 'MISMATCH want=%s got=%s'%(want,got)))
PY

echo
echo "=== 2. rig MANIFEST.sha256 ==="
( cd .softhouse/capture/t391-accrual-promotion && shasum -a 256 -c MANIFEST.sha256 2>&1 | grep -v ': OK$' | head -20; \
  echo "  files in manifest: $(wc -l < MANIFEST.sha256 | tr -d ' ')"; \
  echo "  FAILED lines: $(shasum -a 256 -c MANIFEST.sha256 2>/dev/null | grep -c 'FAILED')" )

echo
echo "=== 3. cited capture bodies vs T406's OWN live fetch, value by value ==="
python3 - <<'PY'
import json, os
T='/tmp/t406-t391'
REV='/Users/buv/gerege-nbfi/.claude/worktrees/agent-a29ead654f5e65674/.softhouse/reviews/t406-review-t391/obs'
pairs=[('T391-A01-je-L29.json','R02-je-L29.json'),
       ('T391-A02-je-L30.json','R02-je-L30.json'),
       ('T391-A04-je-L32.json','R02-je-L32.json')]
for cap,mine in pairs:
    a=json.load(open(os.path.join(T,'.softhouse/capture/t391-accrual-promotion/out',cap)),parse_float=str,parse_int=str)
    b=json.load(open(os.path.join(REV,mine)),parse_float=str,parse_int=str)
    ka=[(e['id'],e['glAccountId'],e['glAccountCode'],e['entryType']['value'],e['amount'],e['manualEntry']) for e in a['pageItems']]
    kb=[(e['id'],e['glAccountId'],e['glAccountCode'],e['entryType']['value'],e['amount'],e['manualEntry']) for e in b['pageItems']]
    print('  %-26s graded projection identical to T406 live fetch: %s' % (cap, ka==kb))
    if ka!=kb:
        print('    committed:',ka); print('    live     :',kb)
PY

echo
echo "=== 4. TOKEN-BOUNDED occurrence of every amount token in its cited artefact ==="
python3 - <<'PY'
import json, os, re
T='/tmp/t406-t391'
NEIGH_L=set('0123456789.+-'); NEIGH_R=set('0123456789.eE')
def token_bounded(hay, needle):
    i=0
    while True:
        i=hay.find(needle,i)
        if i<0: return False
        l = hay[i-1] if i>0 else ''
        r = hay[i+len(needle)] if i+len(needle)<len(hay) else ''
        if l not in NEIGH_L and r not in NEIGH_R: return True
        i+=1
for name in ('LDG-ACC-01-accrual-six-slots-runaccruals-trigger',
             'LDG-ACC-02-accrual-six-slots-minor-unit-residue',
             'LDG-ACC-03-accrual-six-slots-scheduled-job'):
    v=json.load(open(os.path.join(T,'.softhouse/vectors/ledger',name+'.json')),parse_float=str)
    raw=open(os.path.join(T,v['provenance']['capture_ref'])).read()
    toks=sorted({l['amount_major_text'] for l in v['expect']['legs']})
    for t in toks:
        print('  %-14s %-14s bare_substring=%-5s token_bounded=%s'
              % (name[:14], t, str(t in raw), token_bounded(raw,t)))
PY
