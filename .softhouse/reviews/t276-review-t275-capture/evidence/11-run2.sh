#!/bin/sh
# T276 part 2: the GENERIC-SLOT identity claim (T275 A2-503: "id 12 SURVIVES, max(id) unmoved").
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
  printf '%s' "$2" > "$D/body2.json"
  code=$(curl -sk -X PUT "$B/loanproducts/23" -H "$A" -H "$T" -H "$CT" \
    --data-binary @"$D/body2.json" -o "$D/resp2.json" -w '%{http_code}')
  echo "HTTP $code"
  cat "$D/resp2.json"; echo
}

snap "G0 baseline"
put "G1 generic FUND_SOURCE value change GL 16 -> 18 (both ASSET)" '{"fundSourceAccountId": 18, "locale": "en"}'
snap "G1 after"
put "G2 generic FUND_SOURCE value change GL 18 -> 21 (ASSET -> LIABILITY)" '{"fundSourceAccountId": 21, "locale": "en"}'
snap "G2 after"
put "G3 RESTORE generic FUND_SOURCE back to GL 16" '{"fundSourceAccountId": 16, "locale": "en"}'
snap "G3 after"
put "G4 RESTORE channel to the single T275 end-state entry pt2 -> GL 17" '{"locale": "en", "paymentChannelToFundSourceMappings": [{"paymentTypeId": 2, "fundSourceAccountId": 17}]}'
put "G5 RESTORE description to the T275 end-state string" '{"description": "T275 unrelated-field update probe: no accounting parameter is present in this body", "locale": "en"}'
snap "G5 after (restored)"
