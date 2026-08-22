#!/bin/sh
# T276 INDEPENDENT re-issue of T275 FINDING 1, with the reviewer's OWN identity query.
# Nothing here is copied from T275's instruments except the base URL/credentials/tenant,
# which are facts about the oracle, not about the claim under review.
set -u
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'
D=/tmp/t276/head

snap() {
  echo "===== SNAPSHOT $1 ====="
  docker exec -i fineract-db-1 psql -U root -d fineract_gerege -f - < "$D/q.sql"
}

put() {
  echo "===== PUT $1  body: $2 ====="
  printf '%s' "$2" > "$D/body.json"
  code=$(curl -sk -X PUT "$B/loanproducts/23" -H "$A" -H "$T" -H "$CT" \
    --data-binary @"$D/body.json" -o "$D/resp.json" -w '%{http_code}')
  echo "HTTP $code"
  cat "$D/resp.json"; echo
}

snap "S0 baseline"
put "S1 repoint generic FUND_SOURCE 16 -> 2" '{"fundSourceAccountId": 2, "locale": "en"}'
snap "S1 after"
put "S2 channel pt2 value change GL 17 -> 16" '{"locale": "en", "paymentChannelToFundSourceMappings": [{"paymentTypeId": 2, "fundSourceAccountId": 16}]}'
snap "S2 after"
put "S3 no accounting parameter at all" '{"description": "T276 reviewer probe: no accounting parameter is present in this body", "locale": "en"}'
snap "S3 after"
put "S4 channel list emptied" '{"locale": "en", "paymentChannelToFundSourceMappings": []}'
snap "S4 after"
put "S5 channel re-added" '{"locale": "en", "paymentChannelToFundSourceMappings": [{"paymentTypeId": 2, "fundSourceAccountId": 16}]}'
snap "S5 after"
put "S6 KEY CHANGE pt2 -> pt1 (T275 marked this UNVERIFIED)" '{"locale": "en", "paymentChannelToFundSourceMappings": [{"paymentTypeId": 1, "fundSourceAccountId": 16}]}'
snap "S6 after"
put "S7 MULTI-ENTRY list (T275 marked this UNVERIFIED)" '{"locale": "en", "paymentChannelToFundSourceMappings": [{"paymentTypeId": 1, "fundSourceAccountId": 16}, {"paymentTypeId": 2, "fundSourceAccountId": 17}]}'
snap "S7 after"
