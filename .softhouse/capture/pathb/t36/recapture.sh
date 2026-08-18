#!/bin/sh
# T36 — re-capture the four Path B sets against a PRODUCTION-SETTINGS tenant.  Closes T22 P0-6.
#
# Tenant `gerege`: timezone Asia/Ulaanbaatar (+08, no DST — the ZONE is asserted, never an offset),
# c_configuration.rounding-mode = 4 (HALF_UP), MoneyHelper.PRECISION = 19 (deployed bytecode).
# Effective MathContext therefore (19, HALF_UP) — the ratified production setting.
#
# Additive only.  Creates no tenant, restarts nothing, drops nothing: a second worker is running
# Path A captures against this same server for the whole fire.  Products 1-4 already exist in
# `gerege` from the committed byte-verbatim payloads (t22-audit/fresh-tenant.sh); this run reuses
# them so the calc requests can be sent BYTE-VERBATIM from req/, productId included.
#
# Preconditions are FAIL-THE-RUN: no capture is attempted unless every one holds.
set -u
D=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$D/.." && pwd)
O=$D/out/recapture-gerege
TENANT=${TENANT:-gerege}
mkdir -p "$O"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T="Fineract-Platform-TenantId: $TENANT"
CT='Content-Type: application/json'

echo "### preconditions (T22 P0-4) — a breach aborts before any capture"
CANARY_REQ="$W/t22-audit/req/calc-pmode2-gerege.json" sh "$D/preconditions.sh" "$TENANT" \
  | tee "$O/preconditions.txt"
# shellcheck disable=SC2181
if [ "$(grep -c '^  FAIL' "$O/preconditions.txt")" != "0" ]; then
  echo "ABORT: preconditions breached — nothing captured." >&2
  exit 1
fi

echo
echo "### product persistence read-back, from PostgreSQL rows not from the create response"
SCHEMA=$(docker exec fineract-db-1 psql -U root -d fineract_tenants -At \
  -c "select c.schema_name from tenants t join tenant_server_connections c on c.id=t.oltp_id where t.identifier='$TENANT';" | tr -d '\r')
docker exec fineract-db-1 psql -U root -d "$SCHEMA" -At \
  -c "select to_jsonb(t) from m_product_loan t where id in (1,2,3,4) order by id;" > "$O/products-asrow.jsonl"
docker exec fineract-db-1 psql -U root -d "$SCHEMA" -At \
  -c "select id, coalesce(installment_amount_in_multiples_of::text,'NULL'), coalesce(days_in_year_custom_strategy,'NULL') from m_product_loan where id in (1,2,3,4) order by id;"

echo
echo "### captures — explicit filenames, HTTP status checked, non-200 fails the run"
set -e
for pair in "01:calc-B-01-baseline:B-01-baseline" \
            "02:calc-B-02-multiplesof100:B-02-multiplesof100" \
            "03:calc-B-03-diycs-fullleapyear:B-03-diycs-fullleapyear" \
            "04:calc-B-04-diycs-feb29only:B-04-diycs-feb29only"; do
  n=${pair%%:*}; rest=${pair#*:}; req=${rest%%:*}; outname=${rest#*:}
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
              -H "$A" -H "$T" -H "$CT" -d @"$W/req/$req.json" \
              -o "$O/$outname-raw.json" -w '%{http_code}')
  echo "B-$n  HTTP $code  -> $O/$outname-raw.json"
  if [ "$code" != "200" ]; then
    echo "CAPTURE FAILED: B-$n returned HTTP $code — the file is an ERROR BODY, not a capture." >&2
    exit 1
  fi
done

echo
shasum -a 256 "$O"/B-0*-raw.json
