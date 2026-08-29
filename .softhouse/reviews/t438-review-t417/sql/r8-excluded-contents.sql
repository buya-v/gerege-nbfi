\pset footer off
\echo '== distinct parameter names across ALL batch_job_execution_params =='
SELECT parameter_name, parameter_type, count(*) FROM batch_job_execution_params GROUP BY 1,2 ORDER BY 3 DESC;
\echo '== distinct taskletTypes seen in batch_step_execution_context =='
SELECT substring(short_context from '"batch.taskletType":"([^"]*)"') AS tasklet, count(*)
FROM batch_step_execution_context GROUP BY 1 ORDER BY 2 DESC;
\echo '== distinct job_name in batch_job_instance =='
SELECT job_name, count(*) FROM batch_job_instance GROUP BY 1 ORDER BY 2 DESC;
\echo '== any decimal/numeric column ANYWHERE in the 8 excluded tables? =='
SELECT count(*) AS numeric_cols FROM information_schema.columns
WHERE table_schema='public'
  AND table_name IN ('batch_job_execution','batch_job_execution_context','batch_job_execution_params','batch_job_instance','batch_step_execution','batch_step_execution_context','job_run_history','job')
  AND data_type IN ('numeric','decimal','double precision','real','money');
