#!/usr/bin/env bash
# OH-WCCAP-P — wc-discount-nonzero, step 2: submit a facility on the discounted
# product, approve, disburse, and read the balance back.
#
# Expected (from WorkingCapitalLoanBalance.applyDisbursement, discount 37.53,
# disbursed 1000):
#   totalDiscountFee              = 37.53   -> 3753 minor
#   principal                     = 1037.53 -> 103753 minor
#   unrealizedIncomeFromDiscountFee = max(37.53-0-0,0) = 37.53 -> 3753 minor
#
# All money tokens in req/ are integers (1000) or quoted decimal strings ("37.53").
#
# Re-runnable: the loan is keyed on externalId.
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh

ohs_ctx wc-discount-nonzero

PRODUCT_NAME="OHK-WC-Discount-Nonzero"
EXT_ID="OHWCCAP-DISCNONZERO-L01"
CLIENT=5                 # SEED-C11 Borrower, active
DATES="03 September 2026"
BUSINESS_DATE="2026-09-03"

PRODUCT_ID=$(curl -skS "$OHS_BASE/working-capital-loan-products" -H "$OHS_AUTH" -H "$OHS_TEN" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next((x["id"] for x in d if x.get("name")==sys.argv[1]),""))' "$PRODUCT_NAME")
if [ -z "$PRODUCT_ID" ]; then
    echo "REFUSED: discounted product '$PRODUCT_NAME' not found; run step01-product.sh first" >&2
    exit 3
fi
echo "PRODUCT_ID=$PRODUCT_ID" >&2

ohs_get wc-loans-pre "/working-capital-loans"

LOAN_ID=$(curl -skS "$OHS_BASE/working-capital-loans" -H "$OHS_AUTH" -H "$OHS_TEN" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next((x["id"] for x in d.get("content",[]) if x.get("externalId")==sys.argv[1]),""))' "$EXT_ID")

if [ -n "$LOAN_ID" ]; then
    echo "loan '$EXT_ID' already exists id=$LOAN_ID (reused)" >&2
else
    cat > "$OHS_REQ/wc-loan-discount-submit.json" <<EOF
{
  "clientId": $CLIENT,
  "productId": $PRODUCT_ID,
  "externalId": "$EXT_ID",
  "submittedOnDate": "$DATES",
  "expectedDisbursementDate": "$DATES",
  "principalAmount": 1000,
  "totalPaymentVolume": 1000,
  "periodPaymentRate": 1,
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
    ohs_post wc-loan-discount-submit "/working-capital-loans" "$OHS_REQ/wc-loan-discount-submit.json"
    LOAN_ID=$(ohs_id "$OHS_OUT/wc-loan-discount-submit-raw.json" 2>/dev/null || true)
    if [ -z "${LOAN_ID:-}" ]; then
        echo "REFUSED: no loan id after submit; status=$(cat "$OHS_OUT/wc-loan-discount-submit.status" 2>/dev/null)" >&2
        exit 3
    fi
fi
echo "LOAN_ID=$LOAN_ID" >&2

cat > "$OHS_REQ/wc-loan-discount-approve.json" <<EOF
{
  "approvedOnDate": "$DATES",
  "expectedDisbursementDate": "$DATES",
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
ohs_post wc-loan-discount-approve "/working-capital-loans/$LOAN_ID?command=approve" "$OHS_REQ/wc-loan-discount-approve.json"

cat > "$OHS_REQ/wc-loan-discount-disburse.json" <<EOF
{
  "actualDisbursementDate": "$DATES",
  "transactionAmount": 1000,
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
ohs_post wc-loan-discount-disburse "/working-capital-loans/$LOAN_ID?command=disburse" "$OHS_REQ/wc-loan-discount-disburse.json"

ohs_get wc-loan-discount-detail "/working-capital-loans/$LOAN_ID"
ohs_get wc-loans-post "/working-capital-loans"

echo "$LOAN_ID" > "$OHS_OUT/LOAN_ID"
echo "$BUSINESS_DATE" > "$OHS_OUT/business-date"
