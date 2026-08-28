\pset pager off
-- T390's instrument header and FU-T390-4 both say "Nineteen jobs read is_active = t in this
-- tenant". T391 says 31 of 41. Measured here.
SELECT count(*) AS total_jobs,
       count(*) FILTER (WHERE is_active) AS active,
       count(*) FILTER (WHERE NOT is_active) AS inactive
  FROM job;
SELECT id, name, is_active, cron_expression, scheduler_group
  FROM job ORDER BY id;
-- how many DISTINCT jobs actually ran in the 24h to now?
SELECT count(DISTINCT job_id) AS distinct_jobs_run_last_24h, count(*) AS runs
  FROM job_run_history
 WHERE start_time >= (now() AT TIME ZONE 'UTC') - INTERVAL '24 hours';
