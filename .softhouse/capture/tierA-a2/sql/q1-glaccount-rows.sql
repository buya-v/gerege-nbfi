-- A2: what the oracle ACTUALLY STORES for a GL account tree.
-- The REST read (/glaccounts/{id}) returns `nameDecorated` but never `hierarchy`,
-- so the stored hierarchy string can only be observed here.
-- NOTE the column is `manual_journal_entries_allowed`, not `manual_entries_allowed`
-- (the JSON field is `manualEntriesAllowed` — the names differ across the boundary).
\pset border 2
SELECT id, parent_id, gl_code, name, classification_enum, account_usage,
       manual_journal_entries_allowed, disabled, hierarchy, tag_id
FROM acc_gl_account
ORDER BY id;
