#!/bin/bash
# T455 / C-T448-4 and C-T448-5 — THE CARDINALS, MEASURED. Two artefacts, never one twice.
#
# WHY THIS FILE EXISTS. T433's handoff restated three numbers it did not measure: T393's
# matrix as "13 cases" (it is 11), "the other eleven rows are argued" (nine were), and "17
# existing invocation sites" — which T448 established is the dispatch brief's figure, i.e. the
# LINE COUNT of a grep block, echoed back as a finding. The driver supplied that 17. A cardinal
# handed to a worker and returned as a measurement is the shape this file refuses to repeat,
# so every number below is produced HERE, and the two that can be are produced from TWO
# DIFFERENT ARTEFACTS — a source file and an output file, or git's engine and python's.
#
# TWO DERIVATIONS THAT SHARE A PRIMITIVE DO NOT CORROBORATE EACH OTHER. That is T448's lesson
# about T433's METHOD A and METHOD B, and it constrains what counts as a cross-check here:
# LEG 1 uses `git grep` (git's own pathspec + regex engine); LEG 2 reads the bytes of every
# tracked file with python and never invokes git grep at all. Agreement between them is
# evidence; agreement between two `git grep` invocations would not be.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298).
#   T455_ROOT=<repo checkout to measure>  bash 40-t455-cardinals.sh
#
# EXIT 0  every cross-check agreed.  EXIT 1  a cross-check disagreed — the disagreement is
# the finding and is printed.  EXIT 3  REFUSED: an artefact needed to measure is absent.
set -u

ROOT="${T455_ROOT:?T455_ROOT must name the repository checkout to measure}"
DRIVE=".softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh"
MATRIX=".softhouse/capture/t393-t382-conditions/out/drive/MATRIX.tsv"
GRADER="verify-capture-integrity.py"

# `[ -d "$ROOT/.git" ]` IS WRONG HERE and this file used it first: in a LINKED WORKTREE — which
# is how every softhouse worker runs — `.git` is a FILE holding a gitdir pointer, not a
# directory, so the test refused a perfectly good checkout. Ask git instead of guessing at its
# layout. (Fail-closed in the wrong place is still a broken instrument: it refuses to measure
# exactly the trees this program actually works in.)
git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1 \
  || { echo "REFUSED: $ROOT is not inside a git work tree." >&2; exit 3; }
for f in "$DRIVE" "$MATRIX"; do
  [ -f "$ROOT/$f" ] || { echo "REFUSED: $f absent under $ROOT; nothing to measure." >&2; exit 3; }
done

FAILURES=0
agree() {   # agree <label> <a> <b>
  if [ "$2" = "$3" ]; then echo "  OK   $1: both legs say $2"
  else echo "  BAD  $1: leg 1 says $2, leg 2 says $3 — a disagreement is the finding"
       FAILURES=$((FAILURES + 1)); fi
}

echo "############ T455 — THE CARDINALS, MEASURED HERE"
echo "  root   = $ROOT"
echo "  commit = $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo UNKNOWN)"
echo

echo "--- 1. C-T448-4: HOW MANY CASES IS T393's MATRIX? ---------------------------------"
echo "    LEG 1 - the SOURCE: run_case invocations in the drive script."
CASES_SRC="$(grep -c '^run_case ' "$ROOT/$DRIVE")"
echo "    LEG 2 — the OUTPUT: distinct case names in the committed MATRIX.tsv, and its row"
echo "            count, which must be cases x 2 refs."
CASES_OUT="$(awk 'NR>1 && NF>0 {print $1}' "$ROOT/$MATRIX" | sort -u | wc -l | tr -d ' ')"
ROWS_OUT="$(awk 'NR>1 && NF>0' "$ROOT/$MATRIX" | wc -l | tr -d ' ')"
echo "      run_case invocations in the script : $CASES_SRC"
echo "      distinct cases in MATRIX.tsv       : $CASES_OUT"
echo "      data rows in MATRIX.tsv            : $ROWS_OUT   (= cases x 2 refs)"
agree "matrix cardinality" "$CASES_SRC" "$CASES_OUT"
if [ "$ROWS_OUT" != "$((CASES_SRC * 2))" ]; then
  echo "  BAD  MATRIX.tsv holds $ROWS_OUT data rows, not $((CASES_SRC * 2)) — the two artefacts disagree"
  FAILURES=$((FAILURES + 1))
else
  echo "  OK   the row count is exactly cases x 2 refs ($ROWS_OUT)"
fi
echo "      T433 restated this as a 13-case matrix. It is $CASES_SRC."
echo
echo "    HOW MANY ROWS WERE ARGUED RATHER THAN MEASURED. T433 drove exactly two cases through"
echo "    the whole runner — the CONTROL (calibration) and f1-13b (the row it changed) — and"
echo "    argued the rest. Measured from the case list, not from the sentence:"
DRIVEN=2
echo "      cases: $CASES_SRC   driven through run-all.sh by T433: $DRIVEN   argued: $((CASES_SRC - DRIVEN))"
echo "      T433 restated this as eleven argued. It is $((CASES_SRC - DRIVEN))."
echo "    T448 MEASURED ALL $((CASES_SRC - DRIVEN)) — including the control row — and every one"
echo "    matched T393's committed value (its out/50-F5-ARGUED-ROWS.txt). So T433's ARGUMENT"
echo "    holds; it now holds ON MEASUREMENT rather than on reasoning, and F-5 closes as"
echo "    MEASURED. T455 does not re-drive them: they are settled, and re-running a settled"
echo "    measurement is not a second derivation, it is the same one twice."
echo

echo "--- 2. C-T448-5: WHAT INVOKES THE GRADER? -----------------------------------------"
echo "    THE DEFINITION, STATED BEFORE THE COUNT, because the '17' was a count with no"
echo "    definition attached. An INVOCATION LINE is a tracked, non-out/ line in a .sh or .py"
echo "    that either RUNS the grader (python3 ... $GRADER) or BINDS its path to a shell"
echo "    variable for later execution (VAR=...$GRADER). A line that merely NAMES the"
echo "    grader inside a quoted assertion string is a MENTION, not an invocation, and is"
echo "    counted separately, and the gap between the two columns is measured, not asserted."
echo
echo "    LEG 1 — git's engine."
L1_LINES="$(git -C "$ROOT" grep -n -E "(python3[^|;]*$GRADER|^[[:space:]]*[A-Za-z_]+=[^=]*$GRADER)" -- '*.sh' '*.py' 2>/dev/null | grep -v '/out/' | grep -c . )"
L1_FILES="$(git -C "$ROOT" grep -l -E "(python3[^|;]*$GRADER|^[[:space:]]*[A-Za-z_]+=[^=]*$GRADER)" -- '*.sh' '*.py' 2>/dev/null | grep -v '/out/' | grep -c . )"
L1_MENTION="$(git -C "$ROOT" grep -c -F -- "$GRADER" -- '*.sh' '*.py' 2>/dev/null | grep -v '/out/' | awk -F: '{s+=$NF} END{print s+0}')"
echo "      invocation lines : $L1_LINES"
echo "      invoking files   : $L1_FILES"
echo "      total mentions   : $L1_MENTION   (the figure a bare grep produces)"
echo
echo "    LEG 2 — python reads the bytes of every tracked file. No git grep anywhere in it."
L2="$(git -C "$ROOT" ls-files -- '*.sh' '*.py' | python3 -c '
import os, re, sys
root = sys.argv[1]
grader = sys.argv[2]
run = re.compile(r"python3[^|;]*" + re.escape(grader))
bind = re.compile(r"^\s*[A-Za-z_]+=[^=]*" + re.escape(grader))
files, lines, mentions = set(), 0, 0
for rel in sys.stdin.read().split("\n"):
    if not rel or "/out/" in rel:
        continue
    try:
        with open(os.path.join(root, rel), "r", encoding="utf-8", errors="replace") as fh:
            body = fh.read()
    except OSError:
        # An unreadable file is NOT an absent one. Refuse rather than under-count.
        print("REFUSED %s" % rel)
        sys.exit(3)
    for ln in body.split("\n"):
        if grader in ln:
            mentions += 1
        if run.search(ln) or bind.search(ln):
            lines += 1
            files.add(rel)
print("%d %d %d" % (lines, len(files), mentions))
' "$ROOT" "$GRADER")" || { echo "REFUSED: leg 2 could not read the corpus." >&2; exit 3; }
case "$L2" in
  REFUSED*) echo "REFUSED: $L2" >&2; exit 3 ;;
esac
L2_LINES="$(echo "$L2" | awk '{print $1}')"
L2_FILES="$(echo "$L2" | awk '{print $2}')"
L2_MENTION="$(echo "$L2" | awk '{print $3}')"
echo "      invocation lines : $L2_LINES"
echo "      invoking files   : $L2_FILES"
echo "      total mentions   : $L2_MENTION"
echo
agree "invocation LINES"   "$L1_LINES"   "$L2_LINES"
agree "invoking FILES"     "$L1_FILES"   "$L2_FILES"
agree "total MENTIONS"     "$L1_MENTION" "$L2_MENTION"
echo
echo "    THE LIST, so the count stands beside the thing it counts and a later reader can"
echo "    decompose it instead of restating it (P-80 is a count that outlives its list):"
git -C "$ROOT" grep -c -E "(python3[^|;]*$GRADER|^[[:space:]]*[A-Za-z_]+=[^=]*$GRADER)" \
  -- '*.sh' '*.py' 2>/dev/null | grep -v '/out/' | sed 's/^/      /' || true
echo
echo "    T455_EXCLUDE, if given, is a path prefix whose files are subtracted, so a figure for"
echo "    PRE-EXISTING invokers can be produced without hand-editing a total."
EXCL="${T455_EXCLUDE:-}"
if [ -n "$EXCL" ]; then
  X_LINES="$(git -C "$ROOT" grep -n -E "(python3[^|;]*$GRADER|^[[:space:]]*[A-Za-z_]+=[^=]*$GRADER)" -- '*.sh' '*.py' 2>/dev/null | grep -v '/out/' | grep -c "^$EXCL" )"
  X_FILES="$(git -C "$ROOT" grep -l -E "(python3[^|;]*$GRADER|^[[:space:]]*[A-Za-z_]+=[^=]*$GRADER)" -- '*.sh' '*.py' 2>/dev/null | grep -v '/out/' | grep -c "^$EXCL" )"
  echo "      excluding $EXCL : $X_FILES file(s), $X_LINES line(s)"
  echo "      PRE-EXISTING     : $((L2_FILES - X_FILES)) file(s), $((L2_LINES - X_LINES)) line(s)"
else
  echo "      T455_EXCLUDE not set, so no pre-existing figure is produced. THAT IS A STATEMENT"
  echo "      ABOUT THIS RUN, not a claim that the two figures coincide."
fi
echo
echo "    THE ONE THAT IS ADJUDICATED, NOT MERELY PRESENT: run-all.sh runs the grader as"
echo "    \`sec 10 0\`, so its exit code is graded against 0 and any move fails RUN-ALL VERDICT."
ADJ="$(grep -c -F -- 'sec 10 0 python3 "$DIR/verify-capture-integrity.py"' "$ROOT/.softhouse/reviews/A2-11/run-all.sh")"
echo "      adjudicated invocation sites: $ADJ"
if [ "$ADJ" != "1" ]; then
  echo "  BAD  expected exactly one adjudicated site, found $ADJ"
  FAILURES=$((FAILURES + 1))
else
  echo "  OK   exactly one, and it is the one P-45 is satisfied by"
fi
echo
echo "    THE LIMIT OF THIS COUNT, STATED. Both legs search .sh and .py only. A future invoker"
echo "    written in any other language would be invisible to both, and 'not found' would be a"
echo "    statement about this search. T448 checked '*.py' as well as '*.sh' and found no .py"
echo "    invoker; that is still true above, and it is a MEASUREMENT that goes stale."

echo
if [ "$FAILURES" -ne 0 ]; then
  echo "T455 CARDINALS: FAIL — $FAILURES cross-check(s) disagreed."
  exit 1
fi
echo "T455 CARDINALS: PASS. The matrix is $CASES_SRC cases and $ROWS_OUT rows, $((CASES_SRC - DRIVEN))"
echo "of them argued by T433 and measured by T448. The grader is invoked from $L2_FILES files"
echo "across $L2_LINES lines, of which exactly $ADJ is ADJUDICATED; a bare grep for the name"
echo "returns $L2_MENTION, which is the kind of number the '17' was."
exit 0
