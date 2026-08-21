#!/bin/sh
# cap.sh NAME METHOD PATH [BODYFILE]
#
# One observation = one HTTP exchange, recorded verbatim.
#
# This deliberately does NOT fail on a non-2xx status, unlike the Path B loan-schedule
# recipe. In slice A2 a refusal IS the observation: the whole point of the
# validation/uniqueness/hierarchy captures is to record what the oracle says NO to and
# in exactly what words. The status is therefore recorded as data
# (out/NAME.status), never used to discard the body.
#
# What IS an error here is a transport failure (curl exit != 0) — that means no
# observation was made at all, and the script exits non-zero so nothing gets committed.
set -e
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"

NAME=$1; METHOD=$2; RPATH=$3; BODY=$4
[ -n "$NAME" ] && [ -n "$METHOD" ] && [ -n "$RPATH" ] || { echo "usage: cap.sh NAME METHOD PATH [BODYFILE]" >&2; exit 2; }

OUT="$DIR/out/$NAME.json"
STATUS="$DIR/out/$NAME.status"

{
  echo "$METHOD $RPATH"
  echo "Fineract-Platform-TenantId: gerege"
  echo "Authorization: Basic <mifos:password>"
  [ -n "$BODY" ] && echo "Content-Type: application/json" && echo "body-file: $BODY"
  echo "captured-at-utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$DIR/out/$NAME.http"

if [ -n "$BODY" ]; then
  code=$(curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -H "$CT" \
              -d @"$DIR/$BODY" -o "$OUT" -w '%{http_code}')
else
  code=$(curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -o "$OUT" -w '%{http_code}')
fi
rc=$?
if [ $rc -ne 0 ]; then
  echo "TRANSPORT FAILURE (curl rc=$rc) for $NAME — NO OBSERVATION WAS MADE." >&2
  rm -f "$OUT"
  exit 1
fi

echo "$code" > "$STATUS"
printf '%-44s HTTP %s\n' "$NAME" "$code"
