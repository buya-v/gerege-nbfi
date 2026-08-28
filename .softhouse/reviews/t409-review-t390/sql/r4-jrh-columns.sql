\pset pager off
SELECT table_name, column_name, data_type
  FROM information_schema.columns
 WHERE table_name IN ('job_run_history','job')
 ORDER BY table_name, ordinal_position;
