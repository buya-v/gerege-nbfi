#!/usr/bin/env bash
# Adds task Z (id T920): fan-out 20, ALL name-only, task branch PRUNED.
# Z is the BUDGET SINK.  Nothing about Z's own verdict is interesting; what matters is
# how much of the PROCESS-GLOBAL --deadline-secs budget Z's probe eats before the next
# task is reconciled in the same process.
set -euo pipefail
F="${1:?fixture dir}"
cd "$F"
MAIN=$(git rev-parse main)
for n in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20; do
  git checkout -q -b "softhouse/s${n}-T920-decoy" "$MAIN"
  echo "s${n}" >> shared/notes.txt
  git add -A
  git commit -q -m "RESCUED: WIP from a worker that never signalled done"
  git checkout -q main
done
echo "added 20 name-only refs for T920"
git for-each-ref --format='%(refname:short)' refs/heads | grep -c T920
