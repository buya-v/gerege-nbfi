#!/usr/bin/env bash
# Master rig runner. Steps are numbered per the task, but executed in dependency
# order: provisioning criteria (step03) must reference the loan product (step05),
# so the loan product is created before the criteria. Every step is idempotent:
# check-then-create keyed on the SEED- external id / name / glCode.
set -uo pipefail

BIN="$(cd "$(dirname "$0")" && pwd)"

"$BIN/step01-businessdate.sh"
"$BIN/step02-glaccounts.sh"
"$BIN/step05-loanproduct.sh"
"$BIN/step03-provisioningcriteria.sh"
"$BIN/step04-clients.sh"
"$BIN/step06-loans.sh"
"$BIN/step07-loss-loan.sh"
"$BIN/step08-rounding-loan.sh"

echo "=== run.sh complete ==="
cat "$BIN/../out/state.json"
