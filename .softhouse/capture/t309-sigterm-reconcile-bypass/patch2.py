import io
p = ".softhouse/bin/fire-program.sh"
s = io.open(p, encoding="utf-8").read()

# ---------------------------------------------------------------- stop_driver ---
old = '''  if (( ${#survivors} )); then
    log "driver did not stop on SIGTERM within ${DRIVER_STOP_GRACE_SECS}s -- SIGKILLing ${survivors[*]}"
    kill -KILL "${survivors[@]}" 2>/dev/null
  else
    log "driver stopped on SIGTERM; no survivors"
  fi
  return 0
}'''.replace("--", "—")
assert s.count(old) == 1, s.count(old)

new = '''  if (( ${#survivors} )); then
    log "driver did not stop on SIGTERM within ${DRIVER_STOP_GRACE_SECS}s — SIGKILLing ${survivors[*]}"
    kill -KILL "${survivors[@]}" 2>/dev/null
    # T309 — CONFIRM THE DEATH, do not assume it. `kill -KILL` returns as soon as the
    # signal is QUEUED; the process is not off the table yet. That mattered the moment
    # T309 put reconcile_tasks_json on this path, because its first act is
    # foreign_live_session_in_repo(), which reads /bin/ps and treats a live in-repo
    # `claude` as a reason to REFUSE. Without this poll the wrapper could refuse to
    # reconcile because of the very driver it had just killed — a race that would have
    # made the whole fix intermittently inert, which is worse than absent because it
    # would have tested green.
    # Bounded at ~2s (20 x 0.1s) and it never blocks longer: SIGKILL is uncatchable, so
    # anything still present after that is in an uninterruptible wait, and this SAYS so
    # rather than pretending otherwise.
    local tick left
    for tick in {1..20}; do
      left=()
      for p in "${survivors[@]}"; do
        st=$(/bin/ps -o stat= -p "$p" 2>/dev/null)
        [[ -n "$st" && "$st" != Z* ]] && left+=("$p")
      done
      (( ${#left} )) || break
      /bin/sleep 0.1
    done
    if (( ${#left} )); then
      log "ERROR: ${#left} process(es) still on the process table after SIGKILL — ${left[*]} — they are in an uninterruptible wait. Anything downstream that reads process liveness will see them and may REFUSE; that is the safe direction, but it means this fire's cleanup is INCOMPLETE."
    else
      log "driver SIGKILLed; confirmed off the process table"
    fi
  else
    log "driver stopped on SIGTERM; no survivors"
  fi
  # T309: remember what we stopped. foreign_live_session_in_repo() skips these, because
  # they are OUR driver, not a foreign session — the function's whole subject is
  # "somebody ELSE working in this checkout" and our own corpse is not that.
  STOPPED_TREE=("${DRIVER_TREE[@]}")
  return 0
}'''
s = s.replace(old, new)

# declare STOPPED_TREE beside DRIVER_TREE
old2 = 'typeset -ga DRIVER_TREE; DRIVER_TREE=()\n'
assert s.count(old2) == 1
new2 = ('typeset -ga DRIVER_TREE; DRIVER_TREE=()\n'
        '# T309: the tree stop_driver last signalled, so the liveness probe can exclude it.\n'
        'typeset -ga STOPPED_TREE; STOPPED_TREE=()\n')
s = s.replace(old2, new2)

io.open(p, "w", encoding="utf-8").write(s)
print("patch2 ok")
