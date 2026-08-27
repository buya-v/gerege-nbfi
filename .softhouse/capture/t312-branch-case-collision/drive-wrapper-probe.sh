#!/bin/bash
# T312 -- drive fire-program.sh's NEW two preflight lines, against a SCRATCH repo.
#
# WHY A SCRATCH REPO.  A live fire holds .softhouse/LOCK on /Users/buv/gerege-nbfi while
# this task runs, and `install-hook` writes into that repo's shared .git/hooks.  Driving
# the wrapper at the real checkout would install an unreviewed hook under a live fire's
# feet.  So GEREGE_NBFI_REPO is pointed at a throwaway clone; `--probe` exits before the
# lock, the pull and the driver, so nothing else in the wrapper is exercised.
#
# Usage: bash .softhouse/capture/t312-branch-case-collision/drive-wrapper-probe.sh
set -u
BIN="$(cd "$(dirname "$0")/../../bin" && pwd)"
S="$(mktemp -d "${TMPDIR:-/tmp}/t312-probe.XXXXXX")"
R="$S/repo"

mkdir -p "$R"
git -C "$R" init -q -b main
git -C "$R" config user.email t312@example.invalid
git -C "$R" config user.name T312
echo x > "$R/f"
git -C "$R" add -A
git -C "$R" commit -q -m base
git -C "$R" branch softhouse/T400-has-work main
git -C "$R" commit -q --allow-empty -m "work on T400"
git -C "$R" branch -f softhouse/T400-has-work HEAD
git -C "$R" pack-refs --all --prune
git -C "$R" update-ref refs/heads/softhouse/t400-has-work main    # the shadow

echo "=== the scratch repo, before the wrapper runs"
git -C "$R" rev-parse softhouse/T400-has-work softhouse/t400-has-work
ls "$R/.git/hooks/reference-transaction" 2>&1

echo
echo "=== fire-program.sh --probe  (GEREGE_NBFI_REPO=$R, CLAUDE_BIN stubbed)"
GEREGE_NBFI_REPO="$R" \
LOG_DIR="$S/logs" \
CLAUDE_BIN=/bin/echo \
FINERACT_SRC="$S" \
zsh "$BIN/fire-program.sh" --probe 2>&1 | grep -E 'refguard\||sweep\||probe only|fire start'
echo "[wrapper exit ${PIPESTATUS[0]}]"

echo
echo "=== after: is the guard installed, and does it now refuse a NEW shadow?"
ls -l "$R/.git/hooks/reference-transaction"
echo "-- first, the case git ALREADY refuses on its own: a LOOSE ref against a LOOSE ref."
git -C "$R" branch softhouse/T401-new-shadow main
git -C "$R" branch softhouse/t401-new-shadow main
echo "   ^ 'already exists' came from git, not from the guard: on a case-insensitive"
echo "     filesystem the two loose refs are one path, so git's own existence check hits."
echo "-- now the case git does NOT refuse: a loose ref against a PACKED ref."
git -C "$R" pack-refs --all --prune
ls "$R/.git/refs/heads/softhouse/" 2>&1
git -C "$R" branch softhouse/t401-new-shadow main
echo "   ^ THAT refusal is the guard.  Without it this is the silent success that hid"
echo "     T297's and T305's work."
echo
echo "scratch = $S"
