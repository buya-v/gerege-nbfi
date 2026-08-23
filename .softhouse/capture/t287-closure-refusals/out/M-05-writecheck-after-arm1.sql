-- T287 WRITE-CHECK. Run BEFORE and AFTER every refusal probe.
--
-- "A refused write writes nothing" is a CLAIM until it is measured. This is the measurement.
-- If the before/after pair is identical the claim holds for that probe; if it is not, the
-- probe had a side effect and that is the finding, not something to suppress.
--
-- max(id) is included deliberately and separately from count(*): a sequence counter can
-- advance without a row surviving (T276 learned this the expensive way on
-- acc_product_mapping), and only max(id) can see that.
--
-- PostgreSQL. Read-only: every statement is a SELECT.
\pset pager off
SELECT count(*) AS je_rows, max(id) AS je_max_id, min(entry_date) AS earliest, max(entry_date) AS latest
FROM acc_gl_journal_entry;
SELECT count(*) AS closure_rows, max(id) AS closure_max_id FROM acc_gl_closure;
SELECT count(*) AS payment_detail_rows, max(id) AS payment_detail_max_id FROM m_payment_detail;
SELECT last_value AS je_seq_last_value, is_called FROM acc_gl_journal_entry_id_seq;
