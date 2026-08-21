#!/bin/zsh
# Runs the REAL pre-fix line-224 bytes (captured verbatim via
# `git show main:.softhouse/bin/fire-program.sh | sed -n '224p'` into
# pre-fix-line224.txt, committed alongside this script) against the scratch
# git repo built by setup-scratch-repo.sh. Never touches the live
# .softhouse/LOCK of the running fire.
set -uo pipefail
HERE="${0:A:h}"
SCRATCH=/tmp/t172-scratch-repo
[[ -d "$SCRATCH/.git" ]] || { echo "run setup-scratch-repo.sh first"; exit 1; }
cd "$SCRATCH" || exit 1

PRE_LINE=$(cat "$HERE/pre-fix-line224.txt")
echo "Pre-fix line-224 (exact bytes from main):"
echo "  $PRE_LINE"
echo

echo "=== git status --porcelain (real, scratch repo) ==="
git status --porcelain
echo

DIRTY=$(git status --porcelain | LC_ALL=C grep -av '^?? \.softhouse/LOCK' || true)
echo "DIRTY (pre-fix pattern) ="
print -r -- "$DIRTY"
echo

if print -r -- "$DIRTY" | grep -q 'LOCKED_STATE.md'; then
  echo "VERDICT: sibling survived in DIRTY -- no bug reproduced here"
else
  echo "VERDICT: sibling silently DROPPED from DIRTY -- BUG CONFIRMED RED, against real git status output"
fi
