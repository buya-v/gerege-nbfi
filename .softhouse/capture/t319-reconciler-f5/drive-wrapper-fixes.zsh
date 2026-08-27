#!/bin/zsh
# T319 -- DRIVE THE TWO fire-program.sh REPAIRS, on their own bytes.
#
# PART A -- F3a. `foreign_live_session_in_repo()` is cut out of fire-program.sh by line
# range and eval'd, T302's technique, so nothing is paraphrased. Exactly ONE edit is made
# and it is declared: the absolute token `/bin/ps` is rebound to a shim, because the
# function calls ps by absolute path and PATH cannot reach it. The subject row carries the
# pid of a genuinely live process, because the function does `kill -0` on every candidate
# and a fabricated pid would be discarded for the wrong reason -- proving nothing.
#
# PART B -- F2. The worktree rescue's three git commands, driven against the population
# they serve: a worktree holding an uncommitted deliverable with the stale
# `.git/worktrees/<name>/index.lock` that a `git add` interrupted by SIGKILL leaves behind.
#
# Nothing outside $TMPDIR is written. The real repo is READ ONLY. No signal is sent to any
# process this script did not start.
set -uo pipefail
SRC="${0:A:h}/../../bin/fire-program.sh"
PASS=0; FAIL=0

ck() {  # $1 = label, $2 = expected, $3 = observed
  if [[ "$2" == "$3" ]]; then print -r -- "    >>> OK   $1 (= $3)"; PASS=$((PASS+1))
  else print -r -- "    >>> **WRONG** $1: expected $2, observed $3"; FAIL=$((FAIL+1)); fi
}

print -r -- "=============================================================="
print -r -- "PART A -- F3a: the candidate filter, on foreign_live_session_in_repo's bytes"
print -r -- "=============================================================="
FIRST=$(/usr/bin/grep -n '^foreign_live_session_in_repo() {' "$SRC" | cut -d: -f1)
LAST=$(/usr/bin/awk -v s="$FIRST" 'NR>=s && $0=="}" {print NR; exit}' "$SRC")
print -r -- "cut lines $FIRST-$LAST of $SRC"
BODY=$(/usr/bin/sed -n "${FIRST},${LAST}p" "$SRC")

REPO=${REPO:-/Users/buv/gerege-nbfi}
FOREIGN_SESSIONS=""
typeset -ga STOPPED_TREE; STOPPED_TREE=()
SB=$(mktemp -d /tmp/t319probe.XXXXXX)

# A genuinely live process to be the subject. `kill -0` must succeed on it, and it must
# NOT be this shell: the function skips `pid == $$` by design, and using $$ made the first
# draft of this harness report examined=0 for every case -- the subject was being skipped
# for the right reason and the harness read it as the defect. Recorded because it is the
# same "a zero that means something else" trap the code under test is about.
/bin/sleep 120 &
LIVE=$!
trap 'kill $LIVE 2>/dev/null' EXIT INT TERM
print -r -- "live subject: pid $LIVE (a /bin/sleep this script started, and only that)"

mkshim_ps() {   # $1 = dir, $2 = the one subject row
  local d="$1" row="$2"
  mkdir -p "$d"
  { print -r -- '#!/bin/sh'
    print -r -- "cat <<'TBL'"
    print -r -- '    1 Ss   /sbin/launchd'
    print -r -- '  400 Ss   /usr/libexec/logd'
    print -r -- '  900 S    /usr/sbin/cupsd'
    print -r -- "$row"
    print -r -- 'TBL' ; } > "$d/ps"
  chmod +x "$d/ps"
}
mkshim_lsof() { # $1 = dir, $2 = cwd to report
  local d="$1" c="$2"
  mkdir -p "$d"
  { print -r -- '#!/bin/sh'; print -r -- 'echo p0'; print -r -- 'echo fcwd'
    print -r -- "echo n$c" ; } > "$d/lsof"
  chmod +x "$d/lsof"
}
run_case() {    # $1 = ps shim path, $2 = lsof shim path
  local b="${BODY//\/bin\/ps/$1}"
  LSOF_BIN="$2"
  eval "$b"
  foreign_live_session_in_repo
  local rc=$?
  print -r -- "    evidence: $FOREIGN_SESSIONS"
  print -r -- "    rc=$rc"
  return $rc
}

# CASE 1 -- T302's CASE 1: a live session whose f[3] has no `claude` basename, because the
# install path contains a space. A `node .../cli.js` wrapper launch has the same shape.
print -r -- ""
print -r -- "CASE 1  live session, command '/Applications/Claude Code/claude --resume', cwd IN-REPO"
print -r -- "        (pre-T319 this matched NOTHING: examined=0 -> return 1 = MAY RECONCILE)"
mkshim_ps  "$SB/c1" " $LIVE S    /Applications/Claude Code/claude --resume"
mkshim_lsof "$SB/c1" "$REPO"
run_case "$SB/c1/ps" "$SB/c1/lsof"; RC=$?
ck "rc (0 = a live foreign session was found, caller must NOT reconcile)" 0 $RC

# CASE 2 -- a node-launched CLI, cwd elsewhere. Must be EXAMINED and then dismissed by cwd,
# not skipped unseen.
print -r -- ""
print -r -- "CASE 2  live 'node /opt/claude/cli.js', cwd ELSEWHERE"
mkshim_ps  "$SB/c2" " $LIVE S    node /opt/claude/cli.js --print"
mkshim_lsof "$SB/c2" "/Users/buv"
run_case "$SB/c2/ps" "$SB/c2/lsof"; RC=$?
ck "rc (1 = examined and dismissed on CWD, not skipped unseen)" 1 $RC

# CASE 3 -- a process whose name merely CONTAINS the letters. Must NOT be examined:
# absence stays establishable, and this is the case that killed the first draft of the
# widening (a bare `*claude*` substring test), caught by this harness and not by reading.
print -r -- ""
print -r -- "CASE 3  live '/usr/sbin/notaclaude', which merely CONTAINS the letters"
mkshim_ps  "$SB/c3" " $LIVE S    /usr/sbin/notaclaude --serve"
print -r -- "        (a bare *claude* substring test matches this; a PATH-SEGMENT test does not)"
mkshim_lsof "$SB/c3" "$REPO"
run_case "$SB/c3/ps" "$SB/c3/lsof"; RC=$?
ck "rc (1 = substring-only match must NOT count; `notaclaude` is not claude)" 1 $RC

# CASE 4 -- control: a plain `claude` basename, cwd in repo. Unchanged behaviour.
print -r -- ""
print -r -- "CASE 4  control: '/Users/buv/.local/bin/claude -p ...', cwd IN-REPO"
mkshim_ps  "$SB/c4" " $LIVE S    /Users/buv/.local/bin/claude -p /softhouse-program"
mkshim_lsof "$SB/c4" "$REPO"
run_case "$SB/c4/ps" "$SB/c4/lsof"; RC=$?
ck "rc (0 = unchanged from before T319)" 0 $RC

rm -rf "$SB"

print -r -- ""
print -r -- "=============================================================="
print -r -- "PART B -- F2: the rescue's three return codes, against a stale index.lock"
print -r -- "=============================================================="
W=$(mktemp -d /tmp/t319resc.XXXXXX)
(
  cd "$W"
  git init -q -b main main >/dev/null 2>&1
  cd main
  git config user.email t319@local; git config user.name T319
  print -r -- seed > seed.txt; git add -A; git commit -q -m seed
  git worktree add -q -b worker ../wt >/dev/null 2>&1
) || { print -r -- "could not build the fixture"; exit 1 }
print -r -- "deliverable, uncommitted" > "$W/wt/deliverable.md"
# The stale lock a SIGKILLed `git add` leaves behind, at the LINKED worktree's own gitdir.
LOCKD=$(git -C "$W/wt" rev-parse --git-dir)
print -r -- "stale" > "$LOCKD/index.lock"
print -r -- "planted stale index.lock at $LOCKD/index.lock"

# The three commands, verbatim from the sweep, with their rcs read as T319 now reads them.
STAMP=20260828-t319
WB="softhouse/rescued-agent-t319-$STAMP"
git -C "$W/wt" checkout -q -b "$WB" 2>/dev/null; CO_RC=$?
git -C "$W/wt" add -A >/dev/null 2>&1; ADD_RC=$?
git -C "$W/wt" -c user.name=Buyan -c user.email=b@l commit -q -m "RESCUED" >/dev/null 2>&1; CM_RC=$?
print -r -- "    checkout rc=$CO_RC   add rc=$ADD_RC   commit rc=$CM_RC"
if (( CO_RC != 0 || ADD_RC != 0 || CM_RC != 0 )); then
  VERDICT="NOTHING was rescued"
else
  VERDICT="rescued"
fi
print -r -- "    T319 logs: $VERDICT"
print -r -- "    pre-T319 logged UNCONDITIONALLY: rescued agent-t319 -> $WB"
BR=$(git -C "$W/main" branch --list "$WB" | wc -l | tr -d ' ')
DIRTY=$(git -C "$W/wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
print -r -- "    GROUND TRUTH: branch '$WB' exists? $BR   worktree still dirty? $DIRTY path(s)"
ck "verdict matches ground truth (branch absent => NOTHING was rescued)" "NOTHING was rescued" "$VERDICT"
ck "no RESCUE_PAIRS entry would be appended (T319 'continue's before it)" 0 $BR
rm -rf "$W"

print -r -- ""
print -r -- "=============================================================="
print -r -- "T319 wrapper drives: $PASS correct, $FAIL wrong"
print -r -- "=============================================================="
(( FAIL == 0 ))
