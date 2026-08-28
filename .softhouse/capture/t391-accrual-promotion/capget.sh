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
#   * out/NAME.http = the record INCLUDING the key actually sent;
#   * out/NAME.status and out/NAME.json;
#   * nothing written under out/ until the exchange completed, so an aborted run
#     leaves no half-artefact;
#   * a non-2xx is recorded AS DATA, never treated as an error.
#
# NO `out/NAME.req` IS WRITTEN, AND THAT IS A CORRECTION THE BAR MADE. The first
# draft of this script wrote one, holding the request LINE and headers. The
# repository-wide wire-float round-trip guard takes EVERY `*.req` at any depth
# under .softhouse/capture as A REQUEST BODY and requires it to parse as JSON
# [.softhouse/conformance.sh, the guard's own derive(): "every *.json whose DIRECT
# parent directory is named req, plus every *.req wire-bytes artefact"], so eight
# text files that are not bodies REFUSED the whole run at exit 2. The guard was
# RIGHT and the script was wrong: A GET HAS NO BODY, so there are no body bytes
# to pin, and a `.req` that is not a request body is a lie about the population
# it joins. cap11.sh has the same property and writes no `.req` for its GETs
# either -- T388's own A03/A04/A05 GET captures carry `.http`, `.status` and
# `.json` and nothing else. The `.http` record below carries the request line,
# the headers and the Idempotency-Key actually sent, which is the whole of what a
# GET request IS.
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

for f in "$OUT" "$STATUS" "$HTTP"; do
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
{
  cat "$TMPD/req"
  printf 'body: <none>\n'
  printf 'captured-at-utc: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$HTTP"
echo "$NAME -> HTTP $code"
