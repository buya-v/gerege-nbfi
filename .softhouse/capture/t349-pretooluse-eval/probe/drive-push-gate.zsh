#!/bin/zsh
# T349 -- end-to-end RED/GREEN of the CANDIDATE guard (push-gate) through a real
# Agent-tool worktree spawn in the throwaway repo.
#
#   RED   : an unpushed dispatch commit on HEAD  -> spawn must be REFUSED
#   GREEN : the same commit pushed to origin/main -> spawn must be ALLOWED
#   OFFLINE-OPEN / OFFLINE-CLOSED : origin unreachable, both fail directions
set -u
ROOT=${T349_ROOT:-/tmp/t349-scratch}
CAP=${T349_CAP:?capture dir}
DRIVE=$CAP/probe/drive-run.zsh
PROMPT=$CAP/probe/prompt-spawn.txt
export T349_REPO="$ROOT/repo"

step() { print -r -- ""; print -r -- "############ $1"; }

cd "$ROOT/repo"

step "RED -- commit a dispatch record and do NOT push it"
print -r -- '{"tasks":[{"id":"T999","status":"in_progress","branch":"softhouse/T999"}]}' > .softhouse/tasks.json
git add -A >/dev/null; git commit -q -m "dispatch record (deliberately unpushed)"
git rev-parse HEAD
git ls-remote origin refs/heads/main
zsh "$DRIVE" P1-pushgate-RED-unpushed push-gate "$PROMPT"

step "GREEN -- push that exact commit, then spawn again"
git push -q origin main
git rev-parse HEAD
git ls-remote origin refs/heads/main
zsh "$DRIVE" P2-pushgate-GREEN-pushed push-gate "$PROMPT"

step "OFFLINE fail-OPEN -- origin points at an unroutable host"
git remote set-url origin "ssh://git@192.0.2.1:22/nonexistent.git"
T349_FAIL=open T349_NET_TIMEOUT=8 zsh "$DRIVE" P3-offline-FAILOPEN push-gate "$PROMPT"

step "OFFLINE fail-CLOSED -- same unroutable origin, opposite decision"
T349_FAIL=closed T349_NET_TIMEOUT=8 zsh "$DRIVE" P4-offline-FAILCLOSED push-gate "$PROMPT"

git remote set-url origin "$ROOT/origin.git"
print -r -- ""
print -r -- "origin restored to $ROOT/origin.git"
