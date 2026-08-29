#!/bin/bash
# T448 -- IS THE f1-13b ROW's NEW `1` CAUSED BY ARM F, OR BY SOMETHING ELSE ON THE BRANCH?
#
# T433 moved T393's `f1-13b` row from `0 0` to `0 1` in a TRACKED executable
# (`10-drive-conditions.sh:241`) and says that removing ARM F would therefore fail T393's own
# drive. That sentence is only true if the `1` is ARM F's doing. T433's branch changes four
# files, so "it is 1 now" is not by itself an attribution.
#
# THE MEASUREMENT. Build T393's f1-13b mutation -- a post-fork observation mutated AND its
# MANIFEST.sha256 row rewritten in the SAME commit -- and grade section 10 on it at TWO refs:
#   BEFORE  the pre-ARM-F ref (unmodified `main` tip), where the arm does not exist;
#   AFTER   the T433 ref, where it does.
# Both halves are load-bearing, in the same way T433's own residual row is: if BEFORE goes red
# the residual was never real, and if AFTER goes green the arm does not reach it.
#
# ENGINE (P-33/P-53): `grep -c -F` fixed strings; the mutation is `printf >>` plus T393's own
# `12-relaunder-manifest.py`, so the laundering is the one the matrix row actually names.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298):
#   T448_SRC=<repo>  T448_SCRATCH=<dir OUTSIDE the repo>  T448_OUT=<dir> \
#   T448_BEFORE=<pre-ARM-F sha>  T448_AFTER=<sha carrying ARM F> \
#   bash 60-t448-f113b-attribution.sh
#
# CALIBRATION BEFORE ANY NEGATIVE (P-72; C4): the mutation function returns non-zero if it did
# not apply, and an unapplied mutation is exit 3 -- a case that did not mutate reports the
# colour of a clean tree, which is a control and not an attribution.
#
# EXIT 0  BEFORE=0 and AFTER=1 with ARM F naming the file: the `1` IS ARM F's.
# EXIT 1  it is not. EXIT 3 REFUSED, never read as a result.
set -u

SRC="${T448_SRC:?T448_SRC must name the source repository}"
SCRATCH="${T448_SCRATCH:?T448_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T448_OUT:?T448_OUT must name the directory to write transcripts into}"
BEFORE="${T448_BEFORE:?T448_BEFORE must name the pre-ARM-F commit-ish}"
AFTER="${T448_AFTER:?T448_AFTER must name the commit-ish carrying ARM F}"

CAP=".softhouse/capture/tierA-a2"
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
MAN="$CAP/MANIFEST.sha256"
PICK=".softhouse/capture/t393-t382-conditions/instruments/11-pick-targets.py"
LAUNDER=".softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py"

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t448-f113b"

if ! TARGETS="$(python3 "$SRC/$PICK")"; then
  echo "REFUSED: 11-pick-targets.py could not run in $SRC." >&2
  exit 3
fi
POSTFORK="$(printf '%s\n' "$TARGETS" | awk -F'\t' '$1=="POSTFORK"{print $2}')"
if [ -z "$POSTFORK" ]; then
  echo "REFUSED: the POSTFORK target came back EMPTY; there is no mutation to make." >&2
  exit 3
fi

echo "############ T448 -- f1-13b ATTRIBUTION"
echo "  BEFORE = $BEFORE  (no ARM F)"
echo "  AFTER  = $AFTER  (ARM F present)"
echo "  target = $POSTFORK  (MEASURED by 11-pick-targets.py, never typed)"
echo

grade_at() {   # grade_at <tag> <ref> ; echoes the section-10 exit code
  local tag="$1" ref="$2" rc
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || exit 3
    git clone --quiet --shared "$SRC" "$D" || exit 3
    git -C "$D" config user.email "t448@softhouse.local" || exit 3
    git -C "$D" config user.name "T448" || exit 3
  fi
  git -C "$D" reset --quiet --hard || exit 3
  git -C "$D" clean -qfdx || exit 3
  git -C "$D" checkout --quiet --detach "$ref" || exit 3
  git -C "$D" reset --quiet --hard "$ref" || exit 3
  # T393's f1-13b mutation, verbatim in effect: mutate + launder in ONE commit.
  printf '\nT448-F113B-MARKER\n' >> "$D/$CAP/$POSTFORK" || exit 3
  python3 "$D/$LAUNDER" "$D" "$POSTFORK" > /dev/null || exit 3
  git -C "$D" add -- "$CAP/$POSTFORK" "$MAN" || exit 3
  git -C "$D" commit -q -m "T448 f1-13b: post-fork observation mutated, manifest row rewritten in the SAME commit" || exit 3
  ( cd "$D" && python3 "$INT" ) > "$OUT/f113b-$tag.txt" 2>&1
  rc=$?
  echo "$rc"
}

RC_B="$(grade_at BEFORE "$BEFORE")"
NAMED_B="$(grep -c -F "LAUNDERED-OR-MUTATED" "$OUT/f113b-BEFORE.txt")"
RC_A="$(grade_at AFTER "$AFTER")"
NAMED_A="$(grep -c -F "LAUNDERED-OR-MUTATED $POSTFORK" "$OUT/f113b-AFTER.txt")"

printf '  %-8s section10=%s  ARM-F-named=%s   expected 0 / named 0\n' BEFORE "$RC_B" "$NAMED_B"
printf '  %-8s section10=%s  ARM-F-named=%s   expected 1 / named 1\n' AFTER  "$RC_A" "$NAMED_A"

BAD=0
[ "$RC_B" = "0" ]    || BAD=$((BAD + 1))
[ "$NAMED_B" = "0" ] || BAD=$((BAD + 1))
[ "$RC_A" = "1" ]    || BAD=$((BAD + 1))
[ "$NAMED_A" = "1" ] || BAD=$((BAD + 1))

echo
if [ "$BAD" -ne 0 ]; then
  echo "T448 f1-13b ATTRIBUTION: $BAD assertion(s) did not hold. The row's new value is NOT"
  echo "attributable to ARM F on this evidence."
  exit 1
fi
echo "T448 f1-13b ATTRIBUTION: the row's new expectation IS ARM F's doing. On the identical"
echo "laundered tree, section 10 exits 0 and names nothing where the arm is absent, and exits 1"
echo "NAMING the file where it is present. Removing ARM F therefore does fail T393's own drive."
exit 0
