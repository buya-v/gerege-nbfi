#!/bin/bash
# T428: re-run T421's sweep on the T421 tree AND on main, and cross-check with an
# independent raw grep that never opens a JSON parser at all.
set -u
tree="$1"; out="$2"
cd "$tree" || exit 9
{
  echo "T428 TIMESTAMP SWEEP -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "tree: $tree   HEAD: $(git rev-parse HEAD)"
  echo
  echo "=== 1. T421's own sweep, re-run by T428 ==="
} > "$out"
python3 .softhouse/capture/t421-t406-conditions/bin/timestamp-sweep.py >> "$out" 2>&1
{
  echo
  echo "=== 2. INDEPENDENT CROSS-CHECK: raw grep, no JSON parser, no float ==="
  echo "every ...T..:..:..Z token anywhere under .softhouse/vectors, deduplicated:"
} >> "$out"
LC_ALL=C grep -rhoE '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z' .softhouse/vectors \
  | LC_ALL=C sort -u > /tmp/t428-instants.txt
LC_ALL=C sed 's/^/   /' /tmp/t428-instants.txt >> "$out"
{
  echo -n "   DISTINCT INSTANTS: "; LC_ALL=C grep -c '' /tmp/t428-instants.txt
  echo -n "   ROUND HOURS among them (mm:ss == 00:00): "
  LC_ALL=C grep -cE 'T[0-9]{2}:00:00Z' /tmp/t428-instants.txt || true
  echo "   (listed:)"
  LC_ALL=C grep -E 'T[0-9]{2}:00:00Z' /tmp/t428-instants.txt | LC_ALL=C sed 's/^/      /' || true
  echo -n "   NOW: "; date -u +%Y-%m-%dT%H:%M:%SZ
  echo "   FUTURE among them (string compare against NOW):"
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  LC_ALL=C awk -v now="$now" '$0 > now {print "      FUTURE " $0}' /tmp/t428-instants.txt
  echo "   (no line above means none)"
  echo
  echo "=== 3. FILE COUNT under .softhouse/vectors ==="
  echo -n "   .json files: "; LC_ALL=C find .softhouse/vectors -name '*.json' | LC_ALL=C grep -c ''
} >> "$out"
tail -25 "$out"
