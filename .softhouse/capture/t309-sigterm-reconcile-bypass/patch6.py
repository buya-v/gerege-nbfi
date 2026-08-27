import io
p = ".softhouse/bin/fire-program.sh"
s = io.open(p, encoding="utf-8").read()

old = '''reconcile_bounded() {
  local budget=$1; shift
  local ticks=$(( budget * 10 ))
  RECON_VERDICT="not attempted"
  ( reconcile_tasks_json "$@" ) &
  local job=$! waited=0
'''
assert s.count(old) == 1
new = '''reconcile_bounded() {
  local budget=$1; shift
  local ticks=$(( budget * 10 ))
  RECON_VERDICT="not attempted"
  # DEFINED YET? `on_signal` is armed by `trap` roughly 370 lines before
  # `reconcile_tasks_json` is defined, and zsh creates a function body only when the
  # definition is REACHED. A signal delivered inside that window would otherwise produce
  # a bare "command not found" in the fire log and a silent non-repair. The traps are
  # NOT moved below the definitions instead, because that would widen the window in which
  # the LOCK is on disk with no EXIT trap behind it, which is the worse trade.
  if ! typeset -f reconcile_tasks_json >/dev/null 2>&1; then
    RECON_VERDICT="FAILED — the signal arrived before reconcile_tasks_json was defined"
    log "ERROR: signal-path reconcile is not possible — $RECON_VERDICT. tasks.json is UNREPAIRED."
    return 1
  fi
  # RECON_VERDICT is set by reconcile_tasks_json, which has to run in a SUBSHELL to be
  # backgroundable — so its assignment cannot reach this scope. Hand it back through a
  # file. If the job is killed at the deadline the file is absent and the FAILED verdict
  # set below stands: an unread verdict is never spelled like a clean one.
  local vf="$LOG_DIR/fire-$STAMP.recon-verdict"
  rm -f "$vf"
  ( reconcile_tasks_json "$@"; print -r -- "$RECON_VERDICT" > "$vf" ) &
  local job=$! waited=0
'''
s = s.replace(old, new)

old2 = '''  wait "$job"
  return $?
}

# Commit whatever the signal-path reconcile changed.'''
assert s.count(old2) == 1
new2 = '''  wait "$job"
  local rc=$?
  if [[ -r "$vf" ]]; then
    RECON_VERDICT="$(<"$vf")"
    rm -f "$vf"
  else
    RECON_VERDICT="UNKNOWN — the reconcile subshell left no verdict; treat tasks.json as UNVERIFIED"
  fi
  log "signal-path reconcile verdict: $RECON_VERDICT"
  return $rc
}

# Commit whatever the signal-path reconcile changed.'''
s = s.replace(old2, new2)

old3 = '''    RECONCILE_DEADLINE_SECS=$budget reconcile_bounded "$budget"
    commit_reconcile_result'''
assert s.count(old3) == 1
new3 = '''    # Plain assignment, not a `VAR=x func` prefix: zsh's scoping for a prefixed
    # assignment on a SHELL FUNCTION is not the same as on an external command, and a
    # signal handler is not the place to depend on which one this shell implements.
    RECONCILE_DEADLINE_SECS=$budget
    reconcile_bounded "$budget"
    RECONCILE_DEADLINE_SECS=""
    commit_reconcile_result'''
s = s.replace(old3, new3)
io.open(p, "w", encoding="utf-8").write(s)
print("patch6 ok")
