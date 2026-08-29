#!/bin/bash
# T459 arm SKIPWT -- T454 named `--skip-worktree` / `--assume-unchanged` as an OPEN, UNDRIVEN
# route.  This drives it.  Attacker model: the worker runs the bar in its own worktree and
# publishes the transcript; the fraud is the transcript, not the commit.
set -u
. "$( cd "$( dirname "$0" )" && pwd )/drive.sh"
BASE="${1:-02fb1af4}"; MODE="${2:-skip-worktree}"
A="SKIPWT-$MODE"
arm "$A" "$BASE"
D="$( stage "$A" "$BASE" )" || exit 3
plant_unreg "$D/src"
( cd "$D/src" && git commit -q -m "T459 SKIPWT fixture: an unregistered checker" ) >/dev/null 2>&1 || exit 3
rm -rf "$D/graded"
git clone -q --no-hardlinks "$D/src" "$D/graded" >/dev/null 2>&1 || exit 3
G="$D/graded"

echo "    BEFORE: git status --porcelain:"; ( cd "$G" && git status --porcelain ) | sed 's/^/      /'
# 1. suppress the working-tree comparison for the harness
( cd "$G" && git update-index "--$MODE" -- "$CONF" ) || exit 3
# 2. overwrite the harness on disk with the ROW forgery -- the guard is NOT stripped
forge "$G" "$D/forged.txt" ROW
cp "$D/forged.txt" "$G/$CONF"
echo "    committed HEAD:harness = $( cd "$G" && git rev-parse "HEAD:$CONF" )"
echo "    on disk (--no-filters)  = $( git hash-object --no-filters -- "$G/$CONF" )"
echo "    AFTER : git status --porcelain:"; ( cd "$G" && git status --porcelain ) | sed 's/^/      /'
echo "    AFTER : git diff-index --name-only HEAD:"; ( cd "$G" && git diff-index --name-only HEAD -- ) | sed 's/^/      /'
runbar "$G" "$D/bar.log"
echo "    --- the guard's own two object ids, as printed:"
LC_ALL=C grep -m2 'this harness .*committed .* on disk' "$D/bar.log" | sed 's/^/    /'
LC_ALL=C grep -m1 'HARNESS-TEXT CENSUS' -A2 "$D/bar.log" | sed 's/^/    /'
