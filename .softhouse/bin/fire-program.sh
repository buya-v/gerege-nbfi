#!/bin/zsh
# Local fire of the gerege-nbfi migration driver.
#
# Runs on Buyan's Mac via launchd (mn.gerege.nbfi.softhouse-program), so the
# Fineract REFERENCE ORACLE on localhost is reachable — which is what the cloud
# routine cannot do. Vector capture and conformance therefore only truly advance
# on this fire.
#
#   "oracle" here == the Fineract reference implementation. Oracle DATABASE is
#   prohibited by CLAUDE.md; the engine everywhere is PostgreSQL.
#
# Usage:
#   fire-program.sh            # preflight, take the lock, run the driver
#   fire-program.sh --probe    # preflight only; print findings, touch nothing
#   fire-program.sh --force    # ignore a live lock (use only after a crash)

set -uo pipefail

REPO="${GEREGE_NBFI_REPO:-/Users/buv/gerege-nbfi}"
FINERACT_SRC="${FINERACT_SRC:-/Users/buv/fineract}"
LOG_DIR="${LOG_DIR:-$HOME/Library/Logs/gerege-nbfi}"
LOCK="$REPO/.softhouse/LOCK"
LOCK_MAX_AGE_SECS="${LOCK_MAX_AGE_SECS:-21600}"   # 6h — older than this is stale
CLAUDE_BIN="${CLAUDE_BIN:-$HOME/.local/bin/claude}"

# Reference-oracle probes. PostgreSQL only — never MySQL/MariaDB, never Oracle DB.
PG_HOST="${PG_HOST:-localhost}"
PG_PORT="${PG_PORT:-5432}"
FINERACT_HEALTH_URL="${FINERACT_HEALTH_URL:-https://localhost:8443/fineract-provider/actuator/health}"

PROBE_ONLY=0; FORCE=0
for a in "$@"; do
  case "$a" in
    --probe) PROBE_ONLY=1 ;;
    --force) FORCE=1 ;;
    *) print -u2 "unknown arg: $a"; exit 64 ;;
  esac
done

mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
FIRE_START_EPOCH=$(date +%s)
LOG="$LOG_DIR/fire-$STAMP.log"
exec > >(tee -a "$LOG") 2>&1

log() { print -r -- "[$(date +%H:%M:%S)] $*"; }
log "fire start — repo=$REPO probe=$PROBE_ONLY force=$FORCE log=$LOG"

# T213: the merged/clean worktree-prune classifier lives in its own file so
# the T213 fixture harness can source the SAME code this fire runs, rather
# than a reimplementation that could drift from it. `${0:A:h}` resolves
# against the script's own path (before the `cd "$REPO"` below moves us),
# so this works whether fire-program.sh was invoked with a relative or
# absolute path.
SCRIPT_DIR="${0:A:h}"

# T309 -- WHICH BYTES IS THIS FIRE ACTUALLY RUNNING?
# T301 exists because a branch that changed THIS FILE was landed while a fire was live,
# and afterwards nobody could say from the evidence whether the live fire had been
# running the pre-landing or the post-landing bytes. That question is answerable by a
# measurement taken at start, so take it. Two facts, because they answer different halves:
#   * the sha256 identifies the VERSION;
#   * the inode identifies the FILE OBJECT the running shell has open, which is what
#     decides whether a later rewrite can reach it at all.
#
# WHAT THE HAZARD ACTUALLY IS, MEASURED (T309 probes, .softhouse/capture/
# t309-sigterm-reconcile-bypass/probe-zsh-reread.txt and probe-git-inode.txt):
#   * zsh 5.9 does NOT slurp a script: it goes back to the file for more input. A ~90 KB
#     script rewritten IN PLACE (same inode) mid-run executed the REWRITTEN tail
#     [probe 1 leg B]. So "editing the running wrapper" is a real hazard, not folklore.
#   * but a rename-into-place (NEW inode) does NOT reach the running shell, which holds
#     an fd on the old inode [probe 1 leg C] -- and every git operation that lands a
#     change (merge, checkout -- <path>, pull --ff-only) was measured to write a NEW
#     inode and rename it over the path [probe 2, git 2.50.1 (Apple Git-155); every leg
#     asserts the content actually changed, because the first draft passed vacuously].
# CONSEQUENCE: landing a branch that edits this file while a fire is live is SAFE; the
# live fire finishes on the bytes it started with. What is NOT safe is an IN-PLACE
# rewrite of the live path -- `sed -i ''`, `cat > fire-program.sh`, a python
# `open(path,"w")`, or an editor that saves without an atomic rename. Do not do that to a
# checkout that has a fire running in it; edit in a worktree and land it through git.
if [[ -r "${0:A}" ]]; then
  log "wrapper identity: path=${0:A} inode=$(/usr/bin/stat -f %i "${0:A}" 2>/dev/null || print '?') sha256=$(/usr/bin/shasum -a 256 "${0:A}" 2>/dev/null | cut -c1-16 || print '?') bytes=$(/usr/bin/stat -f %z "${0:A}" 2>/dev/null || print '?')"
else
  log "WARN: could not read this script's own bytes at ${0:A} -- the version of the wrapper this fire ran is UNRECORDED"
fi

source "$SCRIPT_DIR/lib-worktree-prune.zsh" || { log "FATAL: could not source lib-worktree-prune.zsh"; exit 1; }

cd "$REPO" || { log "FATAL: repo not found"; exit 1; }

# ---------------------------------------------------------------- preflight ---
[[ -x "$CLAUDE_BIN" ]] || { log "FATAL: claude CLI not executable at $CLAUDE_BIN"; exit 1; }
[[ -d "$FINERACT_SRC" ]] && log "fineract source: present at $FINERACT_SRC" \
                         || log "WARN: fineract source missing at $FINERACT_SRC — source analysis will be blocked"

# PostgreSQL reachable? (the engine for BOTH the reference oracle and the Go module)
if nc -z -G 2 "$PG_HOST" "$PG_PORT" 2>/dev/null; then
  PG_STATUS="reachable at $PG_HOST:$PG_PORT"
else
  PG_STATUS="NOT reachable at $PG_HOST:$PG_PORT"
fi
log "postgres: $PG_STATUS"

# Prohibited-engine sentinels: anything listening on Oracle DB 1521 / MySQL 3306
PROHIBITED=""
nc -z -G 2 "$PG_HOST" 1521 2>/dev/null && PROHIBITED="$PROHIBITED oracle-db:1521"
nc -z -G 2 "$PG_HOST" 3306 2>/dev/null && PROHIBITED="$PROHIBITED mysql:3306"
[[ -n "$PROHIBITED" ]] && log "WARN: prohibited engine port(s) open —$PROHIBITED. PostgreSQL is the only permitted database; do not point the oracle at these."

# Docker available? Decides whether a down oracle is "bring it up" or "park it".
if docker info >/dev/null 2>&1; then
  DOCKER_STATUS="running ($(docker version --format '{{.Server.Version}}' 2>/dev/null))"
else
  DOCKER_STATUS="NOT running — the driver cannot start the reference-oracle stack this fire"
fi
log "docker: $DOCKER_STATUS"

# Fineract reference oracle up?
if curl -sk --max-time 8 "$FINERACT_HEALTH_URL" >/dev/null 2>&1; then
  ORACLE_STATUS="REACHABLE at $FINERACT_HEALTH_URL"
else
  ORACLE_STATUS="UNREACHABLE at $FINERACT_HEALTH_URL"
fi
log "reference oracle (Fineract): $ORACLE_STATUS"

# T312 — BRANCH CASE-SHADOW GUARD. Two lines, deliberately: `install-hook` is idempotent
# and installs a git reference-transaction hook that REFUSES creation of a
# refs/heads/softhouse/* ref differing from an existing one only by case; `sweep --quiet`
# prints any shadow already present. It is here rather than in the skill because the
# skill's corpse check is a glob the driver retypes each fire, and P-45 — "a guard that
# only works when someone remembers to run it enforces nothing" — is exactly how fire
# 20260827-230001 recorded eight branches as "gone or empty" over 73 committed commits.
# Never fatal: both are `|| true`, and a broken guard must not stop a fire.
/usr/bin/python3 "$SCRIPT_DIR/branch_sweep.py" install-hook --repo "$REPO" 2>&1 | while IFS= read -r l; do log "refguard| $l"; done || true
/usr/bin/python3 "$SCRIPT_DIR/branch_sweep.py" sweep --repo "$REPO" --pattern 'softhouse/*' --quiet 2>&1 | while IFS= read -r l; do log "sweep| $l"; done || true

if (( PROBE_ONLY )); then
  log "probe only — exiting without taking the lock or invoking the driver"
  exit 0
fi

# --------------------------------------------------------------------- lock ---
# The lock lives in the repo and is pushed, so the daily CLOUD fire sees it too
# and exits instead of running a second orchestrator over the same state.
git pull --ff-only --quiet || log "WARN: git pull --ff-only failed; continuing on local state"

# T202 — SIGKILL is untrappable, so a hard-killed fire STRANDS its lock, and on
# this host that is the NORMAL outcome rather than the exotic one. Two measured
# facts combine (both under zsh 5.9, see .softhouse/reviews/t202-probe/):
#   1. zsh DEFERS a trap until the current FOREGROUND child exits — a SIGTERM
#      sent 0.6 s into a 30 s foreground child ran the handler 29.88 s later,
#      at the child's exit, not on delivery.
#   2. the fire's foreground child is `claude`, which runs for HOURS.
# launchd's stop path is SIGTERM then SIGKILL after a short grace, so the signal
# handler below will usually never get to run at all — the fire is SIGKILLed
# with the lock still on disk, and then EVERY fire for the next 6 h exits at the
# "another orchestrator holds the lock" branch below. The lock records the
# holder's host and pid in the JSON body written just below; if that pid is
# gone on THIS host, the holder is dead and the lock is stale NOW, whatever age.
#
# POLARITY: fail-CLOSED. This function returns "dead" only when every leg is
# POSITIVELY established. Unreadable lock, unparseable host or pid, a lock from
# a DIFFERENT host, our own pid, or a pid that is still alive all return 1 and
# leave the existing ${LOCK_MAX_AGE_SECS} age rule in sole charge. It can make
# takeover happen SOONER; it can never make a live lock look free.
lock_holder_is_dead() {
  local body host pid
  [[ -r "$LOCK" ]] || return 1
  body="$(<"$LOCK")" || return 1
  [[ "$body" == *'"host": "'* ]] || return 1
  [[ "$body" == *'"pid": '*   ]] || return 1
  host="${${body#*\"host\": \"}%%\"*}"
  pid="${${body#*\"pid\": }%%,*}"
  [[ "$host" == "$(hostname -s)" ]] || return 1   # never judge another machine
  [[ "$pid" == <1-> ]]             || return 1   # zsh numeric glob; junk => alive
  (( pid == $$ ))                  && return 1   # never judge ourselves
  kill -0 "$pid" 2>/dev/null       && return 1   # still running => not stale
  return 0
}

if [[ -f "$LOCK" ]] && (( ! FORCE )); then
  LOCK_EPOCH=$(/usr/bin/stat -f %m "$LOCK" 2>/dev/null || print 0)
  AGE=$(( $(date +%s) - LOCK_EPOCH ))
  if lock_holder_is_dead; then
    log "lock holder is a DEAD pid on this host (lock age ${AGE}s) — a hard-killed fire stranded it; taking it over now instead of waiting out ${LOCK_MAX_AGE_SECS}s:"; cat "$LOCK"
  elif (( AGE < LOCK_MAX_AGE_SECS )); then
    log "another orchestrator holds the lock (age ${AGE}s):"; cat "$LOCK"
    log "exiting — not running two orchestrators over one repo"
    exit 0
  else
    log "stale lock (age ${AGE}s > ${LOCK_MAX_AGE_SECS}s) — taking it over"
  fi
fi

# P-85 / STEP 0. `started_at` is stamped once and is NOT a freshness signal: it
# cannot tell "the holder died five hours ago" from "the holder has been working
# for five hours." On 2026-08-22 a second session reused this fire's id AND its
# started_at, so a LIVE holder wore a six-hour-old timestamp, the cloud fire
# applied the 6h rule exactly as written, and four worker branches died with its
# sandbox. `heartbeat` is written here so the field EXISTS from the first
# instant a lock is held -- but it is corroboration only. The AUTHORITATIVE
# freshness signal is the holder's most recent push to origin/main
# (`git log -1 --format=%ct origin/main`), because push recency is DERIVED from
# doing the work rather than maintained beside it, and so cannot silently fall
# behind the truth the way a remembered field can (P-45, five recorded times).
# If heartbeat and push-recency ever disagree, believe push-recency.
#
# T309 -- `fire` IS RECORDED HERE, AND IT IS LOAD-BEARING, NOT DECORATION. It is the
# only unfakeable answer to "which fire dispatched this task?" available to a process
# running INSIDE a live fire. `ready-tasks.py --reconcile`, in `in_session` mode, demotes
# an `in_progress` task only when the task's own `fire` differs from THIS value -- the
# argument being the lock's exclusivity: at most one fire holds this file, so a task
# stamped with a different fire id belongs to a fire that is over. The id was previously
# recoverable only by parsing `"log"` for the stamp, which is a derivation, not a field.
cat > "$LOCK" <<EOF
{
  "holder": "local-launchd",
  "host": "$(hostname -s)",
  "pid": $$,
  "fire": "$STAMP",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "heartbeat": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "heartbeat_note": "CORROBORATION ONLY. The authoritative liveness signal is the newest commit on origin/main; see STEP 0 of the softhouse-program skill.",
  "log": "$LOG",
  "oracle": "$ORACLE_STATUS",
  "postgres": "$PG_STATUS"
}
EOF
git add -f "$LOCK" >/dev/null 2>&1
git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" commit -q -m "softhouse: local fire lock ($STAMP)" >/dev/null 2>&1
git push -q origin main 2>/dev/null || log "WARN: could not push lock — cloud fire may not see it"

LOCK_RELEASED=0

# T217 — bound release_lock's `git push`. Before this, the push at the end of
# release_lock had no timeout: a hung remote could keep release_lock from
# RETURNING forever. Established by reading the code (not assumed): the LOCAL
# lock file is removed by `rm -f "$LOCK"`, the first statement below, BEFORE
# any git call — so a hung push is never a lock-safety problem; STEP 0's
# preflight reads that file, and it is already gone. What a hung push DOES
# threaten is the exit path itself: `release_lock` runs either at the tail of
# a normal run (the `trap release_lock EXIT`) or from `on_signal`, which calls
# `exit $rc` only AFTER `release_lock` returns. A push that never returns
# means `on_signal` never reaches its `exit`, so the whole point of T211 — the
# handler completing inside launchd's SIGTERM->SIGKILL grace — is undone by
# this one call, and the fire is SIGKILLed anyway (which also kills any
# still-running `git push`/ssh child, since it is the wrapper itself that
# dies, not just the driver tree).
# FAILURE MODE ACCEPTED: the remote may not see the release promptly (or at
# all, if the push was going to fail anyway) — the CLOUD fire's view of the
# lock can lag by up to GIT_PUSH_TIMEOUT_SECS. That is strictly better than
# today's unbounded hang, and it never re-strands the LOCAL lock, which is the
# one STEP 0 on THIS host actually checks.
# FAILURE MODE PROTECTED AGAINST: a hung push keeping a signal handler (or the
# EXIT trap) alive past launchd's grace, turning a clean T211 stop back into a
# SIGKILL — the exact regression this follow-up exists to close.
GIT_PUSH_TIMEOUT_SECS="${GIT_PUSH_TIMEOUT_SECS:-10}"

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
(( HAVE_EPOCHREALTIME )) || log "WARN: zsh/datetime is unavailable — bounded waits fall back to \`date +%s\` at 1s granularity"

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

# Run `git push` in the background and give it at most GIT_PUSH_TIMEOUT_SECS
# of wall clock. If it is still running at the deadline, TERM then KILL the
# WHOLE tree it spawned (git push forks git-remote-https/ssh; killing only the
# top pid can leave those running) — reusing driver_tree's generic ps-snapshot
# walk, defined further down. That is safe to call from here even though it
# textually appears later: every top-level statement in this script (function
# definitions included) runs in order before any CALL to release_lock can
# happen — release_lock is only reached via `trap … EXIT` or `on_signal`,
# both registered after driver_tree's own definition has already executed.
# Never blocks longer than the bound; always returns.
git_push_bounded() {
  local desc=$1; shift
  git push -q "$@" >/dev/null 2>&1 &
  local job=$!
  # T309: was `while (( waited < GIT_PUSH_TIMEOUT_SECS ))` around `/bin/sleep 1`, i.e. a
  # bound in ticks. Same defect as the one measured in reconcile_bounded, milder only
  # because a 1s sleep dwarfs its own overhead; it is still not the bound it claims to be,
  # and this function's stated 10s is what on_signal's budget arithmetic RESERVES.
  wait_bounded "$job" "$GIT_PUSH_TIMEOUT_SECS"
  if kill -0 "$job" 2>/dev/null; then
    log "WARN: git push ($desc) still running after ${GIT_PUSH_TIMEOUT_SECS}s — killing it so the caller can return; the LOCAL lock file is already gone, only the remote's view of the release may lag"
    local -a tree
    if driver_tree "$job"; then
      tree=("${DRIVER_TREE[@]}")
    else
      tree=("$job")
    fi
    kill -TERM "${tree[@]}" 2>/dev/null
    /bin/sleep 1
    kill -KILL "${tree[@]}" 2>/dev/null
    wait "$job" 2>/dev/null
    return 1
  fi
  wait "$job"
  local rc=$?
  (( rc != 0 )) && log "WARN: git push ($desc) failed rc=$rc"
  return $rc
}

release_lock() {
  (( LOCK_RELEASED )) && return
  cd "$REPO" || return
  rm -f "$LOCK"
  LOCK_RELEASED=1
  # Stage ONLY the lock's deletion — the driver commits its own state changes.
  git add -A -- "$LOCK" >/dev/null 2>&1
  git diff --cached --quiet && { log "lock already released"; return; }
  git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" commit -q -m "softhouse: release local fire lock ($STAMP)" >/dev/null 2>&1
  git_push_bounded "release lock" origin main
  log "lock released"
}

# T211 — STOPPING THE DRIVER, which a signal handler must do BEFORE it releases
# the lock. All of this is measured under zsh 5.9 through the real launchd shape
# (`/bin/zsh -lc <script>`, own session, DEFAULT signal dispositions); the
# transcripts are in .softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/
# T211-probe/ and the four facts it rests on are:
#
#   1. `setopt monitor` is REFUSED in this shape — zsh 5.9 answers
#      "can't change option: monitor" with no controlling terminal
#      [T211-probe/semantics.txt, S5b]. So there is NO job control, so a
#      background job does NOT get its own process group: every descendant
#      shares the WRAPPER'S pgid [semantics2.txt, S4b; and the live fire
#      20260822-080001, where wrapper 65843 and `claude` 5329 both sit in pgid
#      65843]. `kill -- -$$` would therefore signal the wrapper itself, so the
#      one-line process-group kill is not available to us.
#   2. `$!` of a bare background PIPELINE is its LAST member — `jq`, not the
#      driver [semantics2.txt, S4-clean]. `$!` of `( … ) &` is the SUBSHELL,
#      which is the parent of every member [S4b]. run_driver uses the subshell
#      form for exactly that reason.
#   3. The tree is THREE levels deep, because /usr/bin/caffeinate EXECS the
#      utility in place and leaves its assertion-holder as a CHILD of it
#      [semantics.txt S7, treewalk.txt]. Measured shape:
#          $!  zsh          ( … ) & subshell
#           ├─ zsh          the { … } group == pipeline member 1
#           │   └─ claude   caffeinate exec'd it in place  <-- the one that matters
#           │       └─ caffeinate   assertion holder
#           ├─ tee
#           └─ jq
#      So `kill $!` alone MISSES `claude` by two levels [treewalk.txt].
#   4. SIGINT is SIG_IGN in an asynchronous child of a non-job-control shell
#      (the POSIX rule that produced T202's P-55 false reading), while SIGTERM
#      is not [semantics.txt, S6]. A handler that forwarded SIGINT would be a
#      dead letter; TERM-then-KILL is what actually stops the job.
#
# WHY THIS IS NOT OPTIONAL: `background + wait + exit` on its own exits in
# 0.130s but leaves the child RUNNING, reparented to pid 1
# [waittrap-matrix.txt, cell bg/exit]. That would trade a stranded LOCK for an
# unlocked `claude` still writing to the repo — strictly worse. Killing the
# tree is the half of the fix that makes the prompt exit safe.
#
# T217 — DRIVER_STOP_GRACE_SECS CALIBRATED AGAINST A REAL `claude`, not a
# `/bin/sleep` stand-in. T211 chose 3s against a fake child that dies
# instantly, which cannot answer "how long does claude itself take to exit on
# SIGTERM" by construction. Measured directly: the real binary at
# $HOME/.local/bin/claude, `-p` (headless), `--model haiku`, own session,
# default signal dispositions, SIGTERM delivered mid-request (4 trials, 3–7s
# into a call that runs ~9–10s end to end) — SIGTERM-to-exit was 0.826s,
# 1.055s, 1.141s, 1.156s, 1.194s, 2.591s (n=6, mean ~1.16s, max 2.591s); a
# separate cluster of 3 trials with SIGTERM delivered at 0.2–0.5s (still in
# startup, before the model call) exited in 0.162–0.208s. No trial hung.
# [VERIFIED: this run, .softhouse/reviews/t217-probe/calibrate-grace-out.txt]
# Set to 5s — roughly 2x the observed max (2.591s), not merely clearing it —
# because the measured trials are a single-turn, tool-free `-p` call on one
# machine on one day; a real fire's `claude` is running `/softhouse-program`
# with Bash/Edit tool calls and possibly MCP connections, which this
# calibration did NOT exercise and could plausibly add shutdown latency
# (extra child processes, open sockets) beyond what a bare text completion
# shows [UNVERIFIED for that heavier shape — see handoff]. Still overridable
# by environment without editing this file.
DRIVER_JOB_PID=0
DRIVER_STOP_GRACE_SECS="${DRIVER_STOP_GRACE_SECS:-5}"
typeset -ga DRIVER_TREE; DRIVER_TREE=()
# T309: the tree stop_driver last signalled, so the liveness probe can exclude it.
typeset -ga STOPPED_TREE; STOPPED_TREE=()

# Fills DRIVER_TREE with $1 and every descendant, parents before children.
# PROGRAM NAMED (P-58): /bin/ps, the BSD ps shipped with macOS; `-o pid=,ppid=`
# with empty headers, so there is no header line to skip and no locale-dependent
# column title to parse. ONE snapshot, not a `pgrep -P` per level: repeated
# pgrep calls each see a different instant, so a process that forks between two
# of them is invisible to the walk, and the walk cannot tell that from "no such
# child". A single snapshot cannot tear that way.
# POLARITY: fail-CLOSED — if ps does not answer, it returns 1 and says so rather
# than reporting an empty tree that looks like "nothing to kill".
driver_tree() {
  local root=$1 line pid ppid depth added snap
  local -a lines f
  DRIVER_TREE=()
  [[ "$root" == <1-> ]] || return 1
  snap=$(/bin/ps -Ao pid=,ppid= 2>/dev/null) || return 1
  lines=(${(f)snap})
  (( ${#lines} > 1 )) || return 1        # a one-line process table is not a table
  DRIVER_TREE=("$root")
  # depth cap 6: the measured tree is 3 deep; the cap makes the loop total even
  # if the process table were somehow cyclic.
  for depth in 1 2 3 4 5 6; do
    added=0
    for line in $lines; do
      f=(${=line})
      pid=$f[1]; ppid=$f[2]
      [[ "$pid" == <1-> && "$ppid" == <1-> ]] || continue
      (( ${DRIVER_TREE[(I)$ppid]} )) || continue     # parent not (yet) in the tree
      (( ${DRIVER_TREE[(I)$pid]}  )) && continue     # already collected
      DRIVER_TREE+=("$pid"); added=1
    done
    (( added )) || break
  done
  return 0
}

# Stop the driver job and everything under it. Safe to call at ANY point in the
# fire: DRIVER_JOB_PID is 0 whenever no driver is running, and it is zeroed
# before any killing starts, so a second signal arriving mid-handler is a no-op
# rather than a second round of kills.
stop_driver() {
  local job=$DRIVER_JOB_PID
  (( job > 0 )) || return 0
  DRIVER_JOB_PID=0
  if ! driver_tree "$job"; then
    log "ERROR: could not enumerate the driver's process tree (/bin/ps did not answer) — signalling ONLY the job pid $job. The driver's own children may survive as ORPHANS; treat this fire's processes as UNVERIFIED and look for a stray claude/caffeinate by hand."
    kill -TERM "$job" 2>/dev/null
    return 1
  fi
  log "stopping the driver: ${#DRIVER_TREE} process(es) — ${DRIVER_TREE[*]}"
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
  if (( ${#survivors} )); then
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
    local tick; local -a left
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
}

# T202 — `trap release_lock EXIT INT TERM` released the lock and then LET THE
# SCRIPT CARRY ON. Measured under zsh 5.9 against these very bytes: a SIGINT at
# tick 2 of 40 ran release_lock, deleted the LOCK, and the body then executed
# all 38 remaining ticks — every one of them logging lock_present=NO — and the
# script exited **rc=0**. SIGTERM behaved identically. A fire that keeps working
# while holding no lock is precisely how two orchestrators end up in one repo,
# which is the one thing .softhouse/LOCK exists to prevent (and STEP 0 of
# /softhouse-program with it). A handler that cleans up must also TERMINATE.
#
# Disposition, one line of reasoning each:
#   INT  (130) operator interrupt — stop; do not spend hours more after a human
#              asked for the fire to end.
#   TERM (143) launchd unload/shutdown, `launchctl kill`, plain `kill` — same.
#   HUP  (129) session or login shell gone. Untrapped, zsh already terminated on
#              it AND ran the EXIT trap (measured rc=1), so the lock was safe;
#              trapping it only replaces a misleading rc=1 with a truthful 129.
#   QUIT (131) measured: zsh 5.9 IGNORES SIGQUIT in a non-interactive script
#              (untrapped, the subject ran to completion, rc unchanged), so today
#              a SIGQUIT cannot stop a fire at all. An explicit trap DOES fire
#              (measured), which turns a dead letter into a clean stop.
#   KILL       untrappable, by construction. Nothing in-process can help; it is
#              handled OUT of process by lock_holder_is_dead() above.
# `release_lock` is re-entrant-guarded, so the EXIT trap that follows the
# handler's `exit` is a no-op rather than a second git round-trip.
#
# T211 — the handler now STOPS THE DRIVER FIRST, then releases the lock.
# That order is the point: the lock exists to keep two orchestrators out of one
# repo, so releasing it while `claude` is still alive opens exactly the window
# it was written to close. Stopping first costs DRIVER_STOP_GRACE_SECS (5s by
# default, T217-calibrated against a real `claude` — see the constant's own
# comment above) against launchd's ~20s SIGTERM->SIGKILL grace, and against
# the 6h a stranded lock costs the next fire.
#
# T309 — AND THE RECONCILER, WHICH WAS WIRED EXCLUSIVELY TO THE PATH THAT DOES NOT NEED IT.
#
# THE MEASURED DEFECT. T288 built the tasks.json repair and called it from ONE place:
# `run_exit_guard`, in the script's normal tail. `on_signal` released the lock and
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
#   2. reconcile + commit   — the repair. BOUNDED (see the budget arithmetic below), and
#                             run while the LOCK IS STILL ON DISK, so ready-tasks.py's
#                             ancestry check has a lock to check. See the note in the
#                             body: releasing it first was this patch's own first draft
#                             and it silently disarmed that check.
#   3. release_lock         — removes the lock file, stages the deletion, commits, and
#                             makes ONE bounded
#                             push that carries BOTH commits. Deliberately one push, not
#                             two: a second `git_push_bounded` would add another whole
#                             GIT_PUSH_TIMEOUT_SECS to a handler racing a SIGKILL.
#
# THE BUDGET IS DERIVED, NOT PICKED. launchd sends SIGTERM then SIGKILL after its
# ExitTimeOut; the plist (mn.gerege.nbfi.softhouse-program) sets no ExitTimeOut key, so
# the default applies — ~20s [VERIFIED: the plist has no ExitTimeOut; the 20s figure is
# Apple's documented default and is NOT measured here, so SIGNAL_GRACE_SECS is
# overridable]. What is already spent before the reconcile can start is stop_driver's
# DRIVER_STOP_GRACE_SECS (5s, T217-calibrated) plus up to ~2s confirming a SIGKILL
# landed. What must still be affordable AFTER it is release_lock's bounded push
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
# worktrees persist, and the NEXT fire's `run_exit_guard` sweeps them on its way out. So
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
  local job=$!
  wait_bounded "$job" "$budget"
  if kill -0 "$job" 2>/dev/null; then
    log "ERROR: the signal-path reconcile exceeded its ${budget}s budget — killing it so this handler can still release the lock and exit inside launchd's grace. tasks.json was NOT repaired and any in_progress task in it is UNVERIFIED."
    local -a tree
    if driver_tree "$job"; then tree=("${DRIVER_TREE[@]}"); else tree=("$job"); fi
    kill -TERM "${tree[@]}" 2>/dev/null
    /bin/sleep 0.2
    kill -KILL "${tree[@]}" 2>/dev/null
    wait "$job" 2>/dev/null
    # ready-tasks.py writes through `<path>.t288.tmp` + os.replace, so tasks.json itself
    # is intact; only the temp file can be orphaned. Remove it, or the next fire's
    # dirty-tree rescue commits it into the repo as a deliverable.
    rm -f "$REPO/.softhouse/tasks.json.t288.tmp"
    RECON_VERDICT="FAILED — killed at its ${budget}s signal-path budget; state is NOT truthful"
    return 1
  fi
  wait "$job"
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

# Commit whatever the signal-path reconcile changed. NO PUSH: release_lock's single
# bounded push, immediately after, carries this commit with it.
commit_reconcile_result() {
  git add -- ':(top).softhouse/tasks.json' >/dev/null 2>&1
  git diff --cached --quiet -- ':(top).softhouse/tasks.json' 2>/dev/null && {
    log "signal-path reconcile: no change to commit"
    return 0
  }
  if git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \
       commit -q -m "softhouse: wrapper reconciled state after fire $STAMP was signalled (T309)

The driver was killed by a signal, so it never ran STEP 5.5 and never demoted its own
dispatches. A killed worker is dead, not paused. Reconcile: $RECON_VERDICT" >/dev/null 2>&1; then
    log "signal-path reconcile: committed the state correction"
  else
    log "ERROR: the signal-path reconcile's state correction could not be COMMITTED — it exists only in the working tree. The next fire's dirty-tree rescue should pick it up; if it does not, commit it by hand."
  fi
}

on_signal() {
  local sig=$1 rc=$2
  local t0=$(date +%s)
  log "SIG$sig received — stopping the driver, reconciling tasks.json, releasing the lock and TERMINATING (rc=$rc). A fire must never keep working after its lock is gone, and it must never leave in_progress behind for workers it just killed."
  stop_driver

  # THE LOCK STAYS ON DISK UNTIL AFTER THE RECONCILE, AND THAT IS A CORRECTION TO THIS
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

  # The repair, inside a budget derived from what is actually left.
  local elapsed=$(( $(date +%s) - t0 ))
  # The "- 2" is not slack for its own sake: reconcile_bounded's own teardown (SIGTERM,
  # 0.2s, SIGKILL, reap) and commit_reconcile_result's `git commit` both run AFTER the
  # budget is spent and BEFORE release_lock's push starts. Worst case with the defaults:
  # ~1s stopping the driver + 7s reconcile + ~0.5s teardown + ~0.3s commit + 10s push
  # = ~18.8s, inside the ~20s grace. MEASURED wedge run after this correction is in
  # .softhouse/capture/t309-sigterm-reconcile-bypass/wedge.txt.
  local budget=$(( SIGNAL_GRACE_SECS - elapsed - GIT_PUSH_TIMEOUT_SECS - 2 ))
  if (( budget < SIGNAL_RECONCILE_MIN_SECS )); then
    log "WARN: SKIPPING the signal-path reconcile — budget arithmetic leaves ${budget}s (grace ${SIGNAL_GRACE_SECS}s - ${elapsed}s already spent stopping the driver - ${GIT_PUSH_TIMEOUT_SECS}s reserved for the lock-release push - 2s for teardown and commit), below the ${SIGNAL_RECONCILE_MIN_SECS}s minimum. tasks.json is UNREPAIRED and any in_progress task in it is a DEAD dispatch; the next fire must not believe it."
  else
    log "signal-path reconcile: ${budget}s of budget (grace ${SIGNAL_GRACE_SECS}s - ${elapsed}s spent - ${GIT_PUSH_TIMEOUT_SECS}s push reserve - 2s teardown/commit)"
    # Plain assignment, not a `VAR=x func` prefix: zsh's scoping for a prefixed
    # assignment on a SHELL FUNCTION is not the same as on an external command, and a
    # signal handler is not the place to depend on which one this shell implements.
    RECONCILE_DEADLINE_SECS=$budget
    reconcile_bounded "$budget"
    RECONCILE_DEADLINE_SECS=""
    commit_reconcile_result
  fi

  release_lock
  log "SIG$sig handler complete after $(( $(date +%s) - t0 ))s (launchd grace is ~${SIGNAL_GRACE_SECS}s) — exiting rc=$rc"
  exit $rc
}
trap 'on_signal INT  130' INT
trap 'on_signal TERM 143' TERM
trap 'on_signal HUP  129' HUP
trap 'on_signal QUIT 131' QUIT
trap release_lock EXIT

# ------------------------------------------------------------------- driver ---
PROMPT="/softhouse-program

Local fire on Buyan's Mac at $(date -u +%Y-%m-%dT%H:%M:%SZ). Environment facts for THIS fire — treat as given, do not re-probe unless something contradicts them:
- Fineract REFERENCE ORACLE: $ORACLE_STATUS
- PostgreSQL: $PG_STATUS
- Docker: $DOCKER_STATUS
- Fineract source checkout: $FINERACT_SRC (pinned commit of record 426a23544)
- Prohibited-engine ports open: ${PROHIBITED:-none}

DATABASE RULE (non-negotiable, CLAUDE.md): PostgreSQL is the only database, for the reference oracle, the Go module, vector capture and shadow runs alike. Bring the oracle up with the postgresql compose profile only. Oracle Database, MySQL and MariaDB are prohibited — no ojdbc / oracle.jdbc / :1521, no com.mysql.cj / mariadb / go-sql-driver/mysql. Go connects via pgx. 'The oracle' means the Fineract reference implementation, never Oracle Database.

Oracle handling, in this order:
- REACHABLE → prioritise the vector-capture and conformance work that ONLY this local fire can do.
- UNREACHABLE but Docker RUNNING → this is task T1's job, not a reason to park: bring the reference-oracle stack up yourself with the PostgreSQL compose profile (\`docker-compose-postgresql.yml\` / \`config/docker/compose/postgresql.yml\` in $FINERACT_SRC — never the mysql/mariadb compose files), assert driverClassName == org.postgresql.Driver and a jdbc:postgresql:// URL, record the connection facts + Postgres server version + pinned Fineract commit in .softhouse/reference-oracle.md, then continue with vector work. If the stack genuinely cannot be brought up (build failure, image pull failure, port conflict), record exactly what failed in .softhouse/reference-oracle.md and THEN park.
- UNREACHABLE and Docker NOT running → park vector/conformance tasks with reason oracle_unreachable.
Never synthesise a vector you did not observe from the oracle, and never let conformance report PASS when the oracle is down (exit 2 is not a pass). When parked, spend the fire on work that needs no oracle — source analysis, DEC/spec drafts, the Tier-C gap audit, Tier-D corpus mining.

You hold the repo lock at .softhouse/LOCK; the wrapper releases it when you exit. Checkpoint at the ~90% token soft limit per the skill, push .softhouse/ state, and stop cleanly."

# -------------------------------------------------- did this fire get a turn ---
# T288(C). On 2026-08-22 at 23:00 a fire started, was refused by the five-hour quota
# 20 seconds later, exited rc=1 without doing one unit of work, and the wrapper
# reported that BYTE-IDENTICALLY to a driver that crashed mid-run. A whole
# oracle-reaching window was spent on nothing and nothing said so.
#
# The distinction is fully machine-readable in the driver's own event stream, and the
# discriminator is NOT the one the incident write-up assumed. MEASURED over the three
# jsonl streams still on this host:
#   fire-20260822-230001 (quota, never got a turn)
#     rate_limit_event -> .rate_limit_info = {status:"rejected", rateLimitType:"five_hour",
#                         resetsAt:1787414400}      <-- NESTED, not a top-level key
#     assistant events: exactly 1, .message.model == "<synthetic>"
#     result: {subtype:"success", is_error:true, num_turns:1,
#              result:"You've hit your session limit · resets 12am (Asia/Ulaanbaatar)"}
#   fire-20260822-080001 (a NORMAL, productive fire)
#     rate_limit_event statuses: 1 allowed_warning AND 1 **rejected**
#     assistant events: 100 with model claude-opus-5, 6 "<synthetic>"
#
# So "a rejected rate_limit_event appears" is NOT the signal — a healthy fire that
# works until the quota runs out emits one too, and reading it as "never got a turn"
# would mislabel this program's most productive fires. The signal is
# **ZERO assistant events from a real model**. `<synthetic>` is the harness speaking,
# not the model, and it is excluded by name.
#
# jq is used STREAMING (no -s): the largest stream on this host is 7.7 MB and slurping
# it would be the only unbounded-memory step in the wrapper. If jq is absent, or the
# stream is unreadable, this says UNCLASSIFIED — it never guesses a class.
DRIVER_TURN_LINE=""
classify_driver_turns() {
  DRIVER_TURN_LINE="turns UNCLASSIFIED (no event stream on disk)"
  local raw="$LOG_DIR/fire-$STAMP.jsonl"
  [[ -r "$raw" ]] || return 0
  if [[ ! -x /usr/bin/jq ]]; then
    DRIVER_TURN_LINE="turns UNCLASSIFIED (/usr/bin/jq not executable; the stream is at $raw)"
    return 0
  fi
  # ONE jq, NO PIPELINE, and `-n … reduce inputs` rather than `-s`: -s would load the
  # whole stream into memory and a pipeline into wc/tail would put P-57's pipefail
  # hazard inside a classifier (a poisoned rc is indistinguishable from a real one
  # under `set -o pipefail`). jq's own rc is checked directly instead.
  local out rc real rejected resets
  out=$(/usr/bin/jq -nr 'reduce inputs as $e ({r:0,t:"",x:""};
          if ($e.type=="assistant" and (($e.message.model // "") != "<synthetic>"))
            then .r += 1
          elif ($e.type=="rate_limit_event" and (($e.rate_limit_info.status // "") == "rejected"))
            then (.t = ($e.rate_limit_info.rateLimitType // "?")
                  | .x = (($e.rate_limit_info.resetsAt // "?") | tostring))
          else . end)
        | "\(.r)|\(.t)|\(.x)"' "$raw" 2>/dev/null)
  rc=$?
  if (( rc != 0 )) || [[ -z "$out" ]]; then
    DRIVER_TURN_LINE="turns UNCLASSIFIED (jq exited $rc reading $raw) — read the stream by hand before concluding anything about this fire"
    return 0
  fi
  real="${out%%|*}"; rejected="${${out#*|}%%|*}"; resets="${out##*|}"
  [[ "$real" == <0-> ]] || { DRIVER_TURN_LINE="turns UNCLASSIFIED (jq answered %r for the turn count, which is not a number)"; return 0; }
  if (( real == 0 )) && [[ -n "$rejected" ]]; then
    DRIVER_TURN_LINE="**QUOTA: THIS FIRE NEVER GOT A TURN** — 0 model turns, rate limit '$rejected' rejected (resetsAt=$resets). This is NOT a driver crash and nothing in the repo advanced; the window was spent on nothing."
  elif (( real == 0 )); then
    DRIVER_TURN_LINE="**THE DRIVER PRODUCED 0 MODEL TURNS** and no quota rejection was recorded — cause UNKNOWN, read $raw before blaming the driver's logic."
  elif [[ -n "$rejected" ]]; then
    DRIVER_TURN_LINE="$real model turn(s), then rate limit '$rejected' rejected (resetsAt=$resets) — the fire DID work before the quota ended it."
  else
    DRIVER_TURN_LINE="$real model turn(s), no quota rejection recorded"
  fi
}

# ---------------------------------------------------------------- chaining ---
# A fire ends when the driver's CONTEXT fills, not when the work is done. Waiting
# for the next cron slot then wastes hours of an otherwise-idle machine. So chain:
# re-invoke a FRESH driver immediately while there is runnable work, progress is
# being made, and the budget holds. Each iteration is a new context reading the
# same repo state, which is exactly what the next scheduled fire would have been.
CHAIN_MAX="${CHAIN_MAX:-8}"
CHAIN_N=0

run_driver() {
  log "invoking driver (chain iteration $((CHAIN_N+1))/$CHAIN_MAX)"

# ROOT CAUSE OF EVERY LOST LOCAL FIRE (found 2026-08-18 by fire 20260818-230002).
# `claude -p` waits only 600s for background tasks after the driver's final
# response, then TERMINATES them:
#   "Background tasks still running after 600s; terminating.
#    Set CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 to wait indefinitely."
# That exact line appears in fire-20260817-191707, -20260818-080003, -170002 and
# -200001 — i.e. in EVERY fire that stranded work. The diagnosis recorded in
# RESUME.md ("fire-program.sh dispatches and exits without awaiting its workers")
# was WRONG: the driver did await; the harness killed the workers under it.
# An opus worker re-deriving money math or building a capture container routinely
# needs far more than 10 minutes, so the ceiling must be removed, not raised.
export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0
log "background-task wait ceiling: disabled (CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0)"

# Stream progress instead of going dark until the end: raw events land in
# fire-<stamp>.jsonl, a one-line-per-step digest goes to the human log. Without
# this the log shows "invoking driver" and nothing else for hours.
RAW="$LOG_DIR/fire-$STAMP.jsonl"
DIGEST='
  if .type=="assistant" then
    (.message.content[]? | select(.type=="tool_use")
      | "TOOL " + .name + " :: " + ((.input | tostring)[0:160]))
  elif .type=="result" then
    "RESULT " + (.subtype // "?") + " :: " + (((.result // "") | tostring)[0:600])
  elif .type=="system" and .subtype=="init" then "INIT session " + (.session_id // "?")
  else empty end'

# Both 2026-08-18 fires died mid-response with "your computer went to sleep":
# launchd fires it, the Mac idles, the driver is killed with the run mid-flight.
# caffeinate holds off idle/disk/system sleep for exactly the driver's lifetime.
CAFFEINATE=()
[[ -x /usr/bin/caffeinate ]] && CAFFEINATE=(/usr/bin/caffeinate -i -m -s)

# T211 — WHY THE DRIVER IS BACKGROUNDED AND `wait`ed ON, instead of run in the
# foreground. zsh DEFERS a trap until the current FOREGROUND child exits, and
# this fire's foreground child is `claude`, which runs for HOURS. launchd stops
# a job with SIGTERM then SIGKILL, so with a foreground child the SIGKILL strand
# is the NORMAL outcome of stopping a fire, not the exotic one — and a stranded
# fire leaves .softhouse/LOCK on disk, which parks the NEXT fire at STEP 0 for
# up to LOCK_MAX_AGE_SECS (6h) behind a holder that is already dead.
#
# Measured under zsh 5.9 through the real launchd shape, with these very bytes
# and the pre-fix bytes as the control
# [.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T211-probe/]:
#
#   shape                        signal->exit   trap ran?   LOCK        child
#   FOREGROUND (pre-fix)         >45.0s HUNG    NO          STRANDED    ORPHANED
#   background + wait (this)       ~0.2s        YES         released    killed
#
# THREE THINGS `wait` ALONE DOES NOT GIVE YOU, each measured rather than assumed:
#
#   a. THE HANDLER MUST `exit`. `wait` is RESTARTED after a handler that merely
#      returns: in the bg/return cell the handler ran at +1.35s and the shell
#      then went straight back to waiting and had to be SIGKILLed at +20s
#      [waittrap-matrix.txt]. T202 already made every handler terminate, and
#      that is now load-bearing for this fix, not just for the lock.
#   b. THE CHILD MUST BE KILLED. bg/exit exits in 0.130s and still leaves the
#      child running, reparented to pid 1 [waittrap-matrix.txt]. See
#      stop_driver() above; that is why on_signal calls it first.
#   c. `${pipestatus[1]}` DIES. After `wait`, $pipestatus holds ONE element, not
#      the pipeline's three [semantics.txt, S4/S5] — so the old
#      `RC=${pipestatus[1]}` would silently start reporting something that is
#      not the driver's status. The driver's real exit code is therefore written
#      to a file by the `{ … }` group below and read back after the wait.
#
# The `( … ) &` subshell form is deliberate: `$!` of a bare background pipeline
# is its LAST member (jq), while `$!` of `( … ) &` is the subshell that PARENTS
# every member — which is what stop_driver needs as its root [semantics2.txt].
DRIVER_RC_FILE="$LOG_DIR/fire-$STAMP.driver-rc"
rm -f "$DRIVER_RC_FILE"

if [[ -x /usr/bin/jq ]]; then
  ( { "${CAFFEINATE[@]}" "$CLAUDE_BIN" -p "$PROMPT" \
        --permission-mode bypassPermissions \
        --add-dir "$FINERACT_SRC" \
        --output-format stream-json --verbose
      print -r -- $? > "$DRIVER_RC_FILE" } \
    | tee "$RAW" \
    | /usr/bin/jq -r --unbuffered "$DIGEST" 2>/dev/null ) &
  DRIVER_JOB_PID=$!
  log "driver job pid=$DRIVER_JOB_PID — backgrounded; the wrapper now sits in \`wait\`, so a SIGTERM is handled in a fraction of a second instead of waiting out the driver"
  wait "$DRIVER_JOB_PID"
  DRIVER_WAIT_RC=$?
  DRIVER_JOB_PID=0
  log "raw event stream: $RAW"
else
  ( { "${CAFFEINATE[@]}" "$CLAUDE_BIN" -p "$PROMPT" \
        --permission-mode bypassPermissions \
        --add-dir "$FINERACT_SRC" \
        --output-format text
      print -r -- $? > "$DRIVER_RC_FILE" } ) &
  DRIVER_JOB_PID=$!
  log "driver job pid=$DRIVER_JOB_PID — backgrounded; the wrapper now sits in \`wait\`, so a SIGTERM is handled in a fraction of a second instead of waiting out the driver"
  wait "$DRIVER_JOB_PID"
  DRIVER_WAIT_RC=$?
  DRIVER_JOB_PID=0
fi

# Recover the DRIVER's own exit code — not the job's, which is the last pipeline
# member's (measured: a `{ exit 37 } | cat | cat` job waits rc=0 while the file
# correctly holds 37 [semantics2.txt, S9]).
# POLARITY: fail-CLOSED. The chain loop below stops on a non-zero RC and chains
# a fresh driver on a zero one, so "we could not read the driver's status" must
# never be spelled the same way as "the driver succeeded".
if [[ -r "$DRIVER_RC_FILE" ]] && [[ "$(<"$DRIVER_RC_FILE")" == <0-255> ]]; then
  RC=$(<"$DRIVER_RC_FILE")
elif (( DRIVER_WAIT_RC != 0 )); then
  RC=$DRIVER_WAIT_RC
  log "WARN: driver rc file $DRIVER_RC_FILE is missing or unreadable — falling back to the job's own status rc=$RC"
else
  RC=70
  log "ERROR: driver rc file $DRIVER_RC_FILE is missing or unreadable AND the job reported success. REFUSING to record a clean driver exit this fire did not observe — reporting rc=70 so the chain STOPS instead of launching a fresh driver on an unknown outcome."
fi

  classify_driver_turns
  log "driver exited rc=$RC — $DRIVER_TURN_LINE"
}

# -------------------------------------------- T288: is ANYONE still working here ---
# The reconcile below rewrites tasks.json, so it must first establish — POSITIVELY —
# that no live session owns those tasks. This is the only leg of the fix that can hurt
# if it is wrong, so it is the only one that is allowed to say "I don't know".
#
# WHAT A LIVE WORKER ACTUALLY LOOKS LIKE, measured on this host during a live fire with
# six workers dispatched (`/bin/ps -Ao pid=,ppid=,command=`, 2026-08-23):
#   * there is NO process per worker. A subagent is in-process inside `claude`; the
#     entire fire is ONE `claude` (pid 28980, caffeinate exec'd it in place) plus its
#     assertion-holder child. Any design that looked for a process per task would have
#     found nothing and demoted everything.
#   * so worker liveness == liveness of the SESSION that owns them, and the session is
#     identifiable by its cwd:
#         lsof -a -d cwd -p 28980 -Fn  ->  n/Users/buv/gerege-nbfi        (IN the repo)
#         lsof -a -d cwd -p 1207  -Fn  ->  n/Users/buv                    (NOT in it)
#     pid 1207 is an unrelated interactive `claude` that was running at the same time.
#     A blanket "any claude is alive => refuse" would have gone permanently inert
#     against it; reading the cwd tells the two apart, and that was measured, not assumed.
#
# By the time this runs the fire's OWN driver has been `wait`ed on (or killed by
# stop_driver), so it is gone and is skipped by the kill -0 leg below. What is left is
# exactly the case that must be protected: somebody ELSE working in this checkout.
#
# POLARITY: fail-CLOSED, three-valued.
#   0 = a live foreign session WAS found            -> caller must not reconcile
#   1 = none found, and every candidate was decided -> caller may reconcile
#   2 = could not establish (no lsof, no ps, a live claude whose cwd would not read)
#                                                    -> caller must not reconcile
# Only 1 authorises the rewrite. "I could not tell" is never spelled like "nobody".
LSOF_BIN="${LSOF_BIN:-/usr/sbin/lsof}"
FOREIGN_SESSIONS=""
foreign_live_session_in_repo() {
  FOREIGN_SESSIONS=""
  [[ -x "$LSOF_BIN" ]] || { FOREIGN_SESSIONS="$LSOF_BIN is not executable — cwd of a live session cannot be read"; return 2; }
  local snap
  snap=$(/bin/ps -Ao pid=,stat=,command= 2>/dev/null) || { FOREIGN_SESSIONS="/bin/ps did not answer"; return 2; }
  local -a lines; lines=(${(f)snap})
  (( ${#lines} > 1 )) || { FOREIGN_SESSIONS="/bin/ps returned a one-line table, which is not a table"; return 2; }
  local repo_phys="${REPO:A}"        # :A resolves symlinks — lsof reports physical paths
  # EVERY local is declared ONCE, here. Measured under zsh 5.9: `local x` inside a loop
  # body, when x already exists at this scope, does not re-declare it — it PRINTS
  # `x=<value>` to stdout (`zsh -c 'f(){ local a; for a in x y; do local a; done }; f'`
  # emits `a=x` / `a=y`). The first draft of this function declared `local l` inside the
  # lsof loop and leaked a line of raw lsof output into the fire log. Caught by driving
  # it, not by reading it.
  local line pid st first cwd lsofout l checked=0 unknown=0 found=0
  local -a f
  for line in $lines; do
    f=(${=line})
    (( ${#f} >= 3 )) || continue
    pid=$f[1]; st=$f[2]; first=$f[3]
    [[ "$pid" == <1-> ]] || continue
    (( pid == $$ )) && continue
    [[ "${first:t}" == claude ]] || continue      # the CLI, not /Applications/Claude.app
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
    (( checked++ ))
    lsofout=$("$LSOF_BIN" -w -a -d cwd -p "$pid" -Fn 2>/dev/null)
    cwd=""
    for l in ${(f)lsofout}; do
      [[ "$l" == n* ]] && cwd="${l#n}"
    done
    # EVERY expansion here is BRACED. Unbraced `$pid:cwd=` applies zsh's `:c` history
    # modifier to $pid and `$cwd:elsewhere` applies `:e`, which silently turned this
    # evidence string into `pid=28980wd=lsewhere` on the first drive — the evidence line
    # for a fail-closed guard, quietly corrupted by the shell. Measured, then fixed.
    if [[ -z "$cwd" ]]; then
      if kill -0 "$pid" 2>/dev/null; then
        FOREIGN_SESSIONS="${FOREIGN_SESSIONS} [pid ${pid} cwd UNREADABLE]"
        (( unknown++ ))
      fi
      continue
    fi
    if [[ "$cwd" == "$repo_phys" || "$cwd" == "$repo_phys"/* ]]; then
      FOREIGN_SESSIONS="${FOREIGN_SESSIONS} [pid ${pid} cwd ${cwd} IN-REPO]"
      (( found++ ))
    else
      FOREIGN_SESSIONS="${FOREIGN_SESSIONS} [pid ${pid} cwd ${cwd} elsewhere]"
    fi
  done
  FOREIGN_SESSIONS="claude processes examined=$checked in-repo=$found unreadable=$unknown --$FOREIGN_SESSIONS"
  (( found ))   && return 0
  (( unknown )) && return 2
  return 1
}

# T309 — THIS DEFINITION MOVED OUT OF `run_exit_guard`, AND THAT WAS NOT COSMETIC.
# T288 defined `reconcile_tasks_json` INSIDE run_exit_guard, twenty lines above its only
# call. A zsh function body is not created until the enclosing function RUNS, so before
# the first driver had exited the name did not exist at all — and `on_signal` fires from
# the moment the traps are installed, which is BEFORE that. So the brief's finding is
# stronger than 'on_signal never calls the reconciler': on the first chain iteration it
# could not have called it, because there was nothing to call. It lives at top level now,
# beside `foreign_live_session_in_repo` which it depends on, so both call sites reach the
# same bytes and neither is ordering-dependent.
#
# ---------------------------------------------- T288: repair the state, don't warn ---
# THE DEFECT THIS REPLACES. Everything below used to be one WARN. Fire 20260822-140002
# ended its turn with four live workers (T271/T283/T285/T286); all four died with it,
# all four stayed `in_progress`, and RESUME.md was never rewritten. At 23:00 the next
# fire was refused by the quota 20 seconds in, and at 23:00:32 this wrapper printed
#     WARN: exit-protocol violation — .softhouse/RESUME.md predates this fire's start;
#           the next fire may act on stale state. Review it by hand.
# IT WAS RIGHT AND IT DID NOTHING. "Review it by hand" has no reader: the only thing
# that reads a fire log is the next fire, and the next fire reads RESUME.md and
# tasks.json instead. Two fires later the state was still lying and the 08:00 fire had
# to reconstruct the truth from six branch names and two log files.
#
# REPAIR, NOT REFUSE — and here is what was rejected. A louder refusal was the obvious
# alternative: exit non-zero, or drop a marker file the next fire is told to read.
# Both fail for the same reason the WARN failed. A non-zero exit is read by launchd,
# which does nothing with it; the next fire still opens a tasks.json that says four
# workers are busy. A marker file needs (a) somebody to remember to read it and (b)
# somebody to remember to clear it — two remembered obligations, which is P-45's exact
# shape: "a guard that only works when someone remembers to run it enforces nothing."
# So the wrapper edits the two artefacts the next fire actually reads, and both repairs
# are SELF-CLEARING by construction: a demoted task leaves `needs_retry` when it is
# retried, and the banner disappears the moment a driver rewrites RESUME.md per STEP
# 5.5.4. Nothing new has to be remembered by anyone.
#
# The refusal path still exists — but only where a repair could be WRONG, i.e. when a
# live session might own those tasks. There the wrapper says so in the log AND leaves
# the state untouched, because demoting a live worker's task would get it dispatched
# twice.
RECON_VERDICT="not attempted"
reconcile_tasks_json() {
  local -a pairs; pairs=("$@")
  if [[ ! -f .softhouse/tasks.json ]]; then
    RECON_VERDICT="no tasks.json in this repo"
    log "reconcile: $RECON_VERDICT"
    return 0
  fi
  local probe_rc
  foreign_live_session_in_repo; probe_rc=$?
  case $probe_rc in
    0)
      RECON_VERDICT="REFUSED — a live session is working in this repo ($FOREIGN_SESSIONS)"
      log "WARN: NOT reconciling tasks.json — $FOREIGN_SESSIONS. Some other session may own the in_progress tasks, and demoting a LIVE worker's task would get it dispatched twice. State left exactly as found; if that session is not in fact working, fix tasks.json by hand."
      return 1 ;;
    2)
      RECON_VERDICT="REFUSED — worker liveness could not be established ($FOREIGN_SESSIONS)"
      log "ERROR: NOT reconciling tasks.json — could not establish whether a live session owns it ($FOREIGN_SESSIONS). REFUSING to rewrite state on a guess. Any in_progress task in tasks.json is UNVERIFIED; check it by hand before the next fire trusts it."
      return 1 ;;
  esac
  log "reconcile: no live session owns this repo — $FOREIGN_SESSIONS"
  local -a args; args=(--reconcile --fire "$STAMP" --repo "$REPO")
  # T309: the NORMAL tail leaves this empty (nothing is waiting on the wrapper there, and
  # a budget imposed for no reason is a way to lose evidence). The SIGNAL path sets it,
  # because it is racing launchd's SIGTERM->SIGKILL grace. Two call sites, two budgets,
  # and the difference is deliberate rather than a default nobody chose.
  [[ -n "${RECONCILE_DEADLINE_SECS:-}" ]] && args+=(--deadline-secs "$RECONCILE_DEADLINE_SECS")
  local p; for p in "${pairs[@]}"; do args+=(--rescue "$p"); done
  local out rc
  out=$(/usr/bin/python3 "$SCRIPT_DIR/ready-tasks.py" "${args[@]}" 2>&1)
  rc=$?
  local l; for l in ${(f)out}; do log "reconcile| $l"; done
  case $rc in
    0) RECON_VERDICT="ran clean (see the reconcile| lines in $LOG)" ;;
    3) RECON_VERDICT="FAILED — tasks.json could not be read or written; state is NOT truthful" ;;
    4) RECON_VERDICT="REFUSED by ready-tasks.py and NOTHING was changed — either the caller could not be established as the lock holder, or it ran in \`in_session\` mode and no in_progress task could be proven to belong to a dead fire (T309). Read the reconcile| lines." ;;
    *) RECON_VERDICT="ready-tasks.py exited $rc (unexpected)" ;;
  esac
  (( rc == 0 )) || log "ERROR: reconcile did not complete — $RECON_VERDICT"
  return 0
}

# ------------------------------------------------------- exit-protocol guard ---
run_exit_guard() {
# Reset per iteration: a value left over from the previous chain iteration would make
# the chain judge THIS driver's progress against a sha from the last one.
GUARD_HEAD_BEFORE_REPAIR=""
# The driver is required to checkpoint on EVERY exit path (skill STEP 5.5). It has
# been observed exiting rc=0 mid-run with deliverables uncommitted and RESUME.md
# stale, which makes the work invisible to the next fire. Detect and rescue.
# T190: no grep and no pipeline in this guard. git's own pathspec exclusion does the
# filtering — the idiom the rescue's own `git add` below already uses — and git's exit
# status is CHECKED instead of swallowed by `|| true`.
#   Why the PIPELINE had to go, not just the `|| true`: this script runs
#   `set -uo pipefail` WITHOUT `-e` (line 17). When git fails it prints nothing, so
#   the downstream filter selects nothing and exits 1, and zsh's pipefail reports the
#   RIGHTMOST non-zero status — rc=1, byte-identical to a genuinely clean tree
#   (measured: git rc=128 + filter rc=1 -> pipeline rc=1, pipestatus=(128 1)).
#   A pipeline here therefore CANNOT distinguish "clean" from "git broke", which is
#   the fail-open: the guard reported the reassuring answer when it had learned nothing.
#   Why `:(top)`: a bare `-- .` pathspec is cwd-relative and would silently narrow the
#   guard to a subdirectory; `:(top)` anchors both pathspecs at the repo root whatever
#   cwd is, so the guard does not depend on the `cd "$REPO"` at line 49.
#   Dropping grep also removes every byte-class, locale, binary-detection and
#   grep-implementation question from a load-bearing guard (T189, P-58).
DIRTY=$(git status --porcelain -- ':(top)' ':(top,exclude).softhouse/LOCK')
GS_RC=$?
if (( GS_RC != 0 )); then
  log "ERROR: exit-protocol guard could not read git status (rc=$GS_RC) — REFUSING to conclude the tree is clean. No rescue attempted (git is not answering); treat this fire's deliverables as UNVERIFIED and inspect the tree by hand."
elif [[ -n "$DIRTY" ]]; then
  log "WARN: exit-protocol violation — driver left uncommitted work:"
  # No `| head` here either: under pipefail an early-exiting consumer poisons the
  # pipeline status (measured rc=141 at 50k lines), which is P-57's hazard sitting
  # inside the very guard this task is de-fanging. zsh slice, byte-identical output.
  local -a DIRTY_LINES; DIRTY_LINES=("${(@f)DIRTY}")
  print -rl -- "${(@)DIRTY_LINES[1,20]}"
  # T202: `:(top)`-anchored, so the rescue measures the same thing the `git
  # status` above it measures. The old `-- . ':!.softhouse/LOCK'` was
  # CWD-RELATIVE and therefore ASYMMETRIC with the `:(top)` status T190 added —
  # worse than the pre-T190 state, because the two disagreed about their subject.
  # Measured from a subdirectory of a scratch repo: status listed BOTH stranded
  # deliverables, `git add` staged NOTHING, HEAD did not move, and the guard
  # still logged `rescued: committed the leftovers`. Both rcs are now CHECKED, so
  # "rescued" is printed only after a commit that actually happened.
  # POLARITY: fail-CLOSED — it now says "NOTHING was rescued" instead of claiming
  # a rescue it did not perform.
  git add -A -- ':(top)' ':(top,exclude).softhouse/LOCK' >/dev/null 2>&1
  ADD_RC=$?
  if (( ADD_RC != 0 )); then
    log "ERROR: exit-protocol rescue could not stage the leftovers (git add rc=$ADD_RC) — NOTHING was rescued. The paths listed above are still uncommitted; inspect the tree by hand."
  else
    git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \
        commit -q -m "softhouse: rescue uncommitted deliverables left by fire $STAMP (exit-protocol violation)" >/dev/null 2>&1
    COMMIT_RC=$?
    if (( COMMIT_RC == 0 )); then
      log "rescued: committed the leftovers so the next fire can see them"
    else
      log "ERROR: exit-protocol rescue staged the leftovers but the COMMIT FAILED (git commit rc=$COMMIT_RC) — NOTHING was rescued. The paths listed above are still uncommitted; inspect the tree by hand."
    fi
  fi
fi

# The main tree is not the only place work hides. A worker killed mid-flight
# (the fire exiting while its background agents still run) leaves everything
# uncommitted INSIDE its worktree, where the main-tree sweep above cannot see it.
# Observed 2026-08-18 17:22: three workers killed, 4,482 insertions stranded.
# T202: enumerate into an ARRAY with git's own status CHECKED. The old
# `for W in $(git worktree list --porcelain | awk ... | tail -n +2)` discarded
# the pipeline's rc entirely, so a failing `git worktree list` produced ZERO
# iterations that were indistinguishable from "no linked worktrees" — P-35, a
# check that inspected nothing reporting a pass. Dropping `$(...)` word-splitting
# also stops a worktree path containing a space from being split into two bogus
# paths, and dropping awk/tail removes two more programs from a load-bearing
# guard (P-33/P-58) — zsh's own `${(@f)}` and array slice do the same work.
# POLARITY: fail-CLOSED.
WT_RAW=$(git worktree list --porcelain)
WT_RC=$?
local -a WT_PATHS WT_BRANCHES WT_LOCKED; WT_PATHS=(); WT_BRANCHES=(); WT_LOCKED=()
if (( WT_RC != 0 )); then
  log "ERROR: worktree sweep could not enumerate worktrees (git worktree list rc=$WT_RC) — REFUSING to conclude there is nothing to rescue. Any worker deliverables still sitting in a linked worktree are UNVERIFIED; inspect them by hand."
else
  # T213: parse branch/detached/locked lines alongside `worktree` lines, in
  # lockstep, so WT_BRANCHES[i]/WT_LOCKED[i] are always the branch/lock-state
  # for WT_PATHS[i] — needed below by the prune sweep (T190/T202's rescue loop
  # only ever needed the path). A `worktree` line always starts a new
  # porcelain record, so it both flushes nothing (there's nothing to flush —
  # each field just overwrites in place) and pushes a placeholder onto
  # WT_BRANCHES/WT_LOCKED that a following `branch`/`detached`/`locked` line
  # then fills in — leaving all three arrays the same length and aligned by
  # construction, not by a second pass. `locked` is captured because
  # fire-program's own live-agent worktrees carry it (measured on the live
  # repo, T213 handoff) — a currently-running agent's worktree must never be
  # a prune candidate regardless of what its branch looks like.
  local WT_LINE
  for WT_LINE in "${(@f)WT_RAW}"; do
    if [[ "$WT_LINE" == 'worktree '* ]]; then
      WT_PATHS+=("${WT_LINE#worktree }")
      WT_BRANCHES+=("")
      WT_LOCKED+=("")
    elif [[ "$WT_LINE" == 'branch refs/heads/'* ]]; then
      (( ${#WT_BRANCHES} > 0 )) && WT_BRANCHES[${#WT_BRANCHES}]="${WT_LINE#branch refs/heads/}"
    elif [[ "$WT_LINE" == 'detached' ]]; then
      (( ${#WT_BRANCHES} > 0 )) && WT_BRANCHES[${#WT_BRANCHES}]="(detached)"
    elif [[ "$WT_LINE" == 'locked' ]]; then
      (( ${#WT_LOCKED} > 0 )) && WT_LOCKED[${#WT_LOCKED}]="no reason given"
    elif [[ "$WT_LINE" == 'locked '* ]]; then
      (( ${#WT_LOCKED} > 0 )) && WT_LOCKED[${#WT_LOCKED}]="${WT_LINE#locked }"
    fi
  done
  # entry 1 is the main tree, which the sweep above has already covered
  if (( ${#WT_PATHS} > 0 )); then
    WT_PATHS=("${(@)WT_PATHS[2,-1]}")
    WT_BRANCHES=("${(@)WT_BRANCHES[2,-1]}")
    WT_LOCKED=("${(@)WT_LOCKED[2,-1]}")
  fi
fi

# T288: indexed, so the branch the worktree was ON is available beside its path. The
# sweep already knew it (WT_BRANCHES was parsed in lockstep by T213) and threw it away
# at the moment of rescue — which is exactly the fact the 08:00 fire had to reconstruct
# by hand from six `rescued-agent-*` names. Kept now as `<task-branch>=<rescue-branch>`
# pairs and handed to the reconciler, which writes it into the task's note.
local -a RESCUE_PAIRS; RESCUE_PAIRS=()
local WI
for (( WI = 1; WI <= ${#WT_PATHS}; WI++ )); do
  W="${WT_PATHS[$WI]}"
  [[ -d "$W" ]] || continue
  # T202 — THE UNFIXED TWIN OF T190's FAIL-OPEN, twenty lines below its patch and
  # inside the same function. `WD=$(... | wc -l | tr -d ' ')`: `wc -l` prints `0`
  # on empty input, so when git FAILED the guard read the worktree as CLEAN and
  # silently `continue`d — ABANDONING EXACTLY THE STRANDED DELIVERABLES the
  # comment three lines above it was written for (2026-08-18: three workers
  # killed, 4,482 insertions stranded, an entire DEC-1 retry among them).
  # Unlike T190's site the rc here IS recoverable and was merely never read:
  # measured git=128, wc=0, tr=0, so `pipefail` yields the pipeline rc=128
  # [.softhouse/reviews/t202-probe/red-Ta.txt]. So take the status directly and
  # CHECK it — and count the paths with a zsh array instead of `wc`, which
  # deletes the `0`-on-failure ambiguity at its source rather than masking it.
  # POLARITY: fail-CLOSED — a broken worktree is now loudly UNVERIFIED, never
  # quietly clean. A genuinely clean worktree still costs one line of nothing.
  WS=$(git -C "$W" status --porcelain)
  WS_RC=$?
  if (( WS_RC != 0 )); then
    log "ERROR: worktree sweep could not read git status for $W (rc=$WS_RC) — REFUSING to treat it as clean. NOT rescued, because git is not answering there; treat anything inside it as UNVERIFIED and inspect it by hand."
    continue
  fi
  [[ -n "$WS" ]] || continue
  local -a WS_LINES; WS_LINES=("${(@f)WS}")
  WD=${#WS_LINES}
  WN=$(basename "$W")
  # T202: a git ref may not contain a space (or ~ ^ : ? * [ \ or a control char),
  # so a worktree whose path has one produced a branch name `git checkout -b`
  # rejects — the sweep then logged "rescuing to ..." and rescued NOTHING
  # [measured: scenario S6, 0 branches created]. Fold anything outside the safe
  # set to `-`; every real worktree name (`agent-<hex>`) is unchanged by this.
  WN="${WN//[^A-Za-z0-9._-]/-}"
  WB="softhouse/rescued-$WN-$STAMP"
  log "WARN: worktree $WN left $WD uncommitted path(s) — rescuing to $WB"
  git -C "$W" checkout -q -b "$WB" 2>/dev/null
  git -C "$W" add -A >/dev/null 2>&1
  git -C "$W" -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \
      commit -q -m "RESCUED: WIP from a worker that never signalled done (fire $STAMP)

Committed by the orchestrator's worktree sweep. Completeness UNVERIFIED — no handoff was written. Treat as partial until re-reviewed." >/dev/null 2>&1
  log "rescued $WN -> $WB"
  # The worktree's PRIOR branch is what a task records in tasks.json .branch. A
  # worktree still on its harness default (`worktree-agent-<hex>`) or detached has no
  # task to pair with, and is recorded as a rescue with no owner rather than guessed at.
  local PRIOR="${WT_BRANCHES[$WI]}"
  if [[ -n "$PRIOR" && "$PRIOR" != "(detached)" && "$PRIOR" != "$WB" ]]; then
    RESCUE_PAIRS+=("$PRIOR=$WB")
    log "rescue pairing: task branch $PRIOR -> $WB"
  else
    log "rescue pairing: $WB has NO task branch to pair with (worktree was on '${PRIOR:-none}') — it will not be named in any task note"
  fi
done

# T213: the sweep above walks EVERY worktree on EVERY fire, so its cost grows
# without bound as merged worktrees pile up. The stored task description said
# 84; the driver re-measured 36 at this task's dispatch (2026-08-22); this
# worker re-measured again, later the same day, at 43 (`git worktree list |
# grep -c "agent-"`, run from this worktree). Three different counts within
# one day, on one fire — P-69: a measured count's shelf life is shorter than
# a busy fire. Re-measure at read time; do not carry any of these numbers
# forward as current.
#
# Prune the ones that are done with: MERGED into main AND CLEAN, both — plus
# the two extra fail-closed guards `wt_prune_check` also enforces (never a
# `locked` worktree; never the harness's own never-repurposed default branch
# for that worktree) after both were needed to correctly classify live
# worktrees found during this task's own testing — see lib-worktree-prune.zsh
# for why. Reuses WT_PATHS/WT_BRANCHES/WT_LOCKED from the enumeration above
# (main tree already excluded, aligned index-for-index). The decision itself
# lives in wt_prune_check() (lib-worktree-prune.zsh) so it is fixture-tested
# in isolation — see that file's header for the polarity discipline. This
# loop's only job is to act on a PRUNE verdict; it does not re-derive one.
#
# `git worktree remove` (no --force) is itself a THIRD, independent clean
# check — git refuses if it finds modifications we somehow missed, or if the
# worktree is locked — so a race between our check and this call fails closed
# too, not silently.
local WT_PRUNED=0 WT_KEPT=0
local i W BR WLK VERDICT VERDICT_RC RM_OUT RM_RC
for (( i = 1; i <= ${#WT_PATHS}; i++ )); do
  W="${WT_PATHS[$i]}"
  BR="${WT_BRANCHES[$i]}"
  WLK="${WT_LOCKED[$i]}"
  VERDICT=$(wt_prune_check "$W" "$BR" main "$WLK")
  VERDICT_RC=$?
  if (( VERDICT_RC == 0 )); then
    RM_OUT=$(git worktree remove "$W" 2>&1)
    RM_RC=$?
    if (( RM_RC == 0 )); then
      log "pruned: removed worktree $W (branch $BR was merged into main, clean)"
      if git branch -d "$BR" >/dev/null 2>&1; then
        log "pruned: deleted merged branch $BR"
      else
        log "WARN: worktree $W removed but branch $BR could not be deleted (already gone, or checked out elsewhere) — harmless, branch is merged"
      fi
      WT_PRUNED=$((WT_PRUNED+1))
    else
      log "WARN: $W was classified PRUNE but 'git worktree remove' refused (rc=$RM_RC) — NOT pruned, left in place: $RM_OUT"
      WT_KEPT=$((WT_KEPT+1))
    fi
  else
    log "keep: $W — $VERDICT"
    WT_KEPT=$((WT_KEPT+1))
  fi
done
log "worktree prune sweep: pruned=$WT_PRUNED kept=$WT_KEPT"

reconcile_tasks_json "${RESCUE_PAIRS[@]}"

# RESUME.md must have been rewritten during this fire, or a fresh session resumes
# from a stale manifest — worse than none, because it looks authoritative. So when it
# was NOT rewritten, the wrapper says so IN THE FILE, at the top, where the next fire
# cannot read past it. mtime is the primary test; the banner's own presence is the
# second, because a chained iteration re-runs this after the first one already touched
# the mtime, and a driver that rewrote RESUME.md properly deletes the banner with it.
STALE_BANNER_OPEN='<!-- T288-WRAPPER-BANNER — written by fire-program.sh, not by a driver -->'
STALE_BANNER_CLOSE='<!-- /T288-WRAPPER-BANNER -->'
if [[ -f .softhouse/RESUME.md ]]; then
  RESUME_MTIME=$(/usr/bin/stat -f %m .softhouse/RESUME.md 2>/dev/null || print 0)
  RESUME_BODY=$(<.softhouse/RESUME.md)
  RESUME_STALE=0
  (( RESUME_MTIME < FIRE_START_EPOCH )) && RESUME_STALE=1
  [[ "$RESUME_BODY" == *"$STALE_BANNER_CLOSE"* ]] && RESUME_STALE=1
  if (( RESUME_STALE )); then
    log "WARN: exit-protocol violation — .softhouse/RESUME.md was not rewritten by this fire. Stamping the file itself so the next fire reads the correction before the stale table."
    # Strip any banner this wrapper wrote earlier, so chained iterations replace rather
    # than stack. Shortest-prefix removal through the close marker; zsh builtin, no sed.
    [[ "$RESUME_BODY" == "$STALE_BANNER_OPEN"* ]] && RESUME_BODY="${RESUME_BODY#*$STALE_BANNER_CLOSE}"
    RESUME_BODY="${RESUME_BODY#$'\n'}"
    {
      print -r -- "$STALE_BANNER_OPEN"
      print -r -- "> ## STALE — this manifest was NOT rewritten by fire \`$STAMP\`, which ended $(date -u +%Y-%m-%dT%H:%M:%SZ)."
      print -r -- ">"
      print -r -- "> Everything below predates that fire, so its task table, its \"next action\" and its"
      print -r -- "> pause reason are all claims about a world that has moved. The driver did not reach"
      print -r -- "> STEP 5.5, which is why a shell script is writing this."
      print -r -- ">"
      print -r -- "> - driver outcome: rc=\`$RC\` — $DRIVER_TURN_LINE"
      print -r -- "> - tasks.json reconcile: $RECON_VERDICT"
      print -r -- "> - a task shown below as \`in_progress\` is a DEAD dispatch unless the reconcile line"
      print -r -- ">   above says it was refused; read \`tasks.json\` notes, not this table."
      print -r -- "> - fire log: \`$LOG\`"
      print -r -- ">"
      print -r -- "> This banner is not maintained by anyone. It disappears when a driver rewrites"
      print -r -- "> RESUME.md per STEP 5.5.4, and it comes back on any fire that fails to."
      print -r -- "$STALE_BANNER_CLOSE"
      print -r -- ""
      print -r -- "$RESUME_BODY"
    } > .softhouse/RESUME.md.t288.tmp
    if [[ -s .softhouse/RESUME.md.t288.tmp ]]; then
      mv -f .softhouse/RESUME.md.t288.tmp .softhouse/RESUME.md
      log "stamped .softhouse/RESUME.md with the staleness banner"
    else
      rm -f .softhouse/RESUME.md.t288.tmp
      log "ERROR: refused to replace RESUME.md with an empty file — the banner was NOT written and the stale manifest stands. Inspect it by hand."
    fi
  fi
fi

# Commit whatever the two repairs above changed. Separate from the deliverable rescue
# commit at the top of this guard: that one is worker output, this one is the wrapper
# correcting the record, and a postmortem should be able to tell them apart.
#
# GUARD_HEAD_BEFORE_REPAIR — A REGRESSION THIS FIX WOULD OTHERWISE HAVE INTRODUCED,
# found by driving it. The chain loop stops when an iteration produces NO commits
# ("nothing advanced"). A wrapper that now commits a repair on every exit would satisfy
# that test forever: the banner carries the fire's end timestamp, so it differs every
# iteration, so HEAD always moves, so a driver that does nothing eight times running
# would be re-invoked all eight times. The chain must judge the DRIVER's progress, so
# it is handed the sha from BEFORE the wrapper's own correction.
GUARD_HEAD_BEFORE_REPAIR=$(git rev-parse HEAD 2>/dev/null) || GUARD_HEAD_BEFORE_REPAIR=""
git add -- ':(top).softhouse/tasks.json' ':(top).softhouse/RESUME.md' >/dev/null 2>&1
if ! git diff --cached --quiet -- ':(top).softhouse/tasks.json' ':(top).softhouse/RESUME.md' 2>/dev/null; then
  git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \
      commit -q -m "softhouse: wrapper reconciled state after fire $STAMP (exit-protocol enforcement)

The driver was already gone; a killed worker is dead, not paused, so any task still
claiming in_progress was demoted to needs_retry with the WIP evidence in its note.
Driver: rc=$RC — $DRIVER_TURN_LINE
Reconcile: $RECON_VERDICT" >/dev/null 2>&1 \
    && log "committed the wrapper's state correction" \
    || log "ERROR: the wrapper's state correction could not be COMMITTED — it exists only in the working tree and the next fire will not see it. Commit it by hand."
fi

  git push -q origin main 2>/dev/null || log "WARN: could not push after exit-protocol guard"
}

# --------------------------------------------------------------- chain loop ---
while (( CHAIN_N < CHAIN_MAX )); do
  HEAD_BEFORE=$(git rev-parse HEAD)
  run_driver
  run_exit_guard
  CHAIN_N=$((CHAIN_N+1))

  (( RC != 0 )) && { log "chain: stopping — driver exited rc=$RC"; break; }

  # No commits this iteration means the driver found nothing to advance. One more
  # attempt would repeat it; the next scheduled fire can try with fresh state.
  # T288: measured against the sha from before the wrapper's OWN state-correction
  # commit, so the wrapper repairing a lie is never mistaken for the driver making
  # progress. Falls back to HEAD when the guard did not reach that point, which is the
  # pre-T288 behaviour and errs towards chaining rather than towards stopping early.
  HEAD_AFTER="${GUARD_HEAD_BEFORE_REPAIR:-$(git rev-parse HEAD)}"
  if [[ "$HEAD_AFTER" == "$HEAD_BEFORE" ]]; then
    log "chain: stopping — iteration produced no commits (nothing advanced)"
    break
  fi

  # Program finished, or every remaining task is blocked on a human.
  if /usr/bin/python3 - <<'PY'
import json,sys
try:
    prog=json.load(open('.softhouse/program.json'))
    if prog.get('status')=='complete': sys.exit(0)
    tasks=json.load(open('.softhouse/tasks.json'))['tasks']
    live=[t for t in tasks if t.get('status') not in
          ('done','parked','rejected','superseded','done_partial','approved')
          and t.get('executor')!='user']
    sys.exit(0 if not live else 1)
except Exception:
    sys.exit(1)
PY
  then
    log "chain: stopping — no runnable work left (program complete or all remaining work is a user gate)"
    break
  fi

  log "chain: work remains and the last iteration advanced — starting the next driver immediately"
done

log "chain finished after $CHAIN_N iteration(s)"
exit $RC
