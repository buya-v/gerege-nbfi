#!/bin/bash
# T444 — collect the decisive lines out of each arm transcript.
set -u
D="$1"
[ -n "$D" ] || { echo "usage: collect.sh <arm-output-dir>"; exit 9; }
for f in "$D"/*.out; do
  n="$(basename "$f" .out)"
  echo "############ $n"
  echo "-- P-84: PRESENCE of the probe line first --"
  echo "   grep -c 'probe = ' = $(LC_ALL=C grep -c 'probe = ' "$f")"
  LC_ALL=C grep -hE 'GUARDS-DIR-REGISTRATION: population' "$f"
  LC_ALL=C grep -hE '^VERDICT' "$f"
  LC_ALL=C grep -hE 'probe = ' "$f"
  LC_ALL=C grep -hE 'REACHED-BY .*zz-t444' "$f"
  LC_ALL=C grep -hE 'THAT WITNESS IS A SYMLINK|MORE THAN ONE TRACKED PATH|DID NOT ROUND-TRIP|matched NO INDEX ENTRY|DOES NOT NAME|which is NOT TRACKED|IS INVOKED BY NOTHING|RESOLVES TO NO INDEX ENTRY|RESOLVES TO MORE THAN ONE INDEX|IS A SYMLINK, and a symlink|unreadable corpus member' "$f" | head -4
  echo
done
