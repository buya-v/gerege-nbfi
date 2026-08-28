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
LOCK_MAX_AGE_SECS="${LOCK_MAX_AGE_SECS:-21600}"   # 6h — freshness threshold (STEP 0 arms 4/5)
LOCK_CEILING_SECS="${LOCK_CEILING_SECS:-86400}"   # 24h — T279 lifetime CEILING (STEP 0 arm 3)
CLAUDE_BIN="${CLAUDE_BIN:-$HOME/.local/bin/claude}"

# Reference-oracle probes. PostgreSQL only — never MySQL/MariaDB, never Oracle DB.
PG_HOST="${PG_HOST:-localhost}"
PG_PORT="${PG_PORT:-5432}"
FINERACT_HEALTH_URL="${FINERACT_HEALTH_URL:-https://localhost:8443/fineract-provider/actuator/health}"

# ================================================================ T279 ============
# THE STEP 0 LOCK DECISION, IN EXECUTABLE FORM — AND IT IS THE *SAME* DECISION THE
# DRIVER SKILL DOCUMENTS.
#
# WHAT WAS HERE BEFORE, AND WHY IT WAS WRONG. Until T279 this file decided staleness on
# `/usr/bin/stat -f %m "$LOCK"` — the lock FILE'S MTIME. T265 measured it live: a lock
# whose `started_at` said 8 h read an age of 12.6 MINUTES, 38x off, because the
# `git pull --ff-only` a few lines below REWRITES the file and resets its mtime. So the
# only fire that can reach the reference oracle decided on a signal that the fire's own
# first action destroys, while STEP 0 of `softhouse-program/SKILL.md` declared push
# recency authoritative. Two orchestrators reading two different rules is the P-85 shape --
# P-85 is *"two orchestrators held the lock at once, and the cause was an unpushed in-flight
# state"* [.softhouse/patterns.md:2822].
# [T265 F-3, `.softhouse/reviews/t265-review-lock-fix/` on branch softhouse/t265-review-lock-fix @422f517a.]
#
# WHY IT IS A PURE FUNCTION OF FIVE SIGNALS. T265 F-1 measured that the four arms STEP 0
# shipped did not partition the state space: 18 distinguishable states matched NO arm and
# had no verdict, and 22 matched arms that DISAGREED. A rule set like that answers
# differently depending on the order it is read in, which is exactly how a local fire and
# a cloud fire both conclude they may proceed. The seven arms below are written to be
# MUTUALLY EXCLUSIVE, so the answer cannot depend on evaluation order at all — proven by
# enumerating all 192 states in `.softhouse/capture/t279-lock-partition/enumerate.py`
# (0 zero-match, 0 multi-match, all arms pairwise disjoint), and the SAME enumeration is
# replayed through THIS function by `drive-wrapper-vs-skill.zsh`, which is what makes
# "the wrapper and the skill decide the same way" a measurement rather than a claim.
#
# ARM 3 IS THE CEILING, AND IT IS NOT A RELAPSE INTO `started_at`. P-85's lesson is that
# `started_at` is not a FRESHNESS signal — it cannot tell "died five hours ago" from "has
# been working for five hours." True, and arm 3 does not use it as one. It uses it as a
# LIFETIME BOUND: past 24 h the holder cannot still be legitimately alive, whatever the
# tip says. Without it rule 2's freshness term is refreshed by THIRD PARTIES and the lock
# has no guaranteed takeover time at all — measured live, `fire-20260827-230001` faced a
# lock 105 h old whose tip was 2.99 h old, which rule 2 as written reads as HELD forever.
# [`.softhouse/capture/t279-lock-partition/out/measure-f2.txt` §5, §6.]
#
#   $1 lock_present  1 | 0
#   $2 released_at   "" = null/absent; anything else = released
#   $3 started_age   seconds since `started_at`, or "" if it could not be read
#   $4 tip_age       seconds since ct(origin/main), or "" if it could not be read
#   $5 pid_state     alive_here | dead_here | absent | other_host
#
# POLARITY: fail-CLOSED on every unreadable signal. A negative age (clock skew) fails the
# `<0->` glob and lands in arm 6 -> HELD. A signal you cannot read is never permission to
# take the lock.
lock_decide() {
  local present="$1" rel="$2" sage="$3" tage="$4" pstate="$5"
  (( present ))                     || { print -r -- FREE-no-lock;    return 0; }   # arm 0
  [[ -n "$rel" ]]                   && { print -r -- FREE-released;   return 0; }   # arm 1
  [[ "$pstate" == dead_here ]]      && { print -r -- TAKE-dead-pid;   return 0; }   # arm 2
  if [[ "$sage" == <0-> ]] && (( sage >= LOCK_CEILING_SECS )); then
    print -r -- TAKE-ceiling; return 0                                             # arm 3
  fi
  if [[ "$tage" == <0-> ]] && (( tage < LOCK_MAX_AGE_SECS )); then
    print -r -- HELD-live; return 0                                                # arm 4
  fi
  if [[ "$tage" == <0-> ]] && (( tage >= LOCK_MAX_AGE_SECS )) \
     && [[ "$sage" == <0-> ]] && (( sage >= LOCK_MAX_AGE_SECS )); then
    print -r -- TAKE-both-stale; return 0                                          # arm 5
  fi
  print -r -- HELD-default                                                         # arm 6
}

# T279 — `lock_pid_state` is the four-way form; `lock_holder_is_dead` is kept as the thin
# wrapper the comments at :884 and :1057 name, so those references stay true. T265 F-5 is
# RECORDED, NOT FIXED, and the polarity claim above is narrowed accordingly: `kill -0`
# returns EPERM for a LIVE process owned by another uid, and this function reads that as
# dead. Not reachable while both fires run as uid 501 under a user-domain launchd agent;
# reachable the moment anything runs a fire under `sudo`. So the correct claim is "it can
# never make a live lock look free FOR A HOLDER RUNNING AS THE SAME USER." pid REUSE goes
# the safe way (a recycled pid reads alive, so the holder merely waits out arm 3).
lock_pid_state() {
  local body host pid
  [[ -r "$LOCK" ]]            || { print -r -- absent; return 0; }
  body="$(<"$LOCK")"          || { print -r -- absent; return 0; }
  [[ "$body" == *'"host": "'* ]] || { print -r -- absent; return 0; }
  [[ "$body" == *'"pid": '*   ]] || { print -r -- absent; return 0; }
  host="${${body#*\"host\": \"}%%\"*}"
  pid="${${body#*\"pid\": }%%,*}"
  [[ "$host" == "$(hostname -s)" ]] || { print -r -- other_host; return 0; }  # never judge another machine
  [[ "$pid" == <1-> ]]             || { print -r -- absent;     return 0; }   # junk, or the "pid": 0 T265 F-4 found
  (( pid == $$ ))                  && { print -r -- alive_here; return 0; }   # never judge ourselves
  kill -0 "$pid" 2>/dev/null       && { print -r -- alive_here; return 0; }
  print -r -- dead_here
}

lock_holder_is_dead() { [[ "$(lock_pid_state)" == dead_here ]] }

# `released_at`, empty unless the key is present AND its value is not `null`.
lock_released_at() {
  local body v
  [[ -r "$LOCK" ]] || return 0
  body="$(<"$LOCK")" || return 0
  [[ "$body" == *'"released_at":'* ]] || return 0
  v="${${body#*\"released_at\":}%%,*}"
  v="${v//[$' \t\r\n\"']/}"
  [[ "$v" == null || -z "$v" ]] && return 0
  print -r -- "$v"
}

# Age of the lock's `started_at`, in seconds. Empty = could not read it (arm 6, HELD).
lock_started_age() {
  local body iso e now
  [[ -r "$LOCK" ]] || return 0
  body="$(<"$LOCK")" || return 0
  [[ "$body" == *'"started_at": "'* ]] || return 0
  iso="${${body#*\"started_at\": \"}%%\"*}"
  e=$(TZ=UTC /bin/date -j -f "%Y-%m-%dT%H:%M:%SZ" "$iso" +%s 2>/dev/null) || return 0
  [[ "$e" == <1-> ]] || return 0
  now=$(date +%s)
  print -r -- $(( now - e ))
}

# THE AUTHORITATIVE FRESHNESS SIGNAL: seconds since the newest PUBLISHED commit. The
# `git pull --ff-only` above has already fetched, so `origin/main` is current; a fetch
# failure leaves a stale remote-tracking ref, which reads OLDER, which fails toward
# takeover — so it is refetched here and a failure returns empty (arm 6, HELD) instead.
origin_main_tip_age() {
  local ct now
  git fetch --quiet origin main 2>/dev/null || return 0
  ct=$(git log -1 --format=%ct origin/main 2>/dev/null) || return 0
  [[ "$ct" == <1-> ]] || return 0
  now=$(date +%s)
  print -r -- $(( now - ct ))
}


# `--lock-decide <5 signals>` prints one verdict and exits. It is handled HERE, before
# the T301 snapshot re-exec and before any preflight, so the conformance driver can
# evaluate the whole state space against the SHIPPED file cheaply and without a repo,
# a lock, a network or a side effect. It is a query; it takes nothing and writes nothing.
if [[ "${1:-}" == "--lock-decide" ]]; then
  shift
  (( $# == 5 )) || { print -u2 "usage: --lock-decide <present> <released_at> <started_age> <tip_age> <pid_state>"; exit 64; }
  lock_decide "$@"
  exit 0
fi

# `--lock-signals` reads the four signals off a REAL `$LOCK` in a REAL repo (honouring
# GEREGE_NBFI_REPO, so it can be pointed at a scratch clone) and prints them with the
# verdict. Same query discipline as `--lock-decide`: it takes no lock, writes nothing,
# spawns nothing. This is the entry point `drive-two-fires.zsh` uses, so the two-fire
# drive exercises the actual signal-reading code and not a re-implementation of it.
if [[ "${1:-}" == "--lock-signals" ]]; then
  cd "$REPO" 2>/dev/null || { print -u2 "no such repo: $REPO"; exit 66; }
  if [[ -f "$LOCK" ]]; then
    _p=1; _r="$(lock_released_at)"; _s="$(lock_started_age)"; _t="$(origin_main_tip_age)"; _ps="$(lock_pid_state)"
  else
    _p=0; _r=""; _s=""; _t="$(origin_main_tip_age)"; _ps=absent
  fi
  print -r -- "repo=$REPO"
  print -r -- "lock_present=$_p released_at=${_r:-<null>} started_age=${_s:-<unreadable>} tip_age=${_t:-<unreadable>} pid_state=$_ps"
  print -r -- "mtime_age=$(( $(date +%s) - $(/usr/bin/stat -f %m "$LOCK" 2>/dev/null || print 0) ))   # printed only; decides nothing"
  print -r -- "verdict=$(lock_decide "$_p" "$_r" "$_s" "$_t" "$_ps")"
  exit 0
fi

PROBE_ONLY=0; FORCE=0
for a in "$@"; do
  case "$a" in
    --probe) PROBE_ONLY=1 ;;
    --force) FORCE=1 ;;
    *) print -u2 "unknown arg: $a"; exit 64 ;;
  esac
done

# ================================================================ T301 ============
# RUN FROM AN IMMUTABLE SNAPSHOT OF THIS FILE.
#
# WHY, MEASURED. zsh does not slurp a script; it goes back to the file for more input
# as it executes. T301 measured how far ahead it has read when it blocks: about
# 7.6 KB [.softhouse/capture/t301-wrapper-self-modification/probe-source-and-shift.txt,
# PART 3b]. This file is ~124 KB and the multi-hour `wait` on the driver sits at byte
# ~66,000, so roughly 50 KB of it is UNREAD for the entire fire -- and that 50 KB is not
# inert filler. It is `run_exit_guard`, `reconcile_tasks_json`, `wt_prune_blindspot_check`
# and the worktree-prune sweep that calls `git worktree remove`. Corrupt a byte there and
# the failure is not "the fire crashes", it is "the classifier that decides what to
# DELETE was rewritten under us".
#
# WHAT ACTUALLY HAPPENS ON AN IN-PLACE EDIT, MEASURED. Not a clean line-boundary swap.
# T301 PART 3b swapped ORIG->MARK, four characters for four, so nothing shifted at all,
# and still caught a SPLICE at the read boundary: the row that straddled it executed as
#     ROW 0291 ORIK
# -- three bytes from the file the shell started with, the rest from the file on disk
# after the edit. It fell inside a quoted string there so it printed harmlessly. Inside a
# command name, a variable, an `if`/`fi` or a heredoc delimiter it is a syntax error or,
# worse, a DIFFERENT COMMAND. [probe-source-and-shift.txt, PART 3b, verbatim rows.]
#
# WHY THIS IS NOT ALREADY SOLVED BY GIT. It nearly is, and that is worth stating plainly
# rather than overselling the fix. A shell holds an fd on an INODE, so only a writer that
# keeps the inode can reach it. T301 measured 17 writers + both Claude Code file tools
# [probe-writer-inode.txt]:
#   ISOLATED (new inode): git merge / checkout -- <path> / pull --ff-only / reset --hard /
#     stash pop / apply / checkout-index / restore; sed -i '' (BSD); mv; install; patch;
#     Claude Code Write; Claude Code Edit.
#   IN PLACE (same inode, CAN REACH A RUNNING FIRE):
#     cat > file    python open(path,"w")    >> append    tee file    cp src dst
#     dd conv=notrunc    ex -s
# So landing a branch is safe, and always was. The residual is the second list, and it is
# not hypothetical: `cp` is what a human reaches for ("copy the fixed wrapper over the
# live one"), it is the dangerous half of the cp/mv pair, and agents in this pipeline run
# under instructions that PREFER `cat > file` heredocs to the (isolated) Write tool.
# P-45 is the argument against leaving this as the convention "never edit the live path".
# CITING THE TEXT, because the paraphrase in circulation is not what the pattern says.
# P-45 is titled "A test-only guard is not a guard" and its rule is: *"when hardening a
# check, verify the path that ACTUALLY EXECUTES in CI/conformance calls it, not merely
# that a test does."* [.softhouse/patterns.md:1503-1506]. "Never in-place-edit the live
# wrapper" is not called by any executing path at all -- it is prose in a task brief --
# so it is the limiting case of the same defect. Fifteen lines of `cp` + `exec` move the
# protection onto the path that actually runs.
#
# THE COSTS, AND HOW EACH IS PAID.
#   * `${0:A:h}` resolved SCRIPT_DIR against this script's own path, and SCRIPT_DIR
#     locates lib-worktree-prune.zsh, branch_sweep.py, ready-tasks.py and
#     ../guards/repo-state-attest.sh. Running from /tmp would break all four. So the
#     ORIGINAL directory is pinned into FIRE_SCRIPT_DIR before the exec and SCRIPT_DIR
#     reads it back below. Nothing else in this file uses $0.
#     (Those four are not exposed to the hazard anyway: a sourced zsh file is read and
#     parsed entirely by `source` and a later edit -- in place OR renamed -- cannot reach
#     it [probe-source-and-shift.txt, PART 1], and python compiles a whole module before
#     running it. Only THIS file is read incrementally.)
#   * The re-exec loop is guarded by FIRE_SNAPSHOT_OF, which only the exec'd copy sees.
#   * FAIL-OPEN, deliberately: if mktemp or cp fails we log it loudly and run from the
#     repo copy exactly as before. A fire that refuses to start because /tmp is full
#     would be a worse bug than the one being fixed, and the failure is visible at
#     second zero of the log rather than silently hours in.
#   * Stale snapshots from earlier fires are swept below. The CURRENT one is left on
#     disk; it is ~124 KB and the running shell needs it.
#
# ALTERNATIVE REJECTED: "forbid merging bin/ changes from inside a fire, hand them to the
# cloud fire or a human." It is unnecessary (git renames; measured) AND unenforceable
# (P-45 again), so it buys nothing and costs a rule someone must remember. It would also
# have blocked this fire's own T324 and T325 wrapper landings, which were correct.
FIRE_SCRIPT_DIR="${FIRE_SCRIPT_DIR:-${0:A:h}}"
FIRE_REPO_SCRIPT="${FIRE_REPO_SCRIPT:-${0:A}}"
FIRE_SNAPSHOT_NOTE=""
if [[ -z "${FIRE_SNAPSHOT_OF:-}" && "${FIRE_NO_SNAPSHOT:-0}" != "1" ]]; then
  # sweep snapshots older than a day from fires that are long gone
  /usr/bin/find "${TMPDIR:-/tmp}" -maxdepth 1 -name 'fire-wrapper-snap.*' -type d -mtime +1 \
    -exec /bin/rm -rf {} + 2>/dev/null || true
  _t301_dir="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/fire-wrapper-snap.XXXXXX" 2>/dev/null)" || _t301_dir=""
  if [[ -n "$_t301_dir" && -r "${0:A}" ]] && /bin/cp "${0:A}" "$_t301_dir/fire-program.sh" 2>/dev/null; then
    /bin/chmod +x "$_t301_dir/fire-program.sh" 2>/dev/null
    export FIRE_SNAPSHOT_OF="${0:A}"
    export FIRE_SCRIPT_DIR FIRE_REPO_SCRIPT
    exec /bin/zsh "$_t301_dir/fire-program.sh" "$@"
    # not reached; if exec itself failed zsh has already died with an error
  fi
  FIRE_SNAPSHOT_NOTE="SNAPSHOT FAILED (mktemp/cp under ${TMPDIR:-/tmp}) — running directly from the repo copy, which an IN-PLACE writer (cat >, cp, tee, >>, python open(w)) could still reach mid-fire"
  print -u2 "WARN: $FIRE_SNAPSHOT_NOTE"
fi
# ==================================================================================

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
# T301: pinned before the snapshot re-exec above, so this still points at the REPO's
# bin/ directory even though $0 now names a copy under $TMPDIR. When no snapshot was
# taken FIRE_SCRIPT_DIR was set from ${0:A:h} a few lines above, so the value is
# identical to what this line produced before T301.
SCRIPT_DIR="${FIRE_SCRIPT_DIR:-${0:A:h}}"

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
# rewrite of the live path. T301 CORRECTS THE LIST THIS COMMENT USED TO GIVE, because
# two of its four entries were asserted rather than measured
# [.../t301-wrapper-self-modification/probe-writer-inode.txt]:
#   * `sed -i ''` on this host does NOT rewrite in place -- BSD sed writes a temp file
#     and renames, so it is ISOLATED. It was named here as dangerous and is not.
#   * `cp src dst` IS in place and was NOT named. So are `tee`, `>>` and `ex -s`.
#     `cp` is the one that bites: "copy the fixed wrapper over the live one" is the
#     natural thing to type and it is the dangerous half of the cp/mv pair.
# Since T301 this is belt AND braces: the fire re-execs from a snapshot under $TMPDIR
# (see the T301 block above), so even an in-place writer against the repo path cannot
# reach the running interpreter. Still edit in a worktree and land it through git -- the
# snapshot protects the RUNNING fire, not the next one.
if [[ -r "${0:A}" ]]; then
  log "wrapper identity: path=${0:A} inode=$(/usr/bin/stat -f %i "${0:A}" 2>/dev/null || print '?') sha256=$(/usr/bin/shasum -a 256 "${0:A}" 2>/dev/null | cut -c1-16 || print '?') bytes=$(/usr/bin/stat -f %z "${0:A}" 2>/dev/null || print '?')"
else
  log "WARN: could not read this script's own bytes at ${0:A} -- the version of the wrapper this fire ran is UNRECORDED"
fi
# T301 -- the line above now identifies a copy under $TMPDIR, which is the honest answer
# to "which bytes is this fire running" but loses the answer to "which commit is that".
# So log the REPO copy too, and say which mode we are in. If the snapshot failed, say
# that here as well rather than only on stderr before the log existed.
if [[ -n "${FIRE_SNAPSHOT_OF:-}" ]]; then
  log "wrapper snapshot: RUNNING FROM A SNAPSHOT — repo copy=$FIRE_SNAPSHOT_OF inode=$(/usr/bin/stat -f %i "$FIRE_SNAPSHOT_OF" 2>/dev/null || print '?') sha256=$(/usr/bin/shasum -a 256 "$FIRE_SNAPSHOT_OF" 2>/dev/null | cut -c1-16 || print '?') bytes=$(/usr/bin/stat -f %z "$FIRE_SNAPSHOT_OF" 2>/dev/null || print '?'); the repo copy is now free to be modified by the fire this wrapper is about to start"
elif [[ -n "${FIRE_SNAPSHOT_NOTE:-}" ]]; then
  log "WARN: wrapper snapshot: $FIRE_SNAPSHOT_NOTE"
else
  log "wrapper snapshot: DISABLED by FIRE_NO_SNAPSHOT=1 — this fire reads its own bytes from the repo path for its whole life"
fi

source "$SCRIPT_DIR/lib-worktree-prune.zsh" || { log "FATAL: could not source lib-worktree-prune.zsh"; exit 1; }

# ------------------------------------------ T325: repo-state attestation ---
# T318 measured six live damage gates in this program and found FIVE OF THEM
# BLIND to a committed clobber. Two of the five are in THIS FILE, and the worst
# of them is this file's implementation of the driver's own STEP 5.5:
#
#     "`git status --porcelain` must come back empty"
#
# T318 drove nine distinct shapes of destruction and six legitimate operations
# through that sentence. It answered CLEAN on ALL FIFTEEN
# [VERIFIED: .softhouse/capture/t318-committed-clobber-blindness/evidence/
#  30-red-green-drive.txt, the LEGACY column]. That is not a weak test; over this
# class it has NO discriminating power at all, and every fire that has asserted
# cleanliness from it has been asserting nothing.
#
# The reframing that fixes it: "is the tree clean?" is not the property anyone
# wants -- a fire is SUPPOSED to commit, to move tasks.json, to create worker
# branches. The property wanted is "the repo differs from before only in ways
# this operation was authorized to produce", which is a relation between THREE
# things (before, after, writ) and which NO predicate over a single state can
# express. So the wiring below is differential: snapshot at the top of each chain
# iteration, snapshot again at the end of the exit guard, compare against the
# fire's writ (`fire-compare`, whose writ is defined once inside the guard so the
# wrapper and the false-positive drives cannot drift apart).
#
# NEVER FATAL, AND THAT IS ARGUED, NOT TIMID. The attestation reports; it does
# not abort a fire. A guard that stops the program on its own false positive is
# removed within two fires -- T318's arm G5 caught exactly that shape in its own
# first draft (it flagged the sanctioned `git checkout -b softhouse/<task>` as
# damage). The value here is that the finding reaches the log and the postmortem
# at all: today the fire asserts "clean" and is not even wrong, it is uninformed.
# T325-ATTEST-WIRING BEGIN
#   (marker: .softhouse/capture/t325-adopt-attestation/instruments/
#    50-wrapper-glue-drive.zsh EXTRACTS the lines between these two markers and
#    drives THE SHIPPED GLUE — because a guard that works and a wiring that
#    fails open are indistinguishable from the guard's own test suite. The
#    instrument REFUSES if it cannot find the markers.)
ATTEST="${ATTEST:-$SCRIPT_DIR/../guards/repo-state-attest.sh}"
ATTEST_DIR="${ATTEST_DIR:-$LOG_DIR}"
ATTEST_BEFORE=""   # per chain iteration. EMPTY means "no baseline was taken",
                   # which resolves to UNATTESTED, never to clean.

# Run the guard and log every line it prints, prefixed. Returns the guard's rc.
# `bash`, never `sh`/`zsh`: the guard is a bash script and uses bash arrays --
# the same wrong-interpreter discipline `conformance.sh` enforces with exit 3.
attest_run() {
  local prefix="$1"; shift
  if [[ ! -r "$ATTEST" ]]; then
    log "ERROR: $prefix — the repo-state attestation guard is NOT READABLE at $ATTEST. This fire is UNATTESTED: nothing in this log supports a claim that nothing was destroyed. (P-45: 'a guard that only works when someone remembers to run it enforces nothing' — one that is not on disk enforces less.)"
    return 2
  fi
  local out rc l
  out=$(bash "$ATTEST" "$@" 2>&1); rc=$?
  for l in "${(@f)out}"; do
    [[ -n "$l" ]] && log "$prefix| $l"
  done
  return $rc
}

# The exit-protocol half of the attestation. Called at the very end of
# run_exit_guard, AFTER the wrapper's own rescue/repair commits and its push, so
# the window it attests is the whole iteration including everything STEP 5.5
# itself does.
attest_exit_protocol() {
  local after rc
  if [[ -z "$ATTEST_BEFORE" || ! -r "$ATTEST_BEFORE" ]]; then
    log "ERROR: exit-protocol attestation: NO BASELINE SNAPSHOT for this iteration (${ATTEST_BEFORE:-<none taken>}). The fire is UNATTESTED — which is NOT the same as clean, and must not be reported as clean. Everything below the legacy \`git status\` line in this log is the pre-T325 blind reading."
    return 2
  fi
  after="${ATTEST_BEFORE%.before}.after"
  attest_run "attest-after" snapshot "$REPO" "$after"
  rc=$?
  if (( rc != 0 )); then
    log "ERROR: exit-protocol attestation: could not take the AFTER snapshot (rc=$rc). UNATTESTED — the guard fails CLOSED, so 'I could not measure' never resolves to 'no damage'."
    return 2
  fi
  attest_run "attest" fire-compare "$ATTEST_BEFORE" "$after"
  rc=$?
  case $rc in
    0) log "attest: exit-protocol attestation PASSED — every delta between $ATTEST_BEFORE and $after is inside this fire's writ (seven terms, not one)" ;;
    1) log "ERROR: EXIT-PROTOCOL VIOLATION — the repo-state attestation reports DAMAGE (see the attest| lines above for which term fired). This is reported, never suppressed: it is the finding the legacy \`git status --porcelain\` check could not produce for any of the nine shapes T318 drove." ;;
    *) log "ERROR: exit-protocol attestation REFUSED (rc=$rc) — it could not measure. UNATTESTED, not clean." ;;
  esac
  return $rc
}
# T325-ATTEST-WIRING END

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

# T325 — THE PRE-FLIGHT BASELINE READING (FU-T318-5).
#
# `/softhouse` STEP 0.1 and `/softhouse-plan` STEP 0.1 both say "`git status` —
# abort if the tree is dirty". T318 lists both as BLIND gates, and the reason
# they matter most is the moment they occupy: pre-flight is the point at which an
# undetected clobber left by the PREVIOUS fire is silently adopted as this
# fire's baseline. Everything the fire then measures is measured against damage.
#
# Those two gates live in `.claude/skills/*/SKILL.md`, outside T325's edit set,
# and this line does not change them — see the T325 handoff, which states the
# exact prose replacement and its owner. What this line does is put the reading
# on the path that actually executes on this host every day, so the fact reaches
# a log even while the prose stays stale.
#
# It is a SURVEY, not a compare, because at pre-flight there is no "before" to
# be differential against — and the survey votes on exactly one term (index skip
# bits), which no legitimate operation in this pipeline produces. Deliberately
# NOT fatal: a fire that refuses to start because of an inherited condition it
# cannot fix would park the whole program, and would be commented out within two
# fires. It reports, loudly, and the fire proceeds.
attest_run "attest-preflight" survey "$REPO" --label "fire $STAMP pre-flight baseline"
ATTEST_PRE_RC=$?
case $ATTEST_PRE_RC in
  0) log "attest-preflight: baseline reading taken — no hidden-work term fired in $REPO before this fire started" ;;
  1) log "ERROR: attest-preflight: HIDDEN WORK IS ALREADY PRESENT in $REPO before this fire has done anything. An index skip bit switches off the working-tree comparison that this file's exit guard, \`git worktree remove\` and the prune classifier all rely on. Do NOT read this fire's later 'clean' lines as evidence about those paths; clear the bit by hand (\`git update-index --no-assume-unchanged <path>\`) after checking what is under it." ;;
  *) log "WARN: attest-preflight: the baseline survey REFUSED (rc=$ATTEST_PRE_RC) — this fire starts from an UNMEASURED baseline. Not fatal, but the exit attestation's 'no damage' is weaker by exactly this much." ;;
esac

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
#
# T279 MOVED THE FOUR SIGNAL READERS AND `lock_pid_state` UP to sit beside `lock_decide()`
# near the top of this file, so that `--lock-decide` / `--lock-signals` can drive the REAL
# reading code against a scratch clone without running a preflight, and so that all of the
# lock logic is inside the ~7.6 KB zsh has already read when it blocks on the driver (T301).
# The T202 reasoning above is unchanged and still describes `lock_pid_state`.

if [[ -f "$LOCK" ]] && (( ! FORCE )); then
  LOCK_REL="$(lock_released_at)"
  LOCK_SAGE="$(lock_started_age)"
  LOCK_TAGE="$(origin_main_tip_age)"
  LOCK_PSTATE="$(lock_pid_state)"
  LOCK_VERDICT="$(lock_decide 1 "$LOCK_REL" "$LOCK_SAGE" "$LOCK_TAGE" "$LOCK_PSTATE")"
  # The mtime the wrapper used to decide on is still PRINTED, so the log shows how far
  # apart the two signals are on any given day. It decides nothing (T265 F-3).
  LOCK_MTIME_AGE=$(( $(date +%s) - $(/usr/bin/stat -f %m "$LOCK" 2>/dev/null || print 0) ))
  log "lock signals: released_at='${LOCK_REL:-<null>}' started_age=${LOCK_SAGE:-<unreadable>}s tip_age=${LOCK_TAGE:-<unreadable>}s pid=${LOCK_PSTATE} (file mtime age ${LOCK_MTIME_AGE}s — NOT a freshness signal) -> ${LOCK_VERDICT}"
  case "$LOCK_VERDICT" in
    TAKE-dead-pid)
      log "arm 2: lock holder is a DEAD pid on this host — a hard-killed fire stranded it; taking it over now, whatever the age:"; cat "$LOCK" ;;
    TAKE-ceiling)
      log "arm 3: lock exceeds the ${LOCK_CEILING_SECS}s lifetime CEILING (started_age=${LOCK_SAGE}s) — no fire can legitimately still be running; taking it over:"; cat "$LOCK" ;;
    TAKE-both-stale)
      log "arm 5: both signals stale (tip_age=${LOCK_TAGE}s, started_age=${LOCK_SAGE}s > ${LOCK_MAX_AGE_SECS}s) — taking it over" ;;
    FREE-released)
      log "arm 1: lock carries released_at=${LOCK_REL} — free; taking it" ;;
    HELD-live)
      log "arm 4: another orchestrator holds the lock and is PUBLISHING (newest origin/main commit ${LOCK_TAGE}s old):"; cat "$LOCK"
      log "exiting — not running two orchestrators over one repo"
      exit 0 ;;
    *)
      log "arm 6 (default): no arm established that this lock is free, so it is HELD. Signals above; a signal that could not be read is never permission to take the lock:"; cat "$LOCK"
      log "exiting — not running two orchestrators over one repo"
      exit 0 ;;
  esac
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
# T319 -- `fire` IS RECORDED HERE AS A CROSS-CHECK, AND THIS COMMENT IS THE THIRD VERSION
# OF ITSELF. T309 attempt 1 wrote here that `fire` "IS LOAD-BEARING, NOT DECORATION" and
# that `ready-tasks.py --reconcile` "demotes an `in_progress` task only when the task's own
# `fire` differs from THIS value". That rule was discarded by T309's own attempt 2 (it
# would have demoted six live workers) and this comment was not updated -- so for four days
# the wrapper DOCUMENTED A RULE THE RESOLVER EXPLICITLY REFUSES TO FOLLOW, which is how the
# next author gets it wrong twice. [Found by T302, REVIEW-A2 "what I checked and found
# clean"; fixed here.]
#
# WHAT IT IS NOW. `ready-tasks.py` finds this fire's lock commit as "the newest commit that
# TOUCHED .softhouse/LOCK, whose SUBJECT is `softhouse: local fire lock (<id>)`", and reads
# the fire id off THAT SUBJECT. So the anchor is the act of taking the lock, not a field and
# not a commit-message search -- a reviewer who quotes the subject in a commit body cannot
# move it, and a lock written without this field still works. The field below is only a
# cross-check: when it is present and disagrees with the anchor's id, the resolver REFUSES
# rather than choosing one. Keeping it is cheap and its failure direction is safe.
#
# NOTE FOR THE NEXT AUTHOR: this is the LOCK's `fire`. The TASK-level `fire` and
# `dispatched_at` fields in tasks.json are a different thing, they were measured stale and
# half-populated (12 of 203 tasks), and T319 removed every read of them.
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
# T319 — F8b. How much of the outer budget the INNER (graceful) deadline gives back, so
# the degraded tail can actually write before the outer bound kills the subtree. See the
# use site in on_signal for the measurement this is derived from.
RECONCILE_TAIL_RESERVE_SECS="${RECONCILE_TAIL_RESERVE_SECS:-1}"

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
    # T319 — F8b. THESE TWO NUMBERS USED TO BE THE SAME NUMBER, WHICH COLLAPSED THE
    # TWO-LAYER DESIGN INTO ONE LAYER IN EXACTLY THE CASE IT WAS BUILT FOR. The stated
    # polarity (see the budget comment above) is that the INNER bound degrades gracefully
    # — WIP evidence becomes UNVERIFIED, the demotions still land and still get written —
    # while the OUTER bound is brutal: the subtree is killed and NOTHING is written. With
    # inner == outer the inner path only BEGINS degrading at the instant the outer kill is
    # due, so the graceful layer can never finish before the brutal one fires.
    # The inner deadline is therefore the outer budget MINUS the time the degraded tail
    # needs to parse, decide and write. T302 measured that tail end-to-end on the real
    # 792 KB tasks.json at N=0 (startup + parse + report, no git): 0.106 s
    # [VERIFIED: .softhouse/reviews/T302/a2/out-f8-cost.txt]. RECONCILE_TAIL_RESERVE_SECS
    # is 1 s — an order of magnitude of margin over the measurement, and still small
    # against the ~7 s budget the defaults produce. It is a variable, not a literal, so
    # the next person to re-measure changes one thing.
    local inner=$(( budget - RECONCILE_TAIL_RESERVE_SECS ))
    (( inner < 1 )) && inner=1
    log "signal-path reconcile layers: inner (--deadline-secs, graceful) ${inner}s, outer (reconcile_bounded, kills the subtree) ${budget}s — the inner MUST be smaller, or the graceful layer never completes"
    RECONCILE_DEADLINE_SECS=$inner
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
  # T319 adds `named` and `mentions` to this one declaration site, for the reason the
  # paragraph above gives.
  local line pid st first cwd lsofout l seg checked=0 unknown=0 found=0 named=0 mentions=0 unnamed=0
  local -a f
  for line in $lines; do
    f=(${=line})
    (( ${#f} >= 3 )) || continue
    pid=$f[1]; st=$f[2]; first=$f[3]
    [[ "$pid" == <1-> ]] || continue
    (( pid == $$ )) && continue
    # T319 — F3a. `[[ "${first:t}" == claude ]] || continue` WAS A ONE-WAY FILTER AND IT
    # FAILED IN THE DESTRUCTIVE DIRECTION. A process this line did not recognise
    # incremented NEITHER `checked` NOR `unknown`, so it could never reach the
    # `(( unknown )) && return 2` leg; with nothing recognised at all the function fell
    # through to `return 1` — the value that AUTHORISES rewriting tasks.json — while a
    # session genuinely working in this checkout ran on. The evidence string printed
    # `examined=0` honestly; the return code did not, and `reconcile_tasks_json` reads
    # only the return code. That is precisely the sentence this function's own header
    # forbids: "'I could not tell' is never spelled like 'nobody'".
    # T302 drove it: the SAME live pid, with `command` reading `/Applications/Claude ...`
    # (a spaced install path; a `node .../cli.js` wrapper launch has the identical
    # signature) gave `examined=0 in-repo=0 -> 1 MAY RECONCILE`
    # [VERIFIED: .softhouse/reviews/T302/out/3-liveness-probe.txt, CASE 1].
    # THE FIX WIDENS RECOGNITION, AND DELIBERATELY NOT THE RETURN. Two other repairs were
    # considered and REJECTED, because the direction matters more than the tidiness:
    #   * "examined=0 => return 2" — the obvious one-liner, and WRONG. Zero claude
    #     processes on the host is a perfectly establishable "nobody", and it is the
    #     NORMAL state on the wrapper's exit path after its own driver has been waited on
    #     (T302 F11 measured exactly ONE in-repo `claude` during a live fire: the driver).
    #     Returning 2 there would refuse every normal-tail reconcile and make T288's whole
    #     repair inert — replacing a fail-OPEN with a permanent fail-CLOSED, which is the
    #     failure T288 was written to remove.
    #   * "lsof every live process, decide on cwd alone" — correct in principle and
    #     unaffordable: /bin/ps lists hundreds of processes here and this runs inside a
    #     ~7s signal budget. It would also REFUSE on any shell or editor sitting in the
    #     repo, which is F3b made worse.
    # So the candidate test is widened from "basename is exactly claude" to "basename is
    # claude, OR the command line mentions claude anywhere". That is cheap (a string
    # test, no extra process), it is bounded (the lsof cost follows the number of MATCHES,
    # not the size of the table), and every widening of it can only add REFUSALS.
    [[ "$st" == Z* ]] && continue                 # a zombie is dead, merely unreaped
    # NOTE ON THE `local` PLACEMENT: `named` and `mentions` are declared with the other
    # locals at the top of this function, NOT here. Under zsh 5.9 a bare `local x` inside
    # a loop body, when x already exists at this scope, PRINTS `x=<value>` to stdout — the
    # leak that put a raw lsof line into the fire log the first time this function was
    # driven. Declaring in the loop would reintroduce it.
    named=0; mentions=0
    [[ "${first:t}" == claude ]] && named=1       # the CLI, not /Applications/Claude.app
    # TWO STAGES, and the second one exists because the FIRST DRAFT OF THIS WIDENING WAS
    # A SUBSTRING TEST AND ITS OWN HARNESS CAUGHT IT: `*claude*` matches `notaclaude`,
    # `claudette`, and any path that merely contains the letters. Over-matching here only
    # ever adds REFUSALS, so it is the safe direction -- but a probe that refuses on
    # unrelated processes drifts into the permanent inertness of F3b, which is the other
    # failure this function has. So: a cheap substring pre-filter to skip the ~600 rows of
    # a real process table, then an exact PATH-SEGMENT test on the few that survive it.
    # A segment equal to `claude` matches `/Applications/Claude Code/claude`,
    # `node /opt/claude/cli.js` and `~/.local/bin/claude`; it does not match `notaclaude`.
    if (( ! named )) && [[ "${line:l}" == *claude* ]]; then
      for seg in ${=${${line:l}//\// }}; do
        [[ "$seg" == claude || "$seg" == claude.* ]] && { mentions=1; break }
      done
    fi
    (( named || mentions )) || continue
    (( named )) || (( unnamed++ ))
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
  FOREIGN_SESSIONS="claude processes examined=$checked (of which ${unnamed} matched only by MENTIONING claude, not by executable name) in-repo=$found unreadable=$unknown --$FOREIGN_SESSIONS"
  (( found ))   && return 0
  (( unknown )) && return 2
  # examined=0 STILL returns 1, and T319 says so out loud rather than leaving it to be
  # rediscovered: with the widened candidate test above, "no process on this table so
  # much as mentions claude" IS an establishable absence, and it is the normal state on
  # the wrapper's exit path. The unestablishable case is now `unknown`, one line up.
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
  # T319 — F7. THIS LINE IS THE ONLY PLACE IN THE PROGRAM ENTITLED TO PASS THAT FLAG, and
  # it is passed HERE rather than at the top of the function on purpose: it is reachable
  # only after `foreign_live_session_in_repo` returned 1, which is the probe that makes
  # the assertion true. Before T319 `ready-tasks.py` granted `wrapper` mode -- demote
  # everything -- to ANY caller the moment `.softhouse/LOCK` was not on disk, and the
  # justification for that authority was this probe, which lives in THIS file and is run
  # by exactly one caller. The precondition is now supplied by the caller that satisfies
  # it instead of assumed by the callee about everybody.
  # Normally the LOCK IS on disk here (on_signal deliberately reconciles before
  # release_lock), so this flag changes nothing; it matters in the window where the
  # lock file is missing anyway -- e.g. the `cat > "$LOCK"` whose rc is not read.
  local -a args; args=(--reconcile --fire "$STAMP" --repo "$REPO"
                       --no-live-session-established-out-of-band)
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
    4) RECON_VERDICT="REFUSED by ready-tasks.py and NOTHING was changed — either the caller could not be established as the lock holder, or it ran in \`in_session\` mode and no in_progress task passed all three ownership terms (inherited at the lock commit, not rewritten by this fire since, named with --corpse) (T309/T319). Read the reconcile| lines: they name which term failed, per task." ;;
    *) RECON_VERDICT="ready-tasks.py exited $rc (unexpected)" ;;
  esac
  (( rc == 0 )) || log "ERROR: reconcile did not complete — $RECON_VERDICT"
  return 0
}

# --------------------------------------------- T324: the prune blind-spot gate ---
# T324-PRUNE-BLINDSPOT-GUARD BEGIN
#   (marker: .softhouse/capture/t324-worktree-prune-skipbit/instruments/
#    20-blindspot-guard-drive.zsh EXTRACTS the lines between these two markers and
#    drives THE SHIPPED BYTES. Do not delete or reword the markers; the instrument
#    refuses to run if it cannot find them, rather than testing a copy.)
#
# WHAT WENT WRONG, AND THE WORD THAT WENT WRONG IS "INDEPENDENT".
# ------------------------------------------------------------------------------
# Until T324 the prune path had three checks and the comment below (still there,
# now corrected) called the third of them "a THIRD, independent clean check":
#
#   1. `wt_prune_check` rule 1 — `git merge-base --is-ancestor`
#   2. `wt_prune_check` rule 2 — `git status --porcelain`
#   3. `git worktree remove` without `--force`, which refuses on a dirty tree
#
# THEY ARE NOT INDEPENDENT. Checks 2 and 3 both ask ONE oracle the SAME question:
# "git, compare the working tree against the index". A git index SKIP BIT
# (`git update-index --assume-unchanged` or `--skip-worktree`) TURNS THAT
# COMPARISON OFF for a path. It moves no ref, no HEAD, no config and no commit, so
# there is nothing for check 1 to see either. One bit therefore blinds all three
# AT THE SAME INSTANT.
#
# THAT IS WORSE THAN HAVING ONE CHECK, NOT BETTER. Three checks that fail
# independently would agree only by coincidence, so agreement is evidence. Three
# checks that share an oracle agree by construction, and their agreement is read
# as strong evidence when it carries no more information than the single check
# they are all restating. The redundancy did not add safety; it added CONFIDENCE
# it had not earned, and the confidence is what let the removal proceed.
#
# DRIVEN, END TO END, NOT REASONED:
#   T318, evidence/50-prune-mitigation-drive.txt — `wt_prune_check` answered
#   PRUNE, `git worktree remove` returned rc=0, and a worktree holding 61 bytes of
#   irreplaceable worker output was DESTROYED.
#   T324, evidence/10-taxonomy.txt — reproduced on git 2.50.1 (Apple Git-155) for
#   `--assume-unchanged`, for `--skip-worktree`, and for both bits at once.
#
# WHAT THIS FUNCTION ADDS, AND WHY IT IS ACTUALLY INDEPENDENT
# ------------------------------------------------------------------------------
# It does not ask git to compare anything. It reads THE INDEX'S OWN PER-ENTRY
# BITS — the very state that switches the comparison off. A term cannot be
# silenced by the mechanism it is looking at, which is the property the other
# three lack and the only reason this one is worth adding.
#
#   TERM 1  `git ls-files -v` — REFUSE if any entry's tag is not `H`.
#           MEASURED TAG LETTERS, not read off a man page (T324 instrument 10):
#             --assume-unchanged            -> `h`  (lowercase of the normal tag)
#             --skip-worktree               -> `S`  (UPPERCASE)
#             both bits set together        -> `h`  (assume-unchanged wins the display)
#           SO THE RULE MUST BE "TAG != H", NEVER "TAG IS LOWERCASE". A
#           lowercase-only rule reads as the natural one and would sail past
#           `--skip-worktree` — the exact shape the T324 brief demanded be settled
#           by experiment rather than by assumption. Both bits produce identical
#           destruction; only their letters differ.
#
#   TERM 2  `git status --porcelain -uall` — REFUSE if anything is listed.
#           This is NOT a restatement of `wt_prune_check` rule 2, and the
#           difference is the whole point: worktree-local
#           `status.showUntrackedFiles=no` makes a bare `--porcelain` report CLEAN
#           with live untracked files on disk, and `git worktree remove` inherits
#           that config and destroys them (T324 instrument 10, shape H, measured
#           rc=0 with 56 bytes lost). `-uall` is a command-line override and is
#           immune to it.
#           `git -c status.showUntrackedFiles=normal` was measured to defeat the
#           same config equally well, and is DELIBERATELY NOT STACKED ON TOP.
#           It defends the same threat by the same mechanism — config precedence —
#           so the pair would be one term wearing two hats, which is the exact
#           error this whole comment exists to name. One term, chosen and stated.
#
# DIRECTION — FAIL CLOSED, AND THE ASYMMETRY IS THE ARGUMENT, NOT A PREFERENCE.
# ------------------------------------------------------------------------------
# Refusing to prune a worktree that was in fact disposable costs a directory on
# disk and a reader's patience, and the next fire re-evaluates it. Pruning one
# that was not destroys work that exists nowhere else — no ref, no reflog, no
# stash, no remote. The two errors differ by orders of magnitude AND by
# reversibility, so the tie is not a tie and it breaks toward KEEP.
#
# BUT T319 RECORDED THE COUNTER-CONSIDERATION AND IT IS HONOURED HERE. Its F3a
# note rejects a repair that would "replace a fail-OPEN with a permanent
# fail-CLOSED, which is the failure T288 exists to remove." A prune check that
# refuses everything has traded a rare catastrophe for a permanent one: the
# wrapper's cleanup becomes inert and worktrees accumulate without bound, which
# is T213's original defect restored. So the refusal here is NARROW by
# construction and its cost is MEASURED, not asserted:
#   - it fires only on evidence that git's own comparison has been switched off
#     for this worktree, or that something untracked is really there;
#   - a genuinely clean worktree is untouched (instrument 10 shape A: `H-only`,
#     no untracked, still PRUNE — the control that proves it is not inert);
#   - live-checkout census of all 55 linked worktrees, read-only
#     (evidence/30-live-worktree-census.txt): ZERO of 55 carry a non-'H' index
#     tag, so TERM 1's refusal cost on the current population is EXACTLY NOTHING.
#     6 of 55 carry untracked content, and every one of those was ALREADY being
#     kept by `wt_prune_check` rule 2, so TERM 2 adds no refusal either — it
#     changes the answer only where config has hidden those files from rule 2.
#
# KNOWN LIMIT, STATED RATHER THAN IMPLIED (P-66's rule: "'NOT FOUND' is a
# statement about the search, never about the world"). This closes the SKIP-BIT
# chain and the untracked-config chain. It does NOT close GITIGNORED content:
# instrument 10 shape G shows `status` CLEAN, `ls-files -v` `H-only`,
# `git worktree remove` rc=0, and 35 bytes of a gitignored file destroyed. That is
# a real kill shape, and it is a FOLLOW-UP (FU-T324-1) rather than something
# fixed here.
#
# THE REASON IS NOT THE ONE THAT WAS FIRST WRITTEN HERE, AND THE MEASUREMENT IS
# WHY. The draft of this comment said an ignored-file term "would refuse
# essentially every worktree in this repo". The census says otherwise: 3 of 55.
# That is not inertness and the claim is withdrawn. The actual reason to decide
# that term deliberately instead of reflexively is WHAT the ignored paths are —
# measured, they are `.claude/worktrees/` (the directory every worktree lives in,
# an artefact of the layout) and `.softhouse/toolchain/`, which `.gitignore`
# itself annotates "NOT committed — reversible with `rm -rf
# .softhouse/toolchain`". A gate that refuses on content the repository declares
# reproducible is refusing for a reason uncorrelated with whether work exists,
# and its refusal rate is not stable: it grows with whatever build output a later
# task adds to `.gitignore`. So it is a real decision with a real trade-off,
# taken by whoever holds that task, with the numbers in front of them.
#
# Returns 0 = no blind-spot evidence, removal may proceed.
#         1 = REFUSE; prints the reason. Every git failure resolves to 1
#             (fail-closed): "I could not read the index" is never "the index is
#             clean", the same T190/T202 polarity discipline as the rest of this
#             file and of lib-worktree-prune.zsh.
wt_prune_blindspot_check() {
  local W="$1"
  if [[ -z "$W" || ! -d "$W" ]]; then
    print -r -- "REFUSE: blind-spot check got no readable worktree path (${W:-<empty>})"
    return 1
  fi

  # --- TERM 1: the index's own per-entry bits ---------------------------------
  # Exit status captured on its own line, BEFORE the output is looked at, and the
  # filtering is done with a zsh array subscript rather than a pipeline — T190's
  # rule in this file: under `set -uo pipefail` without `-e`, a pipeline reports
  # the RIGHTMOST status, so `git-fails | filter-finds-nothing` is byte-identical
  # to `git-succeeds | filter-finds-nothing`. No pipeline, no conflation.
  local LSV LSV_RC
  LSV=$(git -C "$W" ls-files -v -- ':(top)' 2>/dev/null)
  LSV_RC=$?
  if (( LSV_RC != 0 )); then
    print -r -- "REFUSE: could not read the index of $W (git ls-files -v rc=$LSV_RC) — an unreadable index is not evidence of an unmarked one"
    return 1
  fi
  local -a LSV_LINES MARKED
  LSV_LINES=(${(f)LSV})
  MARKED=(${LSV_LINES:#H *})
  if (( ${#MARKED} > 0 )); then
    print -r -- "REFUSE: $W has ${#MARKED} index entries carrying a NON-'H' git index tag — a skip bit (\`--assume-unchanged\` -> 'h', \`--skip-worktree\` -> 'S') switches OFF the working-tree comparison that BOTH the porcelain clean check AND \`git worktree remove\` rely on, so all of them would report clean while live content sits on disk. First 5: ${(j:, :)MARKED[1,5]}"
    return 1
  fi

  # --- TERM 2: untracked content, immune to status.showUntrackedFiles ---------
  local UNTR UNTR_RC
  UNTR=$(git -C "$W" status --porcelain -uall -- ':(top)' 2>/dev/null)
  UNTR_RC=$?
  if (( UNTR_RC != 0 )); then
    print -r -- "REFUSE: \`git status --porcelain -uall\` failed inside $W (rc=$UNTR_RC) — refusing to treat an unanswerable tree as an empty one"
    return 1
  fi
  if [[ -n "$UNTR" ]]; then
    local -a U; U=(${(f)UNTR})
    print -r -- "REFUSE: $W has ${#U} path(s) that \`git status --porcelain -uall\` reports and a bare \`--porcelain\` can be configured not to (\`status.showUntrackedFiles=no\`). First 5: ${(j:, :)U[1,5]}"
    return 1
  fi

  return 0
}
# T324-PRUNE-BLINDSPOT-GUARD END

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
  # T325 — GATE 3 OF FIVE. `[[ -n "$WS" ]] || continue` is this sweep's whole
  # theory of "there is nothing here to rescue", and it is `git status
  # --porcelain` again: the same predicate T318 drove CLEAN through nine
  # destruction shapes. In a worktree the shape that matters is the index skip
  # bit, because it makes the sweep skip the worktree AND (before T324) let the
  # prune loop delete it — the sweep's silence was the first link of that chain.
  #
  # WHY A SURVEY AND NOT THE DIFFERENTIAL `compare` HERE, stated so the asymmetry
  # is a decision and not an omission: the worktrees that most need this are the
  # ones a worker CREATED during the fire now ending, so no "before" snapshot of
  # them can exist. `wt_prune_blindspot_check` (T324, defined above, already
  # fixture-driven against the shipped bytes) is exactly the single-state subset
  # that applies, so it is REUSED rather than reimplemented — a second copy of a
  # rule is a rule that will disagree with itself later.
  #
  # DETECTIVE, NOT CORRECTIVE. It logs; it does not clear the skip bit and does
  # not commit behind the worker's back. Clearing an index bit in a worktree that
  # may still have a live agent in it is a mutation this sweep has no writ for,
  # and the destruction it would guard against is already blocked one loop below
  # by T324's prune override. One fire of delay, not destruction — the same trade
  # the signal path already makes for the whole sweep.
  # T325-SWEEP-HIDDENWORK-GUARD BEGIN
  #   (marker: .softhouse/capture/t325-adopt-attestation/instruments/
  #    40-sweep-gate-drive.zsh EXTRACTS the lines between these two markers and
  #    drives THE SHIPPED BYTES, the discipline T324 established for its own
  #    guard. Do not delete or reword the markers; the instrument REFUSES to run
  #    if it cannot find them, rather than quietly testing a copy of the rule.)
  if [[ -z "$WS" ]]; then
    local BS_OUT BS_RC
    BS_OUT=$(wt_prune_blindspot_check "$W"); BS_RC=$?
    if (( BS_RC != 0 )); then
      log "ERROR: worktree $(basename "$W") reads CLEAN to this sweep's \`git status --porcelain\`, and the hidden-work terms DISAGREE — $BS_OUT"
      log "       NOT rescued: this sweep will not clear an index bit or commit inside a worktree that may still hold a live agent. The prune loop below KEEPS it (T324), so nothing is destroyed — but the content is uncommitted and invisible to the next fire. Inspect $W by hand."
    fi
    continue
  fi
  # T325-SWEEP-HIDDENWORK-GUARD END
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
  # T319 — F2. THE TWIN'S TWIN, AND ALL THREE RETURN CODES WERE THROWN AWAY.
  # These three commands used to run with `2>/dev/null` / `>/dev/null 2>&1` and NO rc
  # read, followed by an UNCONDITIONAL `log "rescued $WN -> $WB"`. T202 fixed exactly this
  # shape 100 lines above, in the MAIN-TREE rescue at the top of this same function, where
  # ADD_RC and COMMIT_RC are read and a failure logs "NOTHING was rescued"; the fix was
  # applied to one branch of the function and not the other.
  # T302 drove the unfixed branch against the population it serves — a SIGKILLed worker,
  # which leaves the stale `.git/worktrees/<name>/index.lock` that a `git add` interrupted
  # by a signal leaves behind: checkout rc=128, add rc=128, commit rc=128, and the wrapper
  # logged `rescued agent-deadbeef -> softhouse/rescued-agent-deadbeef-...` for a branch
  # that DOES NOT EXIST, over a worktree that was still dirty
  # [VERIFIED: .softhouse/reviews/T302/out/2-phantom-rescue.txt].
  # T288 made that worse than a wrong log line: it appended the pair to RESCUE_PAIRS, and
  # `ready-tasks.py --rescue` writes it into the task's PERMANENT note as evidence — "swept
  # onto <branch> by this fire's worktree sweep". The blast radius went up and the
  # verification did not. An unverified rescue must never become evidence.
  # POLARITY: fail-CLOSED. Any non-zero rc means NOTHING was rescued, it is logged as
  # such naming the rc, and NO pair is appended. A genuinely successful rescue is
  # unchanged.
  local CO_RC ADD_RC CM_RC
  git -C "$W" checkout -q -b "$WB" 2>/dev/null; CO_RC=$?
  git -C "$W" add -A >/dev/null 2>&1; ADD_RC=$?
  git -C "$W" -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \
      commit -q -m "RESCUED: WIP from a worker that never signalled done (fire $STAMP)

Committed by the orchestrator's worktree sweep. Completeness UNVERIFIED — no handoff was written. Treat as partial until re-reviewed." >/dev/null 2>&1; CM_RC=$?
  if (( CO_RC != 0 || ADD_RC != 0 || CM_RC != 0 )); then
    log "ERROR: NOTHING was rescued from $WN — git failed (checkout rc=$CO_RC, add rc=$ADD_RC, commit rc=$CM_RC). The branch $WB may not exist and the worktree is still dirty with $WD uncommitted path(s). This is NOT paired into any task note, because an unverified rescue must not become evidence. Inspect $W by hand."
    continue
  fi
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
# T324 CORRECTION — THIS COMMENT USED TO CLAIM SOMETHING THAT IS MEASURED FALSE,
# AND THE CLAIM IS THE DEFECT. It read:
#
#     "`git worktree remove` (no --force) is itself a THIRD, independent clean
#      check — git refuses if it finds modifications we somehow missed"
#
# `git worktree remove` IS A THIRD CHECK. IT IS NOT AN INDEPENDENT ONE. It asks
# git to compare the working tree against the index — the same question
# `wt_prune_check`'s rule 2 asks, of the same oracle. A single index skip bit
# (`git update-index --assume-unchanged` / `--skip-worktree`) switches that
# comparison off, and because a skip bit moves no ref, no HEAD, no config and no
# commit, rule 1 cannot see it either. ONE BIT BLINDS ALL THREE SIMULTANEOUSLY,
# and T318 drove it end to end: PRUNE, then rc=0, then a worktree destroyed with
# 61 bytes of irreplaceable worker output in it
# (.softhouse/capture/t318-committed-clobber-blindness/evidence/
#  50-prune-mitigation-drive.txt).
#
# Counting checks is not measuring safety. Three checks sharing one oracle are
# ONE check that has been read three times, and the agreement between them is
# read as corroboration when it is only repetition — which is why this comment
# made the situation worse than a single honest check would have.
#
# `git worktree remove` is still called without `--force`, and it is still worth
# having: it is the term that catches a plain untracked file (instrument 10 shape
# F: rc=128, content survives) and a worktree locked between our check and this
# call. It is simply not a second opinion about a tree that git has been told to
# stop looking at. `wt_prune_blindspot_check` above is the term that IS
# independent, because it reads the skip bits themselves rather than the
# comparison they suppress.
local WT_PRUNED=0 WT_KEPT=0
local i W BR WLK VERDICT VERDICT_RC RM_OUT RM_RC BSPOT BSPOT_RC
for (( i = 1; i <= ${#WT_PATHS}; i++ )); do
  W="${WT_PATHS[$i]}"
  BR="${WT_BRANCHES[$i]}"
  WLK="${WT_LOCKED[$i]}"
  VERDICT=$(wt_prune_check "$W" "$BR" main "$WLK")
  VERDICT_RC=$?
  # T324: a PRUNE verdict from wt_prune_check is NECESSARY, not sufficient. Its
  # two rules read refs and the porcelain comparison; neither can see the index
  # bit that disables the comparison. Ask the independent term before acting.
  if (( VERDICT_RC == 0 )); then
    BSPOT=$(wt_prune_blindspot_check "$W")
    BSPOT_RC=$?
    if (( BSPOT_RC != 0 )); then
      # Fold into the existing verdict variables so the single `keep:` line
      # below reports it once, with WT_KEPT counted once. The prefix names the
      # override so a log reader can see that two checks DISAGREED — the case
      # that matters, and the one a silent downgrade would hide.
      VERDICT_RC=$BSPOT_RC
      VERDICT="T324 BLIND-SPOT OVERRIDE (wt_prune_check said PRUNE) — $BSPOT"
    fi
  fi
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

# T325 — GATE 2 OF FIVE, AND THE ONE THE TASK CALLS MOST IMPORTANT: this
# function IS the driver's STEP 5.5 in executable form. Everything above has now
# happened — the deliverable rescue, the worktree sweep, the tasks.json
# reconcile, the RESUME.md banner, the wrapper's own commit and the push — so
# this is the last moment at which the fire can say anything about what it did to
# the repository. Until now the only thing it could say was `git status
# --porcelain`, which T318 measured to be CLEAN on a re-inited repo with a forged
# identity and a committed clobber. It is called AFTER the push deliberately:
# the push moves `refs/remotes/origin/main`, and a gate that cannot see its own
# protocol's final step is a gate nobody will keep.
attest_exit_protocol
}

# --------------------------------------------------------------- chain loop ---
while (( CHAIN_N < CHAIN_MAX )); do
  HEAD_BEFORE=$(git rev-parse HEAD)
  # T325 — the BEFORE half of the exit-protocol attestation, taken PER ITERATION
  # rather than per fire. A chained fire runs the driver up to CHAIN_MAX times and
  # `run_exit_guard` after each one, so a per-fire baseline would attribute
  # iteration 3's damage to a window that also contains iterations 1 and 2 and
  # would blur exactly the attribution the guard exists to provide.
  # Cost, measured rather than assumed (T318 left it Unverified-6): 1.08s wall on
  # this repo at 7,391 tracked files and 612 refs — against a fire whose
  # foreground child runs for hours.
  ATTEST_BEFORE="$ATTEST_DIR/attest-$STAMP-iter$((CHAIN_N+1)).before"
  attest_run "attest-before" snapshot "$REPO" "$ATTEST_BEFORE"
  if (( $? != 0 )); then
    log "WARN: could not take the pre-driver repo-state snapshot for iteration $((CHAIN_N+1)) — this iteration will end UNATTESTED (which is not the same as clean)."
    ATTEST_BEFORE=""
  fi
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
