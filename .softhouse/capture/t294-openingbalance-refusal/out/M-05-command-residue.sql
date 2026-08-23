-- T294 -- WHAT RESIDUE THIS PROBE LEAVES, CHARACTERISED RATHER THAN COUNTED.
--
-- T289 F-T289-3 found that T287's disclosure read as "a counter moved" when the truth was
-- "the oracle's public API now tells this story". So this rig reads its own audit row back
-- and commits it, and the paired GET /v1/audits capture beside it shows what the PUBLIC
-- endpoint serves. READ-ONLY.
SELECT id, action_name, entity_name, resource_id, status, office_id, api_get_url
  FROM m_portfolio_command_source
 ORDER BY id DESC
 LIMIT 4;

SELECT id, command_as_json
  FROM m_portfolio_command_source
 ORDER BY id DESC
 LIMIT 1;

-- SEQUENCES. T287's permanent, unrestorable residue was a sequence's is_called flag. This
-- probe should touch NO sequence except m_portfolio_command_source's, because it never
-- reached a persist. Measured rather than assumed.
-- pg_sequences does NOT expose is_called, so each sequence relation is read directly. Both
-- columns are named for what they are; a column labelled is_called that is really
-- "last_value IS NOT NULL" would be the kind of mislabel A2-34 F-4 cost this program once.
SELECT 'acc_gl_journal_entry_id_seq'       AS sequencename, last_value, is_called FROM acc_gl_journal_entry_id_seq
UNION ALL
SELECT 'acc_gl_closure_id_seq',             last_value, is_called FROM acc_gl_closure_id_seq
UNION ALL
SELECT 'm_portfolio_command_source_id_seq', last_value, is_called FROM m_portfolio_command_source_id_seq
UNION ALL
SELECT 'm_command_id_seq',                  last_value, is_called FROM m_command_id_seq
ORDER BY 1;
