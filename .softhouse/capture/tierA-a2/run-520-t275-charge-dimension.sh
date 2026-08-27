#!/bin/sh
# T275 / GROUP B -- THE THIRD RESOLUTION DIMENSION: charge_id.
#
# CAPTURE-PLAN.md §5 excluded this row with: "feeToIncomeAccountMappings /
# penaltyToIncomeAccountMappings (charge-specific resolution) -- needs an `m_charge`
# fixture; none exists on `gerege`. This is the THIRD resolution dimension (`charge_id`)
# and it is untested here -- the payment-type dimension is captured, the charge dimension
# is not."
#
# THAT EXCLUSION NO LONGER HOLDS, AND THIS RUN MEASURES THAT RATHER THAN ASSERTING IT.
# Step 0 dumps m_charge, m_code, m_code_value and the acc_product_mapping DDL BEFORE any
# probe is sent, so the fixture premise is a committed observation with a timestamp on it
# and not a sentence inherited from an earlier fire. `gerege` carries LOAN charges seeded
# by the T40/T48/T51 Path B fires, penalties among them. Nothing here creates a charge.
#
# WHY THE OVERRIDES POINT AT UNUSUAL ACCOUNTS. The generic slots are incomeFromFee -> GL 9
# and incomeFromPenalty -> GL 10. If a charge override also pointed at GL 9 or GL 10,
# resolution could not be DISTINGUISHED from the fallback -- the capture would be vacuous
# in exactly the P-22 way. So the fee override targets GL 11 (Recoveries) and the penalty
# override targets GL 8 (Interest On Loans). Both are INCOME DETAIL accounts, so a refusal
# cannot be blamed on account type, and both differ from the generic slot they override.
#
# EVERY PROBE IS A QUESTION, NOT AN EXPECTATION. No expected status is written anywhere in
# this script. A 200 and a 403 are recorded identically, and whichever comes back is the
# finding.
#
# Product creation is not a money movement -- no loan, no transaction, no journal entry --
# so cap8.sh (which sends no Idempotency-Key) is the correct instrument.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"
Q="$DIR/capsql.sh"

echo "== T275 group B: the charge_id resolution dimension =="

# --- 0. THE FIXTURE PREMISE, MEASURED. Read this before believing any §5 exclusion.
sh "$Q" A2-520-db-fixtures sql/q9-t275-fixture-state.sql || exit 1

# --- 1. the instrument: a CASH product carrying charge 1 (fee) and charge 6 (penalty),
#        each with an income override that differs from its generic slot.
sh "$C" A2-522-prod-charge-mappings POST /loanproducts req/t275-080-charge-mappings.json || exit 1
cat "$DIR/out/A2-522-prod-charge-mappings.json"; echo

# The readback needs the id the oracle assigned. If the create was REFUSED there is no id,
# and this prints that fact and skips rather than inventing one.
PID=$(python3 -c 'import json,sys,decimal
try:
    print(json.load(open(sys.argv[1]), parse_float=decimal.Decimal).get("resourceId",""))
except Exception:
    print("")' "$DIR/out/A2-522-prod-charge-mappings.json")
echo "observed resourceId = ${PID:-<none: the create was refused, readback SKIPPED, nothing fabricated>}"
if [ -n "$PID" ]; then
  sh "$C" A2-523-prod-charge-mappings-readback GET "/loanproducts/$PID" || exit 1
fi

# --- 2. a fee override naming a charge that is NOT attached to the product.
sh "$C" A2-524-prod-fee-charge-not-attached POST /loanproducts req/t275-081-fee-charge-not-attached.json || exit 1
cat "$DIR/out/A2-524-prod-fee-charge-not-attached.json"; echo

# --- 3. a PENALTY override on a non-penalty charge AND a FEE override on a penalty charge.
sh "$C" A2-525-prod-penalty-mapping-on-fee-charge POST /loanproducts req/t275-082-penalty-mapping-on-fee-charge.json || exit 1
cat "$DIR/out/A2-525-prod-penalty-mapping-on-fee-charge.json"; echo

# --- 4. a fee override pointed at an EXPENSE account. §3 row 9 captured GL-type checking
#        on the generic slots; does it reach the charge-scoped ones?
sh "$C" A2-526-prod-fee-income-expense-account POST /loanproducts req/t275-083-fee-income-expense-account.json || exit 1
cat "$DIR/out/A2-526-prod-fee-income-expense-account.json"; echo

# --- 5. the charge-dimension twin of prod-067-duplicate-channel (§4.1), which the oracle
#        accepted at 200 and which then detonated at resolution.
sh "$C" A2-527-prod-duplicate-fee-charge POST /loanproducts req/t275-084-duplicate-fee-charge.json || exit 1
cat "$DIR/out/A2-527-prod-duplicate-fee-charge.json"; echo

# --- 6. what actually landed in acc_product_mapping. Before this run the corpus had ZERO
#        rows with charge_id NOT NULL, so a charge-scoped row appearing here is itself the
#        proof that the parameter was HONOURED and not silently ignored (A2-bad-053 shows
#        this oracle ignores unknown parameters at HTTP 200, which is what would make a
#        misnamed probe look like an absence of validation).
sh "$Q" A2-528-db-mapping-after-charge-dimension sql/q8-t275-mapping-ids.sql || exit 1

echo "== group B complete =="
