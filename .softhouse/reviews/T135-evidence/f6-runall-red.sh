#!/bin/sh
# T135 — F-6 item 3, done properly: LIVE=1 so all four proofs close, and the ONLY thing wrong is
# the provenance verification.  The pre-fix runner must then say the good word anyway.
set -u
C=/tmp/t135/clone
T=$C/.softhouse/capture/pathb/t99
CAP=$C/.softhouse/capture/pathb/t36/out/recapture-gerege/B-01-baseline-raw.json

cp "$CAP" /tmp/t135/f6/cap.save
cp "$T/run-all.sh" /tmp/t135/f6/runall-fixed.sh
git -C "$C" show 38c8b5f:.softhouse/capture/pathb/t99/run-all.sh > /tmp/t135/f6/runall-prefix.sh
printf ' ' >> "$CAP"
echo "tampered one byte into $CAP"
echo

for side in prefix fixed; do
  cp /tmp/t135/f6/runall-$side.sh "$T/run-all.sh"
  echo "=== run-all.sh as of: $side"
  out=$(sh "$T/run-all.sh" 2>&1); st=$?
  echo "  RUNNER EXIT=$st"
  printf '%s\n' "$out" | grep -E '^f[1-4]|wrote out/sweep|^  exit |ALL FOUR PROOFS|NOT CLEAN|AT LEAST ONE' | sed 's/^/    /'
  echo
done

cp /tmp/t135/f6/runall-fixed.sh "$T/run-all.sh"
cp /tmp/t135/f6/cap.save "$CAP"
git -C "$C" checkout -- .softhouse/capture/pathb/t99/out
echo "restored; clone clean? [$(git -C "$C" status --porcelain | wc -l | tr -d ' ') dirty path(s)]"
