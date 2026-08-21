#!/bin/sh
# A2-7 leg 4 — is the creation-mandatory set enforced anywhere OTHER than creation?
#
# Source fact that motivates the probe [fineract@426a23544
# fineract-provider/src/main/java/org/apache/fineract/portfolio/loanproduct/
# serialization/LoanProductDataValidator.java]:
#   validateForCreate  :664 .. :712   nine accounts .notNull()
#                      :765 .. :781   three receivables .notNull() when accrual
#   validateForUpdate  :1333          entry point
#                      :1796          accountingRule itself .ignoreIfNull()
#                      :1818 .. :1878 EVERY account param .ignoreIfNull()
#
# So on the update path nothing is mandatory. This flips product 46 from CASH BASED to
# ACCRUAL PERIODIC supplying none of the three receivable accounts, then reads the
# product back. Whatever the oracle does is the observation; the probe predicts nothing.
DIR=$(cd "$(dirname "$0")" && pwd)

sh "$DIR/cap.sh" A2-240-update-cash-to-accrual PUT /loanproducts/46 \
   req/a2-7-upd-240-cash-to-accrual.json || exit 1
cat "$DIR/out/A2-240-update-cash-to-accrual.json"; echo

sh "$DIR/cap.sh" A2-241-read-product-after-accrual-switch GET /loanproducts/46 || exit 1

# --- the control. Same endpoint, same product, still no account parameters; the ONLY
# difference from A2-240 is that the accounting rule is not changed.
sh "$DIR/cap.sh" A2-242-update-no-rule-change PUT /loanproducts/46 \
   req/a2-7-upd-242-no-rule-change.json || exit 1
cat "$DIR/out/A2-242-update-no-rule-change.json"; echo

sh "$DIR/cap.sh" A2-243-read-product-after-no-rule-change GET /loanproducts/46 || exit 1
