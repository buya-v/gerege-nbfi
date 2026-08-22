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

cat > "$LOCK" <<EOF
{
  "holder": "local-launchd",
  "host": "$(hostname -s)",
  "pid": $$,
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "log": "$LOG",
  "oracle": "$ORACLE_STATUS",
  "postgres": "$PG_STATUS"
}
EOF
git add -f "$LOCK" >/dev/null 2>&1
git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" commit -q -m "softhouse: local fire lock ($STAMP)" >/dev/null 2>&1
git push -q origin main 2>/dev/null || log "WARN: could not push lock — cloud fire may not see it"

LOCK_RELEASED=0
release_lock() {
  (( LOCK_RELEASED )) && return
  cd "$REPO" || return
  rm -f "$LOCK"
  LOCK_RELEASED=1
  # Stage ONLY the lock's deletion — the driver commits its own state changes.
  git add -A -- "$LOCK" >/dev/null 2>&1
  git diff --cached --quiet && { log "lock already released"; return; }
  git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" commit -q -m "softhouse: release local fire lock ($STAMP)" >/dev/null 2>&1
  git push -q origin main 2>/dev/null || log "WARN: could not push lock release"
  log "lock released"
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
on_signal() {
  local sig=$1 rc=$2
  log "SIG$sig received — releasing the lock and TERMINATING (rc=$rc). A fire must never keep working after its lock is gone."
  release_lock
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

if [[ -x /usr/bin/jq ]]; then
  "${CAFFEINATE[@]}" "$CLAUDE_BIN" -p "$PROMPT" \
    --permission-mode bypassPermissions \
    --add-dir "$FINERACT_SRC" \
    --output-format stream-json --verbose \
  | tee "$RAW" \
  | /usr/bin/jq -r --unbuffered "$DIGEST" 2>/dev/null
  RC=${pipestatus[1]}
  log "raw event stream: $RAW"
else
  "${CAFFEINATE[@]}" "$CLAUDE_BIN" -p "$PROMPT" \
    --permission-mode bypassPermissions \
    --add-dir "$FINERACT_SRC" \
    --output-format text
  RC=$?
fi

  log "driver exited rc=$RC"
}

# ------------------------------------------------------- exit-protocol guard ---
run_exit_guard() {
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
local -a WT_PATHS; WT_PATHS=()
if (( WT_RC != 0 )); then
  log "ERROR: worktree sweep could not enumerate worktrees (git worktree list rc=$WT_RC) — REFUSING to conclude there is nothing to rescue. Any worker deliverables still sitting in a linked worktree are UNVERIFIED; inspect them by hand."
else
  local WT_LINE
  for WT_LINE in "${(@f)WT_RAW}"; do
    [[ "$WT_LINE" == 'worktree '* ]] && WT_PATHS+=("${WT_LINE#worktree }")
  done
  # entry 1 is the main tree, which the sweep above has already covered
  (( ${#WT_PATHS} > 0 )) && WT_PATHS=("${(@)WT_PATHS[2,-1]}")
fi

for W in "${WT_PATHS[@]}"; do
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
done

# RESUME.md must have been rewritten during this fire, or a fresh session resumes
# from a stale manifest — worse than none, because it looks authoritative.
if [[ -f .softhouse/RESUME.md ]]; then
  RESUME_MTIME=$(/usr/bin/stat -f %m .softhouse/RESUME.md)
  if (( RESUME_MTIME < FIRE_START_EPOCH )); then
    log "WARN: exit-protocol violation — .softhouse/RESUME.md predates this fire's start; the next fire may act on stale state. Review it by hand."
  fi
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
  if [[ "$(git rev-parse HEAD)" == "$HEAD_BEFORE" ]]; then
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
