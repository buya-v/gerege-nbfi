#!/usr/bin/env bash
# capture-state.sh LOAN_ID LABEL — OH-CHGCAP-BD
#
# Capture the three citeable read-backs for one loan at one step, plus read-only
# SQL corroboration:
#   out/loan-LID-LABEL-detail-raw.json          GET /loans/LID?associations=all
#   out/loan-LID-LABEL-transactions-raw.json    GET /loans/LID/transactions
#   out/loan-LID-LABEL-journalentries-raw.json  GET /journalentries?loanId=LID
#   out/db-LABEL.txt                             read-only SELECTs
# Each GET writes a .status companion; a non-200 is recorded, never fatal.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan-charge-partial-waive-repaid

LID="${1:?usage: capture-state.sh LOAN_ID LABEL}"
LABEL="${2:?usage: capture-state.sh LOAN_ID LABEL}"

ohs_get "loan-$LID-$LABEL-detail"          "/loans/$LID?associations=all"
ohs_get "loan-$LID-$LABEL-transactions"    "/loans/$LID/transactions"
ohs_get "loan-$LID-$LABEL-journalentries"  "/journalentries?loanId=$LID&limit=120"
bash "$(dirname "$0")/db-evidence.sh" "$LID" "$LABEL" >/dev/null
echo "captured state $LABEL for loan $LID"
