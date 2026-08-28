-- T379 -- spot-check of the three POLICY 5 evasions T371 recorded, plus T371's own
-- classifier re-run for SET equality (not count equality). READ ONLY.
SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;

\echo '--- (9a) sequence state. SELECT on a sequence relation READS, it does not advance.'
SELECT 'acc_gl_closure_id_seq' AS seq, last_value, is_called FROM acc_gl_closure_id_seq;
SELECT 'acc_gl_journal_entry_id_seq' AS seq, last_value, is_called FROM acc_gl_journal_entry_id_seq;

\echo '--- (9b) the table the consumed sequence belongs to'
SELECT count(*) AS closure_rows, max(id) AS closure_max_id FROM acc_gl_closure;

\echo '--- (9c) base tables in the tenant schema vs the 2 the instrument watches'
SELECT count(*) AS base_tables_public FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE';
SELECT count(*) AS base_tables_all_schemas FROM information_schema.tables
WHERE table_type='BASE TABLE' AND table_schema NOT IN ('pg_catalog','information_schema');

\echo '--- (9d) reversed=t rows and where they sit relative to the id-64 floor'
SELECT count(*) AS reversed_true, min(id) AS min_id, max(id) AS max_id
FROM acc_gl_journal_entry WHERE reversed = true;

\echo '--- (9e) float/real/money columns across the WHOLE schema'
SELECT count(*) AS float_columns FROM information_schema.columns
WHERE table_schema='public' AND data_type IN ('double precision','real','money');

\echo '--- (11) T371 OWN classifier re-run, and SET equality against the shape classifier'
SELECT count(*) FILTER (WHERE t371_token AND NOT notuuid) AS token_but_uuid_shaped,
       count(*) FILTER (WHERE notuuid AND NOT t371_token) AS notuuid_but_no_token,
       count(*) FILTER (WHERE t371_token AND notuuid)     AS agree
FROM (SELECT idempotency_key ~* '(^|[^a-z0-9])(t[0-9]{2,3}|a2-[0-9]+|arm[0-9]+)([^a-z0-9]|$)' AS t371_token,
             idempotency_key !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$' AS notuuid
      FROM m_portfolio_command_source) s;

\echo '--- (12) append-only max ids: CLOSING read for this review'
SELECT (SELECT count(*) FROM acc_gl_journal_entry) AS je_rows,
       (SELECT max(id) FROM acc_gl_journal_entry)  AS je_max,
       (SELECT count(*) FROM m_portfolio_command_source) AS cs_rows,
       (SELECT max(id) FROM m_portfolio_command_source)  AS cs_max,
       (SELECT count(*) FROM acc_gl_closure) AS closure_rows;
