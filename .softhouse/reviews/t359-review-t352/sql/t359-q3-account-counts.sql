-- T359: per-account leg counts NOW, and the same counts with T352's four transactions
-- excluded (the ledger is append-only, so that is the pre-T352 count, re-derived).
\pset footer off
SELECT account_id,
       count(*) AS legs_now,
       count(*) FILTER (WHERE transaction_id NOT IN
         ('a29bca0816a7','a29bca9bf813','a29bcaa6a41b','a29bcb5d6fcf')) AS legs_excluding_t352
FROM acc_gl_journal_entry
WHERE account_id IN (16,17,18,21,22)
GROUP BY account_id ORDER BY account_id;
SELECT count(*) AS all_legs, count(DISTINCT transaction_id) AS all_txns FROM acc_gl_journal_entry;
