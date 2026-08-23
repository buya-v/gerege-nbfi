#!/bin/zsh
# T309 — DRIVE THE SIGTERM PATH RED, THEN GREEN.
#
# The claim under test: "fire-program.sh reconciles tasks.json when it is SIGTERMed."
# Before T309 that was FALSE — on_signal() released the lock and `exit`ed without ever
# reaching reconcile_tasks_json, and the function was not even defined yet on a first
# chain iteration. This harness builds a scratch repo, dispatches eight fake in_progress
# tasks (the shape of the 20260823-080004 incident), starts a real fire-program.sh over a
# fake `claude`, SIGTERMs it, and reads tasks.json back.
#
# IT RUNS BOTH SETS OF BYTES. `--rev <gitish>` copies fire-program.sh + ready-tasks.py
# from that revision into the scratch repo, so the SAME harness grades the pre-fix and
# the post-fix wrapper. A harness that only ever sees the fix cannot tell a fix from a
# tautology (P-91's corollary: a rig is inside the trust boundary of the thing it grades).
#
# DETACHMENT, AND WHY IT IS NOT OPTIONAL. ready-tasks.py decides its authority from
# /bin/ps ANCESTRY. Run straight out of an agent's Bash tool the wrapper is a descendant
# of a `claude`, which selects `in_session` mode — not the mode a launchd fire runs in.
# So the wrapper is started through a launcher that `exec`s it after its own parent has
# exited, which reparents it to pid 1 and gives it a launchd-shaped ancestry. The
# launcher writes its pid (preserved across `exec`) so the harness can signal it.
#
# Usage:
#   zsh drive-sigterm.zsh --rev HEAD          # post-fix  -> expect RECONCILED
#   zsh drive-sigterm.zsh --rev main          # pre-fix   -> expect NOT reconciled
#   zsh drive-sigterm.zsh --rev HEAD --foreign-claude   # a live in-repo session -> REFUSED
#
# Exit 0 = the run completed and its verdict is printed. The CALLER decides whether that
# verdict is the expected one; this script does not know which revision is supposed to
# pass, on purpose.
set -uo pipefail

REV=HEAD
FOREIGN=0
NORECON=0
WEDGE=0
KEEP=0
NTASKS=8
for a in "$@"; do
  case "$a" in
    --rev) ;;                       # value consumed below
    --foreign-claude) FOREIGN=1 ;;
    --no-reconcile) NORECON=1 ;;
    --wedge) WEDGE=1 ;;
    --keep) KEEP=1 ;;
    *) ;;
  esac
done
# tiny hand-rolled pair parsing (the surface is three flags)
i=1
while (( i <= $# )); do
  case "${@[$i]}" in
    --rev) (( i++ )); REV="${@[$i]}" ;;
    --ntasks) (( i++ )); NTASKS="${@[$i]}" ;;
  esac
  (( i++ ))
done

SRC="${SRC:-$(cd "${0:A:h}/../../.." && pwd)}"      # the repo this harness lives in
WORK="${TMPDIR:-/tmp}/t309-drive.$$"
mkdir -p "$WORK" || exit 1
if (( ! KEEP )); then trap 'rm -rf "$WORK"' EXIT; fi

print "=============================================================================="
print "T309 DRIVE — wrapper bytes from revision: $REV"
print "  source repo: $SRC"
print "  scratch:     $WORK"
print "  foreign live claude in repo: $FOREIGN"
print "  reconcile disabled (A/B control): $NORECON"
print "  resolver WEDGED (fault injection): $WEDGE"
print "  in_progress tasks planted:   $NTASKS"
print "=============================================================================="

# ------------------------------------------------------------------ scratch repo ---
git init -q --bare "$WORK/origin.git"
git init -q "$WORK/repo" 2>/dev/null
cd "$WORK/repo" || exit 1
git checkout -q -b main 2>/dev/null
git config user.email t309@example.invalid
git config user.name  T309
git remote add origin "$WORK/origin.git"
mkdir -p .softhouse/bin

# THE SAME BYTES, from the revision under test (T213's rule).
git -C "$SRC" show "$REV:.softhouse/bin/fire-program.sh"      > .softhouse/bin/fire-program.sh || exit 1
git -C "$SRC" show "$REV:.softhouse/bin/ready-tasks.py"       > .softhouse/bin/ready-tasks.py  || exit 1
git -C "$SRC" show "$REV:.softhouse/bin/lib-worktree-prune.zsh" > .softhouse/bin/lib-worktree-prune.zsh || exit 1
# FAULT INJECTION. `--wedge` replaces the resolver with one that never returns, so the
# OUTER wall-clock bound in reconcile_bounded() is the only thing that can end the
# handler. Without this leg that bound is an untested guard, which is the defect class
# this whole task is about.
if (( WEDGE )); then
  cat > .softhouse/bin/ready-tasks.py <<'WEDGEEOF'
import sys, time
sys.stdout.write("WEDGED RESOLVER — this process never returns\n")
sys.stdout.flush()
time.sleep(3600)
WEDGEEOF
fi
chmod +x .softhouse/bin/fire-program.sh
print "wrapper sha256: $(/usr/bin/shasum -a 256 .softhouse/bin/fire-program.sh | cut -c1-16)"
print "resolver sha256: $(/usr/bin/shasum -a 256 .softhouse/bin/ready-tasks.py | cut -c1-16)"

# Eight dead dispatches, four with a branch that exists at the dispatch commit and four
# with a branch that was never created — the exact split measured in the incident.
/usr/bin/python3 - "$NTASKS" <<'PY'
import json, sys
n = int(sys.argv[1])
tasks = [{"id": "T%03d" % (900 + i),
          "title": "planted dead dispatch %d" % i,
          "status": "in_progress",
          "executor": "agent",
          "model": "opus",
          "target": "code",
          "branch": "softhouse/T%03d-planted" % (900 + i),
          "fire": "20260823-080004",
          "dependencies": []} for i in range(n)]
tasks.append({"id": "T999", "title": "an untouched task", "status": "todo",
              "executor": "agent", "dependencies": []})
json.dump({"tasks": tasks}, open(".softhouse/tasks.json", "w"), indent=2, ensure_ascii=False)
PY
print "# a placeholder so the repo has a first commit" > README.md
git add -A && git commit -q -m "scratch base"
git push -q origin main

# four of the eight get a branch at the dispatch commit with ZERO commits ahead
for k in 0 1 2 3; do
  git branch "softhouse/T$((900+k))-planted" main
done

# ------------------------------------------------------------------- fake claude ---
# Named exactly `claude`: fire-program.sh's liveness probe matches on the basename of
# ps's first field, and stop_driver has to find it as a descendant.
cat > "$WORK/claude" <<'EOF'
#!/bin/zsh
# fake driver: emit enough valid stream-json for the wrapper's jq digest, then sit.
print -r -- '{"type":"system","subtype":"init","session_id":"t309-fake"}'
print -r -- '{"type":"assistant","message":{"model":"claude-opus-5","content":[{"type":"tool_use","name":"Bash","input":{"command":"pretending to work"}}]}}'
/bin/sleep 600
EOF
chmod +x "$WORK/claude"

# ---------------------------------------------------------------------- launcher ---
# `exec` preserves the pid, and the ( … & ) form makes the launcher's parent exit at once
# so the wrapper is reparented to pid 1 — a launchd-shaped ancestry with no `claude` in it.
MINSECS=2
(( NORECON )) && MINSECS=999
cat > "$WORK/launch.zsh" <<EOF
#!/bin/zsh
print -r -- \$\$ > "$WORK/wrapper.pid"
export GEREGE_NBFI_REPO="$WORK/repo"
export LOG_DIR="$WORK/logs"
export CLAUDE_BIN="$WORK/claude"
export FINERACT_SRC="$WORK/fineract-stub"
export GIT_PUSH_TIMEOUT_SECS=10
export SIGNAL_RECONCILE_MIN_SECS=$MINSECS
exec /bin/zsh "$WORK/repo/.softhouse/bin/fire-program.sh"
EOF
mkdir -p "$WORK/fineract-stub" "$WORK/logs"

# --------------------------------------------------- optional foreign live session ---
FOREIGN_PID=0
if (( FOREIGN )); then
  # argv[0] must literally be `claude`; only bash's `exec -a` can set that here.
  /bin/bash -c "cd '$WORK/repo' && exec -a claude /bin/sleep 300" &
  FOREIGN_PID=$!
  /bin/sleep 0.5
  print "planted a foreign live session: pid $FOREIGN_PID, argv0=$(/bin/ps -o command= -p $FOREIGN_PID | cut -c1-40)"
fi

# ------------------------------------------------------------------------- launch ---
rm -f "$WORK/wrapper.pid"
( /bin/zsh "$WORK/launch.zsh" >"$WORK/launch.out" 2>&1 & )
# wait for the wrapper to reach the driver
WPID=0
for t in {1..90}; do
  [[ -r "$WORK/wrapper.pid" ]] && WPID=$(<"$WORK/wrapper.pid")
  LOGF=$(print -l "$WORK"/logs/fire-*.log(N) | tail -1)
  [[ -n "$LOGF" ]] && grep -q "driver job pid=" "$LOGF" 2>/dev/null && break
  /bin/sleep 1
done
LOGF=$(print -l "$WORK"/logs/fire-*.log(N) | tail -1)
if [[ -z "$LOGF" ]] || ! grep -q "driver job pid=" "$LOGF" 2>/dev/null; then
  print "HARNESS ERROR: the wrapper never reached the driver. launch.out:"
  cat "$WORK/launch.out" 2>/dev/null
  [[ -n "$LOGF" ]] && tail -40 "$LOGF"
  exit 1
fi
print "wrapper pid=$WPID  log=$LOGF"
print "wrapper ancestry (should contain NO 'claude'):"
/bin/ps -Ao pid=,ppid=,command= | /usr/bin/awk -v p="$WPID" '$1==p {print "    "$0}'
PPID_OF_W=$(/bin/ps -o ppid= -p "$WPID" 2>/dev/null | tr -d ' ')
print "    parent pid: ${PPID_OF_W:-?}  ($(/bin/ps -o command= -p "${PPID_OF_W:-1}" 2>/dev/null | cut -c1-40))"

print ""
print -r -- "--- tasks.json BEFORE the signal ---"
/usr/bin/python3 -c "
import json,collections
t=json.load(open('$WORK/repo/.softhouse/tasks.json'))['tasks']
print('   ', dict(collections.Counter(x['status'] for x in t)))
"

# ---------------------------------------------------------------------- SIGTERM ---
print ""
print -r -- "--- sending SIGTERM to wrapper $WPID ---"
T0=$(/usr/bin/python3 -c 'import time;print(time.time())')
kill -TERM "$WPID" 2>/dev/null
for t in {1..400}; do
  kill -0 "$WPID" 2>/dev/null || break
  /bin/sleep 0.1
done
T1=$(/usr/bin/python3 -c 'import time;print(time.time())')
ELAPSED=$(/usr/bin/python3 -c "print('%.2f' % ($T1-$T0))")
if kill -0 "$WPID" 2>/dev/null; then
  print "HARNESS: wrapper STILL ALIVE after 40s — killing it"
  kill -KILL "$WPID" 2>/dev/null
fi
print "SIGTERM -> wrapper exit: ${ELAPSED}s   (launchd's grace is ~20s)"

(( FOREIGN_PID )) && kill -KILL "$FOREIGN_PID" 2>/dev/null

print ""
print -r -- "--- handler transcript ---"
/usr/bin/awk '/SIGTERM received|SIGTERM|reconcile|RECONCILE|lock released|local lock file|handler complete|stopping the driver|no survivors|SIGKILL/' "$LOGF" | sed 's/^/    /'

print ""
print -r -- "--- tasks.json AFTER the signal ---"
/usr/bin/python3 - "$WORK/repo/.softhouse/tasks.json" <<'PY'
import json, sys, collections
t = json.load(open(sys.argv[1]))["tasks"]
c = collections.Counter(x["status"] for x in t)
print("    ", dict(c))
ip = [x for x in t if x["status"] == "in_progress"]
nr = [x for x in t if x["status"] == "needs_retry"]
print("     still in_progress: %d      demoted to needs_retry: %d" % (len(ip), len(nr)))
if nr:
    print("     sample note: %s" % nr[0].get("note", "")[:220])
print()
if ip:
    print("VERDICT: **NOT RECONCILED** — %d task(s) still claim in_progress after the fire" % len(ip))
    print("         was SIGTERMed. The next orchestrator will be told work is happening.")
    sys.exit(10)
print("VERDICT: **RECONCILED** — every dead dispatch was demoted to needs_retry.")
PY
VERDICT_RC=$?

print ""
print -r -- "--- git log in the scratch repo (did the repair get COMMITTED?) ---"
git -C "$WORK/repo" log --oneline -6 | sed 's/^/    /'
print ""
print -r -- "--- orphaned temp files? (reconcile_bounded must clean tasks.json.t288.tmp) ---"
print -l -- "$WORK"/repo/.softhouse/*.tmp(N) | sed 's/^/    LEFTOVER: /'
print -r -- "    (no LEFTOVER line above means none)"
print -r -- ""
print -r -- "--- did the lock get released? ---"
[[ -e "$WORK/repo/.softhouse/LOCK" ]] && print "    LOCK STILL ON DISK — the fire stranded it" || print "    LOCK is gone"

print ""
print "ELAPSED_SECONDS=$ELAPSED"
print "VERDICT_RC=$VERDICT_RC"
exit 0
