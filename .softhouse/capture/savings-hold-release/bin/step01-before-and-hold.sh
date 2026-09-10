#!/usr/bin/env bash
# step01-before-and-hold.sh — OH-HOLDCAP-R
#
# Phase 1 of a three-point read-back for the CLAUDE.md non-negotiable
#   "Holds are postings and alter `available` only, never posted `balance`."
#
# 1. capture account 1 + its transactions BEFORE any hold
# 2. POST the hold (command=holdAmount)
# 3. capture account 1 + its transactions AFTER the hold
#
# Step 2 (release) is deliberately a separate script so the run can COMMIT
# between the two phases (brief: "commit as you go").
#
# Everything is read/written through the Fineract API and captured with the
# shared ohsweep helpers. SQL below is READ-ONLY evidence.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx savings-hold-release

ACCT=1
# Non-round hold, strictly less than the 1000.31 posted balance.
# 1000.31 - 137.29 = 863.02 -> every cell a whole number of minor units.
HOLD_AMOUNT='137.29'
# Business date is 2026-09-03 (verified via GET /businessdate); the last
# transaction on account 1 is the 2026-09-01 interest posting, so a
# transaction dated at the business date clears the "not before last
# transaction" rule.
TXN_DATE='03 September 2026'

db_snap() {
    local name="$1"
    {
        echo "# OH-HOLDCAP-R read-only DB evidence — phase=$name"
        echo "# captured at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "--- m_savings_account (id=$ACCT) ---"
        docker exec gerege-oracle-db psql -U root -d fineract_gerege -A -F'|' -c \
            "select id, account_balance_derived, total_savings_amount_on_hold from m_savings_account where id=$ACCT;"
        echo "--- m_savings_account_transaction (savings_account_id=$ACCT) ---"
        docker exec gerege-oracle-db psql -U root -d fineract_gerege -A -F'|' -c \
            "select id, transaction_type_enum, amount, running_balance_derived, coalesce(release_id_of_hold_amount,0) as release_id, is_reversed, is_reversal from m_savings_account_transaction where savings_account_id=$ACCT order by id;"
    } > "$OHS_OUT/db-$name.txt"
}

# ---- 1. BEFORE ----------------------------------------------------------
ohs_get savings-hold-before-account       "/savingsaccounts/$ACCT?associations=all"
ohs_get savings-hold-before-transactions  "/savingsaccounts/$ACCT?associations=transactions"
db_snap before

# ---- 2. HOLD ------------------------------------------------------------
# reasonForBlock is REQUIRED by SavingsAccountTransactionDataValidator
# (notBlank, no ignoreIfNull).  All money is a JSON string; no parsed-number
# round trip -> byte-stable under a binary-double round trip.
HOLD_BODY=$(mktemp)
printf '%s' "{\"transactionDate\":\"$TXN_DATE\",\"transactionAmount\":\"$HOLD_AMOUNT\",\"locale\":\"en\",\"dateFormat\":\"dd MMMM yyyy\",\"lienAllowed\":false,\"reasonForBlock\":\"OH-HOLDCAP-R reference-oracle hold/release capture\"}" > "$HOLD_BODY"
ohs_post savings-hold-holdAmount "/savingsaccounts/$ACCT/transactions?command=holdAmount" "$HOLD_BODY"
rm -f "$HOLD_BODY"

# ---- 3. AFTER HOLD ------------------------------------------------------
ohs_get savings-hold-after-hold-account       "/savingsaccounts/$ACCT?associations=all"
ohs_get savings-hold-after-hold-transactions  "/savingsaccounts/$ACCT?associations=transactions"
db_snap after-hold

echo "hold tx id: $(ohs_id "$OHS_OUT/savings-hold-holdAmount-raw.json")"
