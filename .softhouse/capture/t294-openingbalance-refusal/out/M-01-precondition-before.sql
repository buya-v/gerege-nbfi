-- T294 -- THE PRECONDITION OF THE REFUSAL, READ-ONLY, RE-DERIVED FROM SOURCE.
--
-- JournalEntryWritePlatformServiceJpaRepositoryImpl.java:703 defineOpeningBalance(JsonCommand)
--   :708  findByFinancialActivityTypeWithNotFoundDetection(300)  -- must RESOLVE, or a
--         different error is returned first and this is not the refusal we captured
--   :709  contraId = that mapping's GL account id
--   :717  validateJournalEntriesArePostedBefore(contraId)
--   :810-816  throws error.msg.journalentry.defining.openingbalance.not.allowed when
--         findNonContraTransactionIds(contraId) is NON-EMPTY.
--
-- JournalEntryRepository.java:32-34, VERBATIM JPQL:
--   select DISTINCT j.transactionId from JournalEntry j
--    where j.transactionId not in
--          (select DISTINCT je.transactionId from JournalEntry je where je.glAccount.id = :contraId)
--
-- JournalEntry.java:52 maps glAccount to column account_id; :63 maps transactionId to
-- column transaction_id. The statements below are that JPQL translated to SQL with NOTHING
-- hard-coded: contraId is derived here exactly as the Java derives it.
SELECT id, financial_activity_type, gl_account_id
  FROM acc_gl_financial_activity_account
 WHERE financial_activity_type = 300;

SELECT count(*) AS non_contra_transaction_id_count
  FROM (SELECT DISTINCT j.transaction_id
          FROM acc_gl_journal_entry j
         WHERE j.transaction_id NOT IN (
                 SELECT DISTINCT je.transaction_id
                   FROM acc_gl_journal_entry je
                  WHERE je.account_id = (SELECT gl_account_id
                                           FROM acc_gl_financial_activity_account
                                          WHERE financial_activity_type = 300))) t;

SELECT count(*) AS contra_account_entry_count
  FROM acc_gl_journal_entry
 WHERE account_id = (SELECT gl_account_id
                       FROM acc_gl_financial_activity_account
                      WHERE financial_activity_type = 300);
