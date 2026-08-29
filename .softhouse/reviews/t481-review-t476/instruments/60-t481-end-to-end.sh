#!/bin/bash
# T481 -- THE REGRESSION, END TO END, ON TREES I BUILD. RE-DERIVED, NOT INHERITED.
#
# The acceptance test the driver set: no spelling caught at the T455 ref may be missed at
# T476's tip. The expensive half of that is where the harm lands -- the artefact a reader
# opens -- so this drives section 10 AND the whole runner at three refs.
#
# Three cases, and the third is the control that gives the first its meaning:
#   U   `echo <words, UNQUOTED>  # <tag>`   -- no quote character anywhere on the line
#   Q   the SAME line with the words QUOTED -- one pair of characters is the whole difference
#   A2  `print(b"<claim>".decode())  # <tag>` -- a bytes Constant is not a str Constant
#   G   the clean tree at the tip, through the whole runner: a predicate that reddens honest
#       trees is a freeze, not a guard.
#
# THE PYTHON ANCHOR IS WRITTEN WITH ANSI-C QUOTING, NOT COMMAND SUBSTITUTION. T476 recorded
# that `$(printf ...)` strips the trailing newline, welds the smuggled line onto `import sys`
# and makes the mutated .py unparseable -- at which point the case measures the LEXICAL
# FALLBACK and not the spelling it names. The mutation below independently REFUSES unless the
# mutated .py still parses, so that defect cannot recur silently here either.
#
# NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL (P-103); every path is assembled from S and
# every parameter is required.
#
#   T481_SRC=<repo> T481_SCRATCH=<dir OUTSIDE the repo> T481_OUT=<dir> \
#   T481_T455=<ref> T481_T467=<ref> T481_T476=<ref>  bash 60-t481-end-to-end.sh
#
# EXIT 0 every case behaved as recorded.  EXIT 1 one did not.  EXIT 3 REFUSED.
set -u

SRC="${T481_SRC:?T481_SRC must name the source repository}"
SCRATCH="${T481_SCRATCH:?T481_SCRATCH must name a scratch directory OUTSIDE the repository}"
R455="${T481_T455:?T481_T455 must name the ref carrying the emitter rule}"
R467="${T481_T467:?T481_T467 must name the ref carrying the payload rule}"
R476="${T481_T476:?T481_T476 must name the ref under test}"

S=".softhouse"
A2="$S/reviews/A2-11"
INT="$A2/verify-capture-integrity.py"
RUNALL="$A2/run-all.sh"
TRANSCRIPT="$A2/TRANSCRIPT-A2-11.txt"
RELAUNDER="$S/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py"
TAG="QUOTED-FALSE-CLAIM"
SENTENCE="$(printf 'There is no committed baseline older than %s for those 632.' HEAD)"
ANCHOR='  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
PYANCHOR=$'import hashlib\nimport os\nimport sys\n'
D="$SCRATCH/t481-e2e"
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
  git -C "$D" checkout --quiet --force --detach "$1" >/dev/null 2>&1 || return 1
  git -C "$D" reset --quiet --hard "$1" || return 1
  git -C "$D" clean -qfdx || return 1
  [ -f "$D/$INT" ] && [ -f "$D/$RUNALL" ] && [ -f "$D/$RELAUNDER" ]
}

smuggle() {
  python3 - "$D" "$RUNALL" "$RELAUNDER" "$SENTENCE" "$TAG" "$1" "$ANCHOR" "$PYANCHOR" <<'PYEOF'
import ast, os, sys
root, runall, relaunder, sentence, tag, case, anchor, pyanchor = sys.argv[1:9]
SH = {"U": "  echo %s  # %s\n" % (sentence, tag),
      "Q": '  echo "%s"  # %s\n' % (sentence, tag)}
PY = {"A2": 'print(b"%s".decode())  # %s\n' % (sentence, tag)}
if case in SH:
    path, ins, at, after = os.path.join(root, runall), SH[case], anchor, False
else:
    path, ins, at, after = os.path.join(root, relaunder), PY[case], pyanchor, True
src = open(path, encoding="utf-8").read()
if at not in src:
    sys.stderr.write("REFUSED: anchor absent; the edit would be a no-op.\n")
    sys.exit(3)
new = src.replace(at, (at + ins) if after else (ins + at), 1)
if new == src:
    sys.stderr.write("REFUSED: the edit changed nothing.\n")
    sys.exit(3)
if path.endswith(".py"):
    try:
        ast.parse(new)
    except SyntaxError as exc:
        sys.stderr.write("REFUSED: the mutated .py no longer parses (%s); the case would "
                         "measure the lexical fallback, not the spelling it names.\n" % exc)
        sys.exit(3)
open(path, "w", encoding="utf-8").write(new)
PYEOF
}

grade() {
  ( cd "$D" && python3 "$INT" ) > "$SCRATCH/e2e-$1.txt" 2>&1
  echo "$?"
}

echo "==========================================================================="
echo "T481 -- THE REGRESSION SUITE, RE-DRIVEN"
echo "  emitter rule ref : $R455"
echo "  payload rule ref : $R467"
echo "  union ref        : $R476"
echo "==========================================================================="
echo
echo "--- SECTION 10's OWN EXIT, THREE CASES x THREE REFS ---"
for CASE in U Q A2; do
  J=0
  for REF in "$R455" "$R467" "$R476"; do
    J=$((J + 1))
    prepare "$REF" || { echo "REFUSED: could not prepare $REF" >&2; exit 3; }
    smuggle "$CASE" || { echo "REFUSED: could not plant $CASE at $REF" >&2; exit 3; }
    eval "RC_${CASE}_$J=\"\$(grade $CASE-$J)\""
  done
  eval "printf '  case %-3s  section 10 exit:  T455=%s  T467=%s  T476=%s\n' \
        \"$CASE\" \"\$RC_${CASE}_1\" \"\$RC_${CASE}_2\" \"\$RC_${CASE}_3\""
done
echo
verdict "U   caught at the emitter ref"       "$RC_U_1"  1
verdict "U   MISSED at the payload ref"       "$RC_U_2"  0
verdict "U   caught at the union ref"         "$RC_U_3"  1
verdict "A2  caught at the emitter ref"       "$RC_A2_1" 1
verdict "A2  MISSED at the payload ref"       "$RC_A2_2" 0
verdict "A2  caught at the union ref"         "$RC_A2_3" 1
verdict "Q   the CONTROL: caught at the payload ref" "$RC_Q_2" 1
verdict "Q   the CONTROL: caught at the union ref"   "$RC_Q_3" 1
echo

echo "--- THE WHOLE RUNNER, AND THE TRANSCRIPT A READER OPENS ---"
J=0
for REF in "$R467" "$R476"; do
  J=$((J + 1))
  prepare "$REF" || exit 3
  smuggle U || exit 3
  ( cd "$D" && bash "$RUNALL" ) > "$SCRATCH/e2e-runall-$J.txt" 2>&1
  eval "RA_$J=\$?"
  eval "UN_$J=\"\$(grep -F -- \"\$SENTENCE\" \"\$D/\$TRANSCRIPT\" 2>/dev/null | grep -c -v -F -- \"\$TAG\")\""
  eval "VP_$J=\"\$(grep -c -E '^  RUN-ALL VERDICT: PASS' \"\$D/\$TRANSCRIPT\" 2>/dev/null)\""
  eval "VF_$J=\"\$(grep -c -E '^  RUN-ALL VERDICT: FAIL' \"\$D/\$TRANSCRIPT\" 2>/dev/null)\""
  eval "printf '  ref %s: runner exit=%s  untagged sentences in the transcript=%s  verdict PASS=%s FAIL=%s\n' \
        \"$REF\" \"\$RA_$J\" \"\$UN_$J\" \"\$VP_$J\" \"\$VF_$J\""
done
verdict "runner at the payload ref exits 0 with the smuggled line live" "$RA_1" 0
verdict "its transcript carries the sentence UNTAGGED"                  "$UN_1" 1
verdict "and that transcript calls the run a PASS"                      "$VP_1" 1
verdict "runner at the union ref FAILS on the same tree"                "$RA_2" 1
verdict "its transcript carries the same bytes"                         "$UN_2" 1
verdict "but calls the run a FAIL"                                      "$VF_2" 1
verdict "and does NOT call it a PASS"                                   "$VP_2" 0
echo
echo "  The echo is live at both refs -- section 10 grades SOURCE and cannot unprint an"
echo "  emitter. What moves is the RECORD: a transcript that carries a false sentence"
echo "  untagged and calls itself a PASS is citable; the same bytes under a FAIL are not."
echo

echo "--- CASE G: THE CLEAN TREE AT THE UNION REF, WHOLE RUNNER ---"
prepare "$R476" || exit 3
( cd "$D" && bash "$RUNALL" ) > "$SCRATCH/e2e-clean.txt" 2>&1
G_RC=$?
G_DEV="$(grep -o 'deviations: [0-9]*' "$SCRATCH/e2e-clean.txt" | tail -1 | tr -dc '0-9')"
G_SEC="$(grep -o 'sections run: [0-9]*' "$SCRATCH/e2e-clean.txt" | tail -1 | tr -dc '0-9')"
G_UN="$(grep -F -- "$SENTENCE" "$D/$TRANSCRIPT" 2>/dev/null | grep -c -v -F -- "$TAG")"
verdict "clean tree: runner exit"                      "$G_RC"  0
verdict "clean tree: sections run"                     "$G_SEC" 10
verdict "clean tree: deviations"                       "$G_DEV" 0
verdict "clean tree: untagged sentences in transcript" "$G_UN"  0
echo

if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: every case behaved as recorded. EXIT 0"
  exit 0
fi
echo "RESULT: $FAILURES case(s) did not. EXIT 1"
exit 1
