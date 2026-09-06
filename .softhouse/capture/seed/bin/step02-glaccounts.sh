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
[ -f "$STATE" ] || echo '{}' > "$STATE"

# GL account type ids: 1=ASSET 2=LIABILITY 3=EQUITY 4=INCOME 5=EXPENSE
# usage ids: 1=DETAIL 2=HEADER
create_gl() {
  local name="$1" glcode="$2" type_id="$3" usage_id="$4" desc="$5"
  local existing id

  existing=$(curl -sk "$BASE/glaccounts?limit=1000" -H "$AUTH" -H "$TEN" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print([g['id'] for g in d if g.get('glCode')=='$glcode'])")

  if [ "$existing" != "[]" ]; then
    id=$(echo "$existing" | python3 -c "import json,sys; print(json.load(sys.stdin)[0])")
    echo "{\"name\":\"$name\",\"glCode\":\"$glcode\",\"id\":$id,\"reused\":true}"
    return
  fi

  cat > "$REQ_DIR/gl-$glcode.json" <<EOF
{"name":"$name","glCode":"$glcode","manualEntriesAllowed":true,"type":$type_id,"usage":$usage_id,"description":"$desc"}
EOF

  curl -sk -X POST "$BASE/glaccounts" \
    -H "$AUTH" -H "$TEN" -H "$CT" \
    --data-binary @"$REQ_DIR/gl-$glcode.json" \
    > "$OUT_DIR/gl-$glcode-raw.json"

  local resp
  resp=$(cat "$OUT_DIR/gl-$glcode-raw.json")
  id=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('resourceId', d.get('id','')))" <<<"$resp")
  echo "{\"name\":\"$name\",\"glCode\":\"$glcode\",\"id\":$id,\"reused\":false}"
}

ASSET=$(create_gl "SEED-Provisioning-Asset" "SEED-10001" 1 1 "SEED provisioning asset account")
LIAB=$(create_gl "SEED-Provisioning-Liability" "SEED-20001" 2 1 "SEED provisioning liability account")
INCOME=$(create_gl "SEED-Provisioning-Income" "SEED-40001" 4 1 "SEED provisioning income account")
EXPENSE=$(create_gl "SEED-Provisioning-Expense" "SEED-50001" 5 1 "SEED provisioning expense account")

# Merge into existing state.json (never clobber keys written by other steps)
python3 - "$STATE" "$ASSET" "$LIAB" "$INCOME" "$EXPENSE" <<'PY'
import json, sys
state_path = sys.argv[1]
state = json.load(open(state_path))
for arg in sys.argv[2:]:
    o = json.loads(arg)
    code = o["glCode"]
    if code.endswith("10001"): state["asset"] = o["id"]
    elif code.endswith("20001"): state["liability"] = o["id"]
    elif code.endswith("40001"): state["income"] = o["id"]
    elif code.endswith("50001"): state["expense"] = o["id"]
json.dump(state, open(state_path, 'w'), indent=2)
PY

echo "GL state => $(cat "$STATE")"
