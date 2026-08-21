#!/bin/sh
# A2-7 leg 2 — THE deliverable: a loan product created with a full cash-based
# product-to-account mapping, and that mapping READ BACK ACROSS THE CONTRACT BOUNDARY.
#
# WHY this exists. Before this task the A2 corpus contained ELEVEN `POST /loanproducts`
# and ZERO `GET /loanproducts/{id}` (verified by listing the first line of every
# out/*.http). The mappings were read back only from PostgreSQL
# (out/A2-072-db-product-mapping-rows.txt, `SELECT ... FROM acc_product_mapping`).
# A Go port is graded at the ADAPTER CONTRACT, not at the table, so a DB-only read-back
# grades nothing about the shape the boundary emits: which JSON field carries each slot,
# whether the account's type/usage travel with it, and what happens to a mapping whose
# account was retyped underneath it.
#
# A2-210  create the nine-mandatory-slots-only cash product      (the write)
# A2-211  read it back                                           (the read)
# A2-212  read back product 22 — full cash mapping WITH a payment-channel fund-source
#         override, and whose fundSource GL account (id 2) was retyped ASSET -> INCOME
#         after the product was created, by the already-captured A2-111.
# A2-213  read back product 28 — accrual, the twelve-slot mapping.
# A2-214  re-send prod-061's fundSourceAccountId=2 now that account 2 is INCOME. The
#         oracle accepted that exact id as product 23. Whatever it answers now is the
#         observation.
DIR=$(cd "$(dirname "$0")" && pwd)

sh "$DIR/cap.sh" A2-210-create-cash-nine-mandatory POST /loanproducts \
   req/a2-7-prod-210-cash-nine-mandatory.json || exit 1
cat "$DIR/out/A2-210-create-cash-nine-mandatory.json"; echo

PID=$(python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print(d.get("resourceId",""))' \
      "$DIR/out/A2-210-create-cash-nine-mandatory.json")
echo "observed resourceId = ${PID:-<none>}"

if [ -n "$PID" ]; then
  sh "$DIR/cap.sh" A2-211-read-product-nine-mandatory GET "/loanproducts/$PID" || exit 1
fi

sh "$DIR/cap.sh" A2-212-read-product22-channel-override GET /loanproducts/22 || exit 1
sh "$DIR/cap.sh" A2-213-read-product28-accrual          GET /loanproducts/28 || exit 1

sh "$DIR/cap.sh" A2-214-create-fundsource-retyped POST /loanproducts \
   req/a2-7-prod-214-fundsource-retyped-account.json || exit 1
cat "$DIR/out/A2-214-create-fundsource-retyped.json"; echo
