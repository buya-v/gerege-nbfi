#!/usr/bin/env bash
# T322 -- DETERMINISM, MEASURED BY REPETITION.
#
# T320-3b: `for text, left := range count` over a Go MAP, appending to the
# admissibility reason slice without sorting. Go randomises map iteration order
# PER RANGE STATEMENT AND PER PROCESS, so with two surplus amounts the ORDER of
# a graded refusal's reason list varied run to run. In a harness whose entire
# discipline is byte-stable transcripts, that is a flaky vector waiting to
# happen. T306 sorted it; NOTHING measured that it stayed sorted until the arm
# `the SURPLUS report is ORDER-STABLE across runs` and this file.
#
# WHY REPETITION IS THE ONLY HONEST MEASUREMENT. Reading `sort.Strings` in the
# source proves the call is THERE, not that the report it produces is stable --
# a second unsorted map anywhere downstream would reintroduce the defect and the
# source read would still look right. So this runs the arm in MANY PROCESSES.
#
# The arm evaluates one inadmissible vector 65 times per invocation and demands
# byte-identical joined reason text. -count=20 gives 20 independent map-seed
# randomisations, i.e. 1300 evaluations.
#
# USAGE: bash .softhouse/capture/t322-admit-widening/determinism.sh
# EXIT:  0 stable in every run; 1 an ordering moved; 2 dependency missing.

set -u
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || exit 2
[ -f "$REPO_ROOT/.softhouse/bin/go-env.sh" ] || { echo "MISSING .softhouse/bin/go-env.sh"; exit 2; }
# shellcheck source=/dev/null
. "$REPO_ROOT/.softhouse/bin/go-env.sh" >/dev/null 2>&1
command -v go >/dev/null 2>&1 || { echo "no go toolchain"; exit 2; }

ARM='TestOpeningBalanceLegPairingIsRedDrivable/the_SURPLUS_report_is_ORDER-STABLE_across_runs'
COUNT="${1:-20}"

cd "$REPO_ROOT/nexus" || exit 2
echo "\$ go test ./internal/apps/ledger/conformance/ -run '$ARM' -count=$COUNT -v"
out="$(go test ./internal/apps/ledger/conformance/ -run "$ARM" -count="$COUNT" -v 2>&1)"
rc=$?
passes="$(printf '%s\n' "$out" | grep -c -- "--- PASS: $ARM")"
fails="$(printf '%s\n' "$out" | grep -c -- "--- FAIL: $ARM")"
printf '%s\n' "$out" | tail -5
echo
echo "ARM PASSES = $passes   ARM FAILS = $fails   go rc=$rc"
echo "EVALUATIONS = $((passes * 65))  (65 Admit() calls per invocation, each in a fresh process)"
if [ "$rc" -ne 0 ] || [ "$fails" -ne 0 ] || [ "$passes" -ne "$COUNT" ]; then
  echo "T322-DETERMINISM: NOT STABLE, or the arm did not run $COUNT times -- EXIT 1"
  exit 1
fi
echo "T322-DETERMINISM: byte-identical reason text in $passes independent processes -- EXIT 0"
exit 0
