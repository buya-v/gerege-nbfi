#!/usr/bin/env bash
# STEP 2 (OH-PROVEDGE-BA): create three ACTIVE loans on product 2 (SEED-Probe-Loan)
# whose FIRST instalment is due exactly 29 / 59 / 89 days before the pinned
# business date 2026-09-03, with no repayment made.
#
# Fineract's monthly (repaymentFrequencyType=2, repaymentEvery=1) schedule puts
# the first due date one month after the actual disbursement date, so:
#
#   age 89  due 2026-06-06  <- disburse 2026-05-06
#   age 59  due 2026-07-06  <- disburse 2026-06-06
#   age 29  due 2026-08-05  <- disburse 2026-07-05
#
# Ages are confirmed from the oracle's own loan read-back in step 3 BEFORE any
# provisioning entry is created. Request bodies are written once and posted with
# --data-binary so every body is byte-stable.
set -uo pipefail

BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'
REQ_DIR=".softhouse/capture/provisioning-upper-edge/req"
OUT_DIR=".softhouse/capture/provisioning-upper-edge/out"
DB='gerege-oracle-db'

mkdir -p "$REQ_DIR" "$OUT_DIR"

PRODUCT=2

# externalId | client externalId | client activation | disbursement/first-due+1mo
LOANS=(
  "EDGE-L89|EDGE-C89|06 April 2026|06 May 2026"
  "EDGE-L59|EDGE-C59|06 May 2026|06 June 2026"
  "EDGE-L29|EDGE-C29|05 June 2026|05 July 2026"
)

existing_client() {
  curl -sk "$BASE/clients?limit=1000" -H "$AUTH" -H "$TEN" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); items=d.get('pageItems', d if isinstance(d,list) else []); print([c['id'] for c in items if c.get('externalId')=='$1'])"
}

existing_loan() {
  curl -sk "$BASE/loans?externalId=$1" -H "$AUTH" -H "$TEN" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); items=d.get('pageItems', []); print([x['id'] for x in items])"
}

for entry in "${LOANS[@]}"; do
  IFS='|' read -r ext cext activation disburse <<< "$entry"

  # --- client (idempotent) ---
  ec=$(existing_client "$cext")
  if [ "$ec" != "[]" ]; then
    cid=$(echo "$ec" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
    echo "client $cext exists id=$cid"
  else
    cat > "$REQ_DIR/client-$cext.json" <<EOF
{"officeId":1,"firstname":"$cext","lastname":"Borrower","externalId":"$cext","legalFormId":1,"active":true,"activationDate":"$activation","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    curl -sk -X POST "$BASE/clients" -H "$AUTH" -H "$TEN" -H "$CT" \
      --data-binary @"$REQ_DIR/client-$cext.json" > "$OUT_DIR/client-$cext-raw.json"
    cid=$(python3 -c "import json;d=json.load(open('$OUT_DIR/client-$cext-raw.json'));print(d.get('resourceId', d.get('clientId', d.get('id',''))))")
    echo "client $cext created id=$cid"
  fi

  # --- loan (idempotent, keyed on externalId) ---
  el=$(existing_loan "$ext")
  if [ "$el" != "[]" ]; then
    lid=$(echo "$el" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
    echo "loan $ext exists id=$lid"
  else
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
  "submittedOnDate": "$disburse",
  "expectedDisbursementDate": "$disburse",
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
    curl -sk -X POST "$BASE/loans" -H "$AUTH" -H "$TEN" -H "$CT" \
      --data-binary @"$REQ_DIR/loan-$ext-submit.json" > "$OUT_DIR/loan-$ext-submit-raw.json"
    lid=$(python3 -c "import json;print(json.load(open('$OUT_DIR/loan-$ext-submit-raw.json')).get('resourceId',''))")
    if [ -z "$lid" ]; then
      echo "loan $ext SUBMIT FAILED => $(cat "$OUT_DIR/loan-$ext-submit-raw.json")" >&2
      exit 1
    fi

    cat > "$REQ_DIR/loan-$ext-approve.json" <<EOF
{"approvedOnDate":"$disburse","expectedDisbursementDate":"$disburse","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    curl -sk -X POST "$BASE/loans/$lid?command=approve" -H "$AUTH" -H "$TEN" -H "$CT" \
      --data-binary @"$REQ_DIR/loan-$ext-approve.json" > "$OUT_DIR/loan-$ext-approve-raw.json"

    cat > "$REQ_DIR/loan-$ext-disburse.json" <<EOF
{"actualDisbursementDate":"$disburse","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    curl -sk -X POST "$BASE/loans/$lid?command=disburse" -H "$AUTH" -H "$TEN" -H "$CT" \
      --data-binary @"$REQ_DIR/loan-$ext-disburse.json" > "$OUT_DIR/loan-$ext-disburse-raw.json"
    echo "loan $ext created id=$lid (disburse $disburse)"
  fi

  echo "$ext|$cext|$cid|$lid" >> "$OUT_DIR/edge-loans-idmap.txt"
  sleep 1
done

echo "--- first instalment due dates, read-only SQL (corroboration) ---"
docker exec "$DB" psql -U postgres -d fineract_gerege -A -F'|' -c \
"select l.id, l.external_id, s.duedate, s.completed_derived
   from m_loan l join m_loan_repayment_schedule s on s.loan_id=l.id
  where l.external_id like 'EDGE-L%' and s.installment=1 order by l.id;"

echo "loans done"
