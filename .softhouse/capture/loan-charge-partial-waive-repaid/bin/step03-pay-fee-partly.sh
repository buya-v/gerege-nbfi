#!/usr/bin/env bash
# step03-pay-fee-partly.sh — OH-CHGCAP-BD
#
# Partly pay the FEE.  A repayment of 100.00 (smaller than the fee's 123.45 and
# than the period-1 total due) dated 15 January 2026 — the fee's own due date,
# inside period 1 and after the 2026-01-01 disbursement.  The product allocates
# penalty -> fee -> interest -> principal within period 1; period 1 carries no
# penalty, so the whole 100.00 lands on the fee and leaves it partly paid.
#
# Observes charge.go UpdatePaidAmountBy (partial branch): amountPaid 0 -> 100.00,
# amountOutstanding 123.45 -> 23.45, paid stays false, waived stays false.
#
# Write: POST /loans/{id}/transactions?command=repayment.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan-charge-partial-waive-repaid

LID=$(cat "$OHS_OUT/.loan-id")
REQ="$OHS_REQ/loan-$LID-repay-100.00-partial.json"
cat > "$REQ" <<'EOF'
{"transactionDate":"15 January 2026","transactionAmount":"100.00","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF

ohs_post "loan-$LID-repay-100.00-partial" "/loans/$LID/transactions?command=repayment" "$REQ"

bash "$(dirname "$0")/capture-state.sh" "$LID" "after-partial"

echo "--- after the partial fee payment ---"
python3 - "$OHS_OUT/loan-$LID-after-partial-detail-raw.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
s = d['summary']
print('status', d['status']['code'], 'totalOutstanding', s['totalOutstanding'])
print('buckets out: prin', s['principalOutstanding'], 'int', s['interestOutstanding'],
      'fee', s['feeChargesOutstanding'], 'pen', s['penaltyChargesOutstanding'])
for c in (d.get('charges') or []):
    print('  charge', c['id'], c['name'], 'penalty', c['penalty'], 'amt', c['amount'],
          'paid', c['amountPaid'], 'waived', c['amountWaived'], 'out', c['amountOutstanding'],
          'paidFlag', c['paid'], 'waivedFlag', c['waived'])
PY
echo "step03 done."
