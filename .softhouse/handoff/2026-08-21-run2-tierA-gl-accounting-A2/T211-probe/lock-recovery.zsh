#!/bin/zsh
# T211 -- REGRESSION GUARD for T202's lock_holder_is_dead() recovery.
#
# T211 must not break it, so it is re-driven here against the POST-FIX bytes,
# with the same fail-CLOSED polarity T202 wrote it with.  This is a REFUSAL
# test, so it is judged by WHAT IT SAYS and WHICH POPULATION SURVIVES, never by
# an exit code (P-62): every one of these cases exits 0 or 1 for reasons that
# have nothing to do with whether the takeover was correct.
#
# Cases, and the answer each MUST give:
#   1 dead pid, this host        -> DEAD    (takeover NOW, whatever the age)
#   2 live pid, this host        -> ALIVE   (never take a live lock)
#   3 our own pid                -> ALIVE   (never judge ourselves)
#   4 a DIFFERENT host           -> ALIVE   (never judge another machine)
#   5 junk pid                   -> ALIVE   (unparseable => assume alive)
#   6 missing "pid" key          -> ALIVE
#   7 lock file absent/unreadable-> ALIVE
set -uo pipefail
SRC=${T211_SUBJECT:?set T211_SUBJECT=<fire-program.sh>}
WORK=/tmp/t211-scratch/lockrec
rm -rf $WORK; mkdir -p $WORK
LOCK=$WORK/LOCK
LOCK_MAX_AGE_SECS=21600

print -r -- "subject bytes: $SRC"
print -r -- "extracting lock_holder_is_dead() verbatim..."
/usr/bin/python3 - "$SRC" "$WORK/fn.zsh" <<'PY'
import sys
src, out = sys.argv[1:3]
lines = open(src, encoding="utf-8").read().splitlines(keepends=True)
a = next(i for i, l in enumerate(lines) if l.startswith("lock_holder_is_dead() {"))
b = next(i for i in range(a, len(lines)) if lines[i].rstrip() == "}")
open(out, "w", encoding="utf-8").write("".join(lines[a:b + 1]))
print("  lines %d-%d (%d lines)" % (a + 1, b + 1, b - a + 1))
PY
source "$WORK/fn.zsh"

# a pid that is certainly dead: spawn and reap one
/bin/sh -c 'exit 0' & DEADPID=$!; wait $DEADPID 2>/dev/null
# a pid that is certainly alive for the duration
/bin/sleep 30 & LIVEPID=$!

mk() { print -r -- "$1" > "$LOCK" }
HOST=$(hostname -s)

check() {
  local label=$1 expect=$2
  local got
  if lock_holder_is_dead; then got=DEAD; else got=ALIVE; fi
  if [[ "$got" == "$expect" ]]; then
    print -r -- "  PASS  $label -> $got (expected $expect)"
  else
    print -r -- "  FAIL  $label -> $got (expected $expect)   <-- T202's recovery is BROKEN"
    FAILED=1
  fi
}
FAILED=0

print -r -- ""
print -r -- "host=$HOST  self=$$  deadpid=$DEADPID  livepid=$LIVEPID"
print -r -- ""

mk "{\"holder\":\"local-launchd\",\"host\": \"$HOST\",\"pid\": $DEADPID, \"log\":\"x\"}"
check "1 dead pid on this host          " DEAD

mk "{\"holder\":\"local-launchd\",\"host\": \"$HOST\",\"pid\": $LIVEPID, \"log\":\"x\"}"
check "2 LIVE pid on this host          " ALIVE

mk "{\"holder\":\"local-launchd\",\"host\": \"$HOST\",\"pid\": $$, \"log\":\"x\"}"
check "3 our OWN pid                    " ALIVE

mk "{\"holder\":\"local-launchd\",\"host\": \"some-other-mac\",\"pid\": $DEADPID, \"log\":\"x\"}"
check "4 dead pid on a DIFFERENT host   " ALIVE

mk "{\"holder\":\"local-launchd\",\"host\": \"$HOST\",\"pid\": notanumber, \"log\":\"x\"}"
check "5 junk pid                       " ALIVE

mk "{\"holder\":\"local-launchd\",\"host\": \"$HOST\", \"log\":\"x\"}"
check "6 no pid key                     " ALIVE

rm -f "$LOCK"
check "7 lock file absent               " ALIVE

kill -9 $LIVEPID 2>/dev/null
print -r -- ""
if (( FAILED )); then
  print -r -- "LOCK-RECOVERY REGRESSION: FAILED — T211 broke T202's lock_holder_is_dead()"
else
  print -r -- "LOCK-RECOVERY REGRESSION: all 7 cases correct — T202's recovery is INTACT under T211"
fi
print -r -- "LOCKREC DONE"
