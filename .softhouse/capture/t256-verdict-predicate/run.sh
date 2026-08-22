#!/usr/bin/env bash
# T259 -- run everything this task produced, in the order a reader should meet it.
#
# This is the entry point a conformance probe line would call. NOTHING CALLS IT YET:
# `.softhouse/conformance.sh` is held by T253 this fire and T259 may not touch it. Backlog B-2 in
# the handoff names the wiring. Until then R-VPA is in the condition it was written to condemn --
# a measurement nobody reads -- and saying so here is the point of P-78.
#
# EXIT: 0 all green; 1 at least one leg refused; 2 a leg errored. Never conflated (P-80).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"

echo "================================================================================"
echo "T259 -- verdict/predicate agreement"
echo "HEAD         : $(git -C "$ROOT" rev-parse HEAD)"
echo "vector store : $(git -C "$ROOT" rev-parse HEAD:.softhouse/vectors)"
echo "================================================================================"

WORST=0
note() {
  local name="$1" rc="$2"
  echo ">>> $name exit $rc"
  if [ "$rc" -gt "$WORST" ]; then WORST="$rc"; fi
}

echo ""
echo "### 1. Independent re-derivation of the five-and-three count"
RC=0
python3 "$HERE/rederive_counts_t259.py" || RC=$?
note rederive_counts_t259.py "$RC"

echo ""
echo "### 2. Fail-open lint, pointed at T259's OWN instruments first (P-80)"
RC=0
python3 "$HERE/lint_failopen_t259.py" "$HERE" || RC=$?
note lint_failopen_t259.py "$RC"

echo ""
echo "### 3. R-VPA over the committed evidence -- GREEN, and still loud"
RC=0
python3 "$HERE/check_verdict_predicate_agreement.py" || RC=$?
note check_verdict_predicate_agreement.py "$RC"

echo ""
echo "### 4. The census -- how far the shape reaches (REPORTS; does not gate)"
RC=0
python3 "$HERE/census_verdict_shape.py" || RC=$?
note census_verdict_shape.py "$RC"

echo ""
echo "### 5. The red/green battery"
RC=0
bash "$HERE/red/drive-red.sh" || RC=$?
note drive-red.sh "$RC"

echo ""
echo "================================================================================"
echo "T259 RUN: worst exit $WORST"
echo "vector store at end: $(git -C "$ROOT" rev-parse HEAD:.softhouse/vectors)"
echo "================================================================================"
exit "$WORST"
