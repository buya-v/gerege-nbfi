#!/usr/bin/env bash
# =============================================================================================
# T452 -- A SIXTH CLASS MEMBER, FOUND BY THE RE-CLASSIFICATION AND BY NEITHER T442 NOR T447.
#
# `.softhouse/capture/t388-accrual-capture/30-casualty-sweep-t388.sh:83` is a P-72 POSITIVE
# CALIBRATION, ENFORCED at `exit 3`, whose known-positive string is spelled as a LITERAL IN THE
# SEARCHER'S OWN SOURCE and whose corpus is `.softhouse/capture/t388-accrual-capture/` -- the
# searcher's own task directory. It is SELF-ONLY: the ONE file in that corpus that carries the
# string is the script itself. So the assertion "the engine can find something here" is
# satisfied by the searcher's own bytes and by nothing else, and it would keep passing if every
# other file in the corpus were deleted.
#
# It is a STRONGER instance than `a2-33-dec2-rev5/sweep.sh` (F-T447-1), which at least has ten
# sibling carriers: this one is STRICTLY VACUOUS. It is PRESENT-direction and it is ENFORCED,
# which is the fail-OPEN half -- the silent one.
#
# WHY IT WAS MISSED. T442's census routes any pattern held in a `$VAR` into the RUNTIME bucket
# and counts it safe on syntax alone; the probe here is `$CALIB_POS_STR` and the pathspec is
# `$CALIB_POS_PATH`, so the row was invisible in BOTH operand positions.
#
# T452 CANNOT REPAIR IT: `.softhouse/capture/t388-accrual-capture/` is another task's grant.
# This drive is the RECORD that files it, with the numbers, so the next owner does not have to
# rediscover it. Paste-ready task entry is in the T452 handoff.
#
# EXIT 0 = the finding reproduces exactly as described. EXIT 1 = it does not (say so loudly).
# EXIT 2 = could not measure.
# =============================================================================================
set -uo pipefail
REPO=${T452_REPO:-$(git rev-parse --show-toplevel 2>/dev/null)} || REPO=""
[ -n "$REPO" ] || { echo "REFUSED: not inside a git work tree" >&2; exit 2; }
cd "$REPO" || exit 2

SUT='.softhouse/capture/t388-accrual-capture/30-casualty-sweep-t388.sh'
[ -r "$SUT" ] || { echo "REFUSED: cannot read $SUT" >&2; exit 2; }

FAILED=0
check() {
  printf '  %-56s expected=%-10s actual=%-10s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  [ "$2" = "$3" ] || FAILED=$((FAILED+1))
}

echo "=============================================================================="
echo "T452 -- T388 VACUOUS POSITIVE CALIBRATION"
echo "repo   : $REPO"
echo "commit : $(git rev-parse HEAD)"
echo "dirty  : $(git status --porcelain | grep -c '' | tr -d ' ') path(s)"
echo "subject: $SUT  sha256 $(shasum -a 256 "$SUT" | cut -c1-16)"
echo "=============================================================================="
echo

# The probe and the corpus are READ OUT OF THE SUBJECT, never retyped here: a drive that
# hard-codes the string it is grading stops grading the subject the moment the subject changes.
POS=$(LC_ALL=C sed -n "s/^CALIB_POS_STR='\(.*\)'\$/\1/p" "$SUT" | head -1)
PTH=$(LC_ALL=C sed -n "s/^CALIB_POS_PATH='\(.*\)'\$/\1/p" "$SUT" | head -1)
if [ -z "$POS" ] || [ -z "$PTH" ]; then
  echo "REFUSED: could not read CALIB_POS_STR / CALIB_POS_PATH out of the subject." >&2
  echo "         The subject has been edited; re-read it before trusting this drive." >&2
  exit 2
fi
echo "probe  read from the subject : '$POS'"
echo "corpus read from the subject : '$PTH'"
echo

n_in=$(git grep -c -F "$POS" -- "$PTH" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
f_in=$(git grep -l -F "$POS" -- "$PTH" 2>/dev/null | grep -c '')
f_self=$(git grep -l -F "$POS" -- "$PTH" 2>/dev/null | grep -c -x -F "$SUT")
f_tree=$(git grep -l -F "$POS" -- . 2>/dev/null | grep -c '')
corpus_n=$(git ls-files -- "$PTH" | grep -c '')
tree_n=$(git ls-files | grep -c '')
enforced=$(LC_ALL=C grep -c 'exit 3' "$SUT")
echo "matches of the probe in the calibration corpus     : $n_in in $f_in file(s)"
git grep -l -F "$POS" -- "$PTH" 2>/dev/null | sed 's/^/       /'
echo "of those files, the searcher itself                : $f_self"
echo "files carrying the probe ANYWHERE in the tree      : $f_tree   (tree-qualified: see header)"
echo "tracked files in the calibration corpus            : $corpus_n"
echo "tracked files in the repository                    : $tree_n"
echo "'exit 3' enforcement sites in the subject          : $enforced"
echo
check "the calibration matches at all"                 "yes" "$( [ "$n_in" -ge 1 ] && echo yes || echo no )"
check "SELF-ONLY: exactly one carrier"                 "1"   "$f_in"
check "and that carrier is the searcher"               "1"   "$f_self"
# --- THIS DRIVE IS A MEMBER OF THE CLASS IT MEASURES, and that is handled, not dodged.
# Publishing this transcript makes it a tracked carrier of the probe -- exactly `F-T447-3`. The
# handling is the one T452 argued for: DO NOT EXCLUDE (that is the immunisation anti-pattern),
# QUALIFY. The finding is asserted on the corpus THE SUBJECT'S OWN ASSERTION SEARCHES, which no
# publication of ours can enter, so `carriers == 1` is drift-stable. Carriers ELSEWHERE in the
# tree are asserted as a SET -- they may only be T452's own record -- so a new carrier anywhere
# else turns this drive RED instead of quietly softening the finding.
extra=$(git grep -l -F "$POS" -- . ":(exclude)$PTH" 2>/dev/null | grep -c '')
foreign=$(git grep -l -F "$POS" -- . ":(exclude)$PTH" 2>/dev/null \
          | grep -vc '^\.softhouse/capture/t452-t447-conditions/')
echo "carriers outside the subject's own calibration corpus : $extra"
git grep -l -F "$POS" -- . ":(exclude)$PTH" 2>/dev/null | sed 's/^/       /'
echo "of those, any that are NOT T452's own record          : $foreign"
check "carriers outside the corpus are only T452's record" "0" "$foreign"
check "the corpus it certifies is far larger"          "yes" "$( [ "$corpus_n" -gt 100 ] && echo yes || echo no )"
check "the assertion is ENFORCED (aborts on a miss)"   "yes" "$( [ "$enforced" -ge 1 ] && echo yes || echo no )"
echo

# NON-VACUITY OF THIS DRIVE (P-22): a probe that IS carried by other files must NOT be reported
# as self-only, or the check above would fire on anything.
CTRL='SWEEP CALIBRATE+'
c_files=$(git grep -l -F "$CTRL" -- .softhouse 2>/dev/null | grep -c '')
echo "control: a string that IS widely carried ('$CTRL') -> $c_files file(s)"
check "control is NOT self-only"                       "yes" "$( [ "$c_files" -gt 1 ] && echo yes || echo no )"
echo

echo "VERDICT: a P-72 positive calibration, PRESENT-direction and ENFORCED, whose only carrier"
echo "         is the searcher. STRICTLY VACUOUS: it would pass over an empty corpus. This is"
echo "         the fail-OPEN half of the C-T440-1 class, and it is LIVE and UNOWNED."
echo "         T452 has no grant here. Filed with an owner in the T452 handoff."
echo "=============================================================================="
echo "T452-T388-VACUOUS-RESULT: carriers=$f_in self=$f_self corpus=$corpus_n enforced=$enforced disagreements=$FAILED"
echo "=============================================================================="
[ "$FAILED" -eq 0 ] || exit 1
exit 0
