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

if [[ -f "$LOCK" ]] && (( ! FORCE )); then
  LOCK_EPOCH=$(/usr/bin/stat -f %m "$LOCK" 2>/dev/null || print 0)
  AGE=$(( $(date +%s) - LOCK_EPOCH ))
  if (( AGE < LOCK_MAX_AGE_SECS )); then
    log "another orchestrator holds the lock (age ${AGE}s):"; cat "$LOCK"
    log "exiting — not running two orchestrators over one repo"
    exit 0
  fi
  log "stale lock (age ${AGE}s > ${LOCK_MAX_AGE_SECS}s) — taking it over"
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

release_lock() {
  cd "$REPO" || return
  rm -f "$LOCK"
  # Stage ONLY the lock's deletion — the driver commits its own state changes.
  git add -A -- "$LOCK" >/dev/null 2>&1
  git diff --cached --quiet && { log "lock already released"; return; }
  git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" commit -q -m "softhouse: release local fire lock ($STAMP)" >/dev/null 2>&1
  git push -q origin main 2>/dev/null || log "WARN: could not push lock release"
  log "lock released"
}
trap release_lock EXIT INT TERM

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

log "invoking driver"

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

# ------------------------------------------------------- exit-protocol guard ---
# The driver is required to checkpoint on EVERY exit path (skill STEP 5.5). It has
# been observed exiting rc=0 mid-run with deliverables uncommitted and RESUME.md
# stale, which makes the work invisible to the next fire. Detect and rescue.
DIRTY=$(git status --porcelain | grep -v '^?? \.softhouse/LOCK' || true)
if [[ -n "$DIRTY" ]]; then
  log "WARN: exit-protocol violation — driver left uncommitted work:"
  print -r -- "$DIRTY" | head -20
  git add -A -- . ':!.softhouse/LOCK' >/dev/null 2>&1
  git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \
      commit -q -m "softhouse: rescue uncommitted deliverables left by fire $STAMP (exit-protocol violation)" >/dev/null 2>&1
  log "rescued: committed the leftovers so the next fire can see them"
fi

# The main tree is not the only place work hides. A worker killed mid-flight
# (the fire exiting while its background agents still run) leaves everything
# uncommitted INSIDE its worktree, where the main-tree sweep above cannot see it.
# Observed 2026-08-18 17:22: three workers killed, 4,482 insertions stranded.
for W in $(git worktree list --porcelain | awk '/^worktree/{print $2}' | tail -n +2); do
  [[ -d "$W" ]] || continue
  WD=$(git -C "$W" status --porcelain | wc -l | tr -d ' ')
  (( WD == 0 )) && continue
  WN=$(basename "$W")
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
exit $RC
