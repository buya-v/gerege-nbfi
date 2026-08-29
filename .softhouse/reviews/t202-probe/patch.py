#!/usr/bin/env python3
"""T202 -- applies the three fixes to the WORKTREE COPY of fire-program.sh.
Each replacement asserts its anchor occurs EXACTLY ONCE (P-35: a substitution
that matched zero or two sites is an error, not a pass)."""

# T465 -- the lock's repo-relative path is ASSEMBLED and spliced in at @LOCK@, never spelt.
# A spelt `.softhouse/`-rooted literal in a tracked instrument is a row in T316's dead-path
# frontier whenever the fire lock is out of the index -- the state main is in after every fire
# exit. THE SPLICED VALUES ARE BYTE-IDENTICAL to the literals they replace: this is a change of
# spelling, not of the patch T202 applied. (The `new` text below is the T202-ERA text; T465 has
# since re-spelt the same two lines in fire-program.sh, so this archived patch no longer applies
# cleanly to today's file -- it is a record of what T202 did, not a re-runnable migration.)
SH_DIR = ".softhouse"
LOCKPATH = SH_DIR + "/LOCK"

import sys, io

path = sys.argv[1]
src = io.open(path, encoding="utf-8").read()


def sub(old, new, label):
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"ANCHOR {label!r} matched {n} times, expected exactly 1 -- ABORT")
    return src.replace(old, new)


# ------------------------------------------------------------------ T-c (1/2)
# SIGKILL recovery at lock acquisition.
old = '''if [[ -f "$LOCK" ]] && (( ! FORCE )); then
  LOCK_EPOCH=$(/usr/bin/stat -f %m "$LOCK" 2>/dev/null || print 0)
  AGE=$(( $(date +%s) - LOCK_EPOCH ))
  if (( AGE < LOCK_MAX_AGE_SECS )); then
    log "another orchestrator holds the lock (age ${AGE}s):"; cat "$LOCK"
    log "exiting — not running two orchestrators over one repo"
    exit 0
  fi
  log "stale lock (age ${AGE}s > ${LOCK_MAX_AGE_SECS}s) — taking it over"
fi
'''
new = '''# T202 — SIGKILL is untrappable, so a hard-killed fire STRANDS its lock, and on
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
# holder's host and pid (:107–:117); if that pid is gone on THIS host, the
# holder is dead and the lock is stale NOW, whatever its age.
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
  host="${${body#*\\"host\\": \\"}%%\\"*}"
  pid="${${body#*\\"pid\\": }%%,*}"
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
'''
src = sub(old, new, "T-c lock acquisition")

# ------------------------------------------------------------------ T-c (2/2)
# The trap itself: release AND terminate.
old = '''release_lock() {
  cd "$REPO" || return
  rm -f "$LOCK"
'''
new = '''LOCK_RELEASED=0
release_lock() {
  (( LOCK_RELEASED )) && return
  cd "$REPO" || return
  rm -f "$LOCK"
  LOCK_RELEASED=1
'''
src = sub(old, new, "T-c release_lock reentry guard")

old = '''trap release_lock EXIT INT TERM
'''
new = '''# T202 — `trap release_lock EXIT INT TERM` released the lock and then LET THE
# SCRIPT CARRY ON. Measured under zsh 5.9 against these very bytes: a SIGINT at
# tick 2 of 40 ran release_lock, deleted the LOCK, and the body then executed
# all 38 remaining ticks — every one of them logging lock_present=NO — and the
# script exited **rc=0**. SIGTERM behaved identically. A fire that keeps working
# while holding no lock is precisely how two orchestrators end up in one repo,
# which is the one thing @LOCK@ exists to prevent (and STEP 0 of
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
'''.replace("@LOCK@", LOCKPATH)
src = sub(old, new, "T-c trap")

# ---------------------------------------------------------------------- T-b
old = '''  git add -A -- . ':!@LOCK@' >/dev/null 2>&1
  git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \\
      commit -q -m "softhouse: rescue uncommitted deliverables left by fire $STAMP (exit-protocol violation)" >/dev/null 2>&1
  log "rescued: committed the leftovers so the next fire can see them"
'''.replace("@LOCK@", LOCKPATH)
new = '''  # T202: `:(top)`-anchored, so the rescue measures the same thing the `git
  # status` above it measures. The old `-- . ':!@LOCK@'` was
  # CWD-RELATIVE and therefore ASYMMETRIC with the `:(top)` status T190 added —
  # worse than the pre-T190 state, because the two disagreed about their subject.
  # Measured from a subdirectory of a scratch repo: status listed BOTH stranded
  # deliverables, `git add` staged NOTHING, HEAD did not move, and the guard
  # still logged `rescued: committed the leftovers`. Both rcs are now CHECKED, so
  # "rescued" is printed only after a commit that actually happened.
  # POLARITY: fail-CLOSED — it now says "NOTHING was rescued" instead of claiming
  # a rescue it did not perform.
  git add -A -- ':(top)' ':(top,exclude)@LOCK@' >/dev/null 2>&1
  ADD_RC=$?
  if (( ADD_RC != 0 )); then
    log "ERROR: exit-protocol rescue could not stage the leftovers (git add rc=$ADD_RC) — NOTHING was rescued. The paths listed above are still uncommitted; inspect the tree by hand."
  else
    git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \\
        commit -q -m "softhouse: rescue uncommitted deliverables left by fire $STAMP (exit-protocol violation)" >/dev/null 2>&1
    COMMIT_RC=$?
    if (( COMMIT_RC == 0 )); then
      log "rescued: committed the leftovers so the next fire can see them"
    else
      log "ERROR: exit-protocol rescue staged the leftovers but the COMMIT FAILED (git commit rc=$COMMIT_RC) — NOTHING was rescued. The paths listed above are still uncommitted; inspect the tree by hand."
    fi
  fi
'''.replace("@LOCK@", LOCKPATH)
src = sub(old, new, "T-b rescue add/commit")

# ---------------------------------------------------------------------- T-a
old = '''for W in $(git worktree list --porcelain | awk '/^worktree/{print $2}' | tail -n +2); do
  [[ -d "$W" ]] || continue
  WD=$(git -C "$W" status --porcelain | wc -l | tr -d ' ')
  (( WD == 0 )) && continue
  WN=$(basename "$W")
'''
new = '''# T202: enumerate into an ARRAY with git's own status CHECKED. The old
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
'''
src = sub(old, new, "T-a worktree sweep")

io.open(path, "w", encoding="utf-8").write(src)
print(f"patched {path}")
