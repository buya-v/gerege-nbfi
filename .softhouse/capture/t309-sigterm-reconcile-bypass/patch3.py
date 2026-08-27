import io
p = ".softhouse/bin/fire-program.sh"
s = io.open(p, encoding="utf-8").read()

# --------------------------------- foreign_live_session_in_repo: skip our own tree ---
old = '''    [[ "${first:t}" == claude ]] || continue      # the CLI, not /Applications/Claude.app
    [[ "$st" == Z* ]] && continue                 # a zombie is dead, merely unreaped
    kill -0 "$pid" 2>/dev/null || continue        # exited between the snapshot and now
'''
assert s.count(old) == 1
new = '''    [[ "${first:t}" == claude ]] || continue      # the CLI, not /Applications/Claude.app
    [[ "$st" == Z* ]] && continue                 # a zombie is dead, merely unreaped
    kill -0 "$pid" 2>/dev/null || continue        # exited between the snapshot and now
    # T309 — OUR OWN driver is not a FOREIGN session, and this function's whole subject
    # is "somebody ELSE working in this checkout". Before T309 the distinction never
    # arose: this only ran from the wrapper's normal tail, where the driver had already
    # been `wait`ed on and was off the table by construction. On the SIGNAL path it has
    # been KILLED microseconds earlier by stop_driver, and stop_driver's own poll can
    # time out on an uninterruptible wait — so without this the wrapper could refuse to
    # reconcile because of the corpse it had just made.
    # NOT a blanket "skip any claude": only the exact pids stop_driver signalled, and
    # only in this fire. The residual is pid reuse inside the ~1s between the kill and
    # this snapshot, which would let a brand-new unrelated `claude` be skipped; that is
    # narrow, it is stated rather than hidden, and it is strictly smaller than the race
    # it removes.
    if (( ${STOPPED_TREE[(I)$pid]} )); then
      FOREIGN_SESSIONS="${FOREIGN_SESSIONS} [pid ${pid} SKIPPED: this fire's own driver, already stopped]"
      continue
    fi
'''
s = s.replace(old, new)

# -------------------------------------------- reconcile_tasks_json: optional deadline ---
old2 = '''  local -a args; args=(--reconcile --fire "$STAMP" --repo "$REPO")
'''
assert s.count(old2) == 1
new2 = '''  local -a args; args=(--reconcile --fire "$STAMP" --repo "$REPO")
  # T309: the NORMAL tail leaves this empty (nothing is waiting on the wrapper there, and
  # a budget imposed for no reason is a way to lose evidence). The SIGNAL path sets it,
  # because it is racing launchd's SIGTERM->SIGKILL grace. Two call sites, two budgets,
  # and the difference is deliberate rather than a default nobody chose.
  [[ -n "${RECONCILE_DEADLINE_SECS:-}" ]] && args+=(--deadline-secs "$RECONCILE_DEADLINE_SECS")
'''
s = s.replace(old2, new2)

# rc=4 message is no longer only about the lock holder
old3 = '''    4) RECON_VERDICT="REFUSED by ready-tasks.py — the caller is not the lock holder" ;;'''
assert s.count(old3) == 1
new3 = '''    4) RECON_VERDICT="REFUSED by ready-tasks.py and NOTHING was changed — either the caller could not be established as the lock holder, or it ran in \\`in_session\\` mode and no in_progress task could be proven to belong to a dead fire (T309). Read the reconcile| lines." ;;'''
s = s.replace(old3, new3)

io.open(p, "w", encoding="utf-8").write(s)
print("patch3 ok")
