#!/usr/bin/env bash
set -uo pipefail

BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'
REQ_DIR=".softhouse/capture/seed/req"
OUT_DIR=".softhouse/capture/seed/out"
STATE="$OUT_DIR/state.json"

mkdir -p "$REQ_DIR" "$OUT_DIR"

PRODUCT=$(python3 -c "import json;print(json.load(open('$STATE'))['loanProduct'])")

# loan externalId -> client externalId -> disbursement date (relative to pinned
# business date 2026-09-01 so overdue ages land in distinct provisioning bands)
declare -a LOANS=(
  "SEED-L01|SEED-C11|01 June 2026"
  "SEED-L02|SEED-C12|01 July 2026"
  "SEED-L03|SEED-C13|01 August 2026"
)

CLIENT_ID() {
  python3 -c "import json;print(json.load(open('$STATE'))['clients']['$1'])"
}

seed_loan() {
  local ext="$1" client_ext="$2" date="$3"
  local cid lid

  cid=$(CLIENT_ID "$client_ext")

  # idempotence: key on externalId
  local existing
  existing=$(curl -sk "$BASE/loans?externalId=$ext" -H "$AUTH" -H "$TEN" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); items=d.get('pageItems', []); print([x['id'] for x in items])")
  if [ "$existing" != "[]" ]; then
    lid=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
    echo "loan $ext already exists id=$lid (reused)" >&2
    echo "{\"externalId\":\"$ext\",\"id\":$lid,\"reused\":true}"
    return
  fi

  # 1) submit
  cat > "$REQ_DIR/loan-$ext-submit.json" <<EOF
{
  "clientId": $cid,
  "productId": $PRODUCT,
  "externalId": "$ext",
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
  "submittedOnDate": "$date",
  "expectedDisbursementDate": "$date",
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
  curl -sk -X POST "$BASE/loans" -H "$AUTH" -H "$TEN" -H "$CT" \
    --data-binary @"$REQ_DIR/loan-$ext-submit.json" > "$OUT_DIR/loan-$ext-submit-raw.json"
  lid=$(python3 -c "import json;print(json.load(open('$OUT_DIR/loan-$ext-submit-raw.json')).get('resourceId',''))")

  if [ -z "$lid" ]; then
    echo "loan $ext SUBMIT FAILED => $(cat "$OUT_DIR/loan-$ext-submit-raw.json")" >&2
    echo "{\"externalId\":\"$ext\",\"id\":null,\"reused\":false,\"error\":true}"
    return
  fi

  # 2) approve
  cat > "$REQ_DIR/loan-$ext-approve.json" <<EOF
{
  "approvedOnDate": "$date",
  "expectedDisbursementDate": "$date",
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
  curl -sk -X POST "$BASE/loans/$lid?command=approve" -H "$AUTH" -H "$TEN" -H "$CT" \
    --data-binary @"$REQ_DIR/loan-$ext-approve.json" > "$OUT_DIR/loan-$ext-approve-raw.json"

  # 3) disburse
  cat > "$REQ_DIR/loan-$ext-disburse.json" <<EOF
{
  "actualDisbursementDate": "$date",
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
  curl -sk -X POST "$BASE/loans/$lid?command=disburse" -H "$AUTH" -H "$TEN" -H "$CT" \
    --data-binary @"$REQ_DIR/loan-$ext-disburse.json" > "$OUT_DIR/loan-$ext-disburse-raw.json"

  echo "{\"externalId\":\"$ext\",\"id\":$lid,\"reused\":false}"
}

RESULTS=""
for entry in "${LOANS[@]}"; do
  IFS='|' read -r ext client_ext date <<< "$entry"
  R=$(seed_loan "$ext" "$client_ext" "$date")
  echo "$R"
  RESULTS="$RESULTS $R"
done

python3 - "$STATE" $RESULTS <<'PY'
import json,sys
state=json.load(open(sys.argv[1]))
loans={}
for arg in sys.argv[2:]:
    o=json.loads(arg)
    if o.get('id') is not None:
        loans[o['externalId']]=o['id']
state['loans']=loans
json.dump(state, open(sys.argv[1],'w'), indent=2)
PY
echo "loans state => $(cat "$STATE")"
