-- T390 Q0: the real column list of acc_gl_journal_entry, so Q1 names columns that exist.
SELECT ordinal_position, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'acc_gl_journal_entry'
ORDER BY ordinal_position;
