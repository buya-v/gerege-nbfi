#!/bin/zsh
# T288 — drive a fire-program.sh END TO END against the fixture repo and print what it
# left behind. The whole point is that the guard can be WATCHED failing and watched
# working: the same script runs the pre-fix bytes and the post-fix bytes.
#
#   drive.sh red    <worktree>  <base>   # the bytes at HEAD, before this task
#   drive.sh green  <worktree>  <base>   # the working-tree bytes, after this task
#
# The fixture must already exist (build-fixture.sh). Nothing here touches the real repo.
set -uo pipefail
MODE="${1:?usage: drive.sh red|green <worktree> [base]}"
WT="${2:?}"
BASE="${3:-/tmp/t288-drive}"
REPO="$BASE/repo"

RUNDIR="$BASE/$MODE-bin"
rm -rf "$RUNDIR"; mkdir -p "$RUNDIR"
if [[ "$MODE" == red ]]; then
  # the bytes as merged, straight out of git — not a hand-made "before" copy
  git -C "$WT" show HEAD:.softhouse/bin/fire-program.sh   > "$RUNDIR/fire-program.sh"
  git -C "$WT" show HEAD:.softhouse/bin/ready-tasks.py    > "$RUNDIR/ready-tasks.py"
  git -C "$WT" show HEAD:.softhouse/bin/lib-worktree-prune.zsh > "$RUNDIR/lib-worktree-prune.zsh"
else
  cp "$WT/.softhouse/bin/fire-program.sh" "$WT/.softhouse/bin/ready-tasks.py" \
     "$WT/.softhouse/bin/lib-worktree-prune.zsh" "$RUNDIR/"
fi
chmod +x "$RUNDIR/fire-program.sh"

print -r -- "=== DRIVE $MODE — $(git -C "$WT" rev-parse --short HEAD) working tree, repo $REPO"

# THE WRAPPER IS RUN ORPHANED, ON PURPOSE. In production launchd starts it, so its
# ancestor chain is `launchd -> zsh`. Started from this agent's shell instead, its chain
# is `... -> claude -> zsh`, and ready-tasks.py refuses to reconcile anything with a
# `claude` in its ancestry — correctly, since that means a live session is running.
# Driving it from a terminal would therefore only ever exercise the REFUSAL path and
# never the repair. `( cmd & ) &` exits the intermediate subshell immediately, so the
# wrapper is reparented to pid 1 and the chain matches the deployed one. Completion is
# detected by the wrapper's own log, not by wait(2), because it is no longer our child.
DONE_MARK="$BASE/$MODE.done"
rm -f "$DONE_MARK"
( GEREGE_NBFI_REPO="$REPO" FINERACT_SRC=/tmp LOG_DIR="$BASE/logs" \
  CLAUDE_BIN="${CLAUDE_BIN:-$BASE/fake/claude}" CHAIN_MAX=1 \
  zsh -c "zsh '$RUNDIR/fire-program.sh' > '$BASE/$MODE.wrapper.out' 2>&1; print -r -- \$? > '$DONE_MARK'" & ) &
for i in {1..120}; do
  [[ -f "$DONE_MARK" ]] && break
  /bin/sleep 1
done
if [[ -f "$DONE_MARK" ]]; then
  print -r -- "--- wrapper stdout ---"
  cat "$BASE/$MODE.wrapper.out"
  print -r -- "=== wrapper exited rc=$(<"$DONE_MARK")"
else
  print -r -- "=== wrapper DID NOT FINISH within 120s — this drive proves nothing; read $BASE/$MODE.wrapper.out"
fi
print -r -- "--- ancestry the wrapper actually ran under (proves no live session was faked away):"
grep -m3 -E 'reconcile: |reconcile\| +lock:' "$BASE/$MODE.wrapper.out" 2>/dev/null || print -r -- "  (no reconcile lines — expected for the red drive, which has no reconcile at all)"

print -r -- ""
print -r -- "=== tasks.json AFTER the fire"
/usr/bin/python3 - "$REPO" <<'PY'
import json, sys
d = json.load(open(sys.argv[1] + "/.softhouse/tasks.json"))
for t in d["tasks"]:
    print("  %-6s %-14s branch=%s" % (t["id"], t["status"], t.get("branch")))
    if t.get("note"):
        print("         note: %s" % t["note"])
PY

print -r -- ""
print -r -- "=== first 14 lines of RESUME.md AFTER the fire"
head -14 "$REPO/.softhouse/RESUME.md"

print -r -- ""
print -r -- "=== commits the wrapper made"
git -C "$REPO" log --oneline main -6
