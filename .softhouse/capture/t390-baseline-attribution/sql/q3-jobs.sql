-- T390 Q3: the scheduler. Which jobs are active, and when did each last run?
SELECT id, display_name, cron_expression, is_active, currently_running,
       previous_run_start_time, next_run_time, task_priority
FROM job
ORDER BY id;
