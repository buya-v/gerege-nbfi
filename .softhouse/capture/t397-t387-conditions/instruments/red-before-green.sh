#!/usr/bin/env bash
# T397 — the RED-before-GREEN drive for T387's F-T387-2.
#
# WHAT "RED" MEANS HERE, stated because the obvious reading is wrong. The true
# pre-T397 tree does not merely fail the new tests, it does not COMPILE them:
# `tokenBoundedIndex` does not exist on `main`, so `go test` there reports a build
# error and no test result at all — which is not evidence that the tests detect
# the defect, only that the symbol is new.
#
# So RED is driven by NEUTRALISING THE NEW CALL SITE instead. `if tokenBounded...`
# becomes `if false && tokenBounded...`, which leaves the helper compiled and
# restores `verbatimInCapture` to EXACTLY its pre-T397 semantics: a bare
# bytes.Contains and nothing else. Every arm that depends on the boundary rule
# then fails, and the arms that do not (the helper's own table, the retained
# downstream self-correction, the anti-vacuity control) stay green — which is the
# discrimination a bare build failure could not have shown.
#
# Usage: bash red-before-green.sh <repo-root>
set -euo pipefail

ROOT="${1:?repo root}"
ADMIT="$ROOT/nexus/internal/apps/ledger/conformance/admit.go"
OUT="$ROOT/.softhouse/capture/t397-t387-conditions/out"
TESTS='TestANumericPrefixOfTheCapturedAmountIsNotVerbatim|TestTheBoundaryRuleFormsNoNumber|TestThePrefixIsStillCaughtDownstreamIfAdmissionIsBypassed|TestObservedCharactersMustBeInTheCitedCapture'

mkdir -p "$OUT"
cp "$ADMIT" "$OUT/../admit.go.t397"
trap 'cp "$OUT/../admit.go.t397" "$ADMIT"; rm -f "$OUT/../admit.go.t397"' EXIT

# --- RED --------------------------------------------------------------------
perl -pi -e 's/\Qif tokenBoundedIndex(raw, \E/if false \&\& tokenBoundedIndex(raw, /' "$ADMIT"
grep -q 'if false && tokenBoundedIndex' "$ADMIT" || { echo "NEUTRALISATION DID NOT APPLY"; exit 9; }
( cd "$ROOT/nexus" && go test -count=1 -run "$TESTS" -v ./internal/apps/ledger/conformance/ ) \
  > "$OUT/RED-bare-bytes-Contains.log" 2>&1 && red=0 || red=$?
echo "RED exit = $red" | tee -a "$OUT/RED-bare-bytes-Contains.log"

# --- GREEN ------------------------------------------------------------------
cp "$OUT/../admit.go.t397" "$ADMIT"
grep -q 'if false && tokenBoundedIndex' "$ADMIT" && { echo "RESTORE FAILED"; exit 9; }
( cd "$ROOT/nexus" && go test -count=1 -run "$TESTS" -v ./internal/apps/ledger/conformance/ ) \
  > "$OUT/GREEN-token-bounded.log" 2>&1 && green=0 || green=$?
echo "GREEN exit = $green" | tee -a "$OUT/GREEN-token-bounded.log"

echo "RED=$red GREEN=$green"
[ "$red" -ne 0 ] || { echo "THE DRIVE IS VACUOUS: the tests pass with the boundary rule OFF"; exit 8; }
[ "$green" -eq 0 ] || { echo "THE FIX DOES NOT MAKE THEM PASS"; exit 8; }
echo "RED-before-GREEN CONFIRMED"
