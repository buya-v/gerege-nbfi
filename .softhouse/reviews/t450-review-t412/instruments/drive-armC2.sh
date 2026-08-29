#!/bin/bash
# T450 ARM C (rerun) -- a REAL undocumented capture-namespace collision, created with a single
# ADDED *.md under .softhouse/ (inside the STATE set). t305- already prefixes exactly one
# capture directory; a second one with no OWNER*.md is an undocumented collision.
set -u
C=/tmp/t450/clone
OUT=/tmp/t450/stateset
cd "$C" || exit 9
BASE=$(git rev-parse origin/drive 2>/dev/null || git rev-parse drive)
rm -rf /tmp/t450/remote.git
git init -q --bare /tmp/t450/remote.git
git remote remove bare 2>/dev/null
git remote add bare /tmp/t450/remote.git
git checkout -q -B drive "$BASE"
git clean -qfdx -e .git >/dev/null 2>&1
git reset -q --hard "$BASE"
mkdir -p .softhouse/capture/t305-second-directory
printf 'T450 review probe: a SECOND t305- capture directory, with no OWNER record.\n' \
  > .softhouse/capture/t305-second-directory/note.md
git add .softhouse/capture/t305-second-directory/note.md
git -c user.name=T450 -c user.email=t450@local commit -q -m "T450 ARM C2: undocumented capture-namespace collision via one added .md (STATE set)"
git diff --name-status "$BASE" HEAD > "$OUT/C2-delta.txt"
git rev-parse HEAD > "$OUT/C2-sha.txt"
git push bare HEAD:refs/heads/main > "$OUT/C2-push.txt" 2>&1
echo "PUSH_RC=$?" >> "$OUT/C2-push.txt"
S=$(date +%s)
bash .softhouse/hooks/bar-attest.sh "$(cat "$OUT/C2-sha.txt")" > "$OUT/C2-fullbar.txt" 2>&1
echo "BAR_ATTEST_RC=$? WALL=$(( $(date +%s) - S ))" >> "$OUT/C2-fullbar.txt"
[ -f .git/softhouse-driver-gate/last-refused-bar.log ] && cp .git/softhouse-driver-gate/last-refused-bar.log "$OUT/C2-refused-bar.log"
rm -f .git/softhouse-driver-gate/last-refused-bar.log
git checkout -q -B drive "$BASE"; git clean -qfdx -e .git >/dev/null 2>&1
rm -rf /tmp/t450/remote.git
echo DONE > /tmp/t450/armC2-done.txt
