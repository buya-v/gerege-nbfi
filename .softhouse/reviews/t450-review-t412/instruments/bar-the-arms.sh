#!/bin/bash
set -u
C=/tmp/t450/clone
OUT=/tmp/t450/stateset
cd "$C" || exit 9
for a in A B C; do
  SHA=$(cat "$OUT/$a-sha.txt")
  S=$(date +%s)
  bash .softhouse/hooks/bar-attest.sh "$SHA" > "$OUT/$a-fullbar.txt" 2>&1
  RC=$?
  E=$(date +%s)
  echo "BAR_ATTEST_RC=$RC WALL=$((E-S))" >> "$OUT/$a-fullbar.txt"
  # the transcript bar-attest keeps on refusal
  if [ -f .git/softhouse-driver-gate/last-refused-bar.log ]; then
    cp .git/softhouse-driver-gate/last-refused-bar.log "$OUT/$a-refused-bar.log"
    rm -f .git/softhouse-driver-gate/last-refused-bar.log
  fi
done
echo DONE > /tmp/t450/bararms-done.txt
