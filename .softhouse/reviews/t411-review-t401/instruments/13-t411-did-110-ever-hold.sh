#!/usr/bin/env bash
# T411: T385's prose says 110 tracked .zsh / 98 under capture+reviews.
# T401 reports these as "rotted" (110 -> 121). Rot means the figure was TRUE
# when written and drifted. This walks EVERY commit on main and asks whether
# .zsh ever equalled 110 -- and if so, when, relative to T385's own commits.
# A figure that was never true is not rot; it is a bad measurement, and the
# remedies are different.
set -uo pipefail
GREP=/usr/bin/grep
echo "scanning every commit on main for .zsh == 110 and capture+reviews == 98"
echo
hit110=0; hit98=0; n=0
while read -r sha; do
  n=$((n+1))
  T="$(git ls-tree -r --name-only "$sha" 2>/dev/null)" || continue
  z=$(printf '%s\n' "$T" | $GREP -cE '\.zsh$')
  cr=$(printf '%s\n' "$T" | $GREP -cE '^\.softhouse/(capture|reviews)/.*\.zsh$')
  if [ "$z" = "110" ]; then hit110=$((hit110+1)); echo "  .zsh==110 at $(git rev-parse --short "$sha")  $(git log -1 --format=%s "$sha" | cut -c1-60)"; fi
  if [ "$cr" = "98" ]; then hit98=$((hit98+1)); echo "  c+r ==98  at $(git rev-parse --short "$sha")  $(git log -1 --format=%s "$sha" | cut -c1-60)"; fi
done < <(git rev-list main)
echo
echo "commits scanned            : $n"
echo "commits where .zsh == 110  : $hit110"
echo "commits where c+r  ==  98  : $hit98"
