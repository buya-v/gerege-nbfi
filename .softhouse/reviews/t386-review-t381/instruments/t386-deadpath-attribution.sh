#!/usr/bin/env bash
# T386 -- WHOSE CHANGE MOVED THE DEAD-PATH NUMBER? Established by RUNNING, never by arithmetic.
#
#   bash .../t386-deadpath-attribution.sh <main-worktree> <branch-worktree> <merge-worktree>
#
# The T381 branch reports deadOccurrences=109 and the merge result reports 108. Subtracting one
# from the other and calling the difference "T381's" would be P-83 exactly. So the guard is run
# on THREE trees and each prints its own cardinal: plain `main`, the branch alone, and the merge.
# The attribution then falls out of the three measurements instead of out of a subtraction.
set -uo pipefail
for w in "$@"; do
  [ -d "$w" ] || { echo "no such worktree: $w" >&2; exit 2; }
  echo "=============================================================================="
  echo "TREE : $w"
  ( cd "$w" && echo "HEAD : $(git rev-parse --short HEAD)  $(git log -1 --format=%s | cut -c1-70)" )
  ( cd "$w" && echo "CLEAN: $(git status --porcelain | grep -c .) modified/untracked path(s)" )
  ( cd "$w" && bash .softhouse/guards/check-dead-path-frontier.sh 2>&1 | grep -E 'DEADPATH-CENSUS|frontier|FRONTIER' )
  echo
done
