#!/bin/sh
# T48 -- determinism control for the charge-gap pass.
#
# Re-posts every T48 request VERBATIM against the same running oracle and requires the
# response bytes to be IDENTICAL to the committed capture.  Creates nothing, modifies
# nothing.  A single differing byte is exit 1.
set -eu
. "$(dirname "$0")/lib.sh"

O=$CH/out/t48
R=$CH/out/t48-rerun
mkdir -p "$R"

sh "$CH/bin/run-preconditions.sh" "$R/preconditions.txt" > /dev/null || {
  echo "ABORT: preconditions breached." >&2; exit 1; }
echo "preconditions: ALL PASS"

BAD=0
for f in "$CH"/req/calc-T48-CH-*.json; do
  case "$f" in *TEMPLATE.json) continue;; esac
  n=$(basename "$f" .json); n=${n#calc-}
  curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
       -d @"$f" -o "$R/$n-raw.json" -w ''
  if cmp -s "$O/$n-raw.json" "$R/$n-raw.json"; then
    echo "  ok  $n  byte-identical"
  else
    echo "  DIFFERS  $n"; BAD=$((BAD+1))
  fi
done

echo
if [ "$BAD" = "0" ]; then
  echo "== DETERMINISM PASS -- every T48 capture reproduced byte for byte"
  exit 0
fi
echo "== DETERMINISM FAIL -- $BAD captures differ on re-run"
exit 1
