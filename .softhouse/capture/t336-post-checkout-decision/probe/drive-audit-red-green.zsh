#!/bin/zsh
# T336 — drive `.softhouse/hooks/push-before-spawn-audit.py` RED and GREEN (P-22).
# RED FIRST, against a repo where the driver spawned before publishing the dispatch record.
# If the RED case comes out clean the detector is worthless and must not ship.
#
# The scratch repos below reproduce the SHAPE of the two misses on record: the driver
# commits its dispatch record and spawns, and only pushes afterwards.
set -u
GIT=/usr/bin/git
AUDIT=${1:?path to push-before-spawn-audit.py}
# ABSOLUTE, because this script cd's into scratch repos. Attempt 1 of this driver used the
# relative path and every case reported exit 2 -- including the control that EXPECTS 2,
# which "passed" for entirely the wrong reason. P-22, inside the P-22 driver.
AUDIT=${AUDIT:A}
[[ -f $AUDIT ]] || { print "no audit at $AUDIT"; exit 2 }

T=$(mktemp -d /tmp/t336-audit.XXXXXX)
$GIT init -q --bare "$T/remote.git"
$GIT clone -q "$T/remote.git" "$T/repo" 2>/dev/null
R="$T/repo"
$GIT -C "$R" config user.email t336@local
$GIT -C "$R" config user.name T336
mkdir -p "$R/.softhouse"

# a fire starts: LOCK + RESUME + a dispatch record with the task NOT yet dispatched
print 'lock' > "$R/.softhouse/LOCK"
print 'in-flight' > "$R/.softhouse/RESUME.md"
print '{"tasks":[{"id":"T999","status":"ready"},{"id":"T998","status":"ready"}]}' \
    > "$R/.softhouse/tasks.json"
$GIT -C "$R" add -A >/dev/null
$GIT -C "$R" commit -qm "fire start"
$GIT -C "$R" push -q -u origin HEAD:main
$GIT -C "$R" branch --set-upstream-to=origin/main main >/dev/null 2>&1

spawn () {   # $1 = admin name, $2 = task branch the worker adopts
  cd "$R"
  $GIT worktree add -q -b "worktree-$1" "$T/$1" >/dev/null 2>&1
  cd "$T/$1"
  $GIT switch -q -c "$2"     # the worker adopts its task branch, as workers do
}

print "############################################################"
print "# RED — driver COMMITS the dispatch record, SPAWNS, and pushes 2 s later."
print "#       That is the 101 s / 135 s shape. The audit MUST fail."
print "############################################################"
print '{"tasks":[{"id":"T999","status":"in_progress","branch":"softhouse/T999-red"},{"id":"T998","status":"ready"}]}' \
    > "$R/.softhouse/tasks.json"
$GIT -C "$R" commit -qam "dispatch T999 -- COMMITTED, NOT PUSHED"
spawn agent-red1 softhouse/T999-red
sleep 2
$GIT -C "$R" push -q origin main
print "  (committed, spawned, pushed 2 s later)\n"
python3 "$AUDIT" --repo "$R" --worktree-glob 'agent-red*' --min-spawns 1
print "\n  AUDIT EXIT: $?   <-- must be 1"

print "\n############################################################"
print "# GREEN — next batch: commit, PUSH, then spawn."
print "############################################################"
print '{"tasks":[{"id":"T999","status":"in_progress","branch":"softhouse/T999-red"},{"id":"T998","status":"in_progress","branch":"softhouse/T998-green"}]}' \
    > "$R/.softhouse/tasks.json"
print 'in-flight batch 2' > "$R/.softhouse/RESUME.md"
$GIT -C "$R" commit -qam "dispatch T998 -- pushed BEFORE the first worktree add"
$GIT -C "$R" push -q origin main
sleep 2
spawn agent-green1 softhouse/T998-green
print "  (committed, pushed, spawned 2 s later)\n"
python3 "$AUDIT" --repo "$R" --worktree-glob 'agent-green*' --min-spawns 1
print "\n  AUDIT EXIT: $?   <-- must be 0"

print "\n############################################################"
print "# RED 2 — the OTHER half of P-85: the LOCK itself is not published."
print "#         origin says no fire is running while a worker is live."
print "############################################################"
$GIT -C "$R" rm -q --cached .softhouse/LOCK >/dev/null
$GIT -C "$R" commit -qm "remove LOCK from origin (simulating a fire whose lock was never published)"
$GIT -C "$R" push -q origin main
sleep 1
print '{"tasks":[{"id":"T997","status":"in_progress","branch":"softhouse/T997-nolock"}]}' \
    > "$R/.softhouse/tasks.json"
$GIT -C "$R" commit -qam "dispatch T997"
$GIT -C "$R" push -q origin main
sleep 1
spawn agent-nolock1 softhouse/T997-nolock
python3 "$AUDIT" --repo "$R" --worktree-glob 'agent-nolock*' --min-spawns 1
print "\n  AUDIT EXIT: $?   <-- must be 1 (LOCK absent from origin)"

print "\n############################################################"
print "# CONTROL — too few subjects must be REFUSED (exit 2), never a PASS."
print "############################################################"
python3 "$AUDIT" --repo "$R" --worktree-glob 'agent-nothing-matches-*' --min-spawns 1
print "\n  AUDIT EXIT: $?   <-- must be 2"

print "\n############################################################"
print "# CONTROL — a worktree that never adopted a softhouse/* branch is UNMAPPED,"
print "#           and a run in which NOTHING was judged must be exit 2, not 0."
print "############################################################"
cd "$R"
$GIT worktree add -q -b worktree-agent-unmapped1 "$T/agent-unmapped1" >/dev/null 2>&1
python3 "$AUDIT" --repo "$R" --worktree-glob 'agent-unmapped*' --min-spawns 1
print "\n  AUDIT EXIT: $?   <-- must be 2 (nothing judged), NOT 0"

print "\nscratch: $T"
