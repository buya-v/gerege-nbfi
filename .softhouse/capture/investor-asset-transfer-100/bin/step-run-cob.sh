#!/usr/bin/env bash
# OH-INV-Y step 4: re-run LOAN_CLOSE_OF_BUSINESS (job 34) and capture the per-loan outcome.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf 'COB window start (UTC): %s\n' "$TS" | tee "$OUT/cob-window-ohinvy.txt"

cap_get job34-status-pre "/jobs/34"

code=$(curl -sk -D "$OUT/cob-execute-ohinvy.headers" \
    -o "$OUT/cob-execute-ohinvy.json" -w '%{http_code}' -X POST \
    "$BASE/jobs/34?command=executeJob" -H "$AUTH" -H "$TEN")
printf '%s\n' "$code" > "$OUT/cob-execute-ohinvy.status"
printf 'POST %-52s -> %s\n' '/jobs/34?command=executeJob' "$code"

# job is async; allow the batch to drain before reading status/logs
sleep 25
cap_get job34-status-post "/jobs/34"

docker logs --since "$TS" gerege-oracle-app > "$OUT/cob-run-ohinvy.log" 2>&1
printf 'log lines captured: %s\n' "$(wc -l < "$OUT/cob-run-ohinvy.log" | tr -d ' ')"

grep -n -E "Loan \(id=12\)|ASSET_TRANSFER|Financial Activity|FinancialActivityAccount|InvestorAccounting|LoanAccountOwnerTransfer|createJournalEntries|Skipping was triggered|Error was triggered|BUILD|COMPLETED|FAILED" \
    "$OUT/cob-run-ohinvy.log" > "$OUT/cob-run-ohinvy-signals.txt" 2>&1 || true
printf -- '--- signals ---\n'
cat "$OUT/cob-run-ohinvy-signals.txt"
