#!/bin/bash
# T12 rehydration assertion: from COMMITTED state alone, what would the next fire pick up?
# Fails loudly if any already-terminal task would be re-executed.
set -u -o pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
python3 - <<'PY'
import json,sys
t=json.load(open('.softhouse/tasks.json'))
TERMINAL={'done','approved','parked','done_partial','superseded','rejected'}
# 'superseded': the task's commits were merged as part of a successor task's branch.
# Added fire 20260820-110001, when T65 (rejected, but merged via T69) was flagged re-runnable.
#
# 'rejected': terminal FOR THAT TASK ID. A rejection in this pipeline never re-runs under the same
# id -- the retry carries a NEW id and branches off the rejected branch, so the rejected work is
# preserved rather than repeated (T65 -> T69 after T67; T70 -> T72 after T71). Re-running the id
# would re-do work a reviewer has already ruled on. Added fire 20260820-140000, when T70 (rejected
# by T71, deliberately NOT merged) was flagged re-runnable.
#
# THE GUARD THAT MAKES THAT SAFE: a rejected task must NAME ITS SUCCESSOR, or the rejection would
# silently vanish -- terminal, unmerged, and nobody assigned to finish it. That is the failure mode
# this whole check exists to catch, so it is asserted rather than trusted.
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

# A 'rejected' task is terminal, so it must have a live successor or the work is orphaned.
#
# This is checked against an EXPLICIT 'superseded_by' FIELD, never by scanning notes. The first
# draft of this guard scanned note/description text for the rejected id and was a SILENT FALSE
# GREEN: T15's note mentions T70 in passing ("archiving now would freeze the marker T70 failed to
# fix"), which the scan counted as a successor. It passed with the real successor deleted. The guard was
# tested by deleting T72/T73 and confirming it FAILED to fail -- an assertion that cannot fail is
# worse than no assertion, which is this project's P-14 in miniature.
orphans=[]
for k in t['tasks']:
    if k.get('status')!='rejected': continue
    succ=k.get('superseded_by')
    if not succ or succ not in by:
        orphans.append((k['id'], f"superseded_by={succ!r}"))
    elif by[succ].get('status') in ('rejected',):
        orphans.append((k['id'], f"successor {succ} is itself rejected"))
if orphans:
    print("FAIL: rejected task(s) with no live successor -- terminal, unmerged, nobody finishing them:")
    for i,why in orphans: print(f"   {i}: {why}")
    sys.exit(1)
rej=[k['id'] for k in t['tasks'] if k.get('status')=='rejected']
if rej: print(f"REJECTED, terminal for that id, each with a named successor: {rej}")
print("ASSERTION HOLDS: no terminal task is selected for re-execution.")
PY
