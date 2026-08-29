#!/bin/bash
# T476 -- IS THE SUPERSET CONTROL A CONTROL, OR A SENTENCE THAT CANNOT FAIL? (P-98)
#
# The repair's load-bearing claim is that ARM 1 -- T455's emitter rule, kept inside the union
# -- makes "the new predicate sees everything the old one saw" TRUE BY CONSTRUCTION rather
# than true on whichever shapes somebody generated. The ablation in 20-t476-population-cost.py
# says something uncomfortable about that arm and it is reported rather than buried: on the
# 249-case generated matrix, DISABLING ARM 1 LOSES NOTHING, because the widened arms happen to
# cover the same cases. An arm that earns no catches is exactly the shape of a control that
# cannot fail, and this file is the answer to that objection: it makes the defect come back.
#
# THE MUTATION unwires ARM 1 from `printed_payloads` and changes nothing else. The edit
# REFUSES if its anchor is absent, so a no-op cannot read as a pass.
#
# WHAT MUST HAPPEN, for the control to be a control (and note what must NOT: the regression
# suite still PASSES without ARM 1, because the widened arms cover those eight shapes -- so the
# SUPERSET CONTROL is the ONLY thing in the tree that sees the guarantee go):
#   * the SUPERSET CONTROL fails;
#   * section 10 exits 1 on a CLEAN tree -- no smuggled sentence anywhere;
#   * and the unmutated tip is green on the same corpus, so the red is the mutation.
#
# NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL (P-103); every one is assembled from S. Every
# `echo` quotes its argument.
#
#   T476_SRC=<repo>  T476_SCRATCH=<dir OUTSIDE the repo>  T476_T476=<commit-ish> \
#   bash 30-t476-superset-falsifiable.sh
#
# EXIT 0 every case behaved as recorded.  EXIT 1 one did not.  EXIT 3 REFUSED.
set -u

SRC="${T476_SRC:?T476_SRC must name the source repository}"
SCRATCH="${T476_SCRATCH:?T476_SCRATCH must name a scratch directory OUTSIDE the repository}"
R476="${T476_T476:?T476_T476 must name the commit-ish carrying the union}"

S=".softhouse"
INT="$S/reviews/A2-11/verify-capture-integrity.py"
D="$SCRATCH/t476-falsify"
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

run() {   # run <label> ; echoes the exit code
  ( cd "$D" && python3 "$INT" ) > "$SCRATCH/falsify-$1.txt" 2>&1
  echo "$?"
}

hits() { grep -c -F -- "$2" "$SCRATCH/falsify-$1.txt"; }

echo "==========================================================================="
echo "T476 -- THE SUPERSET CONTROL, MADE TO FAIL"
echo "  tree under test: $R476"
echo "==========================================================================="
echo

prepare "$R476" || { echo "REFUSED: could not prepare $R476" >&2; exit 3; }
RC_CLEAN="$(run clean)"
CHK_CLEAN="$(grep -c -E '^  (PASS|FAIL)' "$SCRATCH/falsify-clean.txt")"
SUP_CLEAN="$(hits clean 'PASS  SUPERSET CONTROL')"
REG_CLEAN="$(hits clean 'PASS  T476 / C-T467-1 — THE REGRESSION SUITE')"
echo "  UNMUTATED TIP, clean corpus:"
verdict "    section 10 exit"                    "$RC_CLEAN"  0
verdict "    SUPERSET CONTROL passes"            "$SUP_CLEAN" 1
verdict "    the REGRESSION SUITE check passes"  "$REG_CLEAN" 1
echo "    checks run: $CHK_CLEAN"
echo

prepare "$R476" || { echo "REFUSED: could not re-prepare $R476" >&2; exit 3; }
python3 - "$D/$INT" <<'PYEOF' || { echo "REFUSED: the mutation did not apply" >&2; exit 3; }
import sys
p = sys.argv[1]
src = open(p, encoding="utf-8").read()
anchor = "    out = list(emitter_payloads(text))\n"
if anchor not in src:
    sys.stderr.write("REFUSED: ARM 1 is not wired the way this mutation expects.\n")
    sys.exit(3)
new = src.replace(anchor, "    out = []  # ARM 1 UNWIRED BY 30-t476-superset-falsifiable.sh\n", 1)
if new == src:
    sys.stderr.write("REFUSED: the edit changed nothing.\n")
    sys.exit(3)
open(p, "w", encoding="utf-8").write(new)
PYEOF

RC_MUT="$(run unwired)"
CHK_MUT="$(grep -c -E '^  (PASS|FAIL)' "$SCRATCH/falsify-unwired.txt")"
SUP_MUT="$(hits unwired 'FAIL  SUPERSET CONTROL')"
REG_MUT="$(hits unwired 'FAIL  T476 / C-T467-1 — THE REGRESSION SUITE')"
TB_MUT="$(hits unwired 'Traceback (most recent call last)')"
echo "  ARM 1 UNWIRED, same clean corpus:"
verdict "    section 10 exit -- BY A VALUE, on a clean tree"  "$RC_MUT"  1
verdict "    SUPERSET CONTROL fails"                          "$SUP_MUT" 1
verdict "    traceback"                                       "$TB_MUT"  0
verdict "    every check still runs (nothing is skipped)"     "$CHK_MUT" "$CHK_CLEAN"
echo
echo "  AND THE RESULT THAT MATTERS MOST IS THE ONE THAT DID NOT MOVE:"
verdict "    the REGRESSION SUITE check still PASSES without ARM 1" "$REG_MUT" 0
echo
echo "  The payloads the replaced rule sees and the unwired union does not:"
grep -A1 -F 'FAIL  SUPERSET CONTROL' "$SCRATCH/falsify-unwired.txt" | tail -1
echo

echo "  READ THAT PAIR CAREFULLY, BECAUSE IT IS THE WHOLE ARGUMENT FOR THE UNION."
echo "  Unwire ARM 1 and all eight regression spellings are STILL caught -- the widened arms"
echo "  happen to cover them, exactly as the ablation in 20-t476-population-cost.py reports."
echo "  A worker who graded this repair the way T467 graded its own would therefore see"
echo "  nothing wrong. The ONLY check that reddens is the SUPERSET CONTROL, and what it"
echo "  reddens on is the python side, where the AST arm does not read raw source lines and"
echo "  nothing else does either. ARM 1 is not there for catches. It is there so that 'the"
echo "  union sees everything the replaced rule saw' is a property of the CODE and not of"
echo "  whichever shapes a matrix enumerates -- which is the exact failure being repaired."
echo "  The control is a WIRING TRIPWIRE on that guarantee, and it is deliberately stricter"
echo "  than the semantic relation: it compares (lineno, payload) pairs, so a future author"
echo "  who changes how payloads are represented is made to look. The SEMANTIC property --"
echo "  everything T455 CATCHES, T476 catches -- is measured over a generated 249-case cross"
echo "  product by 20-t476-population-cost.py, which is the independent half of this claim."
echo

if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: the control is falsifiable and the tip is green. EXIT 0"
  exit 0
fi
echo "RESULT: $FAILURES case(s) did not behave as recorded. EXIT 1"
exit 1
