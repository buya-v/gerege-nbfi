-- T390 Q1: every journal-entry row above id 95, with its provenance columns.
-- READ-ONLY. Asks who created L32/L33/L34 and by what path.
-- Column names taken from out/q0-je-columns.txt, not guessed (the first attempt named
-- createdby_id, which does not exist; the real column is created_by).
SELECT j.id,
       j.transaction_id,
       j.account_id,
       j.type_enum,
       j.amount,
       j.entry_date,
       j.created_date,
       j.created_on_utc,
       j.created_by,
       j.loan_transaction_id,
       j.entity_type_enum,
       j.manual_entry,
       j.description
FROM acc_gl_journal_entry j
WHERE j.id > 95
ORDER BY j.id;
