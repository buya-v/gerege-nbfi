\pset pager off
SELECT column_name, data_type
  FROM information_schema.columns
 WHERE table_name='acc_gl_journal_entry'
 ORDER BY ordinal_position;
