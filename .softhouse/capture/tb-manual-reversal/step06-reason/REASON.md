# Step 6 — why `m_trial_balance` is still empty after a successful-looking job 30

Observed on the live `gerege` oracle, run of 2026-09-11 02:31:02 UTC. The manual
execution of job 30 did **not** report `success`: it reported `failed`, and the table
stayed at 0 rows. The reason is a hard `ClassCastException` in the tasklet, thrown
**before** any insert.

## The failure, verbatim

`POST /jobs/30?command=executeJob` → HTTP 202. `/jobs/30/runhistory` version 6:

```
status: failed
triggerType: application
jobRunStartTime: 2026-09-11T02:31:02.915Z
jobRunEndTime:   2026-09-11T02:31:02.939Z
java.lang.ClassCastException: class java.time.OffsetDateTime cannot be cast to
class java.time.LocalDate
    at ...UpdateTrialBalanceDetailsTasklet
        .lambda$insertTrialBalanceForDate$0(UpdateTrialBalanceDetailsTasklet.java:80)
    at ...UpdateTrialBalanceDetailsTasklet
        .insertTrialBalanceForDate(UpdateTrialBalanceDetailsTasklet.java:83)
    at ...UpdateTrialBalanceDetailsTasklet
        .processTrialBalanceGaps(UpdateTrialBalanceDetailsTasklet.java:67)
    at ...UpdateTrialBalanceDetailsTasklet
        .execute(UpdateTrialBalanceDetailsTasklet.java:53)
```

(Full text: `step04-job30/runhistory-after.json`, `error_message`/`error_log`.)

## The code path, with `file:line`

Pinned `/Users/buv/fineract` @ `426a23544`. Paths abbreviated below; full paths:

* tasklet: `fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/jobs/updatetrialbalancedetails/UpdateTrialBalanceDetailsTasklet.java`
* repository: `fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/domain/JournalEntryRepository.java`
* model: `fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/domain/JournalEntry.java`
* audit base: `fineract-core/src/main/java/org/apache/fineract/infrastructure/core/domain/AbstractAuditableWithUTCDateTimeCustom.java`

1. `UpdateTrialBalanceDetailsTasklet.java:53` → `processTrialBalanceGaps(jdbcTemplate)`.
2. `UpdateTrialBalanceDetailsTasklet.java:62`
   `journalEntryRepository.findTransactionDatesAfter(baselineDate)` returns the eligible
   entry dates; `baselineDate` is `LocalDate.of(2010,1,1)` because
   `trialBalanceRepository.findMaxCreatedDate()` is `null` on an empty table
   (`:60-61`).
3. `UpdateTrialBalanceDetailsTasklet.java:67` → `insertTrialBalanceForDate(tbGap)` for
   the first date ≥ 1 day before the business date.
4. `UpdateTrialBalanceDetailsTasklet.java:72` calls
   `journalEntryRepository.findTrialBalanceLinesForDate(tbGap)`.
5. `JournalEntryRepository.java:52-66` — the JPQL selects, in order:
   `je.office.id` (row[0]), `je.glAccount.id` (row[1]),
   `SUM(CASE WHEN je.type = 1 THEN -1 * je.amount ELSE je.amount END)` (row[2], `BigDecimal`),
   `je.transactionDate` (row[3], `LocalDate`),
   **`je.createdDate` (row[4])**,
   `SUM(je.amount)` (row[5], `BigDecimal`).
6. `JournalEntry.java:41` — `public class JournalEntry extends
   AbstractAuditableWithUTCDateTimeCustom<Long>`.
7. `AbstractAuditableWithUTCDateTimeCustom.java:59-61` — the inherited `createdDate`
   field is declared `private OffsetDateTime createdDate;` mapped to column
   `created_on_utc` (`AuditableFieldsConstants.CREATED_DATE_DB_FIELD`, verified in the
   live schema: `step06-reason/row4-type.txt` — `timestamp with time zone`).
8. `UpdateTrialBalanceDetailsTasklet.java:80` —
   `tb.setTransactionDate((LocalDate) row[4]);` casts that `OffsetDateTime` to
   `LocalDate` → `ClassCastException`.

The `map(...).toList()` at `:74-83` is terminal, so the exception fires while building
the list; `trialBalanceRepositoryWrapper.save(trialBalances)` at `:85` is never reached.
The step rolls back and **no row is ever written** — hence an empty `m_trial_balance`
after a run that found eligible rows.

## Why the five cron runs said `success` but wrote nothing

`processTrialBalanceGaps` has two non-writing outcomes and one failing outcome
(`WHY-EMPTY.md` has the full argument):

* no eligible gap (empty, or skipped at `:64` because it is < 1 day before the business
  date) → step COMPLETED, no insert;
* an eligible gap → `:80` throws → step FAILED, rollback, no insert.

The five recorded cron runs (2026-09-05…09-09, versions 1-5) all fell in the first
bucket. This manual run is the first execution that faced an eligible gap — entry date
`2026-06-15`, months before the business date `2026-09-03` — so it took the failing
path. The `success` in `m_trial_balance`'s history was therefore never evidence that a
trial balance was written.

## Conclusion (the brief's step 6)

**Stop. No retry.** The failure is independent of the entry/reversal under test: it
fires on the first eligible date for every date, because `created_on_utc` is non-null on
all 114 journal-entry rows (`step05-trial-balance/je-count-maxid.txt`; baseline
`raw/00-je-created-on-utc-nullcount.txt` = 110 non-null / 0 null). A second
manual-reversal pair cannot change the cast and would only add rows. It is not posted.

The expected net was therefore taken from the journal entries (`step05-trial-balance/
equiv-query-2026-06-15.txt`), not from an oracle-written trial-balance row. No value is
synthesised: every figure in `OWNER.md` is either read off the live tenant or produced by
a read-only SQL transcription of `JournalEntryRepository.java:52-66`.
