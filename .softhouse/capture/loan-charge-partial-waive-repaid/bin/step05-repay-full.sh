#!/usr/bin/env bash
# step05-repay-full.sh — OH-CHGCAP-BD
#
# Repay the loan IN FULL.  The oracle's own repayment template
# (GET /loans/{id}/transactions/template?command=repayment) supplies the amount;
# we cross-check it against summary.totalOutstanding of the after-waive detail
# and send the same value as a JSON string.  Dated on the pinned business date
# 2026-09-03.
#
# This is the money-crossing lifecycle observation.  Observes:
#   charge.go UpdatePaidAmountBy (full branch) on the fee: amountPaid 100.00 ->
#     123.45, amountOutstanding 23.45 -> 0, paid true.
#   lifecycle.go DetermineTransition from Active with
#     Facts{RepaidInFull:true, AllChargesPaid:true, HasOutstanding:false}
#     -> Transition{ClosedObligationsMet, EventRepaidInFull, Needed:true}
#   lifecycle.go NextStatus(Active, EventRepaidInFull) -> ClosedObligationsMet.
#
# Write: POST /loans/{id}/transactions?command=repayment.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan-charge-partial-waive-repaid

LID=$(cat "$OHS_OUT/.loan-id")
BDATE="03 September 2026"

# read-only: the oracle's own suggested repayment
ohs_get "loan-$LID-template-repayment" "/loans/$LID/transactions/template?command=repayment"

# payoff = the after-waive total outstanding
PAY=$(python3 - "$OHS_OUT/loan-$LID-after-waive-detail-raw.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(d['summary']['totalOutstanding'])
PY
)
echo "payoff amount = $PAY"
printf '%s\n' "$PAY" > "$OHS_OUT/.payoff-amount"

REQ="$OHS_REQ/loan-$LID-repay-$PAY-full.json"
cat > "$REQ" <<EOF
{"transactionDate":"$BDATE","transactionAmount":"$PAY","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF

ohs_post "loan-$LID-repay-$PAY-full" "/loans/$LID/transactions?command=repayment" "$REQ"

bash "$(dirname "$0")/capture-state.sh" "$LID" "final"

echo "--- FINAL state ---"
python3 - "$OHS_OUT" "$LID" <<'PY'
import json, sys
out, lid = sys.argv[1], sys.argv[2]
d = json.load(open(f'{out}/loan-{lid}-final-detail-raw.json'))
s = d['summary']
print('status', d['status']['code'], '/', d['status'].get('value'))
print('closedOnDate', d.get('timeline', {}).get('closedOnDate'))
print('totalOutstanding', s['totalOutstanding'])
print('buckets out: prin', s['principalOutstanding'], 'int', s['interestOutstanding'],
      'fee', s['feeChargesOutstanding'], 'pen', s['penaltyChargesOutstanding'])
for c in (d.get('charges') or []):
    print('  charge', c['id'], c['name'], 'penalty', c['penalty'], 'amt', c['amount'],
          'paid', c['amountPaid'], 'waived', c['amountWaived'], 'out', c['amountOutstanding'],
          'paidFlag', c['paid'], 'waivedFlag', c['waived'])
ps = d.get('repaymentSchedule', {}).get('periods') or []
print('periods complete:', sum(1 for p in ps if p.get('complete')), '/', len(ps),
      '| any obligationsMetOnDate:',
      any(p.get('obligationsMetOnDate') for p in ps))
PY
echo "step05 done."
