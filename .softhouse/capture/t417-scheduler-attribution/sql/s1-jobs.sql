\echo '== s1a: the job table, EVERY row. Cardinal derived, never typed. =='
SELECT id, name, is_active, cron_expression, previous_run_start_time, next_run_time,
       currently_running, is_misfired, scheduler_group, task_priority
FROM job ORDER BY id;

\echo '== s1b: the cardinal, derived =='
SELECT count(*) AS jobs_total,
       count(*) FILTER (WHERE is_active) AS jobs_active,
       count(*) FILTER (WHERE NOT is_active) AS jobs_inactive
FROM job;

\echo '== s1c: job table columns =='
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='job' ORDER BY ordinal_position;
