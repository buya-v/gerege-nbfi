#!/bin/bash
# =============================================================================
# nightq.sh [queue-dir] — the OVERNIGHT QUEUE (Buyan, 2026-09-11: "queue but don't merge").
#
# Runs every brief in <queue-dir> (default .softhouse/briefs/queue/), in filename order,
# ONE AT A TIME, each in its own worktree on its own branch cut from the CURRENT main.
# It NEVER merges, NEVER pushes, NEVER touches the driver's checkout beyond reading the
# queue and writing logs. The driver reviews every branch in the morning (review.sh) and
# merges or discards.
#
# A queued brief's first line must name its worktree and branch the usual way:
#     Worktree: `/Users/buv/oh-gerege-<x>` (branch `feat/<BR>`)
# The driver writes ONLY oracle-free briefs into the queue: nobody is watching the oracle.
#
# Stall guard: each run gets NIGHTQ_LIMIT_MIN minutes of wall clock (default 75); past
# that it is killed BY PID and the queue moves on. Its worktree is left as it is, so the
# driver can salvage it. A killed run is written to the report as KILLED, never as done.
#
# Start it detached and caffeinated:
#     nohup caffeinate -is bash .softhouse/briefs/tools/nightq.sh > .softhouse/briefs/logs/nightq.log 2>&1 &
# Report: the nohup log above (one line per brief).
# NIGHTQ_DRY=1 creates the worktrees and branches and runs nothing (the control test).
# =============================================================================
set -u
REPO=/Users/buv/gerege-nbfi
Q="$REPO/.softhouse/briefs/queue"
[ $# -ge 1 ] && Q="$1"
LIMIT_MIN="${NIGHTQ_LIMIT_MIN:-75}"
OH=/Users/buv/.local/bin/openhands
# The report is this script's STDOUT (the nohup redirect below captures it) -- no second file,
# so no path is claimed that exists only at run time (T316 dead-path frontier, 2026-09-11).
say(){ printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

[ -d "$Q" ] || { echo "nightq: no queue dir $Q" >&2; exit 2; }
cd "$REPO" || exit 2
say "nightq: start — queue $Q, limit ${LIMIT_MIN}m per run, main at $(git rev-parse --short main)"

for brief in $(ls "$Q"/*.md 2>/dev/null | grep -v "/done-" | sort); do
  name=$(basename "$brief" .md)
  wt=$(grep -m1 -o 'Worktree: `[^`]*`' "$brief" | sed 's/Worktree: `//; s/`$//')
  br=$(grep -m1 -o '(branch `[^`]*`)' "$brief" | sed 's/(branch `//; s/`)$//')
  if [ -z "$wt" ] || [ -z "$br" ]; then say "SKIP $name — no Worktree/branch line"; continue; fi
  if [ -e "$wt" ] || git show-ref --quiet "refs/heads/$br"; then say "SKIP $name — $wt or $br already exists"; continue; fi
  if ! git worktree add -q -b "$br" "$wt" main 2>&1; then say "SKIP $name — worktree add failed"; continue; fi
  cp "$brief" "$wt/TASK.md"
  log="$wt.oh.log"   # beside the worktree, outside the tracked tree
  if [ "${NIGHTQ_DRY:-0}" = 1 ]; then (sleep "${NIGHTQ_DRY_SLEEP:-2}") & else
    (cd "$wt" && exec "$OH" --headless --always-approve -f TASK.md) > "$log" 2>&1 &
  fi
  pid=$!
  say "RUN  $name — pid $pid, $wt ($br)"
  waited=0; killed=0
  while kill -0 "$pid" 2>/dev/null; do
    sleep 30; waited=$((waited + 30))
    if [ "$waited" -ge $((LIMIT_MIN * 60)) ]; then
      pkill -P "$pid" 2>/dev/null; kill "$pid" 2>/dev/null; sleep 5
      pkill -9 -P "$pid" 2>/dev/null; kill -9 "$pid" 2>/dev/null; killed=1
      say "KILLED $name — wall-clock limit ${LIMIT_MIN}m; worktree left for salvage"
      break
    fi
  done
  commits=$(git -C "$wt" log --oneline main..HEAD 2>/dev/null | wc -l | tr -d ' ')
  dirty=$(git -C "$wt" status --porcelain 2>/dev/null | grep -v 'TASK.md' | wc -l | tr -d ' ')
  [ "$killed" = 1 ] && say "     $name at kill: $commits commit(s), $dirty uncommitted path(s)"
  [ "$killed" = 1 ] || say "END  $name — ${waited}s, $commits commit(s), $dirty uncommitted path(s) — REVIEW before merge"
  mv "$brief" "$Q/done-$(basename "$brief")"
done
say "nightq: queue empty — nothing merged, nothing pushed"
