# DEC-2 — PROPOSED REVISION (NOT RATIFIED, NOT APPLIED) — the ORACLE-DERIVED column declaration

> **⚠ THIS IS A PROPOSAL. `docs/adr/DEC-2-gl-accounting-adapter.md` IS RATIFIED AND WAS NOT TOUCHED
> BY `T429`.** Amending a ratified DEC-n is a gate, not an edit. This file carries the proposed text
> and its evidence so that the driver or Buyan can ratify or reject it as a unit; it is raised under
> **`G-22`** in `.softhouse/gates.md`.
>
> **Author:** `T429`, branch `softhouse/T429-oracle-derived-columns`, local fire `20260829-080002`.
> **Oracle:** live, `{"status":"UP"}`, PostgreSQL `18.3`, database `fineract_gerege`, tenant
> `gerege`, Fineract pinned `426a23544e8426a38ae43ae404670a0a7e85b9eb`
> [`git -C /Users/buv/fineract rev-parse HEAD`, verified before a single line number was read].
> **Every observation instant is recorded.** Evidence:
> `.softhouse/capture/t429-oracle-derived-columns/`.

---

## 0. What this proposes, in four sentences

1. **DEC-2's `I-5` row asserts a premise that is now measurably FALSE**, and the falsehood is the
   load-bearing clause, not a stale cardinal. It says *"60 of the 60 rows … carry
   `last_modified_on_utc > created_on_utc` … so the column **discriminates nothing**"*. Measured
   `2026-08-29T00:08:40Z`: **91 of 109**, with **18 rows carrying equality**. The column
   **discriminates**. Proposed text in §3.
2. **A new normative section is proposed** naming the three `acc_gl_journal_entry` columns the
   reference oracle writes by its own denormalisation, declaring that a conforming port **must not**
   produce them, and stating that a mismatch on them **is the port being right**. Text in §4.
3. **The declaration is already built and already enforced** — `.softhouse/vectors/oracle-derived-columns.json`,
   loaded by `nexus/internal/apps/ledger/conformance/oraclederived.go`, printed on every run,
   pinned by count, with twelve drives. That part needed no gate and was not held for one. §5.
4. **Nothing here narrows the graded domain**, and that is deliberate: `G-12`'s measurement
   explicitly **rejected** option (c) on the ground that narrowing the graded domain is a hard
   `user` gate. §6 sets out why this proposal is compatible with that rejection rather than a
   re-litigation of it.

---

## 1. The divergence, stated plainly

`CLAUDE.md`, non-negotiable:

> **The ledger is double-entry and append-only. Balances are derived, never written.**

The reference oracle does the opposite. `acc_gl_journal_entry` carries three columns that are a
running total **stored on the posted row**, and scheduled job 9 `Update Accounting Running Balances`
**rewrites them in place**:

```
UPDATE acc_gl_journal_entry
   SET is_running_balance_calculated=?, organization_running_balance=?,
       office_running_balance=?, last_modified_by=?, last_modified_on_utc=?
 WHERE  id=?
```

[VERIFIED: `fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/JournalEntryRunningBalanceUpdateServiceImpl.java:163-165`,
pinned `426a23544`. The batch is executed at `:181` via `jdbcTemplate.batchUpdate`. A second,
office-scoped `UPDATE` at `:211` writes `office_running_balance` **alone**.]

The path from the scheduler to that statement, end to end:

| step | source | pinned citation |
|---|---|---|
| job row | tenant DB `job` id **9**, `Update Accounting Running Balances`, cron `0 1 0 1/1 * ? *`, `is_active = t` | measured, `T429-S04-jobs` |
| Spring Batch step/job beans | `AccountRunningBalanceUpdateConfig.java` | `JobName.ACCOUNTING_RUNNING_BALANCE_UPDATE` |
| tasklet | `AccountRunningBalanceUpdateTasklet.java` | `execute()` calls `journalEntryRunningBalanceUpdateService.updateRunningBalance()` |
| the write | `JournalEntryRunningBalanceUpdateServiceImpl.java:71-79, 106-189, 191-217` | the two raw `UPDATE`s above |

**It does not go through the command bus.** A tasklet is not a command; `m_portfolio_command_source`
holds no row for it. (The *hand-fired* route does exist — `POST /journalentries?command=updateRunningBalance`,
`UpdateRunningBalanceCommandHandler` — and this tenant carries **7** such command rows, action
`UPDATERUNNINGBALANCE`, entity `JOURNALENTRY`. Both routes reach the same service and write the same
columns.)

**And the oracle's own domain model does not know these columns exist.** `JournalEntry.java`
(`@Entity`, `@Table(name = "acc_gl_journal_entry")`) declares no field for either balance or the
flag, and carries exactly **two** `@Setter` annotations in the whole class — `reversalJournalEntry`
(`:58`) and `reversed` (`:78`). So on a posted row:

- **two** columns are mutable through the ORM, both by a **reversal**, both through the command bus;
- **three** are mutable only by a raw batch `UPDATE` from a service outside the domain model;
- **the rest are written once, at insert.**

That is the whole shape of the divergence, and it is why the three are separable from the rest by
something better than judgement.

---

## 2. What this means for a Go port, and why the mismatch is the port being RIGHT

A port that honours the non-negotiable **has no field to put the number in**. Checked, not assumed:
`PostedEntry` and `PostedLeg` in `nexus/internal/apps/ledger/conformance/impl.go:61-96` carry
`TransactionID`, `RequestedAmountMinor`, `Legs`, `TotalDebitsMinor`, `TotalCreditsMinor`, and per
leg `AccountID`, `AccountCode`, `Side`, `AmountMinor`, `SlotName`. **There is no balance member of
any kind, at any level.** The port derives; it does not store.

So the port can never match those three columns. Before `T429` nothing said that was correct, and
three bad outcomes were available:

1. a future parity run **reds** on a column the port is correct to refuse;
2. somebody **"fixes" the port to write balances** — violating a non-negotiable to make a bar go
   green;
3. the columns are **quietly never compared** — an *undeclared ungraded region*, which is how a port
   silently stops being graded.

§5 records which mechanism closes each.

---

## 3. PROPOSED CORRECTION to DEC-2 `§4.4`, invariant `I-5`

**Two sites carry the false clause** — `DEC-2-gl-accounting-adapter.md:1061` (the `I-5` row of the
invariant table) and `:3004` (open item 13). Both assert, present tense:

> **60 of the 60 rows in `acc_gl_journal_entry` carry `last_modified_on_utc > created_on_utc`**,
> clustered at two batch instants … so the column **discriminates nothing**

**The conclusion is drawn from UNIVERSALITY.** The column is dismissed *because every row carries
it*. That premise is now false, and this is the **second** time it has moved: `T391` measured
91 of 109 on 2026-08-29 and filed it; `T429` re-measures it independently at a second instant and
gets the same figure, so the observation is stable rather than a transient.

**MEASURED `2026-08-29T00:08:40Z`** (live, read-only `SELECT`, `T429-S01-i5-pin`):

```
 total | modified | untouched | null_lm |        oldest_created         |        newest_created
   109 |       91 |        18 |       0 | 2026-08-21 06:03:41.494198+00 | 2026-08-28 16:01:00.117772+00

               cohort               | total | modified | untouched
 a: id <= 75 (pre-T388)             |    71 |       71 |         0
 b: id 76-95 (T388)                 |    20 |       20 |         0
 c: id 96-113 (scheduled job, T391) |    18 |        0 |        18
```

**The column DISCRIMINATES**, and what it discriminates is exactly *"job 9 has recomputed this row"*
from *"job 9 has not reached it yet"*:

- the 91 modified rows carry `last_modified_on_utc` in `[16:01:00.033938, 16:01:00.039824]` on
  2026-08-28, one distinct modifier (app user 2, `system`);
- **job 9's last run was `2026-08-28 16:01:00.003 → .048`** (`job_run_history` id **12720**,
  `trigger_type cron`, `status success`) — the window **strictly contains** the modification window;
- the 18 untouched rows were created at `16:01:00.100 … .117` — **after job 9 finished**;
- and `is_running_balance_calculated` is **TRUE on exactly the 91 and FALSE on exactly the 18**. The
  match is one-to-one, which is what turns an interval argument into an identification.

**Attribution, with its limit stated.** Two jobs' windows contain the modification window: job 9
(`.003 → .048`) and job 17 `Recalculate Interest For Loans` (`.032 → .048`). The interval alone does
not separate them. What separates them is the **source**: across the whole pinned checkout, excluding
tests, there are exactly **two** `UPDATE acc_gl_journal_entry` statements and **both are in
`JournalEntryRunningBalanceUpdateServiceImpl`**; the only other write path to the table is the JPA
entity, whose two setters are the reversal pair, and this tenant has 3 reversals against 91 modified
rows. [LIMIT, stated rather than promoted: `job_run_history` records *when* a job ran, not *which
rows it wrote*, and there is no foreign key from a journal entry to a job. The claim rests on the
source enumeration; the interval merely agrees with it.]

### 3.1 Proposed replacement clause

> **the timestamps are NOT what shows it, and the reason has itself been corrected twice.**
> Revisions 6–8 argued that `last_modified_on_utc` discriminates nothing *because it is universal*
> — *"60 of the 60 rows"*. **That premise is false and was already false when it was last
> restated.** MEASURED `2026-08-29T00:08:40Z` against the live oracle (Fineract `426a23544`,
> PostgreSQL `fineract_gerege`, tenant `gerege`): **91 of 109** rows carry
> `last_modified_on_utc > created_on_utc` and **18 carry equality**. The column **does**
> discriminate — it separates the rows scheduled job 9 `Update Accounting Running Balances` has
> recomputed from the rows it has not reached, one-to-one with
> `is_running_balance_calculated`. **The conclusion is unchanged and the ground is replaced.**
> `I-5`'s NEVER-MUTATES half stays ungraded on the simpler and stronger reason `T246` already
> gave: **a snapshot never observes a write**, so it cannot separate *"flags and adds"* from
> *"flags and rewrites"* whatever the timestamps say. What the timestamps additionally show —
> and this is new — is that **the oracle DOES mutate posted rows, nightly, outside the command
> bus**, on three columns which `DEC-2 §4.4a` (proposed, §4 below) declares ORACLE-DERIVED.
>
> **`P-69` again, third instance in this document.** The clause was true when written. Nothing
> in the document notices when a live-oracle count moves underneath it, and this one moves
> **every night job 9 runs**. Any future restatement should cite the declaration, which is
> re-measured by a program, rather than a number typed into prose.

---

## 4. PROPOSED NEW SECTION — DEC-2 §4.4a, "ORACLE-DERIVED COLUMNS"

> ### §4.4a — ORACLE-DERIVED COLUMNS: where a conforming port is RIGHT not to match the oracle
>
> Three columns of `acc_gl_journal_entry` are written by the reference oracle's own
> denormalisation and **must not** be produced by a conforming port. A difference on them is
> **not** a conformance failure; it is the port honouring `CLAUDE.md`'s append-only
> non-negotiable.
>
> | column | wire field | written by |
> |---|---|---|
> | `organization_running_balance` | `organizationRunningBalance` | job 9 → `JournalEntryRunningBalanceUpdateServiceImpl:163-181` |
> | `office_running_balance` | `officeRunningBalance` | job 9 → `:163-181` and `:211-217` |
> | `is_running_balance_calculated` | `runningBalanceComputed` | job 9 → `:163-181`; also the job's own work queue, `:72-73` |
>
> **A CONFORMING PORT:**
>
> 1. **derives** every balance from the append-only entries and **never reads** these columns —
>    not to serve a response, not to seed an incremental computation, not in a report predicate
>    (this is `G-12`'s recommendation (a), taken without qualification);
> 2. **keeps the columns in the adopted schema** with Fineract's own DDL defaults
>    (`NOT NULL DEFAULT 0.000000` / `DEFAULT false`) so that a Fineract process pointed at the
>    same database still starts, and **never recomputes them** (`G-12`'s narrowed (b));
> 3. **ships no equivalent of `ACCOUNTING_RUNNING_BALANCE_UPDATE`.**
>
> **A row-level diff of the two systems will differ on these three columns on every entry, for
> the whole shadow-parity window.** Whoever runs that diff must exclude them explicitly, and
> `.softhouse/vectors/oracle-derived-columns.json` is the artefact that exclusion must be taken
> from — not a list retyped into a diff script.
>
> **THE BOUNDARY, and it is not negotiable by this section.** Leg amounts, GL account ids and
> codes, debit/credit sense and transaction linkage are **GRADED, ALWAYS**. Nineteen columns of
> `acc_gl_journal_entry` are money or structure and are protected in source
> (`moneyAndStructureColumns`, `nexus/internal/apps/ledger/conformance/oraclederived.go`):
> declaring one of them ORACLE-DERIVED **refuses the run at exit 2**, and no edit to the JSON can
> reach that rule. A money or structure column may be **GRADED** (a cell compares it) or a
> printed **GRADED_GAP** (no cell yet — a coverage gap, said as one). It may never be exempt.
>
> **NOT A FRESHNESS SIGNAL.** `runningBalanceComputed: true` was observed by `A2-29` on rows wrong
> by MNT 2,000,000.00. `T429` observed the other polarity: on `2026-08-29T00:08Z`, entry 96
> (transaction `L32`, a `12356.34` DEBIT on ASSET account 41, derived running balance
> `72866.39`) is served by `GET /journalentries/96?runningBalance=true` as
> `"organizationRunningBalance":0.000000, "runningBalanceComputed":false`. **The oracle is serving
> a balance of ZERO for an account that is not empty**, and will until job 9 next runs. Neither
> the value nor the flag is a correctness signal, in either direction.

---

## 5. What is already built, enforced and printed — and what is not

**None of §5 required a gate, and none of it was held for one.** It classifies columns; it does not
amend a ratified document.

| the risk | the mechanism | where |
|---|---|---|
| (1) a parity run reds on a column the port is right to refuse | the declaration exists, is loaded by name, and is **printed on every run**, including as a NAMED ABSENCE if it fails to load | `oraclederived.go` → `Summary.OracleDerivedLines`, called from `loanschedule/conformance/report.go` |
| (2) somebody grades a running balance to make a bar green | **disjointness against the MEASURED comparator vocabulary.** `CellFields()` runs a probe through the real comparator; the loader refuses if any cell it emits is a spelling the declaration forbids | `oraclederived.go` `validate`, drive `TestGradingAnOracleDerivedColumnRefusesTheRun` |
| (3) the columns are quietly never compared | store-root census + pinned counts. A store-root `.json` not on `storeRootNonVectorFiles` **refuses the store**; the counts are pinned in Go in both directions | `loanschedule/conformance/census.go`, `OracleDerivedColumnPin` &c. |
| a money column is exempted | the protected set is **hard-coded in Go**; the JSON cannot override it | `moneyAndStructureColumns`, drive `TestMoneyColumnCannotBeDeclaredOracleDerived` (6 sub-cases) |
| a vector is captured from the accelerator | **A2-29 §6.1 made mechanical**: the loader scans the cited capture BYTES for `organizationRunningBalance` / `officeRunningBalance` / `runningBalanceComputed` and refuses the vector as INADMISSIBLE | `CaptureRuleReasons`, wired into `Admit`; drive `TestVectorCapturedWithRunningBalanceParameterIsRefused` |
| the check silently stops running | the three scan outcomes are distinct and the **UNREADABLE count is printed**, never folded into CLEAN | `CaptureScanOutcome`, drive `TestUnreadableCitationIsReportedAndNotCountedClean` |

**HONESTLY STATED, because a claim of enforcement is worth exactly its weakest arm:**

- **Two of the surfaces were ALREADY closed before `T429` and this task did not close them.**
  `expect.legs[].excluded_fields` is closed to the single member `gl_account_type` by
  `admit.go:112-120`, and `graded_against[].divergent_cells` is checked against `IsCellField`. A
  vector naming a running-balance cell in either was already inadmissible. The new arms are the
  three in the table that were not.
- **The capture rule is not retroactive evidence.** It scans what a vector CITES. Measured on the
  committed corpus: **34 artefacts scanned, 0 forbidden, 0 unreadable.** That is a fact about the 15
  ledger vectors in the store today, not a proof about captures nobody promoted.
- **This declaration covers `acc_gl_journal_entry` and no other table.** Four related shapes were
  found and are recorded, with reasons, in the declaration itself: `m_savings_account_transaction`
  (out of the graded surface under the NBFI licence gate), `m_loan_transaction` (a different
  context), `m_trial_balance` and `acc_gl_journal_entry_annual_summary` (both measured at **zero
  rows**). `acc_gl_account` was searched and found to carry **no** stored balance column at all.

---

## 6. Why this is NOT `G-12` option (c), which was rejected

`G-12`'s measurement block records: *"Reject (c), and do not take it. Treating exposing cells as
outside the graded domain narrows the graded domain, which is a hard `user` gate — but more to the
point it is not needed … The right instrument is a positive rule on capture, not a negative
carve-out on grading."*

**That rejection is upheld here, not worked around.**

- **The graded domain is not narrowed.** Nothing that was compared before is compared less. The
  fourteen cells the comparator emits are the fourteen it emitted before, and the declaration
  asserts **set equality** with them in both directions — so this task could not have narrowed the
  domain without going red on its own check.
- **What it adds is the positive rule on capture that `A2-29` asked for and nobody built.** From
  `A2-29` to `T429` that rule lived in the gate register and in one vector's `_note`, where it was
  an assertion by the author that the author had obeyed it. It is now a scan of the capture bytes.
- **The declaration is a RECORD of a region that was never in the graded domain, made
  machine-readable and printed.** `A2-29` itself named the cost that record pays for: *"Whoever runs
  the parity diff must exclude those columns explicitly, and that exclusion is itself a narrowing
  that has to be written down."* This is that writing-down.

---

## 7. What `T429` did NOT do

- **Did not touch `docs/adr/DEC-2-gl-accounting-adapter.md`.** It is ratified.
- **Did not narrow the graded domain**, and could not have done so without failing its own drives.
- **Did not close `G-12`.** `G-12` remains OPEN; this proposal restates its recommendation and
  builds the instrument it asked for, which is not the same as the driver deciding it.
- **Did not write to the reference oracle.** Every SQL statement went through a rig that refuses a
  file containing a write keyword before `psql` is invoked; every HTTP exchange was a `GET` through
  a tool with no method argument.
- **Did not re-decide any ratified tenant parameter**, and did not touch `.softhouse/conformance.sh`
  (held by `T417` this fire; the population pins are in Go instead, following `T360`'s precedent).

---

## 8. Ratification checklist

- [ ] The `I-5` correction in §3.1 is accepted, and both sites (`:1061`, `:3004`) are updated.
- [ ] §4's `§4.4a` is accepted into DEC-2 as a normative section.
- [ ] `G-22` is annotated with the outcome in `.softhouse/gates.md`.
- [ ] If rejected: `.softhouse/vectors/oracle-derived-columns.json` and its loader stay (they
      classify, they do not amend), but this file is marked REJECTED rather than deleted, so the
      record of what was proposed survives the decision.
