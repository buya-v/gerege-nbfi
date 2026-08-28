-- T359: (1) the stored rows for MY OWN probe a29bd5eaeb1b, and (2) the decisive
-- attribution test T352 did not run — ask PostgreSQL directly what numeric(19,6)
-- does to the same characters, with no Java in the path at all. If the engine
-- alone reproduces the stored value, the rounding is the column's coercion and
-- not MoneyHelper's tenant RoundingMode, which is what T352 asserted from a
-- source ABSENCE and never demonstrated positively.
\pset footer off
\echo '--- (1) the rows my probe wrote ---'
SELECT id, transaction_id, account_id, type_enum, currency_code,
       amount, scale(amount) AS amount_scale, reversed
FROM acc_gl_journal_entry WHERE transaction_id = 'a29bd5eaeb1b' ORDER BY id;

\echo '--- (2) PostgreSQL alone, no Java: what does numeric(19,6) do to these characters? ---'
SELECT '300.6255545'::numeric(19,6)  AS t359_probe_coerced,
       '100.1234565'::numeric(19,6)  AS t352_probe_coerced,
       '-300.6255545'::numeric(19,6) AS negative_coerced,
       '300.625554'::numeric(19,6)   AS what_half_even_would_give;

\echo '--- (3) ledger totals after MY probe, so the next task inherits a true baseline ---'
SELECT count(*) AS legs, max(id) AS max_id, count(DISTINCT transaction_id) AS txns
FROM acc_gl_journal_entry;
SELECT account_id, count(*) AS legs FROM acc_gl_journal_entry
WHERE account_id IN (16,17,18,21,22) GROUP BY account_id ORDER BY account_id;
SELECT currency_code, count(*) AS legs FROM acc_gl_journal_entry
GROUP BY currency_code ORDER BY currency_code;
