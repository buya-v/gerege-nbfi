#!/usr/bin/env bash
# t553-battery.sh <repo> <old-guard> <new-guard>
# NEGATIVE CONTROL on REAL history: re-drives T493's/T550's whole published
# battery through BOTH guards and reports each verdict plus whether the two
# agree. Rows are T552 REVIEW §7's table, with the producer column T552's
# MINOR-1 found missing (GREEN-B is a CLOUD row) and MINOR-2's absent GREEN-A
# restored.
set -uo pipefail
REPO="$1"; OLD="$2"; NEW="$3"
cd "$REPO"
run() {  # run <guard> <producer> <ref> <now>
  local out rc
  out="$("$1" --producer "$2" --ref "$3" --now "$4" --no-fetch 2>&1)"; rc=$?
  printf '%s|%s' "$rc" "$(printf '%s\n' "$out" | grep -oE 'AXIS [0-9] [a-z. ]+: *[^ ]+ *(consecutive|since)?' | tr '\n' ' ')"
}
row() {  # row <label> <producer> <ref> <now>
  local o n
  o="$(run "$OLD" "$2" "$3" "$4")"; n="$(run "$NEW" "$2" "$3" "$4")"
  local orc="${o%%|*}" nrc="${n%%|*}"
  local agree="AGREE"; [ "$orc" = "$nrc" ] || agree="**DIFFER**"
  printf '%-14s %-6s %-24s old_exit=%s new_exit=%s  %s\n' "$1" "$2" "$4" "$orc" "$nrc" "$agree"
}
echo "=== T493/T550 battery, ref 6aa31e5e, shipped defaults — old guard vs T553 guard"
row RED-1       local 6aa31e5e 2026-08-27T06:00:00Z
row RED-2       local 6aa31e5e 2026-09-01T00:00:00Z
row RED-3       local 6aa31e5e 2026-09-05T12:17:56Z
row GREEN-A     local 6aa31e5e 2026-08-29T12:00:00Z
row GREEN-B     cloud 6aa31e5e 2026-09-04T13:40:00Z
row GREEN-B-loc local 6aa31e5e 2026-09-04T13:40:00Z
row GREEN-C     local 6aa31e5e 2026-09-03T11:30:00Z
row GREEN-mine  local 6aa31e5e 2026-08-28T23:59:00Z
row GREEN-cloud cloud 6aa31e5e 2026-09-05T12:17:56Z
row ANY-trap    any   6aa31e5e 2026-09-05T12:17:56Z
row MAX-26      local 6aa31e5e 2026-08-27T14:59:00Z
row RED-4-T541  local 6aa31e5e 2026-09-02T23:59:00Z
echo
echo "=== live history, ref origin/main, hourly-ish spot instants"
for d in 2026-08-20 2026-08-24 2026-08-28 2026-09-01 2026-09-03 2026-09-05; do
  row "live-$d" local origin/main "${d}T12:00:00Z"
  row "live-$d" cloud origin/main "${d}T12:00:00Z"
done
