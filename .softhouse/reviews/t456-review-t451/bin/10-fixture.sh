#!/bin/bash
# T456 -- the reviewer's OWN synthetic repo.  Built with `git init`, not cloned, and not
# copied from T451's bin/10-fixture.sh: the cases here are re-derived from the shapes
# `fire-program.sh` produces, and two of them (HLOAD, R2LIVE) do not exist in T451's
# fixture at all.
#
# PATH DISCIPLINE.  Every repo-relative path below is spelled through $S and $R, never as
# a literal ".softhouse/..." string.  These are paths inside $FIX, the SYNTHETIC repo;
# the T316 dead-path census reads a tracked instrument's literal `.softhouse/...` as a
# reference to the tree it runs in, and it is right to.  Four workers this fire reddened
# `guard_dead_path_frontier` by forgetting exactly this.
#
# FAIL-CLOSED (T238 sweeplib shape).  `set -euo pipefail`, every git call checked, and a
# final self-check that the branches this fixture PROMISES actually exist -- so a driver
# can never report "no hits" over a fixture that was never built.
set -euo pipefail

FIX=${1:?usage: 10-fixture.sh <fixture-dir>}
rm -rf "$FIX"; mkdir -p "$FIX"; cd "$FIX"
git init -q -b main .
git config user.email t456@fixture
git config user.name T456

S=".softhouse"           # the synthetic repo's instrument root
C="$S/capture"
R="$S/reviews"
B="$S/bin"

mkdir -p "$B"; : > "$B/.keep"
git add -A; git commit -qm "base: empty repo"

commit() {  # commit <relpath> <content> <subject>
  mkdir -p "$(dirname "$1")"
  printf '%s\n' "$2" > "$1"
  git add -A
  git commit -qm "$3"
}
SWEEP_SUBJECT="RESCUED: WIP from a worker that never signalled done (fire 20260829-140005)"

# ---------------------------------------------------------------- the dispatch commit
commit "$S/dispatch.txt" "wave" "softhouse iter5 WAVE 2: dispatch record for 5 workers"
DISPATCH=$(git rev-parse HEAD)

# ---- G : task branch parked at dispatch AND a rescue ref carrying the work ----------
git branch softhouse/T900-work "$DISPATCH"
git checkout -q -b softhouse/rescued-t900-work-20260829 "$DISPATCH"
commit "$C/t900-work/out/wip.txt" "real analysis" "$SWEEP_SUBJECT"
git checkout -q main

# ---- G2: byte-identical evidence, recorded branch DELETED --------------------------
git branch softhouse/T901-work "$DISPATCH"
git checkout -q -b softhouse/rescued-t901-work-20260829 "$DISPATCH"
commit "$C/t901-work/out/wip.txt" "real analysis" "$SWEEP_SUBJECT"
git checkout -q main
git branch -q -D softhouse/T901-work

# ---- R2: a REVIEWER's worktree swept.  Boilerplate subject naming nobody; its only
#          path is T983's review OF T982.  T982's own branch is pruned.
#          Under `leading` T982 demotes (right).  Under `anywhere` T982 REFUSES forever
#          on somebody else's review of it.  THIS is what T449's patch costs.
git checkout -q -b softhouse/rescued-t983-review-t982-20260829 "$DISPATCH"
commit "$R/t983-review-t982/REVIEW.md" "T983 reviewing T982" "$SWEEP_SUBJECT"
git checkout -q main

# ---- K : T449's case K -- work under ANOTHER id's condition dir, filename names nobody
git checkout -q -b softhouse/rescued-t945-t944-conditions-20260829 "$DISPATCH"
commit "$C/t944-t945-conditions/out/work.txt" "T945 real work" "$SWEEP_SUBJECT"
git checkout -q main

# ---- KOWN: case K's shape WITH this program's real filename convention, which is what
#            the live T428 rescue ref actually looks like.  Same directory ownership,
#            filename named for the OWNER.  Must CARRY under the shipped anchor.
git checkout -q -b softhouse/rescued-t947-t944-conditions-20260829 "$DISPATCH"
commit "$C/t944-t947-conditions/out/T947-S01-counters.psql" "T947 real work" "$SWEEP_SUBJECT"
git checkout -q main

# ---- S : rescue ref touching only a SHARED file -- names no id anywhere -------------
git branch softhouse/T990-shared-file "$DISPATCH"
git checkout -q -b softhouse/rescued-t990-shared-file-20260829 "$DISPATCH"
commit "$B/shared-tool.py" "# real uncommitted work" "$SWEEP_SUBJECT"
git checkout -q main

# ---- HLOAD: TWO name-matching refs for T955, the ONLY carrier SECOND in sort order.
#             Task branch absent (pruned), so `_absent_verdict` runs.  Two refs is the
#             MEASURED maximum fan-out on the real repo -- i.e. this is the ORDINARY
#             population, not a pathological one.  With a slow git it is enough to
#             exhaust REF_PROBE_SECONDS, which MAX_REFS_PROBED=8 never could.
git branch softhouse/aaa-t955-decoy "$DISPATCH"
git checkout -q -b softhouse/zzz-t955-carrier "$DISPATCH"
commit "$C/t955-real/out/w.txt" "x" "T955: the real work"
git checkout -q main

# ---- E : must-block control -- live ref with real OWNING content, branch renamed ----
git checkout -q -b softhouse/T351-progress-accounting "$DISPATCH"
commit "$C/t351-progress-accounting/out/a.txt" "x" "T351: progress accounting"
git checkout -q main
git branch -q -m softhouse/T351-progress-accounting softhouse/T351-progress-accounting-renamed

# ------------------------------------------------------------------- self-check
# P-22 / T238: prove the fixture BUILT before anything is allowed to report over it.
fail=0
for want in softhouse/T900-work softhouse/rescued-t900-work-20260829 \
            softhouse/rescued-t901-work-20260829 \
            softhouse/rescued-t983-review-t982-20260829 \
            softhouse/rescued-t945-t944-conditions-20260829 \
            softhouse/rescued-t947-t944-conditions-20260829 \
            softhouse/T990-shared-file softhouse/rescued-t990-shared-file-20260829 \
            softhouse/aaa-t955-decoy softhouse/zzz-t955-carrier \
            softhouse/T351-progress-accounting-renamed ; do
  if ! git rev-parse -q --verify "refs/heads/$want" >/dev/null; then
    echo "FIXTURE SELF-CHECK FAILED: $want was not created" >&2
    fail=1
  fi
done
for gone in softhouse/T901-work softhouse/T982-x softhouse/T955-x ; do
  if git rev-parse -q --verify "refs/heads/$gone" >/dev/null; then
    echo "FIXTURE SELF-CHECK FAILED: $gone should NOT exist" >&2
    fail=1
  fi
done
[ "$fail" -eq 0 ] || { echo "FIXTURE ABORT -- no drive over this tree is interpretable" >&2; exit 91; }

echo "fixture at $FIX  (dispatch $DISPATCH)"
echo "refs:"
git for-each-ref --format='  ref %(refname:short)' refs/heads
