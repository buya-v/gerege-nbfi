\pset pager off
-- The containment test above compared a `timestamp without time zone` (job_run_history) with a
-- `timestamp with time zone` (acc_gl_journal_entry.created_on_utc). Postgres resolves that with
-- an implicit cast that depends on the SESSION TimeZone. Show the setting, then REDO the test
-- with the conversion written out explicitly so the answer cannot depend on it.
SHOW TimeZone;
SELECT current_setting('TimeZone') AS session_tz, now() AS now_tz;
WITH w AS (
  SELECT min(created_on_utc AT TIME ZONE 'UTC') AS first_write,
         max(created_on_utc AT TIME ZONE 'UTC') AS last_write
    FROM acc_gl_journal_entry WHERE id BETWEEN 96 AND 113
)
SELECT h.id AS jrh_id, h.job_id, j.name,
       h.start_time, h.end_time, w.first_write, w.last_write,
       (h.start_time <= w.first_write AND h.end_time >= w.last_write) AS contains_all
  FROM job_run_history h JOIN job j ON j.id=h.job_id, w
 WHERE h.start_time <= w.last_write AND h.end_time >= w.first_write
 ORDER BY h.start_time;
