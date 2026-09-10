#!/usr/bin/env bash
# shares-nonround-money — widen the shares corpus's frozen money columns.
#
# SUBJECT: a share product whose unit price is NOT the seed 100.00 and whose
# share counts are NOT the seed 1000/100, opened and driven to an Active
# purchase so `unit_price`, `share_capital`, `total_shares`, `purchased_price`,
# `purchased_amount` and the approved-share count all finally vary in the corpus.
#
# WHY 137.50 and 1373/137:
#   unitPrice "137.50" -> 13750 minor units. 100.00 x anything is a multiple of
#   100 minor units and hides truncation/rounding: every product cell and every
#   purchase amount is round, so a port that truncates to whole MNT, rounds half
#   the wrong way, or hardcodes 100.00 is invisible. 137.50 ends in .50, so the
#   purchase total 137 * 137.50 = 18837.50 carries a half-tugrik residue that a
#   whole-tugrik port drops. It is 2dp-exact, so it is vectorable (no sub-minor
#   residue): 137.50 -> 13750 and 18837.50 -> 1883750.
#   totalShares 1373 (issued 1373) -> shareCapital 137.50 * 1373 = 188787.50.
#   requestedShares 137 -> 137 does not divide 1373 (1373 = 137 * 10 + 3), so the
#   account's approved/purchased count is not the product's total either.
#
# Request bodies are byte-stable: every money value is a JSON STRING with the
# exact decimal text ("137.50"); every count is an integer token. Nothing is
# routed through json.dumps of a parsed number, so no 137.50 -> 137.5 drift.
#
# Tenant gerege only, business date 2026-09-03. Additive: re-running against a
# snapshot without the product/account creates them; re-running after only GETs
# the read-backs (name/externalId idempotence).
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh

ohs_ctx shares-nonround-money

PRODUCT_NAME="OHK-Share-Nonround"
PRODUCT_SHORT="OHKN"
ACCOUNT_EXT_ID="OHK-SHARE-ACCT"
CLIENT_ID=6
SAVINGS_ID=2
BIZ_DATE="03 September 2026"

UNIT_PRICE="137.50"
TOTAL_SHARES=1373
SHARES_ISSUED=1373
MIN_SHARES=1
NOMINAL_SHARES=10
MAX_SHARES=2000
REQUESTED_SHARES=137

# --- product (idempotent: keyed on name) --------------------------------------
ohs_get shares-products-list-pre "/products/share"

PRODUCT_ID=$(python3 - "$OHS_OUT/shares-products-list-pre-raw.json" "$PRODUCT_NAME" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(next((p["id"] for p in d.get("pageItems", []) if p.get("name") == sys.argv[2]), ""))
PY
)

if [ -n "$PRODUCT_ID" ]; then
    echo "share product already exists id=$PRODUCT_ID (reused)" >&2
else
    cat > "$OHS_REQ/share-product-create.json" <<EOF
{"name":"$PRODUCT_NAME","shortName":"$PRODUCT_SHORT","description":"OH-SHARES-K non-round money share product","currencyCode":"MNT","digitsAfterDecimal":2,"inMultiplesOf":1,"locale":"en","totalShares":$TOTAL_SHARES,"sharesIssued":$SHARES_ISSUED,"unitPrice":"$UNIT_PRICE","minimumShares":$MIN_SHARES,"nominalShares":$NOMINAL_SHARES,"maximumShares":$MAX_SHARES,"accountingRule":1}
EOF
    ohs_post share-product-create "/products/share" "$OHS_REQ/share-product-create.json"
    PRODUCT_ID=$(ohs_id "$OHS_OUT/share-product-create-raw.json")
    if [ -z "$PRODUCT_ID" ] || [ "$PRODUCT_ID" = "None" ]; then
        echo "share product CREATE FAILED (see out/share-product-create-*.json)" >&2
        exit 1
    fi
fi

# --- account (idempotent: keyed on externalId) --------------------------------
ohs_get shares-accounts-list-pre "/accounts/share?limit=100"

ACCOUNT_ID=$(python3 - "$OHS_OUT/shares-accounts-list-pre-raw.json" "$ACCOUNT_EXT_ID" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(next((a["id"] for a in d.get("pageItems", []) if a.get("externalId") == sys.argv[2]), ""))
PY
)

if [ -n "$ACCOUNT_ID" ]; then
    echo "share account already exists id=$ACCOUNT_ID (reused)" >&2
else
    cat > "$OHS_REQ/share-account-submit.json" <<EOF
{"clientId":$CLIENT_ID,"productId":$PRODUCT_ID,"applicationDate":"$BIZ_DATE","submittedDate":"$BIZ_DATE","externalId":"$ACCOUNT_EXT_ID","requestedShares":$REQUESTED_SHARES,"savingsAccountId":$SAVINGS_ID,"locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post share-account-submit "/accounts/share" "$OHS_REQ/share-account-submit.json"
    ACCOUNT_ID=$(ohs_id "$OHS_OUT/share-account-submit-raw.json")
    if [ -z "$ACCOUNT_ID" ] || [ "$ACCOUNT_ID" = "None" ]; then
        echo "share account SUBMIT FAILED (see out/share-account-submit-*.json)" >&2
        exit 1
    fi

    cat > "$OHS_REQ/share-account-approve.json" <<EOF
{"approvedDate":"$BIZ_DATE","note":"OH-SHARES-K non-round money capture approve","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post share-account-approve "/accounts/share/$ACCOUNT_ID?command=approve" "$OHS_REQ/share-account-approve.json"
fi

# --- activate (idempotent: only while not Active) -----------------------------
# The activate command REFUSES an unsupported `note` parameter
# (error.msg.parameter.unsupported); the seed capture's activate body omits it.
# The refused attempt is preserved under *-refused-note-*.
ohs_get share-account-detail-pre-activate "/accounts/share/$ACCOUNT_ID?associations=all"
ACCOUNT_STATUS=$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("status") or {}).get("id",""))' "$OHS_OUT/share-account-detail-pre-activate-raw.json")
if [ "$ACCOUNT_STATUS" != "300" ]; then
    cat > "$OHS_REQ/share-account-activate.json" <<EOF
{"activatedDate":"$BIZ_DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post share-account-activate "/accounts/share/$ACCOUNT_ID?command=activate" "$OHS_REQ/share-account-activate.json"
fi

# --- read-backs (money variance) ----------------------------------------------
ohs_get share-product-detail "/products/share/$PRODUCT_ID"
ohs_get share-account-detail "/accounts/share/$ACCOUNT_ID?associations=all"
ohs_get shares-products-list-post "/products/share"
ohs_get shares-accounts-list-post "/accounts/share?limit=100"

# --- summary ------------------------------------------------------------------
python3 - "$OHS_OUT" "$PRODUCT_ID" "$ACCOUNT_ID" <<'PY'
import json, os, sys
out = sys.argv[1]

def load(name):
    with open(os.path.join(out, name)) as f:
        return json.load(f)

product = load("share-product-detail-raw.json")
account = load("share-account-detail-raw.json")
purchase = (account.get("purchasedShares") or [{}])[0]

print(json.dumps({
    "product": {
        "id": product.get("id"),
        "name": product.get("name"),
        "unitPrice": product.get("unitPrice"),
        "shareCapital": product.get("shareCapital"),
        "totalShares": product.get("totalShares"),
        "totalSharesIssued": product.get("totalSharesIssued"),
    },
    "account": {
        "id": account.get("id"),
        "externalId": account.get("externalId"),
        "status": (account.get("status") or {}).get("id"),
        "totalApprovedShares": (account.get("summary") or {}).get("totalApprovedShares"),
        "totalPendingForApprovalShares": (account.get("summary") or {}).get("totalPendingForApprovalShares"),
    },
    "purchase": {
        "numberOfShares": purchase.get("numberOfShares"),
        "purchasedPrice": purchase.get("purchasedPrice"),
        "amount": purchase.get("amount"),
        "amountPaid": purchase.get("amountPaid"),
        "status": (purchase.get("status") or {}).get("id"),
        "type": (purchase.get("type") or {}).get("id"),
    },
}, indent=2))
PY
