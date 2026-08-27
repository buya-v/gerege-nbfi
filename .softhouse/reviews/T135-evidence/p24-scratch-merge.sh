#!/bin/sh
# T135 — P-24: an assertion about what happens ON MERGE can only be tested BY MERGING.
set -u
rm -rf /tmp/t135/merge/clone
git clone --no-local --quiet /Users/buv/gerege-nbfi/.claude/worktrees/agent-a76f2ba43853c8af3 /tmp/t135/merge/clone
cd /tmp/t135/merge/clone || exit 9
git checkout -q -b main origin/main
echo "main tip: $(git log --oneline -1)"
git merge --no-edit -q origin/softhouse/T99-pathb-lower-findings 2>&1 | tail -5
echo "merge result: $(git log --oneline -1)"
echo "conflicts: $(git status --porcelain | grep -c '^UU')"
echo
echo "=== what PREFIX_REF resolves to POST-MERGE (lib.sh computes it from main):"
T=/tmp/t135/merge/clone/.softhouse/capture/pathb/t99
echo "  git merge-base main HEAD = $(git merge-base main HEAD)"
echo "  HEAD                     = $(git rev-parse HEAD)"
echo
echo "=== run the ARTEFACT post-merge (P-24's standing step), not just conformance:"
for f in f1 f2 f3 f4; do
  T99_EXPORT_ROOT=/tmp/t135/merge/x-$f sh "$T/prove-$f.sh" > /tmp/t135/merge/$f.txt 2>&1
  echo "  prove-$f.sh -> exit $?"
  tail -2 /tmp/t135/merge/$f.txt | sed 's/^/      /'
done
