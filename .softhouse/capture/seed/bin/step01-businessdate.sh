#!/usr/bin/env bash
set -uo pipefail

BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'
REQ_DIR=".softhouse/capture/seed/req"
OUT_DIR=".softhouse/capture/seed/out"

# 1. enable business date configuration
cat > "$REQ_DIR/enable-business-date.json" <<'EOF'
{"enabled":true}
EOF

curl -sk -X PUT "$BASE/configurations/name/enable-business-date" \
  -H "$AUTH" -H "$TEN" -H "$CT" \
  --data-binary @"$REQ_DIR/enable-business-date.json" \
  > "$OUT_DIR/enable-business-date-raw.json"
echo "enable-business-date => $(cat "$OUT_DIR/enable-business-date-raw.json")"

# 2. pin the business date
cat > "$REQ_DIR/businessdate.json" <<'EOF'
{"type":"BUSINESS_DATE","date":"01 September 2026","dateFormat":"dd MMMM yyyy","locale":"en"}
EOF

curl -sk -X POST "$BASE/businessdate" \
  -H "$AUTH" -H "$TEN" -H "$CT" \
  --data-binary @"$REQ_DIR/businessdate.json" \
  > "$OUT_DIR/businessdate-raw.json"
echo "businessdate POST => $(cat "$OUT_DIR/businessdate-raw.json")"

# 3. read it back and save
curl -sk "$BASE/businessdate" \
  -H "$AUTH" -H "$TEN" \
  > "$OUT_DIR/businessdate-get-raw.json"
echo "businessdate GET => $(cat "$OUT_DIR/businessdate-get-raw.json")"
