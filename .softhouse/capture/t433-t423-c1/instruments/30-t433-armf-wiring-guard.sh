#!/bin/bash
# T433 / C-T423-1 — THE AUTOMATIC RUNNER FOR ARM F, and the proof of what invokes it.
#
# P-45: a guard wired to nothing enforces nothing. ARM F is section 8 of
# `.softhouse/reviews/A2-11/verify-capture-integrity.py`, so it inherits every invoker that
# section-10 grader already had. This script is the ONE line something automatic can call: it
# RUNS the grader, requires ARM F to have actually graded a non-empty population against a
# baseline older than HEAD, and re-asserts by grep that the wiring is still in place.
#
# WHY THIS FILE EXISTS SEPARATELY FROM THE ARM. T433 does not own `.softhouse/conformance.sh`
# (T445 holds it this wave), and `conformance.sh` invokes NO script under `.softhouse/` today
# — established by grep, see the WIRING section this script prints. So the final bar line is
# DEFERRED to a filed follow-up, and this script is the callable it will name. It is not a
# substitute for that line and does not pretend to be one.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298). The repository root defaults to the
# checkout this script sits in — four levels up — and T433_ROOT overrides it.
#
#   bash 30-t433-armf-wiring-guard.sh
#   T433_ROOT=<repo> bash 30-t433-armf-wiring-guard.sh
#
# EXIT 0  ARM F is present, wired, and graded a non-empty population with no unadjudicated
#         difference.
# EXIT 1  a wiring assertion failed, or the grader reported an unadjudicated post-fork
#         difference. NAMED, never counted only.
# EXIT 2  REFUSED — could not measure (missing file, unusable git). Never read as a pass.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="${T433_ROOT:-$(cd "$HERE/../../../.." && pwd)}"
INT="$ROOT/.softhouse/reviews/A2-11/verify-capture-integrity.py"
RUNALL="$ROOT/.softhouse/reviews/A2-11/run-all.sh"
DRIVE="$ROOT/.softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh"
LAUNDER="$ROOT/.softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py"

for f in "$INT" "$RUNALL" "$DRIVE" "$LAUNDER"; do
  [ -f "$f" ] || { echo "REFUSED: missing $f — this guard cannot measure. Never a pass." >&2; exit 2; }
done

BAD=0
ok()  { echo "  OK   $1"; }
bad() { echo "  BAD  $1"; BAD=$((BAD + 1)); }
# want <label> <file> <fixed-string> <expected count> — EXACT, for claims whose count matters.
want() {
  local got; got="$(grep -c -F -- "$3" "$2")"
  if [ "$got" = "$4" ]; then ok "$1  (x$got)"; else bad "$1 — expected x$4, got x$got: $3"; fi
}
# want_min <label> <file> <fixed-string> <minimum> — for identifiers that legitimately recur.
# A minimum, never an exact count: P-29, a count is a weak tripwire and pinning one here would
# go red on a comment being reworded, which is how a guard gets deleted rather than fixed.
want_min() {
  local got; got="$(grep -c -F -- "$3" "$2")"
  if [ "$got" -ge "$4" ] 2>/dev/null; then ok "$1  (x$got, at least $4)"
  else bad "$1 — expected at least x$4, got x$got: $3"; fi
}

echo "############ T433 ARM-F WIRING GUARD"
echo "root: $ROOT"
echo
echo "--- 1. THE ARM EXISTS, INSIDE THE SHIPPED GRADER (not beside it) -------------------"
want     "verify-capture-integrity.py carries ARM F as section 8" "$INT" "=== 8. ARM F" 1
want_min "ARM F names its baseline: the commit that FIRST ADDED each observation" "$INT" "diff-filter=A" 1
want_min "ARM F has an adjudication table it can find MOVED" "$INT" "ARM_F_ADJUDICATED" 4
# T455: `want` -> `want_min`. THE PIN WAS THE WRONG SHAPE, AND THIS FILE SAYS SO ITSELF nine
# lines up: "A minimum, never an exact count: P-29, a count is a weak tripwire and pinning one
# here would go red on a comment being reworded, which is how a guard gets deleted rather than
# fixed." Both of the exact pins T455 changed went red for exactly that reason, on a CLEAN
# tree: T455 added a second mention of `UNGRADED-BORN-AT-TIP` (the re-adjudication instructions
# for ARM_F_BORN_AT_TIP_ADJUDICATED) and two more of the replacement sentence (the new section
# 10's CORRECTED table and its in-memory self-drive fixture). Neither is a weakening: the claim
# these two lines make is PRESENCE, and it is unchanged. The alternative was to suppress the
# new mentions to satisfy a count, which is tuning the artefact to the tripwire.
# THIS IS AN EDIT OUTSIDE T455's THREE ASSIGNED DIRECTORIES, made deliberately and disclosed by
# name in `.softhouse/handoff/T455-t448-conditions.md`, because the alternative was to ship a
# tracked guard that is RED on a clean tree — the same defect T455 was sent to fix in F-6.
want_min "ARM F reports born-at-tip as UNGRADED, never as equal" "$INT" "UNGRADED-BORN-AT-TIP" 1
want "section 9 asserts ARM F actually GRADED something (the vacuity control)" \
     "$INT" "ARM F actually GRADED a non-empty population" 1

echo
echo "--- 2. THE FALSE IMPOSSIBILITY IS GONE FROM EVERY EXECUTABLE IN SCOPE --------------"
echo "    C-T423-1. These are NEGATIVE assertions, and P-35 says every vacuous guard in this"
echo "    repo is a negative one — so each is paired with a POSITIVE assertion that the"
echo "    replacement text is present. A file that was deleted would fail the positive half."
echo "    Each corrected file QUOTES the false text verbatim, so the check must distinguish a"
echo "    quotation from an assertion: quoted lines carry the literal tag [QUOTED-FALSE-CLAIM]"
echo "    and are excluded, and the tag's PRESENCE is asserted too — dropping the quote to"
echo "    silence the guard would fail the positive half."
IMPOSS="there is no committed baseline older than HEAD|no baseline older than HEAD anywhere|does not exist and cannot be manufactured here|committed baseline older than HEAD for those 632"
for f in "$INT" "$RUNALL" "$DRIVE" "$LAUNDER"; do
  n="$(basename "$f")"
  got="$(grep -Ei "$IMPOSS" "$f" | grep -vc "QUOTED-FALSE-CLAIM")"
  if [ "$got" = "0" ]; then ok "$n ASSERTS the impossibility on x0 untagged line(s)"
  else
    bad "$n still asserts the impossibility on x$got untagged line(s):"
    grep -nEi "$IMPOSS" "$f" | grep -v "QUOTED-FALSE-CLAIM" | sed 's/^/         /'
  fi
  q="$(grep -c "QUOTED-FALSE-CLAIM" "$f")"
  if [ "$q" -ge 3 ]; then ok "$n still QUOTES the false text, tagged (x$q lines)"
  else bad "$n no longer quotes the false text (x$q tagged lines) — a bare negation removed"; fi
done
want_min "verify-capture-integrity.py says what the baseline IS" "$INT" "THE BLOB AT THE COMMIT THAT FIRST ADDED EACH OBSERVATION" 1   # T455: want -> want_min, see above
want "run-all.sh's banner says what the baseline IS" "$RUNALL" "BLOB AT THE COMMIT THAT FIRST ADDED EACH OBSERVATION" 1
want "10-drive-conditions.sh says what the baseline IS" "$DRIVE" "THE BLOB AT THE COMMIT THAT" 1
want "12-relaunder-manifest.py says what the baseline IS" "$LAUNDER" "THE BASELINE EXISTS AND ALWAYS DID" 1

echo
echo "--- 3. THE DRIVE MATRIX NOW EXPECTS THE RESIDUAL TO BE CAUGHT ----------------------"
echo "    T393 expected \`0 0\` (undetected at both refs) and gave a FALSE reason. If ARM F is"
echo "    removed or defeated this row goes back to 0 and 10-drive-conditions.sh fails."
want "the f1-13b row expects 0 -> 1, CAUGHT" \
     "$DRIVE" "run_case f1-13b-postfork-laundered-CLOSED-BY-ARM-F mut_commit_mutate_postfork_laundered 0 1" 1

echo
echo "--- 4. WIRING — WHAT AUTOMATICALLY INVOKES ARM F, ESTABLISHED BY GREP ---------------"
echo "    ARM F is INSIDE verify-capture-integrity.py, so every executable that runs that"
echo "    grader now runs ARM F. Enumerated, not asserted:"
grep -rn "verify-capture-integrity.py" "$ROOT/.softhouse" --include="*.sh" 2>/dev/null \
  | grep -v "/out/" | grep -E "python3 |INT=" \
  | sed "s|^$ROOT/|      |" || true
echo
want "run-all.sh invokes it as ADJUDICATED section 10 (exit code 0 is graded)" \
     "$RUNALL" 'sec 10 0 python3 "$DIR/verify-capture-integrity.py"' 1

echo
echo "--- 5. RUN IT. A wiring proof that never executes the guard is P-22 ----------------"
T="$(mktemp -t t433armf)" || { echo "REFUSED: no scratch file" >&2; exit 2; }
( cd "$ROOT" && python3 "$INT" ) > "$T" 2>&1
RC=$?
GRADED="$(sed -n 's/^      GRADED against a birth blob older than HEAD *: \([0-9]*\)$/\1/p' "$T")"
POP="$(sed -n 's/^      post-fork population (HEAD minus the fork sha) : \([0-9]*\)$/\1/p' "$T")"
TIP="$(sed -n 's/^      UNGRADED, born AT THE TIP (boundary iv-a) *: \([0-9]*\)$/\1/p' "$T")"
DIFF="$(grep -c 'LAUNDERED-OR-MUTATED' "$T")"
MOVED="$(grep -c 'ADJUDICATION MOVED' "$T")"
echo "      grader exit                          : $RC"
echo "      ARM F post-fork population           : ${POP:-UNPRINTED}"
echo "      ARM F GRADED (baseline older than HEAD): ${GRADED:-UNPRINTED}"
echo "      ARM F ungraded, born at the tip      : ${TIP:-UNPRINTED}"
echo "      ARM F unadjudicated differences      : $DIFF"
echo "      ARM F adjudications MOVED            : $MOVED"
# ABSENCE IS NOT ZERO. If the line never printed, the arm did not run, and an unset variable
# must never be read as a clean number.
[ -n "$GRADED" ] || bad "ARM F's GRADED line was NEVER PRINTED — the arm did not run. Absence is not zero."
[ -n "$POP" ]    || bad "ARM F's population line was NEVER PRINTED — the arm did not run."
[ "${GRADED:-0}" -gt 0 ] 2>/dev/null && ok "ARM F graded a non-empty population against a baseline older than HEAD" \
  || bad "ARM F graded NOTHING (${GRADED:-UNPRINTED}) — zero differences over an empty graded set is a vacuous pass"
[ "$DIFF" = "0" ] && ok "no unadjudicated post-fork difference" \
  || bad "$DIFF post-fork observation(s) differ from their birth blob — see the grader output"
[ "$MOVED" = "0" ] && ok "ARM F's adjudication has not moved" || bad "an ARM F adjudication MOVED"
[ "$RC" = "0" ] && ok "the shipped grader exits 0 on this tree" || bad "the shipped grader exited $RC"
rm -f "$T"

echo
echo "--- 6. THE GAP THIS SCRIPT DOES NOT CLOSE, NAMED ----------------------------------"
CONF="$ROOT/.softhouse/conformance.sh"
if [ -f "$CONF" ]; then
  N="$(grep -c "reviews/A2-11/run-all.sh\|30-t433-armf-wiring-guard.sh" "$CONF")"
  echo "      .softhouse/conformance.sh references this chain on $N line(s)."
  if [ "$N" = "0" ]; then
    echo "      DISCLOSED, NOT CLOSED: the bar does not invoke ARM F. T433 does not own"
    echo "      conformance.sh (T445 holds it this wave) and conformance.sh invokes no script"
    echo "      under .softhouse/ today, so there was no existing hook to join. The exact line"
    echo "      a follow-up must add, inside run_guards() beside the other HARD guards:"
    echo
    echo "        hard 'ARM F: post-fork observations vs their birth blob (C-T423-1)' \\"
    echo "             bash .softhouse/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh"
    echo
    echo "      This is a DISCLOSURE, not a failure of this script: it is exactly the P-45"
    echo "      condition, stated by name rather than left for the next reader to discover."
  fi
else
  echo "      .softhouse/conformance.sh NOT FOUND from this root — not a statement about the"
  echo "      world, a statement about \$T433_ROOT=$ROOT."
fi

echo
if [ "$BAD" -ne 0 ]; then
  echo "T433 ARM-F WIRING GUARD: FAIL ($BAD assertion(s)). ARM F is missing, unwired, or red."
  exit 1
fi
echo "T433 ARM-F WIRING GUARD: PASS. ARM F exists inside the shipped section-10 grader, the"
echo "false impossibility is absent from every executable in scope AND the replacement text is"
echo "present, T393's residual row now expects CAUGHT, and the arm actually graded ${GRADED} of"
echo "${POP} post-fork observations against a baseline older than HEAD with 0 unadjudicated"
echo "differences and ${TIP} ungraded at the tip."
exit 0
