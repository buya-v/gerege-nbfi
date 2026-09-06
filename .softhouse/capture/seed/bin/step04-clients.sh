#!/usr/bin/env bash
set -uo pipefail

BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'
REQ_DIR=".softhouse/capture/seed/req"
OUT_DIR=".softhouse/capture/seed/out"
STATE="$OUT_DIR/state.json"

mkdir -p "$REQ_DIR" "$OUT_DIR"

# Client activation date is pinned BEFORE every loan/disbursement date so that
# back-dated loans (needed to land in multiple provisioning age bands relative to
# the pinned business date 2026-09-01) pass the "submitted >= activation" rule.
ACTIVATION="01 May 2026"

create_client() {
  local ext="$1" first="$2" last="$3"
  local existing id

  existing=$(curl -sk "$BASE/clients?limit=1000" -H "$AUTH" -H "$TEN" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); items=d.get('pageItems', d if isinstance(d,list) else []); print([c['id'] for c in items if c.get('externalId')=='$ext'])")

  if [ "$existing" != "[]" ]; then
    id=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
    echo "{\"externalId\":\"$ext\",\"id\":$id,\"reused\":true}"
    return
  fi

  cat > "$REQ_DIR/client-$ext.json" <<EOF
{"officeId":1,"firstname":"$first","lastname":"$last","externalId":"$ext","legalFormId":1,"active":true,"activationDate":"$ACTIVATION","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF

  curl -sk -X POST "$BASE/clients" \
    -H "$AUTH" -H "$TEN" -H "$CT" \
    --data-binary @"$REQ_DIR/client-$ext.json" \
    > "$OUT_DIR/client-$ext-raw.json"

  local resp
  resp=$(cat "$OUT_DIR/client-$ext-raw.json")
  id=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('resourceId', d.get('clientId', d.get('id',''))))" <<<"$resp")
  echo "{\"externalId\":\"$ext\",\"id\":$id,\"reused\":false}"
}

C1=$(create_client "SEED-C11" "SEED-C11" "Borrower")
C2=$(create_client "SEED-C12" "SEED-C12" "Borrower")
C3=$(create_client "SEED-C13" "SEED-C13" "Borrower")

python3 - "$STATE" "$C1" "$C2" "$C3" <<'PY'
import json,sys
state=json.load(open(sys.argv[1]))
clients={}
for arg in sys.argv[2:]:
    o=json.loads(arg)
    clients[o['externalId']]=o['id']
state['clients']=clients
json.dump(state, open(sys.argv[1],'w'), indent=2)
PY
echo "clients state => $(cat "$STATE")"
