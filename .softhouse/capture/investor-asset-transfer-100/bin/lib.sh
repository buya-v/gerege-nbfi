#!/usr/bin/env bash
# OH-INV-Y capture helper. Sourced, never executed.
set -uo pipefail

CAP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
CAP="$CAP_ROOT/.softhouse/capture/investor-asset-transfer-100"
REQ="$CAP/req"
OUT="$CAP/out"
BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

# cap_get <name> <path>  — GET, write out/<name>.json and out/<name>.status
cap_get() {
  local name="$1" path="$2" code
  code=$(curl -sk -o "$OUT/$name.json" -w '%{http_code}' \
      "$BASE$path" -H "$AUTH" -H "$TEN")
  printf '%s\n' "$code" > "$OUT/$name.status"
  printf 'GET  %-52s -> %s\n' "$path" "$code"
}

# cap_post <name> <path> <req-file>  — POST --data-binary @file
cap_post() {
  local name="$1" path="$2" reqf="$3" code
  code=$(curl -sk -o "$OUT/$name.json" -w '%{http_code}' -X POST \
      "$BASE$path" -H "$AUTH" -H "$TEN" -H "$CT" \
      --data-binary "@$reqf")
  printf '%s\n' "$code" > "$OUT/$name.status"
  printf 'POST %-52s -> %s\n' "$path" "$code"
}

# cap_sha <file> — print sha256
cap_sha() { shasum -a 256 "$1" | awk '{print $1}'; }
