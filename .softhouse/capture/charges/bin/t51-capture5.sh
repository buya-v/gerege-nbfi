#!/bin/sh
# T51 pass 5 -- reach the SECOND reader of the aliased slot for real.
#
# Pass 4 sent allowFullTermForTranche=true on the request and the oracle answered HTTP 400
# "Full term tranche cannot be enabled because the loan product does not allow it", so the
# flag must be on the PRODUCT.  LoanProductDataValidator.java:1093-1102 requires the product
# to be multi-disburse AND PROGRESSIVE for it.  This pass creates ONE more matched pair --
# ACT/ACT + DAILY + multiDisburseLoan + allowFullTermForTranche, differing only in
# interestRecognitionOnDisbursementDate -- and re-runs the crossing shape on both.
#
# ADDITIVE ONLY: two NEW products, ids recorded; no existing row modified; no charge created;
# calculateLoanSchedule only; m_loan asserted 0 before and after.
set -eu
. "$(dirname "$0")/lib.sh"
O=$CH/out/t51
R=$CH/req
P=$(cd "$CH/../pathb/req" && pwd)
mkdir -p "$O"

echo "== T51 capture pass 5 (product-level allowFullTermForTranche), tenant gerege =="
sh "$CH/bin/run-preconditions.sh" "$O/preconditions-pass5.txt" > /dev/null || {
  echo "ABORT: preconditions breached." >&2; exit 1; }
grep -q '^ALL PRECONDITIONS HOLD' "$O/preconditions-pass5.txt" || {
  echo "ABORT: no PASS line." >&2; exit 1; }
echo "preconditions: ALL PASS (PASS line present)"

docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-before-pass5.txt"
echo "BEFORE  m_charge|m_loan|m_product_loan = $(cat "$O/state-before-pass5.txt")"
[ "$(cut -d'|' -f2 "$O/state-before-pass5.txt")" = "0" ] || { echo "ABORT: m_loan is not 0" >&2; exit 1; }

# Derived from the SAME committed product-3 payload as products 17/18, by text substitution
# on named lines only.
for pair in "true:T5D:prod-T51-P4-ftt-irod-true" "false:T5E:prod-T51-P5-ftt-irod-false"; do
  v=${pair%%:*}; rest=${pair#*:}; sn=${rest%%:*}; out=${rest#*:}
  sed -e "s/\"name\": \"PathB DIYCS FULL_LEAP_YEAR\",/\"name\": \"T51 FTT IROD $v\",/" \
      -e "s/\"shortName\": \"PB3\",/\"shortName\": \"$sn\",/" \
      -e "s/\"multiDisburseLoan\": false,/\"multiDisburseLoan\": true,\n \"maxTrancheCount\": 3,\n \"outstandingLoanBalance\": 5000000,\n \"allowFullTermForTranche\": true,/" \
      -e "s/\"daysInYearCustomStrategy\": \"FULL_LEAP_YEAR\"/\"interestRecognitionOnDisbursementDate\": $v/" \
      "$P/product-3-diycs-fullleapyear.json" > "$R/$out.json"
  echo "  built $out.json  ($(diff "$P/product-3-diycs-fullleapyear.json" "$R/$out.json" | grep -c '^[<>]') changed lines)"
done
echo "-- P4 vs P5: the ONLY difference must be name, shortName and the flag --"
diff "$R/prod-T51-P4-ftt-irod-true.json" "$R/prod-T51-P5-ftt-irod-false.json" || true

mkprod() {
  _f=$1
  _code=$(curl -sk -X POST "$B/loanproducts" -H "$A" -H "$T" -H "$CT" \
            -d @"$R/$_f.json" -o "$O/$_f-create.json" -w '%{http_code}')
  echo "  POST /loanproducts  $_f  HTTP $_code  $(cat "$O/$_f-create.json")" >&2
  [ "$_code" = "200" ] || { echo "PRODUCT CREATE FAILED ($_code)" >&2; exit 1; }
  _id=$(sed -n 's/.*"resourceId":\([0-9]*\).*/\1/p' "$O/$_f-create.json")
  echo "product $_f id=$_id" >> "$O/CREATED-IDS.txt"
  printf '%s' "$_id"
}
echo
P4=$(mkprod prod-T51-P4-ftt-irod-true)
P5=$(mkprod prod-T51-P5-ftt-irod-false)
echo "  new product ids: P4(ftt, irod=true)=$P4  P5(ftt, irod=false)=$P5"

docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select p.id,p.short_name,p.days_in_year_enum,p.interest_calculated_in_period_enum,p.loan_schedule_type,p.interest_recognition_on_disbursement_date,p.allow_multiple_disbursals,t.allow_full_term_for_tranche from m_product_loan p left join m_product_loan_tranche_details t on t.id=p.id where p.id in ($P4,$P5) order by p.id;" \
  | tr -d '\r' > "$O/products-readback-pass5.txt" 2>/dev/null || \
docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select id,short_name,days_in_year_enum,interest_calculated_in_period_enum,loan_schedule_type,interest_recognition_on_disbursement_date,allow_multiple_disbursals from m_product_loan where id in ($P4,$P5) order by id;" \
  | tr -d '\r' > "$O/products-readback-pass5.txt"
cat "$O/products-readback-pass5.txt"

mkftt() {   # <stem> <productId>
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
mkftt FTTP-P4 "$P4"
mkftt FTTP-P5 "$P5"

echo
echo "-- capturing pass 5 --"
for n in FTTP-P4 FTTP-P5; do
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$R/calc-T51-$n.json" -o "$O/T51-$n-raw.json" -w '%{http_code}')
  echo "  T51-$n  HTTP $code"
  echo "T51-$n $code" >> "$O/HTTP-CODES.txt"
done

echo
docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-after-pass5.txt"
echo "AFTER   m_charge|m_loan|m_product_loan = $(cat "$O/state-after-pass5.txt")"
[ "$(cut -d'|' -f2 "$O/state-after-pass5.txt")" = "0" ] || { echo "BREACH: m_loan is not 0" >&2; exit 1; }
sh "$CH/bin/run-preconditions.sh" "$O/preconditions-pass5-after.txt" > /dev/null || {
  echo "BREACH: preconditions no longer hold AFTER pass 5" >&2; exit 1; }
echo "  post-run preconditions: ALL PASS"
echo
shasum -a 256 "$O"/T51-FTTP-*-raw.json
