#!/usr/bin/env bash
# T253b — VERIFYING A CLAIM I INHERITED RATHER THAN TAKING IT ON TRUST.
#
# The claim (from the concurrent cloud fire, relayed by the driver): the fail-open
# TIER of .softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh
# depends on LEFTOVER /tmp STATE on the linting host — C1 calls /tmp/t234_matrix2.txt a
# dead path, while line 7 of that same instrument creates it — so the row flips TIER2 -> TIER1
# on a host where the file has never been created.
#
# I am on the Mac, where the file EXISTS. So I can test the claim directly: move the
# residue aside, re-lint, compare the frontier row-for-row, put it back.
#
# THIS TOUCHES NOTHING TRACKED. One scratch file in /tmp is moved and restored under a trap
# that fires on QUIT as well as EXIT/HUP/INT/TERM.
#
# No bare `grep`, no `rg` (P-75); the frontier rows are extracted with python3 re.
# Every rc is captured and asserted (P-80).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
LINT="$REPO/.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
RESIDUE=/tmp/t234_matrix2.txt
STASH=""

[ -f "$LINT" ] || { printf 'REFUSING: linter absent at %s\n' "$LINT" >&2; exit 2; }

restore() {
  if [ -n "$STASH" ] && [ -f "$STASH" ]; then
    mv -f "$STASH" "$RESIDUE"
    printf 'RESTORED: %s put back\n' "$RESIDUE"
  fi
}
trap restore EXIT HUP INT TERM QUIT

# frontier_rows OUTFILE -> prints "TIER<x> <path>" rows only
frontier_rows() {
  python3 - "$1" <<'PY'
import re, sys
rows = []
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    m = re.match(r'^FAILOPEN-FRONTIER\s+(\S+)\s+(\S+)\s*$', line)
    if m:
        rows.append("%s %s" % (m.group(1), m.group(2)))
print("\n".join(rows))
PY
}

run_lint() {                      # run_lint OUTFILE
  local rc=0
  ( cd "$REPO" && FAILOPEN_LINT_JSON="$(mktemp "${TMPDIR:-/tmp}/t253-lint.XXXXXXXXXX")" \
      python3 "$LINT" ) >"$1" 2>&1 || rc=$?
  # rc 1 is the linter's normal "frontier is non-empty" verdict; >1 is a real error.
  if [ "$rc" -gt 1 ]; then
    printf 'REFUSING: linter exited %d (an ERROR, not a verdict)\n' "$rc" >&2
    exit 2
  fi
  printf '%d' "$rc"
}

A="$(mktemp "${TMPDIR:-/tmp}/t253-lintA.XXXXXXXXXX")"
B="$(mktemp "${TMPDIR:-/tmp}/t253-lintB.XXXXXXXXXX")"

echo "=== CALIBRATION: does the residue exist on this host right now? ==="
if [ -f "$RESIDUE" ]; then
  printf '  PRESENT: %s\n' "$(ls -l "$RESIDUE")"
else
  printf '  ABSENT — the probe cannot run its A arm on this host.\n'
  exit 2
fi
printf '  and line 6-7 of the instrument, which NAME and CREATE it:\n'
sed -n '6,7p' "$REPO/.softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh" \
  | sed 's/^/    | /'
echo

echo "=== ARM A: residue PRESENT (the Mac's normal state) ==="
RC_A="$(run_lint "$A")"
frontier_rows "$A" > "$A.rows"
printf '  linter rc=%s, frontier rows=%d\n' "$RC_A" "$(wc -l < "$A.rows" | tr -d ' ')"
sed 's/^/    /' "$A.rows"
echo

echo "=== ARM B: residue MOVED ASIDE (what any host without the leftover sees) ==="
STASH="$(mktemp "${TMPDIR:-/tmp}/t253-residue.XXXXXXXXXX")"
mv -f "$RESIDUE" "$STASH"
[ -f "$RESIDUE" ] && { echo "REFUSING: residue still present after move"; exit 2; }
echo "  moved $RESIDUE aside; it is now absent"
RC_B="$(run_lint "$B")"
frontier_rows "$B" > "$B.rows"
printf '  linter rc=%s, frontier rows=%d\n' "$RC_B" "$(wc -l < "$B.rows" | tr -d ' ')"
sed 's/^/    /' "$B.rows"
echo

echo "=== VERDICT ==="
if diff -u "$A.rows" "$B.rows" > "$A.diff"; then
  echo "  FRONTIER IDENTICAL between the two arms."
  echo "  THE CLAIM IS NOT REPRODUCED ON THIS HOST: the tier of 02-escape-matrix-fix.sh does"
  echo "  NOT depend on the presence of $RESIDUE."
else
  echo "  FRONTIER DIFFERS — the claim IS reproduced. Residue-dependent classification:"
  sed 's/^/    /' "$A.diff"
fi
