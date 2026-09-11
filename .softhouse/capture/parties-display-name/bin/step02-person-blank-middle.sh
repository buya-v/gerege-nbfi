#!/usr/bin/env bash
# OH-NAMECAP-AW step02 — person, BLANK middle part.
#
# Arm observed: DeriveDisplayName arm 2 with the blank-skip. middlename is absent
# from the request, so the joined display name must not contain a doubled space
# or a leading/trailing separator. fullname stays absent; firstname and lastname
# are the only parts.
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 2
source .softhouse/capture/ohsweep/lib.sh
source .softhouse/capture/parties-display-name/bin/db-readback.sh
ohs_ctx parties-display-name

NAME='OHNAMECAP-P2'
BODY="$(mktemp "${TMPDIR:-/tmp}/namecap-p2.XXXXXX")"
cat > "$BODY" <<'JSON'
{"officeId":1,"firstname":"Синтетик","lastname":"Давхардалгүй","externalId":"OHNAMECAP-P2","legalFormId":1,"active":false,"locale":"en","dateFormat":"dd MMMM yyyy"}
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
