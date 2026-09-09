#!/usr/bin/env bash
# collateral context — collateral products, client collateral, loan-collateral links.
#
# This context has ONE rounding surface exposed through the API:
#   * GET /clients/{clientId}/collaterals/{collateralId} returns the single holding
#     with total = base_price * quantity and totalCollateral = total *
#     pct_to_base/100 computed on the read path (ClientCollateralManagement.java
#     getTotal / getTotalCollateral), even though the column holds only quantity
#     (verified via SQL: m_client_collateral_management has no total column).
#   * The loan-collateral link in this build is the LEGACY model (m_loan_collateral,
#     keyed by a LoanCollateral code value). Its `value` and `description` columns are
#     not populated by the POST; no quantity is stored. No division/rounding occurs.
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh

ohs_ctx collateral

PRODUCT_NAME="SEED-Collateral-Product"
CLIENT=5                 # SEED-C10 (L01 borrower)
LOAN=7                   # SEED-L07 (kept in submitted/pending-approval, created for this link)
CODE_ID=2                # m_code "LoanCollateral"
CODE_VALUE_NAME="SEED Collateral Type"

DB() { docker exec gerege-oracle-db psql -U postgres -d fineract_gerege -tA -c "$1"; }

# --- collateral product (idempotent by name) ----------------------------------
ohs_get collateral-products-pre "/collateral-management"
PRODUCT_ID=$(curl -sk "$OHS_BASE/collateral-management" -H "$OHS_AUTH" -H "$OHS_TEN" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next((x["id"] for x in d if x.get("name")=="'"$PRODUCT_NAME"'"), ""))')
if [ -n "$PRODUCT_ID" ]; then
    echo "collateral product '$PRODUCT_NAME' already exists id=$PRODUCT_ID (reused)" >&2
else
    cat > "$OHS_REQ/collateral-product.json" <<EOF
{"name":"$PRODUCT_NAME","basePrice":100000,"pctToBase":50,"unitType":1,"currency":"MNT","quality":"Good","locale":"en"}
EOF
    ohs_post collateral-product "/collateral-management" "$OHS_REQ/collateral-product.json"
    PRODUCT_ID=$(ohs_id "$OHS_OUT/collateral-product-raw.json")
fi
ohs_get collateral-products-post "/collateral-management"

# --- LoanCollateral code value (legacy loan-collateral type, idempotent) -------
CV_ID=$(DB "SELECT id FROM m_code_value WHERE code_id=$CODE_ID AND code_value='$CODE_VALUE_NAME';")
if [ -z "$CV_ID" ]; then
    cat > "$OHS_REQ/collateral-codevalue.json" <<EOF
{"name":"$CODE_VALUE_NAME","description":"SEED LoanCollateral code value"}
EOF
    ohs_post collateral-codevalue "/codes/$CODE_ID/codevalues" "$OHS_REQ/collateral-codevalue.json"
    CV_ID=$(python3 -c 'import json;print(json.load(open("'"$OHS_OUT"'/collateral-codevalue-raw.json"))["subResourceId"])')
else
    echo "LoanCollateral code value already exists id=$CV_ID (reused)" >&2
fi

# --- client collateral (idempotent via DB) ------------------------------------
CC_ID=$(DB "SELECT id FROM m_client_collateral_management WHERE client_id=$CLIENT AND collateral_id=$PRODUCT_ID ORDER BY id LIMIT 1;")
if [ -z "$CC_ID" ]; then
    cat > "$OHS_REQ/client-collateral.json" <<EOF
{"collateralId":$PRODUCT_ID,"quantity":1.5,"description":"SEED client collateral"}
EOF
    ohs_post client-collateral "/clients/$CLIENT/collaterals" "$OHS_REQ/client-collateral.json"
    CC_ID=$(ohs_id "$OHS_OUT/client-collateral-raw.json")
else
    echo "client collateral already exists id=$CC_ID (reused)" >&2
fi

# --- loan-collateral link (legacy, idempotent via DB) -------------------------
LC_ID=$(DB "SELECT id FROM m_loan_collateral WHERE loan_id=$LOAN AND type_cv_id=$CV_ID ORDER BY id LIMIT 1;")
if [ -z "$LC_ID" ]; then
    cat > "$OHS_REQ/loan-collateral.json" <<EOF
{"collateralTypeId":$CV_ID,"quantity":2}
EOF
    ohs_post loan-collateral "/loans/$LOAN/collaterals" "$OHS_REQ/loan-collateral.json"
    LC_ID=$(ohs_id "$OHS_OUT/loan-collateral-raw.json")
else
    echo "loan collateral already exists id=$LC_ID (reused)" >&2
fi

# --- read-backs ---------------------------------------------------------------
ohs_get client-collateral-readback "/clients/$CLIENT/collaterals"
ohs_get client-collateral-single "/clients/$CLIENT/collaterals/$CC_ID"
ohs_get loan-collateral-readback   "/loans/$LOAN/collaterals"
ohs_get collateral-product-readback "/collateral-management"

# --- MANIFEST -----------------------------------------------------------------
python3 - "$OHS_OUT" "$PRODUCT_ID" "$CC_ID" "$LC_ID" "$CV_ID" <<'PY'
import json, os, sys
out = sys.argv[1]
product_id, cc_id, lc_id, cv_id = sys.argv[2:6]
manifest = {
    "context": "collateral",
    "roundingSurface": {
        "seam": "client-collateral-single read-back",
        "note": ("GET /clients/{clientId}/collaterals/{collateralId} (client-collateral-single-raw.json) "
                 "computes total = base_price * quantity and totalCollateral = total * (pct_to_base/100) on "
                 "the read path and returns them as JSON numbers; the m_client_collateral_management column "
                 "stores only quantity (verified via SQL, no total column). The loan-collateral link in this "
                 "build is the legacy m_loan_collateral model keyed by a LoanCollateral code value; POST "
                 "stores only type_cv_id (value/description null, no quantity).")
    },
    "objects": {
        "collateralProduct": {"id": product_id, "name": "SEED-Collateral-Product",
                               "basePrice": 100000, "pctToBase": 50, "unitType": 1, "currency": "MNT"},
        "loanCollateralCodeValue": {"id": cv_id, "code": "LoanCollateral", "name": "SEED Collateral Type"},
        "clientCollateral": {"id": cc_id, "clientId": 5, "collateralId": product_id, "quantity": 1.5},
        "loanCollateralLink": {"id": lc_id, "loanId": 7, "collateralTypeCodeValueId": cv_id},
        "pendingLoanForLink": {"id": 7, "externalId": "SEED-L07", "state": "submitted and pending approval"},
    },
    "readBackQuirks": {
        "clientCollateral": "GET /clients/5/collaterals returns [] even though m_client_collateral_management has the row (verified via SQL); the write path and read path appear to target different models in this build.",
        "clientCollateralSingle": "GET /clients/5/collaterals/2 returns the single row with computed total=150000.0000000000 and totalCollateral=75000.000000000000000 (basePrice 100000.00000 * quantity 1.50000 = total; total * 50/100 = totalCollateral)."
    },
}
open(os.path.join(out, "..", "MANIFEST.json"), "w").write(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
PY
