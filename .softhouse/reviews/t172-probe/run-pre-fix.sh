#!/bin/zsh
# HISTORICAL RECORD ONLY -- NOT the live regression gate (T210, 22 Aug 2026).
#
# This replays BYTES captured at T172 time (pre-fix-line224.txt), frozen in
# this file. T190 subsequently deleted that exact grep-based guard from
# fire-program.sh and replaced it with a git-pathspec exclusion (see line
# ~313 of the live file) -- so this script's pattern now matches ZERO times
# against the current fire-program.sh (verified: `grep -c` for the pre-fix
# bytes against the live file returns 0). It still runs and still "passes"
# its own internal check, because it was never reading the live file to
# begin with -- it was always replaying a hand-transcribed copy. That is
# exactly the silently-stopped-testing failure P-22 / P-35 (patterns.md)
# warn about; keep this file as a historical record of the T172 bug, but
# use check-lock-exclusion-anchor.sh in this same directory for the LIVE
# gate -- it extracts and replays the CURRENT guard line by pattern (never
# a frozen transcript) and errors loudly if that pattern ever matches zero
# times again.
#
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
