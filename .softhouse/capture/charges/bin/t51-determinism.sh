#!/bin/sh
# T51 -- determinism.  Re-issue EVERY committed T51 request against the same running oracle
# and require the response bytes to be identical to what was captured.  A capture that does
# not reproduce is not evidence about the oracle, it is evidence about the moment.
#
# Creates nothing: calculateLoanSchedule only.  Server state is asserted unchanged.
set -eu
. "$(dirname "$0")/lib.sh"
O=$CH/out/t51
D=$CH/out/t51-rerun
mkdir -p "$D"

echo "== T51 determinism re-run =="
docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$D/state-before.txt"

same=0; diff_=0; missing=0
for f in "$CH"/req/calc-T51-*.json; do
  case "$f" in *TEMPLATE.json) continue;; esac
  n=$(basename "$f" .json); n=${n#calc-}
  orig=$O/T51-${n#T51-}-raw.json
  [ -f "$orig" ] || orig=$O/$n-raw.json
  if [ ! -f "$orig" ]; then
    echo "  SKIP $n (no committed capture)"; missing=$((missing+1)); continue
  fi
  curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
    -d @"$f" -o "$D/$n-rerun.json" -w ''
  if cmp -s "$orig" "$D/$n-rerun.json"; then
    same=$((same+1))
  else
    diff_=$((diff_+1)); echo "  **DIFFERS** $n"
  fi
done
echo "  identical: $same    differing: $diff_    skipped: $missing"

docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$D/state-after.txt"
[ "$(cat "$D/state-before.txt")" = "$(cat "$D/state-after.txt")" ] \
  || { echo "BREACH: the determinism re-run changed server state" >&2; exit 1; }
echo "  server state unchanged: $(cat "$D/state-after.txt")"
[ "$diff_" = "0" ] || { echo "BREACH: $diff_ captures did not reproduce byte for byte" >&2; exit 1; }
echo "DETERMINISM PASS: $same of $same re-issued requests reproduced byte for byte."
