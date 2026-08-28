#!/bin/bash
# T387: drive each admissibility attack against the T360 branch, one at a time.
set -u
OUT=/tmp/t387/attacks
mkdir -p "$OUT"
for a in A1-expect-legs-10013 A2-totals-minor A3-expect-refusal A4-expect-http-status \
         A6-one-digit-mutated A7-representable A8-short-marker; do
  python3 /tmp/t387/attack.py "$a" >/dev/null
  ( cd /tmp/t387/t360 && /tmp/t387/conf-t360 -context ledger -oracle-probe up ) \
      > "$OUT/$a.log" 2>&1
  rc=$?
  echo "=== $a  exit=$rc"
  grep -aE "LDG-DIV-01|ledger inadmissible|ledger parity |divergence vectors" "$OUT/$a.log" | head -4
  grep -aA30 "LDG-DIV-01-oracle-accepts-sub-minor-unit-re... divergence" "$OUT/$a.log" \
      | sed -n '2,12p' | sed 's/^/    /'
  echo "exit=$rc" >> "$OUT/$a.log"
  python3 /tmp/t387/attack.py restore >/dev/null
done
