#!/usr/bin/env bash
# STEP 8 (OH-PROV): add one ROUNDING-SENSITIVE loan whose reserve amount lands
# on a half minor unit, so HALF_UP and HALF_EVEN give DIFFERENT answers.
#
# The loan is submitted against the same SEED-Probe-Loan product but with
# interestRatePerPeriod = 0, so total_outstanding_derived equals the principal
# exactly (interest_outstanding_derived = 0). Principal = 41850.09 MNT
# (4,185,009 minor units). Disbursed 2026-06-01 -> first repayment due
# 2026-07-01 -> 62 days overdue on 2026-09-01, inside DOUBTFUL (60..89, 50 %).
#
#   50 % of 41850.09 = 20925.045 MNT = 2,092,504.5 minor units
#     HALF_UP  -> 20925.05 MNT (2,092,505 minor units)
#     HALF_EVEN -> 20925.04 MNT (2,092,504 minor units)
#
# The two modes disagree on the 5 in the third decimal, which is exactly the
# discrimination that proves the gerege tenant rounds HALF_UP.
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
CLIENT_EXT="SEED-C15"
LOAN_EXT="SEED-L05"
DATE="01 June 2026"
ACTIVATION="01 May 2026"
PRINCIPAL="41850.09"

# --- client (idempotent) -----------------------------------------------------
existing=$(curl -sk "$BASE/clients?limit=1000" -H "$AUTH" -H "$TEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); items=d.get('pageItems', d if isinstance(d,list) else []); print([c['id'] for c in items if c.get('externalId')=='$CLIENT_EXT'])")

if [ "$existing" != "[]" ]; then
  cid=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
  echo "client $CLIENT_EXT already exists id=$cid (reused)"
else
  cat > "$REQ_DIR/client-$CLIENT_EXT.json" <<EOF
{"officeId":1,"firstname":"$CLIENT_EXT","lastname":"Borrower","externalId":"$CLIENT_EXT","legalFormId":1,"active":true,"activationDate":"$ACTIVATION","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
  curl -sk -X POST "$BASE/clients" -H "$AUTH" -H "$TEN" -H "$CT" \
    --data-binary @"$REQ_DIR/client-$CLIENT_EXT.json" \
    > "$OUT_DIR/client-$CLIENT_EXT-raw.json"
  cid=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('resourceId', d.get('clientId', d.get('id',''))))" < "$OUT_DIR/client-$CLIENT_EXT-raw.json")
  echo "client $CLIENT_EXT created id=$cid"
fi

# --- loan (idempotent) --------------------------------------------------------
existing=$(curl -sk "$BASE/loans?externalId=$LOAN_EXT" -H "$AUTH" -H "$TEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); items=d.get('pageItems', []); print([x['id'] for x in items])")
if [ "$existing" != "[]" ]; then
  lid=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
  echo "loan $LOAN_EXT already exists id=$lid (reused)"
else
  cat > "$REQ_DIR/loan-$LOAN_EXT-submit.json" <<EOF
{
  "clientId": $cid,
  "productId": $PRODUCT,
  "externalId": "$LOAN_EXT",
  "principal": "$PRINCIPAL",
  "loanTermFrequency": 12,
  "loanTermFrequencyType": 2,
  "numberOfRepayments": 12,
  "repaymentEvery": 1,
  "repaymentFrequencyType": 2,
  "interestRatePerPeriod": 0,
  "interestRateFrequencyType": 3,
  "amortizationType": 1,
  "interestType": 0,
  "interestCalculationPeriodType": 1,
  "transactionProcessingStrategyCode": "mifos-standard-strategy",
  "loanType": "individual",
  "submittedOnDate": "$DATE",
  "expectedDisbursementDate": "$DATE",
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
  curl -sk -X POST "$BASE/loans" -H "$AUTH" -H "$TEN" -H "$CT" \
    --data-binary @"$REQ_DIR/loan-$LOAN_EXT-submit.json" > "$OUT_DIR/loan-$LOAN_EXT-submit-raw.json"
  lid=$(python3 -c "import json;print(json.load(open('$OUT_DIR/loan-$LOAN_EXT-submit-raw.json')).get('resourceId',''))")
  if [ -z "$lid" ]; then
    echo "loan $LOAN_EXT SUBMIT FAILED => $(cat "$OUT_DIR/loan-$LOAN_EXT-submit-raw.json")" >&2
    exit 1
  fi

  cat > "$REQ_DIR/loan-$LOAN_EXT-approve.json" <<EOF
{"approvedOnDate":"$DATE","expectedDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
  curl -sk -X POST "$BASE/loans/$lid?command=approve" -H "$AUTH" -H "$TEN" -H "$CT" \
    --data-binary @"$REQ_DIR/loan-$LOAN_EXT-approve.json" > "$OUT_DIR/loan-$LOAN_EXT-approve-raw.json"

  cat > "$REQ_DIR/loan-$LOAN_EXT-disburse.json" <<EOF
{"actualDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
  curl -sk -X POST "$BASE/loans/$lid?command=disburse" -H "$AUTH" -H "$TEN" -H "$CT" \
    --data-binary @"$REQ_DIR/loan-$LOAN_EXT-disburse.json" > "$OUT_DIR/loan-$LOAN_EXT-disburse-raw.json"
  echo "loan $LOAN_EXT created id=$lid"
fi

# --- merge state --------------------------------------------------------------
python3 - "$STATE" "$CLIENT_EXT" "$cid" "$LOAN_EXT" "$lid" <<'PY'
import json, sys
state_path, client_ext, cid, loan_ext, lid = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
state = json.load(open(state_path))
state.setdefault('clients', {})[client_ext] = cid
state.setdefault('loans', {})[loan_ext] = lid
json.dump(state, open(state_path, 'w'), indent=2)
PY
echo "state => $(cat "$STATE")"
