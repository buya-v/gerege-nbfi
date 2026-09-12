#!/usr/bin/env bash
# Run extract-product-mappings.py for every loan product named in this replay's
# loan read-backs.  FEIGN must be assigned before use (see OH-TIERD16-CO lesson).
set -u
cd "$(dirname "$0")"
FEIGN="${FEIGN:-/Users/buv/fineract-tierd/fineract-e2e-tests-runner/build/capture/feign-repayment-p3-mnt.log}"
if [ ! -f "$FEIGN" ]; then echo "FEIGN not found: $FEIGN" >&2; exit 1; fi

# Derive the product names from the loan read-backs (loanProductName).
NAMES="$(python3 - <<'PY'
import glob, json, os
seen = []
for f in sorted(glob.glob('loans/loan-*/*.json')):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    if isinstance(d, dict) and d.get('loanProductName'):
        n = d['loanProductName']
        if n not in seen:
            seen.append(n)
print(' '.join(seen))
PY
)"
echo "products: $NAMES"

# shellcheck disable=SC2086
python3 extract-product-mappings.py "$FEIGN" $NAMES
