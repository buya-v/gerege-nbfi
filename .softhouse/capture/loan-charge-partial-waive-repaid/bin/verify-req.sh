#!/usr/bin/env bash
# verify-req.sh — OH-CHGCAP-BD
#
# Byte-stability guard for every committed request body. Money policy: in
# anything WE write, money is an integer number of minor units, and no body may
# carry a JSON number token with a fractional part. Decimal amounts that must be
# sent (the charge amounts and every repayment amount) are sent as JSON STRINGS,
# which parse_float never sees, so they survive a binary-double round trip
# byte-for-byte ("123.45" stays "123.45").
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
CTX_DIR=".softhouse/capture/loan-charge-partial-waive-repaid"

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
