#!/usr/bin/env bash
# T411: 110/98 DID hold, at 49 commits. This finds the LAST commit at which it
# held, and asks whether that commit is an ancestor of T385's first commit --
# i.e. whether the figure was already stale at the moment T385 wrote it down.
set -uo pipefail
GREP=/usr/bin/grep
T385_FIRST=3ce7787f
echo "walking main first-parent, oldest->newest, printing every .zsh transition"
prev=""
git rev-list --reverse --first-parent main | while read -r sha; do
  z=$(git ls-tree -r --name-only "$sha" 2>/dev/null | $GREP -cE '\.zsh$')
  if [ "$z" != "$prev" ]; then
    anc="AFTER-or-AT T385"
    git merge-base --is-ancestor "$sha" "$T385_FIRST" 2>/dev/null && anc="ancestor of T385's first commit"
    printf '  .zsh %4s  first seen at %s  [%s]  %s\n' "$z" "$(git rev-parse --short "$sha")" "$anc" "$(git log -1 --format=%s "$sha" | cut -c1-52)"
    prev="$z"
  fi
done
