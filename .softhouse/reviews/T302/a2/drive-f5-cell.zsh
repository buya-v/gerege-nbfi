#!/bin/zsh
# T302 attempt 2 -- F5, THE CELL T309's OWNERSHIP MATRIX DID NOT HAVE.
#
# T309's run-ownership-matrix.zsh cell B is:
#     cell "B: CORPSES ..."  5428c0a4  5428c0a4  20260823-140001  0  8
#                            ^lock     ^state-under-test
# The lock commit and the state under test are THE SAME COMMIT. The clock is frozen at
# the instant the fire took the lock. Cell A is the only cell that advances it, and in
# cell A the fire dispatched only ids that were NOT in the lock blob.
#
# The real history of fire 20260823-140001 advances the clock AND re-dispatches ids that
# WERE in the lock blob:
#     5428c0a4  14:00:08  lock taken; 8 tasks already in_progress (080004's corpses)
#     5964ab54  14:05:01  "DISPATCH fire 20260823-140001 batch 1 -- 8 workers"
# and softhouse/T302-review-t288 carries a commit dated 14:24:27 that day -- a LIVE
# worker of that fire, on an id that is in the lock blob.
#
# So this harness re-runs T309's own cell shape with the state under test advanced to
# 5964ab54. Correct answer: demote 0. Everything in_progress at 5964ab54 is a live
# worker of the lock-holding fire.
#
# Nothing outside $TMP is written. The real repo is only READ. No signal is sent.
set -u
WT=${WT:-/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3e635faba72121c8}
POST=$WT/.softhouse/bin/ready-tasks.py

print "POST (main, post-T309): sha256 $(/usr/bin/shasum -a 256 $POST | cut -c1-16)"
print "source repo (READ-ONLY): $WT"
print ""

PASS=0; FAIL=0

cell() {
  local name=$1 lockcommit=$2 headcommit=$3 fire=$4 xpost=$5 RECONCILING_FIRE=$6
  print "############################################################"
  print "# CELL $name"
  print "#   lock commit: $lockcommit   state under test: $headcommit   LOCK fire: $fire"
  print "#   correct answer: demote $xpost"
  print "############################################################"
  local TMP R
  TMP=$(mktemp -d /tmp/t302f5.XXXXXX)
  R=$TMP/repo
  mkdir -p $R/.softhouse/bin
  ( cd $R
    git init -q .
    git config user.email t302@local
    git config user.name T302
    git -C $WT show $lockcommit:.softhouse/tasks.json > .softhouse/tasks.json
    git add -A; git commit -q -m "softhouse: local fire lock ($fire)"
    git -C $WT show $headcommit:.softhouse/tasks.json > .softhouse/tasks.json
    git add -A
    git commit -q -m "softhouse: dispatch record" >/dev/null 2>&1 || true
    print '{ "holder":"local-launchd", "host":"'$(hostname -s)'", "pid":'$PPID', "fire":"'$fire'" }' \
      > .softhouse/LOCK
  )
  local out n
  cp $POST $R/.softhouse/bin/ready-tasks.py
  out=$(/usr/bin/python3 $R/.softhouse/bin/ready-tasks.py --reconcile \
          --fire "$RECONCILING_FIRE" --dry-run --repo "$R" 2>&1)
  n=$(print -r -- "$out" | grep -c "in_progress -> needs_retry")
  print -r -- "$out" | grep -E "mode:|in_progress tasks found|in-session evidence|IN-SESSION authority|RESULT:" | sed 's/^/    /'
  print "    demotions: $n"
  if ! print -r -- "$out" | grep -q "RESULT:"; then
    print "    >>> **VACUOUS** -- no RESULT line; a zero here means nothing. Raw:"
    print -r -- "$out" | sed 's/^/        | /'
    FAIL=$((FAIL+1)); rm -rf $TMP; print ""; return
  fi
  print "    --- the tasks it named ---"
  print -r -- "$out" | grep "in_progress -> needs_retry" | sed 's/^/    /'
  if [[ "$n" == "$xpost" ]]; then
    print "    >>> OK (demotions=$n, correct $xpost)"
    PASS=$((PASS+1))
  else
    print "    >>> **WRONG** (demotions=$n, correct $xpost) -- these are LIVE workers"
    FAIL=$((FAIL+1))
  fi
  rm -rf $TMP
  print ""
}

# B  -- T309's own cell, reproduced for calibration. Clock frozen at the lock instant.
cell "B  (T309's cell, clock FROZEN at the lock instant)" \
     5428c0a4 5428c0a4 20260823-140001 8 20260823-140001

# B' -- the same fire, five minutes later, after its OWN dispatch record.
cell "B' (SAME FIRE, clock ADVANCED to its own dispatch commit 5964ab54)" \
     5428c0a4 5964ab54 20260823-140001 0 20260823-140001

print "=============================================================="
print "F5: $PASS correct, $FAIL wrong"
print "=============================================================="
(( FAIL == 0 ))
