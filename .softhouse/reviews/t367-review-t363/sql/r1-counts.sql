-- T367 re-derivation #1 -- READ-ONLY. Every statement is a SELECT.
\pset footer off
SELECT 'cs_total_rows'         AS k, count(*)::text AS v FROM m_portfolio_command_source
UNION ALL SELECT 'cs_max_id',   max(id)::text        FROM m_portfolio_command_source
UNION ALL SELECT 'cs_min_id',   min(id)::text        FROM m_portfolio_command_source
UNION ALL SELECT 'cs_null_idem',count(*)::text       FROM m_portfolio_command_source WHERE idempotency_key IS NULL
UNION ALL SELECT 'cs_blank_idem',count(*)::text      FROM m_portfolio_command_source WHERE idempotency_key IS NOT NULL AND btrim(idempotency_key) = ''
UNION ALL SELECT 'cs_distinct_idem', count(DISTINCT idempotency_key)::text FROM m_portfolio_command_source
UNION ALL SELECT 'cs_rows_gt_352', count(*)::text    FROM m_portfolio_command_source WHERE id > 352
UNION ALL SELECT 'cs_gaps_in_id', (max(id)-min(id)+1-count(*))::text FROM m_portfolio_command_source
UNION ALL SELECT 'je_rows',      count(*)::text      FROM acc_gl_journal_entry
UNION ALL SELECT 'je_max_id',    max(id)::text       FROM acc_gl_journal_entry
UNION ALL SELECT 'je_min_id',    min(id)::text       FROM acc_gl_journal_entry
UNION ALL SELECT 'je_rows_gt_64',count(*)::text      FROM acc_gl_journal_entry WHERE id > 64
UNION ALL SELECT 'je_distinct_txn', count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry
UNION ALL SELECT 'je_currencies', string_agg(DISTINCT currency_code, ',') FROM acc_gl_journal_entry
UNION ALL SELECT 'closure_rows',  count(*)::text     FROM acc_gl_closure
UNION ALL SELECT 'closure_max_id',coalesce(max(id)::text,'null') FROM acc_gl_closure
UNION ALL SELECT 'm_loan_rows',   count(*)::text     FROM m_loan
UNION ALL SELECT 'm_office_rows', count(*)::text     FROM m_office
UNION ALL SELECT 'ledger_float_cols', count(*)::text FROM information_schema.columns
   WHERE table_name IN ('acc_gl_journal_entry','acc_gl_closure') AND data_type IN ('double precision','real','money')
UNION ALL SELECT 'engine', split_part(version(), ' on ', 1);
