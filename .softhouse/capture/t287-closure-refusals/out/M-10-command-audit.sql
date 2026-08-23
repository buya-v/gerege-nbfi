-- T287. What did the command bus actually record for this task's requests?
--
-- Raised by an observation, not by a plan: m_portfolio_command_source moved 347 -> 350 across
-- one CREATE closure and TWO REFUSED journal-entry posts. If refused commands leave audit
-- rows, then "a refused write writes nothing" is true of the LEDGER but NOT of the whole
-- database, and arm 1's claim has to be scoped accordingly rather than left to imply more
-- than was measured.
--
-- PostgreSQL. Read-only: every statement is a SELECT.
\pset pager off
\echo '=== command source rows from id 345 up (this task sits at the tail) ==='
SELECT id, action_name, entity_name, resource_id, office_id, made_on_date, checker_id, processing_result_enum
FROM m_portfolio_command_source
WHERE id >= 345
ORDER BY id;

\echo ''
\echo '=== the same rows, with the command json, so the refused ones are identifiable ==='
SELECT id, action_name, entity_name, left(command_as_json, 120) AS command_json_head
FROM m_portfolio_command_source
WHERE id >= 345
ORDER BY id;
