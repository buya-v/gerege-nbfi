#!/usr/bin/env bash
# OH-COLL-L — collateral-nonround-money.
#
# The collateral corpus's four seed vectors all reference the SAME entities
# (product 2, client 5, holding 2) and the oracle has exactly ONE collateral
# product, whose money inputs are round (basePrice 100000.00, pctToBase 50.00)
# and whose holding quantity is 1.5. The seed's 50.00 is exactly a /2 shortcut
# and its 100000.00 is exactly a whole-tugrik base price, so a port that
# hardcodes either, or that truncates the scale-5 quantity, passes every vector.
#
# This capture creates ONE product whose money inputs are NON-ROUND and whose
# percentage is NOT 50, links it to a client, and reads the computed valuation
# back. Chosen values (arithmetic worked out BEFORE creating anything):
#
#   basePrice  41850.08   -> not round; ends in .08 so a whole-tugrik or
#                            hardcoded-100000 port loses a non-zero fraction
#   pctToBase  37.5       -> NOT 50, so a /2 shortcut or a hardcoded 50 fails;
#                            also non-integer, so an integer-only per-cent
#                            rendering fails
#   quantity   2.5        -> scale-5, NOT a whole number
#
#   total            = 41850.08 * 2.5      = 104625.20   (2dp, exact)
#   totalCollateral  = 104625.20 * 37.5/100 = 39234.45    (2dp, exact)
#
# Both money cells land on whole minor units: 10462520 and 3923445 (MNT minor
# unit 2), so there is NO sub-minor residue (G-19 / DEC-2 predicate G-08). No
# float is used anywhere: basePrice and pctToBase are sent as exact decimal
# text, quantity 2.5 is binary-exact and byte-stable, and every value in the
# vectors is an integer count.
#
# Re-runnable: the product is keyed on name, the holding on (client, product).
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh

ohs_ctx collateral-nonround-money

PRODUCT_NAME="OHK-Collateral-Nonround"
CLIENT=6                 # SEED-C12, Active status_enum 300 (varies client_id from the seed's 5)

DB() { docker exec gerege-oracle-db psql -U postgres -d fineract_gerege -tA -c "$1"; }
api_get() { curl -sk "$OHS_BASE$1" -H "$OHS_AUTH" -H "$OHS_TEN"; }

# --- collateral product (idempotent by name) ----------------------------------
ohs_get collateral-products-pre "/collateral-management"
PRODUCT_ID=$(api_get "/collateral-management" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next((x["id"] for x in d if x.get("name")==sys.argv[1]),""))' "$PRODUCT_NAME")
if [ -n "$PRODUCT_ID" ]; then
    echo "collateral product '$PRODUCT_NAME' already exists id=$PRODUCT_ID (reused)" >&2
else
    cat > "$OHS_REQ/collateral-product-nonround.json" <<'EOF'
{"name":"OHK-Collateral-Nonround","basePrice":"41850.08","pctToBase":"37.5","unitType":1,"currency":"MNT","quality":"Good","locale":"en"}
EOF
    ohs_post collateral-product-nonround "/collateral-management" "$OHS_REQ/collateral-product-nonround.json"
    PRODUCT_ID=$(ohs_id "$OHS_OUT/collateral-product-nonround-raw.json" 2>/dev/null || true)
fi
if [ -z "${PRODUCT_ID:-}" ]; then
    echo "REFUSED: no product id after POST; status=$(cat "$OHS_OUT/collateral-product-nonround.status" 2>/dev/null)" >&2
    exit 3
fi
echo "PRODUCT_ID=$PRODUCT_ID" >&2

# --- client collateral (idempotent via DB) ------------------------------------
CC_ID=$(DB "SELECT id FROM m_client_collateral_management WHERE client_id=$CLIENT AND collateral_id=$PRODUCT_ID ORDER BY id LIMIT 1;")
if [ -z "$CC_ID" ]; then
    cat > "$OHS_REQ/client-collateral-nonround.json" <<EOF
{"collateralId":$PRODUCT_ID,"quantity":2.5,"description":"OH-COLL-L nonround holding"}
EOF
    ohs_post client-collateral-nonround "/clients/$CLIENT/collaterals" "$OHS_REQ/client-collateral-nonround.json"
    CC_ID=$(ohs_id "$OHS_OUT/client-collateral-nonround-raw.json" 2>/dev/null || true)
else
    echo "client collateral already exists id=$CC_ID (reused)" >&2
fi
if [ -z "${CC_ID:-}" ]; then
    echo "REFUSED: no holding id after POST; status=$(cat "$OHS_OUT/client-collateral-nonround.status" 2>/dev/null)" >&2
    exit 3
fi
echo "CC_ID=$CC_ID" >&2

# --- read-backs ---------------------------------------------------------------
ohs_get client-collateral-page-post        "/clients/$CLIENT/collaterals"
ohs_get client-collateral-single-nonround  "/clients/$CLIENT/collaterals/$CC_ID"
ohs_get collateral-product-nonround-readback "/collateral-management/$PRODUCT_ID"
ohs_get collateral-products-post            "/collateral-management"
