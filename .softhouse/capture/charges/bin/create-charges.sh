#!/bin/sh
# T40 — create the ten charge definitions on tenant `gerege`.  ADDITIVE ONLY.
# Nothing existing is mutated: `select count(*) from m_charge` was 0 before this ran,
# so every charge id on the tenant belongs to T40 and a later fire can find them all.
set -eu
. /Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513/.softhouse/capture/charges/bin/lib.sh

O=$CH/out/charges
mkdir -p "$O"

sh "$CH/bin/run-preconditions.sh" "$O/preconditions.txt" > /dev/null || {
  echo "ABORT: preconditions breached — nothing created." >&2; exit 1; }
echo "preconditions: ALL PASS"

for f in "$CH"/req/charge-*.json; do
  n=$(basename "$f" .json)
  post "$f" "$O/$n-create.json" "charges" || exit 1
  cat "$O/$n-create.json"; echo
done

echo
echo "### m_charge as persisted in PostgreSQL"
docker exec fineract-db-1 psql -U root -d fineract_gerege -c \
  "select id,name,charge_applies_to_enum as applies,charge_time_enum as time,charge_calculation_enum as calc,charge_payment_mode_enum as mode,amount,currency_code,is_penalty,is_active from m_charge order by id;"
