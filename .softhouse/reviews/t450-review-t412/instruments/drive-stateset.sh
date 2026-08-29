#!/bin/bash
# T450 -- drive three STATE-set-confined changes through the T412 gate, in a throwaway clone.
set -u
C=/tmp/t450/clone
OUT=/tmp/t450/stateset
rm -rf "$OUT"; mkdir -p "$OUT"
cd "$C" || exit 9
BASE=$(git rev-parse drive)
{ echo "BASE=$BASE"; echo "BASETREE=$(git rev-parse drive^{tree})"; grep FULL .git/softhouse-driver-gate/attest.tsv; } > "$OUT/00-base.txt"

reset_remote() {
  rm -rf /tmp/t450/remote.git
  git init -q --bare /tmp/t450/remote.git
  git checkout -q -B drive "$BASE"
  git clean -qfd
}

arm() {
  local n="$1"
  git push bare HEAD:refs/heads/main >"$OUT/$n-push.txt" 2>&1
  echo "PUSH_RC=$?" >>"$OUT/$n-push.txt"
}

######## ARM A -- MONEY: non-byte-preserved numeric token in a CITED capture record
reset_remote
/usr/bin/python3 /tmp/t450/plantA.py || exit 1
git add .softhouse/capture/out/capture-prod3b-raw.json
git -c user.name=T450 -c user.email=t450@local commit -q -m "T450 ARM A: money float planted in a cited capture record (STATE set)"
git diff --name-status "$BASE" HEAD > "$OUT/A-delta.txt"
git rev-parse HEAD > "$OUT/A-sha.txt"
arm A

######## ARM B -- add a file a pinned DEAD-PATH literal names
reset_remote
mkdir -p .softhouse/capture/t290-second-rig
printf 'T450 review probe: this file makes a pinned dead path resolve.\n' > .softhouse/capture/t290-second-rig/note.txt
git add .softhouse/capture/t290-second-rig/note.txt
git -c user.name=T450 -c user.email=t450@local commit -q -m "T450 ARM B: add a .txt that a pinned dead-path literal names (STATE set)"
git diff --name-status "$BASE" HEAD > "$OUT/B-delta.txt"
git rev-parse HEAD > "$OUT/B-sha.txt"
arm B

######## ARM C -- undocumented capture-namespace collision via a .md
reset_remote
mkdir -p .softhouse/capture/t412-second-directory
printf 'T450 review probe: a second t412- capture directory, no OWNER record.\n' > .softhouse/capture/t412-second-directory/note.md
git add .softhouse/capture/t412-second-directory/note.md
git -c user.name=T450 -c user.email=t450@local commit -q -m "T450 ARM C: colliding capture namespace via a .md (STATE set)"
git diff --name-status "$BASE" HEAD > "$OUT/C-delta.txt"
git rev-parse HEAD > "$OUT/C-sha.txt"
arm C

reset_remote
echo DONE > /tmp/t450/stateset-done.txt
