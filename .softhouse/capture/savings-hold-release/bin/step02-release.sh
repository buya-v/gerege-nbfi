#!/usr/bin/env bash
# step02-release.sh — OH-HOLDCAP-R
#
# Phase 2: release the hold placed by step01 and capture the third read-back.
#
#   POST /savingsaccounts/{id}/transactions/{holdTxId}?command=releaseAmount
#
# The release endpoint reads the transaction id from the PATH and takes the
# business date as the release date (SavingsAccountTransactionDataValidator
# .validateReleaseAmountAndAssembleForm); the only accepted body field is
# externalId, so the body is the empty JSON object.  Body must be non-blank
# or the validator throws InvalidJsonException.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx savings-hold-release

ACCT=1

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

HOLD_TX_ID=$(ohs_id "$OHS_OUT/savings-hold-holdAmount-raw.json")
if [ -z "$HOLD_TX_ID" ]; then
    echo "step02: no hold transaction id captured; nothing to release" >&2
    exit 1
fi

REL_BODY=$(mktemp)
printf '%s' '{}' > "$REL_BODY"
ohs_post savings-hold-releaseAmount "/savingsaccounts/$ACCT/transactions/$HOLD_TX_ID?command=releaseAmount" "$REL_BODY"
rm -f "$REL_BODY"

ohs_get savings-hold-after-release-account       "/savingsaccounts/$ACCT?associations=all"
ohs_get savings-hold-after-release-transactions  "/savingsaccounts/$ACCT?associations=transactions"
db_snap after-release

echo "release tx id: $(ohs_id "$OHS_OUT/savings-hold-releaseAmount-raw.json")"
