#!/usr/bin/env bash
# t553-drive.sh <attack-repo> <guard-path> [extra guard args...]
# Drives the guard against every planted T553 attack branch and the two negative
# controls, at the instant T552 published (--now 2026-09-04T23:00:00Z), printing
# the three axis lines, the verdict and the exit code for each.
set -uo pipefail
REPO="$1"; GUARD="$2"; shift 2
cd "$REPO"
for BR in atk-unenumerated atk-t541 atk-mine-i atk-mine-j atk-mine-k atk-mine-k40 atk-legit atk-legit-boiler; do
  out="$("$GUARD" --producer local --ref "$BR" --now 2026-09-04T23:00:00Z --no-fetch "$@" 2>&1)"
  rc=$?
  printf '=== %-18s exit=%s\n' "$BR" "$rc"
  printf '%s\n' "$out" | grep -E 'AXIS 1|AXIS 3|VERDICT|vetoed|REFUSE' | sed 's/^/    /'
done
