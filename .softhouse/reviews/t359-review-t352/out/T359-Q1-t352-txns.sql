-- T359 independent verification of T352's four claimed transactions.
\pset footer off
SELECT transaction_id, account_id, type_enum, currency_code,
       amount, scale(amount) AS amount_scale, reversed, entry_date, description
FROM acc_gl_journal_entry
WHERE transaction_id IN ('a29bca0816a7','a29bca9bf813','a29bcaa6a41b','a29bcb5d6fcf')
ORDER BY transaction_id, id;
