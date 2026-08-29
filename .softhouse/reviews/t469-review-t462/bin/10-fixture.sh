#!/usr/bin/env bash
# T469 fixture -- built independently of T462's bin/10-fixture.sh.
# NO REAL DOT-SOFTHOUSE PATH IS SPELLED AS A LITERAL: every one is assembled from $S.
set -euo pipefail
F="${1:?fixture dir}"
rm -rf "$F"; mkdir -p "$F"; cd "$F"
S=".$(printf 'softhouse')"          # assembled, never a literal
CAP="$S/$(printf 'capture')"
git init -q -b main .
git config user.email t469@example.invalid
git config user.name T469
mkdir -p shared
echo base > shared/notes.txt
git add -A; git commit -q -m "base: shared module only, names no task id"
MAIN=$(git rev-parse HEAD)

# a DECOY ref: one commit ahead of main, subject names no id, diff touches only a
# SHARED path -> name-only.  $1 = ref name
decoy () {
  git checkout -q -b "$1" "$MAIN"
  echo "$1" >> shared/notes.txt
  git add -A
  git commit -q -m "RESCUED: WIP from a worker that never signalled done"
  git checkout -q main
}
# a CARRIER ref: diff owns a path component starting with the id.  $1 = ref, $2 = id
carrier () {
  low=$(printf '%s' "$2" | tr 'A-Z' 'a-z')
  git checkout -q -b "$1" "$MAIN"
  mkdir -p "$CAP/${low}-work/out"
  echo wip > "$CAP/${low}-work/out/wip.txt"
  git add -A
  git commit -q -m "RESCUED: WIP from a worker that never signalled done"
  git checkout -q main
}

# ---- F2  fan-out 2, carrier SECOND in sort, task branch PRUNED (id T900)
decoy   softhouse/aaa-T900-decoy
carrier softhouse/zzz-T900-rescue T900

# ---- F2S fan-out 2, carrier SECOND, task branch STANDING at the dispatch commit (T901)
decoy   softhouse/aaa-T901-decoy
carrier softhouse/zzz-T901-rescue T901
git branch softhouse/T901-work "$MAIN"

# ---- F8  fan-out 8, carrier EIGHTH (index 7) -- the FLOOR BOUNDARY (T908)
for n in 1 2 3 4 5 6 7; do decoy "softhouse/d${n}-T908-decoy"; done
carrier softhouse/z8-T908-rescue T908

# ---- F9  fan-out 9, carrier NINTH (index 8) -- OUTSIDE the floor (T909)
for n in 1 2 3 4 5 6 7 8; do decoy "softhouse/d${n}-T909-decoy"; done
carrier softhouse/z9-T909-rescue T909

# ---- F1  fan-out 1, carrier first -- MUST-REFUSE control (T910)
carrier softhouse/only-T910-rescue T910

# ---- N   fan-out 2, no carrier -- MUST-DEMOTE control (T911)
decoy softhouse/aaa-T911-decoy
decoy softhouse/zzz-T911-decoy

echo "fixture at $F ; main=$MAIN"
git for-each-ref --format='%(refname:short)' refs/heads | sort
