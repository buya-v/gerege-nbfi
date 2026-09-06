#!/usr/bin/env bash
# shares context — share products, share accounts, purchase/approve/activate,
# and a share-product dividend (the discriminating rounding seam).
#
# Two seams are exercised:
#   1. PURCHASE: total = requestedShares (integer) * unitPrice (integer minor
#      units). 100 shares * 100 MNT = 10,000.00 MNT exactly. No percentage,
#      rate, apportionment or division enters this seam, so it has NO rounding
#      surface. An honest "cannot discriminate" for the purchase itself.
#   2. DIVIDEND: the dividend `dividendAmount` field is a money amount rounded
#      to the currency's 2 minor units (MNT, 2 dp) at create time.
#      dividendAmount = 0.005 MNT  (exactly half a minor unit)
#        HALF_UP   -> 0.01
#        HALF_EVEN -> 0.00
#      The observed read-back is 0.01 => HALF_UP, consistent with the tenant's
#      configured rounding-mode ordinal 4.
#
# Business date pinned to 2026-09-01 (never date/now). Tenant gerege only.
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh

ohs_ctx shares

PRODUCT_NAME="SEED-Share-Product"
ACCOUNT_EXT_ID="SEED-SHARE-ACCT"
CLIENT_ID=6        # SEED-C12 (owns savings account id 2, used for dividend payout)
SAVINGS_ID=2       # SEED-C12 daily savings account
REQUESTED_SHARES=100
UNIT_PRICE=100
DISCRIM_DIVIDEND="0.005"      # half minor unit

# --- product (idempotent: keyed on name) --------------------------------------
ohs_get shares-products-list "/products/share"

PRODUCT_ID=$(python3 - "$OHS_OUT/shares-products-list-raw.json" "$PRODUCT_NAME" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(next((p["id"] for p in d.get("pageItems", []) if p.get("name") == sys.argv[2]), ""))
PY
)

if [ -n "$PRODUCT_ID" ]; then
    echo "share product already exists id=$PRODUCT_ID (reused)" >&2
else
    cat > "$OHS_REQ/share-product-create.json" <<EOF
{"name":"$PRODUCT_NAME","shortName":"SSP","description":"SEED share product (OH-SWEEP shares context)","currencyCode":"MNT","digitsAfterDecimal":2,"inMultiplesOf":1,"locale":"en","totalShares":1000,"sharesIssued":1000,"unitPrice":$UNIT_PRICE,"minimumShares":1,"nominalShares":10,"maximumShares":1000,"accountingRule":1}
EOF
    ohs_post share-product-create "/products/share" "$OHS_REQ/share-product-create.json"
    PRODUCT_ID=$(ohs_id "$OHS_OUT/share-product-create-raw.json")
    [ -z "$PRODUCT_ID" ] || [ "$PRODUCT_ID" = "None" ] && { echo "share product CREATE FAILED" >&2; exit 1; }
fi

# --- account (idempotent: keyed on externalId) --------------------------------
ohs_get shares-accounts-list "/accounts/share?limit=100"

ACCOUNT_ID=$(python3 - "$OHS_OUT/shares-accounts-list-raw.json" "$ACCOUNT_EXT_ID" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(next((a["id"] for a in d.get("pageItems", []) if a.get("externalId") == sys.argv[2]), ""))
PY
)

if [ -n "$ACCOUNT_ID" ]; then
    echo "share account already exists id=$ACCOUNT_ID (reused)" >&2
else
    cat > "$OHS_REQ/share-account-submit.json" <<EOF
{"clientId":$CLIENT_ID,"productId":$PRODUCT_ID,"applicationDate":"01 September 2026","submittedDate":"01 September 2026","externalId":"$ACCOUNT_EXT_ID","requestedShares":$REQUESTED_SHARES,"savingsAccountId":$SAVINGS_ID,"locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post share-account-submit "/accounts/share" "$OHS_REQ/share-account-submit.json"
    ACCOUNT_ID=$(ohs_id "$OHS_OUT/share-account-submit-raw.json")
    [ -z "$ACCOUNT_ID" ] || [ "$ACCOUNT_ID" = "None" ] && { echo "share account SUBMIT FAILED" >&2; exit 1; }

    cat > "$OHS_REQ/share-account-approve.json" <<EOF
{"approvedDate":"01 September 2026","note":"OH-SWEEP shares context approve","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post share-account-approve "/accounts/share/$ACCOUNT_ID?command=approve" "$OHS_REQ/share-account-approve.json"

    cat > "$OHS_REQ/share-account-activate.json" <<EOF
{"activatedDate":"01 September 2026","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post share-account-activate "/accounts/share/$ACCOUNT_ID?command=activate" "$OHS_REQ/share-account-activate.json"
fi

# --- discriminating dividend (idempotent: create only if product has none) -----
ohs_get shares-product-dividends "/shareproduct/$PRODUCT_ID/dividend"

if python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get("totalFilteredRecords",0)==0 else 1)' "$OHS_OUT/shares-product-dividends-raw.json"; then
    cat > "$OHS_REQ/share-dividend-create.json" <<EOF
{"dividendPeriodStartDate":"01 September 2026","dividendPeriodEndDate":"30 September 2026","dividendAmount":"$DISCRIM_DIVIDEND","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post share-dividend-create "/shareproduct/$PRODUCT_ID/dividend" "$OHS_REQ/share-dividend-create.json"
else
    echo "share dividend already exists for product $PRODUCT_ID (reused)" >&2
fi

# --- read-backs ---------------------------------------------------------------
ohs_get share-product-detail "/products/share/$PRODUCT_ID"
ohs_get share-account-detail "/accounts/share/$ACCOUNT_ID?associations=all"
ohs_get shares-product-dividends "/shareproduct/$PRODUCT_ID/dividend"

# --- MANIFEST ------------------------------------------------------------------
python3 - "$OHS_OUT" "$PRODUCT_ID" "$ACCOUNT_ID" "$REQUESTED_SHARES" "$UNIT_PRICE" <<'PY'
import json, os, sys
out, product_id, account_id, req_shares, unit_price = sys.argv[1:6]

dividend = None
dp = os.path.join(out, "shares-product-dividends-raw.json")
if os.path.exists(dp):
    items = json.load(open(dp)).get("pageItems", [])
    if items:
        dividend = items[0]

manifest = {
    "context": "shares",
    "note": "share products, share accounts (purchase/approve/activate), and share-product dividend. Purchase total = requestedShares * unitPrice is integer*integer minor units => NO rounding surface. Discriminating seam is the dividend dividendAmount field rounded to 2 minor units at create: 0.005 MNT -> HALF_UP 0.01 / HALF_EVEN 0.00.",
    "roundingSurface": {
        "seam": "share-product dividend dividendAmount (money, rounded to 2dp at create)",
        "discriminatingInput": {
            "dividendAmount": "0.005",
            "dividendPeriodStartDate": "2026-09-01",
            "dividendPeriodEndDate": "2026-09-30",
        },
        "rawAmount": "0.005",
        "HALF_UP": "0.01",
        "HALF_EVEN": "0.00",
        "observedReadBackAmount": dividend.get("amount") if dividend else None,
        "dividendId": dividend.get("id") if dividend else None,
        "verdict": ("HALF_UP" if (dividend and dividend.get("amount") == 0.01)
                    else ("HALF_EVEN" if (dividend and dividend.get("amount") == 0.0) else "unexpected")),
    },
    "objects": {
        "products": [
            {"id": int(product_id), "name": "SEED-Share-Product", "shortName": "SSP",
             "unitPrice": int(unit_price), "totalShares": 1000},
        ],
        "accounts": [
            {"id": int(account_id), "externalId": "SEED-SHARE-ACCT", "clientId": 6,
             "savingsAccountId": 2, "requestedShares": int(req_shares),
             "note": "purchase total 100*100 = 10000.00 exact (no rounding seam)"},
        ],
        "dividends": [dividend] if dividend else [],
    },
}
open(os.path.join(out, "..", "MANIFEST.json"), "w").write(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
PY
