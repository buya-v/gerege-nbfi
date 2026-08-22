#!/bin/zsh
# T211 SUBJECT -- the fire wrapper reduced to the parts under test, with the
# REAL bytes of `release_lock` / `on_signal` / the trap table / `run_driver`
# sourced verbatim from a given fire-program.sh (see extract.py).  Nothing here
# paraphrases the subject; the harness only supplies the surroundings the real
# script would have supplied.
#
# The one substitution is CLAUDE_BIN -> fake-claude.zsh, which is the whole
# point of the experiment: it models the property that makes the defect bite,
# that the foreground child runs for HOURS.  /usr/bin/caffeinate, the tee|jq
# digest pipeline and the trap table are the real ones.
set -uo pipefail

HERE="${0:A:h}"
FRAG="${T211_FRAG:?T211_FRAG (dir holding traps.zsh + driver.zsh) must be set}"
REPO="${T211_REPO:-/tmp/t211-scratch/repo}"
LOG_DIR="${T211_LOGDIR:-/tmp/t211-scratch/logs}"
LOCK="$REPO/.softhouse/LOCK"
STAMP="T211"
FIRE_START_EPOCH=$(date +%s)
CHAIN_N=0
CHAIN_MAX=1
FINERACT_SRC="${FINERACT_SRC:-/Users/buv/fineract}"
CLAUDE_BIN="$HERE/fake-claude.zsh"
PROMPT="t211 probe prompt"
RC=0

mkdir -p "$LOG_DIR"
# sub-second clock: the whole finding is a LATENCY, and [HH:MM:SS] cannot show it
log() { print -r -- "[$(date +%s.%N)] $*" }

cd "$REPO" || { print -r -- "FATAL: no scratch repo at $REPO"; exit 1 }

source "$FRAG/traps.zsh"          # real LOCK_RELEASED / release_lock / on_signal / trap table
source "$FRAG/driver.zsh"         # real run_driver

log "SUBJECT pid=$$ pgid=$(ps -o pgid= -p $$ | tr -d ' ') sid=$(ps -o sess= -p $$ | tr -d ' ')"
log "LOCK present at start = $([[ -f $LOCK ]] && print YES || print NO)"
log "READY"

run_driver

log "run_driver RETURNED rc=$RC"
log "BODY COMPLETED NORMALLY"
exit 0
