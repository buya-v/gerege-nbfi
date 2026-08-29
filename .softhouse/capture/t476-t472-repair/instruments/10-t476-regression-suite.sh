#!/bin/bash
# T476 / C-T467-1 (MAJOR) -- THE REGRESSION, RE-DERIVED AND THEN REPAIRED, END TO END.
#
# T472 measured that T467's payload predicate is NOT a superset of the emitter rule it
# replaced: two spellings that T455 CAUGHT go through T467's tip, with `run-all.sh` at exit 0
# and the false sentence UNTAGGED in the regenerated transcript a reader actually opens.
#
#     (U)  echo <words, UNQUOTED>  # <tag>      no quote character on the line at all
#     (A2) print(b"<claim>".decode())  # <tag>  a bytes Constant is not a str Constant
#
# THIS FILE RE-DERIVES BOTH AT FIRST HAND rather than inheriting them, at THREE refs, and the
# acceptance test is not "the new fixtures go red" -- it is "NOTHING THE OLD RULE CAUGHT IS
# MISSED", so the T455 column is what the T476 column has to dominate.
#
# Case (Q) is the control that makes (U) mean ONE PAIR OF QUOTE CHARACTERS rather than
# something about the sentence: the SAME line with the words quoted. Case (G) is the
# load-bearing green -- a predicate that reddens honest trees is a freeze, not a guard (P-72).
# The wider spelling matrix is graded at the predicate level, fast, by 20-t476-population-cost.py;
# this file is the expensive end-to-end half, where the harm actually lands.
#
# NO HOST PATH AND NO REPO-RELATIVE PATH IS WRITTEN AS A LITERAL HERE (P-103): every one is
# ASSEMBLED from S. The false sentence is ASSEMBLED from its words for the same reason -- a
# literal would make this tracked file an untagged assertion of the claim it drives against.
# Every `echo` in this file quotes its argument, so the instrument does not itself join the
# unquoted-echo population it measures (T472 found three of T467's own instruments in it).
#
#   T476_SRC=<repo to clone>  T476_SCRATCH=<dir OUTSIDE the repo>  T476_OUT=<transcript dir> \
#   T476_T455=<commit-ish with the emitter rule> \
#   T476_T467=<commit-ish with the payload rule> \
#   T476_T476=<commit-ish with the union>  bash 10-t476-regression-suite.sh
#
# EXIT 0  every case produced the recorded outcome.
# EXIT 1  a case did not -- the finding is printed by name.
# EXIT 3  REFUSED: the harness could not measure. NEVER read as a pass.
set -u

SRC="${T476_SRC:?T476_SRC must name the source repository}"
SCRATCH="${T476_SCRATCH:?T476_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T476_OUT:?T476_OUT must name the directory to write transcripts into}"
R455="${T476_T455:?T476_T455 must name the commit-ish carrying the EMITTER rule}"
R467="${T476_T467:?T476_T467 must name the commit-ish carrying the PAYLOAD rule}"
R476="${T476_T476:?T476_T476 must name the commit-ish carrying the UNION}"

S=".softhouse"
A2="$S/reviews/A2-11"
INT="$A2/verify-capture-integrity.py"
RUNALL="$A2/run-all.sh"
TRANSCRIPT="$A2/TRANSCRIPT-A2-11.txt"
RELAUNDER="$S/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py"
TAG="QUOTED-FALSE-CLAIM"
SENTENCE="$(printf 'There is no committed baseline older than %s for those 632.' HEAD)"
ANCHOR='  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
# NOT `$(printf ...)`: command substitution STRIPS trailing newlines, which silently welded
# the smuggled line onto `import sys` and made the .py unparseable -- so the case stopped
# testing the spelling it names. Found by driving it. ANSI-C quoting keeps the bytes, and the
# mutation below REFUSES unless the mutated file still PARSES.
PYANCHOR=$'import hashlib\nimport os\nimport sys\n'

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t476-regress"
FAILURES=0

verdict() {   # verdict <label> <got> <want>
  if [ "$2" = "$3" ]; then echo "  OK   $1 = $2 (expected $3)"
  else echo "  BAD  $1 = $2, EXPECTED $3"; FAILURES=$((FAILURES + 1)); fi
}

prepare() {   # prepare <ref>
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
  fi
  git -C "$D" checkout --quiet --force --detach "$1" || return 1
  git -C "$D" reset --quiet --hard "$1" || return 1
  git -C "$D" clean -qfdx || return 1
  [ -f "$D/$INT" ] && [ -f "$D/$RUNALL" ] && [ -f "$D/$RELAUNDER" ]
}

grade() {     # grade <label> ; echoes section 10's exit code
  ( cd "$D" && python3 "$INT" ) > "$SCRATCH/graded-$1.txt" 2>&1
  echo "$?"
}

# smuggle <case> -- re-assert the sentence as a LIVE emitter with the tag in a TRAILING
# COMMENT. Literal-string surgery in python, so no shell quoting is load-bearing, and the
# edit REFUSES if its anchor is absent: a no-op must never be able to read as a pass.
smuggle() {
  python3 - "$D" "$RUNALL" "$RELAUNDER" "$SENTENCE" "$TAG" "$1" "$ANCHOR" "$PYANCHOR" <<'PYEOF'
import os, sys
root, runall, relaunder, sentence, tag, case, anchor, pyanchor = sys.argv[1:9]
SH = {
    "U": "  echo %s  # %s\n" % (sentence, tag),
    "Q": '  echo "%s"  # %s\n' % (sentence, tag),
}
PY = {
    "A2": 'print(b"%s".decode())  # %s\n' % (sentence, tag),
}
if case in SH:
    path, ins, src_at, after = os.path.join(root, runall), SH[case], anchor, False
else:
    path, ins, src_at, after = os.path.join(root, relaunder), PY[case], pyanchor, True
src = open(path, encoding="utf-8").read()
if src_at not in src:
    sys.stderr.write("REFUSED: anchor absent; the edit would be a no-op.\n")
    sys.exit(3)
new = src.replace(src_at, (src_at + ins) if after else (ins + src_at), 1)
if new == src:
    sys.stderr.write("REFUSED: the edit changed nothing.\n")
    sys.exit(3)
if path.endswith(".py"):
    # A mutation that breaks the parse is not the spelling this case names: the grader would
    # fall back to its lexical rule and the case would measure the fallback instead. REFUSE.
    import ast
    try:
        ast.parse(new)
    except SyntaxError as exc:
        sys.stderr.write("REFUSED: the mutated .py no longer parses (%s); the case would "
                         "measure the lexical fallback, not the spelling it names.\n" % exc)
        sys.exit(3)
open(path, "w", encoding="utf-8").write(new)
PYEOF
}

echo "==========================================================================="
echo "T476 -- C-T467-1, THE REGRESSION SUITE (end-to-end half)"
echo "  T455 emitter rule : $R455"
echo "  T467 payload rule : $R467"
echo "  T476 union        : $R476"
echo "==========================================================================="
echo
echo "--- SECTION 10's OWN EXIT, THREE CASES x THREE REFS ---"
I=0
for CASE in U Q A2; do
  I=$((I + 1))
  J=0
  for REF in "$R455" "$R467" "$R476"; do
    J=$((J + 1))
    prepare "$REF" || { echo "REFUSED: could not prepare $REF" >&2; exit 3; }
    smuggle "$CASE" || { echo "REFUSED: could not plant case $CASE at $REF" >&2; exit 3; }
    eval "RC_${CASE}_$J=\"\$(grade $CASE-$J)\""
  done
  eval "printf '  case %-3s  section 10 exit:  T455=%s  T467=%s  T476=%s\n' \
        \"$CASE\" \"\$RC_${CASE}_1\" \"\$RC_${CASE}_2\" \"\$RC_${CASE}_3\""
done
echo
echo "--- THE TWO REGRESSIONS T472 NAMED, ASSERTED CASE BY CASE ---"
verdict "U   echo <words UNQUOTED>: CAUGHT at T455"    "$RC_U_1"  1
verdict "U   MISSED at T467 -- lost coverage"          "$RC_U_2"  0
verdict "U   CAUGHT at T476 -- repaired"               "$RC_U_3"  1
verdict "A2  print(b'..'.decode()): CAUGHT at T455"    "$RC_A2_1" 1
verdict "A2  MISSED at T467 -- lost coverage"          "$RC_A2_2" 0
verdict "A2  CAUGHT at T476 -- repaired"               "$RC_A2_3" 1
echo
echo "--- THE CONTROL: (U) DIFFERS FROM (Q) BY ONE PAIR OF QUOTE CHARACTERS ---"
verdict "Q   the SAME line, words QUOTED, caught at T467" "$RC_Q_2" 1
verdict "Q   still caught at T476"                        "$RC_Q_3" 1
echo
echo "  If (Q) and (U) had behaved alike at T467 the finding would be about the sentence."
echo "  They do not: the only difference between the caught line and the missed line is the"
echo "  quoting, because the payload extractor returned [] for a line with no quote character"
echo "  and the trailing-comment tag silenced the binding predicate."
echo

echo "--- THE HARM WHERE IT LANDS: THE WHOLE RUNNER, AND THE READER'S TRANSCRIPT ---"
J=0
for REF in "$R467" "$R476"; do
  J=$((J + 1))
  prepare "$REF" || { echo "REFUSED: could not prepare $REF" >&2; exit 3; }
  smuggle U || { echo "REFUSED: could not plant U at $REF" >&2; exit 3; }
  ( cd "$D" && bash "$RUNALL" ) > "$SCRATCH/runall-U-$J.txt" 2>&1
  eval "RA_$J=\$?"
  eval "UN_$J=\"\$(grep -F -- \"\$SENTENCE\" \"\$D/\$TRANSCRIPT\" 2>/dev/null | grep -c -v -F -- \"\$TAG\")\""
  eval "printf '  runner at ref %s: exit=%s   sentences UNTAGGED in the transcript=%s\n' \
        \"$REF\" \"\$RA_$J\" \"\$UN_$J\""
done
verdict "run-all.sh at T467 exits 0 WITH the smuggled sentence live" "$RA_1" 0
verdict "the reader's transcript at T467 carries it UNTAGGED"        "$UN_1" 1
verdict "run-all.sh at T476 FAILS on the same tree"                  "$RA_2" 1
verdict "the reader's transcript at T476 carries it UNTAGGED x0"     "$UN_2" 0
echo

echo "--- CASE G: THE CLEAN TREE AT T476, THROUGH THE WHOLE RUNNER ---"
prepare "$R476" || { echo "REFUSED: could not prepare $R476" >&2; exit 3; }
( cd "$D" && bash "$RUNALL" ) > "$SCRATCH/runall-clean.txt" 2>&1
G_RC=$?
G_DEV="$(grep -o 'deviations: [0-9]*' "$SCRATCH/runall-clean.txt" | tail -1 | tr -dc '0-9')"
G_SEC="$(grep -o 'sections run: [0-9]*' "$SCRATCH/runall-clean.txt" | tail -1 | tr -dc '0-9')"
G_UN="$(grep -F -- "$SENTENCE" "$D/$TRANSCRIPT" 2>/dev/null | grep -c -v -F -- "$TAG")"
G_S10="$(grade clean)"
G_CHK="$(grep -c -E '^  (PASS|FAIL)' "$SCRATCH/graded-clean.txt")"
verdict "clean tree: run-all.sh exit"                       "$G_RC"  0
verdict "clean tree: sections run"                          "$G_SEC" 10
verdict "clean tree: deviations"                            "$G_DEV" 0
verdict "clean tree: untagged sentences in the transcript"  "$G_UN"  0
verdict "clean tree: section 10's own exit"                 "$G_S10" 0
echo "  clean tree: section 10 runs $G_CHK checks"
echo

echo "--- COVERAGE (F-T464-5): the bytes graded above, by blob id at $R476 ---"
for F in "$INT" "$RUNALL" "$RELAUNDER"; do
  printf '  %-72s %s\n' "$F" "$(git -C "$D" rev-parse "$R476:$F")"
done
echo

if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: every case behaved as recorded. EXIT 0"
  exit 0
fi
echo "RESULT: $FAILURES case(s) did not behave as recorded. EXIT 1"
exit 1
