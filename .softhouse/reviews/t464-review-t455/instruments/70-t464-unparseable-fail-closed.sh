#!/bin/bash
# T464 — IS THE FAIL-CLOSED DIRECTION OF T455's F-6 REPAIR REAL, OR ONLY REACHABLE BY A CRASH?
#
# T455's new section-4 classifier says: "A file that does NOT parse as JSON, and every non-JSON
# file, keeps the raw substring search and any hit is MATERIAL: unparseable fails CLOSED, never
# skipped." Control (k) drives `classify_occurrences` IN MEMORY and it does return MATERIAL.
# This file drives the SHIPPED ARM instead, by putting one of the tokens into the one non-JSON
# file that is already tracked under the vector store.
#
# The vector store already contains exactly one non-`.json` file, so the unparseable branch is
# LIVE, not hypothetical.
#
# NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL — all assembled from `S` at run time.
#
#   T464_SRC=<repo>  T464_SCRATCH=<dir OUTSIDE the repo>  T464_REF=<ref> \
#     bash 70-t464-unparseable-fail-closed.sh
#
# EXIT 0  the arm reaches its NAMED assertion and reports MATERIAL.
# EXIT 1  it does not — the finding is printed.
# EXIT 3  REFUSED.
set -u
S='.softhouse'
ADJ="$S/reviews/A2-11/adjudicate-section1.py"
VEC="$S/vectors"
TOKEN="paymentChannelToFundSourceMappings"

SRC="${T464_SRC:?}"; SCRATCH="${T464_SCRATCH:?}"; REF="${T464_REF:?}"
D="$SCRATCH/failclosed"

rm -rf "$D" || exit 3
git clone --quiet --shared "$SRC" "$D" || exit 3
git -C "$D" checkout --quiet --force --detach "$REF" || exit 3
git -C "$D" clean -qfdx || exit 3
[ -f "$D/$ADJ" ] || { echo "REFUSED: no adjudicator at $REF" >&2; exit 3; }

echo "############ T464 — THE UNPARSEABLE / FAIL-CLOSED BRANCH OF T455's F-6 REPAIR"
NONJSON="$(git -C "$D" ls-files -- "$VEC" | grep -v '\.json$' | head -1)"
if [ -z "$NONJSON" ]; then
  echo "REFUSED: no tracked non-JSON file under the vector store, so the branch is not live" >&2
  exit 3
fi
echo "  the tracked non-JSON file already in the vector store : $NONJSON"
echo

echo "--- 1. CALIBRATION: the arm is green before anything is planted --------------------"
( cd "$D" && python3 "$ADJ" ) > "$SCRATCH/fc-before.txt" 2>&1
RC0=$?
echo "      adjudicate-section1.py exit = $RC0"
grep -E "^  (PASS|FAIL)  NO vector" "$SCRATCH/fc-before.txt" | cut -c1-88 | sed 's/^/      /'
if [ "$RC0" != "0" ]; then
  echo "REFUSED: P-72 — the arm is already red, so any verdict below would be free." >&2
  exit 3
fi
echo

echo "--- 2. PLANT THE TOKEN IN THE NON-JSON FILE. Expected: MATERIAL, named, FAIL. ------"
printf '\nsee %s for details\n' "$TOKEN" >> "$D/$NONJSON" || exit 3
( cd "$D" && python3 "$ADJ" ) > "$SCRATCH/fc-after.txt" 2>&1
RC1=$?
echo "      adjudicate-section1.py exit = $RC1"
echo
echo "      the last 6 lines it produced:"
tail -6 "$SCRATCH/fc-after.txt" | sed 's/^/        /'
echo

NAMED="$(grep -c "^  FAIL  NO vector" "$SCRATCH/fc-after.txt")"
CRASH="$(grep -c "^Traceback" "$SCRATCH/fc-after.txt")"
TALLY="$(grep -c "^FAILURES:" "$SCRATCH/fc-after.txt")"
CONTROLS_BEFORE="$(grep -c "^  PASS  " "$SCRATCH/fc-before.txt")"
CONTROLS_AFTER="$(grep -c "^  PASS  " "$SCRATCH/fc-after.txt")"
echo "      reached the NAMED 'NO vector ... USES any of these tokens' FAIL : x$NAMED"
echo "      died on a python traceback instead                             : x$CRASH"
echo "      printed its own FAILURES tally                                 : x$TALLY"
echo "      checks that reported at all, before -> after                   : $CONTROLS_BEFORE -> $CONTROLS_AFTER"
echo

if [ "$CRASH" -ge 1 ]; then
  echo "  FINDING: the unparseable branch is reachable ONLY BY A CRASH. classify_occurrences"
  echo "  returns ('UNPARSEABLE', <int count>) where the parsed branch returns"
  echo "  ('KIND', <str jsonpath>), and the caller formats it with where[:70] — an int is not"
  echo "  subscriptable. The arm never reaches its named assertion, never prints its FAILURES"
  echo "  tally, and every downstream check in the file — the T374/T362 provenance arms and"
  echo "  section 5's controls (a)-(k) — is SKIPPED. Aggregate direction is still closed"
  echo "  (rc=1, run-all.sh reads section 9 as MOVED), so it is not a fail-OPEN; but control"
  echo "  (k) drives the FUNCTION and the INTEGRATION is broken, which is the gap P-22 warns"
  echo "  about between a control that passes and a guard that works."
  exit 1
fi
if [ "$NAMED" -ge 1 ] && [ "$RC1" = "1" ]; then
  echo "T464 FAIL-CLOSED DRIVE: the arm names it and fails. EXIT 0"
  exit 0
fi
echo "  FINDING: the arm neither named it nor crashed. exit=$RC1 named=$NAMED"
exit 1
