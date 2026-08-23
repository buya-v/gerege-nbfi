-- T287 ARM 2 STATE SNAPSHOT. Run BEFORE the closure is created, WHILE it exists, and AFTER
-- it is deleted. Wider than q3-writecheck.sql because arm 2 deliberately mutates the tenant
-- and every table it can touch must be watched, including the ones that only move forward.
--
-- m_portfolio_command_source is included because Fineract's command bus writes an audit row
-- for every executed write command. Those rows are APPEND-ONLY and are NOT undone by
-- deleting the closure -- they are part of the permanent residue and must be counted, not
-- discovered later.
--
-- Sequence last_value is watched separately from count(*) for the T276 reason: deleting a
-- row does not rewind its sequence, so "restored to 0 rows" and "restored to the prior
-- state" are DIFFERENT CLAIMS and only one of them will be true.
--
-- PostgreSQL. Read-only: every statement is a SELECT.
\pset pager off
SELECT count(*) AS office_rows, max(id) AS office_max_id FROM m_office;
SELECT count(*) AS je_rows, max(id) AS je_max_id, min(entry_date) AS earliest, max(entry_date) AS latest
FROM acc_gl_journal_entry;
SELECT count(*) AS closure_rows, max(id) AS closure_max_id FROM acc_gl_closure;
SELECT id, office_id, closing_date, is_deleted, comments FROM acc_gl_closure ORDER BY id;
SELECT last_value AS closure_seq_last_value, is_called FROM acc_gl_closure_id_seq;
SELECT last_value AS je_seq_last_value, is_called FROM acc_gl_journal_entry_id_seq;
SELECT count(*) AS command_source_rows, max(id) AS command_source_max_id FROM m_portfolio_command_source;
SELECT count(*) AS loan_rows FROM m_loan;
