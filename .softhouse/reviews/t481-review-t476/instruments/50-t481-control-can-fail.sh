#!/bin/bash
# T481 -- CAN THE SUPERSET CONTROL FAIL? BREAK ARM 1 AND WATCH.
#
# A control that cannot fail is worse than none, because it is believed (P-22), and this
# program has found that shape repeatedly. T476 says its SUPERSET CONTROL is the ONLY check
# in the tree that reddens when ARM 1 is unwired -- and that the REGRESSION SUITE does NOT
# move, which is the uncomfortable half. Both halves are re-driven here, on trees I build.
#
# THREE MUTATIONS, not one, because "the control fires when the arm is deleted" and "the
# control fires when the arm is WRONG" are different questions:
#
#   M1  ARM 1 UNWIRED       -- `printed_payloads` no longer seeds itself from the arm.
#   M2  ARM 1 EMPTIED       -- the arm is still called; it returns [] for every input.
#   M3  ARM 1 NARROWED      -- the arm still fires, but only for `echo `, dropping `echo\t`
#                              and `print(`. This is the SEMANTIC failure the guarantee is
#                              supposed to exclude, and it is the one a future author is most
#                              likely to introduce while "tidying".
#
# Each mutation REFUSES (exit 3) if its anchor is absent: a no-op must never read as a pass.
# The check-count column is here because a mutation that SKIPS checks is not the same event
# as one that FAILS a check, and only the second is the control working.
#
# NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL (P-103): every path is assembled from S, and
# the repo/refs are REQUIRED parameters with no defaults.
#
#   T481_SRC=<repo>  T481_SCRATCH=<dir OUTSIDE the repo>  T481_T455=<ref> T481_T467=<ref> \
#   T481_T476=<ref>  bash 50-t481-control-can-fail.sh
#
# EXIT 0  every mutation behaved as recorded.  EXIT 1  one did not.  EXIT 3  REFUSED.
set -u

SRC="${T481_SRC:?T481_SRC must name the source repository}"
SCRATCH="${T481_SCRATCH:?T481_SCRATCH must name a scratch directory OUTSIDE the repository}"
R455="${T481_T455:?T481_T455 must name the ref carrying the emitter rule}"
R467="${T481_T467:?T481_T467 must name the ref carrying the payload rule}"
R476="${T481_T476:?T481_T476 must name the ref under test}"

S=".softhouse"
INT="$S/reviews/A2-11/verify-capture-integrity.py"
D="$SCRATCH/t481-control"
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
  [ -f "$D/$INT" ]
}

mutate() {   # mutate <M1|M2|M3>
  python3 - "$D/$INT" "$1" <<'PYEOF'
import sys
path, which = sys.argv[1], sys.argv[2]
src = open(path, encoding="utf-8").read()
EDITS = {
    # unwire: the union no longer seeds itself from ARM 1
    "M1": ("    out = list(emitter_payloads(text))\n",
           "    out = []\n"),
    # empty: the arm is called and returns nothing
    "M2": ("    out = []\n    for i, line in enumerate(text.split(\"\\n\"), 1):\n",
           "    out = []\n    for i, line in enumerate([], 1):\n"),
    # narrow: the arm still fires, on a strictly smaller set of lines
    "M3": ("        if stripped.startswith(\"echo \") or stripped.startswith(\"echo\\t\") \\\n"
           "                or stripped.startswith(\"print(\"):\n",
           "        if stripped.startswith(\"echo \"):\n"),
}
old, new = EDITS[which]
if old not in src:
    sys.stderr.write("REFUSED: the anchor for %s is absent; the edit would be a no-op.\n" % which)
    sys.exit(3)
out = src.replace(old, new, 1)
if out == src:
    sys.stderr.write("REFUSED: the edit changed nothing.\n")
    sys.exit(3)
import ast
try:
    ast.parse(out)
except SyntaxError as exc:
    sys.stderr.write("REFUSED: the mutated grader no longer parses (%s).\n" % exc)
    sys.exit(3)
open(path, "w", encoding="utf-8").write(out)
PYEOF
}

grade() {    # grade <label>; echoes section 10's exit code
  ( cd "$D" && python3 "$INT" ) > "$SCRATCH/s10-$1.txt" 2>&1
  echo "$?"
}
checks()   { grep -c -E '^  (PASS|FAIL)' "$SCRATCH/s10-$1.txt"; }
superset() { grep -c -E '^  FAIL  SUPERSET CONTROL' "$SCRATCH/s10-$1.txt"; }
suite()    { grep -c -E '^  FAIL  T476 / C-T467-1 . THE REGRESSION SUITE' "$SCRATCH/s10-$1.txt"; }
trace()    { grep -c '^Traceback (most recent call last):' "$SCRATCH/s10-$1.txt"; }
fails()    { grep -c -E '^FAILURES: ' "$SCRATCH/s10-$1.txt"; }

echo "==========================================================================="
echo "T481 -- THE SUPERSET CONTROL, DRIVEN RED THREE WAYS"
echo "==========================================================================="
echo
echo "--- THE CHECK COUNT AT EACH REF (T476 publishes 43 / 48 / 53) ---"
for REF in "$R455" "$R467" "$R476"; do
  prepare "$REF" || { echo "REFUSED: could not prepare $REF" >&2; exit 3; }
  RC="$(grade "ref-$REF")"
  echo "  ref $REF: section 10 exit $RC, checks $(checks "ref-$REF")"
done
echo

echo "--- THE UNMUTATED TIP ---"
prepare "$R476" || exit 3
RC0="$(grade base)"
C0="$(checks base)"
verdict "clean tip: section 10 exit"            "$RC0" 0
verdict "clean tip: SUPERSET CONTROL failures"  "$(superset base)" 0
verdict "clean tip: REGRESSION SUITE failures"  "$(suite base)" 0
echo "  clean tip: checks run = $C0"
echo

for M in M1 M2 M3; do
  echo "--- $M ---"
  prepare "$R476" || exit 3
  if ! mutate "$M"; then
    echo "  REFUSED: mutation $M could not be applied" >&2
    exit 3
  fi
  RC="$(grade "$M")"
  echo "  section 10 exit=$RC  checks=$(checks "$M")  traceback=$(trace "$M")  FAILURES-line=$(fails "$M")"
  echo "  SUPERSET CONTROL failed: $(superset "$M")    REGRESSION SUITE failed: $(suite "$M")"
  verdict "$M: exit is 1, BY A VALUE not a traceback"  "$RC" 1
  verdict "$M: traceback count"                        "$(trace "$M")" 0
  verdict "$M: checks run (nothing skipped)"           "$(checks "$M")" "$C0"
  verdict "$M: the SUPERSET CONTROL goes RED"          "$(superset "$M")" 1
  echo "  (the REGRESSION SUITE's own verdict under $M is reported above, NOT asserted:"
  echo "   whether it moves is the finding, not the expectation.)"
  echo
done

if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: every mutation behaved as recorded. EXIT 0"
  exit 0
fi
echo "RESULT: $FAILURES assertion(s) did not hold. EXIT 1"
exit 1
