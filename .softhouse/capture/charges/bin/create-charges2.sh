#!/bin/sh
# T40 pass 2 — create charge definitions 11 and 12.  ADDITIVE ONLY.
set -eu
. /Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513/.softhouse/capture/charges/bin/lib.sh

O=$CH/out/charges
mkdir -p "$O"
sh "$CH/bin/run-preconditions.sh" "$O/preconditions-pass2.txt" > /dev/null || {
  echo "ABORT: preconditions breached — nothing created." >&2; exit 1; }
echo "preconditions: ALL PASS"

for n in charge-11-pctinterest-specifieddue charge-12-pctamountinterest-specifieddue; do
  post "$CH/req/$n.json" "$O/$n-create.json" "charges" || exit 1
  cat "$O/$n-create.json"; echo
done

docker exec fineract-db-1 psql -U root -d fineract_gerege -c \
  "select id,name,charge_applies_to_enum as applies,charge_time_enum as time,charge_calculation_enum as calc,amount,currency_code,is_penalty,is_active from m_charge order by id;"
