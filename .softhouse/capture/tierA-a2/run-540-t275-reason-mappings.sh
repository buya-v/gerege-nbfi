#!/bin/sh
# T275 / GROUP C -- REASON MAPPINGS: referential integrity, and the ORDER of two rules.
#
# CAPTURE-PLAN.md §5 excluded three rows here. This run takes the part of them that needs
# NO FIXTURE and leaves the rest excluded and named:
#
#   §5 "chargeOffReasonToExpenseAccountMappings, writeOffReasonsToExpenseMappings --
#       need m_code_value code values seeded first."
#       -> the RESOLVING case (a mapping that points at a real reason) is still EXCLUDED.
#          out/A2-520-db-fixtures.txt shows m_code rows `WriteOffReasons` and
#          `ChargeOffReasons` EXIST with ZERO m_code_value rows under them.
#
#   §5 "`write_off_reason_id` having no FK -- needs the write-off-reason fixture to probe
#       a dangling id."
#       -> THIS IS TAKEN HERE, and §5's stated blocker does not apply: a DANGLING id needs
#          no fixture by definition. The fixture would be needed to make the id RESOLVE,
#          which is the opposite probe.
#
#   §5 "'must be an Expense GL account' for charge-off / write-off -- blocked on the same
#       fixture."
#       -> PARTIALLY TAKEN. Whether that rule fires can be observed even with a dangling
#          reason id, because two rules are in play at once and which message comes back
#          reveals their ORDER. That ordering fact is not obtainable from a seeded fixture
#          at all -- it needs exactly this "both wrong" input.
#
# WHY THE ORDER MATTERS TO A PORT. §4.5 already showed this oracle's delete guards have a
# specific precedence and that one guard is missing entirely, escaping to a raw PostgreSQL
# constraint message. The same class of question applies here: a port that validates the
# account type first, where the oracle validates the reason first, returns a DIFFERENT
# error code and message for the same request, and diverges on the wire even though both
# refuse.
#
# THE DDL FACT THIS TESTS AGAINST, measured in the same fire (out/A2-520-db-fixtures.txt):
# acc_product_mapping.charge_off_reason_id, .capitalized_income_classification_id and
# .buydown_fee_classification_id each carry an FK to m_code_value. `write_off_reason_id`
# carries NONE. So on the write-off side the ONLY referential integrity available is the
# application's; on the charge-off side there is a database backstop as well. Two probes,
# one per side, because the two are structurally different and could well answer
# differently.
#
# 999999 is dangling under EITHER code, since neither code has any values at all.
#
# No expected status is written down. A 200 -- which would prove app-only integrity is
# ABSENT on the write-off side -- and a 4xx are recorded identically.
#
# Product configuration only; no money moves; cap8.sh is the correct instrument.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"
Q="$DIR/capsql.sh"

echo "== T275 group C: write-off / charge-off reason mappings =="

# --- 1. write-off side, dangling reason, EXPENSE account (only one rule is violated).
sh "$C" A2-540-prod-writeoff-reason-dangling POST /loanproducts req/t275-090-writeoff-reason-dangling.json || exit 1
cat "$DIR/out/A2-540-prod-writeoff-reason-dangling.json"; echo

# --- 2. write-off side, dangling reason AND a non-expense account (BOTH rules violated).
sh "$C" A2-541-prod-writeoff-reason-dangling-nonexpense POST /loanproducts req/t275-091-writeoff-reason-dangling-nonexpense.json || exit 1
cat "$DIR/out/A2-541-prod-writeoff-reason-dangling-nonexpense.json"; echo

# --- 3. charge-off side, dangling reason, EXPENSE account. This column HAS an FK, so if
#        the application check is absent the failure surfaces from PostgreSQL instead --
#        the A2-bad-045 pattern, where a missing validator leaks raw constraint text.
sh "$C" A2-542-prod-chargeoff-reason-dangling POST /loanproducts req/t275-092-chargeoff-reason-dangling.json || exit 1
cat "$DIR/out/A2-542-prod-chargeoff-reason-dangling.json"; echo

# --- 4. charge-off side, both rules violated.
sh "$C" A2-543-prod-chargeoff-reason-dangling-nonexpense POST /loanproducts req/t275-093-chargeoff-reason-dangling-nonexpense.json || exit 1
cat "$DIR/out/A2-543-prod-chargeoff-reason-dangling-nonexpense.json"; echo

# --- 5. what, if anything, landed. Before this fire the corpus had ZERO rows with
#        write_off_reason_id or charge_off_reason_id set, so a row appearing here is the
#        proof that the parameter was honoured rather than silently ignored.
sh "$Q" A2-544-db-mapping-after-reason-probes sql/q8-t275-mapping-ids.sql || exit 1

echo "== group C complete =="
