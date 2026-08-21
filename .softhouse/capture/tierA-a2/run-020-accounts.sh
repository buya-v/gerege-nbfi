#!/bin/sh
# Create the GL accounts the rest of slice A2 needs (ids 5..18 on a fresh `gerege`).
# NOT set -e: every exchange is recorded, including any the oracle refuses.
DIR=$(cd "$(dirname "$0")" && pwd)
for n in gl-020-liability-header gl-021-overpayment gl-022-income-header \
         gl-023-interest-income gl-024-fee-income gl-025-penalty-income \
         gl-026-recovery-income gl-027-expense-header gl-028-writeoff-expense \
         gl-029-goodwill-expense gl-030-equity-header gl-031-fund-source-alt \
         gl-032-disabled-asset gl-033-nomanual-asset; do
  sh "$DIR/cap.sh" "A2-${n}" POST /glaccounts "req/$n.json" || exit 1
  printf '   -> %s\n' "$(cat "$DIR/out/A2-${n}.json")"
done
