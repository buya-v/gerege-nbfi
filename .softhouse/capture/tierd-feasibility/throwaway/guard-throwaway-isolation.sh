#!/bin/sh
# Tier D FEASIBILITY -- THROWAWAY-INSTANCE ISOLATION GUARD. FAIL-CLOSED. READ-ONLY.
#
# Copy of the T305 rig's guard (capture/t305-openingbalance-accepting-side/throwaway/
# guard-throwaway-isolation.sh), with ONE deliberate strengthening: T305 read its baseline from
# `fineract-db-1` only. The standing app container answering on 8443 right now is
# `gerege-oracle-app`, whose FINERACT_HIKARI_JDBC_URL is jdbc:postgresql://db:5432/fineract_tenants
# on the `gerege-nbfi_default` network -- i.e. its tenant DB is served by `gerege-oracle-db`, not
# by `fineract-db-1`. So this guard reads BOTH, and the after-check in down.sh requires BOTH to be
# unchanged. Reading only one is how an instrument misses the tenant that actually moved (P-72:
# calibrate the instrument on a known positive).
#
# It refuses (exit 1) unless EVERY one of these holds, and fails closed (exit 2) if it cannot
# measure one of them:
#
#   I1  the compose file publishes NEITHER 5432 NOR 8443 -- the ports the standing stack owns.
#   I2  its container names collide with NO running container.
#   I3  it declares NO named volume; the only writable bind mount is under /tmp.
#   I4  it does NOT bind-mount anything from the pinned Fineract checkout read-WRITE.
#   I5  the standing oracle is UP and its ledger counters are recorded for BOTH standing DBs, so
#       the same numbers can be re-read after teardown. The only condition that talks to the
#       standing stack, and it talks READ-ONLY.
#
# EXIT 0 = isolated, baseline printed. 1 = refused. 2 = cannot measure.
set -u
DIR=$(cd "$(dirname "$0")" && pwd)
CF="$DIR/docker-compose.tierd.yml"
STANDING_HEALTH=https://localhost:8443/fineract-provider/actuator/health
# label:container:db -- both candidate standing oracle DBs, both read-only.
STANDING_DBS="fineract-db-1:fineract-db-1:fineract_gerege gerege-oracle-db:gerege-oracle-db:fineract_gerege"

say() { printf '%s\n' "$*"; }
fail=0

say "TierD throwaway-isolation guard -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
[ -f "$CF" ] || { say "CANNOT MEASURE: $CF is missing. Fail-closed."; exit 2; }

# ---- I1 -- published ports --------------------------------------------------------------
PORTS=$(grep -E '^[[:space:]]+- "[0-9]+:[0-9]+"' "$CF" | tr -d ' "-')
say ""
say "I1 published host ports declared by the compose file:"
if [ -z "$PORTS" ]; then say "   (none)"; else for p in $PORTS; do say "   $p"; done; fi
for p in $PORTS; do
  host=$(printf '%s' "$p" | cut -d: -f1)
  case "$host" in
    5432|8443) say "   REFUSE I1 host port $host is the STANDING stack's. This file must never claim it."; fail=1 ;;
    *) ;;
  esac
done
[ "$fail" -eq 0 ] && say "   ok  I1 no standing port is claimed."

# ---- I2 -- container name collision -----------------------------------------------------
NAMES=$(grep -E '^[[:space:]]+container_name:' "$CF" | awk '{print $2}')
[ -n "$NAMES" ] || { say "CANNOT MEASURE I2: no container_name in $CF. Fail-closed."; exit 2; }
RUNNING=$(docker ps -a --format '{{.Names}}' 2>/dev/null) || { say "CANNOT MEASURE I2: docker ps failed."; exit 2; }
say ""
say "I2 container names:"
for n in $NAMES; do
  if printf '%s\n' "$RUNNING" | grep -qx "$n"; then
    say "   NOTE  $n already exists -- this rig's own container from an earlier run, or a collision. down.sh removes it."
  else
    say "   ok    $n does not exist yet."
  fi
  case "$n" in
    fineract-db-1|fineract-fineract-1|gerege-oracle-db|gerege-oracle-app) say "   REFUSE I2 $n IS a standing container name."; fail=1 ;;
  esac
done

# ---- I3/I4 -- volumes -------------------------------------------------------------------
say ""
say "I3/I4 bind mounts declared:"
MOUNTS=$(grep -E '^[[:space:]]+- /[^:]+:/' "$CF" | sed 's/^[[:space:]]*-[[:space:]]*//')
[ -n "$MOUNTS" ] || { say "CANNOT MEASURE I3: no bind mounts parsed from $CF. Fail-closed."; exit 2; }
for m in $MOUNTS; do
  src=$(printf '%s' "$m" | cut -d: -f1)
  mode=$(printf '%s' "$m" | awk -F: '{print $NF}')
  case "$mode" in
    ro) say "   ok    $src  (read-only)" ;;
    rw)
      case "$src" in
        /tmp/*) say "   ok    $src  (read-write, under /tmp -- outside every repository)" ;;
        *)      say "   REFUSE I4 $src is mounted READ-WRITE and is not under /tmp."; fail=1 ;;
      esac ;;
    *) say "   REFUSE I3 '$m' has no explicit ro/rw mode; a capture rig may not leave that implicit."; fail=1 ;;
  esac
done
if grep -qE '^volumes:' "$CF"; then
  say "   REFUSE I3 the file declares a top-level named volume. A throwaway must leave no volume behind."
  fail=1
else
  say "   ok    I3 no named volume declared -- 'docker compose down -v' therefore destroys all state."
fi

# ---- I5 -- the standing oracle, read-only -----------------------------------------------
say ""
say "I5 STANDING reference oracle baseline (read-only):"
HC=$(curl -sk -o /dev/null -w '%{http_code}' "$STANDING_HEALTH" 2>/dev/null)
if [ "$HC" != "200" ]; then
  say "   CANNOT MEASURE I5: standing health probe returned '$HC', not 200."
  say "   A capture rig that cannot see the standing oracle cannot prove it left it alone. Fail-closed."
  exit 2
fi
say "   standing health = 200"
for entry in $STANDING_DBS; do
  label=$(printf '%s' "$entry" | cut -d: -f1)
  cname=$(printf '%s' "$entry" | cut -d: -f2)
  dbname=$(printf '%s' "$entry" | cut -d: -f3)
  docker ps --format '{{.Names}}' | grep -qx "$cname" || { say "   CANNOT MEASURE I5: standing DB container '$cname' is not running. Fail-closed."; exit 2; }
  for q in \
    "acc_gl_journal_entry|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_journal_entry" \
    "acc_gl_closure|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_closure" \
    "distinct_transaction_id|SELECT count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry" \
    "m_portfolio_command_source|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source" \
    "m_client|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_client" \
    "m_loan|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_loan" ; do
    qlabel=$(printf '%s' "$q" | cut -d'|' -f1)
    sql=$(printf '%s' "$q" | cut -d'|' -f2-)
    v=$(docker exec -i "$cname" psql -U root -d "$dbname" -Atc "$sql" 2>/dev/null)
    [ -n "$v" ] || { say "   CANNOT MEASURE I5: '$cname/$qlabel' returned nothing. Fail-closed."; exit 2; }
    say "   $label $qlabel = $v"
  done
done

say ""
if [ "$fail" -ne 0 ]; then
  say "REFUSED: the throwaway rig is not isolated from the standing reference oracle."
  exit 1
fi
say "ISOLATED: the throwaway claims no standing port, no standing container name, no named volume"
say "and no read-write mount outside /tmp; the standing oracle is UP and both baselines are above."
exit 0
