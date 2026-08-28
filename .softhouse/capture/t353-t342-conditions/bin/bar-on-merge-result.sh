#!/bin/bash
# T353 — RUN THE BAR ON THE MERGE RESULT, because that is the tree the driver will land and
# because P-83 says so: *"two independent movements of one pinned number reconcile by
# RUNNING, never by arithmetic"* [`.softhouse/patterns.md:2806`].
#
# WHY IT IS NEEDED HERE. This branch is based on `softhouse/T342-releasedat-failopen`
# @ d870db1d, whose own base `a2fa69f4` predates `dc4e3ee3` on main — the commit that
# repaired the dead-path frontier row T342 filed as a blocker (`.softhouse/reviews/
# t280-review-t279/probe/drive-hook.sh | .softhouse/late.txt`). So the bar run on THIS BRANCH
# ALONE exits 2 on a HARD guard for a reason that predates this task, contributes zero rows
# from its files, and is already fixed on main. Neither transcript alone is the answer; both
# are recorded, and this one is the one that describes what lands.
#
# It clones LOCALLY (hardlinks, no network), merges, and runs the bar in the clone. The real
# repo and this worktree are never written.
#
# usage: bar-on-merge-result.sh <repo-root> <branch> [<base-ref>]
set -uo pipefail
ROOT="${1:?usage: bar-on-merge-result.sh <repo-root> <branch> [base]}"
BRANCH="${2:?}"
BASE="${3:-main}"
S="$(mktemp -d "${TMPDIR:-/tmp}/t353merge.XXXXXX")"
echo "=== cloning $ROOT -> $S/clone (local, hardlinked, no network)"
git clone --quiet --local --no-hardlinks --shared "$ROOT" "$S/clone" 2>&1 | tail -2
cd "$S/clone" || exit 2
git config user.name T353
git config user.email t353@local
# `git clone` gives remote-tracking refs, not local branches, for everything but HEAD.
# Resolve each ref to whichever of the two spellings exists rather than assuming one.
resolve() { git rev-parse --verify --quiet "$1" >/dev/null && { echo "$1"; return; }; git rev-parse --verify --quiet "origin/$1" >/dev/null && { echo "origin/$1"; return; }; echo ""; }
BASE_REF="$(resolve "$BASE")"; BRANCH_REF="$(resolve "$BRANCH")"
[[ -n "$BASE_REF"   ]] || { echo "!! cannot resolve base ref $BASE";     exit 2; }
[[ -n "$BRANCH_REF" ]] || { echo "!! cannot resolve branch ref $BRANCH"; exit 2; }
echo "=== base:   $BASE_REF   $(git rev-parse --short "$BASE_REF")"
git checkout -q -B barmerge "$BASE_REF" || exit 2
echo "=== merging $BRANCH_REF  $(git rev-parse --short "$BRANCH_REF")"
if ! git merge --no-edit -q "$BRANCH_REF" 2>&1 | tail -20; then
  echo "!! MERGE FAILED — the bar cannot be run on a tree that does not exist"
  git status --short | head -20
  exit 3
fi
echo "=== merge result: $(git rev-parse --short HEAD)"
echo "=== running: bash .softhouse/conformance.sh"
bash .softhouse/conformance.sh
rc=$?
echo "MERGE_RESULT_CONFORMANCE_EXIT=$rc"
echo "=== clone left at $S/clone for inspection; remove it when done"
exit $rc
