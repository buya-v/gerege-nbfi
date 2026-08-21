#!/bin/bash
# T156 / P-24 — re-run this task's ARTEFACTS on a SCRATCH MERGE INTO CURRENT MAIN.
#
# P-24: an assertion about what happens ON MERGE can only be tested BY MERGING, and
# three competent parties once missed a relocated time bomb because all three tested on
# the branch, where the bug is invisible. T154 found a live instance of the same thing
# last fire by scratch-merging instead of trusting its fork point. So: merge, then run
# the artefacts, not merely conformance.
#
# Nothing here touches the real repository or any of its worktrees. It clones into a
# throwaway directory, merges there, and deletes nothing outside that directory.
#
#     bash t156-p24-scratch-merge.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
SCRATCH="${TMPDIR:-/tmp}/t156-p24-scratch"
die() { echo "ABORT: $*" >&2; exit 2; }

BRANCH="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)" || die "cannot read the branch"
[ "$BRANCH" != "main" ] || die "run this from the task branch, not from main"

echo "=== T156 / P-24 — artefacts re-run on a scratch merge into CURRENT main"
echo "run at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "branch:      $BRANCH = $(git -C "$REPO" rev-parse HEAD)"
echo "fork point:  $(git -C "$REPO" merge-base main HEAD)"
echo "main NOW:    $(git -C "$REPO" rev-parse main)"
echo "main is $(git -C "$REPO" rev-list --count "$(git -C "$REPO" merge-base main HEAD)"..main) commit(s) ahead of this branch's fork point"
echo

rm -rf "$SCRATCH" || die "cannot clear $SCRATCH"
mkdir -p "$SCRATCH" || die "cannot create $SCRATCH"
git clone --no-local --quiet "$REPO" "$SCRATCH/clone" || die "clone failed"
C="$SCRATCH/clone"
git -C "$C" checkout --quiet -B main origin/main || die "cannot check out origin/main"
echo "clone main:  $(git -C "$C" rev-parse HEAD)"
git -C "$C" merge --quiet --no-edit "origin/$BRANCH" > "$SCRATCH/merge.txt" 2>&1 || {
    cat "$SCRATCH/merge.txt"; die "the merge did not apply cleanly"; }
echo "merged:      $(git -C "$C" rev-parse HEAD)"
conflicts=$(git -C "$C" diff --name-only --diff-filter=U | wc -l | tr -d ' ')
[ "$conflicts" = 0 ] || die "$conflicts conflicted path(s) after merge"
echo "conflicts:   0"
echo

# The store on merged main is whatever merged main carries. Nothing below is compared
# against a number written in this file (T156's own rule); the artefacts derive theirs.
echo "vector files on merged main: $(find "$C/.softhouse/vectors" -name '*.json' -type f | wc -l | tr -d ' ')"
echo

rc=0
echo "=== 1. the interruption prover, on the MERGED tree ==============================="
python3 "$C/.softhouse/capture/pathb/t149/prove-exit-trap.py"
p1=$?; echo "prove-exit-trap.py exit=$p1"; [ "$p1" = 0 ] || rc=1
echo

echo "=== 2. the P-26 sweep, on the MERGED tree ======================================="
python3 "$C/.softhouse/capture/pathb/t149/t156-sweep-unguarded-mutators.py" | tail -25
p2=${PIPESTATUS[0]}; echo "sweep exit=$p2"; [ "$p2" = 0 ] || rc=1
echo

echo "=== 3. prove-redgreen.sh ITSELF, on the MERGED tree ============================="
echo "    (T154's lesson: re-run the ARTEFACT after merging, not only conformance)"
bash "$C/.softhouse/capture/pathb/t149/prove-redgreen.sh"
p3=$?; echo "prove-redgreen.sh exit=$p3"; [ "$p3" = 0 ] || rc=1
echo
echo "merged-tree vector store still intact: $(git -C "$C" status --porcelain -- .softhouse/vectors | wc -l | tr -d ' ') modified path(s) under .softhouse/vectors (expect 0)"
git -C "$C" status --porcelain -- .softhouse/vectors nexus | sed 's/^/    /'
echo
[ "$(git -C "$C" status --porcelain -- .softhouse/vectors | wc -l | tr -d ' ')" = 0 ] || rc=1

echo "RESULT: $( [ "$rc" = 0 ] && echo 'ALL THREE ARTEFACTS HOLD ON THE MERGED TREE' || echo 'SOMETHING FAILS ONLY AFTER MERGING — do not merge' )"
exit "$rc"
