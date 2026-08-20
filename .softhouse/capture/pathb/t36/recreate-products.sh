#!/bin/sh
# T36 — second arm of T22 P0-6: RE-CREATE the four loan products and re-issue the four
# loan applications on the production-settings tenant, so the re-capture does not lean on
# product rows another task created.
#
# Products 1-4 in `gerege` were created by T22's fresh-tenant.sh from the committed
# payloads.  Reusing them lets the calc requests go byte-verbatim (productId 1..4), which
# is the cleanest reproduction — but it is T22's fixture, not this run's.  This script
# creates a SECOND, T36-owned set from the same payloads and captures against it.
#
# Only two fields are changed, and by TEXT substitution on those lines alone, so every
# numeric literal in the payload is byte-identical: `name` and `shortName` must be unique
# per tenant (Fineract rejects a duplicate short name).  `productId` in the calc request
# is likewise substituted textually.  No JSON round-trip: re-serialising through a parser
# risks turning a money literal into a binary float, which CLAUDE.md forbids.
#
# Additive only: new product rows in an existing tenant.  No restart, no drop, no config change.
set -eu
D=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$D/.." && pwd)
O=$D/out/recreate-gerege
REQ=$D/req-recreate
mkdir -p "$O" "$REQ"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

echo "### preconditions"
# T99 (sweep for the F-3 shape — a guard that cannot fail).  Same defect T77 found and T80 fixed in
# recapture.sh, still live here: the redirect captured STDOUT ONLY while preconditions.sh's bad()
# writes every FAIL to STDERR (preconditions.sh:58), so `^  FAIL` could never appear in the file
# being grepped and the ABORT was unreachable; the `grep -c … > /dev/null 2>&1 || true` line above
# it computed a count and threw it away; and the exit status the script actually emits was ignored.
# Two operands now — the EXIT STATUS, and a FAIL grep over a transcript holding BOTH streams —
# either of which aborts.  LC_ALL=C: a BSD grep in a UTF-8 locale returns 0 lines AND 0 on a file
# with an invalid multibyte sequence, which is the silent zero this gate exists to stop.
prestatus=0
CANARY_REQ="$W/t22-audit/req/calc-pmode2-gerege.json" \
  sh "$D/preconditions.sh" gerege > "$O/preconditions.txt" 2>&1 || prestatus=$?
prefails=$(LC_ALL=C grep -ac '^  FAIL' "$O/preconditions.txt" || true)
if [ "$prestatus" -ne 0 ] || [ "$prefails" != "0" ]; then
  echo "ABORT: preconditions breached — exit status $prestatus, $prefails FAIL line(s). NOTHING WAS CAPTURED." >&2
  cat "$O/preconditions.txt" >&2
  exit 1
fi
echo "ALL PASS"

echo
echo "### build T36-owned product payloads (name/shortName only)"
sed -e 's/"name": "PathB Progressive MNT",/"name": "T36 recreate baseline",/' \
    -e 's/"shortName": "PBM1",/"shortName": "T61",/' \
    "$W/req/product-1-baseline.json" > "$REQ/product-1-baseline.json"
sed -e 's/"name": "PathB Progressive MNT mult100",/"name": "T36 recreate mult100",/' \
    -e 's/"shortName": "PBM2",/"shortName": "T62",/' \
    "$W/req/product-2-multiplesof100.json" > "$REQ/product-2-multiplesof100.json"
sed -e 's/"name": "PathB DIYCS FULL_LEAP_YEAR",/"name": "T36 recreate FULL_LEAP_YEAR",/' \
    -e 's/"shortName": "PB3",/"shortName": "T63",/' \
    "$W/req/product-3-diycs-fullleapyear.json" > "$REQ/product-3-diycs-fullleapyear.json"
sed -e 's/"name": "PathB DIYCS FEB_29_PERIOD_ONLY",/"name": "T36 recreate FEB_29_PERIOD_ONLY",/' \
    -e 's/"shortName": "PB4",/"shortName": "T64",/' \
    "$W/req/product-4-diycs-feb29only.json" > "$REQ/product-4-diycs-feb29only.json"

# Everything except those two lines must be byte-identical to the committed payload.
for f in product-1-baseline product-2-multiplesof100 product-3-diycs-fullleapyear product-4-diycs-feb29only; do
  n=$(diff "$W/req/$f.json" "$REQ/$f.json" | grep -c '^[<>]' || true)
  echo "  $f: $n changed lines (must be 4 = 2 removed + 2 added)"
  [ "$n" = "4" ] || { echo "UNEXPECTED PAYLOAD DRIFT in $f" >&2; exit 1; }
done

echo
echo "### create the products"
for f in product-1-baseline product-2-multiplesof100 product-3-diycs-fullleapyear product-4-diycs-feb29only; do
  code=$(curl -sk -X POST "$B/loanproducts" -H "$A" -H "$T" -H "$CT" -d @"$REQ/$f.json" \
              -o "$O/$f-create.json" -w '%{http_code}')
  echo "  $f  HTTP $code  $(cat "$O/$f-create.json")"
  [ "$code" = "200" ] || { echo "PRODUCT CREATE FAILED ($code)" >&2; exit 1; }
done

P1=$(sed -n 's/.*"resourceId":\([0-9]*\).*/\1/p' "$O/product-1-baseline-create.json")
P2=$(sed -n 's/.*"resourceId":\([0-9]*\).*/\1/p' "$O/product-2-multiplesof100-create.json")
P3=$(sed -n 's/.*"resourceId":\([0-9]*\).*/\1/p' "$O/product-3-diycs-fullleapyear-create.json")
P4=$(sed -n 's/.*"resourceId":\([0-9]*\).*/\1/p' "$O/product-4-diycs-feb29only-create.json")
echo "  new product ids: $P1 $P2 $P3 $P4"

echo
echo "### persistence read-back from PostgreSQL (the create response is not evidence)"
docker exec fineract-db-1 psql -U root -d fineract_gerege -At \
  -c "select id||' multiplesOf='||coalesce(installment_amount_in_multiples_of::text,'NULL')||' diycs='||coalesce(days_in_year_custom_strategy,'NULL') from m_product_loan where id in ($P1,$P2,$P3,$P4) order by id;"

echo
echo "### re-issue the four loan applications against the T36-owned products"
sed "s/\"productId\": 1,/\"productId\": $P1,/" "$W/req/calc-B-01-baseline.json"           > "$REQ/calc-B-01-baseline.json"
sed "s/\"productId\": 2,/\"productId\": $P2,/" "$W/req/calc-B-02-multiplesof100.json"     > "$REQ/calc-B-02-multiplesof100.json"
sed "s/\"productId\": 3,/\"productId\": $P3,/" "$W/req/calc-B-03-diycs-fullleapyear.json" > "$REQ/calc-B-03-diycs-fullleapyear.json"
sed "s/\"productId\": 4,/\"productId\": $P4,/" "$W/req/calc-B-04-diycs-feb29only.json"    > "$REQ/calc-B-04-diycs-feb29only.json"

for pair in "01:calc-B-01-baseline:B-01-baseline" \
            "02:calc-B-02-multiplesof100:B-02-multiplesof100" \
            "03:calc-B-03-diycs-fullleapyear:B-03-diycs-fullleapyear" \
            "04:calc-B-04-diycs-feb29only:B-04-diycs-feb29only"; do
  n=${pair%%:*}; rest=${pair#*:}; req=${rest%%:*}; outname=${rest#*:}
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
              -d @"$REQ/$req.json" -o "$O/$outname-raw.json" -w '%{http_code}')
  echo "  B-$n  HTTP $code"
  [ "$code" = "200" ] || { echo "CAPTURE FAILED: HTTP $code is an ERROR BODY, not a capture" >&2; exit 1; }
done

echo
# T99 (sweep for the F-2 shape): hardened digest instrument, not a $PATH-resolved `shasum`.
. "$D/sha256.sh"
sha256_init || { echo "REFUSED: $SHA256_ERROR" >&2; exit 1; }
echo "# sha256 by $SHA256_TOOLS"
for f in "$O"/B-0*-raw.json; do
  sha256_file "$f" || { echo "REFUSED: $SHA256_ERROR" >&2; exit 1; }
  printf '%s  %s\n' "$SHA256_RESULT" "$f"
done
