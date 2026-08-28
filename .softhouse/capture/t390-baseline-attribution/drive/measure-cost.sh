#!/usr/bin/env bash
# T390: measure the instrument's wall cost, three consecutive runs, so the GUARD_COST_BUDGETS
# row proposed for conformance.sh is a MEASUREMENT and not a guess. Integer seconds from bash's
# SECONDS, which is the same resolution conformance.sh's own timed_guard uses.
set -uo pipefail
R=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)
I="$R/.softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh"
echo "instrument: $I"
for n in 1 2 3; do
  t0=$SECONDS
  bash "$I" >/dev/null 2>&1
  rc=$?
  echo "  run $n: rc=$rc elapsed=$((SECONDS - t0))s"
done
