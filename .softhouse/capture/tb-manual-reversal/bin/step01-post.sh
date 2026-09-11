#!/bin/bash
# OH-TBCAP-Y step 1 -- post ONE balanced manual journal entry on office 1.
set -u
DIR=$(cd "$(dirname "$0")/.." && pwd)
source "$DIR/bin/rest.sh"

POSTED="$DIR/step01-post"
mkdir -p "$POSTED"

cp "$DIR/req/01-post-manual-entry.json" "$POSTED/request.json"
rest_post "$POSTED/response.json" "/journalentries" "$DIR/req/01-post-manual-entry.json"
echo "HTTP $(cat "$POSTED/response.json.status")"
cat "$POSTED/response.json"
