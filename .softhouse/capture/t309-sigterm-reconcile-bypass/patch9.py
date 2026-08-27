import io
p = ".softhouse/bin/fire-program.sh"
s = io.open(p, encoding="utf-8").read()

# ---------------------------------------------------------------- 0. the clock ---
old0 = '''GIT_PUSH_TIMEOUT_SECS="${GIT_PUSH_TIMEOUT_SECS:-10}"
'''
assert s.count(old0) == 1
new0 = '''GIT_PUSH_TIMEOUT_SECS="${GIT_PUSH_TIMEOUT_SECS:-10}"

# T309 — A BOUND MUST BE MEASURED IN SECONDS, NOT IN ITERATIONS, AND THIS WAS FOUND BY
# FAULT INJECTION RATHER THAN BY READING.
# Both bounded waits in this file were written as `while (( waited < N ))` around a
# `/bin/sleep`, counting TICKS and calling the product a timeout. That is only a timeout
# if a tick costs exactly what it sleeps. It does not: each tick forks /bin/sleep and
# runs a `kill -0`, and on a loaded machine — e.g. one with a real fire running on it,
# which is the normal condition here — that overhead dominates a 0.1s sleep. MEASURED:
# an 8s "budget" expressed as 80 x `/bin/sleep 0.1` took **21s** of wall clock, and the
# SIGTERM handler that was supposed to finish inside launchd's ~20s grace took 24.29s
# [.softhouse/capture/t309-sigterm-reconcile-bypass/wedge.txt, the pre-fix wedge run].
# So the guard added to keep the handler inside the grace was itself what pushed it out.
#
# `zsh/datetime` gives $EPOCHREALTIME as a PARAMETER — read with no fork, so consulting
# it every tick costs nothing and cannot itself distort what it measures. If the module
# is unavailable the fallback is `date +%s`, which forks and has 1s granularity; that is
# coarser but still a real clock, and the fallback is REPORTED rather than silent.
zmodload zsh/datetime 2>/dev/null
HAVE_EPOCHREALTIME=0
[[ -n "${EPOCHREALTIME:-}" ]] && HAVE_EPOCHREALTIME=1
(( HAVE_EPOCHREALTIME )) || log "WARN: zsh/datetime is unavailable — bounded waits fall back to \\`date +%s\\` at 1s granularity"

# Seconds now, as a float when we can get one. Sets REPLY; no subshell, no fork on the
# EPOCHREALTIME path.
now_secs() {
  if (( HAVE_EPOCHREALTIME )); then REPLY=$EPOCHREALTIME; else REPLY=$(date +%s); fi
}

# wait_bounded <pid> <seconds> -> 0 if it exited in time, 1 if the deadline passed.
# THE LOOP IS GOVERNED BY THE CLOCK. Ticks are only how often it looks.
wait_bounded() {
  local job=$1 budget=$2 start
  now_secs; start=$REPLY
  while kill -0 "$job" 2>/dev/null; do
    now_secs
    (( REPLY - start >= budget )) && return 1
    /bin/sleep 0.1
  done
  return 0
}
'''
s = s.replace(old0, new0)

# ------------------------------------------------------- 1. git_push_bounded ---
old1 = '''  git push -q "$@" >/dev/null 2>&1 &
  local job=$!
  local waited=0
  while (( waited < GIT_PUSH_TIMEOUT_SECS )) && kill -0 "$job" 2>/dev/null; do
    /bin/sleep 1
    (( waited++ ))
  done
  if kill -0 "$job" 2>/dev/null; then'''
assert s.count(old1) == 1
new1 = '''  git push -q "$@" >/dev/null 2>&1 &
  local job=$!
  # T309: was `while (( waited < GIT_PUSH_TIMEOUT_SECS ))` around `/bin/sleep 1`, i.e. a
  # bound in ticks. Same defect as the one measured in reconcile_bounded, milder only
  # because a 1s sleep dwarfs its own overhead; it is still not the bound it claims to be,
  # and this function's stated 10s is what on_signal's budget arithmetic RESERVES.
  wait_bounded "$job" "$GIT_PUSH_TIMEOUT_SECS"
  if kill -0 "$job" 2>/dev/null; then'''
s = s.replace(old1, new1)

# ------------------------------------------------------- 2. reconcile_bounded ---
old2 = '''  local budget=$1; shift
  local ticks=$(( budget * 10 ))
  RECON_VERDICT="not attempted"'''
assert s.count(old2) == 1
new2 = '''  local budget=$1; shift
  RECON_VERDICT="not attempted"'''
s = s.replace(old2, new2)

old3 = '''  local job=$! waited=0
  while (( waited < ticks )) && kill -0 "$job" 2>/dev/null; do
    /bin/sleep 0.1
    (( waited++ ))
  done
  if kill -0 "$job" 2>/dev/null; then'''
assert s.count(old3) == 1
new3 = '''  local job=$!
  wait_bounded "$job" "$budget"
  if kill -0 "$job" 2>/dev/null; then'''
s = s.replace(old3, new3)

# ----------------------------------- 3. the reserve must cover the teardown too ---
old4 = '''  local budget=$(( SIGNAL_GRACE_SECS - elapsed - GIT_PUSH_TIMEOUT_SECS - 1 ))'''
assert s.count(old4) == 1
new4 = '''  # The "- 2" is not slack for its own sake: reconcile_bounded's own teardown (SIGTERM,
  # 0.2s, SIGKILL, reap) and commit_reconcile_result's `git commit` both run AFTER the
  # budget is spent and BEFORE release_lock's push starts. Worst case with the defaults:
  # ~1s stopping the driver + 7s reconcile + ~0.5s teardown + ~0.3s commit + 10s push
  # = ~18.8s, inside the ~20s grace. MEASURED wedge run after this correction is in
  # .softhouse/capture/t309-sigterm-reconcile-bypass/wedge.txt.
  local budget=$(( SIGNAL_GRACE_SECS - elapsed - GIT_PUSH_TIMEOUT_SECS - 2 ))'''
s = s.replace(old4, new4)

old5 = '''    log "WARN: SKIPPING the signal-path reconcile — budget arithmetic leaves ${budget}s (grace ${SIGNAL_GRACE_SECS}s - ${elapsed}s already spent stopping the driver - ${GIT_PUSH_TIMEOUT_SECS}s reserved for the lock-release push - 1s), below'''
assert s.count(old5) == 1
new5 = '''    log "WARN: SKIPPING the signal-path reconcile — budget arithmetic leaves ${budget}s (grace ${SIGNAL_GRACE_SECS}s - ${elapsed}s already spent stopping the driver - ${GIT_PUSH_TIMEOUT_SECS}s reserved for the lock-release push - 2s for teardown and commit), below'''
s = s.replace(old5, new5)

old6 = '''    log "signal-path reconcile: ${budget}s of budget (grace ${SIGNAL_GRACE_SECS}s - ${elapsed}s spent - ${GIT_PUSH_TIMEOUT_SECS}s push reserve - 1s)"'''
assert s.count(old6) == 1
new6 = '''    log "signal-path reconcile: ${budget}s of budget (grace ${SIGNAL_GRACE_SECS}s - ${elapsed}s spent - ${GIT_PUSH_TIMEOUT_SECS}s push reserve - 2s teardown/commit)"'''
s = s.replace(old6, new6)
io.open(p, "w", encoding="utf-8").write(s)
print("patch9 ok")
