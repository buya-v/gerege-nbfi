#!/bin/sh
# T51 pass 4 -- the SECOND reader of the aliased slot.
#
# ProgressiveEMICalculator reads LoanConfigurationDetails.isInterestRecognitionOnDisbursement
# Date() in exactly two places on main sources:
#   * :1579, inside getFractionPeriodDueDateForEndOfYear -- covered by passes 1 and 2;
#   * :194, inside buildLoanApplicationTerms, reached ONLY from addFullTermTrancheDisbursement
#     [:155] which addDisbursement guards with isAllowFullTermForTranche() && numberOfRepayments
#     > 0 && action == DISBURSEMENT [:140-143].
# `allowFullTermForTranche` is a supported calculateLoanSchedule parameter
# [LoanScheduleValidator.java:79], so this pass turns it on and re-runs the crossing shapes on
# the matched product pair.
#
# ADDITIVE ONLY.  Creates nothing: calculateLoanSchedule legs only.
set -eu
. "$(dirname "$0")/lib.sh"
O=$CH/out/t51
R=$CH/req
mkdir -p "$O"

echo "== T51 capture pass 4 (allowFullTermForTranche), tenant gerege =="
sh "$CH/bin/run-preconditions.sh" "$O/preconditions-pass4.txt" > /dev/null || {
  echo "ABORT: preconditions breached." >&2; exit 1; }
grep -q '^ALL PRECONDITIONS HOLD' "$O/preconditions-pass4.txt" || {
  echo "ABORT: no PASS line." >&2; exit 1; }
echo "preconditions: ALL PASS (PASS line present)"

docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-before-pass4.txt"
echo "BEFORE  m_charge|m_loan|m_product_loan = $(cat "$O/state-before-pass4.txt")"

mkftt() {   # <stem> <productId> <allowFullTermForTranche>
  cat > "$R/calc-T51-$1.json" <<EOF
{
 "clientId": 2,
 "productId": $2,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 6,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 6,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 0,
 "allowFullTermForTranche": $3,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 November 2024",
 "submittedOnDate": "01 November 2024",
 "maxOutstandingLoanBalance": 5000000,
 "disbursementData": [
  { "expectedDisbursementDate": "01 November 2024", "principal": 700000 },
  { "expectedDisbursementDate": "01 January 2025", "principal": 500000 } ],
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF
  echo "  wrote calc-T51-$1.json"
}

echo
echo "-- pass-4 fixtures (two tranches, one of them landing ON 01 Jan 2025) --"
mkftt FTT-ON-P1  17 true
mkftt FTT-ON-P2  18 true
mkftt FTT-OFF-P1 17 false
mkftt FTT-OFF-P2 18 false

echo
echo "-- capturing pass 4 --"
for n in FTT-ON-P1 FTT-ON-P2 FTT-OFF-P1 FTT-OFF-P2; do
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$R/calc-T51-$n.json" -o "$O/T51-$n-raw.json" -w '%{http_code}')
  echo "  T51-$n  HTTP $code"
  echo "T51-$n $code" >> "$O/HTTP-CODES.txt"
done

echo
docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-after-pass4.txt"
echo "AFTER   m_charge|m_loan|m_product_loan = $(cat "$O/state-after-pass4.txt")"
[ "$(cat "$O/state-before-pass4.txt")" = "$(cat "$O/state-after-pass4.txt")" ] \
  || { echo "BREACH: pass 4 changed server state; it must create nothing" >&2; exit 1; }
echo "  pass 4 created nothing: before == after"
echo
shasum -a 256 "$O"/T51-FTT-*-raw.json
