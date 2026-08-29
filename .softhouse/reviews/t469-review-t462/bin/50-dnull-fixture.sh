#!/usr/bin/env bash
# Fixture for the D-NULL probe: a task whose work IS ON MAIN (so landed_evidence
# returns `merged`, a REFUSAL) and which also has refs naming it (so the ref probe has
# something to spend the shared budget on).
set -euo pipefail
F="${1:?fixture dir}"
rm -rf "$F"; mkdir -p "$F"; cd "$F"
S=".$(printf 'softhouse')"
CAP="$S/$(printf 'capture')"
git init -q -b main .
git config user.email t469@example.invalid
git config user.name T469
mkdir -p shared
echo base > shared/notes.txt
git add -A; git commit -q -m "base"
# T930's work IS ON MAIN -- an owned path component on the tracked tree
mkdir -p "$CAP/t930-work/out"
echo landed > "$CAP/t930-work/out/result.txt"
git add -A; git commit -q -m "T930: the work landed on main"
MAIN=$(git rev-parse HEAD)
# ...and six refs that merely NAME T930, so the ref probe has work to do
for n in 1 2 3 4 5 6; do
  git checkout -q -b "softhouse/d${n}-T930-decoy" "$MAIN"
  echo "d${n}" >> shared/notes.txt
  git add -A
  git commit -q -m "RESCUED: WIP from a worker that never signalled done"
  git checkout -q main
done
echo "fixture $F ready ; main=$MAIN"
