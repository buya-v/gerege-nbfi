-- A2-15: the ledger's row-level ground truth, as JSON, re-observed on the LIVE
-- reference oracle at promotion time.
--
-- WHY THIS EXISTS BESIDE q4. q4 emits a psql TABLE, which is what a human reads
-- and what A2-370 and A2-390 record. It is NOT parseable as JSON, and
-- `.softhouse/capture/lib/check_wire_float_roundtrip.py` REFUSES a capture record
-- that a stored vector cites and that cannot be parsed as JSON -- correctly, since
-- the evidence a parity vector was transcribed FROM is exactly what it exists to
-- certify. A2-15 hit that refusal on its first run and this file is the answer:
-- the same observation, emitted in the shape the guard can open.
--
-- WHY IT IS RE-RUN RATHER THAN CITED FROM A2-370 (P-69). A2-370 is a SNAPSHOT and
-- the oracle has moved since it was taken: A2-29 added two GL accounts, three
-- manual journal entries, a reversal, a retype and six running-balance
-- recalculations. Citing A2-370's numbers would be citing a state this oracle has
-- left.
--
-- IT DOES NOT PROJECT office_running_balance OR organization_running_balance, and
-- that is deliberate rather than an oversight. GATE G-12 is open on exactly those
-- two columns and A2-29 MEASURED them to be a SECOND SOURCE OF TRUTH rather than a
-- cache. A capture that carried them would invite a later vector to grade one.
--
-- Read-only. Every statement is a SELECT.
\pset border 0
\pset format unaligned
\pset tuples_only on

SELECT json_build_object(
  'capture_case_id', 'A2-390-db-ledger-state-a2-15',
  'seam', 'ledger_db_readback',
  'note', 'A2-15 re-observation of the ledger state on the live reference oracle. '
          'Amounts are acc_gl_journal_entry.amount, numeric(19,6), rendered as the '
          'oracle stores them. No running-balance column is projected (G-12).',
  'accounts', (
    SELECT json_agg(a ORDER BY a.id) FROM (
      SELECT id, parent_id, gl_code, name, classification_enum, account_usage,
             manual_journal_entries_allowed, disabled
      FROM acc_gl_account
    ) a
  ),
  'journal_entries', (
    SELECT json_agg(j ORDER BY j.id) FROM (
      SELECT e.id, e.transaction_id, e.transaction_date, e.type_enum,
             e.account_id, g.gl_code, g.name AS gl_name,
             g.classification_enum AS gl_classification_today,
             e.amount::text AS amount_text, e.currency_code,
             e.manual_entry, e.reversed, e.reversal_id,
             e.entity_type_enum, e.entity_id, e.loan_transaction_id
      FROM acc_gl_journal_entry e JOIN acc_gl_account g ON g.id = e.account_id
    ) j
  ),
  'per_transaction_minor_units', (
    SELECT json_agg(t ORDER BY t.first_id) FROM (
      SELECT transaction_id,
             count(*) AS legs,
             min(id) AS first_id,
             sum(CASE WHEN type_enum = 2 THEN (amount * 100)::numeric(19,0) ELSE 0 END)::text
               AS debit_minor,
             sum(CASE WHEN type_enum = 1 THEN (amount * 100)::numeric(19,0) ELSE 0 END)::text
               AS credit_minor,
             bool_and(amount * 100 = (amount * 100)::numeric(19,0))
               AS every_leg_is_a_whole_minor_unit
      FROM acc_gl_journal_entry GROUP BY transaction_id
    ) t
  ),
  'leg_count_distribution', (
    SELECT json_agg(d ORDER BY d.legs) FROM (
      SELECT legs, count(*) AS transactions FROM (
        SELECT transaction_id, count(*) AS legs
        FROM acc_gl_journal_entry GROUP BY transaction_id
      ) x GROUP BY legs
    ) d
  ),
  'distinct_currency_codes', (
    SELECT json_agg(DISTINCT currency_code) FROM acc_gl_journal_entry
  )
)::text;
