-- T371 q1 -- OPENING read. Every statement here is a SELECT; this file writes nothing.
-- Purpose: attest that T371 did not move the oracle, and pin the floor T371 measured against.
SELECT 'je_rows'      AS k, count(*)::text          AS v FROM acc_gl_journal_entry
UNION ALL SELECT 'je_max_id',   coalesce(max(id)::text,'null')      FROM acc_gl_journal_entry
UNION ALL SELECT 'cs_rows',     count(*)::text                      FROM m_portfolio_command_source
UNION ALL SELECT 'cs_max_id',   coalesce(max(id)::text,'null')      FROM m_portfolio_command_source
UNION ALL SELECT 'closure_rows',count(*)::text                      FROM acc_gl_closure
UNION ALL SELECT 'closure_max_id', coalesce(max(id)::text,'null')   FROM acc_gl_closure;
