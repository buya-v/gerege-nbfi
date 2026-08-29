#!/bin/bash
# T448 -- INDEPENDENT DRIVES against ARM F (section 8 of
# .softhouse/reviews/A2-11/verify-capture-integrity.py), written for the review of T433.
#
# This file does NOT call T433's own drive. It re-drives the ONE control T433 leans on
# hardest (the vacuity control, claim 3) and it CONSTRUCTS the case T433 disclosed as
# undriven, boundary (iv-c): a post-fork observation DELETED and RE-ADDED.
#
# WHY (iv-c) MATTERS AND WHAT IS ACTUALLY BEING TESTED.  ARM F derives each observation's
# baseline from `git log HEAD --diff-filter=A --name-only`, walked newest-first with the LAST
# assignment winning -- i.e. the EARLIEST add is meant to win. A delete-and-re-add creates a
# SECOND add record for the same path. If git's default history simplification, or the
# newest-first walk, ever let the LATER add win, an attacker could reset ARM F's baseline to
# bytes they wrote and launder the manifest in the same commit -- the exact residual ARM F
# exists to catch, restored. T433 argued this away. This file measures it.
#
# ENGINE (P-33/P-53): git plumbing plus `grep -c -F` (fixed strings, no regex classes), so
# there is no \b \d \s \w to be read as a literal by the wrong engine.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298). Every location is a required parameter:
#
#   T448_SRC=<repo>  T448_SCRATCH=<dir OUTSIDE the repo>  T448_OUT=<dir> \
#   T448_REF=<commit-ish carrying ARM F>  bash 20-t448-armf-drives.sh
#
# CALIBRATION BEFORE ANY NEGATIVE (P-72; C4): the `control` case runs FIRST and must come back
# exit 0 on an unmutated clone. If it does not, the harness is broken and every RED below
# would be the harness's colour, not the tree's -- so the script REFUSES (exit 3) instead of
# reporting findings.
#
# EXIT 0  every case produced the exit code and the named reason recorded beside it.
# EXIT 1  at least one did not -- named, never counted only.
# EXIT 3  REFUSED: the harness could not run or its calibration failed. Never read as a pass.
set -u

SRC="${T448_SRC:?T448_SRC must name the source repository}"
SCRATCH="${T448_SCRATCH:?T448_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T448_OUT:?T448_OUT must name the directory to write transcripts into}"
REF="${T448_REF:?T448_REF must name the commit-ish carrying ARM F}"

CAP=".softhouse/capture/tierA-a2"
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
MAN="$CAP/MANIFEST.sha256"
PICK=".softhouse/capture/t393-t382-conditions/instruments/11-pick-targets.py"
LAUNDER=".softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py"

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t448-armf"
MATRIX="$OUT/MATRIX-t448.tsv"
printf 'case\trc\tverdict\tnamed\tat_tip\tmoved\tgraded\texpect\tresult\n' > "$MATRIX" || exit 3

if ! TARGETS="$(python3 "$SRC/$PICK")"; then
  echo "REFUSED: 11-pick-targets.py could not run in $SRC. The mutation target is MEASURED," >&2
  echo "REFUSED: never typed, so without it there is no case to drive." >&2
  exit 3
fi
POSTFORK="$(printf '%s\n' "$TARGETS" | awk -F'\t' '$1=="POSTFORK"{print $2}')"
if [ -z "$POSTFORK" ]; then
  echo "REFUSED: the POSTFORK mutation target came back EMPTY. A drive with no target mutates" >&2
  echo "REFUSED: nothing and reports the colour of a clean tree, which is a null control." >&2
  exit 3
fi

echo "############ T448 INDEPENDENT ARM-F DRIVES"
echo "  ref                        = $REF"
echo "  post-fork mutation target  = $POSTFORK   (MEASURED by 11-pick-targets.py)"
echo

FAILURES=0

prepare() {
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
    git -C "$D" config user.email "t448@softhouse.local" || return 1
    git -C "$D" config user.name "T448" || return 1
  fi
  git -C "$D" checkout --quiet --detach "$REF" || return 1
  git -C "$D" reset --quiet --hard "$REF" || return 1
  git -C "$D" clean -qfdx || return 1
  return 0
}

launder() {   # launder <relpath-under-CAP> : rewrite that file's MANIFEST.sha256 row to agree
  python3 "$D/$LAUNDER" "$D" "$1" > /dev/null || return 1
  return 0
}

mut_none() { return 0; }

mut_vacuity() {   # RE-DRIVE of T433's claim 3: every birth commit becomes the tip
  git -C "$D" checkout -q --detach || return 1
  git -C "$D" branch -q -D t448-vacuity 2>/dev/null
  git -C "$D" checkout -q --orphan t448-vacuity || return 1
  git -C "$D" add -A || return 1
  git -C "$D" commit -q -m "T448 vacuity re-drive: every tracked path re-added in ONE commit" || return 1
  return 0
}

mut_ivc_identical() {   # (iv-c) as T433 disclosed it: delete, then re-add the SAME bytes
  git -C "$D" show "HEAD:$CAP/$POSTFORK" > "$SCRATCH/ivc-keep.bytes" || return 1
  git -C "$D" rm -q -- "$CAP/$POSTFORK" || return 1
  git -C "$D" commit -q -m "T448 (iv-c) step 1: the post-fork observation DELETED" || return 1
  cp "$SCRATCH/ivc-keep.bytes" "$D/$CAP/$POSTFORK" || return 1
  git -C "$D" add -- "$CAP/$POSTFORK" || return 1
  git -C "$D" commit -q -m "T448 (iv-c) step 2: RE-ADDED with byte-identical content" || return 1
  return 0
}

mut_ivc_mutated() {     # (iv-c) WEAPONISED: delete, re-add MUTATED, launder the manifest row
  git -C "$D" show "HEAD:$CAP/$POSTFORK" > "$SCRATCH/ivc-keep.bytes" || return 1
  git -C "$D" rm -q -- "$CAP/$POSTFORK" || return 1
  git -C "$D" commit -q -m "T448 (iv-c2) step 1: the post-fork observation DELETED" || return 1
  cp "$SCRATCH/ivc-keep.bytes" "$D/$CAP/$POSTFORK" || return 1
  printf '\nT448-IVC2-MUTATION-MARKER\n' >> "$D/$CAP/$POSTFORK" || return 1
  launder "$POSTFORK" || return 1
  git -C "$D" add -- "$CAP/$POSTFORK" "$MAN" || return 1
  git -C "$D" commit -q -m "T448 (iv-c2) step 2: RE-ADDED with MUTATED bytes, manifest row laundered in the SAME commit" || return 1
  return 0
}

mut_ivc_relay() {       # (iv-c3): delete, re-add IDENTICAL, then mutate+launder in a THIRD commit
  mut_ivc_identical || return 1
  printf '\nT448-IVC3-MUTATION-MARKER\n' >> "$D/$CAP/$POSTFORK" || return 1
  launder "$POSTFORK" || return 1
  git -C "$D" add -- "$CAP/$POSTFORK" "$MAN" || return 1
  git -C "$D" commit -q -m "T448 (iv-c3) step 3: mutated and laundered AFTER the re-add" || return 1
  return 0
}

mut_ivc_wholly_new() {  # (iv-c4): delete, then re-add bytes bearing NO similarity to the original
  git -C "$D" rm -q -- "$CAP/$POSTFORK" || return 1
  git -C "$D" commit -q -m "T448 (iv-c4) step 1: the post-fork observation DELETED" || return 1
  printf 'T448 (iv-c4): every byte of this observation is new. No similarity to the original.\n' \
    > "$D/$CAP/$POSTFORK" || return 1
  launder "$POSTFORK" || return 1
  git -C "$D" add -- "$CAP/$POSTFORK" "$MAN" || return 1
  git -C "$D" commit -q -m "T448 (iv-c4) step 2: RE-ADDED with wholly new bytes, manifest laundered" || return 1
  return 0
}

run_case() {   # run_case <name> <mutfn> <expected_rc>
  local name="$1" mutfn="$2" want="$3" rc t
  if ! prepare; then
    echo "REFUSED: could not prepare the clone at $REF." >&2
    exit 3
  fi
  if ! "$mutfn"; then
    echo "REFUSED: case $name could not apply its mutation. A case that did not mutate reports" >&2
    echo "REFUSED: the colour of a CLEAN tree, which is a null control, not a finding." >&2
    exit 3
  fi
  t="$OUT/t448-case-$name.txt"
  ( cd "$D" && python3 "$INT" ) > "$t" 2>&1
  rc=$?
  local verdict named at_tip moved graded result
  verdict="$(sed -n 's/^VERDICT: \([A-Z]*\).*/\1/p' "$t" | tail -1)"
  named="$(grep -c -F 'LAUNDERED-OR-MUTATED' "$t")"
  at_tip="$(grep -c -F 'UNGRADED-BORN-AT-TIP' "$t")"
  moved="$(grep -c -F 'ADJUDICATION MOVED' "$t")"
  graded="$(sed -n 's/^      GRADED against a birth blob older than HEAD *: \([0-9]*\)$/\1/p' "$t")"
  result="as expected"
  if [ "$rc" != "$want" ]; then
    result="*** UNEXPECTED ***"
    FAILURES=$((FAILURES + 1))
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$name" "$rc" "${verdict:-none}" "$named" "$at_tip" "$moved" "${graded:-none}" "$want" "$result" >> "$MATRIX"
  printf '  %-34s rc=%s %-8s named=%s tip=%s moved=%s graded=%s  expected %s  %s\n' \
    "$name" "$rc" "${verdict:-none}" "$named" "$at_tip" "$moved" "${graded:-none}" "$want" "$result"
}

# ---- CALIBRATION FIRST. An unmutated clone must come back GREEN, or nothing below means -----
# ---- anything: a harness that is red on a clean tree makes every case red for free. ---------
run_case control mut_none 0
CTRL_RC="$(awk -F'\t' '$1=="control"{print $2}' "$MATRIX")"
if [ "$CTRL_RC" != "0" ]; then
  echo "REFUSED: P-72 CALIBRATION FAILED. The unmutated clone graded rc=$CTRL_RC, not 0." >&2
  echo "REFUSED: every RED below would be the harness's colour and not the tree's." >&2
  exit 3
fi
echo "  P-72 calibration OK: the unmutated clone at $REF grades exit 0."
echo

# ---- CLAIM 3, RE-DRIVEN. An arm that grades 0 rows and reports success is the defect. -------
run_case vacuity-redrive        mut_vacuity          1
# ---- BOUNDARY (iv-c), which T433 disclosed as NOT DRIVEN. -----------------------------------
run_case ivc1-readd-identical   mut_ivc_identical    0
run_case ivc2-readd-mutated     mut_ivc_mutated      1
run_case ivc3-readd-then-mutate mut_ivc_relay        1
run_case ivc4-readd-wholly-new  mut_ivc_wholly_new   1

echo
echo "############ MATRIX"
column -t -s "$(printf '\t')" "$MATRIX" 2>/dev/null || cat "$MATRIX"
echo
echo "unexpected exit codes: $FAILURES"

# ---- A case can be the right colour for the wrong reason. Assert the REASON, by name. -------
REASONS=0
chk() {   # chk <label> <transcript basename> <fixed string> <expected count>
  local got
  got="$(grep -c -F -- "$3" "$OUT/$2")"
  if [ "$got" = "$4" ]; then
    echo "  OK   $1  ($3 x$got)"
  else
    echo "  BAD  $1 -- expected x$4, got x$got: $3"
    REASONS=$((REASONS + 1))
  fi
}
echo "############ REASONS, not just colours"
chk "control: ARM F graded the whole post-fork population and named nothing" \
    "t448-case-control.txt" "DIFFER and are NOT adjudicated               : 0" 1
chk "vacuity: ARM F graded ZERO rows" \
    "t448-case-vacuity-redrive.txt" "GRADED against a birth blob older than HEAD     : 0" 1
chk "vacuity: section 9's f_graded>0 control is the thing that FAILED" \
    "t448-case-vacuity-redrive.txt" "FAIL  ARM F actually GRADED" 1
chk "iv-c1: a byte-identical re-add leaves the EARLIEST add as the baseline, nothing named" \
    "t448-case-ivc1-readd-identical.txt" "LAUNDERED-OR-MUTATED" 0
chk "iv-c2: the WEAPONISED re-add is CAUGHT and NAMED, not silently rebaselined" \
    "t448-case-ivc2-readd-mutated.txt" "LAUNDERED-OR-MUTATED $POSTFORK" 1
chk "iv-c3: mutating AFTER a clean re-add is caught too" \
    "t448-case-ivc3-readd-then-mutate.txt" "LAUNDERED-OR-MUTATED $POSTFORK" 1
chk "iv-c4: a re-add with NO similarity to the original is still caught" \
    "t448-case-ivc4-readd-wholly-new.txt" "LAUNDERED-OR-MUTATED $POSTFORK" 1

echo
if [ "$FAILURES" -ne 0 ] || [ "$REASONS" -ne 0 ]; then
  echo "T448 ARM-F DRIVES VERDICT: FAIL -- $FAILURES wrong exit code(s), $REASONS wrong reason(s)."
  exit 1
fi
echo "T448 ARM-F DRIVES VERDICT: PASS."
exit 0
