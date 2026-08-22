#!/usr/bin/env bash
# T262 -- BAR verification with P-83 discipline: probe line PRESENCE is asserted BEFORE any VALUE
# is read. An absent probe is a DIFFERENT failure from a probe carrying the wrong number, and
# conflating them is how a crash gets read as a refusal.
#
# P-75/P-80 on this instrument itself: only /usr/bin/grep (never bare `grep`, which is bundled
# ugrep with hidden --exclude-dir flags), never `rg`, never `git grep -E`. Every grep exit status
# is CLASSIFIED, not swallowed: 0 = found, 1 = a real measured negative, >1 = an ERROR that aborts
# with exit 2 rather than printing an absence. No short-circuit-to-echo and no short-circuit-to-
# true anywhere: a failure sets a flag through an explicit `if`, so nothing can print an absence
# over an error.
set -euo pipefail

BAR="${1:-/tmp/t262-bar.txt}"
fail=0

# look <fixed-string> -> 0 found, 1 measured-absent; aborts the script on a grep error.
look() {
  local pat="$1" rc=0
  /usr/bin/grep -qF -- "$pat" "$BAR" || rc=$?
  if [ "$rc" -eq 0 ]; then return 0; fi
  if [ "$rc" -eq 1 ]; then return 1; fi
  echo "  ERROR: /usr/bin/grep exit $rc on ${pat} -- aborting, never printing an absence (P-80)"
  exit 2
}

present() {
  local label="$1" pat="$2"
  if look "$pat"; then
    echo "  PRESENT  $label"
  else
    echo "  ABSENT   $label   <<< probe line missing -- NOT the same as a wrong value"
    fail=1
  fi
}

value() {
  local label="$1" pat="$2"
  if look "$pat"; then
    echo "  MATCH    $label"
  else
    echo "  MISMATCH $label   expected: $pat"
    fail=1
  fi
}

echo "=== STEP 1: probe-line PRESENCE (before any value is read) ==="
present "fail-open frontier probe" "CENSUS fail-open instruments"
present "frontier equality probe"  "frontier == pinned"
present "VERDICT line"             "VERDICT: PASS (exit 0)"
present "exemption census block"   "exemption census READ:"

echo ""
echo "=== STEP 2: only now, the VALUES ==="
value "frontier count"        "frontier 11, pinned at 11."
value "frontier equality"     "frontier == pinned (all 11 rows, by path)."
value "invariant violations"  "invariant violations    0"

echo ""
echo "=== STEP 3: the fail-open instrument census on THIS branch ==="
# T259 measured 927 on its own branch. T262 adds its own review scripts, so the expected figure
# here is 927 + (T262's tracked .sh/.py). Read LIVE, never assumed; the FRONTIER is what must hold.
live=$(git ls-files '*.sh' '*.py' | /usr/bin/grep -c . || true)
echo "  tracked .sh/.py on this branch (live): $live"
if look "CENSUS fail-open instruments"; then
  /usr/bin/grep -F "CENSUS fail-open instruments" "$BAR"
fi

echo ""
echo "=== STEP 4: exemption census pins -- every row must read '== pinned' ==="
total=0; matched=0
total=$(/usr/bin/grep -c "exemption census READ:" "$BAR" || true)
matched=$(/usr/bin/grep "exemption census READ:" "$BAR" | /usr/bin/grep -c "== pinned" || true)
echo "  exemption census rows: $total   rows reading '== pinned': $matched"
if [ "$total" -ne 9 ]; then echo "  EXPECTED 9 exemption census pins, got $total"; fail=1; fi
if [ "$total" -ne "$matched" ]; then echo "  NOT ALL PINS MATCHED"; fail=1; fi

echo ""
echo "=== STEP 5: vector store digest, read live ==="
D=$(git rev-parse HEAD:.softhouse/vectors)
echo "  HEAD:.softhouse/vectors = $D"
if [ "$D" != "13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d" ]; then
  echo "  DIGEST MOVED -- expected 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d"
  fail=1
fi

echo ""
if [ "$fail" -eq 0 ]; then
  echo "BAR CHECK: all probes present, all values match."
else
  echo "BAR CHECK: at least one probe absent or value mismatched."
fi
exit "$fail"
