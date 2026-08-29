# T438 — INDEPENDENT review of T417 (G-22, the scheduler pin)

Reviewer T438, fire `20260829-080002`, branch `softhouse/T438-review-t417`.
I did not plan T417's work. **Every figure below I re-derived myself.** Nothing is transcribed
from T417's handoff except where I quote it in order to contradict it.

**Reference oracle:** REACHABLE throughout. PostgreSQL 18.3, container `fineract-db-1`,
database `fineract_gerege`.
**Pinned Fineract:** `git -C /Users/buv/fineract rev-parse HEAD` =
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, working tree clean — verified **before** a single
line number was read out of it.
**Every statement this review issued against the oracle is a SELECT.** All five of my red arms
were manufactured from doctored **copies** of witness files under `/tmp`. The shared instance
was not written to, at any point, by any arm.
**No money value was computed, rounded, compared or stored by this review. No floating point.**

---

# VERDICT: **APPROVED WITH CONDITIONS**

T417's central design judgement is **right, and I tried to break it and could not**: measuring
*movement* rather than *permission* is the correct answer to G-22, the user-2 trap is real and
T417 did not fall into it, and the coverage claim that makes the whole thing worth having —
273 of 281 base tables — is **true, and the 8 excluded tables carry no money and no ledger
state**. Both bars are EXIT 0 and the merge result shows **16**.

Two MAJOR conditions. One is a wrong number published as measured against a predecessor that
was right. The other is that the pin is wired to nothing, and T417's argument for that — which
is correct as far as it goes — does not reach the wiring that actually exists.

| # | severity | finding |
|---|---|---|
| **F-T438-1** | **MAJOR** | `min_entry_date` **2026-01-15 is wrong**; T409's **2026-05-15** is right. An unfiltered `min()` under a filtered column alias, and a false reason given for not chasing the discrepancy. |
| **F-T438-2** | **MAJOR** | **P-45.** The pin is wired to nothing. A wiring that is red only when a capture lands — not nightly — demonstrably exists in this bar already. |
| **F-T438-3** | MINOR | The provenance block's `witness_verdict` reads **`CAPTURE`** for a contaminated window. Present in T417's own committed red-arm transcript, unasserted. |
| **F-T438-4** | MINOR | The reported window is ~0.5–0.8 s narrower at the close end than the interval the digest brackets. Produces a **phantom-writer false alarm**. Measured. |
| **F-T438-5** | MINOR | Table exclusion is an exact list; **sequence exclusion is a prefix match**, and `--self-test` checks only the table side. Zero over-reach today, no guard against tomorrow's. |
| **F-T438-6** | MINOR | The `MOVED` printer **garbles SEQUENCE rows**. Detection is correct; the report a human reads is not. Survived because the 13-arm drive has no sequence-only red arm. |
| **F-T438-7** | LOW | Three line-number citations off by 1–3. Files and symbols correct. |
| **F-T438-8** | LOW | The second raw `UPDATE` at `:211` is on the **command-handler** path, not the scheduler's. Existence claim right; framing overstates. |
| **F-T438-9** | LOW | "34/41/43 are `is_active = f`" implies 32/33 are active. **All five never-run jobs are inactive.** |
| **F-T438-10** | MINOR | Two residual classes are missing from a residual list that is otherwise unusually honest: within-window revert, and the **effective tenant rounding mode living in a JVM cache**. |
| **F-T438-11** | MINOR | `capsql.sh`'s "READ-ONLY by construction" write-verb refusal is line-based and **lets `DELETE`/`FROM` split over two lines through**. Driven. |

Nothing I found is a money-math defect, and nothing I found makes the instrument unsafe to
land. F-T438-1 must be fixed at the site because a later reader is explicitly instructed to
trust the wrong value.

---

# 1. The pin is wired to nothing — adjudicated

**T417's argument, quoted:** a state digest pinned in `conformance.sh` "would go red daily for
reasons no diff caused — P-45 wearing the opposite hat." `.softhouse/conformance.sh` is
**unchanged by this task**, which I confirmed: `git diff main -- .softhouse/conformance.sh` is
empty on both my tree and the merge result, and the merge produced **no conflict** in that file
`[VERIFIED]`.

**The argument is correct about the digest, and it is answering a question nobody asked.**
Nobody needs the *digest* in the bar. What is missing is the *obligation* — a static,
repo-content-only check that a capture promoted to a vector carries the witness it was taken
under. That check never contacts the database, so it cannot go red for reasons no diff caused.
It goes red exactly when someone lands a capture without a witness, which is the event the pin
exists to police.

**And the template for it is already in this bar.** `guard_no_float_in_capture_requests`
[`.softhouse/conformance.sh:1214`] derives its floor from

```
git grep -h -E '"capture_ref"[[:space:]]*:' -- .softhouse/vectors
```

[`:1254`] and opens every capture record a stored vector names. **A guard shaped identically —
"every parity vector carrying `provenance.capture_ref` must also carry `provenance.witness_ref`,
naming a TRACKED witness file whose `meta<TAB>label` row matches" — is pure repo content, zero
oracle contact, and red only on a diff.** That is the wiring T417 says does not exist.

So the answer to the record's question is **yes, there is a wiring reached only when a capture
runs.** T417 conflated "wire the digest into the bar" (correctly rejected) with "wire anything
into the bar" (not examined). What it left instead is FU-T417-1, which asks the *next capture
task* to voluntarily adopt a wrapper — the exact shape recorded in `patterns.md:1503` and, per
the record, five times since.

I also confirm **FU-T417-6** independently: `guard_guards_dir_registration`'s population is

```
git ls-files -- ':(glob).softhouse/guards/**/*.sh' ':(glob)…**/*.py' ':(glob)…**/*.go'
```

[`.softhouse/conformance.sh:3266-3269`, VERIFIED]. Both new instruments live under
`.softhouse/capture/t417-scheduler-attribution/instruments/` and are therefore **structurally
invisible to the one guard whose entire job is finding unwired checkers.** Two more residents
of that blind spot.

**CONDITION C-T438-1 (MAJOR).** Land the static wiring described above, or — if the vector
schema change must wait for an uncontended wave, which is a real constraint T417 names honestly
— land the *cheaper half now*: widen `guard_guards_dir_registration`'s population to
`.softhouse/**/instruments/*.{sh,py,go}` so both instruments become visible to it, and take the
`REACHED-BY` SUBJECT row as the declaration. That is one selector and it converts "nobody runs
it" from invisible to declared. **Drive:** a red arm that adds an instrument with no REACHED-BY
row and shows the bar goes red.

---

# 2. The coverage claim — **TRUE, and the hole is inert**

Derived by me from the live database, not read from T417's `COVERAGE.txt`
[`sql/r1-coverage.sql` → `out/r1-coverage-derived.txt`]:

| | T417 claimed | I measured | |
|---|---|---|---|
| base tables (`public`, `BASE TABLE`) | 281 | **281** | ok |
| graded by the content digest | 273 | **273** | ok |
| excluded | 8 | **8**, and all 8 names exist as base tables | ok |
| sequences (`pg_sequences`, `public`) | 254 | **254** | ok |
| graded by `last_value` | 249 | **249** | ok |
| excluded sequences | 5, named | **exactly those 5** | ok |

**The 8, by name:** `batch_job_execution`, `batch_job_execution_context`,
`batch_job_execution_params`, `batch_job_instance`, `batch_step_execution`,
`batch_step_execution_context`, `job_run_history`, `job`.
**The 5:** `batch_job_execution_seq`, `batch_job_seq`, `batch_step_execution_seq`,
`job_id_seq`, `job_run_history_id_seq`.

**Can any of them carry money or ledger state? No.** I checked the schema and the contents,
not the names `[VERIFIED: sql/r2-excluded.sql, sql/r8-excluded-contents.sql]`:

- **Zero** columns of type `numeric`, `decimal`, `double precision`, `real` or `money` across
  all eight. Every column is `bigint`, `varchar`, `text`, `timestamp`, `boolean`, `smallint`,
  `integer` or `character`.
- The only free-text columns that could smuggle something are
  `batch_job_execution_params.parameter_value` and the two `serialized_context` /
  `short_context` columns. Their entire content, over 13k+ rows: parameter names are
  **`run.id` (13377), `batch-size` (17), `thread-pool-size` (17), `officeId` (9)** and nothing
  else; contexts hold `{"batch.version":"5.2.6"}` and a `batch.taskletType` class name.
- `job` and `job_run_history` are the scheduler's schedule and its run log.

**The near-miss check, which is the one that matters and which T417 did not state:** two base
tables *look* like they should have been swept in and were not — **`batch_custom_job_parameters`
and `job_parameters` are GRADED**, correctly `[VERIFIED]`. The table exclusion is an exact
`NOT IN` list, so no prefix hazard exists on the table side.

I also confirm the tables that would matter are all inside the digest, by reading them out of
my own witness file: `acc_gl_journal_entry` (109 rows, digest `77a7b645…`), `acc_gl_account`,
`acc_gl_closure`, `m_loan_transaction`, `m_savings_account_transaction`, `m_currency`, and
**`c_configuration`** — which is where `rounding-mode = 4` lives (see F-T438-10).

**This is not job 11's shape made smaller.** Job 11 escaped because the watched surface was two
tables and the argument for the other 279 ran through the command bus, which the scheduler does
not use. Here the surface is everything except the batch runner's ledger of itself, and I
verified the exclusion is inert with respect to money rather than accepting that it is.

**F-T438-5 (MINOR).** The *sequence* exclusion is not an exact list — it is
`sequencename NOT LIKE 'batch_job%' AND … 'batch_step%' AND … 'job_run_history%' AND …
'job_id%'` [`oracle-window-witness.sh:161,186-190`]. And `--self-test` [`:553-565`] checks
**only** that `base_tables - graded == 8` named tables; **it makes no equivalent assertion about
sequences.** Today the prefixes over-reach by zero — I checked every sequence starting `job` or
`batch`: `batch_custom_job_parameters_id_seq` and `job_parameters_id_seq` are both correctly
graded `[VERIFIED: out/r1-coverage-derived.txt c8]`. But a future `batch_job_*` or `job_id*`
sequence on a business table would be silently dropped from the graded surface and the
self-test would not notice — which is precisely the "ungraded region nobody has declared
ungraded" the instrument's own comment at `:143-145` warns about.
**Drive:** add the sequence arm to `--self-test` (`seq_total - seq_graded == 5`, each named);
plant a fake `job_idX_seq` in a scratch copy and show the self-test refuses.

---

# 3. The trap — **T417's claim verified by reading the instrument, and the measurement re-taken**

**Claim: the instrument never reads `created_by` or `last_modified_by`.**
`grep -rn "created_by\|last_modified_by" instruments/ drive/` returns **three hits, all of them
comment lines** — `oracle-window-witness.sh:25`, `:34`, `:41` — and **zero** in any SQL string,
any `q()` call, or any awk selector `[VERIFIED]`. Every SELECT the instrument issues is in
`read_tables`, `read_sequences`, `read_scheduler`, `read_job_table`, `runs_overlapping` and
`cmd_coverage`, and I read all six. **The claim is true.** It measures movement.

**Claim: `last_modified_by = 2` on all 109 ledger rows.** Re-measured
`[VERIFIED: sql/r3-core.sql → out/r3-jobs-ledger-entrydate.txt]`:

```
acc_gl_journal_entry:  109 rows / max id 113 / 38 distinct transaction_id
last_modified_by = 2 : 109 rows   (one value, no others)
created_by      = 1 : 91 rows,  = 2 : 18 rows
max(created_on_utc) = max(last_modified_on_utc) = 2026-08-28 16:01:00.117772+00
m_appuser: 1 mifos, 2 system, 3 interopUser
```

**Confirmed, exactly.** A user-2 exemption would indeed retroactively excuse **every row of the
ledger**, and T417's reasoning about why that is the worst possible simplification is sound. The
source half is also right: both raw UPDATEs bind `last_modified_by` from
`platformSecurityContext.authenticatedUser().getId()` — `:178` and `:214`, both VERIFIED at the
pin — so it is a runtime identity and not a constant.

**This is the strongest part of T417's work and I could not dent it.**

---

# 4. The cardinal, the contradiction and the second `UPDATE`

### 4a. The cardinal — **T417 is right, "nineteen" is wrong**

`[VERIFIED: out/r3-jobs-ledger-entrydate.txt j1/j2, out/r1-coverage-derived.txt]`

```
job rows 41   is_active = t : 31   inactive : 10
distinct job_id in job_run_history, last 24h : 31
distinct job_id in job_run_history, all time : 36
```

**41 / 31 / 10, and 31 distinct jobs ran in 24 h. Confirmed independently.** (Job ids run 2–43
with gaps, so "41" is a row count and not a maximum id.) The correction stands and the blind
spot really was 63 % larger than "nineteen".

**F-T438-9 (LOW).** T417 writes: *"Jobs 32, 33, 34, 41, 43 have never run … and 34/41/43 are
`is_active = f`."* The five never-run jobs are exactly those five `[VERIFIED]` — but **all five
are `is_active = f`**, including 32 and 33. Singling out three of five implies the other two
are active. T417's own `COVERAGE.txt` line "ACTIVE jobs with NO run history: (none)" contradicts
it in the same task. **Drive:** delete the parenthetical or make it "all five are inactive."

### 4b. The contradiction — **settled: T409 was right, T417 is wrong** → **F-T438-1 (MAJOR)**

T417's handoff:

> `min(entry_date) WHERE NOT is_running_balance_calculated` = **2026-01-15** … Note T409 wrote
> the minimum as `2026-05-15`; I read **2026-01-15**. The count is 55 either way, so I did not
> chase the discrepancy — but **a later reader should not take `2026-05-15` from T409 without
> re-deriving it.**

Re-derived from the live database `[VERIFIED: sql/r3-core.sql L4]`:

```
SELECT min(entry_date), count(*) FROM acc_gl_journal_entry WHERE NOT is_running_balance_calculated;
  min_entry_date = 2026-05-15     not_calculated = 18
  count(*) WHERE entry_date >= that minimum = 55
```

**The value is `2026-05-15`.** T409 was right.

**Root cause, in T417's own committed SQL** — `sql/s3-ledger-now.sql`, block `s3c`:

```sql
SELECT min(entry_date)                AS min_uncalculated_entry_date,
       count(*) FILTER (WHERE NOT is_running_balance_calculated) AS uncalculated_rows
FROM acc_gl_journal_entry;
```

**The `count(*)` carries a `FILTER`. The `min(entry_date)` does not.** It is the *global*
minimum over all 109 rows, wearing an alias — `min_uncalculated_entry_date` — that asserts a
predicate the aggregate never applied. `2026-01-15` is indeed the global `min(entry_date)`; two
rows carry it `[VERIFIED: entry_date distribution, L5]`.

**The reason given for not chasing it is also false.** "The count is 55 either way" cannot hold:
`count(*) WHERE entry_date >= '2026-01-15'` is **109**, the whole table. The 55 in T417's own
transcript comes from the *second* statement of `s3c`, whose correlated subquery **does** carry
the filter — so the 55 was derived from `2026-05-15` while the prose beside it asserted
`2026-01-15`. The two printed figures are mutually inconsistent and were reconciled with a
claim that does not survive one query.

**Fineract's source agrees with T409 — and T417 quotes the line itself.**
`JournalEntryRunningBalanceUpdateServiceImpl.java:72-73` `[VERIFIED @ 426a23544]`:

```java
String dateFinder = "select MIN(je.entry_date) as entityDate from acc_gl_journal_entry  je "
        + "where je.is_running_balance_calculated=false ";
```

Job 9's restart point **is** the filtered minimum. The 18 uncalculated rows are entry_dates
2026-05-15 (L32, ×6), 2026-06-15 (L33, ×6) and 2026-07-15 (L34, ×6) `[VERIFIED: L4b]`.

**Not drift.** `max(last_modified_on_utc)` is still `2026-08-28 16:01:00.117772+00` and
`uncalculated_rows` is still 18 — the identical state T417 measured. This is a measurement
defect, not a moved oracle.

**Why MAJOR.** The figure is the pre-state of T409's falsifiable prediction, and **FU-T417-2
instructs the next reader to re-run `s3c` and compare**. That reader inherits a query whose
column name lies, a wrong figure in prose, and an explicit instruction to distrust the value
that is actually correct. The program's honesty rule exists for exactly this.

**CONDITION C-T438-2 (MAJOR).** (a) Fix `s3c` to
`min(entry_date) FILTER (WHERE NOT is_running_balance_calculated)`; (b) correct the figure at
the site and **withdraw the instruction to distrust T409's `2026-05-15`**; (c) re-run and record
`2026-05-15 / 18 / 55`. **Drive:** the corrected statement must return 2026-05-15 on this
oracle, and the second statement's 55 must be unchanged.

### 4c. The second raw `UPDATE` at `:211` — **it exists, verbatim**

`JournalEntryRunningBalanceUpdateServiceImpl.java:211` `[VERIFIED @ 426a23544]`:

```java
String sql = "UPDATE acc_gl_journal_entry SET office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?";
```

Executed via `jdbcTemplate.batchUpdate(sql, params)` at `:217`, params bound at `:214-215`. It
writes `office_running_balance` **only** — it does not set `is_running_balance_calculated`, so
it never advances the restart floor. T409 did not name it; T417 did; **it is real.**

**F-T438-8 (LOW).** T417 files it under *"The mutation, re-derived (T409's F-T409-1)"* as
"Same class, same file, also `batchUpdate`" — i.e. as further evidence about the scheduler. It
is not on the scheduler's path. It sits in `updateRunningBalance(Long officeId, LocalDate)`
[`:191`], reached only from `updateOfficeRunningBalance(JsonCommand command)` [`:83`, `:97`] —
**a command handler**, so unlike the nightly sweep it *does* leave an
`m_portfolio_command_source` row. The scheduler's own path is `updateRunningBalance()` [`:71`] →
`updateOrganizationRunningBalance` → the `:163-164` statement. The existence claim is correct;
the placement invites a reader to attribute an API-driven mutation to the scheduler.
**Drive:** one clause naming the path. (Incidentally, `:217` calls `batchUpdate`
unconditionally even when `params` is empty, unlike the `:163` path guarded at `:158` — a
Fineract quirk, not a T417 defect, recorded so nobody re-finds it.)

---

# 5. The minute boundary, and the refusal that was kept

### 5a. Job 36 — **re-measured, T417's number is right**

`[VERIFIED: out/r3-jobs-ledger-entrydate.txt j3/j3b]`

```
job 36  Send Asynchronous Events  is_active = t  cron '0 0/1 * * *  ?'
runs all-time                    10655   (T417 read 10623 ~33 min earlier — consistent)
runs in the last 24 h             1440   (= 60 × 24, exactly)
runs in the last 60 min             60   min 23:42:00.005  max 00:41:00.009 — no gap
```

**Every minute, without a gap.** A blanket "refuse if a job ran in the window" would refuse
every capture longer than 60 seconds. **T417's rejection of that form is measured, not argued,
and I reproduce the measurement.**

I also reproduced the empirical half. My own witness `open`/`close`, then `verify` against
**T417's committed `LIVE-MINUTE-BOUNDARY` witness** — taken 27 minutes earlier — returns
`UNMOVED`, rollup `4c0adcae1804d88464265fc0f7661891` **byte-identical**
`[VERIFIED: out/r4-witness-suite-rerun.txt]`. Across ~27 job-36 runs the graded surface did not
move by one byte. `QUIESCENT-WITH-RUNS` is a real category, not a rationalisation.

### 5b. The refusal that was kept — **checked against source, and it is stronger than T417 argued**

`[all VERIFIED @ 426a23544]`

- `SchedulerJobListener.java:58` `jobWasExecuted`; `:52` `jobToBeExecuted` and `:55`
  `jobExecutionVetoed` are **empty bodies**. So no row exists until a job finishes.
- `:79-80` `jobException != null` only sets `status = FAILED`; the history is still saved.
  Confirmed live: job 30 failed with a `ClassCastException` and **still has jrh 12718**
  (from my own `attribute` run, `out/r4-witness-suite-rerun.txt`).
- `:105-107` builds `ScheduledJobRunHistory` with `.setEndTime(new Date())`, saved at `:109`.
- `JobRegisterServiceImpl.java:319,322` `setGlobalJobListeners(jobListeners)`, for the cron
  scheduler `:293` **and** the temporary scheduler a manual trigger uses `:116`. *Global*
  really does mean every job on that scheduler.

**And one thing T417 did not check, which makes its own case better.**
`SchedularWritePlatformServiceJpaRepositoryImpl.processJobDetailForExecution` is annotated
`@Transactional(propagation = Propagation.REQUIRES_NEW)` [`:144`, with `@Retry` at `:143` and
the comment at `:142` recording that its caller `SchedulerVetoer#veto` must stay
non-transactional]. It sets `currently_running = true` at `:158` and saves at `:161`, so the
in-flight flag is **committed in its own transaction before the job body runs** and is
externally visible for the whole run `[VERIFIED]`. The refusal T417 kept rests on a signal that
is genuinely observable — it did not have to take that on faith, and neither do I.
`currently_running` is cleared at `SchedulerJobListener:103` in the **same** `saveOrUpdate`
[`:109`] that writes the history row, so the flag and the run list can never disagree at a
commit boundary.

**I drove the refusal red myself** (doctoring `jobs<TAB>currently_running` in a `/tmp` copy —
the field prefix is `jobs`, not `meta`, which is the failure T417 kept as
`DRIVE-WITNESS-FIRST-ATTEMPT-red4b-failed.txt`): it refuses, exit 1
`[VERIFIED: out/r5-my-own-red-arms.txt RED-B]`.

---

# 6. What the witness misses by one

I re-asked all three of the record's questions rather than reading T417's residual list back.

### 6a. What moves and moves back inside the window?

**Partly covered, and T417 does not claim the credit or name the gap.** The digest compares two
instants, so a transient is invisible to it — **but the sequence reading is a ratchet.** An
`INSERT` + `DELETE` inside the window consumes a `nextval` and `pg_sequences.last_value` does
not go back, so the round trip is caught. I proved the sequence arm actually discriminates by
driving it red on `acc_gl_journal_entry_id_seq`: exit 1, MOVED
`[VERIFIED: out/r5-my-own-red-arms.txt RED-C]`.

**What is genuinely invisible:** an `UPDATE` reverted within the window, or an `UPDATE` that
rewrites identical bytes. Practical exposure is low — every Fineract mutation path I read sets
`last_modified_on_utc` from `DateUtils.getAuditOffsetDateTime()` [`:178`, `:215`], so a real
revert would leave a different timestamp and the digest would see it. **But it is not in the
declared residual, and residual item 3 covers movement *between* windows, not *within* one.**

### 6b. What lives outside PostgreSQL?

T417 declares the class (residual 5: app-container files, in-memory caches,
`fineract_default` / `fineract_tenants`) but names no member, which makes it unactionable. **The
member that matters to a money program:**

**The effective tenant rounding mode is a static JVM cache, not a database value.**
`MoneyHelper.roundingModeCache` is a `private static final ConcurrentHashMap`
[`MoneyHelper.java:37`], populated by `initializeTenantRoundingMode` [`:54`] at startup
[`MoneyHelperStartupInitializationService.java:68`] **and re-populatable at runtime through
`InternalConfigurationsApiResource.java:90` — an HTTP endpoint** `[all VERIFIED @ 426a23544]`.
The database value it is seeded from is `GlobalConfigurationConstants.ROUNDING_MODE`
[`MoneyHelperInitializationService.java:102-106`], i.e. `c_configuration` row 23,
`rounding-mode`, **enabled, value 4** = `HALF_UP` `[VERIFIED live]` — and the good news is that
**`c_configuration` IS in the graded digest** (74 rows, digest `2351a2be…`) `[VERIFIED: my
witness TSV]`. The bad news is that the digest grades the *seed*, not the *effective* value: the
cache can be re-initialised with the database untouched, and every subsequent capture's
arithmetic changes with the graded surface byte-identical. Given CLAUDE.md pins the production
`MathContext` at `(19, HALF_UP)` and calls it non-re-decidable, this is the single most
consequential piece of un-witnessed state in the program.

Also outside: `fineract_tenants.tenants` carries `timezone_id` — `Asia/Ulaanbaatar` for tenant
`gerege` `[VERIFIED live]` — another CLAUDE.md non-negotiable living where the witness does not
look. And Fineract here runs Quartz on **RAMJobStore**: there are **no `qrtz_*` tables** in the
schema `[VERIFIED: out/r1-coverage-derived.txt c7]`, so all trigger state is in-process.

**F-T438-10 (MINOR), CONDITION C-T438-3.** Add both to the declared residual by name. The
rounding mode is worth more than a mention: `read_scheduler` could emit one extra row —
`SELECT value FROM c_configuration WHERE name='rounding-mode'` — so the seed is at least
*visible* in every witness rather than merely inside a 273-line digest. **Drive:** doctor the
value in a `/tmp` witness copy and show `close` reports it MOVED.

### 6c. A job that starts inside the window and finishes after `close`?

**Handled — and I verified it end to end**, both from source (5b above: `currently_running` is
committed before the body, cleared with the history row) and by driving RED-B. T417's claim
"REFUSED, not missed" is correct.

**But there is a one-instant gap in it, and it is measurable → F-T438-4 (MINOR).**
`emit_witness` [`:245-258`] calls `read_scheduler` **first** and `read_tables` **last**, and
`cmd_close` [`:346-347`] takes the window endpoints from `db_now_utc`, which `read_scheduler`
emits. So the run list is computed over `[T_open_first, T_close_first]` while the digest
brackets `[T_open_last, T_close_last]`. **Measured on this host:**

```
db_now_utc recorded in the witness   2026-08-29 00:43:00.157944
database clock when open() returned  2026-08-29 00:43:00.677086
                                     -> skew ~= 0.52 s   [VERIFIED: out/r7-witness-open-timing.txt]
```

`close` runs 0.6–0.8 s in my transcripts. **A job that fires in that trailing ~0.6 s has its
writes inside the close digest and its run outside the reported window.** With job 36 firing
once per minute that is roughly a 1-in-100 chance per close — and the resulting output is not a
harmless mislabel, it is:

> `ATTRIBUTION: NO job run overlaps this window. The scheduler did not do this. Something else
> wrote to the SHARED reference oracle -- find it, and register it.`

**A false alarm that dispatches a human to hunt a writer that does not exist**, on an
instrument whose whole value is that its red means something. The same window covers the
`currently_running` read: a job can claim itself after `read_scheduler` and write before
`read_tables`, reading 0 in flight and 0 runs.
**Drive / fix:** emit a second `db_now_utc` **after** `read_tables` and use
`[open.first, close.last]` for `runs_overlapping`. Cheap, and it converts the phantom into a
correctly-attributed overlap. **Red arm:** call `attribute` with a window shifted by 0.6 s
across a job-36 fire and show the run appears.

---

# 7. Defects in the artefacts themselves

### F-T438-3 (MINOR) — the provenance block records the wrong verdict for the one case that matters

`capture-under-witness.sh:101`:

```bash
printf 'witness_verdict\t%s\n' "$(grep -o 'VERDICT: [A-Z-]*' "$CLOSELOG" | head -1 | sed 's/VERDICT: //')"
```

`[A-Z-]*` stops at the space. The close verdicts are `QUIESCENT`, `QUIESCENT-WITH-RUNS`,
`REFUSED` — and **`CAPTURE CONTAMINATED`**. The fourth truncates.

I drove it: a wrapper run whose "capture command" doctors the open witness in `/tmp` (no SQL at
all) `[VERIFIED: out/r6-wrapper-red-provenance.txt]`:

```
  rollup_open       c3f489c5bef2023af86ea2c43718a7c2
  rollup_close      4c0adcae1804d88464265fc0f7661891
  witness_verdict   CAPTURE          <-- the contamination marker
  witness_exit      1
```

**The block is sold as "machine-greppable" and its verdict field reads `CAPTURE`.** A downstream
check for `CONTAMINATED` never matches — fail-open in the one direction that costs something —
while a check for `QUIESCENT` fails closed. Given FU-T417-1 proposes lifting exactly this block
into vector provenance, it should not be lifted as-is.

**It is already in T417's own committed evidence.** `out/DRIVE-CAPTURE-WRAPPER.txt:188` reads
`witness_verdict	CAPTURE`. The red arm ran, produced the wrong value, and no arm asserted on
the field. That is the *decorative red arm* T417 correctly diagnosed for RED-4b, one layer out.
**Drive:** `grep -o 'VERDICT: [A-Z][A-Z -]*'`, and add a wrapper arm that asserts
`witness_verdict == CAPTURE-CONTAMINATED`. **CONDITION C-T438-4 (MINOR).**

### F-T438-6 (MINOR) — the `MOVED` report garbles sequence rows

`cmd_close:377` reads the join output with `while IFS=$'\t' read -r nm r1 d1 r2 d2`. Tab **is**
IFS whitespace, so bash collapses runs of it; a `seq` row has no 4th field, so the empty column
vanishes and every later field shifts. Driven `[VERIFIED: out/r5-my-own-red-arms.txt RED-C]`:

```
  ***  acc_gl_journal_entry_id_seq  rows 999999 ->    digest 113 ->    MOVED
```

The doctored value is printed under **rows**, the true value under **digest**, and both arrows
point at nothing. **Detection is correct** (`awk '$2!=$4 || $3!=$5'` compares the right fields
and the exit code is 1) — it is the line a human reads to decide whether to bin a vector that is
wrong. It survived because **none of the 13 drive arms moves a sequence only**: half the graded
surface has no red arm of its own.
**Latent, same root cause:** `print_runs:292` uses the same construct over seven fields
including `j.name` (a `LEFT JOIN`, so NULL-able) and `end_time`. A run row with a NULL
`end_time` — the "app died mid-job" case this instrument exists for — would shift every column.
Today there are **0** such rows `[VERIFIED: 0 null end_time, 0 null start_time, 13370 rows]`, so
it is latent, not live.
**Drive:** replace `IFS=$'\t' read -r …` with `awk -F'\t'`, or pad the seq rows to four fields.
Add a sequence-only red arm and a NULL-`end_time` run-list arm.


### F-T438-11 (MINOR) — `capsql.sh`'s read-only guarantee has a hole, and it is ordinary SQL formatting

`capsql.sh:20-23` states the guarantee in its own header — *"READ-ONLY by construction: refuses
any file containing a write verb before it contacts the database"* — and implements it as:

```bash
if grep -Eqi '(^|[^[:alnum:]_])(insert|update|delete|truncate|drop|alter|grant|revoke)[[:space:]]' "$f"; then
```

`grep` is **line-based**, and the pattern requires a whitespace character **on the same line**
after the verb. I tested the regex against five files (no database contacted)
`[VERIFIED: out/r10-capsql-writeverb-cases.txt]`:

| case | result |
|---|---|
| `INSERT INTO x VALUES (1);` | REFUSED — correct |
| `DELETE`⏎`  FROM acc_gl_journal_entry;` | **ALLOWED** — the verb ends the line |
| `INSERT(1);` | **ALLOWED** — followed by `(`, not whitespace |
| `SELECT 1;` | ALLOWED — correct |
| `-- we must never UPDATE the oracle` | REFUSED — over-broad on comments, but fail-CLOSED, harmless |

`DELETE` on its own line with `FROM` on the next is not contrived; it is how long DML is
routinely formatted. The rig's whole reason for existing is that *"a capture rig that can write
to a shared append-only oracle is a casualty generator"* — its own words — and on this program's
shared instance that is the highest-consequence fail-open in the diff, even though nothing in
T417's four committed `.sql` files comes near it (I re-scanned all four: **zero** write verbs,
**zero** float/numeric casts, **zero** prohibited engines or vendors, **zero** hard-coded time
offsets, **zero** insured/guaranteed language `[VERIFIED: out/r11-t417-diff-scan.txt]`).

**Drive / fix:** read the file with the newlines squashed —
`tr '\n' ' ' < "$f" | grep -Eqi '…[[:space:](]'` — and add the two cases above as red arms.
**CONDITION C-T438-9 (MINOR).**

### F-T438-7 (LOW) — three citations off by 1–3 lines

`[all VERIFIED @ 426a23544 with grep -n]`

| cited | actual | symbol |
|---|---|---|
| `SchedularWritePlatformServiceJpaRepositoryImpl.java:159` | **`:158`** | `setCurrentlyRunning(true)` |
| `SchedulerJobListener.java:100` | **`:103`** | `setCurrentlyRunning(false)` |
| `SchedulerJobListener.java:105-108` "saves it" | construction `:105-107`, **save at `:109`** | `saveOrUpdate` |

File and symbol are right in every case, so no argument depends on the drift. Recorded because
this program's rule is that a line number is read out of a verified pin, and a reader who opens
`:100` finds an unrelated line. **Drive:** re-`grep -n` and correct the three, in the instrument
header and the handoff.

---

# 8. What I ran and found CLEAN (so silence is distinguishable from not looking)

- **The instrument reproduces, end to end, on the live oracle.** `open`, `close`, `--self-test`,
  `coverage`, `attribute` ×2, `verify`, and the `sh` interpreter guard — all re-run by me
  `[out/r4-witness-suite-rerun.txt]`. `open`/`close` → `QUIESCENT` exit 0, 273/249.
  `--self-test` → `base_tables=281 graded=273 excluded_named=8`, OK, exit 0. `sh` → **exit 3**,
  and it is correctly *not* exit 2.
- **Attribution reproduces exactly.** Job 11's insert window `[.100207, .117772]` → **1 run,
  jrh 12721 job 11 CONTAINS, SOLE CANDIDATE, exit 0**. Job 9's mutation window
  `[.033938, .039824]` → **3 overlap, 2 CONTAIN (jrh 12720 job 9 and jrh 12719 job 17), plus
  jrh 12718 job 30 [failed] overlapping — REFUSES TO NAME ONE, exit 1.** Exactly T409's and
  T417's measurement, arrived at independently.
- **Five red arms of my own design, all red** `[out/r5-my-own-red-arms.txt]`: doctored **ledger
  table** digest → MOVED exit 1; doctored **in-flight** flag → REFUSED exit 1; doctored
  **sequence** → MOVED exit 1; a table **removed** from the open witness → `APPEARED` exit 1;
  `close` with no open witness → "absence is not quiescence" exit 1. The guard discriminates;
  it is not a control that cannot fail.
- **`verify` across 27 minutes and ~27 job-36 runs → `UNMOVED`, rollup byte-identical.**
- **Ledger cardinals** 109 / max id 113 / 38 distinct transaction_id; `acc_gl_closure` 0 rows —
  unchanged from both predecessors.
- **The merge is clean**: `main e4bde474` + `T417 131218cf` → `0c35140a`, **no conflicts**, and
  `conformance.sh` is byte-identical to `main`'s on both trees.
- **No floating point, no money value, no `Idempotency-Key` path, no MySQL/MariaDB/Oracle
  driver, no US payment rail, no deposit endpoint** introduced anywhere in T417's diff — I read
  every one of the seven `.sh` files and the four `.sql` files. **All `psql` invocations are
  `SELECT`-only**, and `capsql.sh` refuses write verbs before contacting the database.
- **T417's scope discipline held**: `git diff` against its own merge-base `683c8aff` is one `M`
  (the `oracle-state-baseline.sh` header) plus its own capture directory. The `conformance.sh`
  and deletion noise it warns about in a `main` diff really is `main` moving ahead — I confirmed
  it by merging rather than by diffing.

---

# 9. BAR — run twice, by me, on both trees

Scratch checkouts are **`/tmp/t438/repoA` and `/tmp/t438/repoB`**, both outside the repository
and not nested in one another, so `guard_no_narrow_catch_in_capture_rigs`'s recursive walk
never sees a nested checkout.

|  | **A — T417's tree** | **B — MERGE RESULT** |
|---|---|---|
| HEAD | `131218cf` (`softhouse/T417-scheduler-attribution`) | **`0c35140a`** = `main e4bde474` + `T417 131218cf` |
| tree clean | yes (0 entries) | yes (0 entries) |
| **EXIT CODE** | **0** | **0** |
| **`probe = ` line PRINTED AT ALL** *(presence tested before value)* | **YES — `grep -c 'probe = '` = 1** | **YES — `grep -c 'probe = '` = 1** |
| its value | `reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up` | *identical* |
| **`VERDICT:` line** | `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.` | *identical* |
| **wrong ledger implementations** | **discovered 15, pinned 15, all 15 KILLED** | **discovered 16, pinned 16, all 16 KILLED** |
| dead-path census | `corpus=1460 deadFiles=75 deadOccurrences=108 resolving=1387 indeterminate=114 prose=380` | `corpus=1501 deadFiles=75 deadOccurrences=108 resolving=1433 indeterminate=114 prose=385` |
| repo-state attest frontier | 11, pinned at 11 | 11, pinned at 11 |
| temp-path census | 18, pinned at 18 | 18, pinned at 18 |
| ledger parity | PASS 10 / FAIL 0 | PASS 10 / FAIL 0 |
| ledger cells | 268 graded, of which **63 MONEY cells in int64 minor units** | identical |
| exemption census | graded 4 / loaded 4 / GROUNDED 4 / UNDETERMINED 0 / UNGROUNDED 0 / LEDGER declared 0 / LEDGER parity 10 / LEDGER oracle-refusal 6 / LEDGER money cells 63 — **every figure `== pinned`** | identical |
| divergence vectors | PASS 1 / FAIL 0 (pinned 1) | PASS 1 / FAIL 0 (pinned 1) |
| fail-open corpus | 1460 tracked `.sh`/`.py` | 1501 tracked `.sh`/`.py` |
| guard cost | PASS — every guard timed, none breached | PASS — every guard timed, none breached |

**The merge result shows 16, as the record required.** The extra kill in B is
`ledger-wrong-mapping-key-ignored` (parity FAIL 3), which is T421's, absent from A because T417
forked before T421 merged — the exact explanation T417 gave, now confirmed by running it rather
than by reasoning about it.

**T417 added seven tracked `.sh` files to the dead-path corpus and moved `deadOccurrences` by
ZERO — 108 on both trees.** Claim verified.

Transcripts: `out/BAR-A-t417-tree-131218cf.txt`, `out/BAR-B-merge-result-0c35140a.txt`.

---

## 9b. A third bar — on MY OWN branch — and a red I caused and fixed

A review that reddens the bar it is grading against is worthless, so I ran the bar a **third**
time, on `main + softhouse/T438-review-t417`. **The first attempt went EXIT 2, and my own
evidence file was the cause.**

```
conformance:   literal /tmp, /private/tmp or /var/tmp path to a name: 19, pinned at 18
conformance: THE HOST-STATE CENSUS IS NOT THE PINNED CENSUS (- pinned, + measured):
+.softhouse/reviews/t438-review-t417/out/r11-t417-diff-scan.driver.sh | T=/tmp/t438/t417tree/…
conformance: EXIT 2 — no verdict is available. This is NOT a pass.
```
`[out/BAR-C2-my-branch-EXIT2-before-fix.txt]`

My scan driver performs a repo-wide `grep -r`, which puts it in `guard_no_host_state_in_lint_corpus`'s
corpus, and it bound a literal `/tmp` path to a name — a **new** row on a census pinned at 18.
The guard named the adoptable repair itself. I took the argument form instead: the driver now
takes the tree to scan as `$1` and binds no host path at all.

**Re-run after the fix `[out/BAR-C3-my-branch-EXIT0-after-fix.txt]`:**

| | **C — my branch, merged with `main`** |
|---|---|
| HEAD | `main e4bde474` + `T438 52825722` |
| **EXIT CODE** | **0** |
| `probe = ` PRINTED AT ALL | **YES — count 1**, value `… probe = up` |
| `VERDICT:` | `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.` |
| **wrong ledger implementations** | **discovered 16, pinned 16, all 16 KILLED** |
| host-state temp-path census | **18, pinned at 18** (back to the pin) |
| dead-path census | `corpus=1499 deadFiles=75 deadOccurrences=108 …` — **frontier moved by ZERO** |
| repo-state attest frontier | 11, pinned at 11 |
| guard cost | PASS — none breached |

Recorded rather than tidied away, for the same reason T417 kept its own two failures: **a
reviewer whose evidence turns the bar red and who quietly deletes the evidence has learned
nothing and told nobody.** The finding it produces is that `.softhouse/reviews/**` `.sh`
files enter the same censuses program instruments do — which is worth knowing before the next
reviewer commits a driver script.

---

# 10. Conditions, consolidated

| id | sev | condition | drive |
|---|---|---|---|
| **C-T438-1** | **MAJOR** | Wire the pin to something. The full form is a static "`capture_ref` implies `witness_ref`" guard modelled on `guard_no_float_in_capture_requests` [`conformance.sh:1214,1254`] — repo content only, never nightly-red. The cheap half, landable now: widen `guard_guards_dir_registration`'s population from `.softhouse/guards/**` to `.softhouse/**/instruments/*.{sh,py,go}`. | red arm: an instrument with no REACHED-BY row turns the bar red |
| **C-T438-2** | **MAJOR** | Fix `s3c`'s unfiltered `min()`, correct `2026-01-15` → **`2026-05-15`** at the site, and withdraw the instruction to distrust T409's value. | corrected query returns 2026-05-15 / 18 / 55 on this oracle |
| **C-T438-3** | MINOR | Name the two missing residual classes: within-window revert, and the **effective rounding mode in `MoneyHelper.roundingModeCache`** (seed `c_configuration.rounding-mode = 4`, graded; effective value, not). Emit the seed as a witness row. | doctor the row in a `/tmp` copy → `close` reports it MOVED |
| **C-T438-4** | MINOR | `witness_verdict` must not truncate `CAPTURE CONTAMINATED`. | wrapper arm asserting `witness_verdict == CAPTURE-CONTAMINATED` |
| **C-T438-5** | MINOR | `--self-test` must assert the **sequence** exclusion too (5, each named), not only the table exclusion. | plant `job_idX_seq` in a scratch copy → self-test refuses |
| **C-T438-6** | MINOR | Fix the window-endpoint skew: emit `db_now_utc` after `read_tables` and attribute over `[open.first, close.last]`. | `attribute` over a 0.6 s-shifted window across a job-36 fire shows the run |
| **C-T438-7** | MINOR | Fix the `IFS=$'\t' read` field collapse in the `MOVED` printer; add a sequence-only red arm and a NULL-`end_time` run-list arm. | RED-C prints `last_value 113 -> 999999` correctly |
| **C-T438-9** | MINOR | `capsql.sh`'s write-verb refusal must survive a newline between the verb and its object. | `DELETE`\u23ce`FROM x` is REFUSED |
| **C-T438-8** | LOW | Correct three line numbers (`:159`→`:158`, `:100`→`:103`, save at `:109`); scope the `:211` `UPDATE` to the command-handler path; fix "34/41/43 are inactive" → all five are. | `grep -n` at the pin |

---

## Closing

The thing T417 was asked to remove — a pin that catches the scheduler only when the scheduler
happens to write to a table someone thought to watch — **is removed.** 273 of 281 tables, the
8 excluded are inert with respect to money, the trap was correctly identified and correctly
avoided, the blanket refusal was rejected on a measurement I reproduced, and the in-flight hole
is refused rather than glossed. The two MAJOR items are not defects in that reasoning: one is a
number that got in front of the reasoning, and the other is that nothing runs any of it yet.

**APPROVED WITH CONDITIONS.**

---

*Reviewer honesty statement: everything above marked `[VERIFIED]` I observed myself, in this
fire, from the live oracle at `fineract_gerege` or from `/Users/buv/fineract` confirmed at
`426a23544e8426a38ae43ae404670a0a7e85b9eb`. Items I did NOT check: I did not re-derive
`JOB-SOURCE-MAP.txt`'s 41-of-41 enum mapping; I did not re-run T417's 13-arm witness drive or
its 7-arm wrapper drive as committed (I wrote and ran five red arms of my own design instead);
I did not test T409's 16:01 prediction, which is still ~15 hours away as I write; and I did not
construct an adversarial case where two distinct rows render identically under `row::text`.*
