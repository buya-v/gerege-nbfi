#!/bin/sh
# T305 -- DESTROY the throwaway instance and PROVE the standing reference oracle did not move.
#
# `down -v` removes the containers, the network and the anonymous volumes. The compose file
# declares NO named volume (guard-throwaway-isolation.sh I3 enforces that), so after this runs
# there is no tenant registry, no tenant database, no journal entry and no audit row anywhere
# from this capture. THAT IS THE WHOLE SAFETY ARGUMENT: an accepted opening balance cannot be
# deleted, so it is taken somewhere that can be.
#
# What it does NOT claim to remove: the /tmp/t305-oracle-logs directory (host-side log bind
# mount) and the docker image layers, which were already present and are shared with the
# standing stack.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
CF="$DIR/docker-compose.t305.yml"
BASE="$DIR/out/STANDING-baseline.txt"
STANDING_DB=fineract-db-1
say() { printf '%s\n' "$*"; }

say "T305 throwaway teardown -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
docker compose -p t305-oracle -f "$CF" down -v 2>&1 | sed 's/^/  /'

say ""
say "containers matching t305 after teardown:"
LEFT=$(docker ps -a --format '{{.Names}}' | grep t305 || true)
if [ -n "$LEFT" ]; then say "  *** STILL PRESENT: $LEFT ***"; else say "  (none)"; fi
say "networks matching t305 after teardown:"
NET=$(docker network ls --format '{{.Name}}' | grep t305 || true)
if [ -n "$NET" ]; then say "  *** STILL PRESENT: $NET ***"; else say "  (none)"; fi
say "volumes matching t305 after teardown:"
VOL=$(docker volume ls --format '{{.Name}}' | grep t305 || true)
if [ -n "$VOL" ]; then say "  *** STILL PRESENT: $VOL ***"; else say "  (none)"; fi

say ""
say "STANDING reference oracle after teardown (must equal the baseline this capture opened with):"
HC=$(curl -sk -o /dev/null -w '%{http_code}' https://localhost:8443/fineract-provider/actuator/health 2>/dev/null)
say "  standing health = $HC"
[ "$HC" = "200" ] || { say "  *** standing oracle is NOT answering 200 ***"; exit 1; }
rc=0
for q in \
  "acc_gl_journal_entry|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_journal_entry" \
  "acc_gl_closure|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_closure" \
  "distinct_transaction_id|SELECT count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry" \
  "m_portfolio_command_source|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source" ; do
  label=$(printf '%s' "$q" | cut -d'|' -f1)
  sql=$(printf '%s' "$q" | cut -d'|' -f2-)
  now=$(docker exec -i "$STANDING_DB" psql -U root -d fineract_gerege -Atc "$sql" 2>/dev/null)
  want=$(grep "gerege $label = " "$BASE" | sed "s/.*gerege $label = //")
  if [ "$now" = "$want" ]; then
    say "  ok  $label = $now (== baseline)"
  else
    say "  *** $label baseline '$want', now '$now' -- THE STANDING ORACLE MOVED ***"; rc=1
  fi
done
exit $rc
