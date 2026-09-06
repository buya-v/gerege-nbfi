#!/usr/bin/env bash
# t553-capture.sh <attack-repo> <old-guard> <new-guard>
# Regenerates t553-attacks-before-after.txt in full: every attack driven through
# the guard BEFORE T553's fix and again AFTER it, plus the floor sweep that shows
# raising the floor was never the lever, plus the fail-closed prologue drives.
set -uo pipefail
REPO="$1"; OLD="$2"; NEW="$3"
HERE="$(cd "$(dirname "$0")" && pwd)"
NOW=2026-09-04T23:00:00Z

drive() {  # drive <guard> <ref> [extra...]
  local g="$1" r="$2"; shift 2
  ( cd "$REPO" && "$g" --producer local --ref "$r" --now "$NOW" --no-fetch "$@" 2>&1 )
  return $?
}
row() {  # row <guard> <ref> [extra...]
  local out rc
  out="$(drive "$@")"; rc=$?
  printf '$ no-op-fire-streak.sh --producer local --ref %s --now %s --no-fetch %s\n' "$2" "$NOW" "${*:3}"
  printf '%s\n' "$out" | grep -E 'AXIS 1|AXIS 3|VERDICT' | sed 's/^ */  /'
  printf '  exit=%s\n\n' "$rc"
}

echo "# T553 — every attack driven BEFORE the fix and AFTER it"
echo "# rig: t553-plant-attacks.sh (independent re-plant of T552's shapes; T552's own"
echo "#      evidence/ worktree no longer exists on this machine)"
echo "# all fires: 8 consecutive no-op fires off 5d7ef306, +0800, 3h apart, graded at --now $NOW"
echo
for G in BEFORE AFTER; do
  [ "$G" = BEFORE ] && GUARD="$OLD" || GUARD="$NEW"
  echo "==================== $G (guard = $GUARD) ===================="
  for R in atk-unenumerated atk-t541 atk-mine-i atk-mine-j atk-mine-k atk-mine-k40 \
           atk-mine-knum atk-mine-min atk-legit atk-legit-boiler; do
    row "$GUARD" "$R"
  done
  echo "-- floor sweep: is the floor the lever? --"
  row "$GUARD" atk-mine-k   --min-subst-lines 2
  row "$GUARD" atk-mine-k   --min-subst-lines 20
  row "$GUARD" atk-mine-k40 --min-subst-lines 40
done
