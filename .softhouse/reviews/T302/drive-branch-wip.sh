#!/bin/zsh
# T302 — DRIVE ready-tasks.py --reconcile against a scratch repo, to answer ONE question
# with bytes rather than reasoning:
#
#   When a killed worker's branch was ALREADY MERGED into main, what does the note that
#   T288 writes into tasks.json say about it?
#
# Three subjects, all `in_progress`, all demoted by the same run:
#   MERGED   branch exists, merged into main, 0 commits ahead      <- the case under test
#   PRUNED   branch merged into main and then DELETED (the repo's own habit)
#   REAL     branch with genuine unmerged WIP                      <- the control
#   NOBR     no branch recorded                                    <- second control
#
# Run: /bin/zsh .softhouse/reviews/T302/drive-branch-wip.sh
set -uo pipefail
OUT="${0:A:h}/out"; mkdir -p "$OUT"
S=$(mktemp -d /tmp/t302-XXXXXX)
RT="${0:A:h}/../../bin/ready-tasks.py"

cd "$S" || exit 1
git init -q -b main .
git config user.email t302@example.invalid
git config user.name T302
mkdir -p .softhouse/bin
cp "${RT:A}" .softhouse/bin/ready-tasks.py
print -r -- "seed" > seed.txt
git add -A; git commit -qm "seed"

# MERGED: real work, merged into main, branch kept
git checkout -q -b softhouse/T-merged
print -r -- "merged deliverable, 40 lines of it" > merged.txt
git add -A; git commit -qm "T-merged: the deliverable"
git checkout -q main
git merge -q --no-ff -m "merge T-merged" softhouse/T-merged

# PRUNED: real work, merged into main, branch then deleted
git checkout -q -b softhouse/T-pruned
print -r -- "pruned deliverable" > pruned.txt
git add -A; git commit -qm "T-pruned: the deliverable"
git checkout -q main
git merge -q --no-ff -m "merge T-pruned" softhouse/T-pruned
git branch -q -D softhouse/T-pruned

# REAL: genuine unmerged WIP (control — must still read as `commits`)
git checkout -q -b softhouse/T-real
print -r -- "wip" > wip.txt
git add -A; git commit -qm "T-real: wip"
git checkout -q main

/usr/bin/python3 - <<'PY'
import json
tasks = [
 {"id":"T-merged","status":"in_progress","branch":"softhouse/T-merged"},
 {"id":"T-pruned","status":"in_progress","branch":"softhouse/T-pruned"},
 {"id":"T-real","status":"in_progress","branch":"softhouse/T-real"},
 {"id":"T-nobr","status":"in_progress","branch":None},
 {"id":"T-ctl","status":"pending","branch":None},
]
open(".softhouse/tasks.json","w").write(json.dumps({"tasks":tasks},indent=2,ensure_ascii=False))
PY

print -r -- "=== SUBJECT: git branch --merged main ==="
git branch --merged main
print -r -- ""
print -r -- "=== RECONCILE (no LOCK on disk — see finding on the lock fail-open) ==="
/usr/bin/python3 .softhouse/bin/ready-tasks.py --reconcile --fire T302-DRIVE --repo "$S"
print -r -- "reconcile rc=$?"
print -r -- ""
print -r -- "=== RESULTING NOTES ==="
/usr/bin/python3 - <<'PY'
import json,textwrap
for t in json.load(open(".softhouse/tasks.json"))["tasks"]:
    print("%-9s %-12s %s" % (t["id"], t["status"], (t.get("branch") or "-")))
    n = t.get("note")
    if n:
        for l in textwrap.wrap(n, 96): print("           | "+l)
PY
print -r -- ""
print -r -- "scratch repo: $S"
