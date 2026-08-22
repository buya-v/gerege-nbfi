#!/bin/zsh
# T211 -- prove the exact `driver_tree` / `stop_driver` idioms BEFORE they go
# into the live wrapper.  Measured facts they are built on (semantics.txt,
# semantics2.txt, waittrap-matrix.txt):
#   - `setopt monitor` is REFUSED in this shape, so every descendant shares the
#     WRAPPER's process group -> `kill -- -$$` would signal the wrapper itself
#   - `$!` of `( a|b|c ) &` is the SUBSHELL, the parent of all three members
#   - SIGINT is SIG_IGN in an async child; SIGTERM is not
#   - background+wait+exit still ORPHANS the child, so a kill is mandatory
set -uo pipefail
now() { date +%s.%N }
log() { print -r -- "[$(now)] $*" }

# --- the idiom under test, byte-for-byte what will be pasted into the wrapper ---
driver_tree() {
  local root=$1 line pid ppid depth added
  local -a lines f
  DRIVER_TREE=()
  [[ "$root" == <1-> ]] || return 1
  local snap; snap=$(/bin/ps -Ao pid=,ppid= 2>/dev/null) || return 1
  lines=(${(f)snap})
  (( ${#lines} > 1 )) || return 1
  DRIVER_TREE=("$root")
  for depth in 1 2 3 4 5 6; do
    added=0
    for line in $lines; do
      f=(${=line})
      pid=$f[1]; ppid=$f[2]
      [[ "$pid" == <1-> && "$ppid" == <1-> ]] || continue
      (( ${DRIVER_TREE[(I)$ppid]} )) || continue
      (( ${DRIVER_TREE[(I)$pid]}  )) && continue
      DRIVER_TREE+=("$pid"); added=1
    done
    (( added )) || break
  done
  return 0
}

log "shell pid=$$ pgid=$(ps -o pgid= -p $$ | tr -d ' ')"

# build the SAME shape the fix builds: ( { long-child ; rc } | tee | jq ) &
RC=/tmp/t211-scratch/treewalk-rc
rm -f $RC
( { /usr/bin/caffeinate -i -m -s /bin/sleep 120; print -r -- $? > $RC } \
  | /usr/bin/tee /tmp/t211-scratch/treewalk-raw \
  | /bin/cat ) &
JOB=$!
sleep 1.0
log "\$! (the driver job) = $JOB"

typeset -ga DRIVER_TREE
if driver_tree $JOB; then
  log "driver_tree returned ${#DRIVER_TREE} pid(s): ${DRIVER_TREE[*]}"
  for p in $DRIVER_TREE; do
    ps -o pid,ppid,pgid,comm -p $p 2>/dev/null | /usr/bin/sed -n '2p' | /usr/bin/sed 's/^/   /'
  done
else
  log "driver_tree FAILED to build a tree (ps did not answer) -- fail-closed path"
fi

# is the long-running child (the `claude` stand-in) actually IN the tree?
SLEEPPID=$(pgrep -f 'sleep 120' | head -1)
log "the long child (/bin/sleep 120) is pid $SLEEPPID"
if (( ${DRIVER_TREE[(I)$SLEEPPID]} )); then
  log "  -> IN the tree at index ${DRIVER_TREE[(I)$SLEEPPID]}  (a single kill on \$! would have MISSED it)"
else
  log "  -> NOT in the tree -- the walk is WRONG, do not ship it"
fi

log "TERMing the whole tree"
kill -TERM ${DRIVER_TREE[@]} 2>/dev/null
/bin/sleep 1.5
STILL=()
for p in $DRIVER_TREE; do kill -0 $p 2>/dev/null && STILL+=($p); done
log "still present after SIGTERM + 1.5s: ${#STILL} -> ${STILL[*]:-none}"
for p in $STILL; do
  ST=$(ps -o stat= -p $p 2>/dev/null)
  log "   pid $p  ps stat='${ST:-<gone>}'   $([[ $ST == Z* ]] && print '(ZOMBIE - dead, just unreaped)' || print '(genuinely alive)')"
done
kill -KILL ${DRIVER_TREE[@]} 2>/dev/null
wait 2>/dev/null
log "rc file contents = $(cat $RC 2>/dev/null || print '<missing - the child was killed before it could write one>')"
pgrep -f 'caffeinate -i -m -s /bin/sleep 120' >/dev/null 2>&1 \
  && { log "STRAY caffeinate survived"; pkill -f 'caffeinate -i -m -s /bin/sleep 120' } \
  || log "no stray caffeinate"
pgrep -f '/bin/sleep 120' >/dev/null 2>&1 \
  && { log "STRAY sleep survived -- the tree kill MISSED it"; pkill -f '/bin/sleep 120' } \
  || log "no stray sleep -- the tree kill reached the long child"
log "TREEWALK DONE"
