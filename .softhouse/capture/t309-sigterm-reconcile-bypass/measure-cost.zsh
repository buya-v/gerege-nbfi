#!/bin/zsh
# T309 — WHAT DOES THE SIGNAL-PATH RECONCILE ACTUALLY COST?
#
# The brief requires this measured, not estimated, because the reconcile now sits inside
# launchd's SIGTERM->SIGKILL grace.
#
# THE A/B IS ON IDENTICAL BYTES. Comparing HEAD to main would confound two changes that
# landed together — wiring the reconcile in (which costs time) and replacing
# stop_driver's flat 5s sleep with a poll (which gives time back). So the control is the
# SAME post-fix wrapper with SIGNAL_RECONCILE_MIN_SECS=999, which makes it take its own
# documented SKIP branch. The only difference between the two columns is whether the
# reconcile ran.
#
# The third column is the pre-T309 wrapper, for the absolute number that matters to
# launchd: is the handler still comfortably inside the grace?
set -uo pipefail
HERE="${0:A:h}"
TRIALS="${TRIALS:-5}"

sample() {                     # sample <label> <args...>
  local label=$1; shift
  local -a s; s=()
  local t v
  for t in {1..$TRIALS}; do
    v=$(zsh "$HERE/drive-sigterm.zsh" "$@" 2>&1 | /usr/bin/sed -n 's/^ELAPSED_SECONDS=//p' | tail -1)
    s+=("$v")
  done
  print -r -- "$label"
  print -r -- "  samples: ${s[*]}"
  print -r -- "  $(/usr/bin/python3 -c "
import sys
v=[float(x) for x in '${s[*]}'.split()]
v.sort()
print('n=%d  min=%.2f  median=%.2f  max=%.2f  mean=%.2f' % (len(v), v[0], v[len(v)//2], v[-1], sum(v)/len(v)))
")"
  print -r -- ""
}

print -r -- "T309 — SIGTERM to wrapper exit, $TRIALS trials each, 8 in_progress tasks planted"
print -r -- "launchd's SIGTERM->SIGKILL grace is ~20s (plist sets no ExitTimeOut)"
print -r -- "=============================================================================="
sample "A. POST-FIX bytes, reconcile SKIPPED (SIGNAL_RECONCILE_MIN_SECS=999) — control" --rev HEAD --no-reconcile
sample "B. POST-FIX bytes, reconcile RUNS                                   — subject"  --rev HEAD
sample "C. PRE-T309 bytes (main)                                            — baseline" --rev main
print -r -- "READ: B minus A is the cost of the reconcile itself, on identical bytes."
print -r -- "      B minus C is what a fire's stop actually got longer or shorter by."
print -r -- "DONE"
