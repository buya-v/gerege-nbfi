#!/usr/bin/env bash
# T246 — does ANY committed vector grade a reversal? Sweep the vector store.
# Engines: /usr/bin/grep (absolute path, real BSD grep) + python3 re. NEVER bare grep, NEVER rg (P-75).
set -euo pipefail

echo "engine: $(/usr/bin/grep --version 2>&1 | head -1)"
echo "python3: $(python3 -V 2>&1)"
echo

echo "=== CALIBRATION: known POSITIVE and known NEGATIVE on the vector store ==="
printf 'known-POSITIVE  "dec2_revision" in ledger/ : '
/usr/bin/grep -rlc 'dec2_revision' .softhouse/vectors/ledger/ | wc -l | tr -d ' '
printf 'known-NEGATIVE  "ZZZ-NOSUCH-T246"          : '
{ /usr/bin/grep -rl 'ZZZ-NOSUCH-T246' .softhouse/vectors/ || true; } | wc -l | tr -d ' '
echo

echo "=== reversal tokens across the WHOLE vector store (case-insensitive) ==="
for tok in reversed reversal_id reversalId revers I-5 ErrNoDiscriminatingVector; do
  n=$({ /usr/bin/grep -ril -- "$tok" .softhouse/vectors/ || true; } | wc -l | tr -d ' ')
  printf '  %-28s files: %s\n' "$tok" "$n"
  { /usr/bin/grep -rin -- "$tok" .softhouse/vectors/ || true; } | head -20 | sed 's/^/      /'
done
echo

echo "=== the six live reversal TRANSACTION IDS: does any vector carry one? ==="
for tx in a28f54bfdaf3 a28f54c1db73 a28f573f34c7 a28f57412abb a28f605fcdeb a28f614e0263; do
  n=$({ /usr/bin/grep -rl -- "$tx" .softhouse/vectors/ || true; } | wc -l | tr -d ' ')
  printf '  %-16s vector files: %s\n' "$tx" "$n"
done
echo

echo "=== ... and anywhere under .softhouse/ (wider population, P-66) ==="
for tx in a28f54bfdaf3 a28f54c1db73 a28f573f34c7 a28f57412abb a28f605fcdeb a28f614e0263; do
  printf '  %-16s : ' "$tx"
  { /usr/bin/grep -rl -- "$tx" .softhouse/ || true; } | tr '\n' ' '
  echo
done
echo

echo "=== capabilities-ledger.json: what does it say about I-5 / reversal? ==="
python3 - <<'PY'
import json,sys
d=json.load(open('.softhouse/vectors/capabilities-ledger.json'))
s=json.dumps(d,indent=1)
import re
for m in re.finditer(r'.*(?i:revers|I-5).*', s):
    print("   ", m.group(0).strip())
PY
echo
echo "=== END ==="
