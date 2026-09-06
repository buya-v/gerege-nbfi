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

LP_NAME="SEED-Probe-Loan"

existing=$(curl -sk "$BASE/loanproducts" -H "$AUTH" -H "$TEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print([p['id'] for p in d if p.get('name')=='$LP_NAME'])")

if [ "$existing" != "[]" ]; then
  id=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
  echo "loan product already exists id=$id (reused)"
  python3 - "$STATE" "$id" <<'PY'
import json,sys
state=json.load(open(sys.argv[1])); state['loanProduct']=int(sys.argv[2])
json.dump(state, open(sys.argv[1],'w'), indent=2)
PY
  echo "product state => $(cat "$STATE")"
  exit 0
fi

cat > "$REQ_DIR/loanproduct.json" <<'EOF'
{
  "name": "SEED-Probe-Loan",
  "shortName": "SEED",
  "description": "SEED provisioning probe loan",
  "currencyCode": "MNT",
  "digitsAfterDecimal": 2,
  "inMultiplesOf": 0,
  "principal": 100000,
  "numberOfRepayments": 12,
  "repaymentEvery": 1,
  "repaymentFrequencyType": 2,
  "interestRatePerPeriod": 12,
  "interestRateFrequencyType": 3,
  "amortizationType": 1,
  "interestType": 0,
  "interestCalculationPeriodType": 1,
  "transactionProcessingStrategyCode": "mifos-standard-strategy",
  "accountingRule": 1,
  "daysInMonthType": 1,
  "daysInYearType": 1,
  "isInterestRecalculationEnabled": false,
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF

curl -sk -X POST "$BASE/loanproducts" \
  -H "$AUTH" -H "$TEN" -H "$CT" \
  --data-binary @"$REQ_DIR/loanproduct.json" \
  > "$OUT_DIR/loanproduct-raw.json"

resp=$(cat "$OUT_DIR/loanproduct-raw.json")
echo "loanproduct POST resp => $resp"

id=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('resourceId', d.get('loanProductId', d.get('id',''))))" <<<"$resp")
python3 - "$STATE" "$id" <<'PY'
import json,sys
state=json.load(open(sys.argv[1])); state['loanProduct']=int(sys.argv[2]) if sys.argv[2] else None
json.dump(state, open(sys.argv[1],'w'), indent=2)
PY
echo "product state => $(cat "$STATE")"
