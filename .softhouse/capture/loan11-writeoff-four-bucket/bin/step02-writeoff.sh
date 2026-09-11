#!/usr/bin/env bash
# step02-writeoff.sh — OH-WOCAP-V
#
# Phase 2: write off loan 11 and read back the AFTER state.
#
#   POST /loans/{loanId}/transactions?command=writeoff
#
# The command lives on the TRANSACTIONS sub-resource, not on /loans/{id}:
# `POST /loans/{id}?command=writeoff` is refused 400
# (error.msg.query.parameter.value.unsupported), observed as A2-228; the
# transactions form returned 200 as A2-232. Endpoint shape taken from that
# committed observation, not re-derived.
#
# Request body is byte-stable by construction: every value is a JSON string, so
# nothing goes through json.dumps of a parsed number (no 100.00 -> 100.0).
#
# Additive: ONE write, exactly the write-off. No SQL insert. If the oracle
# refuses, the refusal (status + error body) is captured and is the result.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan11-writeoff-four-bucket

LOAN=11
# Business date is 2026-09-03; loan 11's last transaction is the 2026-09-02
# accrual, so a write-off dated at the business date clears the not-before-last-
# transaction rule and is not in the future.
WROFF_DATE='03 September 2026'

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

# ---- WRITE OFF ----------------------------------------------------------
WROFF_BODY=$(mktemp)
printf '%s' "{\"transactionDate\":\"$WROFF_DATE\",\"locale\":\"en\",\"dateFormat\":\"dd MMMM yyyy\"}" > "$WROFF_BODY"
ohs_post loan-writeoff "/loans/$LOAN/transactions?command=writeoff" "$WROFF_BODY"
rm -f "$WROFF_BODY"

echo "writeoff HTTP: $(cat "$OHS_OUT/loan-writeoff.status")"
cat "$OHS_OUT/loan-writeoff-raw.json"; echo

# ---- AFTER --------------------------------------------------------------
ohs_get loan-11-after-detail         "/loans/$LOAN?associations=all"
ohs_get loan-11-after-transactions   "/loans/$LOAN/transactions?limit=100"
ohs_get loan-11-after-journalentries "/journalentries?loanId=$LOAN&limit=80"
db_snap after

echo "--- loan $LOAN summary AFTER (four buckets) ---"
python3 - "$OHS_OUT/loan-11-after-detail-raw.json" <<'PY'
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
echo "after-state captured."
