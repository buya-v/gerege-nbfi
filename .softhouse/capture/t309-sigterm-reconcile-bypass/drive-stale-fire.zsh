#!/bin/zsh
# T309 attempt 2 -- DRIVE THE `task.fire` DISCRIMINATOR AGAINST THE REPO'S REAL STATE.
#
# WHAT IS BEING TESTED, and why it needs a driver rather than an argument. The first
# T309 attempt made `in_session` demotion turn on `task["fire"] != LOCK["fire"]`, on the
# ground that "at most one fire holds the lock, so a task stamped with a different fire
# id belongs to a fire that is over". The PREMISE is sound. The DATA is not: `fire` is
# stamped by the DRIVER at first dispatch and is not refreshed on re-dispatch, so a task
# re-dispatched by a later fire keeps the OLD fire's id and reads as a corpse.
#
# This harness builds a scratch repo out of the REAL tasks.json and the REAL lock commit
# of a REAL fire, plants a LOCK whose pid is a genuine ancestor of this process (so the
# ancestry walk succeeds honestly rather than by stubbing), and asks
# `--reconcile --dry-run` what it WOULD demote. Nothing outside $TMP is touched, no
# signal is sent to anything, and the real repo is only ever READ (`git show`).
#
# Usage:
#   SRC=<real repo> STAMP=<fire id> LOCKCOMMIT=<that fire's lock commit> \
#   RESOLVER=<path to ready-tasks.py under test> zsh drive-stale-fire.zsh
set -u
SRC=${SRC:?set SRC to the real repo}
STAMP=${STAMP:?set STAMP to the fire id under test}
LOCKCOMMIT=${LOCKCOMMIT:?set LOCKCOMMIT to that fire local-fire-lock commit}
RESOLVER=${RESOLVER:?set RESOLVER to the ready-tasks.py under test}

TMP=$(mktemp -d /tmp/t309a2.XXXXXX) || exit 1
print "scratch repo:        $TMP"
print "resolver under test: $RESOLVER"
print "resolver sha256:     $(/usr/bin/shasum -a 256 $RESOLVER | cut -c1-16)"
print "source repo (READ-ONLY): $SRC   lock commit: $LOCKCOMMIT   fire: $STAMP"

R=$TMP/repo
mkdir -p $R/.softhouse/bin
cd $R || exit 1
git init -q . || exit 1
git config user.email t309@local
git config user.name T309

# Commit 1 -- tasks.json exactly as it stood when that fire took its lock, under a
# commit subject byte-identical to the wrapper's (`softhouse: local fire lock (STAMP)`),
# because that subject is what the git-derived discriminator looks for.
git -C $SRC show $LOCKCOMMIT:.softhouse/tasks.json > .softhouse/tasks.json || exit 1
git add -A
git commit -q -m "softhouse: local fire lock ($STAMP)"

# Commit 2 -- tasks.json as it stands NOW, i.e. after that fire dispatched its workers.
git -C $SRC show HEAD:.softhouse/tasks.json > .softhouse/tasks.json || exit 1
git add -A
git commit -q -m "softhouse: $STAMP pre-dispatch record"

cp $RESOLVER .softhouse/bin/ready-tasks.py

# A REAL ancestor pid, so caller_is_lock_holder()'s /bin/ps walk succeeds honestly.
# $PPID launched this shell and is therefore an ancestor of the python below, by
# construction. This process is itself running inside a `claude`, which is what makes
# the run land in `in_session` mode -- the mode under test -- without faking anything.
ANC=$PPID
print "planting LOCK: pid=$ANC (a genuine ancestor), fire=$STAMP, host=$(hostname -s)"
cat > .softhouse/LOCK <<EOF
{
  "holder": "local-launchd",
  "host": "$(hostname -s)",
  "pid": $ANC,
  "fire": "$STAMP",
  "started_at": "2026-08-27T15:00:00Z"
}
EOF

print ""
print "############################################################"
print "# GROUND TRUTH: in_progress NOW, and what each discriminator sees"
print "############################################################"
/usr/bin/python3 - "$SRC" "$LOCKCOMMIT" <<'PY'
import json, subprocess, sys
src, lc = sys.argv[1], sys.argv[2]
def tj(rev):
    out = subprocess.run(["git", "-C", src, "show", "%s:.softhouse/tasks.json" % rev],
                         capture_output=True, text=True, check=True).stdout
    return {t["id"]: t for t in json.loads(out)["tasks"]}
at_lock, now = tj(lc), tj("HEAD")
print("  %-6s %-14s %-22s %s" % ("id", "AT LOCK", "task['fire']",
                                 "in_progress at lock?"))
for i, t in now.items():
    if t.get("status") == "in_progress":
        was = at_lock.get(i, {}).get("status", "(absent)")
        print("  %-6s %-14s %-22s %s" % (i, was, t.get("fire"),
                                         "YES" if was == "in_progress" else "NO"))
print("  ^ 'NO' means the task was NOT claiming in_progress when this fire took its")
print("    lock, so THIS fire dispatched it: it is LIVE and must not be demoted.")
PY

print ""
print "############################################################"
print "# --reconcile --dry-run  (in_session: this process runs inside a live claude)"
print "############################################################"
OUT=$(/usr/bin/python3 .softhouse/bin/ready-tasks.py --reconcile --fire "$STAMP" \
        --dry-run --repo "$R" 2>&1)
RC=$?
print -r -- "$OUT"
print "rc=$RC"

print ""
print "VERDICT"
DEMOTED=$(print -r -- "$OUT" | grep -c "in_progress -> needs_retry")
print "  tasks this caller WOULD demote: $DEMOTED"
if (( DEMOTED > 0 )); then
  print "  **DEMOTES LIVE WORK** -- every in_progress task in this repo was dispatched by"
  print "  fire $STAMP, the fire holding the lock. Demoting them destroys live work."
  print "VERDICT_RC=10"
else
  print "  WITHHELD -- no live dispatch of fire $STAMP would be demoted."
  print "VERDICT_RC=0"
fi
rm -rf $TMP
