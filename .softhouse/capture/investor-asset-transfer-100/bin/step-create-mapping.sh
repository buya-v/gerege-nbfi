#!/usr/bin/env bash
# OH-INV-Y step 3: create the ASSET_TRANSFER(100) financial-activity mapping via API.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

REQF="$REQ/create-financialactivityaccount-asset-transfer-100.json"
printf 'request  %s\n' "$REQF"
printf 'request  sha256 %s\n' "$(cap_sha "$REQF")"
printf 'request  bytes  %s\n' "$(wc -c < "$REQF" | tr -d ' ')"

cap_post create-financialactivityaccount-asset-transfer-100 /financialactivityaccounts "$REQF"
printf 'response body:\n'
cat "$OUT/create-financialactivityaccount-asset-transfer-100.json"; printf '\n'

# read back the full mapping list
cap_get financialactivityaccounts-post /financialactivityaccounts
printf 'mapping list:\n'
cat "$OUT/financialactivityaccounts-post.json"; printf '\n'
