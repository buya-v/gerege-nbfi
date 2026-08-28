#!/bin/sh
# capget.sh NAME PATH IDEMPOTENCY_KEY
#
# T391's read-only capture tool. It is a SEPARATE, NARROWER tool than T388's
# cap11.sh and the narrowing is the point:
#
#   IT CAN ONLY ISSUE `GET`. There is no method argument and no body argument,
#   so this task CANNOT move oracle state through it even by mistake. T391 is a
#   PROMOTION, not a capture campaign: every observation it needs already exists
#   in the oracle, and re-issuing a POST would move the oracle a second time and
#   corrupt the evidence it is promoting (T389's own reason for not re-issuing
#   T388's twenty POSTs).
#
# Everything else is carried over from cap11.sh verbatim in behaviour:
#   * a mandatory Idempotency-Key argument, refused if absent (P-22);
#   * out/NAME.req = the exact wire bytes, plus out/NAME.req.sha256;
#   * out/NAME.http = the record INCLUDING the key actually sent;
#   * out/NAME.status and out/NAME.json;
#   * nothing written under out/ until the exchange completed, so an aborted run
#     leaves no half-artefact;
#   * a non-2xx is recorded AS DATA, never treated as an error.
#
# `Idempotency-Key` is the pinned oracle's own configured header name
# [VERIFIED: fineract-provider/src/main/resources/application.properties,
# `fineract.idempotency-key-header-name=${FINERACT_IDEMPOTENCY_KEY_HEADER_NAME:Idempotency-Key}`].
# It is sent on a GET too, so that every exchange this task makes is attributable
# by name in m_portfolio_command_source-adjacent logs rather than anonymous.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"

NAME=${1-}; RPATH=${2-}; KEY=${3-}
[ -n "$NAME" ] && [ -n "$RPATH" ] || { echo "usage: capget.sh NAME PATH IDEMPOTENCY_KEY" >&2; exit 2; }
[ -n "$KEY" ] || { echo "REFUSING: no Idempotency-Key given. A probe that sends no key proves nothing about idempotency." >&2; exit 2; }

OUT="$DIR/out/$NAME.json"
STATUS="$DIR/out/$NAME.status"
HTTP="$DIR/out/$NAME.http"
REQ="$DIR/out/$NAME.req"
REQSHA="$DIR/out/$NAME.req.sha256"

for f in "$OUT" "$STATUS" "$HTTP" "$REQ" "$REQSHA"; do
  [ -e "$f" ] && { echo "REFUSING: $f already exists. This tool never overwrites a committed observation." >&2; exit 2; }
done

TMPD=$(mktemp -d)
trap 'rm -rf "$TMPD"' EXIT INT TERM HUP QUIT

# The wire bytes of a GET are the request line and headers; there is no body.
{
  printf 'GET %s\n' "$RPATH"
  printf 'Fineract-Platform-TenantId: gerege\n'
  printf 'Authorization: Basic <mifos:password>\n'
  printf 'Idempotency-Key: %s\n' "$KEY"
} > "$TMPD/req"

set +e
code=$(curl -sk -o "$TMPD/body" -w '%{http_code}' \
  -X GET "$B$RPATH" \
  -H "$A" -H "$T" -H "$CT" -H "Idempotency-Key: $KEY")
rc=$?
set -e
if [ "$rc" -ne 0 ]; then
  echo "TRANSPORT FAILURE rc=$rc for $NAME; nothing written." >&2
  exit 1
fi

cp "$TMPD/body" "$OUT"
printf '%s\n' "$code" > "$STATUS"
cp "$TMPD/req" "$REQ"
( cd "$DIR/out" && shasum -a 256 "$NAME.req" > "$NAME.req.sha256" )
{
  cat "$TMPD/req"
  printf 'body: <none>\n'
  printf 'captured-at-utc: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$HTTP"
echo "$NAME -> HTTP $code"
