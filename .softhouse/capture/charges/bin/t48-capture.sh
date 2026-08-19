#!/bin/sh
# T48 -- close the cheap charge gaps T46 left open.  Tenant `gerege`, Path B.
#
# ADDITIVE ONLY.  This script:
#   * modifies NO existing charge definition and deletes none (T40's ids 1-12 stay exactly
#     as they are);
#   * creates NEW charge definitions only, and records every id it creates in
#     out/t48/CREATED-IDS.txt;
#   * never restarts, re-tenants, drops or truncates anything, and never writes tenant
#     configuration -- which is precisely why N46-1 (the AMBIENT charge rounding mode) is
#     NOT attempted here: separating it needs a tenant write on the SHARED server.
#   * uses only `POST /loans?command=calculateLoanSchedule`, which persists nothing
#     (`m_loan` was 0 before this run and must be 0 after; the script asserts it).
#
# The T36/T40 preconditions gate runs FIRST -- 21 assertions including the BEHAVIOURAL
# half-cent canary -- and a breach aborts before anything is created or captured.
#
# PostgreSQL is the only engine touched.  "The oracle" is the Fineract reference
# implementation, never Oracle Database.
set -eu
. "$(dirname "$0")/lib.sh"

O=$CH/out/t48
mkdir -p "$O"

echo "== T48 charge-gap capture, tenant gerege =="

sh "$CH/bin/run-preconditions.sh" "$O/preconditions.txt" > /dev/null || {
  echo "ABORT: preconditions breached -- nothing created, nothing captured." >&2; exit 1; }
echo "preconditions: ALL PASS"

# --- state BEFORE, read straight out of PostgreSQL -------------------------------------
docker exec fineract-db-1 psql -U root -d fineract_gerege -At \
  -c "select 'm_charge', count(*) from m_charge union all select 'm_product_loan', count(*) from m_product_loan union all select 'm_loan', count(*) from m_loan;" \
  > "$O/state-before.txt"
cat "$O/state-before.txt"
LOANS_BEFORE=$(grep '^m_loan|' "$O/state-before.txt" | cut -d'|' -f2)
[ "$LOANS_BEFORE" = "0" ] || { echo "ABORT: m_loan is $LOANS_BEFORE, expected 0" >&2; exit 1; }

# ---------------------------------------------------------------------------------------
# 1. NEW charge definitions -- chargeCalculationType 5, and the invalid 9
# ---------------------------------------------------------------------------------------
: > "$O/CREATED-IDS.txt"

mkcharge() {
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
  printf '%s' "$_code"
}

echo
echo "-- creating NEW charge definitions (additive; ids recorded) --"
# chargeCalculationType 5 = PERCENT_OF_DISBURSEMENT_AMOUNT [ChargeCalculationType.java:30].
# ChargeCalculationType.validValuesForLoan() [:60-64] LISTS 5 and the deserializer accepts it
# at :176-179 -- and then performChargeTimeNCalculationTypeValidation
# [ChargeDefinitionCommandFromApiJsonDeserializer.java:482-496] rejects it for EVERY
# chargeTimeType except TRANCHE_DISBURSEMENT (12) at :492-495.  All four legs are attempted
# and whatever the oracle answers is the observation, rejection included.
mkcharge "T48 percent of disbursement amount at disbursement" 1 5 1.2345 create-c5-tt1 > /dev/null
mkcharge "T48 percent of disbursement amount on specified due date" 2 5 1.2345 create-c5-tt2 > /dev/null
mkcharge "T48 percent of disbursement amount per instalment" 8 5 1.2345 create-c5-tt8 > /dev/null
mkcharge "T48 percent of disbursement amount TRANCHE" 12 5 1.2345 create-c5-tt12 > /dev/null
# chargeCalculationType 9 is OUT OF RANGE -- ChargeCalculationType tops out at 5
# [ChargeCalculationType.java:25-30].  Whatever comes back is the observation, including a
# rejection; the body is kept verbatim.
mkcharge "T48 INVALID calculation type 9" 1 9 1.2345 create-c9-invalid > /dev/null
# chargeTimeType 9 = OVERDUE_INSTALLMENT [ChargeTimeType.java:34] -- recorded for the same
# reason: T46 listed "chargeCalculationType 5 and 9" and 9 is not a calculation type at all,
# so both readings of "9" are exercised rather than guessed at.
mkcharge "T48 flat OVERDUE_INSTALLMENT (chargeTimeType 9)" 9 1 1200 create-tt9-overdue > /dev/null

cat "$O/CREATED-IDS.txt"

# --- resolve the ids the oracle actually assigned, from PostgreSQL ---------------------
docker exec fineract-db-1 psql -U root -d fineract_gerege -At \
  -c "select id,name,charge_time_enum,charge_calculation_enum,amount from m_charge where name like 'T48%' order by id;" \
  > "$O/created-charges.txt"
cat "$O/created-charges.txt"

C5_TT1=$(grep '|T48 percent of disbursement amount at disbursement|' "$O/created-charges.txt" | cut -d'|' -f1)
C5_TT2=$(grep '|T48 percent of disbursement amount on specified due date|' "$O/created-charges.txt" | cut -d'|' -f1)
C5_TT8=$(grep '|T48 percent of disbursement amount per instalment|' "$O/created-charges.txt" | cut -d'|' -f1)
C5_TT12=$(grep '|T48 percent of disbursement amount TRANCHE|' "$O/created-charges.txt" | cut -d'|' -f1)

# Whichever calc-type-5 legs the oracle REFUSED are themselves the observation for gap 2.
C5_ANY=${C5_TT1:-}
[ -n "$C5_ANY" ] || C5_ANY=${C5_TT2:-}
[ -n "$C5_ANY" ] || C5_ANY=${C5_TT8:-}
[ -n "$C5_ANY" ] || C5_ANY=${C5_TT12:-}
if [ -z "$C5_ANY" ]; then
  echo "OBSERVED: the oracle created NO chargeCalculationType 5 definition on any chargeTimeType."
  echo "  gap 2 is answered by the rejection bodies in $O/create-c5-*.json; the calc legs are skipped."
  SKIP_C5=1
else
  SKIP_C5=0
fi

# --- fill the templates.  The capture refuses to post a placeholder id. -----------------
fill() {
  sed "s/\"chargeId\": 0/\"chargeId\": $2/" "$CH/req/$1-TEMPLATE.json" > "$CH/req/$1.json"
  grep -q '"chargeId": 0' "$CH/req/$1.json" && { echo "ABORT: placeholder id left in $1" >&2; exit 1; }
  echo "  filled $1.json with chargeId $2"
}
if [ "$SKIP_C5" = "0" ]; then
  fill calc-T48-CH-10-calc5-disbursement   "${C5_TT1:-$C5_ANY}"
  fill calc-T48-CH-11-calc5-specifieddue   "${C5_TT2:-$C5_ANY}"
  fill calc-T48-CH-12-calc5-instalment     "${C5_TT8:-$C5_ANY}"
  fill calc-T48-CH-13-calc5-omitted        "$C5_ANY"
fi

# ---------------------------------------------------------------------------------------
# 2. the captures
# ---------------------------------------------------------------------------------------
echo
echo "-- capturing --"
for f in "$CH"/req/calc-T48-CH-*.json; do
  case "$f" in *TEMPLATE.json) continue;; esac
  n=$(basename "$f" .json); n=${n#calc-}
  # a non-200 is itself an observation for this pass, so record the body and the code and
  # keep going rather than aborting -- but say so loudly.
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$f" -o "$O/$n-raw.json" -w '%{http_code}')
  echo "  $n  HTTP $code"
  echo "$n $code" >> "$O/HTTP-CODES.txt"
done

# --- state AFTER: the endpoint must have persisted no loan -----------------------------
echo
docker exec fineract-db-1 psql -U root -d fineract_gerege -At \
  -c "select 'm_charge', count(*) from m_charge union all select 'm_product_loan', count(*) from m_product_loan union all select 'm_loan', count(*) from m_loan;" \
  > "$O/state-after.txt"
cat "$O/state-after.txt"
LOANS_AFTER=$(grep '^m_loan|' "$O/state-after.txt" | cut -d'|' -f2)
[ "$LOANS_AFTER" = "0" ] || { echo "BREACH: m_loan is $LOANS_AFTER after the run, expected 0" >&2; exit 1; }
PRODUCTS_AFTER=$(grep '^m_product_loan|' "$O/state-after.txt" | cut -d'|' -f2)
[ "$PRODUCTS_AFTER" = "16" ] || { echo "BREACH: m_product_loan is $PRODUCTS_AFTER, expected 16 (T48 creates no product)" >&2; exit 1; }
echo "  ok  no loan persisted; no product created; only NEW charge ids added"

echo
shasum -a 256 "$O"/T48-CH-*-raw.json
