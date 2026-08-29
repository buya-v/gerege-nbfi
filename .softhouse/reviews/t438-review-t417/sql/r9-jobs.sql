\pset footer off
\echo '== all 41 jobs =='
SELECT id, is_active, cron_expression, name FROM job ORDER BY id;
\echo '== jobs with NO run history =='
SELECT id, is_active, name FROM job j WHERE NOT EXISTS (SELECT 1 FROM job_run_history h WHERE h.job_id=j.id) ORDER BY id;
\echo '== active jobs with NO run history =='
SELECT id, name FROM job j WHERE is_active AND NOT EXISTS (SELECT 1 FROM job_run_history h WHERE h.job_id=j.id) ORDER BY id;
\echo '== distinct jobs ever in history =='
SELECT count(DISTINCT job_id) FROM job_run_history;
