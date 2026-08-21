#!/bin/sh
# A2-7 leg 3 — MEASURE whether the set of GL accounts a loan product must carry AT
# CREATION is the same set the POSTING paths require AT RUNTIME.
#
# THE INSTRUMENT. Product A2-210 was created carrying EXACTLY the nine slots that
# LoanProductDataValidator marks notNull() for cash accounting, and NONE of the slots it
# marks ignoreIfNull() — in particular goodwillCreditAccountId and
# chargeOffExpenseAccountId are absent. out/A2-211-read-product-nine-mandatory.json is
# the read-back that shows the mapping the oracle actually stored. Every probe below
# then drives ONE runtime posting path over that product and records what the oracle
# says. A 404 error.msg.productToAccountMapping.not.found naming a slot is a direct
# observation that the runtime path REQUIRES a slot creation did not.
#
# This measures. It does not infer: no probe's expected answer is written down anywhere,
# and a refusal is recorded exactly as a success is.
#
# Every cap.sh call carries `|| exit 1` (A2-5 fix for D-2): a transport failure must stop
# the batch rather than let the next step read stale bytes.
#
# LIMITATION, stated because it is not obvious: cap.sh sends no `Idempotency-Key`. The
# Gerege non-negotiable binds money-movement POSTs in OUR implementation; this rig
# reproduces the oracle's own wire format and every existing A2 money POST
# (A2-084/085/086/091b/092) was captured the same way. Adding the header here would have
# changed the transport under an existing corpus. Carried to the handoff as a follow-up.
DIR=$(cd "$(dirname "$0")" && pwd)

python3 "$DIR/resolve7.py" "$DIR/req/a2-7-loan-220.json" \
        "$DIR/out/A2-210-create-cash-nine-mandatory.json" resourceId \
        "$DIR/req/a2-7-loan-220-resolved.json" || exit 1

sh "$DIR/cap.sh" A2-220-loan-on-nine-mandatory POST /loans req/a2-7-loan-220-resolved.json || exit 1
cat "$DIR/out/A2-220-loan-on-nine-mandatory.json"; echo

LID=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("loanId",""))' \
      "$DIR/out/A2-220-loan-on-nine-mandatory.json")
echo "observed loanId = ${LID:-<none>}"
[ -n "$LID" ] || { echo "no loan was created — the runtime leg cannot run" >&2; exit 1; }

sh "$DIR/cap.sh" A2-221-approve-loan   POST "/loans/$LID?command=approve"  req/a2-7-approve-221.json  || exit 1
sh "$DIR/cap.sh" A2-222-disburse-loan  POST "/loans/$LID?command=disburse" req/a2-7-disburse-222.json || exit 1
sh "$DIR/cap.sh" A2-223-je-after-disburse GET "/journalentries?loanId=$LID&limit=50" || exit 1

# --- probe 1: CHARGE_OFF_EXPENSE. ignoreIfNull() at creation, UNMAPPED on this product.
sh "$DIR/cap.sh" A2-224-chargeoff-unmapped POST "/loans/$LID/transactions?command=charge-off" \
   req/a2-7-chargeoff-224.json || exit 1
cat "$DIR/out/A2-224-chargeoff-unmapped.json"; echo

# --- probe 2: GOODWILL_CREDIT. ignoreIfNull() at creation, UNMAPPED on this product.
sh "$DIR/cap.sh" A2-225-goodwillcredit-unmapped POST "/loans/$LID/transactions?command=goodwillCredit" \
   req/a2-7-goodwill-225.json || exit 1
cat "$DIR/out/A2-225-goodwillcredit-unmapped.json"; echo

# --- did the two refused probes leave the loan alone?
sh "$DIR/cap.sh" A2-225b-loan-state-after-refusals GET "/loans/$LID" || exit 1

# --- probe 3: an ordinary repayment. Uses only slots in the mandatory set.
sh "$DIR/cap.sh" A2-226-repayment POST "/loans/$LID/transactions?command=repayment" \
   req/a2-7-repayment-226.json || exit 1
cat "$DIR/out/A2-226-repayment.json"; echo
sh "$DIR/cap.sh" A2-227-je-after-repayment GET "/journalentries?loanId=$LID&limit=50" || exit 1

# --- probe 4: write-off. LOSSES_WRITTEN_OFF is mandatory at creation and mapped here.
sh "$DIR/cap.sh" A2-228-writeoff POST "/loans/$LID?command=writeoff" req/a2-7-writeoff-228.json || exit 1
cat "$DIR/out/A2-228-writeoff.json"; echo
sh "$DIR/cap.sh" A2-229-je-after-writeoff GET "/journalentries?loanId=$LID&limit=80" || exit 1

# --- probe 5: recovery payment. INCOME_FROM_RECOVERY is mandatory at creation and mapped.
sh "$DIR/cap.sh" A2-230-recoverypayment POST "/loans/$LID/transactions?command=recoverypayment" \
   req/a2-7-recovery-230.json || exit 1
cat "$DIR/out/A2-230-recoverypayment.json"; echo
sh "$DIR/cap.sh" A2-231-je-after-recovery GET "/journalentries?loanId=$LID&limit=80" || exit 1
