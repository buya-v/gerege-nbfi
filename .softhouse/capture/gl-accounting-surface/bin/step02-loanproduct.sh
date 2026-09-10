#!/usr/bin/env bash
# STEP 2 — create a NEW loan product with accounting ENABLED.
#
# CHOICE: accountingRule = 3, ACCRUAL_PERIODIC. Recorded reason (one line): it is
# the richer observable stream — it posts the disbursement pair AND receivable/
# income accruals AND receivable settlements on repayment, so it exercises the
# three receivable slots and the income slots that CASH (2) never writes
# [apishape.go:133-138, the CASH arm writes no receivable/income slot]. REJECTED:
# CASH (2), which posts only on cash movement and would leave interest-on-loans,
# the three receivables and income-from-recovery unreachable.
source "$(dirname "$0")/common.sh"

glcid() {
  python3 - "$STATE" "$1" <<'PY'
import json,sys
s=json.load(open(sys.argv[1]))
print(s['gl'][sys.argv[2]]['id'])
PY
}

LP_NAME="OHLGR-Accrual-Loan"
existing=$(api_get "/loanproducts" | python3 -c "import json,sys; d=json.load(sys.stdin); print([p['id'] for p in d if p.get('name')=='$LP_NAME'])")
if [ "$existing" != "[]" ]; then
  id=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
  echo "product already exists id=$id (reused)"
  state_set loanProduct "$id"
  cat "$STATE"; exit 0
fi

cat > "$REQ/loanproduct-ohglr.json" <<EOF
{
  "name": "$LP_NAME",
  "shortName": "OGLR",
  "description": "OH-GLR accrual-enabled probe loan (accountingRule 3)",
  "currencyCode": "MNT",
  "digitsAfterDecimal": 2,
  "inMultiplesOf": 0,
  "principal": 100000,
  "numberOfRepayments": 12,
  "repaymentEvery": 1,
  "repaymentFrequencyType": 2,
  "interestRatePerPeriod": 12,
  "interestRateFrequencyType": 3,
  "amortizationType": 1,
  "interestType": 0,
  "interestCalculationPeriodType": 1,
  "transactionProcessingStrategyCode": "mifos-standard-strategy",
  "accountingRule": 3,
  "daysInMonthType": 1,
  "daysInYearType": 1,
  "isInterestRecalculationEnabled": false,
  "locale": "en",
  "dateFormat": "dd MMMM yyyy",
  "fundSourceAccountId": $(glcid OHLGR-20010),
  "loanPortfolioAccountId": $(glcid OHLGR-10010),
  "transfersInSuspenseAccountId": $(glcid OHLGR-10011),
  "receivableInterestAccountId": $(glcid OHLGR-10012),
  "receivableFeeAccountId": $(glcid OHLGR-10013),
  "receivablePenaltyAccountId": $(glcid OHLGR-10014),
  "interestOnLoanAccountId": $(glcid OHLGR-40010),
  "incomeFromFeeAccountId": $(glcid OHLGR-40011),
  "incomeFromPenaltyAccountId": $(glcid OHLGR-40012),
  "incomeFromRecoveryAccountId": $(glcid OHLGR-40013),
  "writeOffAccountId": $(glcid OHLGR-50010),
  "overpaymentLiabilityAccountId": $(glcid OHLGR-20011)
}
EOF

api_post "/loanproducts" "$REQ/loanproduct-ohglr.json" > "$OUT/loanproduct-ohglr-raw.json"
cat "$OUT/loanproduct-ohglr-raw.json"
id=$(python3 -c "import json;print(json.load(open('$OUT/loanproduct-ohglr-raw.json')).get('resourceId',''))")
state_set loanProduct "$id"
echo
echo "product id=$id"
