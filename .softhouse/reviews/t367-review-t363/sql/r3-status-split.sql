-- T367 re-derivation #3 -- READ-ONLY. The 156/194 split at reference-oracle.md:924.
SELECT status, count(*) AS n FROM m_portfolio_command_source GROUP BY status ORDER BY status;
SELECT count(*) AS total FROM m_portfolio_command_source;
-- and the same split restricted to rows at or below the T363 floor (352)
SELECT status, count(*) AS n_at_or_below_352 FROM m_portfolio_command_source WHERE id <= 352 GROUP BY status ORDER BY status;
-- any command-source row with a NULL/blank key, stated three ways
SELECT count(*) FILTER (WHERE idempotency_key IS NULL)          AS null_key,
       count(*) FILTER (WHERE idempotency_key = '')             AS empty_key,
       count(*) FILTER (WHERE btrim(coalesce(idempotency_key,'')) = '') AS null_or_blank_key,
       count(*)                                                 AS rows_total
FROM m_portfolio_command_source;
-- is the column even nullable?
SELECT column_name, is_nullable, data_type
FROM information_schema.columns
WHERE table_name = 'm_portfolio_command_source' AND column_name IN ('idempotency_key','status','result_status_code');
