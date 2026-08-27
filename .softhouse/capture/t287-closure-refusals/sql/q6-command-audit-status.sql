-- T287. q5-command-audit.sql failed on `processing_result_enum` (the column is `status`);
-- that failure is committed verbatim as out/M-10-command-audit.txt. This re-asks with the
-- real schema.
--
-- The question: a REFUSED journal-entry POST left an m_portfolio_command_source row. With
-- what status?
--
-- CORRECTED AFTER EXECUTION. This comment originally guessed the enum as
--   "1 INVALID, 2 PROCESSED, 3 AWAITING_APPROVAL, 4 REJECTED, 5 ERROR, 6 UNDER_PROCESSING"
-- and the guess was WRONG. The observed data contradicted it immediately -- the SUCCESSFUL
-- closure create came back status 1 -- so the enum was read from source instead of guessed
-- [VERIFIED: fineract-core/.../commands/domain/CommandProcessingResultType.java:31-37]:
--   0 INVALID, 1 PROCESSED, 2 AWAITING_APPROVAL, 3 REJECTED, 4 UNDER_PROCESSING, 5 ERROR
-- Only the comment changed; the executed SQL is unchanged, so re-running this file produces
-- the same result set. Because out/M-11-command-audit-status.sql is a byte snapshot of what
-- actually ran, it still carries the WRONG comment and its sha256 therefore differs from
-- this file. That divergence is intended and is exactly what the snapshot exists to expose.
--
-- `status` distinguishes "the write happened" from "the write was refused and only the
-- attempt was logged". This matters for the arm 1 claim: "a refused write writes nothing" is
-- a statement about the LEDGER, and the size of the gap between that and "writes nothing at
-- all" is exactly what this query measures.
--
-- PostgreSQL. Read-only: every statement is a SELECT.
\pset pager off
\echo '=== this task tail, with status, resource_id and idempotency key ==='
SELECT id, action_name, entity_name, status, resource_id, office_id, idempotency_key, made_on_date_utc
FROM m_portfolio_command_source
WHERE id >= 345
ORDER BY id;

\echo ''
\echo '=== status distribution across the WHOLE audit table, for context ==='
SELECT status, count(*) AS rows FROM m_portfolio_command_source GROUP BY status ORDER BY status;
