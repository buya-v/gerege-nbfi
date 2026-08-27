#!/bin/zsh
# T302 attempt 2 -- F7: `wrapper` MODE IS GRANTED TO CALLERS THAT ESTABLISHED NOTHING.
#
# T309's fail-direction table justifies wrapper mode's "demote everything" like this:
#
#   "The caller has already established out of band that there is nothing live to
#    destroy" -- and names fire-program.sh's foreign_live_session_in_repo() as the
#    thing that established it.
#
# But that gate lives in the WRAPPER (fire-program.sh:1136), not in ready-tasks.py. And
# caller_is_lock_holder()'s FIRST leg is:
#
#     if not os.path.exists(lock):
#         return "wrapper", "no .softhouse/LOCK on disk -- nobody holds this repo", None
#
# So ANY caller, from ANY process, at ANY moment when .softhouse/LOCK is not on disk,
# receives the authority to demote every in_progress task -- with NO liveness check of
# any kind, because ready-tasks.py contains none. The precondition is ASSUMED, not
# REQUIRED. The documented usage line (ready-tasks.py:89) invites exactly that call.
#
# This is also the leg T302 attempt 1 flagged as a fail-OPEN and T309 left in place,
# adding a comment that ARGUES for it: "with no lock there is no live fire to protect".
#
# Nothing outside $TMP is written. --dry-run throughout. The real repo is only READ.
set -u
WT=${WT:-/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3e635faba72121c8}
POST=$WT/.softhouse/bin/ready-tasks.py

print "POST (main, post-T309): sha256 $(/usr/bin/shasum -a 256 $POST | cut -c1-16)"
print ""
print "=== 0. does ready-tasks.py contain ANY liveness check of its own? ==="
for pat in lsof '/bin/ps' foreign_live kill; do
  print -n "    grep -c '$pat' ready-tasks.py -> "
  grep -c -- "$pat" $POST
done
print "    (ps_ancestors uses /bin/ps for ANCESTRY only -- who am I -- never for"
print "     'is some other session alive in this repo'. There is no lsof, no cwd read.)"
print ""

cell() {   # cell <name> <lock-json-or-NONE> <expect>
  local name=$1 lockjson=$2 expect=$3
  local TMP R out n
  TMP=$(mktemp -d /tmp/t302f7.XXXXXX); R=$TMP/repo
  mkdir -p $R/.softhouse/bin
  ( cd $R
    git init -q .
    git config user.email t302@local
    git config user.name T302
    git -C $WT show 5964ab54:.softhouse/tasks.json > .softhouse/tasks.json
    git add -A; git commit -q -m "state under test: fire 20260823-140001 with 8 LIVE workers"
  )
  [[ "$lockjson" == NONE ]] || print -r -- "$lockjson" > $R/.softhouse/LOCK
  cp $POST $R/.softhouse/bin/ready-tasks.py
  print "############################################################"
  print "# $name"
  print "#   LOCK on disk: $([[ "$lockjson" == NONE ]] && print NO || print YES)"
  print "#   correct answer: $expect"
  print "############################################################"
  out=$(/usr/bin/python3 $R/.softhouse/bin/ready-tasks.py --reconcile \
          --fire 20260823-140001 --dry-run --repo "$R" 2>&1)
  n=$(print -r -- "$out" | grep -c "in_progress -> needs_retry")
  print -r -- "$out" | grep -E "lock:|mode:|in_progress tasks found|RESULT:" | sed 's/^/    /'
  print "    demotions: $n"
  rm -rf $TMP
  print ""
}

cell "CELL 1 -- NO LOCK ON DISK, 8 live workers in tasks.json" \
     NONE "REFUSE (liveness is unestablished; nothing here can establish it)"

cell "CELL 2 -- CONTROL: LOCK present, holder pid 1 is NOT an ancestor" \
     '{ "holder":"local-launchd", "host":"'$(hostname -s)'", "pid":1, "fire":"20260823-140001" }' \
     "REFUSE (and it does)"

cell "CELL 3 -- CONTROL: LOCK present, holder pid IS an ancestor (this zsh)" \
     '{ "holder":"local-launchd", "host":"'$(hostname -s)'", "pid":'$$', "fire":"20260823-140001" }' \
     "in_session narrow authority"
