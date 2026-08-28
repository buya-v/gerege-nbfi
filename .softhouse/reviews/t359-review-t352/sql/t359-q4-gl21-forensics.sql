-- T359: every leg on gl 21 with its id, so T352's claimed "7 -> 12" can be audited row by
-- row, plus the full id tail of the table to detect any write AFTER T352's nine legs.
\pset footer off
SELECT id, transaction_id, account_id, currency_code, amount, entry_date, created_on_utc,
       left(coalesce(description,''),44) AS descr
FROM acc_gl_journal_entry WHERE account_id = 21 ORDER BY id;
SELECT id, transaction_id, account_id, currency_code, amount, created_on_utc,
       left(coalesce(description,''),44) AS descr
FROM acc_gl_journal_entry WHERE id >= 55 ORDER BY id;
