-- T391 -- is loan 8 accrued 3 of 6 periods or 6 of 6? Read-only.
-- q7 section 3 guessed three column names and psql refused it; that transcript is kept
-- with its ERROR line rather than replaced. This query asks the schema first.
\echo '=== 1. the accrual-shaped columns m_loan_repayment_schedule actually has ==='
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'm_loan_repayment_schedule'
  AND (column_name LIKE '%accru%' OR column_name LIKE '%recognized%' OR column_name LIKE '%waived%')
ORDER BY ordinal_position;

\echo '=== 2. loan 8: the six periods ==='
SELECT installment, fromdate, duedate, principal_amount, interest_amount,
       fee_charges_amount, penalty_charges_amount, completed_derived, obligations_met_on_date
FROM m_loan_repayment_schedule WHERE loan_id = 8 ORDER BY installment;

\echo '=== 3. loan 8: accrual coverage, one row per period, joined to the ACCRUAL txns ==='
SELECT r.installment, r.duedate,
       t.id AS accrual_txn, t.transaction_date, t.amount AS accrued_amount,
       t.interest_portion_derived, t.fee_charges_portion_derived, t.penalty_charges_portion_derived,
       t.created_by
FROM m_loan_repayment_schedule r
LEFT JOIN m_loan_transaction t
       ON t.loan_id = r.loan_id AND t.transaction_type_enum = 10 AND t.transaction_date = r.duedate
WHERE r.loan_id = 8 ORDER BY r.installment;
