#!/bin/sh
# T135 — a DELIBERATELY BROADER vacuity sweep than T99b's, to find real sites its pattern misses.
# Run from a script => /usr/bin/grep (BSD grep), LC_ALL=C throughout (P-33).
set -u
ROOT=$1
cd "$ROOT" || exit 9
echo "root: $ROOT   grep: $(command -v grep)  $(grep --version 2>&1 | head -1)"

echo
echo "=== 1. ANY grep counting form (split flags, long flag, any cluster)"
LC_ALL=C grep -rnE "grep([[:space:]]+-[a-zA-Z]+)*[[:space:]]+(-[a-zA-Z]*c[a-zA-Z]*|--count)([[:space:]]|$)" \
  --include='*.sh' . | sed 's|^\./||'

echo
echo "=== 2. ANY zero/empty comparison used as a verdict"
LC_ALL=C grep -rnE '\[+[[:space:]]+("?\$\{?[A-Za-z_][A-Za-z0-9_]*\}?"?)[[:space:]]+(=|==|-eq)[[:space:]]+"?0"?[[:space:]]+\]+|\[+[[:space:]]+-z[[:space:]]|test[[:space:]]+-z[[:space:]]|\$\{#[A-Za-z_]' \
  --include='*.sh' . | sed 's|^\./||'

echo
echo "=== 3. grep -q / grep -s used as an ABSENCE test (if ! grep -q ...)"
LC_ALL=C grep -rnE 'if[[:space:]]+!|![[:space:]]+.*grep[[:space:]]+-[a-zA-Z]*q|grep[[:space:]]+-[a-zA-Z]*q' \
  --include='*.sh' . | sed 's|^\./||'

echo
echo "=== 4. test -s / -s file emptiness tests"
LC_ALL=C grep -rnE '\[[[:space:]]+-s[[:space:]]|test[[:space:]]+-s[[:space:]]' --include='*.sh' . | sed 's|^\./||'

echo
echo "=== 5. python-side absence verdicts (len(...)==0, not x, == 0)"
LC_ALL=C grep -rnE 'len\([^)]*\)[[:space:]]*==[[:space:]]*0|==[[:space:]]*0[[:space:]]*:|if not [a-z_]+:' \
  --include='*.py' . | sed 's|^\./||'
