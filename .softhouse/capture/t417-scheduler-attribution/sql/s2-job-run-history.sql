\echo '== s2a: job_run_history columns =='
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='job_run_history' ORDER BY ordinal_position;

\echo '== s2b: high-water mark and span =='
SELECT count(*) AS rows, min(id) AS min_id, max(id) AS max_id,
       min(start_time) AS min_start, max(start_time) AS max_start, max(end_time) AS max_end
FROM job_run_history;

\echo '== s2c: which jobs ran in the last 24h (job-table time is naive UTC) =='
SELECT h.job_id, j.name, j.is_active, count(*) AS runs_24h,
       min(h.start_time) AS first_24h, max(h.start_time) AS last_24h,
       count(*) FILTER (WHERE h.status <> 'success') AS non_success
FROM job_run_history h JOIN job j ON j.id=h.job_id
WHERE h.start_time >= (now() AT TIME ZONE 'UTC') - interval '24 hours'
GROUP BY h.job_id, j.name, j.is_active ORDER BY h.job_id;

\echo '== s2d: jobs that are ACTIVE but have NEVER appeared in job_run_history =='
SELECT j.id, j.name, j.cron_expression, j.previous_run_start_time
FROM job j WHERE j.is_active AND NOT EXISTS (SELECT 1 FROM job_run_history h WHERE h.job_id=j.id)
ORDER BY j.id;

\echo '== s2e: the 2026-08-28 16:01 sweep, every run overlapping that minute =='
SELECT h.id, h.job_id, j.name, h.start_time, h.end_time, h.status,
       left(coalesce(h.error_message,''),60) AS err
FROM job_run_history h JOIN job j ON j.id=h.job_id
WHERE h.start_time < timestamp '2026-08-28 16:02:00' AND h.end_time > timestamp '2026-08-28 16:00:00'
ORDER BY h.start_time;

\echo '== s2f: every DISTINCT job that has EVER run, with its total run count =='
SELECT h.job_id, j.name, j.is_active, count(*) AS runs_all_time
FROM job_run_history h LEFT JOIN job j ON j.id=h.job_id
GROUP BY h.job_id, j.name, j.is_active ORDER BY h.job_id;
