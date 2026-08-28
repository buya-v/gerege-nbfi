\pset pager off
-- EVERY job run whose [start_time, end_time] interval CONTAINS the first and/or last leg write.
-- The two write instants are read literally from acc_gl_journal_entry, not typed.
WITH w AS (
  SELECT min(created_on_utc) AS first_write, max(created_on_utc) AS last_write
    FROM acc_gl_journal_entry WHERE id BETWEEN 96 AND 113
)
SELECT h.id AS jrh_id, h.job_id, j.name AS job_name, j.display_name,
       h.start_time, h.end_time, h.status,
       (h.start_time <= w.first_write AND h.end_time >= w.last_write) AS contains_all_legs,
       (h.start_time <= w.first_write AND h.end_time >= w.first_write) AS contains_first,
       (h.start_time <= w.last_write  AND h.end_time >= w.last_write)  AS contains_last
  FROM job_run_history h JOIN job j ON j.id = h.job_id, w
 WHERE h.start_time <= w.last_write AND h.end_time >= w.first_write
 ORDER BY h.start_time;
