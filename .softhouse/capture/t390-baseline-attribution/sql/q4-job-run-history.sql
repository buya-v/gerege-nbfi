-- T390 Q4: the scheduler's own run history for the accrual jobs, around the moment
-- L32/L33/L34 were written (2026-08-28 16:01:00.10 UTC).
-- Job 11 = "Add Accrual Transactions"          cron 0 1 0 1/1 * ? *
-- Job 16 = "Add Periodic Accrual Transactions" cron 0 2 0 1/1 * ? *
SELECT h.id, h.job_id, j.display_name, h.version, h.start_time, h.end_time, h.status,
       left(coalesce(h.error_message,''), 120) AS error_message
FROM job_run_history h
JOIN job j ON j.id = h.job_id
WHERE h.start_time > TIMESTAMP '2026-08-28 15:00:00'
ORDER BY h.start_time, h.id;
