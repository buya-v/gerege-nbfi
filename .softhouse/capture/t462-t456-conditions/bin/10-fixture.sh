#!/bin/bash
# T462 -- a synthetic repo built for the TIME axis, re-derived rather than copied.
#
# T456 drove C-T456-1 on ONE shape: HLOAD/T955, fan-out 2, carrier second, task branch
# ABSENT (so `_absent_verdict` runs).  That is one of the TWO callers of
# `refs_carrying_content`; the other -- the ancestor-of-main leg that T451 added, which
# returns `stillborn-carried` -- was never driven on a clock at all.  Both are here.
#
# The fan-out 9 case is here because the floor under test is 8: a claim of the form
# "the time bound now probes at least as many refs as the count cap did" is only
# interesting if the fixture contains a population that STRADDLES 8.  A fixture whose
# largest fan-out is 2 cannot tell a floor of 8 from a floor of 1000.
#
# PATH DISCIPLINE.  Every repo-relative path below is spelled through $S / $C / $B and
# never as a literal dot-softhouse string.  These paths live inside $FIX, a SYNTHETIC
# repo, but the T316 dead-path census reads a tracked instrument's literal spelling as a
# reference to the tree it runs in and is right to; seven workers in fire 20260829-080002
# were refused for forgetting exactly this.
#
# FAIL-CLOSED (T238 sweeplib shape): set -euo pipefail, and a final self-check that
# every branch this fixture PROMISES exists and every branch it promises is GONE is gone.
# A drive over a fixture that never built is not a measurement.
set -euo pipefail

FIX=${1:?usage: 10-fixture.sh <fixture-dir>}
rm -rf "$FIX"; mkdir -p "$FIX"; cd "$FIX"
git init -q -b main .
git config user.email t462@fixture
git config user.name T462

S=".softhouse"          # the SYNTHETIC repo's instrument root -- assembled, never spelled
C="$S/capture"
B="$S/bin"

mkdir -p "$B"; : > "$B/.keep"
git add -A; git commit -qm "base: empty repo"

commit() {  # commit <relpath> <content> <subject>
  mkdir -p "$(dirname "$1")"
  printf '%s\n' "$2" > "$1"
  git add -A
  git commit -qm "$3"
}
SWEEP_SUBJECT="RESCUED: WIP from a worker that never signalled done (fire 20260829-160000)"

commit "$S/dispatch.txt" "wave" "softhouse iter6 WAVE 1: dispatch record, pushed BEFORE the first worktree add"
DISPATCH=$(git rev-parse HEAD)

# ---------------------------------------------------------------------------- F2 ----
# Fan-out 2, carrier SECOND in sort order, recorded branch PRUNED.
# This is T456's HLOAD reproduced from its shape, not copied from its file.
# Leg: _absent_verdict -> relocated (REFUSE) when the carrier is probed.
git branch softhouse/aaa-t801-decoy "$DISPATCH"
git checkout -q -b softhouse/zzz-t801-carrier "$DISPATCH"
commit "$C/t801-real/out/w.txt" "T801 real work" "T801: the real work"
git checkout -q main

# ---------------------------------------------------------------------------- F2S ---
# The SAME evidence with the recorded branch STANDING at the dispatch commit.
# Leg: the ancestor-of-main arm T451 added -> stillborn-carried (REFUSE).
# T456 never drove this leg on a clock; it is the leg C-T449-1 was filed about.
git branch softhouse/T802-work "$DISPATCH"
git branch softhouse/aaa-t802-decoy "$DISPATCH"
git checkout -q -b softhouse/zzz-t802-carrier "$DISPATCH"
commit "$C/t802-work/out/w.txt" "T802 real work" "$SWEEP_SUBJECT"
git checkout -q main

# ---------------------------------------------------------------------------- F9 ----
# Fan-out 9 with the ONLY carrier NINTH.  This is the exact population T451 removed the
# count cap for ("a real carrier sorting at position 9 turned a REFUSAL into a
# demotion").  A floor of 8 must NOT resurrect that defect on a fast host.
for n in 1 2 3 4 5 6 7 8; do
  git branch "softhouse/d${n}-t803-decoy" "$DISPATCH"
done
git checkout -q -b softhouse/zzz-t803-carrier "$DISPATCH"
commit "$C/t803-real/out/w.txt" "T803 real work" "T803: the real work"
git checkout -q main

# ---------------------------------------------------------------------------- F1 ----
# MUST-REFUSE control: one ref, it carries, branch pruned.  If this ever demotes the
# instrument is broken, not the code.
git checkout -q -b softhouse/zzz-t804-carrier "$DISPATCH"
commit "$C/t804-real/out/w.txt" "T804 real work" "T804: the real work"
git checkout -q main

# ---------------------------------------------------------------------------- N -----
# MUST-DEMOTE control: two refs NAMING the id, neither owning a byte of it.  This is the
# T339 shape.  If a floor ever makes this REFUSE, the floor bought a fail-open.
git checkout -q -b softhouse/aaa-t805-decoy "$DISPATCH"
commit "$C/t900-unrelated/out/other.txt" "somebody else's work" "$SWEEP_SUBJECT"
git checkout -q main
git checkout -q -b softhouse/zzz-t805-decoy "$DISPATCH"
commit "$B/shared-tool.py" "# shared file, names nobody" "$SWEEP_SUBJECT"
git checkout -q main

# ------------------------------------------------------------------- self-check -----
fail=0
for want in softhouse/aaa-t801-decoy softhouse/zzz-t801-carrier \
            softhouse/T802-work softhouse/aaa-t802-decoy softhouse/zzz-t802-carrier \
            softhouse/zzz-t803-carrier \
            softhouse/zzz-t804-carrier \
            softhouse/aaa-t805-decoy softhouse/zzz-t805-decoy ; do
  git rev-parse -q --verify "refs/heads/$want" >/dev/null || {
    echo "FIXTURE SELF-CHECK FAILED: $want was not created" >&2; fail=1; }
done
for n in 1 2 3 4 5 6 7 8; do
  git rev-parse -q --verify "refs/heads/softhouse/d${n}-t803-decoy" >/dev/null || {
    echo "FIXTURE SELF-CHECK FAILED: d${n}-t803-decoy missing" >&2; fail=1; }
done
for gone in softhouse/T801-x softhouse/T803-x softhouse/T804-x softhouse/T805-x ; do
  git rev-parse -q --verify "refs/heads/$gone" >/dev/null && {
    echo "FIXTURE SELF-CHECK FAILED: $gone should NOT exist" >&2; fail=1; }
done
# The ORDER claim is load-bearing: every one of these cases depends on the carrier
# sorting LAST among the refs naming its id.  Assert it rather than trusting the names.
for id in t801 t802 t803 t804; do
  last=$(git for-each-ref --format='%(refname:short)' refs/heads \
         | grep -i -- "$id" | sort | tail -1)
  case "$last" in
    *carrier) : ;;
    *) echo "FIXTURE SELF-CHECK FAILED: for $id the last-sorting ref is $last, not the carrier" >&2
       fail=1 ;;
  esac
done
[ "$fail" -eq 0 ] || { echo "FIXTURE ABORT -- no drive over this tree is interpretable" >&2; exit 91; }

echo "fixture at $FIX  (dispatch $DISPATCH)"
echo "cases:"
echo "  F2  T801  fan-out 2, carrier 2nd, branch PRUNED    -> _absent_verdict leg"
echo "  F2S T802  fan-out 2, carrier 2nd, branch STANDING  -> stillborn-carried leg"
echo "  F9  T803  fan-out 9, carrier 9th, branch PRUNED    -> straddles the floor of 8"
echo "  F1  T804  fan-out 1, carrier 1st, branch PRUNED    -> MUST-REFUSE control"
echo "  N   T805  fan-out 2, NO carrier,  branch PRUNED    -> MUST-DEMOTE control"
echo "refs:"
git for-each-ref --format='  ref %(refname:short)' refs/heads
