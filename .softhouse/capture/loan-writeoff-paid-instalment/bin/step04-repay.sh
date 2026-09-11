#!/usr/bin/env bash
# step04-repay.sh — OH-WOPAID-AU
#
# Repay exactly period 1's total due so that instalment reads complete: true,
# while every other instalment stays outstanding.  Period 1 is
# principal 7884.88 + interest 1000.00 = 8884.88 (fee/penalty are in periods 2/3).
#
# The repayment is dated 01 February 2026, period 1's due date: after the
# 2026-01-01 disbursement (so not before the last transaction) and strictly
# before the 2026-09-03 write-off (so the write-off is not forced onto the same
# day as the repayment).  transactionAmount is a JSON STRING, so the body has no
# decimal number token and is byte-stable.
#
# Write: POST /loans/{id}/transactions?command=repayment.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan-writeoff-paid-instalment

LID=$(python3 -c "import json;print(json.load(open('$OHS_OUT/loan-13-before-detail-raw.json'))['id'])")
REQ="$OHS_REQ/loan-$LID-repay-8884.88.json"
cat > "$REQ" <<'EOF'
{"transactionDate":"01 February 2026","transactionAmount":"8884.88","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF

ohs_post "loan-$LID-repay-8884.88" "/loans/$LID/transactions?command=repayment" "$REQ"

# post-repayment, pre-writeoff: THE discriminating state (one complete instalment)
bash "$(dirname "$0")/capture-state.sh" "$LID" "after-repay"

echo "--- after repayment ---"
python3 - "$OHS_OUT/loan-$LID-after-repay-detail-raw.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
s = d['summary']
print('status', d['status']['code'], 'totalOutstanding', s['totalOutstanding'])
print('buckets out: prin', s['principalOutstanding'], 'int', s['interestOutstanding'],
      'fee', s['feeChargesOutstanding'], 'pen', s['penaltyChargesOutstanding'])
for p in d['repaymentSchedule']['periods']:
    if p.get('period') in (1, 2, 3):
        print('period', p['period'], p['dueDate'], 'complete=', p.get('complete'),
              'prinOut=', p.get('principalOutstanding'), 'intOut=', p.get('interestOutstanding'))
PY
