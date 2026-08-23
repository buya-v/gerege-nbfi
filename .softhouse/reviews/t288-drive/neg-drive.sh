#!/bin/zsh
# T288 — THE CASE THAT MUST NOT FIRE.
#
# A guard that demotes everything is not a guard, it is a delete. So: same fixture, same
# three `in_progress` tasks, same dead driver — but with a LIVE session working in the
# repo. The wrapper must refuse to touch tasks.json and must say why.
#
# THE STAND-IN IS NAMED HONESTLY: it is `/bin/sleep` started via `exec -a claude`, with
# its cwd inside the fixture repo. It is NOT an agent and it dispatches nothing. What it
# exercises is exactly what the probe reads and nothing more — the process's argv[0]
# basename and its cwd as reported by lsof. The real shape those two fields take was
# measured separately against the live fire on this host
# (`/bin/ps` -> `/Users/buv/.local/bin/claude -p …`, `lsof -a -d cwd -p 28980 -Fn` ->
# `n/Users/buv/gerege-nbfi`), which is what makes the stand-in a fair one.
#
# FIRST ATTEMPT WAS `cp /bin/sleep …/claude`, AND IT SILENTLY DID NOT RUN — copying a
# signed system binary invalidates its signature and the kernel kills it on this
# machine. The drive then "passed" the plant step, examined 2 claude processes, neither
# of them the plant, and reported a FAIL for the wrong reason. Hence the assertion
# below: a negative drive that fails to plant anything proves NOTHING, and must say so
# rather than quietly grade the wrong world.
#
# Usage: neg-drive.sh <worktree> [base]
set -uo pipefail
WT="${1:?usage: neg-drive.sh <worktree> [base]}"
BASE="${2:-/tmp/t288-drive}"
REPO="$BASE/repo"

RUNDIR="$BASE/neg-bin"
rm -rf "$RUNDIR"; mkdir -p "$RUNDIR"
cp "$WT/.softhouse/bin/fire-program.sh" "$WT/.softhouse/bin/ready-tasks.py" \
   "$WT/.softhouse/bin/lib-worktree-prune.zsh" "$RUNDIR/"

# a live process that looks to the probe exactly like a session working in this repo
zsh -c "cd '$REPO' && exec -a claude /bin/sleep 400" &
LIVE=$!
/bin/sleep 1
PLANT_ARGV="$(/bin/ps -o command= -p $LIVE 2>/dev/null)"
PLANT_CWD="$(/usr/sbin/lsof -w -a -d cwd -p $LIVE -Fn 2>/dev/null | grep '^n' | sed 's/^n//')"
print -r -- "=== planted a live in-repo session: pid $LIVE"
print -r -- "    argv:  ${PLANT_ARGV:-(NOT RUNNING)}"
print -r -- "    cwd:   ${PLANT_CWD:-(UNREADABLE)}"
if [[ "${PLANT_ARGV:t}" != claude* || -z "$PLANT_CWD" ]]; then
  print -r -- "=== ABORT: the plant is not a live process named `claude` with a readable cwd."
  print -r -- "    This drive would grade a world it did not create. Nothing is proven; fix the plant."
  kill "$LIVE" 2>/dev/null
  exit 2
fi

DONE_MARK="$BASE/neg.done"
rm -f "$DONE_MARK"
( GEREGE_NBFI_REPO="$REPO" FINERACT_SRC=/tmp LOG_DIR="$BASE/logs" \
  CLAUDE_BIN="$BASE/fake/claude" CHAIN_MAX=1 \
  zsh -c "zsh '$RUNDIR/fire-program.sh' > '$BASE/neg.wrapper.out' 2>&1; print -r -- \$? > '$DONE_MARK'" & ) &
for i in {1..120}; do
  [[ -f "$DONE_MARK" ]] && break
  /bin/sleep 1
done
print -r -- "--- wrapper stdout ---"
cat "$BASE/neg.wrapper.out"
print -r -- "=== wrapper exited rc=$(<"$DONE_MARK" 2>/dev/null)"

kill "$LIVE" 2>/dev/null

print -r -- ""
print -r -- "=== did the probe actually SEE the plant? (a drive that planted nothing proves nothing)"
if grep -q "cwd $(cd "$REPO" && pwd -P)" "$BASE/neg.wrapper.out" 2>/dev/null; then
  print -r -- "  yes — the probe's evidence line names a cwd inside the fixture repo"
  grep -m1 'reconcile:\|NOT reconciling' "$BASE/neg.wrapper.out"
else
  print -r -- "  NO — the probe never saw a session in this repo. The refusal below, if any,"
  print -r -- "  happened for some OTHER reason and this drive proves nothing."
fi

print -r -- ""
print -r -- "=== tasks.json AFTER the fire — every in_progress must STILL be in_progress"
/usr/bin/python3 - "$REPO" <<'PY'
import json, sys
d = json.load(open(sys.argv[1] + "/.softhouse/tasks.json"))
bad = 0
for t in d["tasks"]:
    print("  %-6s %-14s note=%s" % (t["id"], t["status"], (t.get("note") or "(none)")[:60]))
    if t["id"] in ("T900", "T901", "T902") and t["status"] != "in_progress":
        bad += 1
    if t["id"] == "T903" and t["status"] != "pending":
        bad += 1
print("  VERDICT: %s" % ("PASS -- the guard left a live session's tasks alone" if not bad
                         else "FAIL -- %d task(s) were demoted while a session was live" % bad))
sys.exit(1 if bad else 0)
PY
