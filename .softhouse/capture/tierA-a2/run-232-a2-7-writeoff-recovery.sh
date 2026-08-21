#!/bin/sh
# A2-7 leg 3b — the two probes leg 3 failed to LAND, retried on the right endpoint.
#
# A2-228 posted writeoff to /loans/{id}?command=writeoff and the oracle answered HTTP 400
# error.msg.query.parameter.value.unsupported. That refusal is kept (it is a real
# observation about the routing, and its `args` list of supported values came back EMPTY,
# which is itself worth having) — it is NOT overwritten. The command exists on the
# TRANSACTIONS sub-resource instead:
# [fineract@426a23544 .../loanaccount/api/LoanTransactionsApiResource.java:591, :663].
#
# A2-230 recoverypayment was on the right endpoint and was refused
# error.msg.loan.account.is.not.written.off because the write-off had not landed. Retried
# here in the correct order.
#
# New ids only; nothing under out/ is rewritten.
DIR=$(cd "$(dirname "$0")" && pwd)

LID=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("loanId",""))' \
      "$DIR/out/A2-220-loan-on-nine-mandatory.json")
echo "loanId from the committed A2-220 observation = ${LID:-<none>}"
[ -n "$LID" ] || exit 1

sh "$DIR/cap.sh" A2-232-writeoff-on-transactions POST "/loans/$LID/transactions?command=writeoff" \
   req/a2-7-writeoff-228.json || exit 1
cat "$DIR/out/A2-232-writeoff-on-transactions.json"; echo

sh "$DIR/cap.sh" A2-233-je-after-writeoff GET "/journalentries?loanId=$LID&limit=80" || exit 1

sh "$DIR/cap.sh" A2-234-recoverypayment-after-writeoff POST \
   "/loans/$LID/transactions?command=recoverypayment" req/a2-7-recovery-230.json || exit 1
cat "$DIR/out/A2-234-recoverypayment-after-writeoff.json"; echo

sh "$DIR/cap.sh" A2-235-je-after-recovery GET "/journalentries?loanId=$LID&limit=80" || exit 1
