#!/bin/zsh
# T302 — DRIVE the worktree sweep's rescue leg against real git bytes.
#
# QUESTION: fire-program.sh:891-901 runs `checkout -b` / `add -A` / `commit` with EVERY rc
# discarded, then logs "rescued $WN -> $WB" unconditionally. The main-tree rescue 100 lines
# above (:783-797) CHECKS both rcs and says "NOTHING was rescued" when they fail — T202's
# own fix, applied to one branch of the function and not the other. T288 then fed the
# unverified $WB into RESCUE_PAIRS, so the claim is now written into tasks.json.
#
# So: is there a REALISTIC way for those commands to fail? A worker SIGKILLed mid-`git add`
# leaves `.git/index.lock` behind. That is the exact scenario the sweep exists for.
#
# This replays the sweep's git invocations VERBATIM (same flags, same order, same
# 2>/dev/null) against a worktree carrying a stale index.lock. It does not execute
# fire-program.sh; the fidelity claim is limited to those three commands.
set -uo pipefail
S=$(mktemp -d /tmp/t302-ph-XXXXXX)
STAMP=20260823-140001
cd "$S" || exit 1
git init -q -b main .
git config user.email t302@example.invalid
git config user.name T302
print -r -- seed > seed.txt; git add -A; git commit -qm seed

git branch -q softhouse/T-victim
git worktree add -q "$S/wt/agent-deadbeef" softhouse/T-victim
W="$S/wt/agent-deadbeef"
print -r -- "4,482 insertions worth of deliverable" > "$W/deliverable.md"

# The stale lock a SIGKILLed `git add` leaves behind. Linked worktrees keep their index
# under the MAIN repo's .git/worktrees/<name>/, so that is where the lock lives.
LOCKPATH="$S/.git/worktrees/agent-deadbeef/index.lock"
: > "$LOCKPATH"
print -r -- "planted stale lock: $LOCKPATH"
print -r -- ""

WS=$(git -C "$W" status --porcelain); WS_RC=$?
print -r -- "git status --porcelain rc=$WS_RC  output=[$WS]"
[[ -n "$WS" ]] || { print -r -- "sweep would have skipped this worktree"; exit 1 }

WN=$(basename "$W"); WN="${WN//[^A-Za-z0-9._-]/-}"
WB="softhouse/rescued-$WN-$STAMP"

print -r -- ""
print -r -- "--- the sweep's three commands, VERBATIM, with the rcs it discards ---"
git -C "$W" checkout -q -b "$WB" 2>/dev/null; print -r -- "  checkout -b rc=$?  <- DISCARDED by fire-program.sh:891"
git -C "$W" add -A >/dev/null 2>&1;          print -r -- "  add -A      rc=$?  <- DISCARDED by fire-program.sh:892"
git -C "$W" -c user.name=Buyan -c user.email=b@e.invalid \
    commit -q -m "RESCUED: WIP from a worker that never signalled done (fire $STAMP)" >/dev/null 2>&1
print -r -- "  commit      rc=$?  <- DISCARDED by fire-program.sh:893-896"
print -r -- ""
print -r -- "--- what the sweep LOGS at this point, unconditionally (fire-program.sh:901) ---"
print -r -- "  rescued $WN -> $WB"
print -r -- ""
print -r -- "--- GROUND TRUTH ---"
if git -C "$S" rev-parse --verify --quiet "$WB^{commit}" >/dev/null; then
  print -r -- "  branch $WB EXISTS"
else
  print -r -- "  branch $WB DOES NOT EXIST — the fire log and the tasks.json note both name a branch that is not there"
fi
print -r -- "  worktree still dirty? [$(git -C "$W" status --porcelain 2>/dev/null)]"
print -r -- "  worktree HEAD branch: $(git -C "$W" rev-parse --abbrev-ref HEAD 2>/dev/null)"
print -r -- ""
print -r -- "--- and the RESCUE_PAIR T288 hands to the reconciler ---"
PRIOR=softhouse/T-victim
print -r -- "  RESCUE_PAIRS += \"$PRIOR=$WB\""
print -r -- "  -> ready-tasks.py note clause: \"Uncommitted WIP left in its worktree was swept onto $WB by this fire's worktree sweep.\""
print -r -- ""
print -r -- "scratch: $S"
