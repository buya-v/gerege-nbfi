import io
p = ".softhouse/bin/fire-program.sh"
s = io.open(p, encoding="utf-8").read()

# ---- 1. backticks inside a double-quoted zsh string are COMMAND SUBSTITUTION.
# Caught by driving it: the fire log read "...must never leave  behind for workers it
# just killed", because `in_progress` was executed as a command (and failed) on the
# signal path. Own goal, in a log line about telling the truth.
old = '''  log "SIG$sig received — stopping the driver, reconciling tasks.json, releasing the lock and TERMINATING (rc=$rc). A fire must never keep working after its lock is gone, and it must never leave `in_progress` behind for workers it just killed."'''
assert s.count(old) == 1
new = '''  log "SIG$sig received — stopping the driver, reconciling tasks.json, releasing the lock and TERMINATING (rc=$rc). A fire must never keep working after its lock is gone, and it must never leave in_progress behind for workers it just killed."'''
s = s.replace(old, new)

# ---- 2. do NOT remove the lock before the reconcile.
old2 = '''  # Step 2: the local half of the lock release, up front. Costs one unlink. release_lock
  # below is idempotent (`rm -f`) and still stages/commits/pushes the deletion.
  if [[ -e "$LOCK" ]]; then
    rm -f "$LOCK"
    log "local lock file removed — STEP 0 of the next fire on this host is already unblocked, whatever happens to the rest of this handler"
  fi

  # Step 3: the repair, inside a budget derived from what is actually left.'''
assert s.count(old2) == 1
new2 = '''  # THE LOCK STAYS ON DISK UNTIL AFTER THE RECONCILE, AND THAT IS A CORRECTION TO THIS
  # PATCH'S OWN FIRST DRAFT. The draft removed the local lock file here, before the
  # reconcile, on the reasoning that an unlink costs nothing and unblocks the next fire
  # even if this handler is SIGKILLed. Driving it showed what that actually bought:
  # ready-tasks.py then reported `lock: no .softhouse/LOCK on disk -- nobody holds this
  # repo`, so its authority check had NOTHING TO CHECK and every caller would have been
  # granted `wrapper` mode by default. Removing the lock first neuters, on the one path
  # where the reconciler now runs, the exact guard that decides whether it may run — the
  # same "wired to the wrong path" shape this task exists to fix, reintroduced by the fix.
  # The stranded-lock risk it was hedging against is already covered out of band:
  # `lock_holder_is_dead()` above takes over a lock whose pid is gone on this host
  # immediately, whatever its age (T202). So the lock is released by `release_lock`
  # below, in its normal position, and the reconcile runs under a lock that names this
  # wrapper — which is what makes the ancestry check meaningful.

  # The repair, inside a budget derived from what is actually left.'''
s = s.replace(old2, new2)

# ---- 3. the ORDER comment above on_signal must match what the code now does.
old3 = '''#   2. rm the LOCAL lock    — the half of release_lock that costs nothing and matters
#                             most. STEP 0 on THIS host reads the FILE; once it is gone
#                             the next fire is unblocked whatever else happens to us.
#                             `release_lock` below is idempotent about this.
#   3. reconcile + commit   — the repair. BOUNDED (see the budget arithmetic below).
#   4. release_lock         — stages the lock deletion, commits, and makes ONE bounded'''
assert s.count(old3) == 1
new3 = '''#   2. reconcile + commit   — the repair. BOUNDED (see the budget arithmetic below), and
#                             run while the LOCK IS STILL ON DISK, so ready-tasks.py's
#                             ancestry check has a lock to check. See the note in the
#                             body: releasing it first was this patch's own first draft
#                             and it silently disarmed that check.
#   3. release_lock         — removes the lock file, stages the deletion, commits, and
#                             makes ONE bounded'''
s = s.replace(old3, new3)
io.open(p, "w", encoding="utf-8").write(s)
print("patch7 ok")
