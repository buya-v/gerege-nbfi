\echo === S04.1 every scheduled job in this tenant, with id, name, cron, active ===
SELECT id, name, display_name, cron_expression, is_active, next_run_time,
       previous_run_start_time, currently_running, task_priority
FROM job ORDER BY id;

\echo === S04.2 job 9 by name, exact ===
SELECT id, name, display_name, cron_expression, is_active, previous_run_start_time, next_run_time
FROM job WHERE display_name LIKE '%%Running Balance%%' OR name LIKE '%%RUNNING_BALANCE%%';

\echo === S04.3 recent job_run_history, most recent 40 ===
SELECT id, job_id, version, start_time, end_time, status, trigger_type
FROM job_run_history ORDER BY id DESC LIMIT 40;

\echo === S04.4 job 9 run history, all of it ===
SELECT h.id, h.job_id, j.display_name, h.start_time, h.end_time, h.status, h.trigger_type
FROM job_run_history h JOIN job j ON j.id = h.job_id
WHERE j.display_name LIKE '%%Running Balance%%' ORDER BY h.id;
