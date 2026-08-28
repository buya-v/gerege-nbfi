-- T352. The three probe entries, read straight out of the column, plus the
-- column's own declared type. PostgreSQL only (CLAUDE.md); no other engine path.
\pset footer off

SELECT column_name, data_type, numeric_precision, numeric_scale
  FROM information_schema.columns
 WHERE table_name = 'acc_gl_journal_entry' AND column_name = 'amount';

SELECT id,
       transaction_id,
       account_id,
       type_enum,
       currency_code,
       amount::text          AS amount_text,
       scale(amount)         AS stored_scale,
       reversed,
       manual_entry,
       entry_date
  FROM acc_gl_journal_entry
 WHERE transaction_id IN ('a29bca0816a7', 'a29bca9bf813', 'a29bcaa6a41b')
 ORDER BY transaction_id, id;

-- Does the residue survive an aggregate? Debits and credits per probe txn.
SELECT transaction_id,
       type_enum,
       count(*)                AS legs,
       sum(amount)::text       AS sum_amount_text
  FROM acc_gl_journal_entry
 WHERE transaction_id IN ('a29bca0816a7', 'a29bca9bf813', 'a29bcaa6a41b')
 GROUP BY transaction_id, type_enum
 ORDER BY transaction_id, type_enum;
