#!/usr/bin/env bash
# OH-WCCAP-P — wc-discount-nonzero, step 1: create the DISCOUNTED working-capital
# product and read it back.
#
# The seed product (id 1, SEED-WC-Product) carries discount 0 (or null), so
# `totalDiscountFee` is structurally zero on the seeded facility and the clamp in
# `UnrealizedIncomeFromDiscountFee` has never had a non-zero operand. This creates
# a product whose `discount` is NON-ZERO.
#
# Chosen numbers (arithmetic worked out BEFORE creating anything):
#
#   product discount = 37.53   -> non-round: a whole-tugrik or hardcoded-zero
#                                 port loses the .53, so truncation is visible.
#                                 Stored directly by
#                                 WorkingCapitalLoanBalance.applyDisbursement()
#                                 [WorkingCapitalLoanBalance.java:117], not
#                                 multiplied by anything, so it lands on exactly
#                                 3753 minor units (MNT, minor unit 2). NO
#                                 sub-minor residue (G-19 / DEC-2 predicate G-08).
#
# `allowAttributeOverrides.discountDefault = false` makes the product discount the
# NON-OVERRIDABLE default, so a loan submitted on this product inherits it without a
# per-loan `discount` param (WorkingCapitalLoanAssemblerImpl.java:187-190).
#
# Re-runnable: the product is keyed on name.
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh

ohs_ctx wc-discount-nonzero

PRODUCT_NAME="OHK-WC-Discount-Nonzero"

ohs_get wc-products-pre "/working-capital-loan-products"

PRODUCT_ID=$(curl -skS "$OHS_BASE/working-capital-loan-products" -H "$OHS_AUTH" -H "$OHS_TEN" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next((x["id"] for x in d if x.get("name")==sys.argv[1]),""))' "$PRODUCT_NAME")

if [ -n "$PRODUCT_ID" ]; then
    echo "product '$PRODUCT_NAME' already exists id=$PRODUCT_ID (reused)" >&2
else
    cat > "$OHS_REQ/wc-product-discount-create.json" <<'EOF'
{
  "name": "OHK-WC-Discount-Nonzero",
  "shortName": "WCD1",
  "description": "Working Capital Loan Product with a non-zero discount",
  "periodPaymentRate": 1,
  "repaymentFrequencyType": "DAYS",
  "repaymentEvery": 30,
  "currencyCode": "MNT",
  "digitsAfterDecimal": 2,
  "inMultiplesOf": 1,
  "principal": 1000,
  "minPrincipal": 10,
  "maxPrincipal": 100000,
  "amortizationType": "EIR",
  "npvDayCount": 360,
  "discount": "37.53",
  "dateFormat": "dd MMMM yyyy",
  "locale": "en",
  "accountingRule": "NONE",
  "allowAttributeOverrides": {
    "delinquencyBucketClassification": false,
    "breach": false,
    "discountDefault": false,
    "periodPaymentFrequency": false,
    "periodPaymentFrequencyType": false
  },
  "paymentAllocation": [
    {
      "transactionType": "DEFAULT",
      "paymentAllocationOrder": [
        {"order": 1, "paymentAllocationRule": "DUE_PENALTY"},
        {"order": 2, "paymentAllocationRule": "DUE_FEE"},
        {"order": 3, "paymentAllocationRule": "DUE_PRINCIPAL"},
        {"order": 4, "paymentAllocationRule": "IN_ADVANCE_PENALTY"},
        {"order": 5, "paymentAllocationRule": "IN_ADVANCE_FEE"},
        {"order": 6, "paymentAllocationRule": "IN_ADVANCE_PRINCIPAL"}
      ]
    }
  ]
}
EOF
    ohs_post wc-product-discount-create "/working-capital-loan-products" "$OHS_REQ/wc-product-discount-create.json"
    PRODUCT_ID=$(ohs_id "$OHS_OUT/wc-product-discount-create-raw.json" 2>/dev/null || true)
    if [ -z "${PRODUCT_ID:-}" ]; then
        echo "REFUSED: no product id after POST; status=$(cat "$OHS_OUT/wc-product-discount-create.status" 2>/dev/null)" >&2
        echo "$PRODUCT_ID" > "$OHS_OUT/wc-product-discount-create.resourceId" 2>/dev/null || true
        exit 3
    fi
fi
echo "PRODUCT_ID=$PRODUCT_ID" >&2

ohs_get wc-products-post "/working-capital-loan-products"
ohs_get wc-product-discount-readback "/working-capital-loan-products/$PRODUCT_ID"

echo "$PRODUCT_ID" > "$OHS_OUT/PRODUCT_ID"
