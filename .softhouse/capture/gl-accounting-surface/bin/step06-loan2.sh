#!/usr/bin/env bash
# STEP 6 — second ADDITIVE loan (OHGLR-L02) whose fee AND penalty are both
# specified-due-date charges, so both stay OUTSTANDING at the pinned business
# date 2026-09-02 and can never be auto-repaid at disbursement. Values differ
# (fee 100.00, penalty 57.00) so a term-swap defect cannot survive.
source "$(dirname "$0")/common.sh"

PRODUCT=$(state_get loanProduct)
FEE=$(state_get feeSddCharge)
PEN=$(state_get penaltyCharge)
CLIENT=$(state_get client)
DATE="01 January 2026"

cat > "$REQ/loan-OHGLR-L02-submit.json" <<EOF
{
  "clientId": $CLIENT,
  "productId": $PRODUCT,
  "externalId": "OHGLR-L02",
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
    {"chargeId": $FEE, "amount": 100.00, "dueDate": "15 February 2026"},
    {"chargeId": $PEN, "amount": 57.00, "dueDate": "15 March 2026"}
  ],
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
api_post "/loans" "$REQ/loan-OHGLR-L02-submit.json" > "$OUT/loan-OHGLR-L02-submit-raw.json"
cat "$OUT/loan-OHGLR-L02-submit-raw.json"; echo
LID=$(python3 -c "import json;print(json.load(open('$OUT/loan-OHGLR-L02-submit-raw.json')).get('resourceId',''))")
[ -z "$LID" ] && { echo "SUBMIT FAILED"; exit 3; }

cat > "$REQ/loan-OHGLR-L02-approve.json" <<EOF
{"approvedOnDate":"$DATE","expectedDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
api_post "/loans/$LID?command=approve" "$REQ/loan-OHGLR-L02-approve.json" > "$OUT/loan-OHGLR-L02-approve-raw.json"
cat "$OUT/loan-OHGLR-L02-approve-raw.json"; echo

cat > "$REQ/loan-OHGLR-L02-disburse.json" <<EOF
{"actualDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
api_post "/loans/$LID?command=disburse" "$REQ/loan-OHGLR-L02-disburse.json" > "$OUT/loan-OHGLR-L02-disburse-raw.json"
cat "$OUT/loan-OHGLR-L02-disburse-raw.json"; echo

state_set loan2 "$LID"
echo "loan2=$LID"
