-- A2 final observed state of the three slice tables, after every probe in this
-- directory has run. This is the row-level ground truth a Go port must reproduce.
\pset border 2
\echo '--- acc_gl_account ---'
SELECT id, parent_id, gl_code, name, classification_enum, account_usage,
       manual_journal_entries_allowed, disabled, hierarchy, tag_id
FROM acc_gl_account ORDER BY id;

\echo '--- acc_gl_financial_activity_account ---'
SELECT f.id, f.financial_activity_type, f.gl_account_id, g.gl_code, g.name,
       g.classification_enum, g.account_usage
FROM acc_gl_financial_activity_account f
JOIN acc_gl_account g ON g.id = f.gl_account_id
ORDER BY f.financial_activity_type;

\echo '--- acc_product_mapping row count per product ---'
SELECT product_id, product_type, count(*) AS mappings,
       count(payment_type) AS payment_type_specific
FROM acc_product_mapping GROUP BY product_id, product_type ORDER BY product_id;

\echo '--- DUPLICATE (product_id, product_type, financial_account_type, payment_type) ---'
\echo '--- the JPA @UniqueConstraint named `financial_action` is NOT in the DDL ---'
SELECT product_id, product_type, financial_account_type, payment_type,
       count(*) AS n, array_agg(gl_account_id ORDER BY id) AS gl_account_ids
FROM acc_product_mapping
GROUP BY product_id, product_type, financial_account_type, payment_type
HAVING count(*) > 1
ORDER BY product_id;

\echo '--- journal entries written by the A2 probes ---'
SELECT j.id, j.loan_transaction_id, j.type_enum, j.account_id, g.gl_code, g.name,
       g.account_usage, j.amount, j.currency_code
FROM acc_gl_journal_entry j JOIN acc_gl_account g ON g.id = j.account_id
ORDER BY j.id;

\echo '--- the amount column type: money must not be a float ---'
SELECT table_name, column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'acc_gl_journal_entry' AND column_name = 'amount';
