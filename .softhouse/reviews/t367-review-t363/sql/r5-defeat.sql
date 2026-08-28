-- T367 re-derivation #5 -- READ-ONLY. Can a probe move the oracle irreversibly and leave
-- NO trace that oracle-state-baseline.sh reads?
\echo '== sequences: last_value vs max(id). The instrument reads max(id) only. =='
SELECT s.schemaname, s.sequencename, s.last_value
FROM pg_sequences s
WHERE s.sequencename IN ('acc_gl_journal_entry_id_seq','acc_gl_closure_id_seq','m_portfolio_command_source_id_seq')
ORDER BY s.sequencename;

\echo '== the tables the instrument ATTRIBUTES on (2) vs the tables in the tenant =='
SELECT count(*) AS tables_in_public_schema FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE';

\echo '== reversed journal entries -- the instrument never reads this column =='
SELECT reversed, count(*) FROM acc_gl_journal_entry GROUP BY reversed ORDER BY reversed;

\echo '== manual_entry / entry_date spread, also unread =='
SELECT manual_entry, count(*) FROM acc_gl_journal_entry GROUP BY manual_entry ORDER BY manual_entry;

\echo '== acc_gl_account: a GL-account retype leaves NO row in either watched table =='
SELECT id, gl_code, name, classification_enum, disabled, manual_entries_allowed
FROM acc_gl_account WHERE id IN (2,16,17,18,21,22) ORDER BY id;

\echo '== float columns across the WHOLE tenant, not just the 2 ledger tables =='
SELECT count(*) AS float_cols_whole_db FROM information_schema.columns
WHERE table_schema='public' AND data_type IN ('double precision','real','money');
SELECT table_name, column_name, data_type FROM information_schema.columns
WHERE table_schema='public' AND data_type IN ('double precision','real','money')
ORDER BY table_name, column_name LIMIT 25;
