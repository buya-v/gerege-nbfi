#!/bin/bash
set -u
OUT=/tmp/t387/attacks
mkdir -p "$OUT"
for a in A5-oracle-accepted-on-parity A10-divergence-relabelled-parity \
         A11-port-refusal-kind-on-parity-class A12-divergence-with-journal-entry-kind \
         A13-marker-not-in-observed-text A14-gate-empty; do
  python3 /tmp/t387/attack2.py "$a" >/dev/null
  ( cd /tmp/t387/t360 && /tmp/t387/conf-t360 -context ledger -oracle-probe up ) \
      > "$OUT/$a.log" 2>&1
  rc=$?
  echo "=== $a  exit=$rc"
  echo "exit=$rc" >> "$OUT/$a.log"
  grep -aE "INADMISSIBLE|LEDGER FATAL|ledger inadmissible|ledger parity |divergence vectors " "$OUT/$a.log" | head -6
  python3 /tmp/t387/attack2.py restore >/dev/null
done
