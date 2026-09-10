#!/usr/bin/env bash
# gl-accounting-surface shared oracle client.
#
# ADDITIVE ONLY: every call here is a GET or a POST that creates a NEW row keyed
# on an OHLGT- external id. No PUT, no DELETE, nothing addressed at an existing
# product/client/loan.
#
# BYTE-STABLE REQUESTS (the defect this rig exists to fix). Every numeric token
# written into a req/*.json body is an INTEGER. An integer token survives a
# binary-double round trip byte-for-byte (`json.dumps(int(tok)) == tok`), where
# `100.00` does not (`100.00` -> `100.0`). Money on the wire that has to survive
# the one genuine Java `double` on the Fineract request path (POST /charges
# `private double amount`, T186 2.4) is written this way, and the loan's
# `principal` is a JSON STRING ("100000"), the shape every Path A capture uses.
# Nothing in this rig is ever re-serialised through json.dumps of a parsed
# number; the templates are written as literal bytes and posted with
# --data-binary.
set -uo pipefail

BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

ROOT="/Users/buv/oh-gerege-glt"
CAP="$ROOT/.softhouse/capture/gl-accounting-surface"
REQ="$CAP/req"
OUT="$CAP/out"
STATE="$OUT/state.json"

mkdir -p "$REQ" "$OUT"
[ -f "$STATE" ] || echo '{}' > "$STATE"

api_get()  { curl -sk -m 30 "$BASE$1" -H "$AUTH" -H "$TEN"; }
api_post() { curl -sk -m 30 -X POST "$BASE$1" -H "$AUTH" -H "$TEN" -H "$CT" --data-binary @"$2"; }

# state_set <key> <json-value-literal>
state_set() {
  python3 - "$STATE" "$1" "$2" <<'PY'
import json,sys
p,k,v=sys.argv[1],sys.argv[2],sys.argv[3]
s=json.load(open(p))
try: v=json.loads(v)
except Exception: pass
s[k]=v
json.dump(s,open(p,'w'),indent=2)
PY
}

state_get() {
  python3 - "$STATE" "$1" <<'PY'
import json,sys
s=json.load(open(sys.argv[1]))
v=s.get(sys.argv[2])
print('' if v is None else v)
PY
}
