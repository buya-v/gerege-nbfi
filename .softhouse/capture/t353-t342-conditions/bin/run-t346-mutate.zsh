#!/bin/zsh
# T353 — run T346's mutation test of the 192-state driver UNEDITED, by staging it at the
# relative depth it expects (`${0:A:h}/../../../capture/t279-lock-partition/…`) instead of
# rewriting its path. Then add the two reader mutations T346 could not re-run here, because
# T353 changed the line M08 targets: `lock_pid_state` no longer reads `host` in its own fork.
#
# WHAT IS BEING MEASURED, in two halves:
#   1. the driver MOVES when an ARM is mutated -> it is a live control, not decoration;
#   2. the driver DOES NOT MOVE when a READER is gutted into a maximal fail-open -> it is
#      provably blind to the code that derives its inputs, which is why the reader self-test
#      inside the wrapper had to exist. T342's F4 as a measurement rather than an argument.
#
# usage: run-t346-mutate.zsh <path-to-fire-program.sh>
emulate -L zsh
set -uo pipefail
FP="${1:?usage: run-t346-mutate.zsh <fire-program.sh>}"; FP="${FP:A}"
HERE="${0:A:h}"
CAPTURE="${HERE:h:h}"                     # .../.softhouse/capture
DRIVER="$CAPTURE/t279-lock-partition/drive-wrapper-vs-skill.zsh"
[[ -r "$DRIVER" ]] || { print -r -- "driver not found at $DRIVER"; exit 2; }

S="$(mktemp -d "${TMPDIR:-/tmp}/t353mut.XXXXXX")"; trap "rm -rf $S" EXIT
mkdir -p "$S/reviews/staged/bin"
ln -s "$CAPTURE" "$S/capture"
cp "$HERE/copied-from-t346/t346-mutate-driver.zsh" "$S/reviews/staged/bin/"

print -r -- "=== PART 1 — T346's mutate-driver, byte-for-byte as it was written"
print -r -- "    (M08 targets a line T353 replaced; it is EXPECTED to report VOID, and a"
print -r -- "     replacement measurement is in part 2.)"
print -r -- ""
zsh "$S/reviews/staged/bin/t346-mutate-driver.zsh" "$FP"

print -r -- ""
print -r -- "=== PART 2 — the reader mutations restated against T353's code."
print -r -- "    Expectation: BOTH still print 0. The 192-state driver SUPPLIES the five"
print -r -- "    signals, so no reader mutation can reach it. If either moves, the driver has"
print -r -- "    grown reader coverage and the self-test's justification needs re-reading."
run_driver() { zsh "$DRIVER" "$1" 2>&1 | sed -n 's/^disagreements with SKILL.md STEP 0 as modelled in rules.py: //p' }
sel() { zsh "$1" --self-test-lock-readers >/dev/null 2>&1; print -r -- $? }

m() {  # $1 id  $2 sed  $3 desc
  cp "$FP" "$S/m.sh"
  sed -i '' "$2" "$S/m.sh"
  if cmp -s "$FP" "$S/m.sh"; then print -r -- "  $1 *** DID NOT APPLY -- VOID ($3)"; return; fi
  local d="$(run_driver "$S/m.sh")" r="$(sel "$S/m.sh")"
  local dmark rmark
  [[ "$d" == "0" ]] && dmark="DRIVER BLIND (expected)" || dmark="*** driver moved -- re-read the claim"
  (( r != 0 )) && rmark="self-test CAUGHT it (rc=$r)" || rmark="*** SELF-TEST BLIND TOO -- that is a hole"
  printf '  %-6s driver_disagreements=%-6s %-28s %s\n' "$1" "${d:-<none>}" "$dmark" "$rmark"
  printf '         %s\n' "$3"
}

m M07b 's#^  v="\$(_lock_json_field released_at str)" .. return 0#  print -r -- "2026-01-01T00:00:00Z"; return 0#' \
  "lock_released_at gutted: ALWAYS reports released (maximal fail-open)"
m M08b 's#^  snap="\$(_lock_json_fields host:str pid:int)" .*#  snap="=$(hostname -s)"$'"'"'\\n'"'"'"=1"#' \
  "lock_pid_state host/pid replaced by constants (T353 restatement of M08)"
m M09b '/^  _iso8601_epoch "\$v" >\/dev\/null || return 0$/d' \
  "the T353 shape gate removed from lock_released_at (= the reviewed T342 behaviour)"
