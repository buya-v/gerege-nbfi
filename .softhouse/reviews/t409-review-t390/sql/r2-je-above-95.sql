\pset pager off
-- Every journal entry above the registered floor 95, with authoring user and both timestamps.
SELECT j.id, j.transaction_id, j.account_id, j.type_enum, j.currency_code,
       j.amount, j.entry_date, j.created_by, j.last_modified_by,
       j.created_date, j.created_on_utc, j.reversed, j.loan_transaction_id, j.manual_entry
  FROM acc_gl_journal_entry j
 WHERE j.id > 95
 ORDER BY j.id;
