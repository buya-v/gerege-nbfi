#!/bin/bash
# T131 - reproduce the bash `unbound variable` diagnostic T80 was grepping, and
# hexdump it, to see WHERE the invalid byte lands relative to the match.
D="$(cd "$(dirname "$0")" && pwd)/out"; mkdir -p "$D"
cat > /tmp/t131-unbound.sh <<'INNER'
set -u
echo "pin is $PIN_PG_MAJOR_MINOR…"
INNER
bash /tmp/t131-unbound.sh > "$D/t80-diag.txt" 2>&1
echo "--- stderr text captured ---"
cat "$D/t80-diag.txt"
echo "--- hexdump ---"
od -An -tx1z "$D/t80-diag.txt"
echo "--- BSD grep, ambient C.UTF-8, -ac ---"
/usr/bin/grep -ac 'unbound variable' "$D/t80-diag.txt"; echo "exit=$?"
echo "--- BSD grep, LC_ALL=C, -ac ---"
LC_ALL=C /usr/bin/grep -ac 'unbound variable' "$D/t80-diag.txt"; echo "exit=$?"
