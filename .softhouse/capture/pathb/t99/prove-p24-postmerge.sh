#!/bin/sh
# T152 — P-24: AN ASSERTION ABOUT WHAT HAPPENS ON MERGE CAN ONLY BE TESTED BY MERGING.
#
# This script exists because the thing it tests is INVISIBLE ON THE BRANCH.  T98 fixed the
# moving-baseline defect by pinning `git merge-base main HEAD`, verified it on the branch — where
# that resolves to the fork point — and shipped a time bomb.  T102 fixed it with a literal sha and
# tested by merging.  T99 then reintroduced the exact computed default at lib.sh:25, in a tree that
# already contained T102's fix and its 20-line explanation, and again verified on the branch.
# T135 caught it by merging.  Three competent parties, one blind spot, three occurrences.
#
# So: a throwaway `--no-local` clone, `main` checked out FRESH FROM THE CLONE'S ORIGIN, this branch
# merged into it, and the four proofs run in the post-merge state.  Nothing here touches the real
# repository or its worktrees; the clone is deleted and recreated on every run.
#
# IT RUNS BOTH SIDES (P-22).  A run that only shows the fixed lib.sh going green cannot tell a fix
# from a no-op, so leg B reverts lib.sh IN THE MERGED CLONE to the pre-T152 computed default and
# runs the same four proofs again.  If leg B does not go red, this script has proved nothing and
# says so.
#
# NOT part of run-all.sh: it clones, merges and needs the live reference oracle, and a proof that
# reaches outside the export directory does not belong in the routine runner.  Run it by hand
# before merging this branch, and again after any change to lib.sh's baseline.
#
# Usage:   sh prove-p24-postmerge.sh
# Exit:    0 = leg A 4/4 exit 0 AND leg B reproduces the defect; 1 = otherwise; 2 = setup failed.
set -u

T99=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$T99" rev-parse --show-toplevel)
BRANCH=$(git -C "$REPO" rev-parse --abbrev-ref HEAD)
SCRATCH=${T152_SCRATCH:-/tmp/t152-p24}
PB=.softhouse/capture/pathb
LIVE=${T99_LIVE:-1}
# The T99 head: the last commit carrying the PRE-T152 lib.sh and prove-f4.sh.  A LITERAL sha, for
# the same reason FORK-POINT-SHA is one — a counterproof baseline that can follow `main` will.
T99_HEAD=8474bf0cc613e577cfa344428eb4b79c24a004c9

die() { printf 'P24 PROOF ABORT: %s\n' "$1" >&2; exit 2; }

echo "=== T152 / P-24 — the four T99 proofs, ON A SCRATCH MERGE INTO CURRENT main"
echo "source repo:   $REPO"
echo "branch:        $BRANCH = $(git -C "$REPO" rev-parse HEAD)"

rm -rf "$SCRATCH" || die "cannot clear $SCRATCH"
mkdir -p "$SCRATCH" || die "cannot create $SCRATCH"
git clone --no-local --quiet "$REPO" "$SCRATCH/clone" || die "clone failed"
C=$SCRATCH/clone

# `main` FROM THE CLONE'S ORIGIN, not from the branch: the whole question is what happens when the
# branch lands on top of whatever `main` is at merge time.
git -C "$C" checkout --quiet -B main origin/main || die "cannot check out origin/main"
MAIN_SHA=$(git -C "$C" rev-parse HEAD)
echo "main:          $MAIN_SHA"
echo "main is $(git -C "$C" rev-list --count "$(git -C "$REPO" merge-base main HEAD)".."$MAIN_SHA") commit(s) ahead of this branch's fork point"

git -C "$C" merge --quiet --no-edit "origin/$BRANCH" > "$SCRATCH/merge.txt" 2>&1
mst=$?
echo
echo "--- the merge"
echo "  exit $mst"
sed 's/^/    /' "$SCRATCH/merge.txt"
[ "$mst" = 0 ] || die "the merge did not complete cleanly; resolve it before reading anything below"
MERGE_SHA=$(git -C "$C" rev-parse HEAD)
CONFLICTS=$(git -C "$C" diff --name-only --diff-filter=U | wc -l | tr -d ' ')
echo "  merge commit:  $MERGE_SHA"
echo "  conflicts:     $CONFLICTS"

echo
echo "--- THE TRAP, shown live: in this state a baseline computed from \`main\` is the merge itself"
COMPUTED=$(git -C "$C" merge-base main HEAD)
echo "  git merge-base main HEAD = $COMPUTED"
echo "  HEAD                     = $MERGE_SHA"
if [ "$COMPUTED" = "$MERGE_SHA" ]; then
  echo "  IDENTICAL — so a proof using the computed ref would extract its 'before' tree from a commit"
  echo "  THAT CONTAINS THE FIX, and compare the fixed code against itself."
else
  echo "  NOT identical — the trap did not arm in this configuration, so leg B below bounds nothing."
fi
FORK=$(LC_ALL=C grep -vE '^[[:space:]]*(#|$)' "$C/$PB/t99/FORK-POINT-SHA" | tail -n 1 | tr -d '[:space:]')
echo "  FORK-POINT-SHA           = $FORK   <- literal, unchanged by any merge"

run_legs() {   # <label> <expected-verdict-text>
  _pass=0
  for f in f1 f2 f3 f4; do
    T99_EXPORT_ROOT=$SCRATCH/export-$1-$f T99_LIVE=$LIVE \
      sh "$C/$PB/t99/prove-$f.sh" > "$SCRATCH/$1-$f.txt" 2>&1
    _st=$?
    _last=$(LC_ALL=C grep -a '^RESULT:\|^T99 PROOF ABORT:\|NOT CLOSED' "$SCRATCH/$1-$f.txt" | tail -1 | cut -c1-110)
    [ -n "$_last" ] || _last=$(tail -1 "$SCRATCH/$1-$f.txt" | cut -c1-110)
    printf '  prove-%s.sh -> exit %s   %s\n' "$f" "$_st" "$_last"
    [ "$_st" = 0 ] && _pass=$((_pass+1))
  done
  LEGS_PASS=$_pass
}

echo
echo "=== LEG A — the merged tree AS THIS BRANCH SHIPS IT (literal FORK-POINT-SHA)"
run_legs A
A_PASS=$LEGS_PASS
echo "  proofs at exit 0: $A_PASS of 4"

echo
echo "=== LEG B — COUNTERPROOF 1: same merged tree, ONLY lib.sh reverted to the computed default"
echo "    (T152's second fix — prove-f4's positive baseline assertion — is left in place, so this"
echo "     leg measures what that assertion is worth ON ITS OWN)"
python3 - "$C/$PB/t99/lib.sh" <<'EOF'
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read()
old = 'PREFIX_REF=$(t99_read_fork_point) || exit 3'
new = 'PREFIX_REF=$(git -C "$T99" merge-base main HEAD)'
if old not in s:
    sys.stderr.write('COUNTERPROOF SETUP FAILED: the pinned line is not where expected\n')
    sys.exit(2)
io.open(p, 'w', encoding='utf-8').write(s.replace(old, new))
print('    reverted lib.sh to: %s' % new)
EOF
[ $? = 0 ] || die "could not build counterproof 1"
run_legs B
B_PASS=$LEGS_PASS
B_F4=$(LC_ALL=C grep -ac 'PROOF ABORT: baseline assertion' "$SCRATCH/B-f4.txt")
echo "  proofs at exit 0: $B_PASS of 4"
echo "  prove-f4 aborts on the baseline assertion: $B_F4 (1 = the belt-and-braces fired by itself)"

echo
echo "=== LEG C — COUNTERPROOF 2: the ACTUAL pre-T152 bytes, restored from the literal T99 head"
echo "    $T99_HEAD"
echo "    Both T152 fixes reverted.  This is the state T135 measured, and it is the state that"
echo "    would have shipped: f1/f2/f3 abort on their digest pins, and prove-f4 — which has no pin"
echo "    and, here, no baseline assertion either — does not refuse.  It CONCLUDES, and concludes"
echo "    'F-4 NOT CLOSED' at exit 1: a false negative on the finding this branch closes."
for fl in lib.sh prove-f4.sh; do
  git -C "$C" show "$T99_HEAD:$PB/t99/$fl" > "$C/$PB/t99/$fl" || die "cannot restore $fl from $T99_HEAD"
  echo "    restored $fl from $T99_HEAD"
done
run_legs C
C_PASS=$LEGS_PASS
C_F4_ST=$(LC_ALL=C grep -ac 'F-4 (stamp-absence ambiguity) NOT CLOSED' "$SCRATCH/C-f4.txt")
echo "  proofs at exit 0: $C_PASS of 4"
echo "  prove-f4 printed 'F-4 ... NOT CLOSED': $C_F4_ST  (1 = T135's measurement reproduced exactly)"

echo
echo "=== VERDICT"
rc=0
if [ "$A_PASS" = 4 ]; then
  echo "  LEG A: 4 of 4 proofs exit 0 on merged main.  The literal baseline survives the merge."
else
  echo "  LEG A: only $A_PASS of 4 exit 0 — THE FIX DOES NOT HOLD POST-MERGE."
  rc=1
fi
if [ "$B_PASS" -lt 4 ] && [ "$B_F4" = 1 ]; then
  echo "  LEG B: $B_PASS of 4 exit 0, and prove-f4 REFUSED on its own baseline assertion — so the"
  echo "         assertion closes the f4 hole independently of the literal sha."
else
  echo "  LEG B: did not behave as claimed ($B_PASS of 4 at exit 0, f4 baseline abort = $B_F4)."
  rc=1
fi
if [ "$C_PASS" -lt 4 ] && [ "$C_F4_ST" = 1 ]; then
  echo "  LEG C: $C_PASS of 4 exit 0 on the real pre-T152 bytes, and prove-f4 reported 'NOT CLOSED'"
  echo "         at exit 1 — T135's measurement reproduced.  Leg A is a measurement of the fix and"
  echo "         not of a no-op."
else
  echo "  LEG C: the pre-fix defect did NOT reproduce ($C_PASS of 4 at exit 0, NOT-CLOSED line ="
  echo "         $C_F4_ST).  This counterproof demonstrates nothing and leg A must not be read as"
  echo "         evidence."
  rc=1
fi
if [ "$rc" = 0 ]; then
  echo "RESULT: P-24 CLOSED for T99's rig — red on the pre-fix bytes, green on the fixed bytes,"
  echo "        both measured ON THE MERGE, which is the only state where the question exists."
else
  echo "RESULT: P-24 NOT CLOSED."
fi
exit $rc
