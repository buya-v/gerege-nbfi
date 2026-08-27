#!/bin/bash
# T238 -- condense the GREEN run body. The full body is 4.9 MB; the instrument is now
# RE-RUNNABLE (that is the whole point of the repair), so the body is reproducible on demand
# and only its sha256, its head/tail and its FULL per-pattern counts are committed.
set -eu
D="$(git rev-parse --show-toplevel)/.softhouse/capture/t238-failopen/evidence/red-drive"
cd "$D"
F=90-green-live.txt
[ -f "$F" ] || { echo "ABORT: $F absent -- nothing to trim (re-run 40-red-drive.sh first)"; exit 91; }
{
  echo "T238 GREEN RUN -- HEAD/TAIL EXCERPT + INTEGRITY DIGEST"
  echo
  echo "The full body was 4.9 MB and is deliberately NOT committed. The repaired instrument is"
  echo "RE-RUNNABLE -- which is the entire point of the repair -- so the body regenerates with:"
  echo "    bash .softhouse/reviews/a2-33-dec2-rev5/sweep.sh REPO"
  echo "FULL per-pattern hit counts for all 34 patterns ARE committed, in"
  echo "    90-green-per-pattern-counts.txt"
  echo
  echo "=== sha256 of the full body as produced at this commit ==="
  shasum -a 256 "$F"
  echo
  echo "=== FIRST 40 LINES ==="
  head -40 "$F"
  echo
  echo "=== LAST 6 LINES ==="
  tail -6 "$F"
} > 90-green-live-EXCERPT.txt
rm -f "$F"
echo "trimmed -> 90-green-live-EXCERPT.txt"
ls -la
