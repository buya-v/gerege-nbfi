#!/usr/bin/env bash
# db-evidence.sh LOAN_ID LABEL — OH-CHGCAP-BD
#
# Read-only SQL corroboration for one loan at one step. Writes out/db-LABEL.txt.
# The citeable evidence is always the JSON wire capture; this file only
# cross-checks it against the table columns. Tenant gerege only.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
LID="${1:?usage: db-evidence.sh LOAN_ID LABEL}"
LABEL="${2:?usage: db-evidence.sh LOAN_ID LABEL}"
OUT=".softhouse/capture/loan-charge-partial-waive-repaid/out"
PSQL=(docker exec gerege-oracle-db psql -U postgres -d fineract_gerege -A -F'|' -c)
{
    echo "# OH-CHGCAP-BD DB evidence: loan $LID [$LABEL] (read-only, tenant gerege)"
    echo "## m_business_date"
    "${PSQL[@]}" "select type, date from m_business_date order by type;"
    echo "## m_loan"
    "${PSQL[@]}" "select id,account_no,external_id,client_id,product_id,loan_status_id,principal_amount,disbursedon_date,principal_outstanding_derived,interest_outstanding_derived,fee_charges_outstanding_derived,penalty_charges_outstanding_derived,total_outstanding_derived,closedon_date from m_loan where id=$LID;"
    echo "## m_loan_repayment_schedule (amount / completed / obligations_met_on_date)"
    "${PSQL[@]}" "select installment,duedate,principal_amount,principal_completed_derived,interest_amount,interest_completed_derived,fee_charges_amount,fee_charges_completed_derived,penalty_charges_amount,penalty_charges_completed_derived,obligations_met_on_date from m_loan_repayment_schedule where loan_id=$LID order by installment;"
    echo "## m_loan_charge"
    "${PSQL[@]}" "select id,charge_id,is_penalty,amount,amount_paid_derived,amount_waived_derived,amount_writtenoff_derived,amount_outstanding_derived,is_paid_derived,waived,due_for_collection_as_of_date from m_loan_charge where loan_id=$LID order by id;"
    echo "## m_loan_transaction"
    "${PSQL[@]}" "select id,transaction_type_enum,transaction_date,amount,principal_portion_derived,interest_portion_derived,fee_charges_portion_derived,penalty_charges_portion_derived,outstanding_loan_balance_derived,is_reversed from m_loan_transaction where loan_id=$LID order by id;"
} > "$OUT/db-$LABEL.txt" 2>&1
echo "wrote $OUT/db-$LABEL.txt"
