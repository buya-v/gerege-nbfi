-- T388: charges available in the tenant, and the currently-max GL account / product ids.
-- Read-only.
\echo '=== charges ==='
SELECT id, name, currency_code, charge_applies_to_enum, charge_time_enum, charge_calculation_enum,
       charge_payment_mode_enum, amount, is_penalty, is_active, is_deleted
FROM m_charge ORDER BY id;
\echo '=== max ids I am about to move ==='
SELECT 'acc_gl_account' AS tbl, max(id) FROM acc_gl_account
UNION ALL SELECT 'm_product_loan', max(id) FROM m_product_loan
UNION ALL SELECT 'm_client', max(id) FROM m_client
UNION ALL SELECT 'm_loan', max(id) FROM m_loan;
\echo '=== gl codes already in use ==='
SELECT gl_code FROM acc_gl_account ORDER BY gl_code;
