#!/bin/zsh
# T346 / P-22 — "a guard you have not seen fail is not a guard".
# `drive-wrapper-vs-skill.zsh` has printed `0 disagreements` on every run this program has
# recorded, including every run made while the fail-opens were live in the tree. A counter
# that has never moved may not be counting. This mutates ONE arm at a time in a COPY of the
# shipped wrapper and checks the counter MOVES. If it does not, the driver is decorative.
# usage: t346-mutate-driver.zsh <path-to-fire-program.sh>
emulate -L zsh
set -uo pipefail
FP="$1"
DRIVER="${0:A:h}/../../../capture/t279-lock-partition/drive-wrapper-vs-skill.zsh"
DRIVER="${DRIVER:A}"
[[ -r "$DRIVER" ]] || { print -r -- "driver not found at $DRIVER"; exit 2; }
W="$(mktemp -d)"; trap "rm -rf $W" EXIT

run_driver() {  # $1 wrapper path -> prints the disagreement count
  zsh "$DRIVER" "$1" 2>&1 | sed -n 's/^disagreements with SKILL.md STEP 0 as modelled in rules.py: //p'
}

print -r -- "driver: $DRIVER"
print -r -- "wrapper under test: $FP"
print -r -- ""

cp "$FP" "$W/pristine.sh"
base="$(run_driver "$W/pristine.sh")"
print -r -- "M00 pristine (no mutation)                          disagreements=$base   [expect 0]"

mutate() {  # $1 id  $2 sed-expr  $3 description
  cp "$FP" "$W/m.sh"
  sed -i '' "$2" "$W/m.sh" || { print -r -- "$1 SED FAILED"; return; }
  if cmp -s "$FP" "$W/m.sh"; then
    print -r -- "$1 *** MUTATION DID NOT APPLY -- result is void ($3)"
    return
  fi
  local d="$(run_driver "$W/m.sh")"
  local want_move="${4:-yes}" mark
  if [[ "$want_move" == no ]]; then
    [[ "$d" == "0" ]] && mark="ok  correctly unmoved (control)" || mark="*** CONTROL FAILED"
  else
    [[ "$d" == "0" || -z "$d" ]] && mark="*** DRIVER BLIND" || mark="ok  driver CAUGHT it"
  fi
  print -r -- "$1 $3"
  print -r -- "      disagreements=${d:-<no count printed>}   $mark"
}

# arm 1: invert the released_at test
mutate M01 's/\[\[ -n "\$rel" \]\]                   && { print -r -- FREE-released/[[ -z "$rel" ]]                   \&\& { print -r -- FREE-released/' \
  "arm 1 inverted: -n rel -> -z rel"
# arm 2: delete the dead-pid arm entirely
mutate M02 '/print -r -- TAKE-dead-pid/d' \
  "arm 2 deleted: dead holder is never reclaimed"
# arm 3: flip the ceiling comparison
mutate M03 's/(( sage >= LOCK_CEILING_SECS ))/(( sage < LOCK_CEILING_SECS ))/' \
  "arm 3 comparison flipped: >= ceiling -> < ceiling"
# arm 4: flip the freshness comparison
mutate M04 's/(( tage < LOCK_MAX_AGE_SECS ))/(( tage <= 0 ))/' \
  "arm 4 freshness condition gutted"
# arm 6: change the default verdict to a take
mutate M05 's/print -r -- HELD-default  /print -r -- TAKE-both-stale/' \
  "arm 6 default flipped from HELD to TAKE"
# a no-op mutation: a comment change only. The driver MUST still say 0.
mutate M06 's/^# T279 . `lock_pid_state`/# T279 MUTATED COMMENT `lock_pid_state`/' \
  "control: comment-only change, driver must still say 0" no

# ---------------------------------------------------------------------------------
# THE HALF THE DRIVER CANNOT SEE. T342's F4 claims the 192-state driver is blind to the
# signal READERS because it SUPPLIES the signals as arguments. That is an argument until
# it is measured. These mutations wreck a reader as badly as it can be wrecked -- a
# maximal fail-open, a live lock always reported released -- and the driver must be
# expected to notice. If it still prints 0, T342's F4 is CONFIRMED as a measurement.
print -r -- ""
print -r -- "--- reader mutations: the driver supplies these signals, so it should be blind ---"
mutate M07 's|^  v="\$(_lock_json_field released_at str)" .. return 0|  print -r -- "2026-01-01T00:00:00Z"; return 0|' \
  "lock_released_at gutted: ALWAYS reports released (maximal fail-open)" yes
mutate M08 's|^  host="\$(_lock_json_field host str)" .*$|  host="$(hostname -s)"|' \
  "lock_pid_state host read replaced by a constant" yes
