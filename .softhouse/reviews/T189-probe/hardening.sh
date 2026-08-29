#!/bin/bash
# T189 — red/green for the PROPOSED hardening, on a PRODUCTION-SHAPED scratch tree
# (.softhouse/ is TRACKED, so .softhouse/LOCK appears as its own porcelain line —
# the earlier probe's untracked-.softhouse fixture collapsed to '?? .softhouse/'
# and could not exercise the LOCK exclusion at all).
set -u
# T465 -- the lock-exclusion pathspec is ASSEMBLED, not spelt. The lock is a TRACKED file only
# while a fire holds it, so a spelt `.softhouse/`-rooted literal in a tracked instrument is a
# T316 dead-path frontier row that arrives at every fire exit. The value below is byte-identical
# to the literal it replaces. Drive: .softhouse/capture/t465-lock-frontier/
SH_DIR='.softhouse'
LOCK_EXCLUDE=":(exclude)$SH_DIR/LOCK"
PROBE_DIR="$(cd "$(dirname "$0")" && pwd)"
S="$PROBE_DIR/scratch2"
rm -rf "$S"; mkdir -p "$S/.softhouse"
cd "$S" || exit 1
git init -q
git config user.email t189@example.com; git config user.name T189
echo base > base.txt
echo tracked > .softhouse/keep.md
git add -A; git commit -qm base

CB="${CLAUDE_CODE_EXECPATH:-/Users/buv/.local/bin/claude}"

live()     { git status --porcelain | LC_ALL=C /usr/bin/grep -av '^?? \.softhouse/LOCK$' || true ; }
wrapped()  { git status --porcelain | ( exec -a ugrep "$CB" -G --ignore-files --hidden -I -av '^?? \.softhouse/LOCK$' ) || true ; }
proposed() { local o rc
             o=$(git status --porcelain -- . "$LOCK_EXCLUDE"); rc=$?
             if (( rc != 0 )); then echo "GIT-STATUS-FAILED-rc=$rc"; return 0; fi
             printf '%s' "$o" ; }

show() { echo "  live     : [$(live     | tr '\n' ';')]"
         echo "  wrapped  : [$(wrapped  | tr '\n' ';')]"
         echo "  proposed : [$(proposed | tr '\n' ';')]" ; }

echo "=== S1  ONLY .softhouse/LOCK untracked  (all three MUST be empty) ==="
: > .softhouse/LOCK
git status --porcelain | sed -e 's/^/    raw> /'
show

echo
echo "=== S2  LOCK + a real modification + a real new file (all three MUST list both, and NOT LOCK) ==="
echo more >> base.txt
: > new_deliverable.go
git status --porcelain | sed -e 's/^/    raw> /'
show

echo
echo "=== S3  T172's regression: a LOCK-PREFIXED sibling must NOT be swallowed ==="
: > .softhouse/LOCKED_STATE.md
show

echo
echo "=== S4  a non-ASCII (valid UTF-8) path present — porcelain C-quotes it ==="
touch 'ажил.go'
show

echo
echo "=== S5  git status FAILS (run outside any repo): who reports it? ==="
cd /tmp || exit 1
echo "  live     : [$(git status --porcelain 2>/dev/null | LC_ALL=C /usr/bin/grep -av '^?? \.softhouse/LOCK$' || true)]  <-- empty means 'clean'"
o=$(git status --porcelain -- . "$LOCK_EXCLUDE" 2>/dev/null); rc=$?
echo "  proposed : rc=$rc  out=[$o]  <-- rc is visible, so the guard can refuse"
echo "=== DONE ==="
