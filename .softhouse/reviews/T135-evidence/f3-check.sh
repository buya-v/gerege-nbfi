#!/bin/sh
set -u
for side in main branch; do
  B=/tmp/t135/f5/$side/.softhouse/capture/pathb
  echo "=== $side, against the REAL committed evidence"
  out=$(sh "$B/t80/forbidden-sentence.sh" 2>&1); st=$?
  echo "  EXIT=$st"
  printf '%s\n' "$out" | grep -E '^files|^violations|^RESULT|OK=|ERROR' | sed 's/^/  /'
  echo "  OK lines=$(printf '%s\n' "$out" | grep -c '^OK ')  absent lines=$(printf '%s\n' "$out" | grep -c '^absent ')  VIOLATION lines=$(printf '%s\n' "$out" | grep -c '^VIOLATION ')"
done

echo
echo "=== ZERO FILES (an empty out/), both sides"
for side in main branch; do
  rm -rf /tmp/t135/f3/$side
  mkdir -p /tmp/t135/f3/$side/t80/out
  cp /tmp/t135/f5/$side/.softhouse/capture/pathb/t80/forbidden-sentence.sh /tmp/t135/f3/$side/t80/
  out=$(sh /tmp/t135/f3/$side/t80/forbidden-sentence.sh 2>&1); st=$?
  echo "  $side: files visible to the globs: $(ls /tmp/t135/f3/$side/t80/out | wc -l | tr -d ' ')   EXIT=$st"
  printf '%s\n' "$out" | sed 's/^/      /'
done

echo
echo "=== DECOY FILES present, none carrying the guarded sentence"
for side in main branch; do
  printf 'nothing to see here\n' > /tmp/t135/f3/$side/t80/out/attack-decoy1.txt
  printf 'nor here\n' > /tmp/t135/f3/$side/t80/out/attack-decoy2.txt
  out=$(sh /tmp/t135/f3/$side/t80/forbidden-sentence.sh 2>&1); st=$?
  echo "  $side: EXIT=$st"
  printf '%s\n' "$out" | grep -E 'RESULT|ERROR|^files|^violations' | sed 's/^/      /'
done

echo
echo "=== A PLANTED VIOLATION (the canary PASS with NO digest pin, on tenant default)"
for side in main branch; do
  printf "  PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)\n== preconditions, tenant 'default' ==\n" \
    > /tmp/t135/f3/$side/t80/out/attack-planted.txt
  out=$(sh /tmp/t135/f3/$side/t80/forbidden-sentence.sh 2>&1); st=$?
  echo "  $side: EXIT=$st  violations=$(printf '%s\n' "$out" | sed -n 's/^violations: //p')"
done
