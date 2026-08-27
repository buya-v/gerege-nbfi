#!/bin/sh
# T51 -- capture the two TO_BE_CAPTURED items that each need ONE additive product, from the
# live reference oracle (Fineract), tenant `gerege`, Path B.
#
# ADDITIVE ONLY.  This script
#   * creates NEW loan products and NEW charge definitions and records every id it creates;
#   * modifies and deletes NO existing m_product_loan, m_charge, m_loan or c_configuration
#     row -- in particular it never writes the tenant rounding mode, which must stay
#     (19, HALF_UP) for the rest of the corpus to remain comparable;
#   * never starts, stops, restarts, re-tenants or reconfigures the shared containers
#     (a sibling worker is running throwaway containers off the same image this fire);
#   * uses only `POST /loans?command=calculateLoanSchedule`, which persists no loan, and
#     asserts m_loan is 0 before AND after.
#
# The T36/T40 preconditions gate runs FIRST -- 21 assertions including the BEHAVIOURAL
# half-cent canary (20925.05; HALF_EVEN would give 20925.04) -- and a breach aborts before
# anything is created or captured.
#
# PostgreSQL is the only engine touched.  "The oracle" here is the Fineract reference
# implementation, never Oracle Database (which is prohibited in this program).
set -eu
. "$(dirname "$0")/lib.sh"

O=$CH/out/t51
mkdir -p "$O"

echo "== T51 capture, tenant gerege =="

sh "$CH/bin/run-preconditions.sh" "$O/preconditions.txt" > /dev/null || {
  echo "ABORT: preconditions breached -- nothing created, nothing captured." >&2
  cat "$O/preconditions.txt" >&2; exit 1; }
grep -q '^ALL PRECONDITIONS HOLD' "$O/preconditions.txt" || {
  echo "ABORT: the preconditions script did not print its PASS line." >&2; exit 1; }
echo "preconditions: ALL PASS (PASS line present)"

# --- state BEFORE, read straight out of PostgreSQL -------------------------------------
docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-before.txt"
echo "BEFORE  m_charge|m_loan|m_product_loan = $(cat "$O/state-before.txt")"
LOANS_BEFORE=$(cut -d'|' -f2 "$O/state-before.txt")
[ "$LOANS_BEFORE" = "0" ] || { echo "ABORT: m_loan is $LOANS_BEFORE, expected 0" >&2; exit 1; }

: > "$O/CREATED-IDS.txt"

# ---------------------------------------------------------------------------------------
# 1. the three NEW products
# ---------------------------------------------------------------------------------------
mkprod() {   # mkprod <payload-stem> -> prints the new product id
  _f=$1
  _code=$(curl -sk -X POST "$B/loanproducts" -H "$A" -H "$T" -H "$CT" \
            -d @"$CH/req/$_f.json" -o "$O/$_f-create.json" -w '%{http_code}')
  echo "  POST /loanproducts  $_f  HTTP $_code  $(cat "$O/$_f-create.json")" >&2
  [ "$_code" = "200" ] || { echo "PRODUCT CREATE FAILED ($_code)" >&2; exit 1; }
  _id=$(sed -n 's/.*"resourceId":\([0-9]*\).*/\1/p' "$O/$_f-create.json")
  echo "product $_f id=$_id" >> "$O/CREATED-IDS.txt"
  printf '%s' "$_id"
}

echo
echo "-- creating the three NEW products (additive; ids recorded) --"
P1=$(mkprod prod-T51-P1-irod-true)
P2=$(mkprod prod-T51-P2-irod-false)
P3=$(mkprod prod-T51-P3-tranche)
echo "  new product ids: P1(irod=true)=$P1  P2(irod=false)=$P2  P3(tranche)=$P3"

# --- read the rows back out of PostgreSQL.  The create response is not evidence. --------
docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select id,short_name,days_in_year_enum,days_in_month_enum,interest_calculated_in_period_enum,loan_schedule_type,interest_recognition_on_disbursement_date,allow_multiple_disbursals,max_disbursals,coalesce(days_in_year_custom_strategy,'NULL') from m_product_loan where id in ($P1,$P2,$P3) order by id;" \
  | tr -d '\r' > "$O/products-readback.txt"
cat "$O/products-readback.txt"

# The whole of item 1 rests on these two rows differing in EXACTLY ONE column.
d=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select count(*) from m_product_loan a join m_product_loan b on b.id=$P2 where a.id=$P1 and a.days_in_year_enum=b.days_in_year_enum and a.days_in_month_enum=b.days_in_month_enum and a.interest_calculated_in_period_enum=b.interest_calculated_in_period_enum and a.loan_schedule_type=b.loan_schedule_type and a.repay_every=b.repay_every and a.repayment_period_frequency_enum=b.repayment_period_frequency_enum and a.number_of_repayments=b.number_of_repayments and a.annual_nominal_interest_rate=b.annual_nominal_interest_rate and a.nominal_interest_rate_per_period=b.nominal_interest_rate_per_period and a.principal_amount=b.principal_amount and a.amortization_method_enum=b.amortization_method_enum and a.interest_method_enum=b.interest_method_enum and a.currency_code=b.currency_code and a.currency_digits=b.currency_digits and coalesce(a.currency_multiplesof,-1)=coalesce(b.currency_multiplesof,-1) and coalesce(a.installment_amount_in_multiples_of,-1)=coalesce(b.installment_amount_in_multiples_of,-1) and coalesce(a.days_in_year_custom_strategy,'x')=coalesce(b.days_in_year_custom_strategy,'x') and a.allow_multiple_disbursals=b.allow_multiple_disbursals and a.allow_partial_period_interest_calcualtion=b.allow_partial_period_interest_calcualtion and a.interest_recognition_on_disbursement_date <> b.interest_recognition_on_disbursement_date;" \
  | tr -d '\r')
[ "$d" = "1" ] || { echo "ABORT: P1 and P2 are not a matched pair differing only in interest_recognition_on_disbursement_date (join returned $d)" >&2; exit 1; }
echo "  P1/P2 matched-pair assertion: PASS (identical on 20 compared columns, differ on interest_recognition_on_disbursement_date)"

# ---------------------------------------------------------------------------------------
# 2. the NEW charge definitions item 2 needs
# ---------------------------------------------------------------------------------------
mkcharge() {   # mkcharge <name> <chargeTimeType> <chargeCalculationType> <amount> <stem>
  _name=$1; _tt=$2; _ct=$3; _amt=$4; _out=$5
  cat > "$O/req-$_out.json" <<EOF
{
 "name": "$_name",
 "chargeAppliesTo": 1,
 "chargeTimeType": $_tt,
 "chargeCalculationType": $_ct,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": $_amt,
 "active": true,
 "penalty": false,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF
  _code=$(curl -sk -X POST "$B/charges" -H "$A" -H "$T" -H "$CT" \
            -d @"$O/req-$_out.json" -o "$O/$_out.json" -w '%{http_code}')
  echo "  POST /charges  $_name  (tt=$_tt ct=$_ct)  HTTP $_code"
  echo "$_out HTTP=$_code $(cat "$O/$_out.json")" >> "$O/CREATED-IDS.txt"
}

echo
echo "-- charge definitions --"
# FLAT at TRANCHE_DISBURSEMENT: the OTHER member of validValuesForTrancheDisbursement()
# [ChargeCalculationType.java:82-84].
mkcharge "T51 flat TRANCHE disbursement" 12 1 7000 create-c1-tt12
# Re-attempt calculation type 5 at a NON-tranche charge time type, so this pass owns its own
# observation of the rejection rather than inheriting T48's.  A rejected POST creates no row.
mkcharge "T51 calc5 at DISBURSEMENT (expected reject)" 1 5 1.2345 create-c5-tt1-reject
mkcharge "T51 calc5 at SPECIFIED_DUE_DATE (expected reject)" 2 5 1.2345 create-c5-tt2-reject
mkcharge "T51 calc5 at INSTALMENT_FEE (expected reject)" 8 5 1.2345 create-c5-tt8-reject

docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select id,name,charge_time_enum,charge_calculation_enum,amount from m_charge where name like 'T51%' order by id;" \
  | tr -d '\r' > "$O/created-charges.txt"
cat "$O/created-charges.txt"
C1_TT12=$(grep '|T51 flat TRANCHE disbursement|' "$O/created-charges.txt" | cut -d'|' -f1)
[ -n "$C1_TT12" ] || { echo "ABORT: the FLAT tranche charge was not created" >&2; exit 1; }
# charge 13 is T48's committed PERCENT_OF_DISBURSEMENT_AMOUNT (ct=5) at TRANCHE_DISBURSEMENT
# (tt=12).  Assert it is still exactly what T48 recorded before leaning on it.
C5=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select id from m_charge where id=13 and charge_time_enum=12 and charge_calculation_enum=5 and amount=1.234500;" | tr -d '\r')
[ "$C5" = "13" ] || { echo "ABORT: charge 13 is not T48's tt=12/ct=5/1.234500 definition" >&2; exit 1; }
echo "  using ct=5 charge id 13 (T48's, unmodified) and ct=1 tranche charge id $C1_TT12"

# ---------------------------------------------------------------------------------------
# 3. fill the templates.  The capture REFUSES to post a payload with a placeholder left in.
# ---------------------------------------------------------------------------------------
fill() {   # fill <stem> <productId> [chargeId]
  _stem=$1; _pid=$2; _cid=${3:-}
  sed "s/\"productId\": 0,/\"productId\": $_pid,/" "$CH/req/calc-T51-$_stem-TEMPLATE.json" > "$CH/req/calc-T51-$4.json"
  if [ -n "$_cid" ]; then
    sed -i '' "s/\"chargeId\": 0,/\"chargeId\": $_cid,/" "$CH/req/calc-T51-$4.json"
  fi
  if grep -q '"productId": 0,' "$CH/req/calc-T51-$4.json" || grep -q '"chargeId": 0,' "$CH/req/calc-T51-$4.json"; then
    echo "ABORT: placeholder left in calc-T51-$4.json" >&2; exit 1
  fi
  echo "  filled calc-T51-$4.json  (productId $_pid${_cid:+, chargeId $_cid})"
}

echo
echo "-- filling templates --"
for s in IROD-AA1 IROD-DEC15 IROD-DEC31 IROD-R13 IROD-NOCROSS IROD-D365; do
  fill "$s" "$P1" "" "${s}-P1"
  fill "$s" "$P2" "" "${s}-P2"
done
fill IROD-AA1-REQTRUE  "$P2" "" IROD-AA1-REQTRUE-P2
fill IROD-AA1-REQFALSE "$P1" "" IROD-AA1-REQFALSE-P1

fill TR-00-ctrl                   "$P3" ""          TR-00-ctrl-P3
fill TR-01-c5-tranche             "$P3" 13          TR-01-c5-tranche-P3
fill TR-02-c2-comparator          "$P3" ""          TR-02-c2-comparator-P3
fill TR-03-c1flat-tranche         "$P3" "$C1_TT12"  TR-03-c1flat-tranche-P3
fill TR-04-c5-onetranche          "$P3" 13          TR-04-c5-onetranche-P3
fill TR-05-c5-nodisbdata          "$P3" 13          TR-05-c5-nodisbdata-P3
# TR-06 already carries productId 1 (the committed single-disbursement comparator), so only
# the chargeId placeholder is filled.
sed "s/\"chargeId\": 0,/\"chargeId\": 13,/" "$CH/req/calc-T51-TR-06-c5-on-singledisb-product-TEMPLATE.json" \
  > "$CH/req/calc-T51-TR-06-c5-on-singledisb-product-P1PROD.json"
grep -q '"chargeId": 0,' "$CH/req/calc-T51-TR-06-c5-on-singledisb-product-P1PROD.json" && {
  echo "ABORT: placeholder left in TR-06" >&2; exit 1; }
echo "  filled calc-T51-TR-06-c5-on-singledisb-product-P1PROD.json (productId 1, chargeId 13)"

# ---------------------------------------------------------------------------------------
# 4. the captures.  A non-200 is itself an observation: the body is kept verbatim.
# ---------------------------------------------------------------------------------------
echo
echo "-- capturing --"
: > "$O/HTTP-CODES.txt"
for f in "$CH"/req/calc-T51-*.json; do
  case "$f" in *TEMPLATE.json) continue;; esac
  n=$(basename "$f" .json); n=${n#calc-}
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$f" -o "$O/$n-raw.json" -w '%{http_code}')
  echo "  $n  HTTP $code"
  echo "$n $code" >> "$O/HTTP-CODES.txt"
done

# ---------------------------------------------------------------------------------------
# 5. state AFTER
# ---------------------------------------------------------------------------------------
echo
docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-after.txt"
echo "AFTER   m_charge|m_loan|m_product_loan = $(cat "$O/state-after.txt")"
LOANS_AFTER=$(cut -d'|' -f2 "$O/state-after.txt")
[ "$LOANS_AFTER" = "0" ] || { echo "BREACH: m_loan is $LOANS_AFTER after the run, expected 0" >&2; exit 1; }

# The tenant arithmetic must be untouched: re-run the behavioural half-cent canary.
sh "$CH/bin/run-preconditions.sh" "$O/preconditions-after.txt" > /dev/null || {
  echo "BREACH: preconditions no longer hold AFTER the run" >&2
  cat "$O/preconditions-after.txt" >&2; exit 1; }
echo "  post-run preconditions: ALL PASS (tenant still at (19, HALF_UP))"

echo
shasum -a 256 "$O"/T51-*-raw.json
