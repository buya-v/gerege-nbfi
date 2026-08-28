#!/usr/bin/env bash
# T325 instrument 05 — WHAT IS `refs/stash` SCOPED TO?
#
# The answer decides whether the per-worktree survey may VOTE on a stash. If
# `refs/stash` lives in the common git dir, then one stash taken anywhere is
# reported by `for-each-ref` in EVERY linked worktree, and a survey that called it
# damage would flag all forty-odd worktrees of this repo at once for a single
# stash in the main tree — the mass false positive that gets a guard deleted.
#
# Measured, not assumed. Prints the git version, because this is a git behaviour
# and the claim expires if git changes it.
set -uo pipefail
R=$(mktemp -d /private/tmp/t325-stash-scope-XXXXXX) || exit 2
echo "git: $(git --version)"
echo "scratch: $R"
git init -q -b main "$R/repo"
cd "$R/repo" || exit 2
git config user.name t325; git config user.email t325@example.com
printf 'hi\n' > f.txt; git add -A; git commit -q -m init
git worktree add -q "$R/wt1" -b wt1branch
echo
echo "--- a stash is created in the MAIN tree only:"
printf 'dirt\n' > f.txt
git stash -q
echo "  main  \`git status --porcelain\` : [$(git status --porcelain)]   <-- stash EMPTIED it"
echo
echo "--- refs visible from the MAIN tree:"
git for-each-ref --format='    %(refname)'
echo "--- refs visible from LINKED WORKTREE wt1 (which never stashed anything):"
git -C "$R/wt1" for-each-ref --format='    %(refname)'
echo
if git -C "$R/wt1" for-each-ref --format='%(refname)' | grep -q '^refs/stash$'; then
  echo "RESULT: refs/stash IS visible from a worktree that did not create it."
  echo "        => COMMON-DIR SCOPED. A per-worktree survey must NOT vote on it;"
  echo "           stash CREATION is caught by the differential compare (T2) instead,"
  echo "           where it can be attributed to a window."
  exit 0
else
  echo "RESULT: refs/stash is NOT visible from the other worktree => per-worktree scoped."
  echo "        The comment in repo-state-attest.sh's cmd_survey is then STALE and"
  echo "        the stash term could be promoted to a vote there. This probe FAILS"
  echo "        loudly in that case rather than passing silently."
  exit 1
fi
