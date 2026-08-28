-- T388 BEFORE SNAPSHOT, part 3. Per-GL-account journal-entry counts, with the
-- column name taken from information_schema (out/T388-B02-before-per-account.txt
-- section A) rather than guessed: acc_gl_account.manual_journal_entries_allowed.
-- Read-only.
\echo '=== PER-GL-ACCOUNT journal entry counts BEFORE T388 -- EVERY account, LEFT JOIN so zero is printed ==='
SELECT a.id AS gl_id, a.gl_code, a.name, a.classification_enum, a.account_usage,
       a.manual_journal_entries_allowed AS manual_ok, a.disabled,
       count(j.id) AS je_rows
FROM acc_gl_account a
LEFT JOIN acc_gl_journal_entry j ON j.account_id = a.id
GROUP BY a.id, a.gl_code, a.name, a.classification_enum, a.account_usage, a.manual_journal_entries_allowed, a.disabled
ORDER BY a.id;
\echo '=== distinct currency codes present in the ledger ==='
SELECT currency_code, count(*) FROM acc_gl_journal_entry GROUP BY 1 ORDER BY 1;
