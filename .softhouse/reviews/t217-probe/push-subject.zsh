#!/bin/zsh
# T217 SUBJECT -- release_lock() (and everything else in the trap block, incl.
# the T217 git_push_bounded / driver_tree it depends on) sourced VERBATIM from
# a given fire-program.sh via the same extraction contract T211 proved works
# on both pre- and post-fix bytes (LOCK_RELEASED=0 .. `trap release_lock EXIT`,
# content-bound, never a line number). The one substitution is PATH: `git` is
# shadowed by a fake that hangs on `push`, which is the whole point of the
# experiment -- it models a stalled remote without touching the network.
set -uo pipefail

HERE="${0:A:h}"
FRAG="${T217_FRAG:?T217_FRAG (dir holding traps.zsh) must be set}"
REPO="${T217_REPO:-/tmp/t217-scratch/repo}"
LOCK="$REPO/.softhouse/LOCK"
STAMP="T217-probe"
log() { print -r -- "[$(date +%s.%N)] $*" }

cd "$REPO" || { print -r -- "FATAL: no scratch repo at $REPO"; exit 1 }

source "$FRAG/traps.zsh"   # real LOCK_RELEASED / git_push_bounded / driver_tree / release_lock

log "READY"
log "LOCK present before release = $([[ -f $LOCK ]] && print YES || print NO)"
log "git resolves to: $(command -v git)"

T0=$(date +%s.%N)
release_lock
T1=$(date +%s.%N)
log "release_lock RETURNED after $(( T1 - T0 ))s"
log "LOCK present after release = $([[ -f $LOCK ]] && print YES || print NO)"
log "BODY COMPLETED NORMALLY"
exit 0
