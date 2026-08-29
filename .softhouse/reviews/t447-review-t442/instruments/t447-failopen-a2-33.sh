#!/usr/bin/env bash
# =============================================================================================
# T447 -- F-T447-1: the ONE row in T442's RUNTIME blind spot that is a PRESENT-assertion in the
# family-only shape, and that nobody adjudicated.
#
# MY FIRST HYPOTHESIS WAS FALSIFIED BY THIS DRIVE AND THAT RUN IS KEPT:
# out/T447-A2-33-HYPOTHESIS-FALSIFIED.txt. I asserted the calibration below was carried by TWO
# files (the searcher and one sibling) -- that number came from T442's census, whose
# matching_files() re-runs every candidate with `git grep -l -F`, CASE-SENSITIVELY, and so does
# not reproduce this row's actual flags (`-I -i -E`). Measured with the row's OWN flags the hit
# set is ELEVEN files. The calibration is therefore NOT vacuous-by-self-match, and T442's
# "0 invert fail-OPEN" is NOT falsified by it. Recording the falsification because a review that
# only reports the hypotheses that survived is not a measurement.
#
# WHAT IS TRUE, AND IS THE FINDING:
# `.softhouse/reviews/a2-33-dec2-rev5/sweep.sh:61` is a P-72 POSITIVE calibration -- an
# assertion that a token must be PRESENT, enforced at exit 92 -- whose entire corpus is the
# SEARCHER'S OWN TASK DIRECTORY, while the sweep it is calibrating searches the WHOLE TREE:
#
#     CAL_RE='a2-33'
#     CAL_N=$(git grep -c -I -i -E "$CAL_RE" -- .softhouse/reviews/a2-33-dec2-rev5 | awk ...)
#     [ "${CAL_N:-0}" -lt 1 ] && exit 92        # <- PRESENT, enforced
#     ...
#     out=$(git grep -n -I -i -E "$re" -- . 2>&1)     # <- the sweep proper: the WHOLE TREE
#
# That is precisely the shape T442's own census prints a warning for:
#     "*** EVERY match lies inside the searcher's OWN task directory: a PRESENT-assertion here
#      would be satisfied only by the author's own artefacts -- the VACUOUS-PASS / fail-OPEN
#      shape. Adjudicate the direction."
# T442 flagged 3 family-only rows and adjudicated all 3 as ABSENT-assertions. This is a FOURTH,
# it is PRESENT-direction, and it was never flagged -- because the pattern is spelled `$CAL_RE`
# and the census's literal extractor cannot see through a variable, so the row went into the
# RUNTIME bucket that T442's own handoff concedes is "counted safe on syntax alone".
#
# WHY IT MATTERS: the defect this calibration was ADDED to catch (by the T238 repair, see the
# subject's own header) is a CORPUS-REACH failure -- a hard-coded, later-deleted worktree path
# that made the sweep print "(no hits)" for all 34 patterns and exit 0. A calibration whose
# corpus is the task's own directory cannot detect a failure to reach the corpus the sweep
# actually searches. Fail direction: it PASSES when the thing it exists to check is not checked.
#
# Exit 0 = every arm came out as declared. Exit 1 = an arm disagreed. Exit 2 = could not measure.
# =============================================================================================
set -uo pipefail
REPO=$(git rev-parse --show-toplevel) || exit 2
cd "$REPO" || exit 2
SUT='.softhouse/reviews/a2-33-dec2-rev5/sweep.sh'
DIR='.softhouse/reviews/a2-33-dec2-rev5'
[ -r "$SUT" ] || { echo "REFUSED: cannot read $SUT" >&2; exit 2; }
FAILED=0

check() {
  printf '  %-58s expected=%-10s actual=%-10s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  [ "$2" = "$3" ] || FAILED=$((FAILED+1))
}

echo "=============================================================================="
echo "T447 F-T447-1 -- an ENFORCED present-assertion whose corpus is its own task dir"
echo "=============================================================================="
echo "repo   : $REPO"
echo "commit : $(git rev-parse HEAD)"
echo "subject: $SUT:61   (the P-72 positive calibration, enforced at exit 92)"
echo

# Located BY CONTENT; the drive refuses if the anchors have moved.
a1=$(grep -c -F "CAL_RE='a2-33'" "$SUT")
a2=$(grep -c -F 'git grep -c -I -i -E "$CAL_RE" -- .softhouse/reviews/a2-33-dec2-rev5' "$SUT")
a3=$(grep -c -F 'out=$(git grep -n -I -i -E "$re" -- . 2>&1)' "$SUT")
a4=$(grep -c -F 'exit 92' "$SUT")
check "anchor: CAL_RE='a2-33'"                        "1"   "$a1"
check "anchor: the calibration's pathspec is its own dir" "1" "$a2"
check "anchor: the SWEEP's pathspec is the whole tree ('-- .')" "1" "$a3"
check "anchor: the calibration is ENFORCED (exit 92)"  "yes" "$( [ "${a4:-0}" -ge 1 ] && echo yes || echo no )"
[ "$a1" = "1" ] || { echo "REFUSED: subject has moved" >&2; exit 2; }

CAL_RE='a2-33'

echo
echo "ARM A  the calibration exactly as shipped (its own flags: -c -I -i -E)"
A=$(git grep -c -I -i -E "$CAL_RE" -- "$DIR" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
A_FILES=$(git grep -l -I -i -E "$CAL_RE" -- "$DIR" 2>/dev/null | grep -c '.')
echo "         matches=$A across $A_FILES file(s)"
check "ARM A: the calibration PASSES (>=1)" "yes" "$( [ "${A:-0}" -ge 1 ] && echo yes || echo no )"

echo
echo "ARM B  FAMILY-ONLY: is every matching file inside the searcher's own task directory?"
OUTSIDE=$(git grep -l -I -i -E "$CAL_RE" -- "$DIR" 2>/dev/null | grep -v "^$DIR/" | grep -c '.')
echo "         matching files OUTSIDE $DIR : $OUTSIDE"
check "ARM B: family-only (0 outside its own task dir)" "0" "$OUTSIDE"
echo "         => T442's census prints the fail-OPEN warning for exactly this shape."

echo
echo "ARM C  SELF-CARRIED COMPONENT: does the searcher's own body satisfy the assertion alone?"
B=$(git grep -c -I -i -E "$CAL_RE" -- "$SUT" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
echo "         matches in the searcher alone = $B"
check "ARM C: the searcher alone would satisfy it" "yes" "$( [ "${B:-0}" -ge 1 ] && echo yes || echo no )"
echo "         (NB: 10 sibling files also carry it, so this is UNDER-SCOPED, not vacuous.)"

echo
echo "ARM D  SCOPE GAP: the calibration's corpus vs the corpus the SWEEP actually searches"
CAL_N=$(git ls-files -- "$DIR" | grep -c '.')
SWP_N=$(git ls-files | grep -c '.')
echo "         tracked files the CALIBRATION can see : $CAL_N"
echo "         tracked files the SWEEP searches ('-- .') : $SWP_N"
check "ARM D: the calibration covers a STRICT SUBSET of the sweep's corpus" "yes" \
      "$( [ "${CAL_N:-0}" -lt "${SWP_N:-0}" ] && echo yes || echo no )"
echo "         => the calibration cannot demonstrate that the sweep's corpus is reachable,"
echo "            which is the exact failure the T238 repair added it to catch."

echo
echo "ARM E  CONTROL, a runtime-assembled token that is genuinely absent"
D_TOK="zzq-t447-control-$$-${RANDOM}-$(date -u +%s)"
git grep -q -F -e "$D_TOK" -- "$DIR" >/dev/null 2>&1; d_rc=$?
echo "         probe=$D_TOK  rc=$d_rc"
check "ARM E: a genuinely absent token returns rc 1" "1" "$d_rc"
echo "         => the engine is not matching everything; ARM A's pass is a real match."

echo
echo "=============================================================================="
printf 'T447-FAILOPEN-A2-33-RESULT: disagreements=%s\n' "$FAILED"
if [ "$FAILED" -gt 0 ]; then echo "*** THIS DRIVE FAILED."; exit 1; fi
echo "Reproduced: an ENFORCED present-assertion, family-only, over a strict subset of the"
echo "corpus it calibrates -- the shape T442's census says must be adjudicated, and did not see."
exit 0
