import io
p = ".softhouse/bin/fire-program.sh"
s = io.open(p, encoding="utf-8").read()

old = '''on_signal() {
  local sig=$1 rc=$2
  log "SIG$sig received — stopping the driver, releasing the lock and TERMINATING (rc=$rc). A fire must never keep working after its lock is gone."
  stop_driver
  release_lock
  exit $rc
}'''
assert s.count(old) == 1

new = '''#
# T309 — AND THE RECONCILER, WHICH WAS WIRED EXCLUSIVELY TO THE PATH THAT DOES NOT NEED IT.
#
# THE MEASURED DEFECT. T288 built the tasks.json repair and called it from ONE place:
# `run_exit_guard`, in the script\'s normal tail. `on_signal` released the lock and
# `exit`ed directly, so SIGTERM/INT/HUP/QUIT terminated the fire WITHOUT EVER REACHING
# IT — and the definition itself lived inside `run_exit_guard`, so on a first chain
# iteration the name did not even exist. But a driver that reaches the normal tail has
# ALREADY run its own STEP 5.5 exit protocol and left tasks.json truthful; the state that
# needs repairing is precisely the state a KILLED driver leaves. The repair was attached
# to the case that does not need it and absent from the case that does.
#
# WHAT IT COST, on this host: fire 20260823-080004 session 2 dispatched 8 workers, was
# SIGTERMed at 12:06:13, logged "driver stopped on SIGTERM; no survivors", released its
# lock and exited. Fire 20260823-140001 then opened on a tasks.json claiming 8 tasks
# `in_progress` — 4 branches sitting at the dispatch commit with zero commits ahead of
# main, 4 never created at all — and demoted them BY HAND.
#
# ORDER, AND EVERY POSITION IS ARGUED FROM THE BUDGET:
#   1. stop_driver          — first, always. The lock exists to keep two orchestrators out
#                             of one repo; releasing it while `claude` is alive opens the
#                             window it was written to close (T211).
#   2. rm the LOCAL lock    — the half of release_lock that costs nothing and matters
#                             most. STEP 0 on THIS host reads the FILE; once it is gone
#                             the next fire is unblocked whatever else happens to us.
#                             `release_lock` below is idempotent about this.
#   3. reconcile + commit   — the repair. BOUNDED (see the budget arithmetic below).
#   4. release_lock         — stages the lock deletion, commits, and makes ONE bounded
#                             push that carries BOTH commits. Deliberately one push, not
#                             two: a second `git_push_bounded` would add another whole
#                             GIT_PUSH_TIMEOUT_SECS to a handler racing a SIGKILL.
#
# THE BUDGET IS DERIVED, NOT PICKED. launchd sends SIGTERM then SIGKILL after its
# ExitTimeOut; the plist (mn.gerege.nbfi.softhouse-program) sets no ExitTimeOut key, so
# the default applies — ~20s [VERIFIED: the plist has no ExitTimeOut; the 20s figure is
# Apple\'s documented default and is NOT measured here, so SIGNAL_GRACE_SECS is
# overridable]. What is already spent before the reconcile can start is stop_driver\'s
# DRIVER_STOP_GRACE_SECS (5s, T217-calibrated) plus up to ~2s confirming a SIGKILL
# landed. What must still be affordable AFTER it is release_lock\'s bounded push
# (GIT_PUSH_TIMEOUT_SECS, 10s). So the reconcile gets what is left, measured at the
# moment it starts rather than assumed from the constants:
#
#     budget = SIGNAL_GRACE_SECS - (elapsed since the signal) - GIT_PUSH_TIMEOUT_SECS - 1
#
# and if that comes out below SIGNAL_RECONCILE_MIN_SECS the reconcile is SKIPPED, loudly,
# with the arithmetic in the log. Skipping is safe by construction because step 2 has
# already happened: the worst case is the pre-T309 behaviour, never a stranded lock.
# The budget is enforced TWICE, at different layers, because they fail differently:
#   * INNER, `ready-tasks.py --deadline-secs` — clamps every subprocess it spawns to the
#     remaining budget and degrades WIP evidence to UNVERIFIED while still performing the
#     demotion. Graceful: the repair lands, the colour is lost.
#   * OUTER, `reconcile_bounded` below — wall-clock kill of the whole subtree if python
#     itself wedges. Brutal: nothing is written. It exists because the inner bound cannot
#     protect against the interpreter never reaching its own deadline check.
#
# WHAT THIS PATH DELIBERATELY DOES *NOT* DO: the worktree WIP sweep. It walks every
# linked worktree with a `git status` each (43 of them when last counted, and the count
# is not stable — P-69), which cannot be fitted into single-digit seconds. Uncommitted
# worker WIP is therefore NOT rescued on the signal path. It is not lost either: the
# worktrees persist, and the NEXT fire\'s `run_exit_guard` sweeps them on its way out. So
# the cost of the omission is one fire of delay, not destruction, and that is the trade
# being made.
SIGNAL_GRACE_SECS="${SIGNAL_GRACE_SECS:-20}"
SIGNAL_RECONCILE_MIN_SECS="${SIGNAL_RECONCILE_MIN_SECS:-2}"

# Run reconcile_tasks_json under a hard wall-clock bound. Same shape as
# git_push_bounded: background it, poll, and kill the whole subtree at the deadline
# (python forks `git` and `/bin/ps`; killing only the top pid can leave those running).
# Polls at 0.1s so a fast reconcile costs ~0.1s of waiting rather than a whole second.
# POLARITY: fail-CLOSED — a reconcile that had to be killed reports FAILED and says the
# state is UNVERIFIED. It never reports the reassuring answer for work it did not see
# finish. Never blocks longer than the bound; always returns.
reconcile_bounded() {
  local budget=$1; shift
  local ticks=$(( budget * 10 ))
  RECON_VERDICT="not attempted"
  ( reconcile_tasks_json "$@" ) &
  local job=$! waited=0
  while (( waited < ticks )) && kill -0 "$job" 2>/dev/null; do
    /bin/sleep 0.1
    (( waited++ ))
  done
  if kill -0 "$job" 2>/dev/null; then
    log "ERROR: the signal-path reconcile exceeded its ${budget}s budget — killing it so this handler can still release the lock and exit inside launchd\'s grace. tasks.json was NOT repaired and any in_progress task in it is UNVERIFIED."
    local -a tree
    if driver_tree "$job"; then tree=("${DRIVER_TREE[@]}"); else tree=("$job"); fi
    kill -TERM "${tree[@]}" 2>/dev/null
    /bin/sleep 0.2
    kill -KILL "${tree[@]}" 2>/dev/null
    wait "$job" 2>/dev/null
    # ready-tasks.py writes through `<path>.t288.tmp` + os.replace, so tasks.json itself
    # is intact; only the temp file can be orphaned. Remove it, or the next fire\'s
    # dirty-tree rescue commits it into the repo as a deliverable.
    rm -f "$REPO/.softhouse/tasks.json.t288.tmp"
    RECON_VERDICT="FAILED — killed at its ${budget}s signal-path budget; state is NOT truthful"
    return 1
  fi
  wait "$job"
  return $?
}

# Commit whatever the signal-path reconcile changed. NO PUSH: release_lock\'s single
# bounded push, immediately after, carries this commit with it.
commit_reconcile_result() {
  git add -- \':(top).softhouse/tasks.json\' >/dev/null 2>&1
  git diff --cached --quiet -- \':(top).softhouse/tasks.json\' 2>/dev/null && {
    log "signal-path reconcile: no change to commit"
    return 0
  }
  if git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \\
       commit -q -m "softhouse: wrapper reconciled state after fire $STAMP was signalled (T309)

The driver was killed by a signal, so it never ran STEP 5.5 and never demoted its own
dispatches. A killed worker is dead, not paused. Reconcile: $RECON_VERDICT" >/dev/null 2>&1; then
    log "signal-path reconcile: committed the state correction"
  else
    log "ERROR: the signal-path reconcile\'s state correction could not be COMMITTED — it exists only in the working tree. The next fire\'s dirty-tree rescue should pick it up; if it does not, commit it by hand."
  fi
}

on_signal() {
  local sig=$1 rc=$2
  local t0=$(date +%s)
  log "SIG$sig received — stopping the driver, reconciling tasks.json, releasing the lock and TERMINATING (rc=$rc). A fire must never keep working after its lock is gone, and it must never leave `in_progress` behind for workers it just killed."
  stop_driver

  # Step 2: the local half of the lock release, up front. Costs one unlink. release_lock
  # below is idempotent (`rm -f`) and still stages/commits/pushes the deletion.
  if [[ -e "$LOCK" ]]; then
    rm -f "$LOCK"
    log "local lock file removed — STEP 0 of the next fire on this host is already unblocked, whatever happens to the rest of this handler"
  fi

  # Step 3: the repair, inside a budget derived from what is actually left.
  local elapsed=$(( $(date +%s) - t0 ))
  local budget=$(( SIGNAL_GRACE_SECS - elapsed - GIT_PUSH_TIMEOUT_SECS - 1 ))
  if (( budget < SIGNAL_RECONCILE_MIN_SECS )); then
    log "WARN: SKIPPING the signal-path reconcile — budget arithmetic leaves ${budget}s (grace ${SIGNAL_GRACE_SECS}s - ${elapsed}s already spent stopping the driver - ${GIT_PUSH_TIMEOUT_SECS}s reserved for the lock-release push - 1s), below the ${SIGNAL_RECONCILE_MIN_SECS}s minimum. tasks.json is UNREPAIRED and any in_progress task in it is a DEAD dispatch; the next fire must not believe it."
  else
    log "signal-path reconcile: ${budget}s of budget (grace ${SIGNAL_GRACE_SECS}s - ${elapsed}s spent - ${GIT_PUSH_TIMEOUT_SECS}s push reserve - 1s)"
    RECONCILE_DEADLINE_SECS=$budget reconcile_bounded "$budget"
    commit_reconcile_result
  fi

  release_lock
  log "SIG$sig handler complete after $(( $(date +%s) - t0 ))s (launchd grace is ~${SIGNAL_GRACE_SECS}s) — exiting rc=$rc"
  exit $rc
}'''
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patch5 ok")
