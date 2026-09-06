#!/usr/bin/env bash
# savings context — savings products, accounts, deposits, interest posting.
#
# Seam under test: savings daily-balance interest accrual + posting, rounded to
# 2dp (MNT, 2 minor units) at the period boundary.
#   daily_interest = balance * (rate/100) / daysInYear
#   balance 1000 MNT, rate 0.1825 %/yr, daysInYear 365
#     => daily_interest = 0.005 MNT  (exactly half a minor unit)
#     HALF_UP  -> 0.01
#     HALF_EVEN-> 0.00
#
# A daily-posting product makes that single-day tie visible as a posted
# transaction. A monthly-posting product (already seeded by an earlier probe) is
# read back too: its 31-day period is 0.155 -> 0.16 (HALF_UP; HALF_EVEN would
# also give 0.16, so that period alone does NOT discriminate — the daily product
# does).
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh

ohs_ctx savings

CLIENT_MONTHLY=5      # SEED-C11
CLIENT_DAILY=6        # SEED-C12
PRODUCT_MONTHLY=1     # SEED-Savings-Product
PRODUCT_DAILY=3       # SEED-Savings-Product-Daily
DISCRIM_AMOUNT="1000"       # -> daily interest 0.005 (half minor unit)
DAILY_OPEN_DATE="31 August 2026"   # one day before the business date 2026-09-01

# --- products -------------------------------------------------------------------
ohs_get savings-products-list "/savingsproducts"

# --- read-back the monthly account already seeded by the earlier probe ----------
ohs_get savings-account-monthly "/savingsaccounts/1?associations=all"

# --- discriminating daily-posting account (idempotent: keyed on client+product) --
DAILY_ID=$(curl -sk "$OHS_BASE/savingsaccounts?clientId=$CLIENT_DAILY&limit=50" \
    -H "$OHS_AUTH" -H "$OHS_TEN" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next((a["id"] for a in d.get("pageItems",[]) if a.get("savingsProductId")==3), ""))')

if [ -n "$DAILY_ID" ]; then
    echo "savings daily account already exists id=$DAILY_ID (reused)" >&2
else
    cat > "$OHS_REQ/savings-daily-submit.json" <<EOF
{"clientId":$CLIENT_DAILY,"productId":$PRODUCT_DAILY,"submittedOnDate":"$DAILY_OPEN_DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post savings-daily-submit "/savingsaccounts" "$OHS_REQ/savings-daily-submit.json"
    DAILY_ID=$(ohs_id "$OHS_OUT/savings-daily-submit-raw.json")
    if [ -z "$DAILY_ID" ] || [ "$DAILY_ID" = "None" ]; then
        echo "savings daily account SUBMIT FAILED => $(cat "$OHS_OUT/savings-daily-submit-raw.json")" >&2
        exit 1
    fi

    cat > "$OHS_REQ/savings-daily-approve.json" <<EOF
{"approvedOnDate":"$DAILY_OPEN_DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post savings-daily-approve "/savingsaccounts/$DAILY_ID?command=approve" "$OHS_REQ/savings-daily-approve.json"

    cat > "$OHS_REQ/savings-daily-activate.json" <<EOF
{"activatedOnDate":"$DAILY_OPEN_DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post savings-daily-activate "/savingsaccounts/$DAILY_ID?command=activate" "$OHS_REQ/savings-daily-activate.json"

    cat > "$OHS_REQ/savings-daily-deposit.json" <<EOF
{"transactionDate":"$DAILY_OPEN_DATE","transactionAmount":"$DISCRIM_AMOUNT","paymentTypeId":"1","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post savings-daily-deposit "/savingsaccounts/$DAILY_ID/transactions?command=deposit" "$OHS_REQ/savings-daily-deposit.json"
fi

# post interest up to the business date (date comes from the pinned business
# date, never date/now)
printf '{}\n' > "$OHS_REQ/savings-daily-postInterest.json"
ohs_post savings-daily-postInterest "/savingsaccounts/$DAILY_ID?command=postInterest" "$OHS_REQ/savings-daily-postInterest.json"

ohs_get savings-account-daily "/savingsaccounts/$DAILY_ID?associations=all"

# --- MANIFEST --------------------------------------------------------------------
python3 - "$OHS_OUT" "$DAILY_ID" <<'PY'
import json, os, sys
out, daily_id = sys.argv[1], sys.argv[2]

def txid(name):
    p = os.path.join(out, f"{name}-raw.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    return d.get("resourceId", d.get("savingsId", d.get("id")))

# observed daily interest posting amount
obs = None
obs_txid = None
dp = os.path.join(out, "savings-account-daily-raw.json")
if os.path.exists(dp):
    dd = json.load(open(dp))
    interest_tx = [t for t in dd.get("transactions", []) if t.get("transactionType", {}).get("interestPosting")]
    if interest_tx:
        obs = interest_tx[0]["amount"]
        obs_txid = interest_tx[0]["id"]

manifest = {
    "context": "savings",
    "note": "savings products/accounts/deposits/interest posting. Discriminating seam is savings daily-balance interest: 1000 MNT @ 0.1825%/yr over 365-day year gives 0.005 MNT/day (half minor unit).",
    "roundingSurface": {
        "seam": "savings daily-balance interest accrual + posting (rounded to 2dp)",
        "discriminatingInput": {
            "balance": "1000.00",
            "ratePerAnnumPct": "0.1825",
            "interestCalculationDaysInYearType": 365,
            "days": 1,
        },
        "rawDailyInterest": "0.005",
        "HALF_UP": "0.01",
        "HALF_EVEN": "0.00",
        "observedPosted": obs,
        "interestTransactionId": obs_txid,
        "verdict": "HALF_UP" if obs == 0.01 else ("HALF_EVEN" if obs == 0.0 else "unexpected"),
    },
    "objects": {
        "products": [
            {"id": 1, "name": "SEED-Savings-Product", "posting": "monthly"},
            {"id": 3, "name": "SEED-Savings-Product-Daily", "posting": "daily"},
        ],
        "accounts": [
            {"id": 1, "clientId": 5, "productId": 1,
             "note": "monthly posting; deposit 1000, interest postings 0.15 (30d) + 0.16 (31d)"},
            {"id": int(daily_id), "clientId": 6, "productId": 3,
             "note": "daily posting; deposit 1000, single-day interest 0.005 -> 0.01 (HALF_UP)"},
        ],
    },
}
open(os.path.join(out, "..", "MANIFEST.json"), "w").write(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
PY
