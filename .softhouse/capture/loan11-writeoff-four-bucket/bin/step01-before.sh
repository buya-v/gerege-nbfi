#!/usr/bin/env bash
# step01-before.sh — OH-WOCAP-V
#
# Phase 1 of the write-off read-back for the loan money rule
#   writeoff.go:36 WriteOffOutstanding — a write-off discharges the WHOLE
#   outstanding principal/interest/fee/penalty and returns it.
#
# Captures loan 11 (product 3, OHLGR-Accrual-Loan, ACCRUAL PERIODIC) BEFORE the
# write-off: detail, transactions, journal entries (accounting is on), and a
# read-only DB cross-check of the four outstanding buckets and the two charges.
#
# The write itself is step02, a separate script, so the run can COMMIT the
# before-state before touching the oracle.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan11-writeoff-four-bucket

LOAN=11

db_snap() {
    local name="$1"
    {
        echo "# OH-WOCAP-V read-only DB evidence — phase=$name"
        echo "# captured at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "--- m_loan (id=$LOAN) ---"
        docker exec gerege-oracle-db psql -U root -d fineract_gerege -A -F'|' -c \
            "select id, account_no, loan_status_id, principal_outstanding_derived, interest_outstanding_derived, fee_charges_outstanding_derived, penalty_charges_outstanding_derived, total_outstanding_derived, principal_writtenoff_derived, interest_writtenoff_derived, fee_charges_writtenoff_derived, penalty_charges_writtenoff_derived, total_writtenoff_derived, writtenoffon_date from m_loan where id=$LOAN;"
        echo "--- m_loan_charge (loan_id=$LOAN) ---"
        docker exec gerege-oracle-db psql -U root -d fineract_gerege -A -F'|' -c \
            "select id, charge_id, is_penalty, amount, amount_paid_derived, amount_waived_derived, amount_writtenoff_derived, amount_outstanding_derived, is_paid_derived, waived from m_loan_charge where loan_id=$LOAN order by id;"
        echo "--- m_loan_transaction (loan_id=$LOAN) ---"
        docker exec gerege-oracle-db psql -U root -d fineract_gerege -A -F'|' -c \
            "select id, transaction_type_enum, transaction_date, amount, principal_portion_derived, interest_portion_derived, fee_charges_portion_derived, penalty_charges_portion_derived, outstanding_loan_balance_derived, is_reversed from m_loan_transaction where loan_id=$LOAN order by id;"
    } > "$OHS_OUT/db-$name.txt"
}

# ---- BEFORE -------------------------------------------------------------
ohs_get loan-11-before-detail         "/loans/$LOAN?associations=all"
ohs_get loan-11-before-transactions   "/loans/$LOAN/transactions?limit=100"
ohs_get loan-11-before-journalentries "/journalentries?loanId=$LOAN&limit=80"
db_snap before

echo "--- loan $LOAN summary BEFORE (four buckets) ---"
python3 - "$OHS_OUT/loan-11-before-detail-raw.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
s=d.get('summary',{})
print("status:", d.get('status',{}).get('code'), "active:", d.get('status',{}).get('active'))
for k in ['principalOutstanding','interestOutstanding','feeChargesOutstanding',
          'penaltyChargesOutstanding','totalOutstanding',
          'principalWrittenOff','interestWrittenOff','feeChargesWrittenOff',
          'penaltyChargesWrittenOff','totalWrittenOff']:
    print(f"  {k} = {s.get(k)}")
PY
echo "before-state captured."
