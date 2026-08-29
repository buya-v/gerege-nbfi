# T429 — THE ORACLE WRITES A BALANCE ONTO A POSTED ROW. THE PORT NEVER WILL, AND NOW SOMETHING SAYS SO.

**Branch:** `softhouse/T429-oracle-derived-columns`. **Gate raised:** `G-22`.
**Fire** `20260829-080002`, local, oracle **REACHABLE**. Tenant `gerege`, database `fineract_gerege`,
PostgreSQL **18.3**, Fineract pinned **`426a23544e8426a38ae43ae404670a0a7e85b9eb`**
[verified with `git -C /Users/buv/fineract rev-parse HEAD` **before** a single line number was read
out of it; the checkout is clean].

**NO ENTITY IN THE REFERENCE ORACLE WAS CREATED, MODIFIED OR DELETED.** Every SQL statement went
through `capsql-readonly.sh`, which scans the executable bytes for a write keyword and exits 2
**before** `psql` is invoked; every HTTP exchange went through `capget.sh`, which has no method
argument and can only issue `GET`. Both rigs are byte-copies of T391's, committed in this task's
capture directory rather than sourced across directories (T287's rule).

**`docs/adr/DEC-2-gl-accounting-adapter.md` WAS NOT EDITED.** It is ratified. The proposed revision is
a separate file and the gate is raised.

---

## The declaration

`.softhouse/vectors/oracle-derived-columns.json`, schema `gerege.ledger.oracle-derived-columns.v1`.
It classifies **all 31 columns** of `acc_gl_journal_entry` — not the interesting ones, all of them,
because a table that declares 31 and lists 30 is silent about one, and the loader refuses that.

### ORACLE-DERIVED — 3 columns, ungraded BY DESIGN, and a mismatch is the port being RIGHT

| column | wire field | written by |
|---|---|---|
| `organization_running_balance` | `organizationRunningBalance` | job 9 → `JournalEntryRunningBalanceUpdateServiceImpl:163-181` |
| `office_running_balance` | `officeRunningBalance` | job 9 → `:163-181`, and `:211-217` which writes it **alone** |
| `is_running_balance_calculated` | `runningBalanceComputed` | job 9 → `:163-181`; also the job's own **work queue**, `:72-73` |

The reason is the same for all three and it is structural, not a judgement call: they are written by a
**raw batched `UPDATE ... WHERE id=?` from a service the JPA entity does not map**, driven from a
Spring Batch tasklet that does not pass through the command bus. A port that honours *"balances are
derived, never written"* has no field to put the number in — `PostedEntry`/`PostedLeg`
(`impl.go:61-96`) carry **no balance member at any level** — so it can never match them.

### PROVENANCE — 7 columns, ungraded for a DIFFERENT reason, stated separately per row

`id` (oracle-assigned surrogate key — the vector's identity is `transaction_id` + leg order),
`created_by`, `last_modified_by`, `created_on_utc`, `last_modified_on_utc`, `created_date`,
`lastmodified_date`.

**They are ungraded because they record the ACT of recording, not the fact recorded.** Two systems
that record the same posting at different instants under different actor ids have both recorded it
correctly. That is a different sentence from *"the oracle writes this and the port must not"*, and the
declaration keeps them apart deliberately.

**Three of the seven carry their own qualification, because a category applied without looking is how
a column ends up in the wrong one:**

- **`last_modified_on_utc` is provenance AND is moved by the denormalisation.** Job 9's `UPDATE` sets
  it on every row it recomputes. It has its own row and its own reason; it is not filed silently
  under "audit stamp".
- **`created_date` and `lastmodified_date` are DEAD** — `NULL` on 109 of 109 rows. Consequence for
  attribution, worth knowing: job 9 does **not** touch the legacy pair, so only the UTC pair moves.
- **`last_modified_by` is 2 (`system`) on 109 of 109 rows, including the 18 never modified.** On this
  table it is a creation stamp on an untouched row and a job stamp on a rewritten one, and **on its
  own it discriminates nothing** — which is what the DEC-2 sentence *about the other column* claims,
  and gets wrong.

### MONEY AND STRUCTURE — 3 GRADED, 18 GRADED_GAP, and NOT ONE MOVED OUT OF GRADING

`amount` → `legs[].amount_minor` · `account_id` → `legs[].gl_account_id` · `type_enum` →
`legs[].entry_side`. See "Money columns — confirmed still graded" below.

**`GRADED_GAP` is a fourth disposition and it exists to stop the third sliding into the first.** It
means *money or structure with no cell yet* — a **coverage gap**, printed as one on every run, never
an exemption. The 18 are listed in the block, by name. Collapsing "we do not grade this because the
port is right not to produce it" into "we do not grade this yet" is exactly how an exemption list
swallows a gap, so the two have different names and different printed sections.

### Where I looked for others — "not found" is a statement about the search

Recorded **in the declaration itself**, not only here, so it prints:

| searched | result |
|---|---|
| every column in the tenant schema ending `_derived` | **125 columns across 15 tables** |
| every column containing `running_balance` | **4**: the three above + `m_savings_account_transaction.running_balance_derived` |
| every column containing `balance` / `total_` / `cumulative` / `outstanding` | 77 |
| every `UPDATE`/`INSERT`/`DELETE` against `acc_gl_journal_entry` in the pinned tree, excluding tests | **3**: two `UPDATE`s (both in the running-balance service) and one raw `INSERT` (`SavingsSchedularInterestPoster:165`, which writes the DDL defaults) |
| `acc_gl_account` | **no stored balance column at all** — searched and found clean, and recorded, because a table searched clean and a table never searched are different states |

**Four related shapes are declared NOT DECLARED, with reasons:**
`m_savings_account_transaction` (out of the graded surface under the NBFI licence gate),
`m_loan_transaction` (a different context with its own comparator),
`m_trial_balance` and `acc_gl_journal_entry_annual_summary` (**both measured at ZERO rows** — a
declaration about behaviour never observed would be reasoning, not measurement).

---

## What I observed from the live oracle (with instants)

Fire clock at first probe **`2026-08-29T00:07:51Z`**; database clock agreed to the second.
`actuator/health` → `{"status":"UP","groups":["liveness","readiness"]}`.

### 1. The I-5 pin, re-measured at `2026-08-29T00:08:40Z` [`out/T429-S01-i5-pin.txt`]

```
 total | modified | untouched | null_lm |        oldest_created         |        newest_created
   109 |       91 |        18 |       0 | 2026-08-21 06:03:41.494198+00 | 2026-08-28 16:01:00.117772+00

               cohort               | total | modified | untouched
 a: id <= 75 (pre-T388)             |    71 |       71 |         0
 b: id 76-95 (T388)                 |    20 |       20 |         0
 c: id 96-113 (scheduled job, T391) |    18 |        0 |        18
```

**The numbers did NOT move since T391 measured them, and that is itself the finding.** Job 9's next
run is `2026-08-29 16:01:00`; it has not fired since T391. So `91 | 109` is now measured at two
independent instants by two tasks, and the column's **discrimination is stable**, not a transient.

### 2. Attribution to job 9 — and the limit on it [`out/T429-S05-attribution.txt`, `out/T429-S04-jobs.txt`]

- the 91 modified rows carry `last_modified_on_utc` in **`[16:01:00.033938, 16:01:00.039824]`**,
  **one** distinct modifier (app user 2, `system`);
- **job 9 ran `2026-08-28 16:01:00.003 → .048`**, `job_run_history` id **12720**, `trigger_type cron`,
  `status success` — the window **strictly contains** the modification window;
- the 18 untouched rows were created `16:01:00.100 … .117`, **after job 9 finished**;
- `is_running_balance_calculated` is **TRUE on exactly the 91 and FALSE on exactly the 18** —
  one-to-one, which turns an interval into an identification.

**THE LIMIT, STATED AND NOT PROMOTED.** Two jobs bracket the window: job 9 and job 17 `Recalculate
Interest For Loans` (`.032 → .048`). The interval **alone does not separate them**. What separates
them is the **source enumeration**: exactly two `UPDATE acc_gl_journal_entry` statements exist in the
whole pinned tree outside tests and both are in `JournalEntryRunningBalanceUpdateServiceImpl`; the
only other write path is the JPA entity, whose two `@Setter`s are the reversal pair, against which
this tenant records 3 reversals and 91 modified rows. `job_run_history` records *when* a job ran, not
*which rows it wrote*, and there is no foreign key from an entry to a job.

### 3. THE DECISIVE WIRE OBSERVATION — the boundary serves a balance of ZERO for an account that is not empty

Three `GET`s, all HTTP 200, all with an `Idempotency-Key`:

| capture | request | running-balance fields in the body |
|---|---|---|
| `T429-G01-je78-default` | `GET /journalentries/78` | **NONE** |
| `T429-G02-je78-runningbalance` | `GET /journalentries/78?runningBalance=true` | all three |
| `T429-G03-je96-runningbalance` | `GET /journalentries/96?runningBalance=true` | all three |

`T429-G03` is the one that matters. Entry 96 is transaction `L32`, a **`12356.34` DEBIT on ASSET
account 41**. The oracle returns:

```
"organizationRunningBalance":0.000000,"officeRunningBalance":0.000000,"runningBalanceComputed":false
```

**The derived running balance at that entry is `72866.39`** — `24000.00 + 20195.38 + 16314.67 +
12356.34`, the four entries on account 41 in `entry_date, id` order, all DEBITs on an ASSET account,
re-derived from `out/T429-S02-columns.txt` §S02.4 rather than from any stored column.
**THE ORACLE IS SERVING ZERO FOR AN ACCOUNT HOLDING 72,866.39**, and will until job 9 next runs.

This is the **opposite polarity** to A2-29's finding and completes it. A2-29 observed
`runningBalanceComputed: true` on rows wrong by MNT 2,000,000.00 — a *stale true*. T429 observes a
*stale false* serving a wrong number. **The flag is not a correctness signal in either direction**,
and the columns are not a cache in either direction.

It also **corrects a closing sentence of A2-29's own gate block**: *"The tenant now has every entry
flagged `calculated = true`."* True when written; false since `2026-08-28 16:01`, when the scheduler
wrote 18 accrual entries **after** job 9 had finished. `P-69`, another site.

### 4. The two mutable columns, which are NOT in the carve-out

`JournalEntry.java` carries exactly **two** `@Setter` annotations in the whole class:
`reversalJournalEntry` (`:58`) and `reversed` (`:78`). So of 31 columns on a posted row, **two** are
ORM-mutable — both by a **reversal**, both **through the command bus** — and **three** are mutable
only by the out-of-band batch `UPDATE`. That is the difference between a correction and a
denormalisation, and it is why `reversed` and `reversal_id` are `GRADED_GAP` (uncovered) and not
`ORACLE_DERIVED` (exempt).

### 5. Sibling tables, measured

`m_trial_balance` **0 rows** (job 30 active, ran `2026-08-28 16:01:00.003`).
`acc_gl_journal_entry_annual_summary` **0 rows** (job 40 `is_active = FALSE`, last ran 2026-08-18).
`m_portfolio_command_source` **379 rows**, of which **7** are `UPDATERUNNINGBALANCE / JOURNALENTRY` —
so the hand-fired route to the same write exists and has been used; the nightly one leaves no command
row at all.

---

## Fineract source citations

All at pinned `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

| claim | file | lines |
|---|---|---|
| **the write** — `UPDATE acc_gl_journal_entry SET is_running_balance_calculated=?, organization_running_balance=?, office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?` | `fineract-provider/…/journalentry/service/JournalEntryRunningBalanceUpdateServiceImpl.java` | **163-165**, batched at **181** |
| the office-scoped write, `office_running_balance` **alone** | same | **211**, batched at **217** |
| the work queue — `MIN(entry_date) WHERE is_running_balance_calculated=false` | same | **72-73** (and **93-94** for the office form) |
| the recompute **seeds from its own prior output** | same | **110-116**, **134-141**, **194-200** |
| the sign rule joins `acc_gl_account.classification_enum` at recompute time | same | **220-250** |
| tasklet → service | `fineract-provider/…/accounting/jobs/accountrunningbalanceupdate/AccountRunningBalanceUpdateTasklet.java` | `execute()` calls `updateRunningBalance()` |
| Spring Batch step/job, `JobName.ACCOUNTING_RUNNING_BALANCE_UPDATE` | `…/AccountRunningBalanceUpdateConfig.java` | whole file |
| the hand-fired command route | `fineract-provider/…/journalentry/handler/UpdateRunningBalanceCommandHandler.java` | whole file |
| **the JPA entity does not map the three columns**, and carries exactly two `@Setter`s | `fineract-accounting/…/journalentry/domain/JournalEntry.java` | `@Entity` **38**, `@Table` **40**, setters **58** and **78**; no `@Column` for any balance |
| the fields are projected only on opt-in | `fineract-provider/…/journalentry/service/JournalEntryReadPlatformServiceImpl.java` | **104-107**, **178-181** (`associationParametersData.isRunningBalanceRequired()`) |
| the DTO fields | `fineract-accounting/…/journalentry/data/JournalEntryData.java` | **73**, **75**, **77** |
| the only raw `INSERT` into the table, writing the DDL defaults | `fineract-savings/…/service/SavingsSchedularInterestPoster.java` | **165** |

---

## What reads this declaration, and when

**It is reached, and here is the chain, each link checkable:**

1. **`storeRootNonVectorFiles`** (`loanschedule/conformance/census.go`) now names
   `oracle-derived-columns.json`. A store-root `.json` that is neither on that list nor loaded as a
   vector **REFUSES THE STORE**. So the file cannot sit there unaccounted for.
2. **`LoadOracleDerivedRegistry`** is called **by name** from `Run`
   (`loanschedule/conformance/grade.go`), beside `LoadPin` and `LoadCapabilityRegistry`. A load
   failure or a validation failure is **FATAL** — `Summary.Fatal`, exit 2, no verdict. So being on
   the list without being read is not a state that can exist either.
3. **`Summary.OracleDerivedLines()`** is rendered by `report.go` on **every run, pass or fail** — and
   as a **NAMED ABSENCE** if no declaration is loaded, because "there is no carve-out" and "nobody
   printed the carve-out" must be distinguishable.
4. **The counts are pinned in Go**, both directions, following T360's `DivergencePinCount` precedent:
   `OracleDerivedColumnPin 3`, `ProvenanceColumnPin 7`, `GradedColumnPin 3`, `GradedGapColumnPin 18`,
   `DeclaredColumnPin 31`, `GradedCellPin 14`, `MoneyAndStructureColumnCount 19`. Widening the
   carve-out is a **source edit a reviewer sees**, never a JSON edit nobody does.

**Pinned in Go and NOT in `.softhouse/conformance.sh`.** Two reasons, the second better than the
first: that file is held by `T417` this fire; and a carve-out's population belongs beside the code
that reads it. **A follow-up is filed** to add the four new pins to the shell exemption census, the
same shape T360's patch under `.softhouse/capture/t360-divergence-class/` already takes.

### The three risks, and which mechanism closes each

| risk | mechanism | drive |
|---|---|---|
| (1) a parity run **reds** on a column the port is right to refuse | the declaration exists, loads fatally, prints every run | `TestTheBlockIsRenderedEvenWithNoDeclaration` |
| (2) somebody **grades a running balance to make a bar green** | **disjointness against the MEASURED comparator vocabulary.** `CellFields()` runs a probe through the real comparator; the loader refuses at exit 2 if a cell it emits is a spelling the declaration forbids | `TestGradingAnOracleDerivedColumnRefusesTheRun` |
| (3) the columns are **quietly never compared** | store-root census + fatal load + printed block + pinned counts | `TestPopulationPinsRefuseInBothDirections`, `TestEveryDeclaredTableClassifiesEveryColumnItClaims` |

**Why (2)'s guard cannot be vacuous:** both sides are measured. The vocabulary comes from running the
comparator, not from a list; the declaration comes from the JSON. **Set equality is asserted in BOTH
directions** — a cell that *disappears* from the comparator goes red (the control-that-cannot-fail
direction, `TestDroppingAMeasuredCellFromTheDeclarationRefuses`) and a cell that *appears* goes red
until somebody classifies it (`TestDeclaringACellTheComparatorDoesNotEmitRefuses`). A running-balance
cell added to the comparator would land in the second.

### A2-29's positive rule on capture, built at last

`A2-29 §6.1` said: *"A ledger parity vector must not set `runningBalance=true` or
`fetchRunningBalance=true`."* From A2-29 until now that rule lived in the gate register and in one
vector's `_note` — **an assertion by the author that the author had obeyed it**. It is now a scan of
the **capture bytes**: `Admit` refuses a vector whose cited artefact contains
`organizationRunningBalance`, `officeRunningBalance` or `runningBalanceComputed`, because those fields
appear in an oracle response **if and only if** the parameter was set — measured **in both
directions** by the `G01`/`G02` pair on the same entry, and asserted in the drive so the fixture
cannot silently stop demonstrating it.

**Coverage is printed, not implied:** `cited artefacts scanned CLEAN 34 FORBIDDEN 0 UNREADABLE 0` on
this run. The three outcomes are distinct types and **UNREADABLE is never folded into CLEAN** — a
check that did not run counted as one that passed is the shape every vacuous guard in this program
has had (`P-35`).

### HONESTLY STATED — two surfaces were ALREADY closed and this task did not close them

`expect.legs[].excluded_fields` was already closed to the single member `gl_account_type`
(`admit.go:112-120`), and `graded_against[].divergent_cells` was already checked against
`IsCellField`. **A vector naming a running-balance cell in either was already inadmissible before
T429.** The new arms are the three in the table above plus the capture rule; claiming the other two
would be claiming credit for default-deny somebody else wrote.

---

## Money columns — confirmed still graded

**NOTHING IN THIS TASK MOVED A MONEY OR STRUCTURE COLUMN OUT OF GRADING, AND NOTHING LATER CAN DO IT
BY EDITING JSON.**

`moneyAndStructureColumns` in `ledger/conformance/oraclederived.go` is a **hard-coded, in-source** set
of **19** columns — `amount`, `account_id`, `type_enum`, `currency_code`, `office_id`,
`transaction_id`, `loan_transaction_id`, `savings_transaction_id`, `client_transaction_id`,
`share_transaction_id`, `payment_details_id`, `entity_type_enum`, `entity_id`, `reversed`,
`reversal_id`, `manual_entry`, `entry_date`, `transaction_date`, `submitted_on_date`.

**Declaring any of them `ORACLE_DERIVED` or `PROVENANCE` refuses the run at exit 2, and the JSON
cannot reach that rule.** Each may be `GRADED` (a cell compares it) or a **printed** `GRADED_GAP` (no
cell yet — said as a coverage gap). It may never be exempt.

`TestMoneyColumnCannotBeDeclaredOracleDerived` drives it through the JSON — the surface a later author
would actually edit — across **six** sub-cases (`amount`, `account_id`, `type_enum`, `transaction_id`,
`reversed`, each as ORACLE_DERIVED and/or PROVENANCE) and asserts the refusal **names the reason**.
`TestCommittedDeclarationLoadsAndClassifiesEveryMeasuredCell` is the paired control: it asserts
`amount` is still `GRADED` by `legs[].amount_minor`, and that every one of the 14 cells the comparator
emits is classified. **A control that cannot fail and one that refuses everything are the same defect
(`P-98`), so both halves are asserted in the same file.**

**And the bar confirms it end to end**, unchanged from main: `ledger cells compared 268 graded, of
which 63 are MONEY cells in int64 minor units`; `LEDGER money cells compared = 63 == pinned 63`; 15
registered wrong ledger implementations all still KILLED, including `ledger-wrong-code-ignored` at
`ledger parity FAIL 10`.

---

## Bar figures

`bash .softhouse/conformance.sh` on the finished **committed** tree, worktree
`/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae042a536ad80fee1`, transcript `/tmp/t429-bar-2.txt`.
**Scratch stayed in `/tmp`; no nested checkout was created inside the repository.**

| | |
|---|---|
| **EXIT CODE** | **0** |
| **`probe = ` line PRINTED AT ALL?** | **YES — PRESENT, exactly ×1** (`grep -c` = 1) |
| **its value** | **`up`** — `reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up` |
| **`VERDICT:`** | **`VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.`** |
| dead-path census | `corpus=1456 deadFiles=75 **deadOccurrences=108** resolving=1387 indeterminate=114 prose=380` |
| dead-path frontier | **`frontier 11, pinned at 11`** — `frontier == pinned (all 11 rows, by path)` |
| ledger | `parity PASS 10 FAIL 0` · `oracle-refusal PASS 6 FAIL 0` · `inadmissible 0` · `harness errors 0` · `cells 268 graded / 63 MONEY` |
| ledger exemption census | declared exemptions `0 == 0` · parity `10 == 10` · oracle-refusal `6 == 6` · money cells `63 == 63` |
| divergence | `PASS 1 FAIL 0 (pinned 1)` |
| namespace census | `dirs=204 prefixed=182 unprefixed=22 collidingIds=2 declared=2 unclaimed=2 shortfallIds=0` — PASS |
| guard-cost census | 15 guards timed, 72 s wall, ceiling breaches 0, unbudgeted guards 0 |

**Every figure matches the baseline the brief recorded for `main` at fire start** (EXIT 0, probe
PRESENT ×1 `up`, `VERDICT: PASS` 46 / 7884, `deadOccurrences 108`, frontier `11 == 11`).

**ONE RED WAS DRIVEN AND FIXED, and it is recorded rather than quietly repaired.** The first bar run on
the committed tree was **EXIT 2** — `a HARD guard failed`, and **the `probe = ` line was NOT PRINTED**,
because `guard_gofmt` refused `oraclederived.go` before the probe ran. `gofmt -w` fixed it; the second
run is the one tabulated. That is the four-exit-2-paths-before-the-probe case the brief warns about,
observed rather than theorised. [`/tmp/t429-bar-1.txt`, kept out of the repository.]

**`go build ./...` clean; `go test ./...` clean** (`ledger`, `ledger/conformance`, `loanschedule`,
`loanschedule/conformance` all `ok`). **12 drives added, all pass.**

**One pre-existing condition, NOT introduced by this task and NOT fixed by it:**
`gofmt -l ./internal/` also lists `internal/apps/loanschedule/contract/contract.go` on this
toolchain (go1.23.4), and the bar is green with it, so `guard_gofmt`'s population is narrower than
`./internal/...`. Left alone: it is another task's file and another task's finding. Filed below.

---

## Unverified

- **[UNVERIFIED] That job 9 and no other job wrote the 91 rows, from the JOB SIDE.** The attribution
  rests on a **source enumeration** (two `UPDATE` statements, both in one service) plus an interval
  that job 17 also satisfies. `job_run_history` records when a job ran, not which rows it wrote, and
  no foreign key exists. I did not fire job 9 to confirm — that would be a write to the oracle.
- **[UNVERIFIED] That the three columns behave the same way in a multi-office tenant.** This tenant
  has one office. A2-29 recorded the same limit.
- **[UNVERIFIED] Anything about `m_trial_balance` or `acc_gl_journal_entry_annual_summary` beyond
  their emptiness.** Both are **0 rows**; I declare their SHAPE and refuse to declare their columns.
- **[UNVERIFIED] That the 125 `_derived` columns outside `acc_gl_journal_entry` are all
  denormalisations of the same kind.** I measured the NAMES and the COUNT. I did not open their write
  paths — that is a loan-context and savings-context question with its own vectors.
- **[UNVERIFIED] That the capture rule would have caught any historical vector.** It scans what a
  vector CITES; on today's corpus it scanned 34 artefacts and found 0. That is a fact about the 15
  vectors in the store, not a proof about captures nobody promoted.
- **[UNVERIFIED] What `guard_gofmt`'s exact file population is.** Observed only that it flagged
  `oraclederived.go` and does not flag `contract.go`.

---

## Follow-ups

1. **`G-22` needs a decision** — the `I-5` correction and the proposed `§4.4a`. Both amend a ratified
   DEC-2, so an agent may not apply them. Full text and evidence:
   `docs/adr/DEC-2-PROPOSED-REVISION-T429-oracle-derived-columns.md`.
2. **The four new pins are in Go, not in the shell exemption census.** Add
   `oracle-derived columns`, `provenance`, `graded`, `graded-gap` to
   `.softhouse/conformance.sh`'s census when that file is free (T417 holds it this fire). The same
   patch shape T360 left under `.softhouse/capture/t360-divergence-class/`.
3. **`G-21` should be annotated with this third measurement.** The I-5 premise has now moved from
   `60/60` → `60/91` → `91/109`, at three instants by three tasks, and it will move again the next
   time job 9 runs. **The driver's own remedy in G-21 applies verbatim: prefer DELETING a live-oracle
   cardinal from a ratified document to refreshing it.**
4. **A2-29's gate block carries a stale closing sentence** — *"every entry flagged `calculated =
   true`"* — false since `2026-08-28 16:01`. `P-69`. Correcting it is a `gates.md` edit, deliberately
   not made here to keep this task's `gates.md` footprint to one appended block (T417 is concurrent).
5. **Declare the savings shape when a savings vector is promoted.**
   `m_savings_account_transaction.running_balance_derived` is the identical defect one context over,
   and the declaration already names it as deferred with the reason.
6. **`internal/apps/loanschedule/contract/contract.go` is not gofmt-clean** on go1.23.4 and the bar
   does not notice. Either widen `guard_gofmt`'s population or format the file — but decide it, since
   a formatting guard whose population is narrower than the module is a guard with an unstated limit.
7. **The shadow-parity diff must read this file.** When a row-level diff of the two systems is built,
   its column exclusions must be **derived from `oracle-derived-columns.json`**, not retyped into a
   diff script. A second copy of this list is a second place for it to be wrong.
