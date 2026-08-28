\pset pager off
SELECT 'm_loan' AS tbl, id::text, last_modified_by::text, last_modified_on_utc::text FROM m_loan WHERE last_modified_on_utc >= TIMESTAMPTZ '2026-08-28 16:00:00+00'
UNION ALL SELECT 'm_loan_transaction', id::text, last_modified_by::text, last_modified_on_utc::text FROM m_loan_transaction WHERE last_modified_on_utc >= TIMESTAMPTZ '2026-08-28 16:00:00+00'
UNION ALL SELECT 'm_loan_repayment_schedule', id::text, last_modified_by::text, last_modified_on_utc::text FROM m_loan_repayment_schedule WHERE last_modified_on_utc >= TIMESTAMPTZ '2026-08-28 16:00:00+00'
UNION ALL SELECT 'm_loan_charge', id::text, last_modified_by::text, last_modified_on_utc::text FROM m_loan_charge WHERE last_modified_on_utc >= TIMESTAMPTZ '2026-08-28 16:00:00+00'
ORDER BY 1,2;
