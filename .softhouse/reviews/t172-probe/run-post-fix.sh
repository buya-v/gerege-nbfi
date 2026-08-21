#!/bin/zsh
# Runs the REAL post-fix line-224 bytes (captured via
# `sed -n '224p' .softhouse/bin/fire-program.sh` on the T172 branch, into
# post-fix-line224.txt, committed alongside this script) against the SAME
# scratch git repo state built by setup-scratch-repo.sh. Never touches the
# live .softhouse/LOCK of the running fire.
set -uo pipefail
HERE="${0:A:h}"
SCRATCH=/tmp/t172-scratch-repo
[[ -d "$SCRATCH/.git" ]] || { echo "run setup-scratch-repo.sh first"; exit 1; }
cd "$SCRATCH" || exit 1

POST_LINE=$(cat "$HERE/post-fix-line224.txt")
echo "Post-fix line-224 (exact bytes from the T172 branch):"
echo "  $POST_LINE"
echo

echo "=== git status --porcelain (real, scratch repo, same state as pre-fix run) ==="
git status --porcelain
echo

DIRTY=$(git status --porcelain | LC_ALL=C grep -av '^?? \.softhouse/LOCK$' || true)
echo "DIRTY (post-fix pattern) ="
print -r -- "$DIRTY"
echo

if print -r -- "$DIRTY" | grep -q 'LOCKED_STATE.md'; then
  echo "VERDICT 1: sibling KEPT in DIRTY -- FIXED (GREEN)"
else
  echo "VERDICT 1: sibling still DROPPED from DIRTY -- FIX DID NOT WORK"
fi

if print -r -- "$DIRTY" | grep -qx '?? \.softhouse/LOCK'; then
  echo "VERDICT 2: real LOCK line present in DIRTY -- OVER-CORRECTED (guard would now be always-dirty on the real lock)"
else
  echo "VERDICT 2: real LOCK line correctly excluded from DIRTY -- not over-corrected"
fi
