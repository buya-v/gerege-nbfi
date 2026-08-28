-- T379 INDEPENDENT re-derivation of T371's F1 split. READ ONLY -- every statement is a SELECT.
-- Deliberately NOT T371's regex. Three orthogonal discriminators:
--   (A) CHARACTER-SET + LENGTH: canonical 36 chars, only [0-9a-f-], hyphens at 9,14,19,24.
--   (B) RFC-4122 VERSION-4 shape: UUID.randomUUID() ALWAYS sets the version nibble to 4 and
--       the variant nibble to one of [89ab]. A key that is UUID-shaped but NOT v4 was NOT
--       minted by IdempotencyKeyGenerator.create() -- it was supplied by a caller. That
--       distinction is invisible to a bare 8-4-4-4-12 hex regex, which is what T371 used.
--   (C) SEMANTIC, vocabulary-free: does the key contain a letter OUTSIDE the hex alphabet
--       followed by two more letters -- i.e. a human-authored word -- with no list of task
--       names anywhere in the predicate.
SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;

\echo '--- (0) column nullability, restated from the catalog'
SELECT is_nullable, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name='m_portfolio_command_source' AND column_name='idempotency_key';

\echo '--- (1) totals under three orthogonal discriminators'
SELECT count(*) AS total,
       count(*) FILTER (WHERE idempotency_key IS NULL)                AS nulls,
       count(*) FILTER (WHERE btrim(coalesce(idempotency_key,''))='') AS blanks,
       count(DISTINCT idempotency_key)                                AS distinct_keys,
       min(id) AS min_id, max(id) AS max_id,
       count(*) FILTER (WHERE length(idempotency_key)=36
                          AND idempotency_key ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') AS shapeA_uuidish,
       count(*) FILTER (WHERE idempotency_key ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$') AS shapeB_v4,
       count(*) FILTER (WHERE idempotency_key ~* '[g-zG-Z][a-zA-Z]{2}') AS shapeC_haswords,
       count(*) FILTER (WHERE idempotency_key !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') AS notA,
       count(*) FILTER (WHERE idempotency_key !~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$') AS notB
FROM m_portfolio_command_source;

\echo '--- (2) SET EQUALITY, not count equality: do notA and C name the SAME rows?'
SELECT
  count(*) FILTER (WHERE nota AND NOT hasword) AS in_notA_only,
  count(*) FILTER (WHERE hasword AND NOT nota) AS in_C_only,
  count(*) FILTER (WHERE nota AND hasword)     AS in_both
FROM (SELECT idempotency_key !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AS nota,
             idempotency_key ~* '[g-zG-Z][a-zA-Z]{2}' AS hasword
      FROM m_portfolio_command_source) s;

\echo '--- (3) A-positive but B-negative: uuid-shaped yet NOT randomUUID-minted'
SELECT id, status, idempotency_key
FROM m_portfolio_command_source
WHERE idempotency_key ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
  AND idempotency_key !~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
ORDER BY id;

\echo '--- (4) uppercase-hex UUIDs? Java UUID.toString() is lowercase, so any hit is caller-supplied'
SELECT count(*) AS uppercase_uuidish
FROM m_portfolio_command_source
WHERE idempotency_key ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
  AND idempotency_key ~ '[A-F]';

\echo '--- (5) the full non-UUID list, with the above/below-floor mark'
SELECT id, status, (id > 352) AS above_floor, idempotency_key
FROM m_portfolio_command_source
WHERE idempotency_key !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
ORDER BY id;

\echo '--- (6) rows 350..359 (FU-T367-4 asserts 352 carries a minted UUID)'
SELECT id, status, idempotency_key,
       idempotency_key ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' AS is_v4_minted
FROM m_portfolio_command_source WHERE id BETWEEN 350 AND 359 ORDER BY id;

\echo '--- (7) F3 re-derivation: the status split, independently'
SELECT status,
       count(*) AS n,
       count(*) FILTER (WHERE id <= 352) AS at_or_below_floor,
       count(*) FILTER (WHERE id  > 352) AS above_floor
FROM m_portfolio_command_source GROUP BY status ORDER BY status;

\echo '--- (8) F3 robustness: how far from a tie is the ERROR majority?'
SELECT count(*) AS total,
       count(*) FILTER (WHERE status=5) AS errors,
       count(*) FILTER (WHERE status<>5) AS non_errors,
       count(*) FILTER (WHERE status=5) - (count(*)/2 + 1) AS margin_over_bare_majority
FROM m_portfolio_command_source;

\echo '--- (9) POLICY 5 evasion spot-checks: sequence, base-table count, reversed rows'
SELECT sequencename, last_value, is_called FROM pg_sequences
WHERE schemaname='public' AND sequencename IN ('acc_gl_closure_id_seq','acc_gl_journal_entry_id_seq');
SELECT (SELECT count(*) FROM acc_gl_closure) AS closure_rows,
       (SELECT max(id)   FROM acc_gl_closure) AS closure_max_id;
SELECT count(*) AS base_tables FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE';
SELECT count(*) AS reversed_true, max(id) AS max_reversed_id
FROM acc_gl_journal_entry WHERE reversed = true;
SELECT count(*) AS float_columns FROM information_schema.columns
WHERE table_schema='public' AND data_type IN ('double precision','real','money');

\echo '--- (10) append-only max ids, for the opening/closing comparison'
SELECT (SELECT count(*) FROM acc_gl_journal_entry) AS je_rows,
       (SELECT max(id) FROM acc_gl_journal_entry)  AS je_max,
       (SELECT count(*) FROM m_portfolio_command_source) AS cs_rows,
       (SELECT max(id) FROM m_portfolio_command_source)  AS cs_max;
