-- T305 M-1 -- IS THE ACCEPTING SIDE OF :812 AVAILABLE ON THIS DATABASE?  READ-ONLY.
--
-- The accepting side is the FALL-THROUGH of the guard T294 captured refusing:
--
--   JournalEntryWritePlatformServiceJpaRepositoryImpl.java:810-816
--     private void validateJournalEntriesArePostedBefore(final Long contraId) {
--         final List<String> transactionIds = this.glJournalEntryRepository.findNonContraTransactionIds(contraId);
--         if (!CollectionUtils.isEmpty(transactionIds)) { throw ... }
--     }
--
-- so the ACCEPT is taken exactly when findNonContraTransactionIds(contraId) is EMPTY.
-- That is one of the two conditions. THE OTHER FIVE ARE SETUP, and they are what this
-- query measures alongside it, because an empty ledger with no type-300 mapping does not
-- yield an ACCEPT -- it yields a DIFFERENT refusal at :708, and a rig that measured only
-- the emptiness would report "available" for a database on which the capture is impossible.
--
--   :708  findByFinancialActivityTypeWithNotFoundDetection(300)    must RESOLVE
--   :764-769 the type-300 account must be an EQUITY type (classification_enum = 3),
--            else error.msg.configuration.opening.balance.contra.account.value.is.invalid.account.type
--   :772  validateGLAccountForTransaction(contraAccount) -- DETAIL + manual allowed + not disabled
--   :719-720 the office must resolve
--   :777  organisationCurrencyRepository.findOneWithNotFoundDetection(currencyCode)
--   :780-796 every leg's GL account must resolve and pass validateGLAccountForTransaction
--
-- JournalEntryRepository.java:32-34, VERBATIM JPQL, translated with NOTHING hard-coded:
--   select DISTINCT j.transactionId from JournalEntry j
--    where j.transactionId not in
--          (select DISTINCT je.transactionId from JournalEntry je where je.glAccount.id = :contraId)
-- JournalEntry.java:52 maps glAccount -> column account_id; :63 maps transactionId -> transaction_id.

\echo '== A. the type-300 contra mapping (:708). Absent => a DIFFERENT refusal, not an accept.'
SELECT f.id, f.financial_activity_type, f.gl_account_id,
       a.gl_code, a.name, a.classification_enum, a.account_usage,
       a.manual_journal_entries_allowed, a.disabled
  FROM acc_gl_financial_activity_account f
  LEFT JOIN acc_gl_account a ON a.id = f.gl_account_id
 WHERE f.financial_activity_type = 300;

\echo '== B. findNonContraTransactionIds -- EMPTY is the accepting side of :812.'
SELECT count(*) AS non_contra_transaction_id_count
  FROM (SELECT DISTINCT j.transaction_id
          FROM acc_gl_journal_entry j
         WHERE j.transaction_id NOT IN (
                 SELECT DISTINCT je.transaction_id
                   FROM acc_gl_journal_entry je
                  WHERE je.account_id = (SELECT gl_account_id
                                           FROM acc_gl_financial_activity_account
                                          WHERE financial_activity_type = 300))) t;

\echo '== C. the raw ledger census: what is here at all.'
SELECT (SELECT count(*) FROM acc_gl_journal_entry)                      AS journal_entries,
       (SELECT count(DISTINCT transaction_id) FROM acc_gl_journal_entry) AS distinct_transaction_ids,
       (SELECT count(*) FROM acc_gl_account)                            AS gl_accounts,
       (SELECT count(*) FROM acc_gl_closure)                            AS gl_closures,
       (SELECT count(*) FROM m_office)                                  AS offices;

\echo '== D. the setup surface a capture would need: EQUITY DETAIL accounts and currencies.'
SELECT count(*) FILTER (WHERE classification_enum = 3 AND account_usage = 1
                          AND manual_journal_entries_allowed AND NOT disabled) AS equity_detail_postable,
       count(*) FILTER (WHERE account_usage = 1 AND manual_journal_entries_allowed AND NOT disabled) AS any_detail_postable,
       count(*)                                                        AS all_gl_accounts
  FROM acc_gl_account;

SELECT code, decimal_places, name FROM m_organisation_currency ORDER BY code;
