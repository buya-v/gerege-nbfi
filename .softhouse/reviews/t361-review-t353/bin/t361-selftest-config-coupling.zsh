#!/bin/zsh
# T361 — CAN THE NEW FATAL CONTROL BRICK THE FIRE FOR A REASON THAT IS NOT A DEFECT?
#
# The brief's item 5 asks this of the preflight gates. The same question has to be asked of
# the SELF-TEST, because it is fatal too and because it hard-codes a fixture (`100 h ago`)
# against a threshold that is CONFIGURABLE from the environment:
#
#   LOCK_CEILING_SECS="${LOCK_CEILING_SECS:-86400}"   fire-program.sh:25
#   _OLD="$(_epoch_iso8601 $(( _NOW_E - 360000 )))"   # 100 h, HARD-CODED in the self-test
#
# If an operator raises the ceiling past 100 h, groups C stop being over the ceiling, the
# self-test reports FAIL-SHUT and — because it is wired fatally — the fire REFUSES TO START.
# A threshold change would then look like a reader regression.
#
# FAIL DIRECTION: SHUT (liveness). It cannot make a lock takeable; it can stop every fire.
emulate -L zsh
set -uo pipefail
FP="${1:?usage: t361-selftest-config-coupling.zsh <fire-program.sh>}"

print -r -- "the two coupled values, quoted by extraction from the shipped file:"
grep -n 'LOCK_CEILING_SECS=' "$FP" | head -3
grep -n '_NOW_E - 360000' "$FP" | head -3
print -r -- ""

printf '%-28s %-42s %s\n' 'LOCK_CEILING_SECS' 'self-test tail' 'rc'
printf '%-28s %-42s %s\n' '---' '---' '---'
typeset -i bad=0
for C in '<unset, default 86400>' 86400 172800 360000 359999 360001 604800; do
  out=""; rc=0
  if [[ "$C" == '<unset'* ]]; then
    out="$(zsh "$FP" --self-test-lock-readers 2>&1)"; rc=$?
  else
    out="$(LOCK_CEILING_SECS=$C zsh "$FP" --self-test-lock-readers 2>&1)"; rc=$?
  fi
  tail_line="${out##*$'\n'}"
  printf '%-28s %-42s %d\n' "$C" "$tail_line" $rc
  (( rc != 0 )) && bad+=1
done
print -r -- ""
print -r -- "ROWS WHERE THE FIRE WOULD REFUSE: $bad"
print -r -- "Any non-zero rc above is a configuration value — not a code defect — turning the"
print -r -- "wired self-test into a hard stop for the whole fire (it exits 2 at the preflight)."
