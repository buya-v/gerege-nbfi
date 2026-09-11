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

say ""
say "3. isolation guard (read-only), then the standing baseline this capture opens with:"
GUARD="$DIR/guard-throwaway-isolation.sh"
[ -x "$GUARD" ] || { say "  CANNOT MEASURE: isolation guard missing or not executable: $GUARD. Fail-closed."; exit 2; }
sh "$GUARD" || { say "  *** isolation guard REFUSED -- see its output above ***"; exit 1; }

# 4. Write the standing baseline that down.sh compares against. It is written HERE, by preflight,
#    BEFORE the throwaway starts, so a teardown can never compare against a missing file (the
#    second feasibility attempt did exactly that and cried wolf).
mkdir -p "$DIR/out"
BASE="$DIR/out/STANDING-baseline.txt"
: > "$BASE"
for entry in fineract-db-1:fineract-db-1:fineract_gerege gerege-oracle-db:gerege-oracle-db:fineract_gerege; do
  label=$(printf '%s' "$entry" | cut -d: -f1)
  cname=$(printf '%s' "$entry" | cut -d: -f2)
  dbname=$(printf '%s' "$entry" | cut -d: -f3)
  docker ps --format '{{.Names}}' | grep -qx "$cname" || { say "  CANNOT MEASURE baseline: standing DB '$cname' is not running. Fail-closed."; exit 2; }
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
    [ -n "$v" ] || { say "  CANNOT MEASURE baseline: '$cname/$qlabel' returned nothing. Fail-closed."; exit 2; }
    printf '%s %s = %s\n' "$label" "$qlabel" "$v" >> "$BASE"
  done
done
n=$(wc -l < "$BASE" | tr -d ' ')
[ "$n" = "12" ] || { say "  CANNOT MEASURE baseline: wrote $n of 12 counters. Fail-closed."; exit 2; }
say "  standing baseline written by preflight.sh: $BASE ($n counters)"

[ "$rc" -eq 0 ] && say "PREFLIGHT OK" || say "PREFLIGHT FAILED"
exit $rc
