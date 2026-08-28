\pset pager off
-- ALL job runs in a wide window around the write, containment or not -- so a "nearby but not
-- containing" run cannot hide.
SELECT h.id AS jrh_id, h.job_id, j.name AS job_name, h.start_time, h.end_time, h.status,
       h.trigger_type, left(coalesce(h.error_message,''),60) AS err
  FROM job_run_history h JOIN job j ON j.id = h.job_id
 WHERE h.start_time >= TIMESTAMPTZ '2026-08-28 15:55:00+00'
   AND h.start_time <= TIMESTAMPTZ '2026-08-28 16:10:00+00'
 ORDER BY h.start_time;
