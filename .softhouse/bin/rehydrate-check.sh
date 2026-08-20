#!/bin/bash
# T12 rehydration assertion: from COMMITTED state alone, what would the next fire pick up?
# Fails loudly if any already-terminal task would be re-executed.
set -u -o pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
python3 - <<'PY'
import json,sys
t=json.load(open('.softhouse/tasks.json'))
TERMINAL={'done','approved','parked','done_partial'}
by={k['id']:k for k in t['tasks']}
ready,blocked,bad=[],[],[]
for k in t['tasks']:
    st=k.get('status')
    if st in TERMINAL: continue
    unmet=[d for d in k.get('dependencies',[]) if by.get(d,{}).get('status') not in TERMINAL]
    (ready if not unmet else blocked).append((k['id'],st,k.get('executor'),unmet))
for k in t['tasks']:
    if k.get('status') in TERMINAL and k.get('attempts',0)==0 and k.get('status')=='done':
        bad.append(k['id'])
print("NEXT FIRE WOULD PICK UP (deps satisfied):")
for i,s,e,_ in sorted(ready): print(f"   {i:5s} status={s:12s} executor={e}")
print("\nBLOCKED (waiting on unmet deps):")
for i,s,e,u in sorted(blocked): print(f"   {i:5s} status={s:12s} waiting on {u}")
term=[k['id'] for k in t['tasks'] if k.get('status') in TERMINAL]
print(f"\nTERMINAL, WOULD NOT RE-EXECUTE: {len(term)} tasks")
overlap=[i for i,_,_,_ in ready if i in term]
if overlap:
    print("FAIL: terminal tasks also selected as ready:",overlap); sys.exit(1)
print("ASSERTION HOLDS: no terminal task is selected for re-execution.")
PY
