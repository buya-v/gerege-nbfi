#!/usr/bin/env bash
# T175 RED PROBE entry point -- t55-analyse.py:352 (invariant I6).
# Run with bash, never sh:   bash <this file>
# Delegates to drive-red.py, which does the work; see its docstring for the six legs.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# T175-red -> analysis -> leapboundary -> capture -> .softhouse -> repo root  (five levels)
ROOT="$(cd "$HERE/../../../../.." && pwd)"
[ -f "$ROOT/CLAUDE.md" ] || { echo "ROOT=$ROOT is not the repo root"; exit 9; }

echo "T175 RED PROBE -- t55-analyse.py:352, the I6 money-decimal-places swallow"
echo "  original  : $HERE/../t55-analyse.py"
echo "  successor : $HERE/../t55-invariants-v2.py"
echo "  committed corpus (never written to): $HERE/../../out"

# Prove the committed originals are untouched by this probe.
before="$(shasum -a 256 "$HERE/../t55-analyse.py" | awk '{print $1}')"
python3 "$HERE/drive-red.py"
rc=$?
after="$(shasum -a 256 "$HERE/../t55-analyse.py" | awk '{print $1}')"
echo
echo "  t55-analyse.py sha256 before probe : $before"
echo "  t55-analyse.py sha256 after  probe : $after"
if [ "$before" = "$after" ]; then
  echo "  AS PREDICTED      the committed original is BYTE-IDENTICAL after the probe"
else
  echo "  NOT AS PREDICTED  the probe modified the committed original"; rc=1
fi
exit "$rc"
