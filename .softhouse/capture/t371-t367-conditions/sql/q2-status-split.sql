-- T371 q2 -- F3: the PROCESSED/ERROR split of m_portfolio_command_source, RE-DERIVED.
-- CommandProcessingResultType at 426a23544: 0 INVALID, 1 PROCESSED, 2 AWAITING_APPROVAL,
-- 3 REJECTED, 4 UNDER_PROCESSING, 5 ERROR.
-- The floor is m_portfolio_command_source.id = 352 (PROBES.tsv), so the split is reported
-- whole-table AND at-or-below-floor, because the doctrine sentence under repair is about
-- the WHOLE table and a reader must be able to tell the two apart.
SELECT status,
       count(*)                                        AS rows_total,
       count(*) FILTER (WHERE id <= 352)               AS rows_at_or_below_floor,
       count(*) FILTER (WHERE id  > 352)               AS rows_above_floor
FROM m_portfolio_command_source
GROUP BY status
ORDER BY status;
SELECT count(*) AS grand_total FROM m_portfolio_command_source;
