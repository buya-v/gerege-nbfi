#!/bin/bash
set -u
C=/tmp/t450/clone2
OUT=/tmp/t450/refusals
cd "$C" || exit 9
BASE=$(git rev-parse origin/drive)
rm -rf /tmp/t450/remote2.git
git init -q --bare /tmp/t450/remote2.git
git checkout -q -B drive "$BASE"
git clean -qfdx -e .git >/dev/null 2>&1
git reset -q --hard "$BASE"
mkdir -p nexus/internal/apps/t450probe
printf 'package t450probe\n' > nexus/internal/apps/t450probe/probe.go
git add nexus/internal/apps/t450probe/probe.go
git -c user.name=T450 -c user.email=t450@local commit -q -m "T450 R5 rerun: outside the allowlist, 2-char bypass reason"
SOFTHOUSE_DRIVER_GATE_BYPASS="ok" git push bare HEAD:refs/heads/main >"$OUT/R5-short-bypass-rerun.txt" 2>&1
echo "PUSH_RC=$?" >>"$OUT/R5-short-bypass-rerun.txt"
git checkout -q -B drive "$BASE"; git clean -qfdx -e .git >/dev/null 2>&1
rm -rf /tmp/t450/remote2.git
