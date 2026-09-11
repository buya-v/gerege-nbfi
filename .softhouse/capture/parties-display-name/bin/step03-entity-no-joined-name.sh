#!/usr/bin/env bash
# OH-NAMECAP-AW step03 — ENTITY (legal form 2), the arm that yields no joined name.
#
# First attempt E1: entity with person-style parts and NO fullname. If the oracle
# accepts it, the derived display name is expected to be empty (arm 3). If the
# oracle refuses E1, THE REFUSAL IS THE RESULT — it is captured verbatim — and a
# fallback entity E2 (fullname only) is created so the corpus still holds an
# entity client with parts and a read-back display name.
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 2
source .softhouse/capture/ohsweep/lib.sh
source .softhouse/capture/parties-display-name/bin/db-readback.sh
ohs_ctx parties-display-name

NAME='OHNAMECAP-E1'
BODY="$(mktemp "${TMPDIR:-/tmp}/namecap-e1.XXXXXX")"
cat > "$BODY" <<'JSON'
{"officeId":1,"firstname":"Байгууллага","middlename":"Туршилтын","lastname":"Жишээ","externalId":"OHNAMECAP-E1","legalFormId":2,"active":false,"locale":"en","dateFormat":"dd MMMM yyyy"}
JSON

ohs_post "$NAME-create" /clients "$BODY"
rm -f "$BODY"

cid="$(ohs_id "$OHS_OUT/$NAME-create-raw.json")"
if [ -z "$cid" ]; then
    echo "REFUSAL: $NAME create status $(cat "$OHS_OUT/$NAME-create.status") — the oracle requires something before an entity can carry no fullname."
    echo "Refusal body: $(cat "$OHS_OUT/$NAME-create-raw.json")"

    NAME='OHNAMECAP-E2'
    BODY="$(mktemp "${TMPDIR:-/tmp}/namecap-e2.XXXXXX")"
    cat > "$BODY" <<'JSON'
{"officeId":1,"fullname":"Байгууллага Туршилтын Жишээ","externalId":"OHNAMECAP-E2","legalFormId":2,"active":false,"locale":"en","dateFormat":"dd MMMM yyyy"}
JSON
    ohs_post "$NAME-create" /clients "$BODY"
    rm -f "$BODY"
    cid="$(ohs_id "$OHS_OUT/$NAME-create-raw.json")"
    if [ -z "$cid" ]; then
        echo "REFUSAL: $NAME create status $(cat "$OHS_OUT/$NAME-create.status"); body follows:" >&2
        cat "$OHS_OUT/$NAME-create-raw.json" >&2
        exit 1
    fi
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
