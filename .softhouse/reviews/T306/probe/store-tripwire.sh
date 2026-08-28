#!/bin/bash
# T306 — RED-DRIVE for the store tripwire added at the T327 merge.
#
# THE CLAIM UNDER TEST: the date arms of the capability gate keep
# `expect.kind == "refusal"` because NO COMMITTED VECTOR is an acceptance at
# either date boundary -- and a test notices the day that stops being true.
#
# A guard that has never been seen red is not a guard (P-35, patterns.md:
# "every vacuous guard this program has found was a NEGATIVE assertion").
# This script makes the store contain exactly that vector, IN A SCRATCH COPY,
# and requires the test to FAIL and to NAME the injected case id.
#
# IT WRITES NOTHING INSIDE THE REPO. .softhouse/vectors/ is reserved for T328
# this batch; the injection happens in mktemp -d and is destroyed with it.
set -u
W="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
. "$W/.softhouse/bin/go-env.sh" || { echo "no toolchain"; exit 2; }
SCRATCH="$(mktemp -d -t t306-tripwire)" || { echo "mktemp failed"; exit 2; }
trap 'rm -rf "$SCRATCH"' EXIT
echo "scratch: $SCRATCH"

mkdir -p "$SCRATCH/.softhouse"
cp -R "$W/nexus" "$SCRATCH/nexus"
cp -R "$W/.softhouse/vectors" "$SCRATCH/.softhouse/vectors"

TEST='TestOpeningBalanceCapabilityIsScopedToTheObservedShape/the_date_arms'

echo
echo "=============================================================="
echo "CONTROL — the scratch copy UNMODIFIED. The tripwire must be GREEN."
echo "=============================================================="
( cd "$SCRATCH/nexus" && go test -count=1 ./internal/apps/ledger/conformance/ -run "$TEST" -v 2>&1 ) > "$SCRATCH/ctrl.txt"
CTRL=$?
grep -E '^(=== RUN|--- (PASS|FAIL)|ok|FAIL|PASS)' "$SCRATCH/ctrl.txt" | sed 's/^/  /'

echo
echo "=============================================================="
echo "RED-DRIVE — inject ONE acceptance at the PRE-CLOSURE boundary"
echo "  claiming ledger.opening.balance.and.closure. This is the shape"
echo "  T328 would write from T327's B-1 bytes."
echo "=============================================================="
python3 "$W/.softhouse/reviews/T306/probe/inject-acceptance.py" "$SCRATCH" || exit 2

( cd "$SCRATCH/nexus" && go test -count=1 ./internal/apps/ledger/conformance/ -run "$TEST" -v 2>&1 ) > "$SCRATCH/red.txt"
RED=$?
grep -E '^(=== RUN|--- (PASS|FAIL)|ok|FAIL|PASS)|ZZZ-T306-INJECTED|PROMOTING' "$SCRATCH/red.txt" | sed 's/^/  /'

echo
echo "=============================================================="
echo "  CONTROL exit=$CTRL (want 0)   RED-DRIVE exit=$RED (want NON-zero)"
if [ "$CTRL" = "0" ] && [ "$RED" != "0" ]; then
  echo "  TRIPWIRE IS REAL: green on the committed store, RED on the promotion."
else
  echo "  TRIPWIRE IS NOT PROVEN. Do not cite it."
fi
echo "=============================================================="
