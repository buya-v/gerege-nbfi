#!/usr/bin/env bash
# T440 point 4: confirm T424's self-caught PIPESTATUS defect and its repair, from behaviour.
set -uo pipefail
echo "T440 PIPESTATUS DEFECT / REPAIR"
echo "bash: $BASH_VERSION"
echo

echo "== B1: does x=\${PIPESTATUS[0]} really REPLACE PIPESTATUS? =="
bash -c 'set -uo pipefail
sh -c "exit 7" | sh -c "exit 0"
echo "  immediately after the pipeline: PIPESTATUS=(${PIPESTATUS[*]}) len=${#PIPESTATUS[@]}"
a=${PIPESTATUS[0]}
echo "  after  a=\${PIPESTATUS[0]}:      PIPESTATUS=(${PIPESTATUS[*]}) len=${#PIPESTATUS[@]}  a=$a"'
echo

echo "== B2: the DEFECTIVE shape, under set -u -- what status does it die with? =="
bash -c 'set -uo pipefail
sh -c "exit 7" | sh -c "exit 0"
x=${PIPESTATUS[0]}
y=${PIPESTATUS[1]}
echo "  reached the end; x=$x y=$y"' 2>&1 | sed 's/^/    /'
rc=${PIPESTATUS[0]}
printf '  DEFECTIVE shape exit status -> %s\n' "$rc"
if [ "$rc" = 1 ]; then
  echo "  [OK]   dies with status 1 -- INDISTINGUISHABLE from 'the guard caught a failing arm'."
else
  echo "  [FAIL] expected 1, got $rc"
fi
echo

echo "== B3: the REPAIRED shape (copy the whole array in ONE statement) =="
bash -c 'set -uo pipefail
sh -c "exit 7" | sh -c "exit 0"
p=( "${PIPESTATUS[@]}" )
x=${p[0]:-1}; y=${p[1]:-1}
echo "  x=$x y=$y  (both readable)"'
rc=$?
printf '  REPAIRED shape exit status -> %s\n' "$rc"
[ "$rc" = 0 ] && echo "  [OK]   survives and both members are readable" || echo "  [FAIL] got $rc"
echo

echo "== B4: does set -u actually matter, i.e. is the defect latent without it? =="
bash -c 'set -o pipefail
sh -c "exit 7" | sh -c "exit 0"
x=${PIPESTATUS[0]}
y=${PIPESTATUS[1]}
echo "  WITHOUT set -u: x=$x y=[$y]  <- y is silently EMPTY, not an error"' 2>&1 | sed 's/^/    /'
echo "  -> without set -u the same bug is SILENT: a numeric test on an empty y then returns 2."
