#!/bin/zsh
# T202 T-c SUBJECT (PRE-FIX): the real release_lock + the real
# `trap release_lock EXIT INT TERM` bytes (sed -n '122,132p' of fire-program.sh),
# wrapped in a body that models the fire: a long-running FOREGROUND child (the
# driver) inside the chain loop. Every 0.2s it reports whether the lock it
# claims to hold still exists.
set -uo pipefail
REPO=$1
LOCK="$REPO/.softhouse/LOCK"
STAMP=TC-PRE
log() { print -r -- "[$(date +%H:%M:%S.$(( ${RANDOM} % 10 )))] $*" }

cd "$REPO" || exit 1
source /tmp/t202/prefix-trap.zsh

print -r -- "SUBJECT pid=$$ pgid=$(ps -o pgid= -p $$ | tr -d ' ')"
print -r -- "READY"

# model the chain loop: a foreground child (the driver) then guard work
for i in {1..40}; do
  /bin/sleep 0.2                       # <- foreground child, as the driver is
  print -r -- "TICK $i lock_present=$([[ -f $LOCK ]] && print YES || print NO)"
done
print -r -- "BODY COMPLETED NORMALLY"
exit 0
