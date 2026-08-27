#!/bin/zsh
# T211 -- THE measurement the whole fix rests on.
#
# T202 named the fix ("background the child and wait") but did not verify it
# against zsh's real semantics.  Three things could each defeat it:
#   (a) zsh might defer a trap during `wait` exactly as it does for a foreground
#       child, in which case the rewrite buys nothing;
#   (b) `wait` might be restarted on EINTR, so the handler runs but the shell
#       goes straight back to waiting -- prompt handler, no prompt exit;
#   (c) the handler might run promptly and exit, but ORPHAN the child.
#
# T211_SHAPE = "fg" (today's shape) | "bg" (the fix's shape)
# T211_HMODE = "exit" (handler exits, as the fire's does)
#            | "return" (handler returns -- isolates (b) from (a))
set -uo pipefail
SHAPE=${T211_SHAPE:?set T211_SHAPE=fg|bg}
HMODE=${T211_HMODE:-exit}
CHILD_SECS=${T211_CHILD_SECS:-300}
PIDF=${T211_CHILDPID:-/tmp/t211-scratch/childpid-waittrap}
now() { date +%s.%N }
log() { print -r -- "[$(now)] $*" }

on_term() {
  log "HANDLER ENTERED (SIGTERM) -- shape=$SHAPE hmode=$HMODE"
  if [[ "$HMODE" == exit ]]; then
    log "HANDLER EXITING rc=143"
    exit 143
  fi
  log "HANDLER RETURNING (not exiting) -- watch whether \`wait\` resumes or returns"
}
trap on_term TERM

log "pid=$$ pgid=$(ps -o pgid= -p $$ | tr -d ' ') shape=$SHAPE hmode=$HMODE"
log "READY"

if [[ "$SHAPE" == fg ]]; then
  log "starting FOREGROUND child (/bin/sleep $CHILD_SECS) -- today's shape"
  /bin/sh -c "echo \$\$ > '$PIDF'; exec /bin/sleep $CHILD_SECS"
  log "FOREGROUND CHILD RETURNED rc=$?"
else
  log "starting BACKGROUND child + wait -- the fix's shape"
  /bin/sh -c "echo \$\$ > '$PIDF'; exec /bin/sleep $CHILD_SECS" &
  CPID=$!
  log "background child pid=\$!=$CPID"
  wait $CPID
  WRC=$?
  log "WAIT RETURNED rc=$WRC   (>128 means it was interrupted by the trapped signal)"
  if kill -0 $CPID 2>/dev/null; then
    log "child $CPID is STILL ALIVE after wait returned -- exiting here would ORPHAN it"
    kill -9 $CPID 2>/dev/null
  else
    log "child $CPID is gone"
  fi
fi

log "BODY COMPLETED NORMALLY"
exit 0
