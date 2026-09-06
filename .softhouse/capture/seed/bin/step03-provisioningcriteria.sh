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

LIAB=$(python3 -c "import json;print(json.load(open('$STATE'))['liability'])")
EXPENSE=$(python3 -c "import json;print(json.load(open('$STATE'))['expense'])")
PRODUCT=$(python3 -c "import json;print(json.load(open('$STATE'))['loanProduct'])")

CRIT_NAME="SEED-Probe-Criteria"

existing=$(curl -sk "$BASE/provisioningcriteria" -H "$AUTH" -H "$TEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print([c.get('criteriaId') or c.get('id') for c in d if (c.get('criteriaName') or c.get('name'))=='$CRIT_NAME'])")

if [ "$existing" != "[]" ]; then
  id=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
  echo "criteria already exists id=$id (reused)"
  python3 - "$STATE" "$id" <<'PY'
import json,sys
state=json.load(open(sys.argv[1])); state['criteria']=int(sys.argv[2])
json.dump(state, open(sys.argv[1],'w'), indent=2)
PY
  echo "criteria state => $(cat "$STATE")"
  exit 0
fi

cat > "$REQ_DIR/provisioningcriteria.json" <<EOF
{
  "criteriaName": "$CRIT_NAME",
  "loanProducts": [{"id": $PRODUCT}],
  "definitions": [
    {"categoryId":1,"minAge":0,"maxAge":29,"provisioningPercentage":1.0,"liabilityAccount":$LIAB,"expenseAccount":$EXPENSE},
    {"categoryId":2,"minAge":30,"maxAge":59,"provisioningPercentage":25.0,"liabilityAccount":$LIAB,"expenseAccount":$EXPENSE},
    {"categoryId":3,"minAge":60,"maxAge":89,"provisioningPercentage":50.0,"liabilityAccount":$LIAB,"expenseAccount":$EXPENSE},
    {"categoryId":4,"minAge":90,"maxAge":36500,"provisioningPercentage":100.0,"liabilityAccount":$LIAB,"expenseAccount":$EXPENSE}
  ]
}
EOF

curl -sk -X POST "$BASE/provisioningcriteria" \
  -H "$AUTH" -H "$TEN" -H "$CT" \
  --data-binary @"$REQ_DIR/provisioningcriteria.json" \
  > "$OUT_DIR/provisioningcriteria-raw.json"

resp=$(cat "$OUT_DIR/provisioningcriteria-raw.json")
echo "criteria POST resp => $resp"

id=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('resourceId', d.get('criteriaId', d.get('id',''))))" <<<"$resp")
python3 - "$STATE" "$id" <<'PY'
import json,sys
state=json.load(open(sys.argv[1])); state['criteria']=int(sys.argv[2]) if sys.argv[2] else None
json.dump(state, open(sys.argv[1],'w'), indent=2)
PY
echo "criteria state => $(cat "$STATE")"
