import io
p = ".softhouse/bin/fire-program.sh"
s = io.open(p, encoding="utf-8").read()

old = '''  log "stopping the driver: ${#DRIVER_TREE} process(es) — ${DRIVER_TREE[*]}"
  # SIGTERM, never SIGINT: INT is SIG_IGN in an async child here (measured).
  kill -TERM "${DRIVER_TREE[@]}" 2>/dev/null
  /bin/sleep "$DRIVER_STOP_GRACE_SECS"
  local -a survivors; survivors=()
  local p st
  for p in "${DRIVER_TREE[@]}"; do
    st=$(/bin/ps -o stat= -p "$p" 2>/dev/null)
    # a Z is already dead and merely unreaped; kill -0 cannot tell the two apart
    [[ -n "$st" && "$st" != Z* ]] && survivors+=("$p")
  done
'''
assert s.count(old) == 1

new = '''  log "stopping the driver: ${#DRIVER_TREE} process(es) — ${DRIVER_TREE[*]}"
  # SIGTERM, never SIGINT: INT is SIG_IGN in an async child here (measured).
  kill -TERM "${DRIVER_TREE[@]}" 2>/dev/null
  # T309 — POLL FOR THE GRACE, DO NOT SLEEP IT. This was `/bin/sleep
  # "$DRIVER_STOP_GRACE_SECS"`, an UNCONDITIONAL 5s, and it was the single largest item
  # in the signal handler's budget: T309 puts a reconcile on this path, and the reconcile
  # gets only what launchd's ~20s grace has left after stop_driver and before
  # release_lock's bounded push. Driven with the flat sleep, the reconcile was handed 3s
  # to do ~2s of work — a margin nobody would choose on purpose.
  #
  # THE MAXIMUM IS UNCHANGED, which is what makes this safe against T217's calibration:
  # a driver that needs the whole DRIVER_STOP_GRACE_SECS still gets it. Only the case
  # where the driver has ALREADY exited returns early. T217 measured the real `claude`
  # exiting on SIGTERM in 0.826-2.591s over six trials, against a 5s grace set at ~2x the
  # observed max; polling turns that deliberate 2x safety margin from a cost paid on
  # every stop into one paid only when it is needed.
  #
  # ONE /bin/ps snapshot per tick, not one per pid: the tree is up to 7 processes, so a
  # per-pid probe would be ~350 forks across a 5s grace, and the snapshot is also what
  # driver_tree and foreign_live_session_in_repo already do (a single instant cannot tear
  # the way N successive probes can).
  local -a survivors; survivors=()
  local p st tick snap
  local -a psl f
  local ticks=$(( DRIVER_STOP_GRACE_SECS * 10 ))
  for (( tick = 0; tick <= ticks; tick++ )); do
    survivors=()
    snap=$(/bin/ps -Ao pid=,stat= 2>/dev/null)
    if [[ -z "$snap" ]]; then
      # POLARITY: fail-CLOSED. /bin/ps not answering must not read as "everything died".
      # Fall back to the pre-T309 behaviour — wait out the whole grace, then treat every
      # pid as a survivor and SIGKILL it, which is what the old code's `st=""` path did.
      log "WARN: /bin/ps did not answer while waiting for the driver to stop — falling back to the full ${DRIVER_STOP_GRACE_SECS}s grace and treating the whole tree as surviving"
      /bin/sleep "$DRIVER_STOP_GRACE_SECS"
      survivors=("${DRIVER_TREE[@]}")
      break
    fi
    psl=(${(f)snap})
    for p in "${DRIVER_TREE[@]}"; do
      for st in $psl; do
        f=(${=st})
        (( ${#f} >= 2 )) || continue
        [[ "$f[1]" == "$p" ]] || continue
        # a Z is already dead and merely unreaped; kill -0 cannot tell the two apart
        [[ "$f[2]" != Z* ]] && survivors+=("$p")
        break
      done
    done
    (( ${#survivors} )) || break
    (( tick < ticks )) && /bin/sleep 0.1
  done
'''
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patch8 ok")
