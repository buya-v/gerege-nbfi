-- T367 re-derivation #2 -- READ-ONLY.
\echo '== journal-entry id gaps (append-only claim) =='
SELECT g AS missing_id FROM generate_series(1, (SELECT max(id) FROM acc_gl_journal_entry)) g
WHERE NOT EXISTS (SELECT 1 FROM acc_gl_journal_entry j WHERE j.id = g) ORDER BY g;

\echo '== journal entries above floor 64 =='
SELECT id, transaction_id, account_id, type_enum, currency_code, amount, created_on_utc, reversed
FROM acc_gl_journal_entry WHERE id > 64 ORDER BY id;

\echo '== rows at/below floor: last 3 =='
SELECT id, transaction_id, account_id, currency_code, amount, created_on_utc
FROM acc_gl_journal_entry WHERE id <= 64 ORDER BY id DESC LIMIT 3;

\echo '== command source above floor 352 =='
SELECT id, idempotency_key, status, action_name, entity_name, made_on_date
FROM m_portfolio_command_source WHERE id > 352 ORDER BY id;

\echo '== command source rows 350-352 =='
SELECT id, idempotency_key, status, action_name, entity_name, made_on_date
FROM m_portfolio_command_source WHERE id BETWEEN 349 AND 352 ORDER BY id;

\echo '== per-account legs, live and excluding the 5 registered txns =='
WITH reg(tid) AS (SELECT unnest(ARRAY['a29bca0816a7','a29bca9bf813','a29bcaa6a41b','a29bcb5d6fcf','a29bd5eaeb1b'])),
     acct(a) AS (SELECT unnest(ARRAY[16,17,18,21,22]))
SELECT 'gl '||acct.a AS account,
       (SELECT count(*) FROM acc_gl_journal_entry j WHERE j.account_id=acct.a AND j.transaction_id NOT IN (SELECT tid FROM reg)) AS at_floor,
       (SELECT count(*) FROM acc_gl_journal_entry j WHERE j.account_id=acct.a) AS live
FROM acct ORDER BY acct.a;

\echo '== distinct currencies excluding registered txns =='
WITH reg(tid) AS (SELECT unnest(ARRAY['a29bca0816a7','a29bca9bf813','a29bcaa6a41b','a29bcb5d6fcf','a29bd5eaeb1b']))
SELECT string_agg(DISTINCT currency_code, ',') AS ccy_at_floor
FROM acc_gl_journal_entry WHERE transaction_id NOT IN (SELECT tid FROM reg);
