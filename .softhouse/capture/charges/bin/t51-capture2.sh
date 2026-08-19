#!/bin/sh
# T51 pass 2 -- the SEPARATING shapes pass 1 showed were missing.
#
# Pass 1 found that chargeCalculationType 5 with THREE genuine tranches on a real
# multi-disbursement product is byte-identical to chargeCalculationType 2 (0 of 302 cells).
# LoanChargeAssembler.java:190-204 creates ONE LoanCharge PER tranche for chargeTimeType 12,
# each with loanPrincipal = that tranche's principal, so the per-tranche reading and the
# whole-principal reading differ only in ways LINEARITY hides:  SUM(p x t_i) = p x SUM(t_i),
# and the tranches sum to the principal.  Two ways to break the linearity:
#   (a) make SUM(tranches) != principal;
#   (b) put a minCap / maxCap on the charge -- LoanChargeService.java:527-528 copies them from
#       the definition onto EACH LoanCharge and LoanCharge.minimumAndMaximumCap [:326-350]
#       clamps each one separately.  A clamp is not linear.
# (b) is also T44/T46/T48's open minCap/maxCap gap, so item 3 rides along with item 2.
#
# Item 1 gains one more direction (non-leap -> leap), and item 3 adds fixedLength.
#
# ADDITIVE ONLY, same rules as pass 1: new charge ids only, no product created here, no
# existing row modified, no tenant configuration written, no container touched,
# calculateLoanSchedule only, m_loan asserted 0 before and after.
set -eu
. "$(dirname "$0")/lib.sh"

O=$CH/out/t51
mkdir -p "$O"

echo "== T51 capture pass 2, tenant gerege =="
sh "$CH/bin/run-preconditions.sh" "$O/preconditions-pass2.txt" > /dev/null || {
  echo "ABORT: preconditions breached." >&2; cat "$O/preconditions-pass2.txt" >&2; exit 1; }
grep -q '^ALL PRECONDITIONS HOLD' "$O/preconditions-pass2.txt" || {
  echo "ABORT: the preconditions script did not print its PASS line." >&2; exit 1; }
echo "preconditions: ALL PASS (PASS line present)"

docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-before-pass2.txt"
echo "BEFORE  m_charge|m_loan|m_product_loan = $(cat "$O/state-before-pass2.txt")"
[ "$(cut -d'|' -f2 "$O/state-before-pass2.txt")" = "0" ] || { echo "ABORT: m_loan is not 0" >&2; exit 1; }

# ---------------------------------------------------------------- capped charge definitions
mkcappedcharge() {   # <name> <tt> <ct> <amount> <capParam> <capValue> <stem>
  _name=$1; _tt=$2; _ct=$3; _amt=$4; _cp=$5; _cv=$6; _out=$7
  cat > "$O/req-$_out.json" <<EOF
{
 "name": "$_name",
 "chargeAppliesTo": 1,
 "chargeTimeType": $_tt,
 "chargeCalculationType": $_ct,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": $_amt,
 "$_cp": $_cv,
 "active": true,
 "penalty": false,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF
  _code=$(curl -sk -X POST "$B/charges" -H "$A" -H "$T" -H "$CT" \
            -d @"$O/req-$_out.json" -o "$O/$_out.json" -w '%{http_code}')
  echo "  POST /charges  $_name  (tt=$_tt ct=$_ct $_cp=$_cv)  HTTP $_code  $(cat "$O/$_out.json")"
  echo "$_out HTTP=$_code $(cat "$O/$_out.json")" >> "$O/CREATED-IDS.txt"
}

echo
echo "-- capped charge definitions (minCap / maxCap: T44/T46/T48's open gap) --"
# 1.2345 % of 500,000 / 300,000 / 400,000 is 6172.5 / 3703.5 / 4938.  A maxCap of 5000 clamps
# only the FIRST tranche if the cap is per-tranche, and clamps the whole 14814 to 5000 if it
# is applied once to the loan principal.  The two readings are 13641.5 and 5000.
mkcappedcharge "T51 pct of disbursement TRANCHE maxCap5000" 12 5 1.2345 maxCap 5000 create-c5-maxcap
mkcappedcharge "T51 pct of amount DISB maxCap5000"          1  2 1.2345 maxCap 5000 create-c2-maxcap
# 0.1 % of each tranche is 500 / 300 / 400; a minCap of 8000 lifts each to 8000 (24000 total)
# if per-tranche, and lifts the single 1200 to 8000 if applied once.
mkcappedcharge "T51 pct of disbursement TRANCHE minCap8000" 12 5 0.1 minCap 8000 create-c5-mincap
mkcappedcharge "T51 pct of amount DISB minCap8000"          1  2 0.1 minCap 8000 create-c2-mincap

docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select id,name,charge_time_enum,charge_calculation_enum,amount,min_cap,max_cap from m_charge where name like 'T51%' order by id;" \
  | tr -d '\r' > "$O/created-charges-pass2.txt"
cat "$O/created-charges-pass2.txt"

id_of() { grep "|$1|" "$O/created-charges-pass2.txt" | cut -d'|' -f1; }
C5MAX=$(id_of "T51 pct of disbursement TRANCHE maxCap5000")
C2MAX=$(id_of "T51 pct of amount DISB maxCap5000")
C5MIN=$(id_of "T51 pct of disbursement TRANCHE minCap8000")
C2MIN=$(id_of "T51 pct of amount DISB minCap8000")
for v in "$C5MAX" "$C2MAX" "$C5MIN" "$C2MIN"; do
  [ -n "$v" ] || { echo "ABORT: a capped charge was not created; see $O/created-charges-pass2.txt" >&2; exit 1; }
done
echo "  capped charge ids: c5/maxCap=$C5MAX  c2/maxCap=$C2MAX  c5/minCap=$C5MIN  c2/minCap=$C2MIN"

# ---------------------------------------------------------------- pass-2 request fixtures
P3=19    # `T51 tranche multidisburse`, created and recorded in pass 1
R=$CH/req

# TR-07 / TR-08 -- tranches summing to 1,000,000 while `principal` stays 1,200,000.
# 1.2345 % of 1,000,000 = 12345 ; 1.2345 % of 1,200,000 = 14814.
mktr() {   # <stem> <chargeId> <tranche-json-block>
  cat > "$R/calc-T51-$1.json" <<EOF
{
 "clientId": 1,
 "productId": $P3,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 12,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 12,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "maxOutstandingLoanBalance": 5000000,
 "disbursementData": [
$3 ],
 "charges": [
  { "chargeId": $2, "amount": $4 } ],
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF
  echo "  wrote calc-T51-$1.json"
}

EVEN='  { "expectedDisbursementDate": "01 January 2026", "principal": 500000 },
  { "expectedDisbursementDate": "01 March 2026", "principal": 300000 },
  { "expectedDisbursementDate": "01 June 2026", "principal": 400000 }'
SHORT='  { "expectedDisbursementDate": "01 January 2026", "principal": 400000 },
  { "expectedDisbursementDate": "01 March 2026", "principal": 300000 },
  { "expectedDisbursementDate": "01 June 2026", "principal": 300000 }'

echo
echo "-- pass-2 fixtures --"
mktr TR-07-c5-tranches-sum-1000000 13       "$SHORT" 1.2345
mktr TR-08-c2-tranches-sum-1000000 3        "$SHORT" 1.2345
mktr TR-09-c5-maxcap               "$C5MAX" "$EVEN"  1.2345
mktr TR-10-c2-maxcap               "$C2MAX" "$EVEN"  1.2345
mktr TR-11-c5-mincap               "$C5MIN" "$EVEN"  0.1
mktr TR-12-c2-mincap               "$C2MIN" "$EVEN"  0.1

# TR-13 -- the capped ct=5 charge on a SINGLE tranche of the whole principal: 1.2345 % of
# 1,200,000 = 14814, clamped to 5000 by either reading.  Isolates "the cap works" from
# "the cap is applied per tranche".
mktr TR-13-c5-maxcap-onetranche "$C5MAX" \
  '  { "expectedDisbursementDate": "01 January 2026", "principal": 1200000 }' 1.2345

# ---------------------------------------------------------------- item 1, the other direction
# NL2L -- disbursed 15 Dec 2023: the crossing period runs from a 365-day year INTO a 366-day
# year, the opposite of every crossing shape in pass 1.
for pid in 17 18; do
  case $pid in 17) tag=P1;; 18) tag=P2;; esac
  cat > "$R/calc-T51-IROD-NL2L-$tag.json" <<EOF
{
 "clientId": 2,
 "productId": $pid,
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
 "expectedDisbursementDate": "15 December 2023",
 "submittedOnDate": "15 December 2023",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF
  echo "  wrote calc-T51-IROD-NL2L-$tag.json"
done

# ---------------------------------------------------------------- item 3, fixedLength
# LoanProductConstants.FIXED_LENGTH is a supported calculateLoanSchedule parameter
# [LoanScheduleValidator.java:77] and has been on the unchanged-gap list since T44.
for fl in 6 12 18; do
  cat > "$R/calc-T51-FL-$fl.json" <<EOF
{
 "clientId": 1,
 "productId": 1,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 12,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 12,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
 "fixedLength": $fl,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF
  echo "  wrote calc-T51-FL-$fl.json"
done

# ---------------------------------------------------------------- capture
echo
echo "-- capturing pass 2 --"
for n in TR-07-c5-tranches-sum-1000000 TR-08-c2-tranches-sum-1000000 \
         TR-09-c5-maxcap TR-10-c2-maxcap TR-11-c5-mincap TR-12-c2-mincap \
         TR-13-c5-maxcap-onetranche \
         IROD-NL2L-P1 IROD-NL2L-P2 FL-6 FL-12 FL-18; do
  f=$R/calc-T51-$n.json
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$f" -o "$O/T51-$n-raw.json" -w '%{http_code}')
  echo "  T51-$n  HTTP $code"
  echo "T51-$n $code" >> "$O/HTTP-CODES.txt"
done

echo
docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-after-pass2.txt"
echo "AFTER   m_charge|m_loan|m_product_loan = $(cat "$O/state-after-pass2.txt")"
[ "$(cut -d'|' -f2 "$O/state-after-pass2.txt")" = "0" ] || { echo "BREACH: m_loan is not 0 after the run" >&2; exit 1; }
sh "$CH/bin/run-preconditions.sh" "$O/preconditions-pass2-after.txt" > /dev/null || {
  echo "BREACH: preconditions no longer hold AFTER pass 2" >&2; exit 1; }
echo "  post-run preconditions: ALL PASS (tenant still at (19, HALF_UP))"
