#!/bin/bash
# T149 — capture the HALF_EVEN arm of the pinned exact tie.
#
# THIS IS NOT A PRODUCTION-REPRESENTATIVE CAPTURE AND NOTHING HERE IS PROMOTABLE.
# It is deliberately taken on the stock `default` tenant, whose c_configuration
# rounding-mode ordinal is 6 (HALF_EVEN) — the reference oracle's own configuration
# default and NOT Gerege's ratified HALF_UP. It exists for exactly one purpose: to be
# the second, OBSERVED arm of the counterfactual carried by the parity vector
# T149-PATHB-TIE, so that the vector's margin is measured against the oracle rather
# than against a model of it.
#
# It cannot go through t36/attest.py, and that is correct rather than a workaround:
# attest.py's gate (capture/lib/attest_gate.py) REFUSES any tenant whose effective
# rounding mode is not HALF_UP, before a single body is fetched. An attestation is a
# claim that the capture was taken at the ratified MathContext, and this one was not.
#
# The request is the committed, digest-pinned canary for the `default` tenant —
# calc-pmode2-default.json, sha256 1461810087… — which differs from the `gerege`
# canary in `productId` alone (10 vs 11). T136 established, and compare-arms.py
# re-establishes on every run, that the two m_product_loan rows are twins across 89
# columns with only `id` differing.
#
# POST /loans?command=calculateLoanSchedule persists nothing.
#
#     bash capture-halfeven-arm.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATHB="$(cd "$HERE/.." && pwd)"
REQ="$PATHB/t22-audit/req/calc-pmode2-default.json"
PINNED_SHA=1461810087c56ba11ae3f37c705f8235fed35020e083c7e5a5beb1a9ac3bf902
OUT="$HERE/out/default-HALF-EVEN-ARM"
BASE=https://localhost:8443/fineract-provider/api/v1

fail() { echo "ABORT: $*" >&2; exit 1; }

# The request is pinned by DIGEST, not by substring — T80 P0-A. A canary matched by
# `grep -qF '"principal": 1162502.5'` also matches 1162502.55, which is NOT a
# half-minor-unit tie and answers 20925.05 under both modes: the assertion would be a
# tautology. Two operands, only one of which a caller can reach.
sha=$(shasum -a 256 "$REQ" | cut -d' ' -f1)
[ "$sha" = "$PINNED_SHA" ] || fail "canary digest mismatch: $sha != $PINNED_SHA — request NOT sent"

mkdir -p "$OUT"
echo default > "$OUT/CAPTURED-FROM-TENANT"
cat > "$OUT/NOT-PRODUCTION-REPRESENTATIVE.txt" <<'EOF'
Taken on tenant `default`, whose effective rounding mode is HALF_EVEN (RoundingMode
ordinal 6). Gerege's ratified tenant parameter is HALF_UP (ordinal 4). NOTHING IN THIS
DIRECTORY IS PROMOTABLE and nothing here carries an attestation, because an attestation
asserts capture at MathContext(19, HALF_UP) and this was not.

It is the OBSERVED counterfactual arm for the parity vector T149-PATHB-TIE.
EOF

code=$(curl -sk -X POST "$BASE/loans?command=calculateLoanSchedule" \
    -H 'Authorization: Basic bWlmb3M6cGFzc3dvcmQ=' \
    -H 'Fineract-Platform-TenantId: default' \
    -H 'Content-Type: application/json' \
    -d @"$REQ" -o "$OUT/pmode2-default-raw.json" -w '%{http_code}')
[ "$code" = 200 ] || fail "HTTP $code — the file in $OUT is an ERROR BODY, not a capture"

# The tenant's configured ordinal, read from the row, so the arm is labelled by what the
# server is rather than by what this script assumes.
ord=$(docker exec fineract-db-1 psql -U root -d fineract_default -At \
        -c "select value from c_configuration where name='rounding-mode';" 2>/dev/null)
[ "$ord" = 6 ] || fail "tenant default c_configuration.rounding-mode is '$ord', expected 6 (HALF_EVEN); this arm is not what it claims"

p1=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]), parse_float=str)['periods'][1]['interestOriginalDue'])" "$OUT/pmode2-default-raw.json")
[ "$p1" = 20925.04 ] || fail "period-1 interest is $p1, expected 20925.04 under HALF_EVEN"

echo "HALF_EVEN arm captured: HTTP $code, tenant default (rounding-mode ordinal $ord),"
echo "  period-1 interest $p1   sha256 $(shasum -a 256 "$OUT/pmode2-default-raw.json" | cut -d' ' -f1)"
