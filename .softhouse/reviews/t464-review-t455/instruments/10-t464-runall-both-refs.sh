#!/bin/bash
# T464 — run-all.sh AT BOTH REFS, and the PIN AT BOTH REFS.
#
# T455 claims `run-all.sh` goes EXIT 1 -> EXIT 0 and section 9 goes `*** MOVED ***` -> as
# adjudicated, and that the green was bought by FIXING THE SEARCH rather than by MOVING THE
# ADJUDICATED PIN. A green bought by moving a pin is not a green, so the pin is measured at
# BOTH refs here, on the same line, with the same fixed string, before either run.
#
# NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL. Every one is assembled from `S` at run time
# (the T238 `sweeplib.sh` shape), so this file cannot add a row to the dead-path frontier for
# a tree that does not carry the branch under review.
#
#   T464_SRC=<repo>  T464_SCRATCH=<dir OUTSIDE the repo>  T464_BEFORE=<ref>  T464_AFTER=<ref> \
#     bash 10-t464-runall-both-refs.sh
#
# EXIT 0  both refs behaved as T455 recorded, and the pin is present x1 at both.
# EXIT 1  a measurement disagreed — the disagreement is the finding and is printed.
# EXIT 3  REFUSED: could not measure. Never read as a pass.
set -u
S='.softhouse'
RUNALL="$S/reviews/A2-11/run-all.sh"
PIN='sec 9 0 python3 "$DIR/adjudicate-section1.py"'

SRC="${T464_SRC:?T464_SRC must name the source repository}"
SCRATCH="${T464_SCRATCH:?T464_SCRATCH must name a scratch dir OUTSIDE the repository}"
BEFORE="${T464_BEFORE:?T464_BEFORE must name the pre-fix ref}"
AFTER="${T464_AFTER:?T464_AFTER must name the ref under review}"
D="$SCRATCH/runall"
FAIL=0

prepare() {
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 3
    git clone --quiet --shared "$SRC" "$D" || return 3
  fi
  git -C "$D" checkout --quiet --force --detach "$1" || return 3
  git -C "$D" reset --quiet --hard "$1" || return 3
  git -C "$D" clean -qfdx || return 3
  [ -f "$D/$RUNALL" ] || { echo "REFUSED: no runner at $1" >&2; return 3; }
}

expect() { if [ "$2" = "$3" ]; then echo "  OK   $1 = $2"; else echo "  BAD  $1 = $2, expected $3"; FAIL=$((FAIL+1)); fi; }

echo "############ T464 — run-all.sh AT BOTH REFS, AND THE ADJUDICATED PIN AT BOTH REFS"
echo "  BEFORE = $BEFORE"
echo "  AFTER  = $AFTER"
echo

echo "--- 0. THE PIN, MEASURED FIRST, AT BOTH REFS ---------------------------------------"
echo "    fixed string: $PIN"
for R in "$BEFORE" "$AFTER"; do
  prepare "$R" || exit 3
  N="$(grep -c -F -- "$PIN" "$D/$RUNALL")"
  L="$(grep -n -F -- "$PIN" "$D/$RUNALL" | cut -d: -f1 | tr '\n' ' ')"
  echo "      $R : x$N  at line(s) $L"
  expect "the adjudicated pin is present exactly once at $R" "$N" 1
done
prepare "$BEFORE" || exit 3
sha_b="$(git -C "$D" show "$BEFORE:$RUNALL" | grep -F -- "$PIN" | shasum -a 256 | cut -d' ' -f1)"
sha_a="$(git -C "$D" show "$AFTER:$RUNALL" | grep -F -- "$PIN" | shasum -a 256 | cut -d' ' -f1)"
echo "      sha256 of the pin line at BEFORE : $sha_b"
echo "      sha256 of the pin line at AFTER  : $sha_a"
expect "the pin line is BYTE-IDENTICAL across the two refs" "$sha_b" "$sha_a"
echo

for R in "$BEFORE" "$AFTER"; do
  LBL="$( [ "$R" = "$BEFORE" ] && echo BEFORE || echo AFTER )"
  echo "--- $LBL ($R) -------------------------------------------------------"
  prepare "$R" || exit 3
  ( cd "$D" && bash "$RUNALL" ) > "$SCRATCH/runall-$LBL.txt" 2>&1
  RC=$?
  echo "      run-all.sh exit = $RC"
  sed -n '/VERDICT . every section/,/RUN-ALL VERDICT/p' "$SCRATCH/runall-$LBL.txt" \
    | grep -E '^  (SECTION|[0-9])|sections run|RUN-ALL VERDICT' | sed 's/^/      /'
  if [ "$LBL" = "BEFORE" ]; then expect "$LBL run-all.sh exit" "$RC" 1
  else expect "$LBL run-all.sh exit" "$RC" 0; fi
  echo
done

[ "$FAIL" -ne 0 ] && { echo "T464 RUNALL DRIVE: $FAIL measurement(s) disagreed with T455."; exit 1; }
echo "T464 RUNALL DRIVE: as T455 recorded — 1 -> 0, section 9 MOVED -> as adjudicated, and"
echo "the adjudicated pin is present x1 and byte-identical at BOTH refs. EXIT 0"
