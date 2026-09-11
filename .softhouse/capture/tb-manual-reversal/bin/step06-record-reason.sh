#!/bin/bash
# OH-TBCAP-Y step 6 -- record, from source, why job 30 leaves m_trial_balance empty
# on the live gerege tenant, and the batch/job rows the failed execution added.
set -u
DIR=$(cd "$(dirname "$0")/.." && pwd)
OUT="$DIR/step06-reason"
mkdir -p "$OUT"
PSQL="docker exec gerege-oracle-db psql -U postgres -d fineract_gerege"

# the failed run's Spring Batch rows
{
  $PSQL -c "SELECT job_instance_id, job_name FROM batch_job_instance WHERE job_instance_id=10046"
  $PSQL -c "SELECT job_execution_id, job_instance_id, create_time, start_time, end_time, status, exit_code FROM batch_job_execution WHERE job_execution_id=10046"
  $PSQL -c "SELECT step_execution_id, job_execution_id, step_name, status, exit_code FROM batch_step_execution WHERE job_execution_id=10046"
  $PSQL -c "SELECT * FROM batch_job_execution_params WHERE job_execution_id=10046"
  $PSQL -c "SELECT job_execution_id, length(short_context) FROM batch_job_execution_context WHERE job_execution_id=10046"
} > "$OUT/batch-rows-10046.txt" 2>&1

# the failing cast's inputs, read off the row the tasklet would have consumed:
# row[4] is je.createdDate -> abstract audit field, type OffsetDateTime.
$PSQL -c "SELECT id, transaction_id, account_id, entry_date, type_enum, amount, reversed, reversal_id, created_on_utc, pg_typeof(created_on_utc) AS created_on_utc_type FROM acc_gl_journal_entry WHERE id IN (141,142,143,144) ORDER BY id" > "$OUT/row4-type.txt" 2>&1

echo "=== batch rows 10046 ==="; cat "$OUT/batch-rows-10046.txt"
echo "=== row[4] source type ==="; cat "$OUT/row4-type.txt"
