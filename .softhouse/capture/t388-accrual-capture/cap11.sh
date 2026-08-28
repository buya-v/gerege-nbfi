#!/bin/sh
# cap10.sh NAME METHOD PATH BODYFILE IDEMPOTENCY_KEY
#
# T236's successor to cap9.sh, for ONE purpose: close the P-40 residual T216 named and
# left (cap9.sh:49's scratch-dir cleanup trap has no QUIT, so Ctrl-\ / SIGQUIT during a
# capture leaks its mktemp dir under /tmp -- LOW materiality, see T236's handoff: no
# vector, no committed evidence, no money path is at risk either way).
#
# WHY A NEW FILE RATHER THAN AN EDIT TO cap9.sh
# ---------------------------------------------
# cap9.sh has now produced committed observations (the A2-3xx series under out/, plus
# req/ and out/*.req.sha256 wire-byte records). T114's standing ruling forbids editing
# a script that produced committed evidence -- same rule cap9.sh itself invoked against
# cap8.sh -- so this is the next link in that chain: cap.sh -> cap8.sh -> cap9.sh ->
# cap10.sh (see SUPERSEDED.txt).
#
# T236 additionally VERIFIED, not merely assumed, that editing cap9.sh in place was
# unsafe by this rig's OWN mechanism, not just by convention: MANIFEST.sha256 hashes
# cap9.sh's exact bytes as part of "the rig" (manifest.py's own stated scope, extended
# there by A2-5 for D-3(iii) specifically to catch an undeclared change to a script that
# produced evidence). That pin is real and verified
# [VERIFIED: sha256 of the on-disk cap9.sh at T236's fork point == the `cap9.sh` line in
# MANIFEST.sha256, both `0444bb32b2ffb2341e3140e4912743bc5d635e3a4b8a1588c0826a9e9fe32c88`],
# so editing cap9.sh in place -- even a one-word, additive-only, no-output-path-touched
# change -- is exactly what that pin exists to catch. Minting a successor is the
# rig's own answer to that, not a judgment call invented here.
#
# The one addition, and nothing else changed: `QUIT` appended to the scratch-dir trap's
# signal list, so `rm -rf "$TMPD"` also runs on SIGQUIT. Every byte cap9.sh writes to
# out/ or req/ on a COMPLETED exchange is unaffected -- the trap only governs behaviour
# on an ABORTED run, which by cap9.sh/cap10.sh's own design (nothing written under out/
# until the exchange completes) never produces a committed observation either way.
#
# Everything else cap9.sh does is carried over verbatim: the required 5th positional
# Idempotency-Key argument (refused if absent -- P-22), `-H "Idempotency-Key: $KEY"` on
# the request and an `idempotency-key:` line in the `.http` record, `--data-binary` (so
# curl does not strip newlines out of the body), out/NAME.req + out/NAME.req.sha256 as
# the exact wire bytes, nothing written under out/ until the exchange completed, a
# non-2xx recorded as data rather than treated as an error, and a transport failure
# naming any pre-existing artefact instead of overwriting it.
#
# `Idempotency-Key` is the pinned oracle's own configured header name
# [VERIFIED: fineract-provider/src/main/resources/application.properties:179 and :857,
# `fineract.idempotency-key-header-name=${FINERACT_IDEMPOTENCY_KEY_HEADER_NAME:Idempotency-Key}`],
# and it is read at IdempotencyStoreFilter.java:72 via
# FineractProperties.getIdempotencyKeyHeaderName().
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"

NAME=${1-}; METHOD=${2-}; RPATH=${3-}; BODY=${4-}; KEY=${5-}
[ -n "$NAME" ] && [ -n "$METHOD" ] && [ -n "$RPATH" ] || { echo "usage: cap10.sh NAME METHOD PATH BODYFILE IDEMPOTENCY_KEY" >&2; exit 2; }
[ -n "$KEY" ] || { echo "REFUSING: cap10.sh exists to send an Idempotency-Key and none was given. A probe that sends no key proves nothing about idempotency." >&2; exit 2; }

OUT="$DIR/out/$NAME.json"
STATUS="$DIR/out/$NAME.status"
HTTP="$DIR/out/$NAME.http"
REQ="$DIR/out/$NAME.req"
REQSHA="$DIR/out/$NAME.req.sha256"

if [ -n "$BODY" ] && [ ! -f "$DIR/$BODY" ]; then
  echo "REFUSING: body file $BODY does not exist — nothing to send and nothing to record." >&2
  exit 2
fi

TMPD=$(mktemp -d "${TMPDIR:-/tmp}/cap10.XXXXXX")
trap 'rm -rf "$TMPD"' EXIT HUP INT TERM QUIT
TMPBODY="$TMPD/body"
TMPREQ="$TMPD/req"

if [ -n "$BODY" ]; then
  cp "$DIR/$BODY" "$TMPREQ"
fi

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

rc=0
if [ -n "$BODY" ]; then
  code=$(curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -H "$CT" -H "Idempotency-Key: $KEY" \
              --data-binary @"$TMPREQ" -o "$TMPBODY" -w '%{http_code}') || rc=$?
else
  code=$(curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -H "Idempotency-Key: $KEY" \
              -o "$TMPBODY" -w '%{http_code}') || rc=$?
fi

if [ "$rc" -ne 0 ]; then
  echo "TRANSPORT FAILURE (curl rc=$rc) for $NAME — NO OBSERVATION WAS MADE." >&2
  echo "  NOTHING was written under out/ for $NAME by this fire." >&2
  for f in "$HTTP" "$OUT" "$STATUS" "$REQ" "$REQSHA"; do
    if [ -e "$f" ]; then
      echo "  PRE-EXISTING from an EARLIER fire, left intact, NOT this fire's output: out/${f##*/}" >&2
    fi
  done
  if [ -e "$HTTP" ]; then
    echo "  that earlier artefact's own captured-at-utc: $(sed -n 's/^captured-at-utc: //p' "$HTTP")" >&2
  fi
  exit 1
fi

if [ -n "$BODY" ]; then
  if command -v shasum >/dev/null 2>&1; then
    SHA=$(shasum -a 256 "$TMPREQ" | awk '{print $1}')
  else
    SHA=$(sha256sum "$TMPREQ" | awk '{print $1}')
  fi
  BYTES=$(wc -c < "$TMPREQ" | tr -d ' ')
  mv "$TMPREQ" "$REQ"
  printf '%s  %s\n' "$SHA" "$NAME.req" > "$REQSHA"
fi
mv "$TMPBODY" "$OUT"
{
  echo "$METHOD $RPATH"
  echo "Fineract-Platform-TenantId: gerege"
  echo "Authorization: Basic <mifos:password>"
  echo "Idempotency-Key: $KEY"
  if [ -n "$BODY" ]; then
    echo "Content-Type: application/json"
    echo "body-file: $BODY"
    echo "body-wire-bytes-artefact: $NAME.req"
    echo "body-sha256: $SHA"
    echo "body-bytes: $BYTES"
  else
    echo "body: <none>"
  fi
  echo "captured-at-utc: $TS"
} > "$HTTP"
echo "$code" > "$STATUS"
printf '%-44s HTTP %s\n' "$NAME" "$code"
