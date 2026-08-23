#!/bin/sh
# cap.sh NAME METHOD PATH [BODYFILE]
#
# One observation = one HTTP exchange, recorded verbatim.
#
# COPIED for T294 from .softhouse/capture/t287-closure-refusals/cap.sh, which T287 had adapted
# from .softhouse/capture/tierA-a2/cap.sh and cap8.sh. Only this header block differs; the
# executable body is byte-identical (T289 F-T289-6 endorsed the bodyless-request fix below,
# and re-deriving it here would risk losing it). Copied rather than sourced for the same
# reason env.sh is. It keeps the three hard-won properties:
#
#   1. A NON-2xx IS NOT AN ERROR. In T287 the refusal IS the observation -- the whole task
#      is to record what the oracle says NO to and in exactly what words. The status is
#      recorded as data (out/NAME.status) and never used to discard the body.
#      What IS an error is a transport failure (curl exit != 0): that means NO observation
#      was made, and nothing is written under out/.
#
#   2. NOTHING under out/ is written until the exchange completed (A2 defect D-2). The body
#      lands in a temp dir and is moved into place only after curl returns 0, so a failed
#      fire can never stamp a fresh captured-at-utc on stale bytes. Pre-existing artefacts
#      from an earlier fire are NAMED and LEFT INTACT, never overwritten.
#
#   3. THE WIRE BYTES ARE SNAPSHOTTED, NOT POINTED AT (A2 defect D-1). out/NAME.req holds a
#      copy of the exact bytes handed to curl, with its own sha256, so a later edit to
#      req/ cannot silently invalidate the recipe. A `body-file:` pointer is not evidence.
#
# curl is given --data-binary, not -d: -d strips newlines and would mean the committed
# out/NAME.req is not what went on the wire.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"

NAME=${1-}; METHOD=${2-}; RPATH=${3-}; BODY=${4-}
[ -n "$NAME" ] && [ -n "$METHOD" ] && [ -n "$RPATH" ] || { echo "usage: cap.sh NAME METHOD PATH [BODYFILE]" >&2; exit 2; }
if [ -n "$BODY" ] && [ ! -f "$DIR/$BODY" ]; then
  echo "REFUSING: $BODY does not exist -- nothing to send and nothing to record." >&2; exit 2
fi

OUT="$DIR/out/$NAME.json"
STATUS="$DIR/out/$NAME.status"
HTTP="$DIR/out/$NAME.http"
REQ="$DIR/out/$NAME.req"
REQSHA="$DIR/out/$NAME.req.sha256"

TMPD=$(mktemp -d "${TMPDIR:-/tmp}/cap294.XXXXXX")
# QUIT alongside EXIT HUP INT TERM: bash does not run the EXIT trap for an untrapped
# SIGQUIT, so Ctrl-\ mid-capture would otherwise leak this scratch dir (T216/T236).
trap 'rm -rf "$TMPD"' EXIT HUP INT TERM QUIT
TMPBODY="$TMPD/body"
TMPREQ="$TMPD/req"

# Snapshot the request bytes BEFORE the request is issued.
#
# A BODYLESS REQUEST GETS NO .req ARTEFACT AT ALL -- it is not an empty request body, there
# is no request body. The first version of this script wrote a zero-byte out/NAME.req for
# every GET, and that is not a cosmetic difference: the repo-wide capture guard
# .softhouse/capture/lib/check_wire_float_roundtrip.py derives its population as
# "*.json under a req/ dir, plus *.req" and json.loads() a zero-byte file, so three empty
# GET artefacts REFUSED the whole capture-tree guard with
#     JSONDecodeError: Expecting value: line 1 column 1 (char 0)
# across every rig in the repository, not just this one. Measured, not theorised -- that is
# the exact failure this rig produced before the fix.
if [ -n "$BODY" ]; then cp "$DIR/$BODY" "$TMPREQ"; fi

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

rc=0
if [ -n "$BODY" ]; then
  code=$(curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -H "$CT" \
              --data-binary @"$TMPREQ" -o "$TMPBODY" -w '%{http_code}') || rc=$?
else
  code=$(curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -o "$TMPBODY" -w '%{http_code}') || rc=$?
fi

if [ "$rc" -ne 0 ]; then
  echo "TRANSPORT FAILURE (curl rc=$rc) for $NAME -- NO OBSERVATION WAS MADE." >&2
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

# The exchange completed. Commit the observation.
mv "$TMPBODY" "$OUT"

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

{
  echo "$METHOD $RPATH"
  echo "Fineract-Platform-TenantId: gerege"
  echo "Authorization: Basic <mifos:password>"
  if [ -n "$BODY" ]; then
    echo "Content-Type: application/json"
    echo "request-source-file: $BODY"
    echo "request-bytes-artefact: $NAME.req"
    echo "request-sha256: $SHA"
    echo "request-bytes: $BYTES"
  else
    echo "request-body: NONE (bodyless request -- no .req artefact is written, by design)"
  fi
  echo "captured-at-utc: $TS"
} > "$HTTP"
echo "$code" > "$STATUS"
printf '%-46s HTTP %s\n' "$NAME" "$code"
