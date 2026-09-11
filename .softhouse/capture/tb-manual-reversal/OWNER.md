# OWNER — OH-TBCAP-Y: the oracle's trial balance across a manual reversal

**Capture only.** No Go was written, no vector promoted, no `nexus/` file touched. Every
write went through the oracle REST API on tenant `gerege`; every SQL read was `SELECT`-only
against `gerege-oracle-db` (never `fineract-db-1`, never `default`). Nothing below is
synthesised: each figure is tagged **[REST]**, **[SQL]** (read-only live tenant),
**[wire]** (transcribed from an oracle response as a string), or **[source]** (pinned
`/Users/buv/fineract` @ `426a23544`). Money is integer **minor units**; wire decimals are
strings.

## Headline

1. The finding's reversal shape is **CONFIRMED [REST][SQL]**: the manual reversal flagged
   the original two legs (`reversed = true`, `reversal_id` set) and posted an **unflagged**
   counter-entry pair (`reversed = false`) on a new transaction id.
2. **No oracle trial-balance row was ever observed, and none can be, on this build.** The
   manual execution of job 30 **FAILED** — `java.lang.ClassCastException:
   java.time.OffsetDateTime cannot be cast to java.time.LocalDate` at
   `UpdateTrialBalanceDetailsTasklet.java:80` — and `m_trial_balance` stayed at **0 rows**.
   Full source trail: `step06-reason/REASON.md`. The five earlier `success` cron runs wrote
   nothing because they never found an eligible date; this is the first execution that did,
   and it threw before the insert.
3. `DeriveTrialBalance` and the oracle therefore **disagree by the reversed amount** — but
   the oracle side of that disagreement is its query semantics over the journal rows, not a
   written `m_trial_balance` row. See "The disagreement" below.

## The one manual entry and its one reversal

Posted `2026-06-15` (after the empty closure list, 80 days before the `2026-09-03` business
date), office 1, reference `OHTBCAPY-1`. All amounts **1234567 minor units** (wire string
`"12345.67"`).

| JE id | txn id | account | side | amount (minor) | reversed | reversal_id | created_on_utc (SQL) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 141 | `a2b795dca42b` | 6 `OHLGR-Transfers-Suspense` (ASSET) | DEBIT (`type_enum` 2) | 1234567 | **true** | 143 | 2026-09-11 02:29:29.802931+00 |
| 142 | `a2b795dca42b` | 10 `OHLGR-Fund-Source` (LIABILITY) | CREDIT (`type_enum` 1) | 1234567 | **true** | 144 | 2026-09-11 02:29:29.80519+00 |
| 143 | `a2b7964aa51b` | 6 `OHLGR-Transfers-Suspense` (ASSET) | CREDIT (`type_enum` 1) | 1234567 | **false** | — | 2026-09-11 02:30:41.894728+00 |
| 144 | `a2b7964aa51b` | 10 `OHLGR-Fund-Source` (LIABILITY) | DEBIT (`type_enum` 2) | 1234567 | **false** | — | 2026-09-11 02:30:41.897944+00 |

Sources: `step03-readback/rest-orig.json`, `step03-readback/rest-rev.json`,
`step03-readback/sql-rows.txt`; reversal response `step02-reverse/response.json`
(`{"transactionId":"a2b7964aa51b"}`, HTTP 200).

This is exactly the finding's claim: original legs flagged, counter legs not. The loan
path's "same transaction id, flag nothing" shape did **not** occur here — this is the
manual path.

## What each step produced, and where it is

| step | action | files |
| --- | --- | --- |
| 0 | read-only baseline | `raw/00-*` (see WHY-EMPTY.md for the table) |
| 1 | POST one manual entry | `req/01-post-manual-entry.json`, `step01-post/{request,response,readback-rest,readback-sql,control-count-maxid,meta}*` |
| 2 | POST `…?command=reverse` | `req/02-reverse.json`, `step02-reverse/{request,response}*` |
| 3 | REST + SQL readback of both txn ids | `step03-readback/{rest-orig,rest-rev}.json`, `sql-rows.txt`, `sql-control-count-maxid.txt`, `meta.txt` |
| 4 | POST `…?command=executeJob` + poll run history | `step04-job30/{execute-response,runhistory-before,runhistory-poll-1,runhistory-after}.json`, `job30-runhistory-sql.txt` |
| 5 | read `m_trial_balance` + query-equivalent | `step05-trial-balance/{mtb-count,mtb-all-rows,mtb-columns,equiv-query-2026-06-15,je-count-maxid}.txt` |
| 6 | source reason for the empty table | `step06-reason/{REASON.md,row4-type.txt,batch-rows-10046.txt}` |

### Controls that make the reads trustworthy

* Baseline SQL vs REST **[SQL][REST]**: `acc_gl_journal_entry` max id **140** = REST
  `GET /journalentries` max id **140** (`raw/00-control-sql-vs-rest.txt`). The 110-vs-104
  count gap is REST dropping the six non-manual provisioning legs, not a stale DB.
* After the capture **[SQL][REST]**: `acc_gl_journal_entry` count/max id **114 / 144**, and
  REST returns ids up to **144** (rows 143/144 read back above). The live instance, not
  `fineract-db-1`, answered every read.
* Business date **[REST]**: `2026-09-03` (COB `2026-09-02`); unchanged by this capture.
* GL closures **[REST]**: `[]` — no date is bounded, as at step 0.

## The oracle's trial balance for these rows

**Rows the oracle wrote: none.** Job 30's manual run is `version 6`, `status = failed`,
`triggerType = application` (`step04-job30/job30-runhistory-sql.txt`). `m_trial_balance`
read after the run: **0 rows**, all columns (`step05-trial-balance/mtb-all-rows.txt`).
The step threw inside the stream map at `:80` before
`trialBalanceRepositoryWrapper.save(...)` at `:85`, so nothing was persisted.

The **per-account lines the oracle's query would have produced** for `entry_date
2026-06-15`, obtained by a read-only SQL transcription of
`JournalEntryRepository.findTrialBalanceLinesForDate` (`JournalEntryRepository.java:52-66`),
are in `step05-trial-balance/equiv-query-2026-06-15.txt`:

| office | account | amount (minor) | entry_date | created_on_utc | closing_balance (minor) |
| --- | --- | --- | --- | --- | --- |
| 1 | 6 | +1234567 | 2026-06-15 | 2026-09-11 02:29:29.802931+00 | 1234567 |
| 1 | 6 | -1234567 | 2026-06-15 | 2026-09-11 02:30:41.894728+00 | 1234567 |
| 1 | 10 | -1234567 | 2026-06-15 | 2026-09-11 02:29:29.80519+00 | 1234567 |
| 1 | 10 | +1234567 | 2026-06-15 | 2026-09-11 02:30:41.897944+00 | 1234567 |

These four rows are **not** an oracle output and must not be graded as one: the query
groups by `je.createdDate` as well as account/date, which is why the reversed pair appears
as two opposite rows per account rather than one net row. They are presented only to show
what the failed insert would have contained, and to make the "nets to zero" claim concrete.

### Does the reversed pair net to zero in the oracle's own table?

* In `m_trial_balance`: **vacuously yes, because there are no rows at all.** The table is
  empty; the pair contributes nothing to it because the job failed before writing.
* In the oracle's **query semantics over the journals**: **yes, per account.**
  Account 6: +1234567 (141, debit) and −1234567 (143, credit) sum to **0**. Account 10:
  −1234567 (142, credit) and +1234567 (144, debit) sum to **0**. There is no `reversed`
  predicate in the query, so both legs of each pair are included and cancel.

Both statements are true and they are different. The finding's premise — the oracle's trial
balance "sums every entry", so a reversed pair nets to zero — is confirmed at the level of
the query. It has **never** been confirmed at the level of a persisted oracle row, because
no such row can be produced by this build.

## What `DeriveTrialBalance` produces on the same rows

Read, not modified: `nexus/internal/apps/ledger/trialbalance.go` (`DeriveTrialBalance`,
`:28-45`; skip at `:31-33`, then debits/credits accumulate at `:36-41`, `Net = debits −
credits` at `:23`). Side comes from `type_enum`: 2 = DEBIT, 1 = CREDIT.

Input = the four observed rows 141, 142, 143, 144.

* 141 (acct 6, DEBIT, 1234567) — `Reversed` → **skipped**
* 142 (acct 10, CREDIT, 1234567) — `Reversed` → **skipped**
* 143 (acct 6, CREDIT, 1234567) — counted: acct 6 credits += 1234567
* 144 (acct 10, DEBIT, 1234567) — counted: acct 10 debits += 1234567

| account | TotalDebits | TotalCredits | Net (debits − credits) |
| --- | --- | --- | --- |
| 6 (ASSET) | 0 | 1234567 | **−1234567** |
| 10 (LIABILITY) | 1234567 | 0 | **+1234567** |

### The disagreement

* Oracle query semantics per account: **0** for account 6, **0** for account 10.
* `DeriveTrialBalance` per account: **−1234567** for account 6, **+1234567** for account 10.
* Delta: **1234567 minor units per account — exactly the reversed amount.** They
  **disagree**, in the direction and for the reason the finding states: the port drops the
  flagged original *and* keeps the unflagged counter-entry, removing the position twice;
  the oracle keeps both and lets them cancel.

Caveat that must travel with this: the oracle's own `m_trial_balance` is empty, so the
comparison is `DeriveTrialBalance` vs the oracle's **query**, never vs an oracle-written
trial-balance row. The GRADING run must not treat the four-row query transcription as
oracle output.

## Oracle-state change caused by this capture

Tables to which this capture added rows, tenant `gerege`:

| table | delta | identity |
| --- | --- | --- |
| `acc_gl_journal_entry` | **+4** (110 → 114) | ids 141,142 (txn `a2b795dca42b`); 143,144 (txn `a2b7964aa51b`) |
| `job_run_history` | **+1** | id 10045, `job_id` 30, `version` 6, `failed`, `application` |
| `batch_job_instance` | **+1** | 10046 `UPDATE_TRIAL_BALANCE_DETAILS` |
| `batch_job_execution` | **+1** | 10046, `FAILED`, create 2026-09-11 02:31:02.922751 |
| `batch_job_execution_context` | **+1** | 10046 (short_context length 54) |
| `batch_job_execution_params` | **+1** | 10046, `run.id = 6` |
| `batch_step_execution` | **+1** | 10073 `UPDATE_TRIAL_BALANCE_DETAILS`, `FAILED` |
| `batch_step_execution_context` | **+1** | for step 10073 |
| `m_trial_balance` | **+0** | still 0 rows — the point of step 5 |

Evidence: `step06-reason/batch-rows-10046.txt`, `step04-job30/job-run-history-count.txt`,
`step05-trial-balance/je-count-maxid.txt`. (The `batch_*` totals also grow from a
background `SEND_ASYNCHRONOUS_EVENTS` job that runs each minute; the deltas above are the
specific ids belonging to this capture's job 30 execution.)

## File manifest (sha256)

All files under this directory except `OWNER.md` and `SHA256SUMS` (which cannot contain
their own hashes). `SHA256SUMS` repeats this list and additionally carries `OWNER.md`'s
hash; verify with `shasum -a 256 -c SHA256SUMS` (run from this directory, expecting the
`./` prefixes below).

```
581f79b41453220ff3f7eb23d6c318b5cf20595a320ba998cc64072a1bab80db  ./WHY-EMPTY.md
343d4bc5c0e278a632812e0c896a0313a695c67a79cd9f0796f2718d374c4362  ./bin/rest.sh
e14b037afabb88269b00e9c4aff5d92839ee31c42ddbed976c5ecdfa7ca5d658  ./bin/step00-baseline.sh
30d53bbb873c72c6ca123b12d57b6258149cb75bd93a06f020e831adf607dbcc  ./bin/step00b-controls.sh
379c59ca99fc122294c076cf3d74b5520be6e3216171180c4d3e6bd9c24ea194  ./bin/step01-post.sh
1283506da79380edc301aaa42e77e7a1633030b7ef990cd82c04872989124194  ./bin/step02-reverse.sh
d2ce04d589bf92becdaa9c94a837cd726ead7c4df92a3d79ba739aa42a42ce47  ./bin/step03-readback.sh
8e6a86942080d19fc286c04df256ecf779c27967a085063dbe8d8479c2556c3a  ./bin/step04-execute-job30.sh
60f26c613b0f3c91cbf6d160fb8c8e2780254e8b0c3339502ca254653c2a22a2  ./bin/step05-read-mtb.sh
7413f5deb9c2fdab83ad4850f5c8b9ae26d4ce82728cf4c8239d659a5e37555d  ./bin/step06-record-reason.sh
299217fd4460d2ecf580c30fd78e675029c71644083036d1b3e33c580be50efc  ./evidence/default-tenant-job30-failure-2026-09-08.txt
223ba84bca2de5cf7f51a4a673ca779d7ef363ff8f6f25ac1a358573871c8cfd  ./evidence/job30-run-log-extract.txt
2d94b37ac720cebb3e8cd2a94b88be7e83343f54f7c31edf2c7ce39807d9a93b  ./raw/00-businessdate-sql.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-businessdate-sql.txt.err
daa87d970de7b1ba05831632dd0ae95b03d35803663f018e60d89bead29178ff  ./raw/00-businessdate.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./raw/00-businessdate.json.status
adf0aa1adf28d1733d2a9f25622b023d9450b89e3bef130b3f9aec62368e3fec  ./raw/00-control-sql-vs-rest.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-control-sql-vs-rest.txt.err
0ec317cf350018f3580ef8ebef4f3bb6f5da882d7ad734d536fd53577e9fb9c4  ./raw/00-gl-accounts-all.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-gl-accounts-all.txt.err
0ec317cf350018f3580ef8ebef4f3bb6f5da882d7ad734d536fd53577e9fb9c4  ./raw/00-gl-manual-accounts.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-gl-manual-accounts.txt.err
4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945  ./raw/00-glclosures.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./raw/00-glclosures.json.status
02e468a2f196525d008ba900215663cb5ba9801ac12326e77c7dae6a15034cd3  ./raw/00-je-count-maxid.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-je-count-maxid.txt.err
dec85d957b9be7cfaf88d451cdd9cf9915ab46bb704d99e980d9a6dbfd341340  ./raw/00-je-created-by-entry-date.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-je-created-by-entry-date.txt.err
20e4f0bec7f24eb902bd3e9ce0597aaaac5ed822e25b7c7188335da6970f6e3d  ./raw/00-je-created-on-utc-nullcount.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-je-created-on-utc-nullcount.txt.err
892339cc685ff954bb6f31fd3e473bb3f985ed34192fea372c2ebae531e16d39  ./raw/00-je-created-on-utc-range.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-je-created-on-utc-range.txt.err
e3c30ccffd473672dab85c88bb437e093b8b29abe5d040c94022773f49ad1cb2  ./raw/00-je-distinct-entry-dates.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-je-distinct-entry-dates.txt.err
b299e95c81d7dc48992c1532dd79d16c53f6c6208a6a431d0c6dc1730fd0079d  ./raw/00-je-entry-date-range.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-je-entry-date-range.txt.err
1668db724a0db054dbe69f215cfd79dc12b0a952fb7465bde851a87a51bf46f1  ./raw/00-je-reversed-counts.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-je-reversed-counts.txt.err
c4534e8b5e76e3ba2627fedfb54b532f6dac04cae1130163b1eb285f3a800ee6  ./raw/00-je-transaction-date-column.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-je-transaction-date-column.txt.err
10dc1bc627a356a91e9e5a53cd3af39ea6ce8a5cd5a65b124fb2c3448c938500  ./raw/00-job30-runhistory.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./raw/00-job30-runhistory.json.status
9377be95efcba073494f6a804258e977a655231d7ecfb47c2eeef7036c6b1fbe  ./raw/00-job30.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./raw/00-job30.json.status
80e39032c91fe3c9de51868ecc214130cb6e6a6d5cb28144cbac738868e09542  ./raw/00-journalentries-rest.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./raw/00-journalentries-rest.json.status
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-mtb-all.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-mtb-all.txt.err
e1a9ee0641d9c854def665b08d73c710b541383036d10c9b051a431a3ac922f2  ./raw/00-mtb-columns.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-mtb-columns.txt.err
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  ./raw/00-mtb-count.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-mtb-count.txt.err
01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b  ./raw/00-mtb-max-created-date.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./raw/00-mtb-max-created-date.txt.err
14a7a9f79ca3f56ba9bc8e0e08b7149339ed7d26993c61090b1f81750e93f3a8  ./raw/00-mtb-schema.txt
dea7c4a853ebd4beba814ccb64f0825ce46d7c2ac8d1ac0c1082baf4caf2781b  ./req/01-post-manual-entry.json
143bb0cd9f15d1ff533b15bcf326c5af6f6c652b6d5b45f362f6daef964f0b9e  ./req/02-reverse.json
fd786f00a7d6728ad11a2ee2a1ff0ca49507edf2a75826cb29f72c133d60be26  ./step01-post/control-count-maxid.txt
98bc0c34dc391ffdb134cdd17395e7eaf50821a913745c87f96d5bc1a3850cd0  ./step01-post/meta.txt
a12f7b58e6eaffb324f19819d947d667525281e4886111ce1dce8dfbf74700f9  ./step01-post/readback-rest.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./step01-post/readback-rest.json.status
541fc1137e52f72ada7c7bba38b67a1737bf7ac15e2d0393e9a6fd8896eeefae  ./step01-post/readback-sql.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./step01-post/readback-sql.txt.err
dea7c4a853ebd4beba814ccb64f0825ce46d7c2ac8d1ac0c1082baf4caf2781b  ./step01-post/request.json
799cc1af05f60b74bb193f3d6b7d1e9d8853f9e98cb428d615c2ef76ad2fc6a6  ./step01-post/response.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./step01-post/response.json.status
143bb0cd9f15d1ff533b15bcf326c5af6f6c652b6d5b45f362f6daef964f0b9e  ./step02-reverse/request.json
8fb60f59bef6a2c89a3bca1487375d089a24090892ac84ec3c6d32330c809b17  ./step02-reverse/response.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./step02-reverse/response.json.status
2e7789b5b80938d3b6e2fdfe96c21db89eb47ba076544343fc5add1e2978ecbd  ./step03-readback/meta.txt
851518c3206ea1cca2b02837f8caa7587be8a6e7df1dc431f3864bac64eb5013  ./step03-readback/rest-orig.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./step03-readback/rest-orig.json.status
90676dadf2485027e6c88f752f92611cff85ba9beb1ca06232938fcd20821b46  ./step03-readback/rest-rev.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./step03-readback/rest-rev.json.status
a508e0792f7c287c9f3394dc75381ab50b61cd7f891d7159320a66704369c586  ./step03-readback/sql-control-count-maxid.txt
e0c9bfc8bf34465d126e214a1126977c8dacd6c09838880c166d2b51246e0d14  ./step03-readback/sql-rows.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./step03-readback/sql-rows.txt.err
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ./step04-job30/execute-response.txt
c17edaae86e4016a583e098582f6dbf3eccade8ef83747df9ba617ded9d31309  ./step04-job30/execute-response.txt.status
1b18326c62b5be448b5cc197469999022c645b8736d599ef589303ce89a7beb4  ./step04-job30/job-run-history-count.txt
c6f5960f1b7a0e6773a3250c3d652e02f2e167d677740f1f71536011b72ae808  ./step04-job30/job30-runhistory-sql.txt
d7509dbceb1247702eb63b147d09dd9b0e4cca72111799e4f906640657ef1b75  ./step04-job30/runhistory-after.json
10dc1bc627a356a91e9e5a53cd3af39ea6ce8a5cd5a65b124fb2c3448c938500  ./step04-job30/runhistory-before.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./step04-job30/runhistory-before.json.status
d7509dbceb1247702eb63b147d09dd9b0e4cca72111799e4f906640657ef1b75  ./step04-job30/runhistory-poll-1.json
27badc983df1780b60c2b3fa9d3a19a00e46aac798451f0febdca52920faaddf  ./step04-job30/runhistory-poll-1.json.status
3a5563ad5feb41694d48e0a518c57aa3851151fcaa3960ac44adb527ee4bdc5e  ./step05-trial-balance/equiv-query-2026-06-15.txt
a508e0792f7c287c9f3394dc75381ab50b61cd7f891d7159320a66704369c586  ./step05-trial-balance/je-count-maxid.txt
4831db41189927cad1bf8a4475e7b4ad2ba35104ce9186b5f10ec23cad29f5bb  ./step05-trial-balance/mtb-all-rows.txt
476644ee500dc3208ea4e262ba245efd2eeb5187e1377e19da97fa26bea70934  ./step05-trial-balance/mtb-columns.txt
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  ./step05-trial-balance/mtb-count.txt
c95534cdac39ee91e1afe0d906cc27dd44ec5dd54e927322e59152c14dc393dd  ./step06-reason/REASON.md
093f5a9dca05d7e59ef75f9ac912e1e07d7f16c915d49dcc3adf0fccd581d50b  ./step06-reason/batch-rows-10046.txt
4ed8f00fad77aef0dbb839ca1cf57cddf826de840ec8fd2c1007b4c5f16b0a18  ./step06-reason/row4-type.txt
```

## Non-negotiables, checked

* Integer minor units everywhere in this map; wire decimals transcribed as strings in the
  raw JSON. No sub-minor value written.
* SQL read-only; **every** write via REST (`/journalentries`, `/journalentries/{id}?command=reverse`,
  `/jobs/30?command=executeJob`). Tenant `gerege` only; `default` never contacted.
* `fineract-db-1` never queried; every SQL read went through `gerege-oracle-db` and was
  controlled against REST.
* No value synthesised. The only derived table (query-equivalent rows) is a read-only SQL
  transcription of the pinned repository query and is labelled as such.
* `nexus/`, `.softhouse/guards/`, `.softhouse/conformance.sh` untouched.
* Exactly one manual entry and one reversal posted. No second pair — the step-6 reason is
  a deterministic cast failure independent of the entry, so a retry was not justified.
