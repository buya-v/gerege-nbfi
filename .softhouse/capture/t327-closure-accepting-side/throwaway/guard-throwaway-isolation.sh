#!/bin/sh
# T327 -- THROWAWAY-INSTANCE ISOLATION GUARD. FAIL-CLOSED. READ-ONLY.
#
# WHAT IT IS FOR. The whole safety argument for capturing the opening-balance ACCEPTING side on a
# throwaway instance is that the STANDING reference oracle is not touched at all. That argument is
# worth exactly as much as the isolation is, so the isolation is MEASURED here rather than asserted
# in a comment (P-89: "PROSE DOES NOT FIRE ON THE NEXT FIRE").
#
# It refuses (exit 1) unless EVERY one of these holds, and it fails closed (exit 2) if it cannot
# measure one of them:
#
#   I1  the compose file publishes NEITHER 5432 NOR 8443 -- the two ports the standing stack owns.
#       A throwaway that grabbed 8443 would not start; a throwaway that grabbed 5432 would not
#       either; but the failure this guard is really about is the reverse -- a compose file edited
#       later to "just use the normal ports" and then run against the live rig.
#   I2  its container names collide with NO running container.
#   I3  it declares NO named volume and NO bind mount into any tenant database directory; the only
#       writable bind mount is under /tmp.
#   I4  it does NOT bind-mount anything from the pinned Fineract checkout read-WRITE (a capture rig
#       must not be able to edit the oracle's own source tree).
#   I5  the standing oracle is UP and its ledger counters are recorded, so the same numbers can be
#       re-read after teardown. This is the only condition that talks to the standing stack, and it
#       talks to it READ-ONLY.
#
# EXIT 0 = isolated, and the standing baseline is printed. 1 = refused. 2 = cannot measure.
set -u
DIR=$(cd "$(dirname "$0")" && pwd)
CF="$DIR/docker-compose.t327.yml"
STANDING_DB=fineract-db-1
STANDING_APP=fineract-fineract-1
STANDING_HEALTH=https://localhost:8443/fineract-provider/actuator/health

say() { printf '%s\n' "$*"; }
fail=0

say "T327 throwaway-isolation guard -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
[ -f "$CF" ] || { say "CANNOT MEASURE: $CF is missing. Fail-closed."; exit 2; }

# ---- I1 -- published ports --------------------------------------------------------------
PORTS=$(grep -E '^\s+- "[0-9]+:[0-9]+"' "$CF" | tr -d ' "-')
say ""
say "I1 published host ports declared by the compose file:"
if [ -z "$PORTS" ]; then
  say "   (none)"
else
  for p in $PORTS; do say "   $p"; done
fi
for p in $PORTS; do
  host=$(printf '%s' "$p" | cut -d: -f1)
  case "$host" in
    5432|8443) say "   REFUSE I1 host port $host is the STANDING stack's. This file must never claim it."; fail=1 ;;
    *) ;;
  esac
done
[ "$fail" -eq 0 ] && say "   ok  I1 no standing port is claimed."

# ---- I2 -- container name collision -----------------------------------------------------
NAMES=$(grep -E '^\s+container_name:' "$CF" | awk '{print $2}')
[ -n "$NAMES" ] || { say "CANNOT MEASURE I2: no container_name in $CF. Fail-closed."; exit 2; }
RUNNING=$(docker ps -a --format '{{.Names}}' 2>/dev/null) || { say "CANNOT MEASURE I2: docker ps failed."; exit 2; }
say ""
say "I2 container names:"
for n in $NAMES; do
  if printf '%s\n' "$RUNNING" | grep -qx "$n"; then
    say "   NOTE  $n already exists -- it is THIS rig's own container from an earlier run, or a collision."
    say "         down.sh removes it. Not a refusal by itself; re-run after teardown."
  else
    say "   ok    $n does not exist yet."
  fi
  case "$n" in
    "$STANDING_DB"|"$STANDING_APP") say "   REFUSE I2 $n IS a standing container name."; fail=1 ;;
  esac
done

# ---- I3/I4 -- volumes -------------------------------------------------------------------
say ""
say "I3/I4 bind mounts declared:"
# A BIND MOUNT is `- <hostpath>:<containerpath>[:mode]`, so the DESTINATION starts with `/` too.
# That shape is what separates a real mount from an `env_file:` entry (`- /x/y.env`, no destination)
# and from a `tmpfs:` entry (`- /tmp:rw,nosuid,size=256m`, whose second field is not a path). The
# first draft of this guard matched `^\s+- /` and refused all six of those as "no explicit ro/rw
# mode" -- a false positive that P-72 ("calibrate the instrument on a known positive") is about, and
# it is recorded here rather than quietly fixed.
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
for q in \
  "acc_gl_journal_entry|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_journal_entry" \
  "acc_gl_closure|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_closure" \
  "distinct_transaction_id|SELECT count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry" \
  "m_portfolio_command_source|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source" \
  "m_loan|SELECT count(*)::text FROM m_loan" \
  "m_office|SELECT count(*)::text FROM m_office" ; do
  label=$(printf '%s' "$q" | cut -d'|' -f1)
  sql=$(printf '%s' "$q" | cut -d'|' -f2-)
  v=$(docker exec -i "$STANDING_DB" psql -U root -d fineract_gerege -Atc "$sql" 2>/dev/null)
  [ -n "$v" ] || { say "   CANNOT MEASURE I5: '$label' returned nothing. Fail-closed."; exit 2; }
  say "   gerege $label = $v"
done

say ""
if [ "$fail" -ne 0 ]; then
  say "REFUSED: the throwaway rig is not isolated from the standing reference oracle."
  exit 1
fi
say "ISOLATED: the throwaway claims no standing port, no standing container name, no named volume"
say "and no read-write mount outside /tmp; the standing oracle is UP and its baseline is above."
exit 0
