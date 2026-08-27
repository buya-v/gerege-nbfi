#!/bin/sh
# T22 INDEPENDENT AUDIT — run REPRODUCE.md end to end against a FRESH tenant.
#
# Tenant `gerege` was provisioned for this audit (see T22-pathb-capture-audit.md
# §"artefacts created on the oracle"):
#   - PostgreSQL database `fineract_gerege`
#   - tenants row identifier='gerege', timezone_id='Asia/Ulaanbaatar'   (CLAUDE.md tz rule)
#   - c_configuration rounding-mode = 4 (HALF_UP)                        (ratified tenant parameter)
# Everything else is the stock demo seed, identical to `default`.
#
# The request bodies are the COMMITTED Path B ones, byte for byte. Product ids
# land at 1..4 in a fresh tenant, so the calc payloads need no rewriting.
set -u
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb
O=$W/t22-audit/out-fresh-tenant
mkdir -p "$O"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

echo "== currencies =="
curl -sk -X PUT "$B/currencies" -H "$A" -H "$T" -H "$CT" \
  -d '{"currencies":["MNT","USD"]}' -o "$O/currencies.json"
cat "$O/currencies.json"; echo

echo "== clients =="
curl -sk -X POST "$B/clients" -H "$A" -H "$T" -H "$CT" \
  -d '{"officeId":1,"fullname":"Path B Fixture Borrower","legalFormId":1,"active":true,"activationDate":"01 January 2026","locale":"en","dateFormat":"dd MMMM yyyy"}' \
  -o "$O/client-1.json"; cat "$O/client-1.json"; echo
curl -sk -X POST "$B/clients" -H "$A" -H "$T" -H "$CT" \
  -d '{"officeId":1,"fullname":"Path B Leap Fixture","legalFormId":1,"active":true,"activationDate":"01 January 2023","locale":"en","dateFormat":"dd MMMM yyyy"}' \
  -o "$O/client-2.json"; cat "$O/client-2.json"; echo

echo "== products =="
for f in product-1-baseline product-2-multiplesof100 \
         product-3-diycs-fullleapyear product-4-diycs-feb29only; do
  curl -sk -X POST "$B/loanproducts" -H "$A" -H "$T" -H "$CT" \
       -d @"$W/req/$f.json" -o "$O/$f-create.json"
  echo "$f -> $(cat "$O/$f-create.json")"
done

echo "== captures =="
for n in 01 02 03 04; do
  case $n in 01) f=calc-B-01-baseline;;           02) f=calc-B-02-multiplesof100;;
             03) f=calc-B-03-diycs-fullleapyear;; 04) f=calc-B-04-diycs-feb29only;; esac
  curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
       -H "$A" -H "$T" -H "$CT" -d @"$W/req/$f.json" -o "$O/B-$n-raw.json"
  echo "B-$n -> $(wc -c < "$O/B-$n-raw.json") bytes"
done
