#!/bin/sh
# T276: re-issue the five REFUSAL captures from their COMMITTED WIRE BYTES and diff the
# response against what T275 recorded. A refusal is deterministic and persists nothing
# (T275 FINDING 7 says a refused create still burns an id but rolls the row back), so
# unlike the successful creates these MUST replay byte-identically if they are real.
set -u
S=/tmp/t276/reissue
C=/tmp/t276/t275tree/.softhouse/capture/tierA-a2

for pair in \
  "A2-526-prod-fee-income-expense-account POST /loanproducts" \
  "A2-540-prod-writeoff-reason-dangling POST /loanproducts" \
  "A2-541-prod-writeoff-reason-dangling-nonexpense POST /loanproducts" \
  "A2-542-prod-chargeoff-reason-dangling POST /loanproducts" \
  "A2-543-prod-chargeoff-reason-dangling-nonexpense POST /loanproducts" ; do
  set -- $pair
  N=$1; M=$2; P=$3
  # send THE COMMITTED WIRE BYTES, not the req/ file the recipe names
  cp "$C/out/$N.req" "$S/wire.json"
  sh "$S/cap8.sh" "T276-$N" "$M" "$P" "wire.json" >/dev/null 2>&1
  echo "=== $N ==="
  echo "  committed status: $(cat "$C/out/$N.status")   re-issued status: $(cat "$S/out/T276-$N.status")"
  if diff -q "$C/out/$N.json" "$S/out/T276-$N.json" >/dev/null 2>&1; then
    echo "  RESPONSE BYTE-IDENTICAL"
  else
    echo "  RESPONSE DIFFERS:"
    diff "$C/out/$N.json" "$S/out/T276-$N.json" | head -20
  fi
done
