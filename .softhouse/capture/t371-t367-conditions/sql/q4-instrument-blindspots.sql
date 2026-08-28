-- T371 q4 -- the THREE EVASIONS T367 found, RE-DERIVED rather than inherited.
-- Every statement is a SELECT. Nothing here writes, and nothing here calls nextval().
--
-- 1. a consumed sequence the instrument cannot see (it floors on max(id), never on a sequence)
SELECT 'seq' AS kind, sequencename, last_value, coalesce(last_value::text,'null') AS lv
FROM pg_sequences
WHERE schemaname = 'public'
  AND sequencename IN ('acc_gl_closure_id_seq','acc_gl_journal_entry_id_seq','m_portfolio_command_source_id_seq')
ORDER BY sequencename;

-- pg_sequences hides is_called, so read it from the sequence relation itself. This is a
-- SELECT over the sequence's own row and does NOT advance it (nextval would; last_value does not).
SELECT 'acc_gl_closure_id_seq' AS seq, last_value, is_called FROM acc_gl_closure_id_seq;

-- 2. how many tables the two watched tables are being asked to cover
SELECT 'base_tables_in_tenant' AS k, count(*)::text AS v
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- 3. an UPDATE below the floor: `reversed` is a column the instrument never reads
SELECT 'reversed_true_rows'            AS k, count(*)::text AS v FROM acc_gl_journal_entry WHERE reversed
UNION ALL
SELECT 'reversed_true_at_or_below_64',      count(*)::text      FROM acc_gl_journal_entry WHERE reversed AND id <= 64
UNION ALL
SELECT 'reversed_true_above_64',            count(*)::text      FROM acc_gl_journal_entry WHERE reversed AND id  > 64;

-- and the float check's true width: the instrument checks two tables; the schema has how many?
SELECT 'float_columns_whole_schema' AS k, count(*)::text AS v
FROM information_schema.columns
WHERE table_schema = 'public'
  AND data_type IN ('double precision','real','money');
