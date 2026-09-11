#!/usr/bin/env bash
# verify-req.sh — OH-WOPAID-AU
#
# Byte-stability guard for every committed request body.
#
# Money policy (rules of evidence): in anything WE write, money is integer minor
# units, and no body may carry a JSON number with a fractional part. A decimal
# JSON token such as 100.00 is routed through a binary double on the way to the
# wire and can come back as 100.0 — the exact defect that reverted a salvage.
#
# This guard fails if any *numeric* JSON token in req/*.json is not an integer.
# Decimal values that must be sent (e.g. a repayment amount) are sent as JSON
# STRINGS, which parse_float never sees.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
CTX_DIR=".softhouse/capture/loan-writeoff-paid-instalment"

fail=0
shopt -s nullglob
for f in "$CTX_DIR"/req/*.json; do
    python3 - "$f" <<'PY' || fail=1
import json, sys
p = sys.argv[1]
b = open(p, 'rb').read()

def no_float(tok):
    raise ValueError('decimal JSON number token %r in %s' % (tok, p))

try:
    json.loads(b, parse_float=no_float)
except ValueError as e:
    print('FAIL', e)
    sys.exit(1)
print('ok  ', p)
PY
done

if [ "$fail" -ne 0 ]; then
    echo "BYTE-STABILITY GUARD FAILED"
    exit 1
fi
echo "all request bodies integer/string only — byte-stable"
