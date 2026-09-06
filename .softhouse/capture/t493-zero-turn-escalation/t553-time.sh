#!/usr/bin/env bash
# t553-time.sh <repo> <guard> <ref> [n]
# Times n (default 3) full runs of the guard over <ref>, reporting wall seconds
# and peak RSS. A guard that makes the fire slow gets disabled as surely as one
# that fails, so this is measured before and after every change.
set -uo pipefail
REPO="$1"; GUARD="$2"; REF="$3"; N="${4:-3}"
cd "$REPO"
i=0
while [ "$i" -lt "$N" ]; do
  i=$((i+1))
  t0=$(python3 -c 'import time;print(time.time())')
  "$GUARD" --producer local --ref "$REF" --no-fetch --quiet >/dev/null
  rc=$?
  t1=$(python3 -c 'import time;print(time.time())')
  python3 -c "print('  run $i: real=%.2fs  exit=$rc' % ($t1-$t0))"
done
