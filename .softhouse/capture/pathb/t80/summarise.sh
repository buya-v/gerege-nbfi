#!/bin/sh
# T80 — one line per attack transcript: PASS count, FAIL count, exit code.  Derived from the
# committed transcripts, so the handoff table cannot drift from the evidence it cites.
set -u
T80=$(cd "$(dirname "$0")" && pwd)
O=$T80/out
printf '%-52s %5s %5s %5s\n' transcript PASS FAIL EXIT
for f in "$O"/attack-*.txt; do
  b=$(basename "$f")
  case "$b" in attack-4-shell-invariance.txt|attack-5-happy-path.txt) ;; esac
  p=$(grep -c '^  PASS' "$f" || true)
  q=$(grep -c '^  FAIL' "$f" || true)
  e=$(grep -m1 '^EXIT=' "$f" | sed 's/EXIT=//')
  [ -n "$e" ] || e='-'
  printf '%-52s %5s %5s %5s\n' "$b" "$p" "$q" "$e"
done
