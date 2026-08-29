# T417 — G-22: the reference oracle edits itself overnight. The pin is a **witnessed capture window**, and it never asks who wrote a row.

**Branch** `softhouse/T417-scheduler-attribution` · fire `20260829-080002` · oracle **REACHABLE** throughout
**Reference oracle** Fineract pinned `426a23544e8426a38ae43ae404670a0a7e85b9eb` — verified with `git -C /Users/buv/fineract rev-parse` before a single line number was read out of it
**Database** PostgreSQL 18.3, container `fineract-db-1`, database `fineract_gerege`, session `TimeZone = Etc/UTC`
**Every statement this task issued against the oracle is a SELECT.** Nothing was written to the shared instance, at any point, by any arm — including the red arms.

---

## Changes Made

### 1. `instruments/oracle-window-witness.sh` — the pin (NEW)

`.softhouse/capture/t417-scheduler-attribution/instruments/oracle-window-witness.sh`

```
open <label>            record the oracle's state before a capture
close <label>           record it after, diff, and REFUSE if it moved
verify <label>          has the oracle moved SINCE that witness?  (vector shelf life)
attribute <from> <to>   which job runs overlap a window -- and REFUSE to name one if >1
coverage                the declared ungraded region, derived
--self-test             the population is non-empty and the exclusion list is a strict subset
```

It reads exactly three things, and **`created_by` / `last_modified_by` are not among them** (see *The trap*):

1. **CONTENT** — a per-table content digest, `md5(string_agg(md5(row::text) ORDER BY …))`, over **every base table** except eight named ones. Order-independent, column-complete, **mutation-sensitive**: an `UPDATE` below the floor changes it, a `DELETE` changes it, and a row in a table that carries no audit column at all changes it.
2. **SEQUENCES** — `pg_sequences.last_value`, which moves when a sequence is **consumed** even if the row was never persisted. That is T371's exception class (a), previously reachable only indirectly.
3. **THE SCHEDULER'S OWN BOOKKEEPING** — `job_run_history` and `job`. This is the **witness**, never the evidence: it says a job ran; it does not say what it wrote.

Exit codes deliberately parallel `conformance.sh`: `0` quiescent · `1` contaminated/refused · `2` oracle unreachable (**not** a verdict) · `3` wrong interpreter.

### 2. `instruments/capture-under-witness.sh` — the one-line adoption (NEW)

```
bash .../capture-under-witness.sh <label> -- <your capture command>
```

Opens a witness, runs the capture, closes the witness, writes a **machine-greppable provenance block**, and refuses non-zero if the oracle moved while the capture was open. The provenance block carries the graded-surface rollup at both ends, the `job_run_history` high-water mark at both ends, the number of job runs inside the window, the verdict, and the exact command a later reader runs to re-check shelf life.

### 3. `drive/drive-witness.sh` — **13 arms, 13 pass**  → `out/DRIVE-WITNESS.txt`

| arm | expected | got |
|---|---|---|
| GREEN-1 quiescent window, undoctored | 0 | **0** |
| **RED-1 replay of the real 00:01 sweep** — ledger moved, 626 runs overlap | 1 | **1**, attribution REFUSED |
| GREEN sole-candidate: job 11's insert window names ONE author | 0 | **0**, names jrh 12721 / job 11 |
| **RED-3 job 9's mutation window** — 3 overlap, 2 contain | 1 | **1**, REFUSES to name one |
| **RED-4 graded content moved with NO job run** | 1 | **1**, "the scheduler did not do this" |
| GREEN-2 control, identical mechanism, undoctored copy | 0 | **0** |
| **RED-4b a job was IN FLIGHT across a boundary** | 1 | **1**, REFUSED |
| RED-5 close with no open witness | 1 | **1**, "absence is not quiescence" |
| **RED-6 shelf life** — the oracle moved since the witness | 1 | **1** |
| GREEN-3 shelf-life control, honest witness | 0 | **0** UNMOVED |
| **RED-7 empty graded surface** — self-test must refuse, not pass everything | 1 | **1** |
| GREEN-4 shipped self-test | 0 | **0** |
| RED-8 invoked as `sh` | 3 | **3**, and it is not exit 2 |

### 4. `drive/drive-live-minute-boundary.sh` — **the live arm** → `out/DRIVE-LIVE-minute-boundary.txt`

A real capture window deliberately spanning a scheduler minute boundary, so a **real scheduled job ran inside it**. Result, `QUIESCENT-WITH-RUNS`, is the measurement that decided the whole design — see *Which of the three options, and why not the others*.

### 5. `drive/drive-capture-wrapper.sh` — **7 arms, 7 pass** → `out/DRIVE-CAPTURE-WRAPPER.txt`

Including a **GREEN arm that runs a real read-only capture** (the committed `capsql` rig) inside a witnessed window and checks the provenance block it produced, and a RED arm where the oracle moves under the capture.

### 6. `drive/map-jobs-to-source.sh` → `out/JOB-SOURCE-MAP.txt`

Joins the **live** `job` table to `JobName.java` to the main-source classes referencing each constant. **41 job rows, 41 mapped to an enum constant, 0 unmapped.** It refuses to run if `/Users/buv/fineract` is not at the pinned commit.

### 7. `.softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh` — class (d) widened (EDIT)

T409's condition **C3** applied to the header block only:

- class (d) now says the scheduler **MUTATES**, not merely inserts, with job 9's raw `UPDATE` cited from source and the intersection with class (c) stated;
- **the typed cardinal "nineteen jobs" is removed.** It was wrong; the file's own header says it *"TYPES NO COUNT"*. Replaced with the derived figure and the SELECT that re-derives it;
- the user-2 warning is sharpened from a hypothetical to the measured fact that makes it fatal;
- points at the new instrument, stating that it **complements** rather than replaces (one grades a WINDOW, the other grades ATTRIBUTION).

Behaviour unchanged; the instrument still exits 0. **`PROBES.tsv` was NOT touched** — nothing needed registering, because nothing has moved in the ledger since T390's append (measured below).

### 8. `capsql.sh` — read-only capture rig (NEW)

`ON_ERROR_STOP=1`, sha256 beside every transcript, and a **write-verb refusal that runs before the database is contacted** — a capture rig that *can* write to a shared append-only oracle is a casualty generator.

---

## What I observed from the live oracle (with instants)

Every figure below is from a committed transcript with its statement's sha256 beside it. **Nothing is transcribed from T390 or T409.**

### The scheduler, re-derived — and T409's F-T409-3 is confirmed

`out/s1-jobs.txt`, **2026-08-29T00:09:30Z**:

| | |
|---|---|
| job rows | **41** |
| `is_active = t` | **31** |
| inactive | **10** |

**"Nineteen jobs are active" is wrong**, in the task brief, in `FU-T390-4`, and in the committed instrument header. It is **31**, and 31 distinct jobs ran in the preceding 24 hours [`out/s2-job-run-history.txt` s2c]. The blind spot was **63% larger than stated**. T409 measured this as F-T409-3 (MODERATE); I re-derived it independently and it is now corrected at the site.

### The 2026-08-28 16:01 sweep, re-derived from job_run_history

`out/s2-job-run-history.txt` s2e — **21 job runs** overlap the minute 16:00–16:02 UTC on 2026-08-28. Endpoints, exact:

| jrh | job | window (UTC) | status |
|---|---|---|---|
| 12718 | 30 Update Trial Balance Details | `.003` → `.034` | **failed**, `ClassCastException` |
| 12719 | 17 Recalculate Interest For Loans | `.032` → `.048` | success |
| 12720 | **9 Update Accounting Running Balances** | `.003` → `.048` | success |
| 12721 | **11 Add Accrual Transactions** | `.049` → `.120` | success |

### The ledger, right now — **and it has not moved since T409 measured it**

`out/s3-ledger-now.txt`, **2026-08-29T00:09:30Z** (re-captured at 00:27:22Z by the wrapper drive, identical):

```
acc_gl_journal_entry rows/maxid          109/113          (== T409 out/r18)
distinct transaction_id                  38               (== T409)
acc_gl_closure rows/maxid                0/null
m_portfolio_command_source rows/maxid    379/379          (== T409)
m_loan / m_office                        8 / 1
max created_on_utc                       2026-08-28 16:01:00.117772+00
max last_modified_on_utc                 2026-08-28 16:01:00.117772+00
```

The most recent write of any kind to the ledger is **still the scheduler's**, ~8 hours before I looked. `oracle-state-baseline.sh` run at the start of this task: **exit 0, ALL MOVEMENT ATTRIBUTED** [`out/BASELINE-instrument-at-start.txt`].

### The mutation, re-derived (T409's F-T409-1)

`out/s3-ledger-now.txt` s3b:

```
created BEFORE 16:00Z and modified at/after it : 91
last_modified_on_utc > created_on_utc          : 91
oldest such row created                        : 2026-08-21 06:03:41.494198+00
mutations ran                                  : 16:01:00.033938 .. 16:01:00.039824
distinct last_modified_by over all 109 rows    : 2
distinct created_by over all 109 rows          : 1,2
```

**CONFIRMED, independently.** And the source citation, verified at the pin:

- `JournalEntryRunningBalanceUpdateServiceImpl.java:163-164` — `UPDATE acc_gl_journal_entry SET is_running_balance_calculated=?, organization_running_balance=?, office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?`, on `jdbcTemplate`, no JPA, no command bus. `updateRunningBalance()` at **`:71`** restarts from `MIN(entry_date) WHERE is_running_balance_calculated=false` — the `dateFinder` string is `:72-73`, and a second copy of the same restart query is at `:93`.
- **A second raw UPDATE that T409 did not name:** `:211` — `UPDATE acc_gl_journal_entry SET office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?`. Same class, same file, also `batchUpdate`.
- **The user id is not a scheduler marker, and the source says so:** both UPDATEs bind `last_modified_by` from `platformSecurityContext.authenticatedUser().getId()` — **`:178`** for the `:163-164` statement and **`:214`** for the `:211` one. It is *whoever the job is authenticated as* at run time, a runtime fact and not a constant.

### The attribution cardinals, re-derived through the new instrument

```
attribute 2026-08-28 16:01:00.100207  .117772   (job 11's INSERT window)
  -> 12721 job 11 CONTAINS      RUNS OVERLAPPING WINDOW = 1     SOLE CANDIDATE (rc 0)

attribute 2026-08-28 16:01:00.033938  .039824   (job 9's MUTATION window)
  -> 12718 job 30 overlaps
     12720 job  9 CONTAINS
     12719 job 17 CONTAINS      RUNS OVERLAPPING WINDOW = 3     REFUSES TO NAME (rc 1)
```

**Exactly T409's measurement: three overlap, two contain.** The instrument refuses rather than picking one — which is C3(i), enforced in code rather than written in prose.

### The live minute-boundary arm — the measurement that shaped the design

`out/DRIVE-LIVE-minute-boundary.txt`, window `2026-08-29 00:15:32.838096` → `00:16:53.566795` UTC:

```
13337  job 36  Send Asynchronous Events  00:16:00.002 -> 00:16:00.028  [success]
RUNS OVERLAPPING WINDOW = 1
GRADED SURFACE: nothing moved. rollup open == close == 4c0adcae1804d88464265fc0f7661891
VERDICT: QUIESCENT-WITH-RUNS (exit 0)
```

A real scheduled job ran inside a real capture window and **moved nothing on the graded surface**. Job 36 has cron `0 0/1 * * * ?`, **1440 runs in the last 24h and 10623 all-time** — it runs every minute without a gap.

### The provenance gap in the vector store, measured

`.softhouse/vectors/ledger/LDG-ACC-03-accrual-six-slots-scheduled-job.json` carries `provenance.capture_ref` + `capture_sha256` and `oracle.fineract_commit` + `oracle.captured_at`. **No field records whether the oracle was still.** That vector's subject is transaction **L32 — a transaction the scheduler wrote**, so the store already grades against autonomously-produced state with no witness of the conditions.

---

## The trap, and how I avoided it

**The trap, in my own words: an attribution rule keyed on an app user id answers the wrong question, and answers it wrongly in both directions.**

It is not sufficient. `system` is an ordinary row of `m_appuser` — id 2, sitting next to `1 mifos` and `3 interopUser` [`out/s3-ledger-now.txt` s3e]. Anything holding those credentials writes rows the rule cannot distinguish from the scheduler's: a human at psql, a fixture load, a batch API call. The rule would wave those through as "the scheduler, that's fine."

It is not necessary. `last_modified_by` comes from `platformSecurityContext.authenticatedUser().getId()` at the moment the job runs [`JournalEntryRunningBalanceUpdateServiceImpl.java:178` and `:214`, VERIFIED at the pin]. Reconfigure the scheduler's identity — or add a second tenant with a different one — and every scheduler write stops matching the rule. The instrument then reports **silence**, and silence reads as clean. **The failure mode is invisible, which is the worst kind.**

It is already fatally overbroad, and this is not a hypothetical any more. **`last_modified_by = 2` is true of every one of the 109 rows in `acc_gl_journal_entry`** [`out/s3-ledger-now.txt` s3d — `distinct last_modified_by: 2`]. A user-2 exemption would not excuse *future* scheduler writes; it would retroactively excuse **the entire ledger**, including every probe T352, T359 and T388 ever fired. The alarm would be converted into a blanket amnesty, and the conversion would look like a one-line simplification in a diff.

And it inverts the burden. "Who was allowed to have written this?" is a question about permission. The question a capture actually needs answered is **"did anything move while I was looking?"** — a question about movement, which does not care who moved it.

**How the design avoids it.** `oracle-window-witness.sh` **never reads `created_by` or `last_modified_by`. Not once.** It compares *content* before and after a window. That has four consequences the user-2 rule cannot have:

1. **It cannot be defeated by identity.** Reconfigure the scheduler to run as anybody; the digest changes when rows change, and it changes the same way.
2. **It sees mutations.** A `max(id)` floor detects appends only; the digest sees the 91 rewrites that both existing floors moved by zero for.
3. **It needs no per-job table map**, so it does not silently narrow when Fineract adds a job or when a job does something its class name did not predict. `map-jobs-to-source.sh` produces such a map, and *nothing consults it* — it exists so a human can reason, deliberately not so the instrument can.
4. **When it does attribute, it refuses to guess.** Naming a job is a separate, narrower operation, and it refuses outright when interval containment does not resolve — which, measured, is exactly what happens for the 91 mutations.

The one thing I kept from the user-id world is the *warning*, moved from prose into behaviour: the old instrument's header now states the retroactive-amnesty measurement, and the new instrument's header states in full why user 2 is not a signature.

---

### Which of the three options, and why not the other two

The brief offered three. I chose **(b) record the scheduler's state as part of a capture's provenance**, **hardened into (c) a guard that refuses**, and **rejected (a) quiescing**.

**(a) Disable the active jobs for the duration of a capture — REJECTED.**
Three costs, and the second is the one that decides it.

- *It makes the oracle less like production.* The nightly sweep is not noise; it is Fineract behaviour we are eventually going to have to port and grade. A vector corpus captured only against a quiesced instance would never contain the accrual-completion and running-balance behaviour that job 11 and job 9 actually produce — and `LDG-ACC-03` shows we already have a vector whose subject *is* a scheduler-written transaction. Quiescing would have made that vector uncapturable.
- ***It is a WRITE to the shared oracle.*** Setting `is_active = false` on 31 jobs is a mutation of `job`, on an instance that every other task's vectors are graded against, performed by a rig whose entire purpose is to stop unrecorded mutation. If a fire dies between disable and re-enable — and **the previous fire killed nine workers mid-flight** — the oracle is left quiesced with nobody knowing, and every subsequent "quiescent" window is quiescent for the wrong reason. That is a fail-open with a very long tail.
- *It does not even solve the problem.* It stops the *scheduler*; it says nothing about a human, a migration, or another concurrent task. RED-4 in my drive is precisely that case, and quiescing would report it clean.

**(c) A guard that refuses a capture taken while a job ran inside its window — REJECTED IN THAT FORM, and the reason is measured, not argued.**
Job 36 runs **every minute, 1440 times in 24 hours**. A blanket refusal on "a job run overlaps the window" refuses **every capture that takes longer than sixty seconds**. That is not a pin, it is an outage — and an instrument that refuses everything is the same defect as one that can never fail (P-98). My live arm is the proof: a real job ran inside a real window and moved **nothing**.

**(b), hardened — CHOSEN.** Record the scheduler's state as provenance, **and refuse on measured movement of graded content** rather than on the possibility of it. This keeps the refusal (the useful half of (c)) while dropping its false-positive rate to the cases that actually matter, and it keeps the oracle production-shaped (the useful half of rejecting (a)). A window with jobs in it and no movement is reported `QUIESCENT-WITH-RUNS` — **proven harmless for that window by measurement, not waved through by a classification and not by who the writer was.**

The one place I did keep an unconditional refusal is **in-flight**: `job_run_history` is written only when a job *finishes* [`SchedulerJobListener.java:58`, `:105-108`, `setEndTime(new Date())`], so a job running across a window boundary is absent from the run list by construction. `job.currently_running` is read at both ends and a non-zero reading **refuses the window**. That hole is refused, not missed.

**Deliberately NOT wired into `conformance.sh`.** The bar runs on a tree, at a time nobody chose, against an oracle that legitimately moves at 00:01 Asia/Ulaanbaatar every night. A state digest pinned in the bar would go red daily for reasons no diff caused — P-45 wearing the opposite hat, a check that cries so reliably its red carries no information. The question this pin answers only exists **at capture time**, so the enforcement point is the capture. The wrapper makes adoption one line. `.softhouse/conformance.sh` is **unchanged by this task**, and T404 held it last wave. Measured against my **merge-base** `683c8aff`, not against `main`: `git diff 683c8aff --name-status` is exactly one `M` — the class-(d) header in `oracle-state-baseline.sh` — plus my own capture directory. (`git diff main` additionally shows a one-line difference in `conformance.sh` and several deletions; those are `main` moving ahead of my fork point when T421/T428 merged, **not** edits of mine. Read the merge-base diff, not the `main` diff, or you will attribute another task's work to this one.)

---

## Coverage — what remains unwatched, by name

Derived, not asserted: `bash .../instruments/oracle-window-witness.sh coverage` → `out/COVERAGE.txt`, and it types no cardinal.

```
TABLES      base tables in the tenant schema : 281
            GRADED by the content digest     : 273
            EXCLUDED, each named below       :   8
SEQUENCES   sequences in the schema          : 254
            GRADED by last_value             : 249
SCHEDULER   job rows / active / inactive     : 41 / 31 / 10
            distinct jobs that ran in 24h    : 31
            ACTIVE jobs with NO run history  : (none)
```

**The eight excluded tables, by name, with the reason.** They are the scheduler's **own bookkeeping**, they move every minute by construction, and including them would make every window contaminated and the instrument worthless:

`batch_job_execution` · `batch_job_execution_context` · `batch_job_execution_params` · `batch_job_instance` · `batch_step_execution` · `batch_step_execution_context` · `job_run_history` · `job`

**The five excluded sequences, by name:** `batch_job_execution_seq` · `batch_job_seq` · `batch_step_execution_seq` · `job_id_seq` · `job_run_history_id_seq`.

Note what is **not** excluded: `m_external_event`, job 36's payload table, is **graded**. Only the batch runner's ledger of itself is out, not business rows any job touches.

**Which of the 41 jobs remain unwatched: none, for finished runs — and here is the argument, settled from source rather than assumed.**
`SchedulerJobListener` is installed with `schedulerFactoryBean.setGlobalJobListeners(jobListeners)` [`JobRegisterServiceImpl.java:319,322`], for **both** the cron scheduler [`:293`] and the temporary scheduler a manually-triggered execution uses [`:116`]. *Global* means every job on that scheduler. `jobWasExecuted` [`SchedulerJobListener.java:58`] saves a `ScheduledJobRunHistory` [`:105-108`] **including on failure** — `jobException != null` only sets `status = FAILED` [`:79-80`]. Confirmed live: job 30 failed with a `ClassCastException` and **still has its row**, jrh 12718.

**The residual, stated so nobody has to discover it:**

1. **The 8 excluded tables.** A write to them by anything other than the batch runner would not be reported.
2. **A job in flight across a window boundary.** No `job_run_history` row exists yet. **REFUSED, not missed** — `job.currently_running` is read at both ends. Driven: RED-4b.
3. **Movement *between* two windows.** The digest compares open to close. Continuity across captures is `verify`'s job, which compares a stored witness to the oracle now — that is the vector shelf-life check, and RED-6 drives it.
4. **Anything below the granularity of a table's rendered row text.** I know of nothing in this class; it is listed so the claim is falsifiable rather than absolute.
5. **State that is not in this database.** Files on the app container, in-memory caches, and the other tenant databases `fineract_default` and `fineract_tenants`. This instrument reads exactly one database and names it in its output on every run.
6. **Jobs 32, 33, 34, 41, 43 have never run** [`out/s2-job-run-history.txt` s2f: 36 of 41 jobs appear in history], and 34/41/43 are `is_active = f`. Nothing about them is *unwatched* — the digest would see their writes — but nobody has yet observed what they do.

**What is NOT unwatched, though a reader of the predecessor instrument would assume so:** the other **271** tables beyond the two `oracle-state-baseline.sh` reads. They are all in the digest. That is the whole point of it, and it is the specific luck-dependence — *"job 11 happens to write to one of the two watched tables"* — that this task existed to remove.

---

## Bar figures

`bash .softhouse/conformance.sh` on the **committed** tree `7626cece`, with `bash`, never `sh`. Transcript `out/BAR-1-clean-tree-7626cece.txt`. All scratch directories were under `/tmp` (`$TMPDIR/t417-drive-$$`, `$TMPDIR/t417-wrap-$$`) and are removed by a trap — nothing nested inside the repository.

| | |
|---|---|
| **EXIT** | **0** |
| **`probe = ` line PRINTED AT ALL** (presence tested BEFORE value) | **YES — `grep -c 'probe = '` = 1** |
| its value | `reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = **up**` (line 201) |
| **`VERDICT:` line** | `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.` (line 713) |

Pins, every one read from that transcript:

- parity vectors **PASS 46 / FAIL 0**; cells compared **7884** graded, 93 ungraded
- **`deadOccurrences=108`** — at the pin; census `corpus=1460 deadFiles=75 resolving=1387 indeterminate=114 prose=380`. This task added **seven** tracked `.sh` files to that corpus and moved the frontier by **zero**; none of my files contains a *quoted* literal holding `.softhouse/` (audited with the census's own selector shape before running it)
- repo-state attest **frontier 11, pinned at 11 — `frontier == pinned`**
- temp-path census **18, pinned at 18 — `census == pinned`, by path and source line**
- ledger parity **PASS 10 / FAIL 0**; ledger cells compared **268** graded, of which **63** are MONEY cells in **int64 minor units**
- exemption census: **every** figure `== pinned` — graded 4, loaded 4, GROUNDED 4, UNDETERMINED 0, UNGROUNDED 0, LEDGER declared 0, LEDGER parity 10, LEDGER oracle-refusal 6, LEDGER money cells 63
- wrong ledger implementations **discovered 15, pinned at 15**, all **KILLED** through the harness
- divergence vectors PASS 1 / FAIL 0 (pinned 1); contract-refusal and self-test fixture unchanged
- guard cost: `guard_dead_path_frontier` 1s / ceiling 60s; no guard over budget

The fire's stated `main` baseline was EXIT 0, probe PRESENT ×1 `up`, `VERDICT: PASS` 46/7884, `deadOccurrences 108`, frontier `11 == 11`. **All five match.** The ledger figures (10/63 rather than T390's 7/39) are higher than T390's transcript because vectors merged since; the exemption census confirms each against its own pin.

**Re-run the bar on the merge result regardless.** A transcript is evidence about the tree it ran on, never about a merge.

---

## Unverified

- **T409's falsifiable prediction cannot be checked in this fire, and I will not pretend otherwise.** It predicts that at **2026-08-29 16:01:00 UTC** job 9 will UPDATE **55** rows and the instrument will still exit 0. I am writing this at **2026-08-29T00:30Z** — that run is **about sixteen hours away**. What I *can* report is the pre-state it rests on, re-derived: `min(entry_date) WHERE NOT is_running_balance_calculated` = **2026-01-15**, `count(*) WHERE NOT is_running_balance_calculated` = **18**, and `count(*) WHERE entry_date >= that minimum` = **55** [`out/s3-ledger-now.txt` s3c]. **The 55 is confirmed as the pre-state; the prediction itself is UNTESTED.** Note T409 wrote the minimum as `2026-05-15`; I read **2026-01-15**. The count is 55 either way, so I did not chase the discrepancy — but a later reader should not take `2026-05-15` from T409 without re-deriving it. `[UNVERIFIED: the 16:01 run has not happened]`
- **The job→source map names *referencing* classes, not exclusive owners.** `grep -rlE "JobName\.CONST[^A-Za-z0-9_]"` finds every main-source file that mentions the constant; for jobs 34 and 43 that is several files including test-support classes. It is a reading aid, and **nothing in the instrument consults it**. `[VERIFIED as what it is; UNVERIFIED as an owner map]`
- **I did not read what each of the 31 active jobs writes.** I deliberately did not: a per-job table map is exactly the artefact whose staleness the witness is designed not to depend on. What each job *can* move is `[UNVERIFIED]`; what each job *did* move inside a witnessed window is measured, per window.
- **The digest's completeness rests on `row::text` rendering every column.** I did not construct an adversarial case where two distinct rows render identically. `[UNVERIFIED, and listed in the coverage residual as item 4 so it is falsifiable]`
- **I did not drive `--prove` on a tree with the witness wired in**, because I wired nothing into `conformance.sh`. T409's condition **C1** is about T390's wiring patch and remains open for whoever lands it; nothing I did makes it easier or harder.
- `.softhouse/vectors/ledger/LDG-ACC-03-…json` carries `oracle.captured_at: 2026-08-29T09:00:00Z`, which is **8.5 hours in the future** relative to this fire. I read the field; I did not investigate it. `[UNVERIFIED — see FU-T417-4]`

### Two failures of my own, kept rather than tidied away

1. **RED-4b passed green on its first run, and the drive caught it.** The in-flight refusal arm doctored `^meta\tcurrently_running`, but the field is emitted with a leading `jobs`, not `meta` — so the `sed` matched nothing, the copy was undoctored, and the arm produced rc 0 while reading as *"the refusal does not work."* **A doctoring that silently fails to doctor is exactly how a red arm becomes decorative.** The failing transcript is kept as `out/DRIVE-WITNESS-FIRST-ATTEMPT-red4b-failed.txt` and the reason is written at the site.
2. **The job map's first version prefix-matched enum constants.** `grep -rl "JobName.ADD_PERIODIC_ACCRUAL_ENTRIES"` also matches `JobName.ADD_PERIODIC_ACCRUAL_ENTRIES_FOR_SAVINGS_WITH_INCOME_POSTED_AS_TRANSACTIONS`, so **job 16 was reported as backed by a *savings* config**. Fixed with a trailing `[^A-Za-z0-9_]`; the wrong map is kept as `out/JOB-SOURCE-MAP-FIRST-ATTEMPT-prefix-bug.txt`. I had a word boundary in the first draft, removed it during a rewrite, and did not notice until I read the output — **the map was wrong in exactly the place a plausible-looking map is most dangerous.**

---

## Follow-ups

- **FU-T417-1 (MAJOR).** **Adopt the wrapper in the next capture task.** The pin only pins what runs under it. One line: `bash .../capture-under-witness.sh <label> -- <your capture command>`. Every capture promoted to a vector from here on should cite its `witness/<label>.provenance.tsv`, and the vector's `provenance` block should gain a `witness_ref` + `rollup` pair so `verify` can answer the shelf-life question later. **That is a vector-schema change and needs an uncontended wave** — I did not make it, because the vector store was live under T429 this fire.
- **FU-T417-2 (MAJOR).** **Check T409's prediction after 2026-08-29 16:01 UTC.** Re-run `capsql.sh s3-ledger-now` and compare s3b/s3c. If `last_modified_on_utc` advances on 55 rows while `oracle-state-baseline.sh` stays green, F-T409-1 is established end to end. If it does not, find out why **before** anyone builds on the model. My witness gives a second reading for free: `attribute '2026-08-29 16:00:00' '2026-08-29 16:05:00'`.
- **FU-T417-3 (MODERATE).** The instrument has **no continuity chain between captures**. `verify` compares a stored witness to *now*, which is the right primitive, but nothing forces the next capture's `open` to be compared against the previous `close`. A `chain` mode that does exactly that would turn "the oracle moved overnight" into a **dated, attributed record** instead of a thing each task rediscovers. Cheap to add on top; not added because it is a second instrument, not a fix to this one.
- **FU-T417-4 (MINOR).** `LDG-ACC-03`'s `oracle.captured_at` is `2026-08-29T09:00:00Z`, in the future relative to this fire. Either the field is Asia/Ulaanbaatar time mislabelled `Z` (+08 would make it 2026-08-29 01:00Z, still ahead of T391's own work), or it is wrong. A provenance timestamp that cannot be true is worse than an absent one. **Not investigated; not mine.**
- **FU-T417-5 (MINOR).** T409's C2 asked for the "nineteen" correction, and I made it in `oracle-state-baseline.sh`'s header — **but the same wrong cardinal is still in `FU-T390-4` in `T390-baseline-attribution.md` and in T417's own record in `tasks.json`.** I did not edit either: a handoff is a dated witness and correcting one in place forges it, and `tasks.json` is the scheduler's. Whoever closes this class should append a superseding note rather than retype.
- **FU-T417-6 (MINOR).** `guard_guards_dir_registration`'s population is `.softhouse/guards/**`, so both my instruments — like T363's before them — are **structurally invisible to the guard that exists to find unwired checkers** (FU-T390-3, still open). Two more instruments now sit in that blind spot. Widening that guard's population to `.softhouse/**/instruments/*.sh` would close it for the whole class.

---

**No money value was computed, rounded, compared or stored by this task. No floating point anywhere. Every statement issued against the reference oracle is a SELECT, and the shared instance was not written to — the red arms were manufactured from doctored COPIES in `/tmp`, never by probing the oracle.**
