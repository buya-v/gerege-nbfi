#!/usr/bin/env bash
# step02-create.sh — OH-CHGCAP-BD
#
# Create ONE agent-bearing loan on product 3 (OHLGR-Accrual-Loan, ACCTUAL PERIODIC),
# principal 100000, 12 monthly periods at 12%/yr, disbursed 2026-01-01 (the same
# shape the loan-writeoff-paid-instalment reference used).  Two specified-due-date
# charges ride on it, reusing the existing definitions read in step01:
#
#   chargeId 5  fee      amount "123.45"  due 15 January 2026  -> falls in period 1
#   chargeId 4  penalty  amount "67.89"   due 15 February 2026 -> falls in period 2
#
# WHY the penalty is in period 2 and not also in period 1: the product's
# allocation order is penalty -> fee -> interest -> principal *within each
# instalment* (observed, see OWNER).  A partial repayment that lands on the fee
# would have to skip a period-1 penalty, which is impossible; a period-1 penalty
# is consumed first and can then no longer be waived.  Placing the penalty in the
# next period keeps it pending and waivable while the fee is partly paid.
#
# Every numeric JSON token is an integer or a JSON string. No float is ever
# serialised, so every body survives a binary-double round trip byte-for-byte.
#
# Writes: POST /clients, POST /loans, /loans/{id}?command=approve, ?command=disburse.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan-charge-partial-waive-repaid

DATE="01 January 2026"
CLIENT_EXT="OHCHGCAP-C01"
LOAN_EXT="OHCHGCAP-L01"

# ---- client ---------------------------------------------------------------
cat > "$OHS_REQ/client-$CLIENT_EXT-create.json" <<EOF
{"officeId":1,"firstname":"OHCHGCAP","lastname":"Borrower","externalId":"$CLIENT_EXT","legalFormId":1,"active":true,"activationDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
ohs_post "client-$CLIENT_EXT-create" "/clients" "$OHS_REQ/client-$CLIENT_EXT-create.json"
CID=$(ohs_id "$OHS_OUT/client-$CLIENT_EXT-create-raw.json")
[ -z "$CID" ] && { echo "CLIENT CREATE FAILED"; cat "$OHS_OUT/client-$CLIENT_EXT-create-raw.json"; exit 3; }
echo "clientId=$CID"
printf '%s\n' "$CID" > "$OHS_OUT/.client-id"

# ---- loan submit ----------------------------------------------------------
cat > "$OHS_REQ/loan-$LOAN_EXT-submit.json" <<EOF
{
  "clientId": $CID,
  "productId": 3,
  "externalId": "$LOAN_EXT",
  "principal": "100000",
  "loanTermFrequency": 12,
  "loanTermFrequencyType": 2,
  "numberOfRepayments": 12,
  "repaymentEvery": 1,
  "repaymentFrequencyType": 2,
  "interestRatePerPeriod": 12,
  "interestRateFrequencyType": 3,
  "amortizationType": 1,
  "interestType": 0,
  "interestCalculationPeriodType": 1,
  "transactionProcessingStrategyCode": "mifos-standard-strategy",
  "loanType": "individual",
  "submittedOnDate": "$DATE",
  "expectedDisbursementDate": "$DATE",
  "charges": [
    {"chargeId": 5, "amount": "123.45", "dueDate": "15 January 2026"},
    {"chargeId": 4, "amount": "67.89", "dueDate": "15 February 2026"}
  ],
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
ohs_post "loan-$LOAN_EXT-submit" "/loans" "$OHS_REQ/loan-$LOAN_EXT-submit.json"
LID=$(ohs_id "$OHS_OUT/loan-$LOAN_EXT-submit-raw.json")
[ -z "$LID" ] && { echo "LOAN SUBMIT FAILED"; cat "$OHS_OUT/loan-$LOAN_EXT-submit-raw.json"; exit 3; }
echo "loanId=$LID"
printf '%s\n' "$LID" > "$OHS_OUT/.loan-id"

# ---- approve + disburse ---------------------------------------------------
cat > "$OHS_REQ/loan-$LOAN_EXT-approve.json" <<EOF
{"approvedOnDate":"$DATE","expectedDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
ohs_post "loan-$LOAN_EXT-approve" "/loans/$LID?command=approve" "$OHS_REQ/loan-$LOAN_EXT-approve.json"

cat > "$OHS_REQ/loan-$LOAN_EXT-disburse.json" <<EOF
{"actualDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
ohs_post "loan-$LOAN_EXT-disburse" "/loans/$LID?command=disburse" "$OHS_REQ/loan-$LOAN_EXT-disburse.json"

# ---- capture the freshly-created state (READ-ONLY) ------------------------
bash "$(dirname "$0")/capture-state.sh" "$LID" "created"

echo "--- created loan summary ---"
python3 - "$OHS_OUT/loan-$LID-created-detail-raw.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
s = d.get('summary', {})
print('status', d.get('status', {}).get('code'))
for k in ['principalDisbursed', 'totalExpectedRepayment', 'principalOutstanding',
          'interestOutstanding', 'feeChargesOutstanding', 'penaltyChargesOutstanding',
          'totalOutstanding']:
    print(f'  {k}={s.get(k)}')
for c in (d.get('charges') or []):
    print('  charge', c['id'], c['name'], 'penalty', c['penalty'], 'amt', c['amount'],
          'paid', c['amountPaid'], 'waived', c['amountWaived'], 'out', c['amountOutstanding'],
          'due', c.get('dueDate'), 'paidFlag', c['paid'], 'waivedFlag', c['waived'])
for p in (d.get('repaymentSchedule', {}).get('periods') or [])[:2]:
    print('  period', p.get('period'), 'due', p.get('dueDate'), 'complete', p.get('complete'),
          'prinDue', p.get('principalDue'), 'intDue', p.get('interestDue'),
          'feeDue', p.get('feeChargesDue'), 'penDue', p.get('penaltyChargesDue'))
PY
echo "step02 done. loanId=$LID"
