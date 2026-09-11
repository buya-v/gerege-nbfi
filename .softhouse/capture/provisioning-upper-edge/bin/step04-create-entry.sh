#!/usr/bin/env bash
# STEP 4 (OH-PROVEDGE-BA): create ONE provisioning entry dated the pinned business
# date 2026-09-03, with the ENT-02 body shape and createjournalentries:false.
# If the oracle refuses (e.g. an entry already covers this date), the refusal body
# is the result: it is captured verbatim and the run stops.
set -uo pipefail

BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'
REQ_DIR=".softhouse/capture/provisioning-upper-edge/req"
OUT_DIR=".softhouse/capture/provisioning-upper-edge/out"

mkdir -p "$REQ_DIR" "$OUT_DIR"

printf '%s' '{"date":"03 September 2026","dateFormat":"dd MMMM yyyy","locale":"en","createjournalentries":false}' \
  > "$REQ_DIR/ENT-02-create.json"

HTTP=$(curl -sk -o "$OUT_DIR/ENT-02-create-raw.json" -w '%{http_code}' \
  -X POST "$BASE/provisioningentries" -H "$AUTH" -H "$TEN" -H "$CT" \
  --data-binary @"$REQ_DIR/ENT-02-create.json")
echo "HTTP $HTTP"
cat "$OUT_DIR/ENT-02-create-raw.json"; echo

RID=$(python3 -c "import json;print(json.load(open('$OUT_DIR/ENT-02-create-raw.json')).get('resourceId',''))")
if [ -z "$RID" ]; then
  echo "provisioning entry NOT created — refusal is the result (see ENT-02-create-raw.json)" >&2
  exit 1
fi
echo "$RID" > "$OUT_DIR/ENT-02-resource-id.txt"
echo "created provisioning entry id=$RID"
