#!/bin/bash
# T476 -- WHAT T472 CONFIRMED MUST STAY TRUE. A NON-REGRESSION RE-DRIVE, NOT A RE-ARGUMENT.
#
# T472 re-derived F-T464-2 independently and it survived in full: the fail-closed branch is
# reached BY A VALUE, the 15 checks the traceback used to skip all run, and control (l) is a
# real control rather than (k) renamed -- restoring T455's exact `int` return on a CLEAN
# corpus makes (l) and (l1) FAIL while (k) still PASSES on the same tree.
#
# T476 touches a DIFFERENT file (the section-10 predicate in verify-capture-integrity.py) and
# must not have moved any of it. "Must not have moved" is a claim about a tree, so it is
# measured here rather than reasoned about. Every cardinal below is re-counted on the tree
# under test; none is quoted from T467's handoff or T472's review.
#
# NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL (P-103). Every `echo` quotes its argument.
#
#   T476_SRC=<repo>  T476_SCRATCH=<dir OUTSIDE the repo>  T476_T476=<commit-ish> \
#   bash 40-t476-failclosed-nonregression.sh
#
# EXIT 0 every cardinal reproduced.  EXIT 1 one did not.  EXIT 3 REFUSED.
set -u

SRC="${T476_SRC:?T476_SRC must name the source repository}"
SCRATCH="${T476_SCRATCH:?T476_SCRATCH must name a scratch directory OUTSIDE the repository}"
R476="${T476_T476:?T476_T476 must name the commit-ish under test}"

S=".softhouse"
ADJ="$S/reviews/A2-11/adjudicate-section1.py"
VEC="$S/vectors"
PROBE_NAME="T476-NON-JSON-PROBE.md"
TOKEN="paymentChannelToFundSourceMappings"
D="$SCRATCH/t476-failclosed"
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
  git -C "$D" checkout --quiet --force --detach "$1" || return 1
  git -C "$D" reset --quiet --hard "$1" || return 1
  git -C "$D" clean -qfdx || return 1
  [ -f "$D/$ADJ" ] || { echo "REFUSED: the adjudicator is absent at $1" >&2; return 1; }
  [ -d "$D/$VEC" ] || { echo "REFUSED: the vector store is absent at $1" >&2; return 1; }
  git -C "$D" config user.email t476@softhouse.invalid || return 1
  git -C "$D" config user.name "T476 drive" || return 1
}

plant() {
  printf '# a note that mentions %s in prose, in a file no JSON parser will accept\n' \
    "$TOKEN" > "$D/$VEC/$PROBE_NAME" || return 1
  git -C "$D" add -- "$VEC/$PROBE_NAME" || return 1
  git -C "$D" commit -q -m "T476 drive: a TRACKED non-JSON vector file carrying a token"
}

run_adj() {
  ( cd "$D" && python3 "$ADJ" ) > "$SCRATCH/fc-$1.txt" 2>&1
  echo "$?"
}

checks_run()  { grep -c -E '^  (PASS|FAIL)' "$SCRATCH/fc-$1.txt"; }
tally_lines() { grep -c '^FAILURES:' "$SCRATCH/fc-$1.txt"; }
traceback()   { grep -c '^Traceback (most recent call last):' "$SCRATCH/fc-$1.txt"; }
named_fail()  { grep -c -F -- 'FAIL  NO vector in the store USES any of these tokens' "$SCRATCH/fc-$1.txt"; }
verd()        { grep -c -F -- "$2" "$SCRATCH/fc-$1.txt"; }

controls_ak() {   # the eleven T455 controls, counted by their own labels, not by position
  local n=0 c
  for c in '(a) a FOURTH failure' '(b) an adjudicated failure' '(c) a section 1 that went GREEN' \
           '(d) a transcript with NO' '(e) the offline prover TRIPS' \
           '(f) the offline prover TRIPS on the subprocess' '(g) the offline prover does NOT trip' \
           '(h) a token used as an object KEY' '(i) a token inside an IDENTIFIER-SHAPED value' \
           '(j) a token inside a PROSE sentence' '(k) a file that does NOT parse as JSON'; do
    if grep -q -F -- "$c" "$SCRATCH/fc-$1.txt"; then n=$((n + 1)); fi
  done
  echo "$n"
}
controls_all() {  # (a)-(k) plus the four T467 added. T472 / C-T467-4: the tree runs FIFTEEN,
  local n                                          # not the eleven T467's handoff table says.
  n="$(controls_ak "$1")"
  local c
  for c in '(l) the UNPARSEABLE branch is reached BY A VALUE' \
           '(l1) EVERY location this file emits is a STRING' \
           '(l2) an identifier-shaped value with ONE TRAILING SPACE' \
           '(m) THE LIMIT, ASSERTED SO IT CANNOT DRIFT'; do
    if grep -q -F -- "$c" "$SCRATCH/fc-$1.txt"; then n=$((n + 1)); fi
  done
  echo "$n"
}

echo "==========================================================================="
echo "T476 -- F-T464-2 AND CONTROL (l): NON-REGRESSION AT $R476"
echo "==========================================================================="
echo

echo "--- CALIBRATION: the clean tree ---"
prepare "$R476" || exit 3
RC_C="$(run_adj clean)"
verdict "clean tree exit"                       "$RC_C"                  0
verdict "clean tree checks run"                 "$(checks_run clean)"    29
verdict "clean tree controls (a)-(k)"           "$(controls_ak clean)"   11
verdict "clean tree controls, ALL of them"      "$(controls_all clean)"  15
echo

echo "--- THE FAIL-CLOSED BRANCH, REACHED BY A VALUE ---"
prepare "$R476" || exit 3
plant || { echo "REFUSED: could not plant the probe" >&2; exit 3; }
RC_P="$(run_adj planted)"
verdict "planted tree exit"                     "$RC_P"                    1
verdict "planted tree traceback"                "$(traceback planted)"     0
verdict "planted tree checks run (29 of 29)"    "$(checks_run planted)"    29
verdict "planted tree controls (a)-(k) reached" "$(controls_ak planted)"   11
verdict "planted tree controls, ALL"            "$(controls_all planted)"  15
verdict "planted tree FAILURES: tally lines"    "$(tally_lines planted)"   1
verdict "planted tree named assertion FAILS"    "$(named_fail planted)"    1
echo

echo "--- IS (l) A CONTROL, OR (k) RENAMED? RESTORE T455's EXACT DEFECT, CLEAN CORPUS ---"
prepare "$R476" || exit 3
python3 - "$D/$ADJ" <<'PYEOF' || { echo "REFUSED: the mutation did not apply" >&2; exit 3; }
import re, sys
p = sys.argv[1]
src = open(p, encoding="utf-8").read()
m = re.search(r'return \(\[\("UNPARSEABLE",.*?\], \[\]\)', src, re.S)
if not m:
    sys.stderr.write("REFUSED: the UNPARSEABLE return is not where this mutation expects it.\n")
    sys.exit(3)
new = src[:m.start()] + 'return ([("UNPARSEABLE", n)], [])' + src[m.end():]
if new == src:
    sys.stderr.write("REFUSED: the edit changed nothing.\n")
    sys.exit(3)
open(p, "w", encoding="utf-8").write(new)
PYEOF
RC_M="$(run_adj lmut)"
verdict "defect restored, CLEAN corpus: exit"      "$RC_M"                      1
verdict "  traceback"                              "$(traceback lmut)"          0
verdict "  checks still all run"                   "$(checks_run lmut)"         29
verdict "  (k) still PASSES -- it did not see it"  "$(verd lmut 'PASS  (k) a file that does NOT parse as JSON')" 1
verdict "  (l)  FAILS"                             "$(verd lmut 'FAIL  (l) the UNPARSEABLE branch is reached BY A VALUE')" 1
verdict "  (l1) FAILS"                             "$(verd lmut 'FAIL  (l1) EVERY location this file emits is a STRING')" 1
echo
echo "  Row 3 is the whole answer to 'is (l) just (k) renamed'. On a corpus where NOTHING"
echo "  real exercises the branch, (l) and (l1) go RED while (k) stays GREEN on the same"
echo "  tree. T472 drove this at T467's tip; it is re-driven here because T476 must not have"
echo "  moved it, and 'must not have moved' is a claim about a tree."
echo

if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: every cardinal T472 confirmed still holds at $R476. EXIT 0"
  exit 0
fi
echo "RESULT: $FAILURES cardinal(s) did not reproduce. EXIT 1"
exit 1
