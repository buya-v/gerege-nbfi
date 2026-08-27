#!/usr/bin/env bash
# T299 -- DRIVE THE JSON-DESTINATION SAFETY OF 50-failopen-lint.py, FIVE ARMS.
#
# ENGINE (P-33/P-53): git ls-files / git status --porcelain / diff -u, GNU-free POSIX usage;
# `git --version` and `python3 --version` are printed below so the transcript names its engine.
#
# CALIBRATION (P-72), and it is the whole reason this drive is trustworthy: ARM 0 proves the
# defect was REAL and REPRODUCIBLE at the pre-fix bytes, in a scratch clone, by watching
# `git status --porcelain` go from empty to a modified TRACKED file. A drive that only ever
# shows the fixed state green cannot distinguish "fixed" from "never broken".
#
# WHAT EACH ARM ASSERTS
#   ARM 0  pre-fix bytes, bare run          -> tracked lint.json MODIFIED      (the defect)
#   ARM 1  post-fix bytes, bare run         -> tree carries no NEW dirty path  (the fix)
#   ARM 2  post-fix, explicit SCRATCH dest  -> NO divert; JSON written there   (no regression)
#   ARM 3  post-fix, explicit TRACKED dest  -> diverts; that file is untouched (the CLASS)
#   ARM 4  frontier bytes bare == override  -> the GRADED output is unchanged
#
# Corpus reachability is asserted before anything is measured, and every failure to reach it
# terminates with a non-zero exit rather than being reported as a result.
set -u

ROOT="$(git rev-parse --show-toplevel)" || exit 2
[ -n "$ROOT" ] || exit 2
cd "$ROOT" || exit 2
LINT=".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
TRACKED_DEFAULT=".softhouse/capture/t238-failopen/evidence/lint.json"
[ -f "$LINT" ] || { echo "ABORT(2): linter absent at $LINT"; exit 2; }
git ls-files --error-unmatch -- "$TRACKED_DEFAULT" >/dev/null || {
  echo "ABORT(2): $TRACKED_DEFAULT is not tracked; this drive's premise is gone."; exit 2; }

echo "T299 DESTINATION-SAFETY DRIVE"
echo "engine    : $(git --version) | $(python3 --version 2>&1)"
echo "repo      : $ROOT"
echo "HEAD      : $(git rev-parse HEAD)"
echo "linter    : $LINT"
echo "default   : $TRACKED_DEFAULT  [tracked: yes, asserted above]"
echo

SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/t299-drive.XXXXXXXX")" || exit 2
trap 'rm -rf "$SCRATCH"' EXIT

# ---------------------------------------------------------------- ARM 0 (CALIBRATION)
echo "=== ARM 0 -- CALIBRATION: the defect, on PRE-FIX bytes, in a scratch clone ==="
CLONE="$SCRATCH/prefix-clone"
git clone -q --no-hardlinks "$ROOT" "$CLONE" || { echo "ARM0 ABORT(2): clone failed"; exit 2; }
# The pre-fix bytes of the linter are the ones at the merge-base commit named below. They are
# extracted from git, never retyped.
BASE="${T299_PREFIX_COMMIT:-39d2156}"
( cd "$CLONE" && git show "$BASE:$LINT" > "$LINT" ) || { echo "ARM0 ABORT(2): extract failed"; exit 2; }
( cd "$CLONE" && git checkout -q -- "$LINT" 2>/dev/null; git show "$BASE:$LINT" > "$LINT" )
a0_before="$( cd "$CLONE" && git status --porcelain -- "$TRACKED_DEFAULT" | wc -l | tr -d ' ' )"
( cd "$CLONE" && python3 "$LINT" ) >"$SCRATCH/arm0.txt" 2>&1
a0_rc=$?
a0_after="$( cd "$CLONE" && git status --porcelain -- "$TRACKED_DEFAULT" | wc -l | tr -d ' ' )"
a0_stat="$( cd "$CLONE" && git diff --numstat -- "$TRACKED_DEFAULT" )"
echo "  pre-fix linter bytes from : $BASE"
echo "  dirty rows for the tracked default BEFORE run : $a0_before"
echo "  linter exit                                   : $a0_rc"
echo "  dirty rows for the tracked default AFTER  run : $a0_after"
echo "  git diff --numstat                            : ${a0_stat:-<empty>}"
if [ "$a0_before" -eq 0 ] && [ "$a0_after" -eq 1 ]; then
  echo "  ARM 0 RESULT: CALIBRATED -- the defect reproduces on pre-fix bytes."
else
  echo "  ARM 0 RESULT: **CALIBRATION LOST** -- the defect did not reproduce, so every"
  echo "                arm below is measuring something this drive cannot interpret."
  exit 1
fi
echo

# ---------------------------------------------------------------- ARM 1
echo "=== ARM 1 -- POST-FIX bare run must add NO dirty path ==="
git status --porcelain >"$SCRATCH/a1-before.txt"
python3 "$LINT" >"$SCRATCH/arm1.txt" 2>&1
a1_rc=$?
git status --porcelain >"$SCRATCH/a1-after.txt"
echo "  linter exit : $a1_rc"
echo "  dirty paths before : $(wc -l <"$SCRATCH/a1-before.txt" | tr -d ' ')"
echo "  dirty paths after  : $(wc -l <"$SCRATCH/a1-after.txt" | tr -d ' ')"
echo "  --- diff of the two porcelain listings ---"
if diff -u "$SCRATCH/a1-before.txt" "$SCRATCH/a1-after.txt" >"$SCRATCH/a1-diff.txt"; then
  echo "  (the two listings are byte-identical)"
  a1_ok=1
else
  cat "$SCRATCH/a1-diff.txt"
  a1_ok=0
fi
echo "  divert banner printed : $(grep -c 'JSON-DESTINATION DIVERTED' "$SCRATCH/arm1.txt")"
sed -n '/JSON-DESTINATION DIVERTED/,+4p' "$SCRATCH/arm1.txt" | sed 's/^/    /'
[ "$a1_ok" -eq 1 ] && echo "  ARM 1 RESULT: PASS" || { echo "  ARM 1 RESULT: FAIL"; exit 1; }
echo

# ---------------------------------------------------------------- ARM 2
echo "=== ARM 2 -- explicit SCRATCH destination must NOT divert (no regression) ==="
J2="$SCRATCH/arm2.json"
FAILOPEN_LINT_JSON="$J2" python3 "$LINT" >"$SCRATCH/arm2.txt" 2>&1
a2_rc=$?
a2_banner="$(grep -c 'JSON-DESTINATION DIVERTED' "$SCRATCH/arm2.txt")"
echo "  linter exit                : $a2_rc"
echo "  divert banner printed      : $a2_banner  (must be 0)"
echo "  bytes written to the asked-for path : $( [ -f "$J2" ] && wc -c <"$J2" | tr -d ' ' || echo MISSING )"
echo "  parses as JSON             : $(python3 -c 'import json,sys;json.load(open(sys.argv[1]));print("yes")' "$J2" 2>&1)"
[ "$a2_banner" -eq 0 ] && [ -s "$J2" ] && echo "  ARM 2 RESULT: PASS" || { echo "  ARM 2 RESULT: FAIL"; exit 1; }
echo

# ---------------------------------------------------------------- ARM 3
echo "=== ARM 3 -- an override AIMED AT A TRACKED FILE also diverts (the CLASS) ==="
for victim in "$TRACKED_DEFAULT" "CLAUDE.md" ".softhouse/patterns.md"; do
  vb="$(git status --porcelain -- "$victim" | wc -l | tr -d ' ')"
  FAILOPEN_LINT_JSON="$victim" python3 "$LINT" >"$SCRATCH/arm3.txt" 2>&1
  vrc=$?
  va="$(git status --porcelain -- "$victim" | wc -l | tr -d ' ')"
  vban="$(grep -c 'JSON-DESTINATION DIVERTED' "$SCRATCH/arm3.txt")"
  vdest="$(sed -n 's/^  written to: //p' "$SCRATCH/arm3.txt")"
  echo "  victim=$victim exit=$vrc banner=$vban dirty_before=$vb dirty_after=$va"
  echo "    diverted to: ${vdest:-<none>}"
  if [ "$vban" -ne 1 ] || [ "$va" -ne "$vb" ]; then
    echo "  ARM 3 RESULT: FAIL on $victim"; exit 1
  fi
done
echo "  ARM 3 RESULT: PASS"
echo

# ---------------------------------------------------------------- ARM 4
echo "=== ARM 4 -- the GRADED output (the frontier lines) is byte-identical either way ==="
grep '^FAILOPEN-FRONTIER ' "$SCRATCH/arm1.txt" | LC_ALL=C sort >"$SCRATCH/fr-bare.txt"
grep '^FAILOPEN-FRONTIER ' "$SCRATCH/arm2.txt" | LC_ALL=C sort >"$SCRATCH/fr-over.txt"
echo "  frontier rows, bare     : $(wc -l <"$SCRATCH/fr-bare.txt" | tr -d ' ')"
echo "  frontier rows, override : $(wc -l <"$SCRATCH/fr-over.txt" | tr -d ' ')"
if diff -u "$SCRATCH/fr-bare.txt" "$SCRATCH/fr-over.txt"; then
  echo "  ARM 4 RESULT: PASS -- the two frontiers are byte-identical"
else
  echo "  ARM 4 RESULT: FAIL -- diverting the JSON changed the graded output"; exit 1
fi
echo
echo "ALL FIVE ARMS PASSED."
