#!/usr/bin/env bash
# OH-NAMECAP-AW step01 — person, THREE distinct non-blank parts.
#
# Arm observed: DeriveDisplayName arm 2 (no fullname; PERSON legal form; the three
# parts joined in firstname, middlename, lastname order, blanks skipped).
#
# Body shape is copied from
#   .softhouse/capture/loan-writeoff-paid-instalment/req/client-OHWOPAID-C01-create.json
# with one deliberate change: active=false, so the client stays PENDING and no
# activation path is exercised (brief: "do not activate them unless the create
# requires it"). office, legalFormId, locale and dateFormat match that accepted body.
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 2
source .softhouse/capture/ohsweep/lib.sh
source .softhouse/capture/parties-display-name/bin/db-readback.sh
ohs_ctx parties-display-name

NAME='OHNAMECAP-P1'
BODY="$(mktemp "${TMPDIR:-/tmp}/namecap-p1.XXXXXX")"
cat > "$BODY" <<'JSON'
{"officeId":1,"firstname":"Синтетик","middlename":"Туршилтын","lastname":"Жишээ","externalId":"OHNAMECAP-P1","legalFormId":1,"active":false,"locale":"en","dateFormat":"dd MMMM yyyy"}
JSON

ohs_post "$NAME-create" /clients "$BODY"
rm -f "$BODY"

cid="$(ohs_id "$OHS_OUT/$NAME-create-raw.json")"
if [ -z "$cid" ]; then
    echo "REFUSAL: $NAME create status $(cat "$OHS_OUT/$NAME-create.status"); body follows:" >&2
    cat "$OHS_OUT/$NAME-create-raw.json" >&2
    exit 1
fi

ohs_get "$NAME" "/clients/$cid"
nc_readback "$NAME" "$cid"

echo "--- $NAME create status: $(cat "$OHS_OUT/$NAME-create.status") clientId: $cid ---"
python3 - "$OHS_OUT/$NAME-raw.json" "$OHS_OUT/$NAME-m-client.json" <<'PY'
import json, sys
get = json.load(open(sys.argv[1]))
db = json.load(open(sys.argv[2]))[0]
print("GET :", {k: get.get(k) for k in ("firstname", "middlename", "lastname", "fullname", "displayName", "legalForm")})
print("DB  :", {k: db.get(k) for k in ("firstname", "middlename", "lastname", "fullname", "display_name", "legal_form_enum")})
PY
