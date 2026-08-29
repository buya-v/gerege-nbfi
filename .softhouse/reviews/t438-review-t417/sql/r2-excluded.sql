\pset footer off
\echo '== e1: row counts of the 8 excluded tables =='
SELECT 'batch_job_execution' t, count(*) FROM batch_job_execution
UNION ALL SELECT 'batch_job_execution_context', count(*) FROM batch_job_execution_context
UNION ALL SELECT 'batch_job_execution_params', count(*) FROM batch_job_execution_params
UNION ALL SELECT 'batch_job_instance', count(*) FROM batch_job_instance
UNION ALL SELECT 'batch_step_execution', count(*) FROM batch_step_execution
UNION ALL SELECT 'batch_step_execution_context', count(*) FROM batch_step_execution_context
UNION ALL SELECT 'job_run_history', count(*) FROM job_run_history
UNION ALL SELECT 'job', count(*) FROM job ORDER BY 1;
\echo '== e2: what is actually IN batch_job_execution_params / context (money? ledger?) =='
SELECT parameter_name, parameter_type, parameter_value FROM batch_job_execution_params LIMIT 20;
\echo '== e2b: contexts =='
SELECT job_execution_id, left(short_context, 300) FROM batch_job_execution_context LIMIT 10;
SELECT step_execution_id, left(short_context, 300) FROM batch_step_execution_context LIMIT 10;
\echo '== e3: the two NEAR-MISS tables that ARE graded =='
SELECT 'batch_custom_job_parameters' t, count(*) FROM batch_custom_job_parameters
UNION ALL SELECT 'job_parameters', count(*) FROM job_parameters;
