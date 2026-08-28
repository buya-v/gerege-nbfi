#!/usr/bin/env bash
# T367 -- does the THIRD pin actually fail? Re-derives the F5 comparison the t305/t327 rigs
# perform, WITHOUT running capture.sh (which would bring a throwaway up and fire writes at it).
#
# The comparison re-implemented here is verbatim in shape from
#   t305/throwaway/capture.sh:63-80  (and capture2.sh:36-59, down.sh:16-52)
#   want=$(grep "gerege $label = " "$BASE" | sed "s/.*gerege $label = //")
#   [ "$now" = "$want" ] || refuse
#
# READ-ONLY: four SELECTs against the standing tenant, and a grep of a committed file.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 2
STANDING_DB=fineract-db-1
rc=0

for rig in t305-openingbalance-accepting-side t327-closure-accepting-side; do
  BASE=".softhouse/capture/$rig/throwaway/out/STANDING-baseline.txt"
  printf '\n=== %s\n    baseline: %s\n' "$rig" "$BASE"
  if [ ! -f "$BASE" ]; then echo "    (no committed baseline)"; continue; fi
  printf '    baseline taken at: %s\n' "$(head -1 "$BASE" | sed 's/.*-- //')"
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
      printf '    ok   %-28s pinned %-10s now %-10s\n' "$label" "$want" "$now"
    else
      printf '    ***  %-28s pinned %-10s now %-10s  WOULD REFUSE\n' "$label" "$want" "$now"; rc=1
    fi
  done
done

printf '\n=== how run-all.sh treats the committed out/ before capture.sh reads the baseline\n'
for rig in t305-openingbalance-accepting-side t327-closure-accepting-side; do
  R=".softhouse/capture/$rig/throwaway/run-all.sh"
  printf '    %s\n' "$R"
  grep -nE 'rm -rf|REFUSE|FORCE_OVERWRITE|guard-throwaway-isolation.sh|bash "\$DIR/capture.sh"' "$R" | sed 's/^/       /'
  printf '       committed files under out/: %s\n' "$(git ls-files ".softhouse/capture/$rig/throwaway/out/" | wc -l | tr -d ' ')"
done

printf '\n=== the 5 sites FU-T363-2 names\n'
git grep -ln 'STANDING-baseline.txt' -- '.softhouse/capture/t305-*/throwaway/*.sh' '.softhouse/capture/t327-*/throwaway/*.sh' | sed 's/^/    /'

echo
[ "$rc" -eq 0 ] && echo "NO PIN IS STALE" || echo "AT LEAST ONE PIN IS STALE -- the rigs would refuse on a STANDALONE capture.sh"
exit 0
