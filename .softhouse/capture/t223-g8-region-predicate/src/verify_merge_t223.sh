#!/bin/bash
# T223 — STANDING RULE item 6: VERIFY THE MERGE BY MERGING (P-24), in a THROWAWAY clone against
# CURRENT main. Checks: exactly one `## G-8` heading, no conflict on .softhouse/tasks.json, and
# gates.md resolving to this branch's blob.
set -uo pipefail
WT=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a01b5f9f0ceec59f4
TMP=$(mktemp -d /tmp/t223-mergecheck.XXXXXX)
BR=softhouse/T223-g8-region-predicate

git clone -q --no-hardlinks "$WT" "$TMP/clone" 2>/dev/null || git clone -q "$WT" "$TMP/clone"
cd "$TMP/clone"
git remote add up /Users/buv/gerege-nbfi 2>/dev/null || true
git fetch -q up main
git fetch -q origin "$BR"
git checkout -q -B mainref up/main
echo "main at:   $(git rev-parse --short HEAD)"
echo "branch at: $(git rev-parse --short origin/$BR)"
git merge --no-edit -q "origin/$BR" > "$TMP/merge.log" 2>&1
RC=$?
echo "merge exit: $RC"
if [ "$RC" -ne 0 ]; then
  echo "--- conflicts ---"
  git diff --name-only --diff-filter=U
  cat "$TMP/merge.log"
fi
echo "G-8 headings in merged gates.md: $(grep -c '^## G-8' .softhouse/gates.md)"
grep -n '^## G-8' .softhouse/gates.md
echo "tasks.json conflicted: $(git diff --name-only --diff-filter=U | grep -c 'tasks.json')"
echo "merged gates.md blob:  $(git rev-parse HEAD:.softhouse/gates.md)"
echo "branch  gates.md blob:  $(git rev-parse origin/$BR:.softhouse/gates.md)"
echo "merged vectors digest: $(git rev-parse HEAD:.softhouse/vectors)"
echo "main   vectors digest: $(git rev-parse up/main:.softhouse/vectors)"
echo "throwaway clone: $TMP/clone"
