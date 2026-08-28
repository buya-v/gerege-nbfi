#!/bin/zsh
# T368 — drive BOTH vintages of the lock readers over the LOCK BODY THAT EXISTS RIGHT NOW,
# to answer the only question that matters operationally: does T365's C1 change the verdict
# on the lock the fire is actually holding?
#
# Readers are EXTRACTED from the shipped file by `sed` (P-46), never retyped, and the
# extraction ABORTS if it does not yield callable functions — an empty extraction that
# "passes" is P-22's shape.
#
# Usage: zsh t368-live-lock.zsh <path-to-fire-program.sh> <path-to-a-LOCK-body>
emulate -L zsh
set -uo pipefail

SRC="${1:?usage: t368-live-lock.zsh <fire-program.sh> <LOCK body>}"
BODY="${2:?usage: t368-live-lock.zsh <fire-program.sh> <LOCK body>}"
W="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/t368-live.XXXXXX")" || exit 3
[[ -n "$W" && -d "$W" && "$W" != "/" ]] || exit 3
trap 'rm -rf "$W"' EXIT

{
  for f in lock_decide _lock_json_fields _lock_json_field _iso8601_epoch _epoch_iso8601 \
           lock_pid_state lock_released_at lock_started_age; do
    sed -n "/^${f}() {/,/^}$/p" "$SRC"
  done
} > "$W/r.zsh"
for f in lock_decide _lock_json_field lock_pid_state lock_released_at lock_started_age; do
  grep -q "^${f}() {" "$W/r.zsh" || { print -u2 "ABORT: extraction of $f failed"; exit 3; }
done

# Thresholds come from the SOURCE, never typed here (P-80, and the reason T361's own
# condition-proof first reported a false FAIL-SHUT).
eval "$(grep -E '^LOCK_[A-Z_]+=' "$SRC")"
: ${LOCK_MAX_AGE_SECS:=21600} ${LOCK_CEILING_SECS:=86400}

LOCK="$W/LOCK"
cp "$BODY" "$LOCK"
source "$W/r.zsh"
whence -w lock_released_at | grep -q function || { print -u2 "ABORT: readers not callable"; exit 3; }

rel="$(lock_released_at)"; sage="$(lock_started_age)"; pst="$(lock_pid_state)"
printf 'src=%s\n  sha256=%s\n  released_at=%s started_age=%s pid_state=%s\n  VERDICT=%s\n' \
  "$SRC" "$(shasum -a 256 "$SRC" | awk '{print $1}')" \
  "${rel:-<empty>}" "${sage:-<unreadable>}" "$pst" \
  "$(lock_decide 1 "$rel" "$sage" 60 "$pst")"
