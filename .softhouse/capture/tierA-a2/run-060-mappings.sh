#!/bin/sh
# Product-to-account-mapping creates. Mixed valid/invalid on purpose:
# each refusal is an observation, so this does not stop on a non-2xx.
DIR=$(cd "$(dirname "$0")" && pwd)
for n in prod-060-cash-with-channel-override prod-061-cash-no-override \
         prod-062-map-header-account prod-063-map-wrong-type \
         prod-064-cash-no-mappings prod-065-map-missing-account \
         prod-066-bad-paymenttype prod-067-duplicate-channel \
         prod-068-accrual-missing-receivables prod-069-accrual-complete; do
  sh "$DIR/cap.sh" "A2-${n}" POST /loanproducts "req/$n.json" || exit 1
  printf '   -> %s\n' "$(head -c 260 "$DIR/out/A2-${n}.json")"
done
