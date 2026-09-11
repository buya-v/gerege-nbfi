#!/bin/bash
# Shared REST helper for OH-TBCAP-Y. Tenant gerege ONLY. Never `default`.
set -u
REST="https://localhost:8443/fineract-provider/api/v1"
AUTH="mifos:password"
TEN="Fineract-Platform-TenantId: gerege"

# rest_get <out> <path>
rest_get() {
  code=$(curl -k -s -o "$1" -w '%{http_code}' -u "$AUTH" -H "$TEN" "$REST$2")
  printf '%s' "$code" > "$1.status"
}

# rest_post <out> <path> <body-file>
rest_post() {
  code=$(curl -k -s -o "$1" -w '%{http_code}' -u "$AUTH" -H "$TEN" \
         -H 'Content-Type: application/json' -X POST --data-binary @"$3" "$REST$2")
  printf '%s' "$code" > "$1.status"
}

# rest_post_nobody <out> <path>
rest_post_nobody() {
  code=$(curl -k -s -o "$1" -w '%{http_code}' -u "$AUTH" -H "$TEN" -X POST "$REST$2")
  printf '%s' "$code" > "$1.status"
}
