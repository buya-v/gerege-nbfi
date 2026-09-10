#!/usr/bin/env bash
# STEP 4 — create a NEW client and a NEW loan on the accrual product, submit ->
# approve -> disburse. The loan carries BOTH new charges so fee and penalty
# outstanding are non-zero AND differ (100.00 vs 57.00).
source "$(dirname "$0")/common.sh"

PRODUCT=$(state_get loanProduct)
FEE=$(state_get feeCharge)
PEN=$(state_get penaltyCharge)
ACTIVATION="01 December 2025"
DATE="01 January 2026"

# ---- client -------------------------------------------------------------
existing=$(api_get "/clients?limit=1000" | python3 -c "import json,sys; d=json.load(sys.stdin); items=d.get('pageItems', d if isinstance(d,list) else []); print([c['id'] for c in items if c.get('externalId')=='OHGLR-C02'])")
if [ "$existing" != "[]" ]; then
  CID=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
  echo "client reused id=$CID"
else
  cat > "$REQ/client-OHGLR-C02.json" <<EOF
{"officeId":1,"firstname":"OHGLR-C02","lastname":"Borrower","externalId":"OHGLR-C02","legalFormId":1,"active":true,"activationDate":"$ACTIVATION","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
  api_post "/clients" "$REQ/client-OHGLR-C02.json" > "$OUT/client-OHGLR-C02-raw.json"
  cat "$OUT/client-OHGLR-C02-raw.json"
  echo
  CID=$(python3 -c "import json;print(json.load(open('$OUT/client-OHGLR-C02-raw.json')).get('resourceId',''))")
fi

# ---- loan ---------------------------------------------------------------
existing=$(api_get "/loans?externalId=OHGLR-L01" | python3 -c "import json,sys; d=json.load(sys.stdin); print([x['id'] for x in d.get('pageItems',[])])")
if [ "$existing" != "[]" ]; then
  LID=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
  echo "loan reused id=$LID"
else
  cat > "$REQ/loan-OHGLR-L01-submit.json" <<EOF
{
  "clientId": $CID,
  "productId": $PRODUCT,
  "externalId": "OHGLR-L01",
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
    {"chargeId": $FEE, "amount": 100.00},
    {"chargeId": $PEN, "amount": 57.00, "dueDate": "15 March 2026"}
  ],
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
  api_post "/loans" "$REQ/loan-OHGLR-L01-submit.json" > "$OUT/loan-OHGLR-L01-submit-raw.json"
  cat "$OUT/loan-OHGLR-L01-submit-raw.json"; echo
  LID=$(python3 -c "import json;print(json.load(open('$OUT/loan-OHGLR-L01-submit-raw.json')).get('resourceId',''))")
  [ -z "$LID" ] && { echo "SUBMIT FAILED — refusing to continue"; exit 3; }

  cat > "$REQ/loan-OHGLR-L01-approve.json" <<EOF
{"approvedOnDate":"$DATE","expectedDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
  api_post "/loans/$LID?command=approve" "$REQ/loan-OHGLR-L01-approve.json" > "$OUT/loan-OHGLR-L01-approve-raw.json"
  cat "$OUT/loan-OHGLR-L01-approve-raw.json"; echo

  cat > "$REQ/loan-OHGLR-L01-disburse.json" <<EOF
{"actualDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
  api_post "/loans/$LID?command=disburse" "$REQ/loan-OHGLR-L01-disburse.json" > "$OUT/loan-OHGLR-L01-disburse-raw.json"
  cat "$OUT/loan-OHGLR-L01-disburse-raw.json"; echo
fi

state_set client "$CID"
state_set loan "$LID"
echo "client=$CID loan=$LID product=$PRODUCT fee=$FEE penalty=$PEN"
