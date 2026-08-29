#!/bin/bash
# T455 — F-6 (the runner is RED on main) and C-T448-6 (the transcript footer is ERASED),
# both measured through the WHOLE runner at two refs, in scratch clones outside the repo.
#
# F-6, AS FOUND AND AS FIXED. T433 found `run-all.sh` already failing on an unmutated tree at
# unmodified `main`: section 9 (`adjudicate-section1.py`) is adjudicated 0 and exits 1, so the
# aggregate reads `RUN-ALL VERDICT: FAIL - 1 section(s) moved`. T448 bisected the cause to
# T391 and called it a FALSE POSITIVE of section 9's own substring search. T455 re-derived
# that by reading every hit: all seven are inside JSON STRING VALUES that are SENTENCES - a
# prose `evidence` field in capabilities-ledger.json and prose `citation` fields in three
# ledger vectors - and the check's claim is about the GRADED CORPUS, not about sentences that
# mention a token. THE SEARCH WAS FIXED, THE PIN WAS NOT MOVED. This file measures both refs
# so the fix is a difference in the runner's output rather than an assertion about it.
#
# C-T448-6. `run-all.sh`'s body is `{ ... } | tee TRANSCRIPT-A2-11.txt`, and tee TRUNCATES, so
# T433's APPENDED correction footer survived exactly until the next run of the script it
# documents. Measured here at BEFORE (marker 1 -> 0) and at AFTER, where the footer is emitted
# INSIDE the teed block and therefore reproduced by construction (marker >= 1 both times).
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298).
#   T455_SRC=<repo>  T455_SCRATCH=<dir OUTSIDE the repo>  T455_OUT=<dir> \
#   T455_BEFORE=<commit-ish without the fix>  T455_AFTER=<commit-ish with it> \
#   bash 10-t455-runall-and-footer.sh
#
# EXIT 0 both refs behaved as recorded.  EXIT 1 one did not.  EXIT 3 REFUSED.
set -u

SRC="${T455_SRC:?T455_SRC must name the source repository}"
SCRATCH="${T455_SCRATCH:?T455_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T455_OUT:?T455_OUT must name the directory to write transcripts into}"
BEFORE="${T455_BEFORE:?T455_BEFORE must name a commit-ish WITHOUT the F-6 fix}"
AFTER="${T455_AFTER:?T455_AFTER must name a commit-ish WITH it}"

RUNALL=".softhouse/reviews/A2-11/run-all.sh"
TRANSCRIPT=".softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt"
FOOTER="CORRECTION APPENDED TO A RECORD"
FOOTER_NEW="CORRECTION INDEX, REGENERATED ON EVERY RUN"

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t455-runall"
FAILURES=0

verdict() {
  if [ "$2" = "$3" ]; then echo "  OK   $1 = $2 (expected $3)"
  else echo "  BAD  $1 = $2, EXPECTED $3"; FAILURES=$((FAILURES + 1)); fi
}

prepare() {
  local ref="$1"
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
  fi
  git -C "$D" checkout --quiet --detach "$ref" || return 1
  git -C "$D" reset --quiet --hard "$ref" || return 1
  git -C "$D" clean -qfdx || return 1
  [ -f "$D/$RUNALL" ] || { echo "REFUSED: $RUNALL absent at $ref" >&2; return 1; }
  [ -f "$D/$TRANSCRIPT" ] || { echo "REFUSED: $TRANSCRIPT absent at $ref" >&2; return 1; }
  return 0
}

# section <case> <n> — the ACTUAL exit code recorded for section n in the VERDICT table, or
# UNPRINTED. Absence is never zero (P-84): a section that did not record a verdict did not run.
section() {
  local v
  v="$(awk -v n="$2" '$1==n && NF>=4 {print $3}' "$OUT/runall-$1.txt" | tail -1)"
  case "$v" in ''|*[!0-9]*) echo "UNPRINTED" ;; *) echo "$v" ;; esac
}

run_ref() {   # run_ref <case-name> <ref>
  local name="$1" ref="$2"
  prepare "$ref" || return 1
  FOOT_BEFORE_OLD="$(grep -c -F -- "$FOOTER" "$D/$TRANSCRIPT")"
  FOOT_BEFORE_NEW="$(grep -c -F -- "$FOOTER_NEW" "$D/$TRANSCRIPT")"
  ( cd "$D" && bash "$RUNALL" ) > "$OUT/runall-$name.txt" 2>&1
  RUNALL_RC=$?
  FOOT_AFTER_OLD="$(grep -c -F -- "$FOOTER" "$D/$TRANSCRIPT")"
  FOOT_AFTER_NEW="$(grep -c -F -- "$FOOTER_NEW" "$D/$TRANSCRIPT")"
  DEV="$(sed -n 's/^  sections run: [0-9]*    deviations: \([0-9]*\)$/\1/p' "$OUT/runall-$name.txt" | tail -1)"
  return 0
}

echo "############ T455 — run-all.sh at two refs: F-6, and the erased footer"
echo "  BEFORE = $BEFORE"
echo "  AFTER  = $AFTER"
echo

echo "--- BEFORE: unmodified, no F-6 fix ------------------------------------------------"
run_ref BEFORE "$BEFORE" || { echo "REFUSED: could not run the runner at BEFORE" >&2; exit 3; }
B_RC="$RUNALL_RC"; B_DEV="${DEV:-UNPRINTED}"
B_S9="$(section BEFORE 9)"; B_S10="$(section BEFORE 10)"
B_FOOT_PRE="$FOOT_BEFORE_OLD"; B_FOOT_POST="$FOOT_AFTER_OLD"
echo "  run-all.sh process exit            : $B_RC"
echo "  deviations                         : $B_DEV"
echo "  section  9 (adjudicate-section1.py): $B_S9   (adjudicated 0)"
echo "  section 10 (verify-capture-integrity.py): $B_S10   (adjudicated 0)"
echo "  T433's APPENDED footer in the tracked transcript: $B_FOOT_PRE before the run, $B_FOOT_POST after"
verdict "BEFORE section 9 is RED on an unmutated tree (F-6 reproduced)" "$B_S9" 1
verdict "BEFORE section 10 is unaffected by it" "$B_S10" 0
verdict "BEFORE the aggregate FAILS" "$B_RC" 1
verdict "BEFORE the appended footer is PRESENT in the committed transcript" "$B_FOOT_PRE" 1
verdict "BEFORE the run ERASES it — tee truncates (C-T448-6)" "$B_FOOT_POST" 0
echo

echo "--- AFTER: the search is fixed and the footer is emitted, not appended ------------"
run_ref AFTER "$AFTER" || { echo "REFUSED: could not run the runner at AFTER" >&2; exit 3; }
A_RC="$RUNALL_RC"; A_DEV="${DEV:-UNPRINTED}"
A_S9="$(section AFTER 9)"; A_S10="$(section AFTER 10)"
A_FOOT_PRE="$FOOT_BEFORE_NEW"; A_FOOT_POST="$FOOT_AFTER_NEW"
echo "  run-all.sh process exit            : $A_RC"
echo "  deviations                         : $A_DEV"
echo "  section  9 (adjudicate-section1.py): $A_S9   (adjudicated 0)"
echo "  section 10 (verify-capture-integrity.py): $A_S10   (adjudicated 0)"
echo "  REGENERATED footer in the transcript: $A_FOOT_PRE before the run, $A_FOOT_POST after"
verdict "AFTER section 9 is GREEN — the SEARCH was fixed, not the pin" "$A_S9" 0
verdict "AFTER section 10 is still green with the (iv-a) close and section 10 landed" "$A_S10" 0
verdict "AFTER the aggregate PASSES" "$A_RC" 0
verdict "AFTER deviations are zero" "$A_DEV" 0
verdict "AFTER the footer SURVIVES the run that used to erase it" "$A_FOOT_POST" 1
echo

echo "--- THE PIN DID NOT MOVE ----------------------------------------------------------"
PIN_B="$(grep -c -F -- 'sec 9 0 python3 "$DIR/adjudicate-section1.py"' "$D/$RUNALL")"
git -C "$D" checkout --quiet --detach "$BEFORE" && git -C "$D" reset --quiet --hard "$BEFORE" || {
  echo "REFUSED: could not return the clone to BEFORE to compare the pin." >&2; exit 3; }
PIN_A="$(grep -c -F -- 'sec 9 0 python3 "$DIR/adjudicate-section1.py"' "$D/$RUNALL")"
echo "  'sec 9 0' present at AFTER: $PIN_B   at BEFORE: $PIN_A"
verdict "section 9's ADJUDICATED VALUE is unchanged at AFTER" "$PIN_B" 1
verdict "and it was the same at BEFORE — a green obtained by moving a pin would show here" "$PIN_A" 1
echo

if [ "$FAILURES" -ne 0 ]; then
  echo "T455 RUNNER DRIVE: FAIL — $FAILURES assertion(s)."
  exit 1
fi
echo "T455 RUNNER DRIVE: PASS. run-all.sh goes $B_RC -> $A_RC across the fix; section 9 goes"
echo "$B_S9 -> $A_S9 with its adjudicated value untouched; section 10 stays 0 through the"
echo "(iv-a) close and the new tag-binding section; and the correction footer goes from"
echo "ERASED BY THE RUN to REPRODUCED BY IT."
exit 0
