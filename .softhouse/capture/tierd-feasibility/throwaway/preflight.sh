#!/bin/sh
# Tier D FEASIBILITY -- PREFLIGHT. Proves the throwaway is built from the SAME IMAGE the
# standing reference oracle runs (T305's "image-id check"), and that tenant `tierd` does not
# exist anywhere on the standing stack.
set -u
DIR=$(cd "$(dirname "$0")" && pwd)
say() { printf '%s\n' "$*"; }
rc=0

say "TierD preflight -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Image identity. The throwaway compose pins `fineract:latest`; the standing app containers
# must run that exact image id, or the throwaway is not the same oracle and this is not a replay.
THROWAWAY_IMG=$(docker image inspect -f '{{.Id}}' fineract:latest 2>/dev/null) || { say "FAIL: fineract:latest not present."; exit 1; }
say "fineract:latest image id = $THROWAWAY_IMG"
for c in gerege-oracle-app fineract-fineract-1; do
  if docker ps -a --format '{{.Names}}' | grep -qx "$c"; then
    id=$(docker inspect -f '{{.Image}}' "$c" 2>/dev/null)
    if [ "$id" = "$THROWAWAY_IMG" ]; then
      say "  ok  $c runs the SAME image ($id)"
    else
      say "  *** $c runs $id -- DIFFERENT from fineract:latest ***"; rc=1
    fi
  else
    say "  --  $c not present"
  fi
done

# 2. The throwaway tenant identifier must not exist on either standing DB.
for cname in fineract-db-1 gerege-oracle-db; do
  if docker ps --format '{{.Names}}' | grep -qx "$cname"; then
    cnt=$(docker exec -i "$cname" psql -U root -d fineract_tenants -Atc "SELECT count(*) FROM tenants WHERE identifier='tierd'" 2>/dev/null)
    [ -n "$cnt" ] || { say "  CANNOT MEASURE tenant collision on $cname. Fail-closed."; exit 2; }
    if [ "$cnt" = "0" ]; then say "  ok  $cname has no tenant 'tierd'"; else say "  *** $cname ALREADY HAS tenant 'tierd' ***"; rc=1; fi
  fi
done

[ "$rc" -eq 0 ] && say "PREFLIGHT OK" || say "PREFLIGHT FAILED"
exit $rc
