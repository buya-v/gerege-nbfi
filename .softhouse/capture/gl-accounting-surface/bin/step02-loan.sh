#!/usr/bin/env bash
# STEP 2 — ONE new ADDITIVE loan (OHLGT-L03) on product 3 (OHLGR-Accrual-Loan,
# accountingRule ACCRUAL PERIODIC) carrying BOTH new charges as specified-due-date
# charges, so both stay OUTSTANDING at the pinned business date 2026-09-02 and can
# never be auto-repaid at disbursement. Values differ (fee 100, penalty 57).
#
# Every numeric token in the bodies below is an integer or a JSON string:
#   principal                  "100000"   (string, the Path A shape)
#   charges[].amount           100, 57    (integer; survives the POST /charges double)
#   loanTermFrequency etc.     12, 1, ... (integers)
# Nothing is re-serialised; each body is written as literal bytes and posted with
# --data-binary (common.sh `api_post`).
source "$(dirname "$0")/common.sh"

PRODUCT=$(state_get loanProduct)
[ -z "$PRODUCT" ] && PRODUCT=3
FEE=$(state_get feeCharge)
PEN=$(state_get penaltyCharge)
CLIENT=$(state_get client)
[ -z "$CLIENT" ] && CLIENT=11
DATE="01 January 2026"

cat > "$REQ/loan-OHLGT-L03-submit.json" <<EOF
{
  "clientId": $CLIENT,
  "productId": $PRODUCT,
  "externalId": "OHLGT-L03",
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
    {"chargeId": $FEE, "amount": 100, "dueDate": "15 February 2026"},
    {"chargeId": $PEN, "amount": 57, "dueDate": "15 March 2026"}
  ],
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
api_post "/loans" "$REQ/loan-OHLGT-L03-submit.json" > "$OUT/loan-OHLGT-L03-submit-raw.json"
cat "$OUT/loan-OHLGT-L03-submit-raw.json"; echo
LID=$(python3 -c "import json;print(json.load(open('$OUT/loan-OHLGT-L03-submit-raw.json')).get('resourceId',''))")
[ -z "$LID" ] && { echo "SUBMIT FAILED"; exit 3; }

cat > "$REQ/loan-OHLGT-L03-approve.json" <<EOF
{"approvedOnDate":"$DATE","expectedDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
api_post "/loans/$LID?command=approve" "$REQ/loan-OHLGT-L03-approve.json" > "$OUT/loan-OHLGT-L03-approve-raw.json"
cat "$OUT/loan-OHLGT-L03-approve-raw.json"; echo

cat > "$REQ/loan-OHLGT-L03-disburse.json" <<EOF
{"actualDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
api_post "/loans/$LID?command=disburse" "$REQ/loan-OHLGT-L03-disburse.json" > "$OUT/loan-OHLGT-L03-disburse-raw.json"
cat "$OUT/loan-OHLGT-L03-disburse-raw.json"; echo

state_set loan3 "$LID"
echo "loan3=$LID"
