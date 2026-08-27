#!/bin/sh
# A2-26 / group F -- the two mandatory CASH slots the corpus still cannot distinguish.
#
# After group C, seven of the nine mandatory cash slots on product 55 have received a
# journal entry. Two have not, on ANY product, in the whole corpus:
#
#   GOODWILL_CREDIT (13)  -- gl 14, mapped on product 55 and never posted to.
#                            A2-225 observed a 404 for this slot, but that was on product
#                            46, which does NOT map it. A product that DOES map it has
#                            never been driven down this path.
#   OVERPAYMENT     (11)  -- gl 6, mapped on every A2 product and never posted to. It
#                            needs a repayment LARGER than the outstanding balance, and
#                            every repayment in the corpus is smaller.
#
# Loan 7 is used because it is the only loan on a product the reference oracle would
# still accept today (G-10(c), proven at A2-315). Its outstanding at A2-339 was
# 949,848.24 -- principal 929,549.42 + interest 20,298.82, read from the capture, not
# assumed -- so a repayment of 1,000,000 must overpay. The exact size of the overpayment
# is whatever the oracle computes; nothing here predicts it.
#
# Both are money-movement POSTs and both are recorded whatever the oracle answers.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"
LID=7

sh "$C" A2-380-goodwill-credit POST "/loans/$LID/transactions?command=goodwillCredit" \
   req/a2-26-goodwill.json || exit 1
cat "$DIR/out/A2-380-goodwill-credit.json"; echo
sh "$C" A2-381-je-after-goodwill GET "/journalentries?loanId=$LID&limit=100" || exit 1

sh "$C" A2-382-repayment-overpay POST "/loans/$LID/transactions?command=repayment" \
   req/a2-26-repayment-overpay.json || exit 1
cat "$DIR/out/A2-382-repayment-overpay.json"; echo
sh "$C" A2-383-je-after-overpay GET "/journalentries?loanId=$LID&limit=100" || exit 1
sh "$C" A2-384-loan-state-after-overpay GET "/loans/$LID?associations=all" || exit 1
