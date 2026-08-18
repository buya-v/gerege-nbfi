#!/bin/sh
# T36 — prove t36_diff.py is FAILABLE.  A comparator that cannot fail proves nothing
# (T22 found exactly that defect in t22-probe/invariants.py, whose I5 was hard-coded PASS).
# Mutate ONE minor unit in a copy of a re-capture and require a non-zero exit.
set -u
D=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$D/.." && pwd)
TMP=$D/out/mutation
mkdir -p "$TMP"

# 112082.40 -> 112082.41 : one minor unit on B-01's final installment.
sed 's/112082\.40/112082.41/' "$D/out/recapture-gerege/B-01-baseline-raw.json" > "$TMP/B-01-mutated.json"
if cmp -s "$D/out/recapture-gerege/B-01-baseline-raw.json" "$TMP/B-01-mutated.json"; then
  echo "MUTATION DID NOT APPLY — test is meaningless" >&2; exit 2
fi

python3 "$D/t36_diff.py" "$W/out/B-01-baseline-raw.json" "$TMP/B-01-mutated.json" "B-01 MUTATED (one minor unit)"
rc=$?
echo
if [ $rc -ne 0 ]; then
  echo "MUTATION TEST PASSED: the comparator exits non-zero on a one-minor-unit change."
  exit 0
fi
echo "MUTATION TEST FAILED: the comparator accepted a mutated capture. Its clean verdicts mean nothing." >&2
exit 1
