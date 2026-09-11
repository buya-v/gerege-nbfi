#!/bin/bash
# OH-TBCAP-Y step 2 -- reverse the manual entry posted in step 1.
set -u
DIR=$(cd "$(dirname "$0")/.." && pwd)
source "$DIR/bin/rest.sh"

TXID="a2b795dca42b"
OUT="$DIR/step02-reverse"
mkdir -p "$OUT"

cp "$DIR/req/02-reverse.json" "$OUT/request.json"
rest_post "$OUT/response.json" "/journalentries/$TXID?command=reverse" "$DIR/req/02-reverse.json"
echo "HTTP $(cat "$OUT/response.json.status")"
cat "$OUT/response.json"
