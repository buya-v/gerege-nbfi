\pset footer off
\echo '== c1: base table count =='
SELECT count(*) AS base_tables FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';
\echo '== c2: the 8 names T417 excludes -- do they all EXIST as base tables? =='
SELECT x.n, (t.table_name IS NOT NULL) AS exists_as_base_table
FROM (VALUES ('batch_job_execution'),('batch_job_execution_context'),('batch_job_execution_params'),
             ('batch_job_instance'),('batch_step_execution'),('batch_step_execution_context'),
             ('job_run_history'),('job')) x(n)
LEFT JOIN information_schema.tables t
  ON t.table_name=x.n AND t.table_schema='public' AND t.table_type='BASE TABLE'
ORDER BY 1;
\echo '== c3: graded count = base tables MINUS the 8 =='
SELECT count(*) AS graded FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE'
  AND table_name NOT IN ('batch_job_execution','batch_job_execution_context','batch_job_execution_params','batch_job_instance','batch_step_execution','batch_step_execution_context','job_run_history','job');
\echo '== c4: sequences total =='
SELECT count(*) AS sequences FROM pg_sequences WHERE schemaname='public';
\echo '== c5: sequences EXCLUDED by the prefix predicate, by name =='
SELECT sequencename FROM pg_sequences WHERE schemaname='public'
 AND NOT (TRUE AND sequencename NOT LIKE 'batch_job%' AND sequencename NOT LIKE 'batch_step%'
          AND sequencename NOT LIKE 'job_run_history%' AND sequencename NOT LIKE 'job_id%')
ORDER BY 1;
\echo '== c6: sequences graded =='
SELECT count(*) AS graded_sequences FROM pg_sequences WHERE schemaname='public'
 AND TRUE AND sequencename NOT LIKE 'batch_job%' AND sequencename NOT LIKE 'batch_step%'
 AND sequencename NOT LIKE 'job_run_history%' AND sequencename NOT LIKE 'job_id%';
\echo '== c7: ANY OTHER base table whose name starts with batch_ or job (over/under-exclusion check) =='
SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'
 AND (table_name LIKE 'batch%' OR table_name LIKE 'job%' OR table_name LIKE '%quartz%' OR table_name LIKE 'qrtz%')
ORDER BY 1;
\echo '== c8: ALL sequences starting with job or batch (does the prefix over-reach?) =='
SELECT sequencename FROM pg_sequences WHERE schemaname='public'
 AND (sequencename LIKE 'job%' OR sequencename LIKE 'batch%') ORDER BY 1;
\echo '== c9: columns of the 8 excluded tables that look monetary =='
SELECT table_name, column_name, data_type FROM information_schema.columns
WHERE table_schema='public'
  AND table_name IN ('batch_job_execution','batch_job_execution_context','batch_job_execution_params','batch_job_instance','batch_step_execution','batch_step_execution_context','job_run_history','job')
ORDER BY table_name, ordinal_position;
