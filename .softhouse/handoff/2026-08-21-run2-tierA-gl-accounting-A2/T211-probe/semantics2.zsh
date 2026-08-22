#!/bin/zsh
# T211 semantics, part 2 -- the questions part 1 left open, plus the one the
# whole fix rests on: does a trap run PROMPTLY while the shell sits in `wait`?
#
# Part 1 measured, under `/bin/zsh -lc`, no tty (the launchd shape):
#   - $pipestatus after `wait` = (0), ONE element  -> RC=${pipestatus[1]} dies
#   - `setopt monitor` is REFUSED ("can't change option: monitor")
#     -> no job control, so no per-job process group, so no `kill -- -PGID`
#   - an async child has SIGINT SIG_IGN'd; SIGTERM kills it
#   - caffeinate EXECS the utility in place; killing the pid zsh returns kills it
# Part 1 also mis-typed /usr/bin/cat (it is /bin/cat here), which degenerated the
# 3-stage pipeline -- so S4 is re-run below with binaries that exist.
set -uo pipefail
now() { date +%s.%N }

print -r -- "=== S4-clean  \$! and the child set for a REAL 3-stage background pipeline ==="
SELF=$$
/bin/sleep 3 | /bin/cat | /bin/cat &
BGP=$!
sleep 0.5
print -r -- "shell pid = $SELF   \$! = $BGP"
print -r -- "children of the shell:"
pgrep -P $SELF 2>/dev/null | while read -r c; do
  ps -o pid,ppid,pgid,comm -p "$c" 2>/dev/null | /usr/bin/sed -n '2p' | /usr/bin/sed 's/^/   /'
done
print -r -- "  -> \$! identifies which member?  (compare pids above)"
wait $BGP; print -r -- "wait \$! rc=$?"
print -r -- ""

print -r -- "=== S4b  '( a | b | c ) &' -- the subshell shape the fix uses ==="
( /bin/sleep 3 | /bin/cat | /bin/cat ) &
BGS=$!
sleep 0.5
print -r -- "\$! = $BGS"
ps -o pid,ppid,pgid,comm -p $BGS 2>/dev/null | /usr/bin/sed -n '2p' | /usr/bin/sed 's/^/   subshell: /'
print -r -- "   descendants of \$! (this is the tree a handler has to stop):"
FRONT=($BGS); ALL=()
while (( ${#FRONT} )); do
  P=${FRONT[1]}; shift FRONT; ALL+=($P)
  K=(${(f)"$(/usr/bin/pgrep -P $P 2>/dev/null)"})
  for k in $K; do [[ -n "$k" ]] && FRONT+=($k); done
done
for P in $ALL; do ps -o pid,ppid,pgid,comm -p $P 2>/dev/null | /usr/bin/sed -n '2p' | /usr/bin/sed 's/^/      /'; done
print -r -- "   pgid of every one of them vs shell pgid $(ps -o pgid= -p $SELF | tr -d ' ')"
wait $BGS; print -r -- "wait rc=$?"
print -r -- ""

print -r -- "=== S8  does 'wait \$!' on a subshell return the SUBSHELL's status? ==="
( exit 42 ) & ; wait $!; print -r -- "( exit 42 ) & ; wait \$!  -> rc=$?   (expect 42)"
print -r -- ""

print -r -- "=== S9  rc-through-a-file, the replacement for \${pipestatus[1]} ==="
RCF=/tmp/t211-scratch/rc-probe
# NOTE: as run, this block was preceded by a deliberately single-quoted variant
# that littered a file named literally `$RCF` in this directory.  It printed
# NOTHING, so removing it leaves semantics2.txt byte-identical to the run; it is
# gone only so the probe does not litter the repo when re-run.
rm -f $RCF
( { /bin/sh -c 'exit 37'; print -r -- $? > $RCF } | /bin/cat | /bin/cat ) &
wait $!
print -r -- "subshell wait rc = $?   (this is the LAST member's status, not the driver's)"
print -r -- "rc file contents = $(cat $RCF 2>/dev/null || print '<missing>')   (expect 37 -- the driver's real status)"
print -r -- ""
print -r -- "SEMANTICS2 DONE"
