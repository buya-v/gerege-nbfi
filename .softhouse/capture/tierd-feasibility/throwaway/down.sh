#!/bin/sh
# Tier D FEASIBILITY -- DESTROY the throwaway instance and PROVE the standing reference oracle
# did not move. Copy of the T305 down.sh, strengthened to check BOTH standing DBs (see the guard
# header for why).
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
CF="$DIR/docker-compose.tierd.yml"
BASE="$DIR/out/STANDING-baseline.txt"
STANDING_DBS="fineract-db-1:fineract-db-1:fineract_gerege gerege-oracle-db:gerege-oracle-db:fineract_gerege"
say() { printf '%s\n' "$*"; }

say "TierD throwaway teardown -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
docker compose -p tierd-oracle -f "$CF" down -v 2>&1 | sed 's/^/  /'

say ""
say "containers matching tierd after teardown:"
LEFT=$(docker ps -a --format '{{.Names}}' | grep tierd || true)
if [ -n "$LEFT" ]; then say "  *** STILL PRESENT: $LEFT ***"; else say "  (none)"; fi
say "networks matching tierd after teardown:"
NET=$(docker network ls --format '{{.Name}}' | grep tierd || true)
if [ -n "$NET" ]; then say "  *** STILL PRESENT: $NET ***"; else say "  (none)"; fi
say "volumes matching tierd after teardown:"
VOL=$(docker volume ls --format '{{.Name}}' | grep tierd || true)
if [ -n "$VOL" ]; then say "  *** STILL PRESENT: $VOL ***"; else say "  (none)"; fi

say ""
say "STANDING reference oracle after teardown (must equal the baseline this capture opened with):"
HC=$(curl -sk -o /dev/null -w '%{http_code}' https://localhost:8443/fineract-provider/actuator/health 2>/dev/null)
say "  standing health = $HC"
[ "$HC" = "200" ] || { say "  *** standing oracle is NOT answering 200 ***"; exit 1; }
rc=0
for entry in $STANDING_DBS; do
  label=$(printf '%s' "$entry" | cut -d: -f1)
  cname=$(printf '%s' "$entry" | cut -d: -f2)
  dbname=$(printf '%s' "$entry" | cut -d: -f3)
  for q in \
    "acc_gl_journal_entry|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_journal_entry" \
    "acc_gl_closure|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_closure" \
    "distinct_transaction_id|SELECT count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry" \
    "m_portfolio_command_source|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source" \
    "m_client|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_client" \
    "m_loan|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_loan" ; do
    qlabel=$(printf '%s' "$q" | cut -d'|' -f1)
    sql=$(printf '%s' "$q" | cut -d'|' -f2-)
    now=$(docker exec -i "$cname" psql -U root -d "$dbname" -Atc "$sql" 2>/dev/null)
    want=$(grep "$label $qlabel = " "$BASE" | sed "s/.*$label $qlabel = //")
    if [ "$now" = "$want" ]; then
      say "  ok  $label $qlabel = $now (== baseline)"
    else
      say "  *** $label $qlabel baseline '$want', now '$now' -- THE STANDING ORACLE MOVED ***"; rc=1
    fi
  done
done
exit $rc
