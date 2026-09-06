#!/usr/bin/env bash
# loan context — repayments / waivers / adjustments on the seeded loans, plus a
# NEW discriminating loan whose first interest installment lands on a half minor
# unit so HALF_UP and HALF_EVEN differ. Reads the resulting schedules + read-backs.
#
# Seam under test: loan interest schedule generation.
#   interest(period) = outstanding_principal * rate/year * days/year
#   rate = 12 %/yr, daysInYear = 360, daysInMonth = 30  => 1 % per month
#   principal 100050.50  ->  period-1 interest = 1000.505
#     HALF_UP  -> 1000.51   (100050.50 -> the .505 rounds the 5 up)
#     HALF_EVEN-> 1000.50   (0 in the kept 2nd decimal is even, so 5 stays down)
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh

ohs_ctx loan

CURRENCY="MNT"
LOAN_PRODUCT=2          # SEED-Probe-Loan
CLIENT=9                # SEED-C15 (rounding client, active, reused)
DISCRIM_EXT="SEED-L06"
DISCRIM_PRINCIPAL="100050.50"   # -> period-1 interest 1000.505 (half minor unit tie)
DISCRIM_DATE="01 August 2026"   # disbursed Aug 1 -> first due Sep 1 (business date)

# --- read-backs of the seeded loans -------------------------------------------
ohs_get loans-list        "/loans?limit=50"
for lid in 1 2 3 4 5; do
    ohs_get "loan-$lid-detail"       "/loans/$lid?associations=all"
    ohs_get "loan-$lid-schedule"     "/loans/$lid?associations=repaymentSchedule"
    ohs_get "loan-$lid-transactions" "/loans/$lid/transactions?limit=100"
done

# --- discriminating loan (idempotent: keyed on externalId) ---------------------
existing=$(curl -sk "$OHS_BASE/loans?externalId=$DISCRIM_EXT" -H "$OHS_AUTH" -H "$OHS_TEN" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print([x["id"] for x in d.get("pageItems",[])])')
if [ "$existing" != "[]" ]; then
    DISCRIM_ID=$(echo "$existing" | python3 -c 'import json,sys;print(json.load(sys.stdin)[0])')
    echo "loan $DISCRIM_EXT already exists id=$DISCRIM_ID (reused)" >&2
else
    cat > "$OHS_REQ/loan-L06-submit.json" <<EOF
{
  "clientId": $CLIENT,
  "productId": $LOAN_PRODUCT,
  "externalId": "$DISCRIM_EXT",
  "principal": "$DISCRIM_PRINCIPAL",
  "loanTermFrequency": 12,
  "loanTermFrequencyType": 2,
  "numberOfRepayments": 12,
  "repaymentEvery": 1,
  "repaymentFrequencyType": 2,
  "interestRatePerPeriod": 12,
  "interestRateFrequencyType": 3,
  "amortizationType": 1,
  "interestType": 0,
  "interestCalculationPeriodType": 1,
  "transactionProcessingStrategyCode": "mifos-standard-strategy",
  "loanType": "individual",
  "submittedOnDate": "$DISCRIM_DATE",
  "expectedDisbursementDate": "$DISCRIM_DATE",
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
    ohs_post loan-L06-submit "/loans" "$OHS_REQ/loan-L06-submit.json"
    DISCRIM_ID=$(ohs_id "$OHS_OUT/loan-L06-submit-raw.json")
    if [ -z "$DISCRIM_ID" ]; then
        echo "loan $DISCRIM_EXT SUBMIT FAILED => $(cat "$OHS_OUT/loan-L06-submit-raw.json")" >&2
        exit 1
    fi

    cat > "$OHS_REQ/loan-L06-approve.json" <<EOF
{"approvedOnDate":"$DISCRIM_DATE","expectedDisbursementDate":"$DISCRIM_DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post loan-L06-approve "/loans/$DISCRIM_ID?command=approve" "$OHS_REQ/loan-L06-approve.json"

    cat > "$OHS_REQ/loan-L06-disburse.json" <<EOF
{"actualDisbursementDate":"$DISCRIM_DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
    ohs_post loan-L06-disburse "/loans/$DISCRIM_ID?command=disburse" "$OHS_REQ/loan-L06-disburse.json"
fi

ohs_get loan-L06-detail    "/loans/$DISCRIM_ID?associations=all"
ohs_get loan-L06-schedule  "/loans/$DISCRIM_ID?associations=repaymentSchedule"

# --- repayment on SEED-L03 (first installment exactly due on business date) -----
REPAY_LOAN=3
REPAY_AMOUNT="8884.88"      # period-1 total: principal 7884.88 + interest 1000.00
cat > "$OHS_REQ/repay-L03.json" <<EOF
{"transactionDate":"01 September 2026","transactionAmount":"$REPAY_AMOUNT","note":"SEED repay probe","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
ohs_post repay-L03 "/loans/$REPAY_LOAN/transactions?command=repayment" "$OHS_REQ/repay-L03.json"

# --- waiver on SEED-L01 (waive earliest overdue interest) ----------------------
WAIVE_LOAN=1
WAIVE_AMOUNT="1000.00"
cat > "$OHS_REQ/waive-L01.json" <<EOF
{"transactionDate":"01 September 2026","transactionAmount":"$WAIVE_AMOUNT","note":"SEED waive probe","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
ohs_post waive-L01 "/loans/$WAIVE_LOAN/transactions?command=waiveinterest" "$OHS_REQ/waive-L01.json"

# --- read-backs after the mutations -------------------------------------------
ohs_get loan-3-transactions-after "/loans/$REPAY_LOAN/transactions?limit=100"
ohs_get loan-3-detail-after       "/loans/$REPAY_LOAN?associations=all"
ohs_get loan-1-transactions-after "/loans/$WAIVE_LOAN/transactions?limit=100"
ohs_get loan-1-detail-after       "/loans/$WAIVE_LOAN?associations=all"

# --- MANIFEST --------------------------------------------------------------------
python3 - "$OHS_OUT" "$DISCRIM_ID" <<'PY'
import json, os, sys
out = sys.argv[1]
discrim_id = sys.argv[2]

def txid(name):
    p = os.path.join(out, f"{name}-raw.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    return d.get("resourceId", d.get("loanId", d.get("id")))

manifest = {
    "context": "loan",
    "note": "repayment on SEED-L03, waiveinterest on SEED-L01, plus a discriminating loan SEED-L06 (principal 100050.50) whose period-1 interest ties HALF_UP vs HALF_EVEN.",
    "roundingSurface": {
        "seam": "loan interest schedule generation (1% of declining principal, rounded to 2dp)",
        "discriminatingInput": {"externalId": "SEED-L06", "principal": "100050.50",
                                 "ratePerPeriod": 12, "rateFrequencyType": 3,
                                 "daysInYear": 360, "daysInMonth": 30},
        "rawInterest": "1000.505",
        "HALF_UP": "1000.51",
        "HALF_EVEN": "1000.50",
    },
    "objects": {
        "seededLoans": [{"id": i, "note": "read back only"} for i in (1, 2, 3, 4, 5)],
        "discriminatingLoan": {"id": discrim_id, "externalId": "SEED-L06", "principal": "100050.50"},
        "repayment": {"loanId": 3, "transactionId": txid("repay-L03"), "amount": "8884.88"},
        "waiver": {"loanId": 1, "transactionId": txid("waive-L01"), "amount": "1000.00"},
    },
}
open(os.path.join(out, "..", "MANIFEST.json"), "w").write(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
PY
