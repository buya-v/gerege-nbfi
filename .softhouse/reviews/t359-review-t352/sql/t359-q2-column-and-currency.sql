-- T359: the amount column's declared type, and every currency present in the ledger.
\pset footer off
SELECT table_name, column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name='acc_gl_journal_entry' AND column_name='amount';
SELECT currency_code, count(*) AS legs, count(DISTINCT transaction_id) AS txns
FROM acc_gl_journal_entry GROUP BY currency_code ORDER BY currency_code;
SELECT count(*) AS legs_with_scale_gt_2
FROM acc_gl_journal_entry WHERE scale(trim_scale(amount)) > 2;
SELECT id, transaction_id, account_id, currency_code, amount
FROM acc_gl_journal_entry WHERE scale(trim_scale(amount)) > 2 ORDER BY id;
