#!/bin/bash
# T481 -- WHAT T472 CONFIRMED AND T476 SAYS IT DID NOT MOVE. RE-DRIVEN, NOT RE-ARGUED.
#
# T476 changed the payload predicate that these controls sit around, in the same review
# directory, so "it did not move" is a claim about a tree and is measured here on trees I
# build. Every cardinal is re-counted; none is quoted from T467's handoff, T472's review or
# T476's.
#
# THREE ARMS:
#   A  the CLEAN tree at the tip           -- exit 0, checks, (a)-(k), ALL controls
#   B  a TRACKED non-JSON vector carrying the token -- the fail-closed branch reached BY A
#      VALUE: exit 1, traceback x0, every check still executed, a FAILURES: tally line
#   C  CONTROL (l)'s FALSIFIABILITY -- T455's exact `int` return restored on a CLEAN corpus.
#      If (l) and (l1) go RED while (k) stays GREEN on the same tree, (l) is a control and
#      not (k) wearing a new number. This is the only arm that answers that question.
#
# Arm C's edit REFUSES if its anchor is absent: a no-op must never read as a pass.
# NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL (P-103).
#
#   T481_SRC=<repo> T481_SCRATCH=<dir OUTSIDE the repo> T481_T476=<ref> \
#   bash 70-t481-failclosed-nonregression.sh
#
# EXIT 0 every cardinal reproduced.  EXIT 1 one did not.  EXIT 3 REFUSED.
set -u

SRC="${T481_SRC:?T481_SRC must name the source repository}"
SCRATCH="${T481_SCRATCH:?T481_SCRATCH must name a scratch directory OUTSIDE the repository}"
R476="${T481_T476:?T481_T476 must name the ref under test}"

S=".softhouse"
ADJ="$S/reviews/A2-11/adjudicate-section1.py"
VEC="$S/vectors"
PROBE="T481-NON-JSON-PROBE.md"
TOKEN="paymentChannelToFundSourceMappings"
D="$SCRATCH/t481-failclosed"
FAILURES=0

verdict() {
  if [ "$2" = "$3" ]; then echo "  OK   $1 = $2 (expected $3)"
  else echo "  BAD  $1 = $2, EXPECTED $3"; FAILURES=$((FAILURES + 1)); fi
}

prepare() {
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
  fi
  git -C "$D" checkout --quiet --force --detach "$R476" >/dev/null 2>&1 || return 1
  git -C "$D" reset --quiet --hard "$R476" || return 1
  git -C "$D" clean -qfdx || return 1
  git -C "$D" config user.email t481@softhouse.invalid || return 1
  git -C "$D" config user.name "T481 drive" || return 1
  [ -f "$D/$ADJ" ] && [ -d "$D/$VEC" ]
}

run_adj() {
  ( cd "$D" && python3 "$ADJ" ) > "$SCRATCH/fc-$1.txt" 2>&1
  echo "$?"
}
checks()  { grep -c -E '^  (PASS|FAIL)' "$SCRATCH/fc-$1.txt"; }
tally()   { grep -c '^FAILURES:' "$SCRATCH/fc-$1.txt"; }
trace()   { grep -c '^Traceback (most recent call last):' "$SCRATCH/fc-$1.txt"; }
# The FAILING CHECK, not the sentence. My first draft counted the sentence and got 2: the
# adjudicator prints it once as a `FAIL  ` line and once in its `FAILURES:` list, so the
# sentence count is 2 while the named failing check is 1. Counting the wrong thing is how a
# reviewer manufactures a finding out of a formatting detail; anchored on the prefix instead.
named()   { grep -c -E '^  FAIL  NO vector in the store USES any of these tokens' "$SCRATCH/fc-$1.txt"; }
state()   { grep -E "^  (PASS|FAIL)  $2" "$SCRATCH/fc-$1.txt" | head -1 | awk '{print $1}'; }

# The controls, counted by their own printed labels rather than by position, so a renamed or
# reordered control is a MISS and not a silent pass.
AK='(a) a FOURTH failure|(b) an adjudicated failure|(c) a section 1 that went GREEN|(d) a transcript with NO|(e) the offline prover TRIPS|(f) the offline prover TRIPS on the subprocess|(g) the offline prover does NOT trip|(h) a token used as an object KEY|(i) a token inside an IDENTIFIER-SHAPED value|(j) a token inside a PROSE sentence|(k) a file that does NOT parse as JSON'
T467C='(l) the UNPARSEABLE branch is reached BY A VALUE|(l1) EVERY location this file emits is a STRING|(l2) an identifier-shaped value with ONE TRAILING SPACE|(m) THE LIMIT, ASSERTED SO IT CANNOT DRIFT'
count_labels() {   # count_labels <file> <alternation>
  local n=0 IFS='|' c
  for c in $2; do
    if grep -q -F -- "$c" "$SCRATCH/fc-$1.txt"; then n=$((n + 1)); fi
  done
  echo "$n"
}

echo "==========================================================================="
echo "T481 -- THE FAIL-CLOSED BRANCH, NON-REGRESSION AT $R476"
echo "==========================================================================="
echo
echo "--- ARM A: THE CLEAN TREE ---"
prepare || { echo "REFUSED: could not prepare" >&2; exit 3; }
A_RC="$(run_adj A)"
verdict "clean: exit"                    "$A_RC" 0
verdict "clean: checks executed"         "$(checks A)" 29
verdict "clean: controls (a)-(k)"        "$(count_labels A "$AK")" 11
verdict "clean: ALL controls (a)-(m)"    "$(( $(count_labels A "$AK") + $(count_labels A "$T467C") ))" 15
verdict "clean: tracebacks"              "$(trace A)" 0
echo

echo "--- ARM B: A TRACKED NON-JSON VECTOR CARRYING THE TOKEN ---"
prepare || exit 3
printf '# a note that mentions %s in prose, in a file no JSON parser will accept\n' \
  "$TOKEN" > "$D/$VEC/$PROBE" || exit 3
git -C "$D" add -- "$VEC/$PROBE" || exit 3
git -C "$D" commit -q -m "T481 drive: a TRACKED non-JSON vector carrying a token" || exit 3
B_RC="$(run_adj B)"
verdict "planted: exit"                        "$B_RC" 1
verdict "planted: tracebacks (BY A VALUE)"     "$(trace B)" 0
verdict "planted: checks executed (none skipped)" "$(checks B)" 29
verdict "planted: controls (a)-(k) reached"    "$(count_labels B "$AK")" 11
verdict "planted: FAILURES: tally lines"       "$(tally B)" 1
verdict "planted: the NAMED assertion appears" "$(named B)" 1
echo

echo "--- ARM C: IS (l) A CONTROL, OR (k) WEARING A NEW NUMBER? ---"
prepare || exit 3
python3 - "$D/$ADJ" <<'PYEOF'
import ast, sys
path = sys.argv[1]
src = open(path, encoding="utf-8").read()
OLD = ('        return ([("UNPARSEABLE", "<raw substring, %d hit(s), %s>"\n'
       '                  % (n, type(exc).__name__))], [])\n')
NEW = '        return ([("UNPARSEABLE", n)], [])\n'
if OLD not in src:
    sys.stderr.write("REFUSED: the anchor is absent; the edit would be a no-op and a "
                     "no-op must never read as a pass.\n")
    sys.exit(3)
out = src.replace(OLD, NEW, 1)
ast.parse(out)
open(path, "w", encoding="utf-8").write(out)
PYEOF
if [ $? -ne 0 ]; then echo "REFUSED: could not restore the defect" >&2; exit 3; fi
C_RC="$(run_adj C)"
verdict "defect restored, CLEAN corpus: exit"        "$C_RC" 1
verdict "defect restored: tracebacks"                "$(trace C)" 0
verdict "defect restored: checks executed"           "$(checks C)" 29
verdict "defect restored: (k) still PASSES"          "$(state C '\(k\) a file that does NOT parse')" PASS
verdict "defect restored: (l) FAILS"                 "$(state C '\(l\) the UNPARSEABLE branch')" FAIL
verdict "defect restored: (l1) FAILS"                "$(state C '\(l1\) EVERY location')" FAIL
echo
echo "  Row by row: on a corpus where NOTHING real exercises the branch, (l) and (l1) go RED"
echo "  while (k) stays GREEN on the same tree. That is the property (k) lacked, and it still"
echo "  holds at a tip whose payload predicate has been rewritten around it."
echo

if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: every cardinal reproduced. EXIT 0"
  exit 0
fi
echo "RESULT: $FAILURES cardinal(s) did not reproduce. EXIT 1"
exit 1
