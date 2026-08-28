#!/usr/bin/env bash
# T409 -- re-derive the SIX t327 standing pins live and make the SAME string comparison
# t327/throwaway/capture.sh:82 and down.sh:51 make. The six label|SQL pairs are copied
# verbatim out of capture.sh:70-75 so the comparison under test is the real one.
#
# It does NOT run capture.sh or down.sh: down.sh tears containers down and capture.sh POSTS.
# READ-ONLY: six SELECTs against the standing oracle.
set -uo pipefail
ROOT="${1:?usage: pins-live.sh <repo-root>}"
T327="$ROOT/.softhouse/capture/t327-closure-accepting-side/throwaway"
T305="$ROOT/.softhouse/capture/t305-openingbalance-accepting-side/throwaway"
STANDING_DB="${STANDING_DB:-fineract-db-1}"

echo "T409 t327 STANDING PIN RE-DERIVATION -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

for BASE in "$T327/out/STANDING-baseline.txt" "$T305/out/STANDING-baseline.txt"; do
  echo "== baseline: ${BASE#$ROOT/}"
  moved=0; unmoved=0; absent=0
  for q in \
    "acc_gl_journal_entry|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_journal_entry" \
    "acc_gl_closure|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_closure" \
    "distinct_transaction_id|SELECT count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry" \
    "m_portfolio_command_source|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source" \
    "m_loan|SELECT count(*)::text FROM m_loan" \
    "m_office|SELECT count(*)::text FROM m_office" ; do
    label=$(printf '%s' "$q" | cut -d'|' -f1)
    sql=$(printf '%s' "$q" | cut -d'|' -f2-)
    now=$(docker exec -i "$STANDING_DB" psql -U root -d fineract_gerege -Atc "$sql" 2>/dev/null)
    want=$(grep "gerege $label = " "$BASE" 2>/dev/null | sed "s/.*gerege $label = //")
    if [ -z "$want" ]; then
      printf '  %-28s baseline carries NO pin for this label -- not pinned by this rig\n' "$label"
      absent=$((absent+1))
    elif [ "$now" = "$want" ]; then
      printf '  %-28s pinned %-10s live %-10s unmoved\n' "$label" "$want" "$now"
      unmoved=$((unmoved+1))
    else
      printf '  %-28s pinned %-10s live %-10s *** MOVED ***\n' "$label" "$want" "$now"
      moved=$((moved+1))
    fi
  done
  echo "  -> MOVED=$moved  unmoved=$unmoved  not-pinned=$absent"
  echo
done
