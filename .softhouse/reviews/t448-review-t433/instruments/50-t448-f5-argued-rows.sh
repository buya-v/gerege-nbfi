#!/bin/bash
# T448 -- TURN T433's F-5 ARGUMENT INTO A MEASUREMENT.
#
# T433 changed one expectation in T393's tracked drive matrix
# (`.softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh`), drove that row
# and the control, and ARGUED the rest: "only two rows can change colour when ARM F is added".
# T433 calls this its own weakest link and files it as F-5.
#
# THE ARGUMENT IS CHEAPER TO MEASURE THAN T433 THOUGHT, and that is this file's whole point.
# T433 abandoned the re-run because it costs "26 whole run-all.sh runs". But the column the
# matrix grades is `sec10` -- the exit code of ONE command inside run-all.sh, read back out of
# the VERDICT table:
#
#     sec10="$(awk '/^  10 /{print $3}' "$OUT/case-$name-$ref.txt" | tail -1)"
#     sec 10 0 python3 "$DIR/verify-capture-integrity.py"
#
# `sec` records the exit status of exactly that command, so grading the command directly on the
# same mutated clone yields the same number in seconds instead of minutes. Nine argued rows
# become nine measurements. Only the AFTER column can move -- ARM F does not exist at BEFORE --
# so BEFORE is not re-run, and this file says so rather than implying it measured both.
#
# A CARDINAL T433 RESTATED AND GOT WRONG, WHICH IS WHY THIS FILE COUNTS IT (P-80): the matrix
# is ELEVEN cases, not thirteen -- `grep -c '^run_case ' 10-drive-conditions.sh` and the
# committed `out/drive/MATRIX.tsv` (22 data rows = 11 cases x 2 refs) both say 11. Two rows
# were driven, so NINE were argued, not eleven. This file asserts the population size before
# it reports anything about the rows, so the count cannot rot silently.
#
# ENGINE (P-33/P-53): `grep -c -F` for the fixed-string assertions; `grep -c -E '^run_case '`
# for the case count, an anchored POSIX ERE with no \b \d \s \w in it.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298):
#   T448_SRC=<repo>  T448_SCRATCH=<dir OUTSIDE the repo>  T448_OUT=<dir> \
#   T448_REF=<commit-ish carrying ARM F>  bash 50-t448-f5-argued-rows.sh
#
# CALIBRATION BEFORE ANY NEGATIVE (P-72; C4): the control row is graded FIRST and must be 0.
# A harness that is red on a clean clone makes every "as expected" below free.
#
# EXIT 0  every argued row produced the value T393's matrix records for it at AFTER.
# EXIT 1  at least one did not -- which would mean the argument was wrong and F-5 is real.
# EXIT 3  REFUSED: the harness could not run, or the case population is not the one described.
set -u

SRC="${T448_SRC:?T448_SRC must name the source repository}"
SCRATCH="${T448_SCRATCH:?T448_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T448_OUT:?T448_OUT must name the directory to write transcripts into}"
REF="${T448_REF:?T448_REF must name the commit-ish carrying ARM F}"

CAP=".softhouse/capture/tierA-a2"
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
MAN="$CAP/MANIFEST.sha256"
DRIVE=".softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh"
PICK=".softhouse/capture/t393-t382-conditions/instruments/11-pick-targets.py"
LAUNDER=".softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py"
MOVEFORK=".softhouse/capture/t393-t382-conditions/instruments/13-move-fork-constant.py"
FAB="T393-FABRICATED-OBSERVATION.http"

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t448-f5"
FAILURES=0

# ---- POPULATION ASSERTION (C3): the matrix must be the 11 cases this file claims. -----------
if [ ! -f "$SRC/$DRIVE" ]; then
  echo "REFUSED: $DRIVE is not in $SRC. There is no matrix to re-measure." >&2
  exit 3
fi
NCASES="$(grep -c -E '^run_case ' "$SRC/$DRIVE")"
if [ "$NCASES" != "11" ]; then
  echo "REFUSED: T393's matrix has $NCASES cases, not the 11 this file was written against." >&2
  echo "REFUSED: the argued-row population changed, so the nine rows below are not the nine." >&2
  exit 3
fi
echo "############ T448 -- F-5's ARGUED ROWS, MEASURED"
echo "  ref = $REF"
echo "  T393 matrix cases: $NCASES  (driven by T433: control, f1-13b  ->  ARGUED: 9)"
echo

if ! TARGETS="$(python3 "$SRC/$PICK")"; then
  echo "REFUSED: 11-pick-targets.py could not run in $SRC." >&2
  exit 3
fi
FORKOBS="$(printf '%s\n' "$TARGETS" | awk -F'\t' '$1=="FORKOBS"{print $2}')"
POSTFORK="$(printf '%s\n' "$TARGETS" | awk -F'\t' '$1=="POSTFORK"{print $2}')"
NONOBS="$(printf '%s\n' "$TARGETS" | awk -F'\t' '$1=="NONOBS"{print $2}')"
if [ -z "$FORKOBS" ] || [ -z "$POSTFORK" ] || [ -z "$NONOBS" ]; then
  echo "REFUSED: a mutation target came back EMPTY: [$FORKOBS] [$POSTFORK] [$NONOBS]." >&2
  exit 3
fi
echo "  targets: FORKOBS=$FORKOBS  POSTFORK=$POSTFORK  NONOBS=$NONOBS"
echo

prepare() {
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
    git -C "$D" config user.email "t448@softhouse.local" || return 1
    git -C "$D" config user.name "T448" || return 1
  fi
  git -C "$D" reset --quiet --hard || return 1
  git -C "$D" clean -qfdx || return 1
  git -C "$D" checkout --quiet --detach "$REF" || return 1
  git -C "$D" reset --quiet --hard "$REF" || return 1
  return 0
}

# ---- T393's mutations, re-spelled here so this file does not depend on sourcing theirs. -----
mut_control() { return 0; }

mut_f1_13() {
  printf '\nT393-MUTATION-MARKER\n' >> "$D/$CAP/$POSTFORK" || return 1
  git -C "$D" add -- "$CAP/$POSTFORK" || return 1
  git -C "$D" commit -q -m "T448/f1-13: committed mutation of a POST-FORK observation" || return 1
}
mut_f1_14() {
  git -C "$D" rm -q -- "$CAP/$POSTFORK" || return 1
  git -C "$D" commit -q -m "T448/f1-14: committed DELETION of a post-fork observation" || return 1
}
mut_f1_15() {
  printf 'HTTP/1.1 200 OK\r\n\r\n{"fabricated":true}\n' > "$D/$CAP/out/$FAB" || return 1
  git -C "$D" add -- "$CAP/out/$FAB" || return 1
  git -C "$D" commit -q -m "T448/f1-15: committed ADDITION of a fabricated observation" || return 1
}
mut_f1_16() {
  printf 'HTTP/1.1 200 OK\r\n\r\n{"fabricated":true}\n' > "$D/$CAP/out/$FAB" || return 1
  return 0
}
mut_f1_09() {
  local keep="$SCRATCH/t448-symlink-target"
  cp "$D/$CAP/$POSTFORK" "$keep" || return 1
  rm -f "$D/$CAP/$POSTFORK" || return 1
  ln -s "$keep" "$D/$CAP/$POSTFORK" || return 1
  return 0
}
mut_f4a() {
  printf '\nT393-MUTATION-MARKER\n' >> "$D/$CAP/$FORKOBS" || return 1
  git -C "$D" add -- "$CAP/$FORKOBS" || return 1
  git -C "$D" commit -q -m "T448/f4a: committed mutation of a FORK-SHA observation" || return 1
}
mut_f4b() {
  mut_f4a || return 1
  local probe old
  probe="$(git -C "$D" rev-parse HEAD)" || return 1
  old="$(python3 "$SRC/$MOVEFORK" "$D/$INT" "$probe")" || return 1
  echo "        FORK constant moved: $old -> $probe"
  return 0
}
mut_f3() {
  printf '\n# T393-MUTATION-MARKER\n' >> "$D/$CAP/$NONOBS" || return 1
  git -C "$D" add -- "$CAP/$NONOBS" || return 1
  git -C "$D" commit -q -m "T448/f3: committed mutation of a fork-sha NON-observation entry" || return 1
}
mut_f3b() {
  printf '\n# T393-MUTATION-MARKER\n' >> "$D/$CAP/$NONOBS" || return 1
  python3 "$SRC/$LAUNDER" "$D" "$NONOBS" > /dev/null || return 1
  git -C "$D" add -- "$CAP/$NONOBS" "$MAN" || return 1
  git -C "$D" commit -q -m "T448/f3b: fork-sha NON-observation mutated, manifest row rewritten" || return 1
}

run_row() {   # run_row <name> <mutfn> <expected sec10 at AFTER, from T393's committed MATRIX.tsv>
  local name="$1" mutfn="$2" want="$3" rc
  if ! prepare; then
    echo "REFUSED: could not prepare the clone at $REF for row $name." >&2
    exit 3
  fi
  if ! "$mutfn"; then
    echo "REFUSED: row $name could not apply its mutation. A row that did not mutate reports" >&2
    echo "REFUSED: the colour of a CLEAN clone, which is a control, not a measurement." >&2
    exit 3
  fi
  ( cd "$D" && python3 "$INT" ) > "$OUT/f5-row-$name.txt" 2>&1
  rc=$?
  local armf result
  armf="$(grep -c -F 'LAUNDERED-OR-MUTATED' "$OUT/f5-row-$name.txt")"
  result="matches T393's matrix"
  if [ "$rc" != "$want" ]; then
    result="*** MOVED -- F-5 IS REAL ***"
    FAILURES=$((FAILURES + 1))
  fi
  printf '  %-36s sec10=%s  armf-named=%s  T393 recorded %s   %s\n' \
    "$name" "$rc" "$armf" "$want" "$result"
}

# ---- CALIBRATION FIRST. ---------------------------------------------------------------------
run_row control mut_control 0
if ! grep -q -F "VERDICT: PASS" "$OUT/f5-row-control.txt"; then
  echo "REFUSED: P-72 CALIBRATION FAILED -- the unmutated clone at $REF did not grade PASS," >&2
  echo "REFUSED: so every row below would carry the harness's colour, not the tree's." >&2
  exit 3
fi
echo "  P-72 calibration OK: the unmutated clone grades PASS, exit 0."
echo
echo "  --- THE NINE ROWS T433 ARGUED RATHER THAN MEASURED, at the AFTER ref ---"

run_row f1-13-commit-mutate-postfork        mut_f1_13  1
run_row f1-14-commit-delete-postfork        mut_f1_14  1
run_row f1-15-commit-add-fabricated         mut_f1_15  1
run_row f1-16-untracked-fabricated          mut_f1_16  1
run_row f1-09-symlink-identical-bytes       mut_f1_09  1
run_row f4a-control-commit-mutate-forkobs   mut_f4a    1
run_row f4b-move-fork-constant              mut_f4b    2
run_row f3-commit-mutate-nonobs             mut_f3     1
run_row f3b-commit-mutate-nonobs-laundered  mut_f3b    1

echo
if [ "$FAILURES" -ne 0 ]; then
  echo "T448 F-5 VERDICT: $FAILURES of the nine argued rows MOVED at the AFTER ref. The argument"
  echo "did not hold and the full re-drive is required, not optional."
  exit 1
fi
echo "T448 F-5 VERDICT: all nine argued rows produce, with ARM F present, exactly the sec10"
echo "value T393's committed MATRIX.tsv records for them. T433's argument is CORRECT -- and it"
echo "is now a measurement rather than an argument, taken in seconds, because the column the"
echo "matrix grades is one command's exit code and not the whole runner's."
exit 0
