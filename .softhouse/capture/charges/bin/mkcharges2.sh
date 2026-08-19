#!/bin/sh
# T40 pass 2 — two more charge definitions, on the SEPARATED code path.
#
# ProgressiveLoanScheduleGenerator.separateTotalCompoundingPercentageCharges (:492-505)
# pulls SPECIFIED_DUE_DATE charges whose calculation is PERCENT_OF_INTEREST or
# PERCENT_OF_AMOUNT_AND_INTEREST out of the main loop and applies them afterwards in
# updatePeriodsWithCharges (:470-489) — which, unlike applyChargesForCurrentPeriod
# (:367-382), DOES call addTotalRepaymentExpected (:486).  Pass 1 never touched that
# path.  These two charges exercise it.
set -eu
R="${T40_WORKTREE:-$(cd "$(dirname "$0")/../../../.." && pwd)}/.softhouse/capture/charges/req"

cat > "$R/charge-11-pctinterest-specifieddue.json" <<'EOF'
{
 "name": "T40 percent of interest on specified due date",
 "chargeAppliesTo": 1,
 "chargeTimeType": 2,
 "chargeCalculationType": 4,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 3.75,
 "penalty": false,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

cat > "$R/charge-12-pctamountinterest-specifieddue.json" <<'EOF'
{
 "name": "T40 percent of amount plus interest on specified due date",
 "chargeAppliesTo": 1,
 "chargeTimeType": 2,
 "chargeCalculationType": 3,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 1.2345,
 "penalty": false,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

ls -1 "$R"/charge-1[12]-*.json
