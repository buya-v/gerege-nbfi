#!/bin/sh
# T36 — T22 P1-11 second clause: put the EMI re-adjust-loop candidates to the ORACLE.
#
# Candidates were SELECTED by t36_emiloop_search.py (T22's audited re-derivation, which does
# NOT implement the loop).  Nothing is authored here: each principal is sent to the running
# server and whatever it answers is the observation.
#
# Payloads are built by TEXT substitution of the integer `principal` in the committed B-01
# calc request, so no JSON round-trip can turn a money literal into a binary float.
set -eu
D=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$D/.." && pwd)
O=$D/out/emiloop
REQ=$D/req-emiloop
mkdir -p "$O" "$REQ"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

CANARY_REQ="$W/t22-audit/req/calc-pmode2-gerege.json" sh "$D/preconditions.sh" gerege > "$O/preconditions.txt"
if grep -q '^  FAIL' "$O/preconditions.txt"; then
  echo "ABORT: preconditions breached" >&2; cat "$O/preconditions.txt" >&2; exit 1
fi
echo "preconditions: ALL PASS"

# 1200000 = the B-01 control (residual +-0.03, loop cannot fire)
# 1200033 / 1200045 = ENTERS the loop but is predicted NOT to adopt (difference does not shrink)
# the rest are predicted to ADOPT a changed EMI
for P in 1200000 1200001 1200004 1200027 1200033 1200039 1200045 1200054 1200189; do
  sed "s/\"principal\": 1200000,/\"principal\": $P,/" \
      "$W/req/calc-B-01-baseline.json" > "$REQ/calc-emiloop-$P.json"
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
              -d @"$REQ/calc-emiloop-$P.json" -o "$O/emiloop-$P-raw.json" -w '%{http_code}')
  echo "  principal $P  HTTP $code  -> out/emiloop/emiloop-$P-raw.json"
  [ "$code" = "200" ] || { echo "CAPTURE FAILED: HTTP $code is an ERROR BODY, not a capture" >&2; exit 1; }
done
# T99 (sweep for the F-2 shape): the digests printed into this transcript are evidence, so they are
# computed by the hardened instrument — absolute-path tools, known-answer tested, two independent
# implementations required to agree — rather than by a bare `shasum` whose meaning $PATH decides.
. "$D/sha256.sh"
sha256_init || { echo "REFUSED: $SHA256_ERROR" >&2; exit 1; }
echo "# sha256 by $SHA256_TOOLS"
for f in "$O"/emiloop-*-raw.json; do
  sha256_file "$f" || { echo "REFUSED: $SHA256_ERROR" >&2; exit 1; }
  printf '%s  %s\n' "$SHA256_RESULT" "$f"
done
