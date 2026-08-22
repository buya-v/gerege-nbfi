#!/bin/sh
# cap8.sh NAME METHOD PATH [BODYFILE]
#
# T163 — the P-25-clean successor to cap.sh.  One observation = one HTTP exchange,
# recorded verbatim, INCLUDING THE BYTES THAT WENT OVER THE WIRE.
#
# WHY THIS FILE EXISTS INSTEAD OF AN EDIT TO cap.sh
# --------------------------------------------------
# cap.sh produced 441 committed observations under out/, every one hashed in
# MANIFEST.sha256.  T114's standing ruling forbids editing a script that produced committed
# evidence; the change goes in a scratch copy so the committed captures stay re-derivable
# from the script that actually made them.  cap.sh is UNCHANGED by T163 and superseded by
# this file.  Everything A2-5 fixed for D-2 is carried over verbatim and is re-proven here
# — see prove-cap8-wire-bytes.py, which re-runs A2-5's transport arguments against THIS
# script rather than assuming they survived the copy.
#
# WHAT T163 ADDS, AND THE DEFECT IT CLOSES
# -----------------------------------------
# A2-11 found that resolve7.py reshapes money literals in the body POSTed to the reference
# oracle.  The reason that survived undetected is structural, and it outlives the one
# script: NOTHING IN THIS CORPUS RECORDS THE BYTES THAT ACTUALLY WENT OVER THE WIRE.
# cap.sh's `.http` record writes `body-file: req/foo.json` — a POINTER to a file that any
# later step may rewrite, and which is not even what curl sent.  A reviewer can therefore
# diff what came BACK, and cannot diff what was SENT.
#
#   1. `--data-binary @FILE` replaces `-d @FILE`.  With `-d`, curl STRIPS carriage returns
#      and newlines out of a file body, so the bytes on the wire are NOT the bytes in the
#      file and no artefact could have been byte-exact while `-d` was in use.  MEASURED,
#      not assumed: prove-cap8-wire-bytes.py runs both flags against a local HTTP server
#      that records what it received.  (This changes the wire form: the trailing newline
#      of a body file is no longer stripped.  It is a whitespace-only change to a JSON
#      document and cannot alter parsed content, but it IS a transport change, so cap8.sh
#      is a new script and no existing capture is re-taken under it.)
#
#   2. out/NAME.req  — the exact bytes sent, committed alongside out/NAME.json.
#      out/NAME.req.sha256 — its digest, so a manifest covers it and drift is detectable.
#      The `.http` record carries `body-sha256:` and `body-bytes:` so the three artefacts
#      cross-check each other.  The `.req` is copied from the body file at the moment of
#      the send and is written only after the exchange completed, so it can never
#      disagree with the `.json` it sits beside.
#
# A refusal is still an observation (a non-2xx does not fail this script); a TRANSPORT
# failure is still an error that writes NOTHING under out/ — .req included.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"

NAME=${1-}; METHOD=${2-}; RPATH=${3-}; BODY=${4-}
[ -n "$NAME" ] && [ -n "$METHOD" ] && [ -n "$RPATH" ] || { echo "usage: cap8.sh NAME METHOD PATH [BODYFILE]" >&2; exit 2; }

OUT="$DIR/out/$NAME.json"
STATUS="$DIR/out/$NAME.status"
HTTP="$DIR/out/$NAME.http"
REQ="$DIR/out/$NAME.req"
REQSHA="$DIR/out/$NAME.req.sha256"

if [ -n "$BODY" ] && [ ! -f "$DIR/$BODY" ]; then
  echo "REFUSING: body file $BODY does not exist — nothing to send and nothing to record." >&2
  exit 2
fi

TMPD=$(mktemp -d "${TMPDIR:-/tmp}/cap8.XXXXXX")
# T216: QUIT added alongside EXIT HUP INT TERM.  Per T156/T168
# (.softhouse/capture/pathb/t149/prove-exit-trap.py), bash does not run the EXIT trap
# for an untrapped SIGQUIT (unlike SIGPIPE/SIGUSR1/SIGALRM) -- without this, Ctrl-\
# during a capture leaks this $TMPD scratch dir instead of cleaning it up.
trap 'rm -rf "$TMPD"' EXIT HUP INT TERM QUIT
TMPBODY="$TMPD/body"
TMPREQ="$TMPD/req"

# The wire bytes are snapshotted BEFORE the send and moved into place only AFTER it
# completed, so out/NAME.req is exactly what out/NAME.json is a response to.
if [ -n "$BODY" ]; then
  cp "$DIR/$BODY" "$TMPREQ"
fi

# Stamped before the request is issued, written only if the request completed.
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

rc=0
if [ -n "$BODY" ]; then
  code=$(curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -H "$CT" \
              --data-binary @"$TMPREQ" -o "$TMPBODY" -w '%{http_code}') || rc=$?
else
  code=$(curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -o "$TMPBODY" -w '%{http_code}') || rc=$?
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

# The exchange completed. Commit the observation: wire bytes, body, request record, status.
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
