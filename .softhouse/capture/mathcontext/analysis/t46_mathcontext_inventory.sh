#!/usr/bin/env bash
#
# T46 -- RE-DERIVE the whole hard-coded-`MathContext` inventory from the pinned Fineract
# checkout, to close audit findings M-1 and M-2 against T42's finding N-3.
#
# M-1: N-3 published NINE `new MathContext(10, …)` sites; there are FIVE.  The nine it listed are
#      the union of the five precision-10 and the four precision-15 sites, all labelled 10.
#      `.softhouse/reference-oracle.md` then folded in the derived total "13 new
#      MathContext(15|10, …)" = 4 + 9, double-counting the 15s.
# M-2: N-3's universal claim ("every hard-coded MathContext outside the loan modules is in
#      savings/deposits") is false: two precision-8 sites are omitted entirely, and one of them
#      -- `ShareAccountCharge.java:240` -- is in `portfolio/shareaccounts/`, a DIFFERENT Tier B
#      context with its own precision.
#
# Nothing here is computed or estimated.  Every line printed is a grep hit with `file:line`.
# The checkout is treated as READ-ONLY; no Gradle build is run.
#
# Usage:  bash analysis/t46_mathcontext_inventory.sh [/path/to/fineract]
set -uo pipefail

REPO="${1:-/Users/buv/fineract}"
EX='/src/test/|/misc/'

cd "$REPO" || { echo "cannot cd to $REPO"; exit 1; }

echo "=============================================================================="
echo "T46 -- hard-coded MathContext inventory, re-derived"
echo "repo    : $REPO"
echo "commit  : $(git rev-parse HEAD 2>/dev/null)"
echo "dirty   : $( [ -n "$(git status --porcelain 2>/dev/null)" ] && echo YES || echo no )"
echo "excluded: paths matching $EX"
echo "=============================================================================="
echo

echo "---- 1. EVERY \`new MathContext(\` site in main source, with file:line ----"
grep -rn --include='*.java' 'new MathContext(' . | grep -Ev "$EX" | sed 's|^\./||' | sort
echo
echo -n "total \`new MathContext(\` sites in main source: "
grep -rn --include='*.java' 'new MathContext(' . | grep -Ev "$EX" | wc -l | tr -d ' '
echo

echo "---- 2. broken down by the PRECISION ARGUMENT as written ----"
for P in 8 10 15; do
  echo
  echo "precision $P  (literal first argument):"
  grep -rn --include='*.java' "new MathContext($P," . | grep -Ev "$EX" | sed 's|^\./|    |' | sort
  echo -n "    count: "
  grep -rn --include='*.java' "new MathContext($P," . | grep -Ev "$EX" | wc -l | tr -d ' '
done
echo
echo "non-literal precision argument (PRECISION constant, a parameter, or read off another mc):"
grep -rn --include='*.java' 'new MathContext(' . | grep -Ev "$EX" \
  | grep -Ev 'new MathContext\((8|10|15),' | sed 's|^\./|    |' | sort
echo -n "    count: "
grep -rn --include='*.java' 'new MathContext(' . | grep -Ev "$EX" \
  | grep -Ev 'new MathContext\((8|10|15),' | wc -l | tr -d ' '
echo

echo "---- 3. the loan modules: how many hard-coded MathContexts? ----"
for M in fineract-loan fineract-progressive-loan fineract-progressive-loan-embeddable-schedule-generator; do
  echo -n "  $M: "
  grep -rn --include='*.java' 'new MathContext(' "./$M" 2>/dev/null | grep -Ev "$EX" | wc -l | tr -d ' '
  grep -rn --include='*.java' 'new MathContext(' "./$M" 2>/dev/null | grep -Ev "$EX" | sed 's|^\./|      |'
done
echo

echo "---- 4. MathContext.DECIMAL64 (precision 16, HALF_EVEN) ----"
echo -n "  total occurrences in main source: "
grep -rn --include='*.java' 'MathContext.DECIMAL64' . | grep -Ev "$EX" | wc -l | tr -d ' '
echo "  by module:"
grep -rn --include='*.java' 'MathContext.DECIMAL64' . | grep -Ev "$EX" | sed 's|^\./||' | cut -d/ -f1 \
  | sort | uniq -c | sed 's/^/    /'
echo -n "  occurrences whose path contains neither 'saving' nor 'deposit': "
grep -rn --include='*.java' 'MathContext.DECIMAL64' . | grep -Ev "$EX" | grep -vi 'saving\|deposit' | wc -l | tr -d ' '
echo -n "  occurrences in any loan module: "
grep -rn --include='*.java' 'MathContext.DECIMAL64' ./fineract-loan ./fineract-progressive-loan 2>/dev/null \
  | grep -Ev "$EX" | wc -l | tr -d ' '
echo

echo "---- 5. NEW (T46): the INDIRECT hard-code that N-3 misses ----"
echo "MathUtil.percentageOf(BigDecimal, BigDecimal, int) builds"
echo "  new MathContext(precision, MoneyHelper.getRoundingMode())"
echo "so a caller passing a LITERAL precision hard-codes the precision AND takes the AMBIENT"
echo "rounding mode.  Loan-module callers passing a literal:"
grep -rn --include='*.java' 'percentageOf(.*, 19)' . | grep -Ev "$EX" | sed 's|^\./|    |' | sort
echo -n "    count: "
grep -rn --include='*.java' 'percentageOf(.*, 19)' . | grep -Ev "$EX" | wc -l | tr -d ' '
echo
echo "the helper itself:"
grep -rn --include='*.java' -A 1 'public static BigDecimal percentageOf(final BigDecimal value, final BigDecimal percentage, final int precision)' . \
  | grep -Ev "$EX" | sed 's|^\./|    |'
echo

echo "=============================================================================="
echo "done -- every line above is a grep hit with file:line; nothing is derived."
echo "=============================================================================="
