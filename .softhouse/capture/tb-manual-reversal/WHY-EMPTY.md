# WHY-EMPTY — why job 30 reports `success` and `m_trial_balance` stays empty

Written BEFORE any write, from the pinned source and a read-only baseline. This is step 0's
required answer. Nothing below is synthesised: every claim is tagged **[observed]** (live
tenant, this run), **[source]** (pinned `/Users/buv/fineract` @ `426a23544`) or
**[read-only SQL]** (the same fact read off the live tenant).

> **CONFIRMED LIVE (steps 4-6, 2026-09-11 02:31 UTC).** The prediction below was exact.
> Job 30 executed against `gerege` returned HTTP 202 but its run history recorded
> `failed`, and `m_trial_balance` stayed at 0 rows. The exception is the `:80` cast:
> `java.lang.ClassCastException: class java.time.OffsetDateTime cannot be cast to class
> java.time.LocalDate`. See `step04-job30/runhistory-after.json`,
> `step04-job30/job30-runhistory-sql.txt` (version 6, `failed`, `application`) and
> `step06-reason/REASON.md`. A second reversal pair was **not** posted: the cast fires on
> the first eligible date regardless of the entry, so a retry could not succeed.

## The baseline (this run, read-only)

| fact | value | file |
| --- | --- | --- |
| `m_trial_balance` row count | **0** | `raw/00-mtb-count.txt` |
| `acc_gl_journal_entry` count / max id | **110 / 140** | `raw/00-je-count-maxid.txt` |
| REST `GET /journalentries` max id | **140** (control passes) | `raw/00-control-sql-vs-rest.txt` |
| `entry_date` range / distinct dates | 2026-01-01 … 2026-09-03 (11 dates) | `raw/00-je-entry-date-range.txt`, `raw/00-je-distinct-entry-dates.txt` |
| `created_on_utc` range | 2026-09-06 10:59:16+00 … 2026-09-11 01:11:44+00 | `raw/00-je-created-on-utc-range.txt` |
| `transaction_date` column | **all 110 NULL** (legacy column, unused by the entity) | `raw/00-je-transaction-date-column.txt` |
| `created_date` column | **all 110 NULL** (legacy column, unused by the entity) | `raw/00-je-created-on-utc-nullcount.txt` |
| `reversed` flags | all false (110), `reversal_id` never set | `raw/00-je-reversed-counts.txt` |
| business date / COB | `2026-09-03` / `2026-09-02`, office 1 | `raw/00-businessdate.json` |
| GL closures | `[]` — no closure bounds any posting date | `raw/00-glclosures.json` |
| job 30 run history | 5 runs, all `success`, `triggerType: cron` | `raw/00-job30-runhistory.json` |

The SQL/REST control the brief demands holds: **SQL max id 140 = REST max id 140.** The two
counts differ (110 vs 104) because `GET /journalentries` omits ids 3–8 (six account-1
provisioning legs, `manual_entry=false`, `entity` NULL) — a REST projection choice, not a
stale database. `fineract-db-1` is untouched.

## What the tasklet does — and does not do

`UpdateTrialBalanceDetailsTasklet.execute` [`UpdateTrialBalanceDetailsTasklet.java:50`]
calls, in order:

1. `processTrialBalanceGaps(jdbcTemplate)` — `:53`
2. `updateClosingBalances(jdbcTemplate)` — `:54` (a no-op while the table is empty:
   `findDistinctOfficeIdsWithNullClosingBalance()` returns nothing — `:92`)

`processTrialBalanceGaps` — `:59-69`:

```
:60  LocalDate maxCreatedDate = trialBalanceRepository.findMaxCreatedDate();
:61  LocalDate baselineDate   = maxCreatedDate != null ? maxCreatedDate : LocalDate.of(2010, 1, 1);
:62  List<LocalDate> tbGaps    = journalEntryRepository.findTransactionDatesAfter(baselineDate);
:63  for (LocalDate tbGap : tbGaps) {
:64      if (DateUtils.getExactDifferenceInDays(tbGap, DateUtils.getBusinessLocalDate()) < 1) continue;
:67      insertTrialBalanceForDate(tbGap);
:68  }
```

`insertTrialBalanceForDate` — `:71-89`:

```
:74  rows.stream().map(row -> {
:76      tb.setOfficeId((Long) row[0]);
:77      tb.setGlAccountId((Long) row[1]);
:78      tb.setAmount((BigDecimal) row[2]);
:79      tb.setEntryDate((LocalDate) row[3]);
:80      tb.setTransactionDate((LocalDate) row[4]);   // <-- throws
:81      tb.setClosingBalance((BigDecimal) row[5]);
:85  trialBalanceRepositoryWrapper.save(trialBalances);
```

The query behind it, `JournalEntryRepository.findTrialBalanceLinesForDate`
[`JournalEntryRepository.java:52-66`], selects and `GROUP BY`s `je.createdDate` as `row[4]`.
`JournalEntry.createdDate` is inherited from `AbstractAuditableWithUTCDateTimeCustom`
[`:61`, type `OffsetDateTime`] and maps to column `created_on_utc`
[`AuditableFieldsConstants.java:29` — `CREATED_DATE_DB_FIELD = "created_on_utc"`].
So `row[4]` is an `OffsetDateTime`, not a `LocalDate`, and the cast at `:80` cannot succeed.

**Proven on the live oracle:** the `default` tenant runs the same tasklet daily and every run
with an eligible date fails with exactly this exception — `java.lang.ClassCastException:
class java.time.OffsetDateTime cannot be cast to class java.time.LocalDate … at
UpdateTrialBalanceDetailsTasklet.lambda$insertTrialBalanceForDate$0(…:80)`
(`evidence/default-tenant-job30-failure-2026-09-08.txt`, lines 34-47, 80-81). The exception
is thrown inside the `map` at `:83`, *before* `:85 save`, so the step rolls back and no row is
ever written. A run that finds eligible rows **FAILS**; it cannot populate the table.

### A second, independent break (source + schema, not exercised)

`TrialBalance extends AbstractPersistableCustom<Long>` (`TrialBalance.java:38`), whose `@Id`
is `@GeneratedValue(strategy = IDENTITY)` (`AbstractPersistableCustom.java:52-56`). The live
table has **no `id` column** — its columns are exactly `office_id, account_id, amount,
entry_date, created_date, closing_balance` (`raw/00-mtb-columns.txt`, `\d m_trial_balance`).
So even if `:80` were fixed, the Hibernate insert would target an identity column that does
not exist. The cast fires first, so this one is recorded but not exercised.

## Why five `success` runs left it empty

There are only two outcomes for `processTrialBalanceGaps`, and **neither writes a row**:

* `tbGaps` is empty, or every gap is skipped at `:64` → `save` is never reached →
  step COMPLETED, no row.
* some gap is eligible and its date has rows → `:80` throws → step FAILED, rolled back.

The five `gerege` cron runs (2026-09-05…09-09, 16:01) all landed in the first case. The
tenant's journal entries were created in two waves **[read-only SQL, `created_on_utc`]**:

* entry date `2026-09-01` **and only that date** existed from 2026-09-06 10:59 UTC;
* every other entry date — `2026-01-01 … 2026-08-01`, `2026-09-02` — was created
  **2026-09-10 02:06 … 04:06 UTC**, and `2026-09-03` **2026-09-11**, i.e. after the last cron
  run (`raw/00-je-created-by-entry-date.txt`).

So during those five runs the candidate set was at most `{2026-09-01}`, and `:64` skips any
gap of less than one day against the then-current business date. The later back-dated waves
have never been processed by a cron run. (The business date *then* is not directly readable
now — `m_business_date` holds only the current row — so the skip itself is **[inferred]**;
what is **[observed]** is that no other entry date existed to process.)

The consequence for this capture: the moment an entry date earlier than the business date by
≥ 1 day exists, the very next job-30 execution takes the second path and **fails at `:80`**.
Posting the manual entry back-dated to a date after the (empty) closure list and ≥ 1 day before
2026-09-03 makes that date eligible, so step 4 of this capture is expected to report a failure,
not a populated table. If it instead reports `success` with an empty table, the eligible set
was empty for a named reason and step 6 records it.

## `m_trial_balance` today cannot hold a trial balance of any window

Independently of the reversal under test: no build of this checkout can write a row to
`m_trial_balance`. The table's emptiness is over-determined by the `:80` cast, and (behind it)
by the missing `id` column. This is the answer to "why five successful runs left the table
empty" and the reason a captured per-account net must come from the journal entries, not from
the oracle's own table.
