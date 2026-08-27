#!/bin/zsh
# T309 attempt 2 -- THE IN-SESSION OWNERSHIP MATRIX, DRIVEN A/B ON IDENTICAL BYTES.
#
# Four cells, two revisions of ready-tasks.py, and the two REAL incidents this whole
# task is about. Every cell asserts a NUMBER OF DEMOTIONS, and the pre-fix revision is
# expected to get BOTH incidents wrong in OPPOSITE directions -- which is the point:
# one predicate serving two purposes cannot be right at both call sites.
#
#   A. LIVE      fire 20260827-230001, the fire running while this was written. All 7
#                in_progress tasks are ITS OWN dispatches. Correct answer: demote 0.
#   B. CORPSES   fire 20260823-140001, opening on the 8 in_progress tasks left by the
#                SIGTERMed 20260823-080004. Correct answer: demote 8.
#   C. NO LOCK COMMIT   the fire's `local fire lock` commit is not reachable. The
#                answer is not knowable, so the correct answer is demote 0 (fail-closed).
#   D. NO `fire` ON THE LOCK   ditto.
#
# Nothing outside $TMP is written. The real repo is only ever READ (`git show`). No
# signal is sent to any process. `.softhouse/LOCK` in the real repo is never touched.
set -u
SRC=${SRC:-/Users/buv/gerege-nbfi}
WT=${WT:?set WT to this worktree}
# BSD mktemp requires the XXXXXX at the END of the template; "XXXXXX.py" is not a
# template at all and silently reuses one literal name.
PREDIR=$(mktemp -d /tmp/t309pre.XXXXXX)
PRE=$PREDIR/ready-tasks.py
POST=$WT/.softhouse/bin/ready-tasks.py

# The PRE revision is the first T309 attempt's bytes, taken from the commit before this
# attempt's patches -- not a hand-written stand-in for them.
git -C $WT show df28ced:.softhouse/bin/ready-tasks.py > $PRE || exit 1

print "PRE  (attempt 1, df28ced): sha256 $(/usr/bin/shasum -a 256 $PRE  | cut -c1-16)"
print "POST (attempt 2, working tree): sha256 $(/usr/bin/shasum -a 256 $POST | cut -c1-16)"
print "source repo (READ-ONLY): $SRC"
print ""

PASS=0; FAIL=0

# cell <name> <lock-commit-or-NONE> <head-commit> <LOCK-fire-or-NONE> <expect-pre> <expect-post> <--fire>
cell() {
  local name=$1 lockcommit=$2 headcommit=$3 fire=$4 xpre=$5 xpost=$6
  local RECONCILING_FIRE=$7
  print "############################################################"
  print "# CELL $name"
  print "#   lock commit: $lockcommit   state under test: $headcommit   LOCK fire: $fire"
  print "#   expect PRE demotes=$xpre   POST demotes=$xpost"
  print "############################################################"
  local TMP R
  TMP=$(mktemp -d /tmp/t309m.XXXXXX)
  R=$TMP/repo
  mkdir -p $R/.softhouse/bin
  ( cd $R
    git init -q .
    git config user.email t309@local
    git config user.name T309
    # Commit 1: whatever tasks.json looked like at the fire's lock commit. When the cell
    # says NONE the commit is still made but under a DIFFERENT subject, so the resolver
    # genuinely cannot find a lock commit -- the fail-closed leg is exercised for real,
    # not stubbed.
    if [[ "$lockcommit" == NONE ]]; then
      git -C $SRC show $headcommit:.softhouse/tasks.json > .softhouse/tasks.json
      git add -A; git commit -q -m "softhouse: some unrelated commit"
    else
      git -C $SRC show $lockcommit:.softhouse/tasks.json > .softhouse/tasks.json
      git add -A; git commit -q -m "softhouse: local fire lock ($fire)"
    fi
    # Commit 2: the state as the reconciler finds it.
    git -C $SRC show $headcommit:.softhouse/tasks.json > .softhouse/tasks.json
    git add -A
    git commit -q -m "softhouse: dispatch record" >/dev/null 2>&1 || true
    if [[ "$fire" == NONE ]]; then
      print '{ "holder":"local-launchd", "host":"'$(hostname -s)'", "pid":'$PPID' }' \
        > .softhouse/LOCK
    else
      print '{ "holder":"local-launchd", "host":"'$(hostname -s)'", "pid":'$PPID', "fire":"'$fire'" }' \
        > .softhouse/LOCK
    fi
  )
  local rev out n want
  for rev in PRE POST; do
    cp ${(P)rev} $R/.softhouse/bin/ready-tasks.py
    # --fire is ALWAYS a real id: it is the reconciling fire's id for the note, and it
    # is not what the LOCK-side test varies. Passing "" here made cell D exit 64 on a
    # usage error and pass VACUOUSLY -- caught by noticing the cell printed no lines at
    # all, which is why every cell greps for its own evidence rather than only counting.
    out=$(/usr/bin/python3 $R/.softhouse/bin/ready-tasks.py --reconcile \
            --fire "$RECONCILING_FIRE" --dry-run --repo "$R" 2>&1)
    n=$(print -r -- "$out" | grep -c "in_progress -> needs_retry")
    print "  --- $rev ---"
    print -r -- "$out" | grep -E "mode:|in_progress tasks found|in-session evidence|IN-SESSION authority|RESULT:" | sed 's/^/    /'
    print "    demotions: $n"
    if ! print -r -- "$out" | grep -q "RESULT:"; then
      print "    >>> $rev **VACUOUS** -- the resolver printed no RESULT line, so it never"
      print "        reached its authority check. A zero here means nothing. Raw output:"
      print -r -- "$out" | sed 's/^/        | /'
      FAIL=$((FAIL+1))
      continue
    fi
    [[ $rev == PRE ]] && want=$xpre || want=$xpost
    if [[ "$n" == "$want" ]]; then
      print "    >>> $rev OK (demotions=$n, expected $want)"
      PASS=$((PASS+1))
    else
      print "    >>> $rev **MISMATCH** (demotions=$n, expected $want)"
      FAIL=$((FAIL+1))
    fi
  done
  print ""
  rm -rf $TMP
}

# A -- the fire that was live while this was written. Its own 7 dispatches.
#      PRE demotes 6 (the 6 that carry a stale `fire`); the 7th has no `fire` and is
#      withheld for the wrong reason. POST demotes 0.
cell "A: LIVE FIRE 20260827-230001 -- its own dispatches must NOT be demoted" \
     558ef32 HEAD 20260827-230001 6 0 20260827-230001

# B -- the real incident. 8 corpses inherited from the SIGTERMed 20260823-080004.
#      PRE demotes 0: none of the 8 carries a `fire` field at all, so attempt 1's
#      predicate is INERT on the exact incident it was built for. POST demotes 8.
cell "B: CORPSES OF 20260823-080004 -- 20260823-140001 must clear all 8" \
     5428c0a4 5428c0a4 20260823-140001 0 8 20260823-140001

# C -- no lock commit reachable. Ownership is unknowable; demote nothing.
cell "C: FAIL-CLOSED -- no reachable lock commit" \
     NONE 5428c0a4 20260823-140001 0 0 20260823-140001

# D -- LOCK carries no `fire`. Same.
cell "D: FAIL-CLOSED -- LOCK records no fire id" \
     5428c0a4 5428c0a4 NONE 0 0 20260823-140001

rm -rf $PREDIR
print "=============================================================="
print "OWNERSHIP MATRIX: $PASS passed, $FAIL failed"
print "=============================================================="
(( FAIL == 0 ))
