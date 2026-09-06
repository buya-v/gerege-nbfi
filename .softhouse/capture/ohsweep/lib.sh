#!/usr/bin/env bash
# ohsweep/lib.sh — ONE oracle pass, MANY contexts. Shared capture helpers.
#
# The oracle (Fineract API) may only be touched by one task at a time, so this
# task does the oracle work for several contexts in one go.  Promotion into
# vectors is a later, offline task; this library only CAPTURES.
#
# Conventions (matching .softhouse/capture/seed/bin/*.sh):
#   * tenant is gerege, never default
#   * dates are pinned to BUSINESS_DATE 2026-09-01, never date/now
#   * raw response body -> $OHS_OUT/<name>-raw.json
#   * HTTP status       -> $OHS_OUT/<name>.status
#   * request body      -> $OHS_REQ/<name>.json  (POST/PUT only)
#   * a non-2xx is an OBSERVATION, recorded, never fatal (a refusal is data)

OHS_BASE='https://localhost:8443/fineract-provider/api/v1'
OHS_AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
OHS_TEN='Fineract-Platform-TenantId: gerege'
OHS_CT='Content-Type: application/json'

ohs_ctx() {
    # ohs_ctx CONTEXT — point OHS_OUT/OHS_REQ at a context and create dirs.
    OHS_CTX="${1:?usage: ohs_ctx CONTEXT}"
    OHS_OUT=".softhouse/capture/$OHS_CTX/out"
    OHS_REQ=".softhouse/capture/$OHS_CTX/req"
    OHS_BIN=".softhouse/capture/$OHS_CTX/bin"
    mkdir -p "$OHS_OUT" "$OHS_REQ" "$OHS_BIN"
}

ohs_call() {
    # ohs_call NAME METHOD RPATH [BODYFILE]
    # Captures response body + status; snapshots POST/PUT request body.
    local name="${1:?}" method="${2:?}" rpath="${3:?}" bodyfile="${4:-}"
    local tmpd body code
    tmpd=$(mktemp -d "${TMPDIR:-/tmp}/ohsweep.XXXXXX") || return 2
    body="$tmpd/body"

    local args=(-skS -X "$method" "$OHS_BASE$rpath" -H "$OHS_AUTH" -H "$OHS_TEN" -H "$OHS_CT")
    if [ -n "$bodyfile" ]; then
        [ -f "$bodyfile" ] || { echo "ohs_call: body file missing: $bodyfile" >&2; rm -rf "$tmpd"; return 2; }
        args+=(--data-binary "@$bodyfile")
    fi

    code=$(curl "${args[@]}" -o "$body" -w '%{http_code}')

    printf '%s\n' "$code" > "$OHS_OUT/$name.status"
    mv "$body" "$OHS_OUT/$name-raw.json"
    if [ -n "$bodyfile" ]; then
        cp "$bodyfile" "$OHS_REQ/$name.json"
    fi
    rm -rf "$tmpd"
    printf '%-24s %-6s %s -> %s\n' "$name" "$method" "$rpath" "$code" >&2
}

ohs_get()  { ohs_call "${1:?}" GET  "${2:?}"; }
ohs_post() { ohs_call "${1:?}" POST "${2:?}" "${3:?}"; }
ohs_put()  { ohs_call "${1:?}" PUT  "${2:?}" "${3:?}"; }

ohs_id() {
    # ohs_id FILE — print resourceId/clientId/loanId/id from a captured raw body.
    python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("resourceId", d.get("clientId", d.get("loanId", d.get("id","")))))' "$1"
}
