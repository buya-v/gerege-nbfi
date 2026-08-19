#!/bin/sh
# T40 — capture the charge-bearing schedules from the live reference oracle (Fineract).
# RAW OBSERVED FORM ONLY.  Nothing here is a parity vector; nothing is contract-shaped.
set -eu
. /Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513/.softhouse/capture/charges/bin/lib.sh

O=${1:-$CH/out/fc}
mkdir -p "$O"

sh "$CH/bin/run-preconditions.sh" "$O/preconditions.txt" > /dev/null || {
  echo "ABORT: preconditions breached — nothing captured." >&2; exit 1; }
echo "preconditions: ALL PASS"
echo

for f in "$CH"/req/calc-FC-*.json; do
  n=$(basename "$f" .json); n=${n#calc-}
  post "$f" "$O/$n-raw.json" || exit 1
done

echo
shasum -a 256 "$O"/FC-*-raw.json
