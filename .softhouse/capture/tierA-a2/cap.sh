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
# observation was made at all, and the script exits non-zero having written NOTHING
# under out/, so nothing gets committed.
#
# ---------------------------------------------------------------------------
# A2-5 fix for D-2 (P-22 class: a handler that cannot fire).
#
# The previous version wrote out/NAME.http FIRST (with a fresh captured-at-utc), then
# ran `code=$(curl …)` followed by `rc=$?`.  Under `set -e` the shell terminated at the
# failing assignment, so `rc=$?`, the diagnostic and the `rm -f "$OUT"` were
# UNREACHABLE — a stale body and a stale status survived under a FRESH captured-at-utc.
# That is manufactured oracle evidence, the worst artefact this rig can produce.
#
# Two changes, both driven RED against the real pre-fix bytes in
# prove-cap-transport-red.py (transcript: RED-GREEN-D2-cap-transport.txt):
#
#   1. `|| rc=$?` keeps the failing curl inside an AND-OR list, which `set -e` does not
#      treat as a failing command.  Reachability is PROVEN, not reasoned: the prover
#      runs this script under sh, bash, dash, zsh, ksh and under -e / -u / -eu /
#      -o pipefail, on both the body and the no-body branch, and asserts the handler
#      fires in every combination.
#   2. NOTHING under out/ is written until the exchange completed.  The body lands in a
#      temp dir; on curl rc=0 it is moved into place and only then are .http and .status
#      written.  A failed fire therefore cannot stamp a fresh timestamp on old bytes.
#
# Pre-existing artefacts from an EARLIER fire are deliberately NOT deleted: they are
# evidence, they are covered by MANIFEST.sha256, and deleting them would both destroy
# evidence and turn every failed retry into a manifest breakage.  Instead the handler
# NAMES them and prints the captured-at-utc they actually carry, so no caller can
# mistake them for this fire's observation.  Only this fire's own partial output (the
# temp dir) is removed.
#
# Callers: run-*.sh now use `|| exit 1` on every cap.sh call.  Those loops are
# deliberately not `set -e` (a refusal is an observation), so without that the batch
# would carry on past a transport failure and `cat` the stale body as if it had just
# been observed.  That laundering is driven RED in the same prover.
# ---------------------------------------------------------------------------
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"

NAME=${1-}; METHOD=${2-}; RPATH=${3-}; BODY=${4-}
[ -n "$NAME" ] && [ -n "$METHOD" ] && [ -n "$RPATH" ] || { echo "usage: cap.sh NAME METHOD PATH [BODYFILE]" >&2; exit 2; }

OUT="$DIR/out/$NAME.json"
STATUS="$DIR/out/$NAME.status"
HTTP="$DIR/out/$NAME.http"

TMPD=$(mktemp -d "${TMPDIR:-/tmp}/cap.XXXXXX")
trap 'rm -rf "$TMPD"' EXIT HUP INT TERM
TMPBODY="$TMPD/body"

# Stamped before the request is issued, written only if the request completed.
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

rc=0
if [ -n "$BODY" ]; then
  code=$(curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -H "$CT" \
              -d @"$DIR/$BODY" -o "$TMPBODY" -w '%{http_code}') || rc=$?
else
  code=$(curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -o "$TMPBODY" -w '%{http_code}') || rc=$?
fi

if [ "$rc" -ne 0 ]; then
  echo "TRANSPORT FAILURE (curl rc=$rc) for $NAME — NO OBSERVATION WAS MADE." >&2
  echo "  NOTHING was written under out/ for $NAME by this fire." >&2
  for f in "$HTTP" "$OUT" "$STATUS"; do
    if [ -e "$f" ]; then
      echo "  PRE-EXISTING from an EARLIER fire, left intact, NOT this fire's output: out/${f##*/}" >&2
    fi
  done
  if [ -e "$HTTP" ]; then
    echo "  that earlier artefact's own captured-at-utc: $(sed -n 's/^captured-at-utc: //p' "$HTTP")" >&2
  fi
  exit 1
fi

# The exchange completed. Commit the observation: body, then request record, then status.
mv "$TMPBODY" "$OUT"
{
  echo "$METHOD $RPATH"
  echo "Fineract-Platform-TenantId: gerege"
  echo "Authorization: Basic <mifos:password>"
  if [ -n "$BODY" ]; then
    echo "Content-Type: application/json"
    echo "body-file: $BODY"
  fi
  echo "captured-at-utc: $TS"
} > "$HTTP"
echo "$code" > "$STATUS"
printf '%-44s HTTP %s\n' "$NAME" "$code"
