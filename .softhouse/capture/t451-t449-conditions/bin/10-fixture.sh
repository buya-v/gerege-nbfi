#!/bin/bash
# T451 -- a synthetic repo built with `git init`, NOT a clone.  Every case below is
# constructed from the SHAPES the shipped pipeline produces, not copied from T449.
#
#   `git worktree add -b softhouse/<id>-<slug>` cuts the task branch from the DRIVER'S
#   dispatch commit, which the driver has just pushed to main.  A worker killed before
#   its first commit therefore leaves that branch AT the dispatch commit: 0 ahead of
#   main, ancestor of main, carrying nothing.  fire-program.sh:3127
#   (`git -C "$W" checkout -q -b "$WB"`) then rescues the worktree's uncommitted WIP
#   onto a SECOND branch and DOES NOT delete the first.  So "task branch parked at the
#   dispatch commit" and "rescue branch carrying the work" COEXIST -- that is case G.
set -euo pipefail
FIX=${1:-/tmp/t451/fixture}
rm -rf "$FIX"; mkdir -p "$FIX"; cd "$FIX"
git init -q -b main .
git config user.email t451@fixture; git config user.name T451
mkdir -p .softhouse/bin
touch .softhouse/bin/.keep
git add -A; git commit -qm "base: empty repo"

commit() { mkdir -p "$(dirname "$1")"; printf '%s\n' "$2" > "$1"; git add -A; git commit -qm "$3"; }

# ---- content ON MAIN ---------------------------------------------------------------
# C/T421 -- work landed under the task's OWN capture dir, branch pruned after the merge.
for i in 1 2 3; do commit ".softhouse/capture/t421-t406-conditions/out/$i.txt" "x" "T421: conditions $i"; done
# D/T428 -- review dir on main, and NO `<id>:` subject (subject is a merge line).
mkdir -p .softhouse/reviews/t428-review-t421
echo y > .softhouse/reviews/t428-review-t421/REVIEW.md
git add -A; git commit -qm "Merge branch 'softhouse/T428-review-t421'"
# T405-shape: real work that landed ONLY under ANOTHER task's condition-bundle dir, and
# no `<id>:` subject either.  A CONTROL: it records that the MAIN-side anchor is NOT
# touched by this task, so this task stays landed-invisible exactly as it is today.
commit ".softhouse/capture/t416-t405-conditions/out/work.txt" "x" "T416: conditions for T405"

# ---- the driver's dispatch commit --------------------------------------------------
commit ".softhouse/dispatch.txt" "wave" "softhouse: iter9 wave 2 -- five dispatched, records pushed BEFORE the first worktree add"
DISPATCH=$(git rev-parse HEAD)

# ---- B/T431: task branch parked AT the dispatch commit, nothing anywhere ------------
git branch softhouse/T431-t407-conditions "$DISPATCH"

# ---- G: STILLBORN TASK BRANCH *AND* A RESCUE REF CARRYING THE WORK ------------------
# Exactly what fire-program.sh:3127 leaves behind.  Note the rescue commit subject is
# the sweep's BOILERPLATE and names no id -- so the subject half of the ref content test
# can never fire on a rescue ref.
git branch softhouse/T900-work "$DISPATCH"
git checkout -q -b softhouse/rescued-t900-work-20260829 "$DISPATCH"
commit ".softhouse/capture/t900-work/out/wip.txt" "real analysis" "RESCUED: WIP from a worker that never signalled done (fire 20260829-080002)"
git checkout -q main

# ---- G2: byte-identical evidence, recorded branch DELETED --------------------------
git branch softhouse/T901-work "$DISPATCH"
git checkout -q -b softhouse/rescued-t901-work-20260829 "$DISPATCH"
commit ".softhouse/capture/t901-work/out/wip.txt" "real analysis" "RESCUED: WIP from a worker that never signalled done (fire 20260829-080002)"
git checkout -q main
git branch -D softhouse/T901-work >/dev/null

# ---- A/T339: the INCIDENT ref.  Name matches, content belongs to ANOTHER task. ------
# Its whole diff is a deletion in an A2 review dir plus T347's marker.  NOTHING in it
# names t339 -- not at the front of a component, not anywhere.  MUST STAY name-only.
mkdir -p .softhouse/reviews/A2-11
printf 'line\n%.0s' 1 2 3 4 5 6 7 8 9 10 > .softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt
git add -A; git commit -qm "A2-11: transcript"
git checkout -q -b softhouse/rescued-t339-base-20260828-080001
git rm -q .softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt
touch .t347-postcheckout-marker; git add -A
git commit -qm "RESCUED: WIP from a worker that never signalled done (fire 20260828-080001)"
git checkout -q main
# T339's own branch is gone (pruned), as in the incident.

# ---- E/T351: MUST-BLOCK control -- live ref, real OWNING content, branch gone -------
git checkout -q -b softhouse/T351-progress-accounting
commit ".softhouse/capture/t351-progress-accounting/out/a.txt" "x" "T351: progress accounting"
git checkout -q main
git branch -m softhouse/T351-progress-accounting softhouse/T351-progress-accounting-renamed

# ---- K: genuine work under ANOTHER task's condition-bundle dir, sweep-rescued -------
# `.softhouse/capture/t944-t945-conditions/` is THIS PROGRAM'S convention for "T945's
# conditions, worked by T944" -- the component BEGINS with t944 and NAMES t945.
git branch softhouse/T945-t944-conditions "$DISPATCH"
git checkout -q -b softhouse/rescued-t945-t944-conditions-20260829 "$DISPATCH"
commit ".softhouse/capture/t944-t945-conditions/out/work.txt" "T945 real work" "RESCUED: WIP from a worker that never signalled done (fire 20260829-080002)"
git checkout -q main
git branch -D softhouse/T945-t944-conditions >/dev/null

# ---- K2: case K's evidence with the task branch STILL PARKED (both defects at once) -
git branch softhouse/T946-t944-conditions "$DISPATCH"
git checkout -q -b softhouse/rescued-t946-t944-conditions-20260829 "$DISPATCH"
commit ".softhouse/capture/t944-t946-conditions/out/work.txt" "T946 real work" "RESCUED: WIP from a worker that never signalled done (fire 20260829-080002)"
git checkout -q main

# ---- H: 9 name-matching refs, the ONLY carrier last in sort order -------------------
for i in 1 2 3 4 5 6 7 8; do git branch "softhouse/T950-decoy-$i" "$DISPATCH"; done
git checkout -q -b softhouse/zz-t950-real "$DISPATCH"
commit ".softhouse/capture/t950-real/out/w.txt" "x" "T950: the real work"
git checkout -q main

# ---- N: STILLBORN task branch + a NAME-ONLY ref.  MUST STAY DEMOTE. -----------------
# The T339 shape with the task branch still parked: the note must name the ref and must
# NOT claim no ref exists, but the ACTION must not change.
git branch softhouse/T960-work "$DISPATCH"
git checkout -q -b softhouse/rescued-t960-base-20260829 "$DISPATCH"
commit ".softhouse/reviews/A2-12/TRANSCRIPT-A2-12.txt" "unrelated" "RESCUED: WIP from a worker that never signalled done (fire 20260829-080002)"
git checkout -q main

# ---- P: pure unstarted -- branch parked, no refs, nothing on main -------------------
git branch softhouse/T970-nothing "$DISPATCH"

# ---- R: THE COST OF THE PROPOSED `anywhere` RELAXATION ------------------------------
# T981 reviews T980.  Its live review branch carries T981's REVIEW OF T980 -- a path
# whose component MENTIONS t980 and BEGINS with t981.  This is the single commonest
# cross-task shape in the real ref store: 7 live (id, ref) pairs on 2026-08-29
# [out/20-realrepo-census.txt].  Under the OWNING anchor T980 demotes, correctly.  Under
# `anywhere` T980 would be told "a live ref CARRIES CONTENT for this task's id ...
# re-dispatch would fork it" -- about somebody else's review of it.
git checkout -q -b softhouse/T981-review-t980 "$DISPATCH"
commit ".softhouse/reviews/t981-review-t980/REVIEW.md" "T981's review of T980" "T981: review of T980"
git checkout -q main
# T980's own branch is pruned.

# ---- R2: THE SHAPE THE PROPOSED RELAXATION ACTUALLY BREAKS --------------------------
# R above is a review branch the reviewer COMMITTED on, and its subject names T980, so
# the generous SUBJECT half already makes it a carrier -- under both anchors.  Measured:
# 15 (id, ref) pairs on the live store carry today and 10 of them are foreign-owned
# refs caught exactly like that [out/21-realrepo-evidence.txt].  So R does not isolate
# the anchor.  R2 does: a REVIEWER's worktree swept by fire-program.sh:3127, whose
# subject is the sweep's boilerplate and names nobody, whose only path is T983's review
# OF T982.  Under the OWNING anchor T982 demotes (right -- T983's review is not T982's
# work).  Under `anywhere` T982 would be REFUSED forever on somebody else's review.
git checkout -q -b softhouse/rescued-t983-review-t982-20260829 "$DISPATCH"
commit ".softhouse/reviews/t983-review-t982/REVIEW.md" "T983's review of T982" "RESCUED: WIP from a worker that never signalled done (fire 20260829-080002)"
git checkout -q main
# T982's own branch is pruned.

# ---- S: THE RESIDUAL NEITHER ANCHOR CLOSES -----------------------------------------
# A worker scoped to a SHARED file (this very task's scope is `ready-tasks.py`) killed
# before its first commit: the rescue ref's diff names NO id at all, at the front of a
# component or anywhere in it.  Both anchors read it name-only and DEMOTE.  Recorded so
# the gap is a measured fixture rather than a sentence in a handoff.
git branch softhouse/T990-shared-file "$DISPATCH"
git checkout -q -b softhouse/rescued-t990-shared-file-20260829 "$DISPATCH"
commit ".softhouse/bin/shared-tool.py" "# real uncommitted work" "RESCUED: WIP from a worker that never signalled done (fire 20260829-080002)"
git checkout -q main

echo "fixture at $FIX  (dispatch $DISPATCH)"
git branch -a | sed 's/^/  ref /'
