#!/usr/bin/env bash
#
# T48 -- PROVE THE RECIPE FAILABLE.
#
# `patterns.md`: "A precondition script is only worth what its negative run proves. An
# assertion suite that has never failed has not been tested."  This script runs
# run-actualactual.sh in deliberately wrong configurations and requires each one to exit
# NON-ZERO with a BREACH line naming the breach.  If any leg PASSES, this script exits 1 --
# because then the recipe is not failable on that axis and its PASS means nothing.
#
# It mutates NOTHING outside .softhouse/capture/actualactual, starts no server, and touches
# neither fineract-fineract-1 nor fineract-db-1.

set -u

CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN="$CAPDIR/src/run-actualactual.sh"
FAILED=0
LEG=0

leg() {
  LEG=$((LEG + 1))
  local name="$1"; shift
  local want="$1"; shift
  echo ""
  echo "### N$LEG -- $name"
  local out rc
  out="$("$@" 2>&1)"
  rc=$?
  if [ "$rc" = "0" ]; then
    echo "  LEG FAILED: the recipe exited 0 in a configuration that should have breached"
    FAILED=1
    return
  fi
  if ! printf '%s' "$out" | grep -q "BREACH"; then
    echo "  LEG FAILED: exited $rc but printed no BREACH line"
    FAILED=1
    return
  fi
  if ! printf '%s' "$out" | grep -qi -- "$want"; then
    echo "  LEG FAILED: BREACH did not mention '$want'"
    printf '%s\n' "$out" | grep "BREACH" | head -4 | sed 's/^/    /'
    FAILED=1
    return
  fi
  echo "  ok  exit $rc; breach named:"
  printf '%s\n' "$out" | grep "BREACH" | head -4 | sed 's/^/      /'
}

echo "== T48 negative tests -- proving run-actualactual.sh failable =="

leg "wrong pinned commit" "pinned checkout is at" \
    env T48_EXPECT_COMMIT=0000000000000000000000000000000000000000 T48_SET=seam bash "$RUN"

leg "wrong image id" "image id is" \
    env T48_EXPECT_IMAGE=sha256:0000000000000000000000000000000000000000000000000000000000000000 \
        T48_SET=seam bash "$RUN"

leg "wrong seam-class digest" "seam class sha256 is" \
    env T48_EXPECT_SEAM_SHA=0000000000000000000000000000000000000000000000000000000000000000 \
        T48_SET=seam bash "$RUN"

# The seam class actually drifting -- a temporary byte change, reverted immediately.
echo ""
LEG=$((LEG + 1))
echo "### N$LEG -- seam class byte-drift (temporary, reverted)"
SEAMF="$CAPDIR/src/EmbeddableProgressiveLoanScheduleGenerator.java"
cp "$SEAMF" "$CAPDIR/out/.seam-backup"
printf '\n// T48 negative test -- this line is removed immediately.\n' >> "$SEAMF"
OUT="$(T48_SET=seam T48_OUT_PREFIX=t48neg bash "$RUN" 2>&1)"; RC=$?
cp "$CAPDIR/out/.seam-backup" "$SEAMF"
rm -f "$CAPDIR/out/.seam-backup"
if [ "$RC" = "0" ]; then
  echo "  LEG FAILED: drifted seam class still produced a PASS"; FAILED=1
else
  echo "  ok  exit $RC; breach named:"
  printf '%s\n' "$OUT" | grep -E "BREACH|DRIFTED" | head -3 | sed 's/^/      /'
fi
if ! diff -q "$SEAMF" /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java > /dev/null; then
  echo "  LEG FAILED: the seam class was NOT restored"; FAILED=1
else
  echo "  ok  seam class restored byte-identical to the pin"
fi

leg "threaded rounding mode forced to HALF_EVEN" "THREADED rounding mode" \
    env T48_SET=seam T48_OUT_PREFIX=t48neg T48_JAVA_PROPS=-Dt48.mathContextRoundingMode=HALF_EVEN bash "$RUN"

leg "threaded precision forced to 12" "THREADED precision" \
    env T48_SET=seam T48_OUT_PREFIX=t48neg T48_JAVA_PROPS=-Dt48.mathContextPrecision=12 bash "$RUN"

leg "tenant rounding ordinal forced to 1 (DOWN)" "AMBIENT MoneyHelper MathContext" \
    env T48_SET=seam T48_OUT_PREFIX=t48neg T48_JAVA_PROPS=-Dt48.tenantRoundingModeOrdinal=1 bash "$RUN"

leg "expected ambient context set to a value the oracle does not hold" "AMBIENT MoneyHelper MathContext" \
    env T48_SET=seam T48_OUT_PREFIX=t48neg "T48_EXPECT_MC=precision=19 roundingMode=HALF_DOWN" bash "$RUN"

echo ""
if [ "$FAILED" = "0" ]; then
  echo "== ALL NEGATIVE LEGS BREACHED AS REQUIRED -- the recipe is proved failable on $LEG axes"
  exit 0
fi
echo "== NEGATIVE TESTS FAILED -- the recipe is NOT failable on every axis it claims"
exit 1
