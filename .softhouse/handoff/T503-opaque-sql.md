# T503 — OPAQUE-SQL: four unreadable mutating statements made readable

Branch: `softhouse/T503-opaque-sql`. Role: coder. Reviewer: T506.

**Verdict on the assignment: all four sites repaired by making the statement a
string literal. No DEC-2 exemption is required and none is proposed for
ratification.** The exemption I would have proposed for `migrate.go` is written
out in §6 anyway, as the rejected alternative, so a reader can overrule me
without re-deriving it.

**One MAJOR finding, unrelated to the assignment and NOT fixed here: the journal
entry INSERT names two columns that do not exist in the reference-oracle schema
and omits three NOT NULL columns that have no default. It cannot execute. It
could not execute on `main` either. Evidence in §5.** That is exactly the class
of defect the OPAQUE-SQL refusal existed to stop from hiding, and it was found by
doing what the guard asked: writing the statement down where somebody could read
it.

---

## 1. The four sites — what each statement actually executes, and how it was made readable

### 1.1 `nexus/internal/apps/ledger/journalentry_postgres.go:59` — the ledger path

**What it executed on `main`.** `r.db.Exec(r.ctx, sql, args...)`, where `sql`
came from `buildJournalEntryInsert`, which assembled:

```
INSERT INTO acc_gl_journal_entry (account_id, office_id, currency_code, transaction_id,
  reversed, manual_entry, entry_date, type_enum, amount, createdby_id, lastmodifiedby_id,
  created_date, lastmodified_date)
VALUES ($1,…,$11,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),($12,…,$22,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),…
```

one `($n…)` tuple per entry, joined with `strings.Join(rows, ",")`. It is an
**INSERT and only an INSERT**. See §2 for the direct I-4 answer.

**How it was made readable.** The row count moved out of the SQL and into the
ARGUMENTS. The statement is now a single fixed literal written at the call site,
with eleven placeholders whatever the batch size, and Postgres unnests eleven
parallel arrays into rows:

```sql
INSERT INTO acc_gl_journal_entry (account_id, …, created_date, lastmodified_date)
SELECT e.account_id, …, e.entry_date::date, e.type_enum, e.amount::numeric, …,
       CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM unnest($1::bigint[], …, $11::bigint[])
     AS e(account_id, …, lastmodifiedby_id)
```

Properties preserved, checked one at a time:

* **Still ONE statement**, so a transaction's legs still commit or roll back
  together. That was the stated reason for the multi-row form and it survives.
* **Still the same thirteen columns, in the same order.** The diff does not add
  or drop a column. In particular the three running-balance columns
  (`is_running_balance_calculated`, `office_running_balance`,
  `organization_running_balance`) remain absent, as G-12 requires.
* **Still integer minor units.** `MinorUnits.FormatDecimal` renders exact decimal
  text; the text array is cast to `numeric` by Postgres. No `float64`, no
  `big.Float`, nothing lossy, in Go or on the wire. `git diff | grep float` is
  empty (§4).
* **Row order is array order.** `unnest` over N arrays zips them positionally, so
  element *j* of every array is row *j*. Verified structurally by the test
  (§3) and by `PREPARE` against the real schema (§5).

**A second thing had to change, and it is a guard heuristic, not a style
preference.** `ledgerguard`'s `sqlArgOf` skips a leading context argument only
when it is a bare `*ast.Ident` whose lowered name contains `ctx`, or a selector
named `Background`. `r.ctx` is a `*ast.SelectorExpr` whose `Sel.Name` is `"ctx"`,
so it matched neither arm and was itself returned AS the SQL argument — meaning
`r.db.Exec(r.ctx, <perfectly readable literal>, …)` would STILL have been
classed OPAQUE-SQL. A one-line local (`ctx := r.ctx`) puts a bare ident in
argument 0 and the literal is then read. I have said so in a comment beside it
rather than leaving a reader to wonder why the local exists, and filed the
heuristic gap as backlog (§7 B-1). **This is the one place where my code shape
is influenced by the guard's implementation rather than by the invariant, and I
am naming it rather than letting the reviewer find it.**

### 1.2 `nexus/internal/apps/workingcapital/postgres.go:366`

**What it executed.** An upsert of one row per loan into `m_wc_loan_balance`:
`INSERT INTO m_wc_loan_balance (wc_loan_id, <13 columns>) VALUES ($1..$14) ON
CONFLICT (wc_loan_id) DO UPDATE SET <each column> = EXCLUDED.<column>`. It never
touched a journal-entry table.

The statement was opaque because the column list was spliced in from the
`wcBalanceColumns` const. **The guard was not merely refusing on principle — it
was measurably blind.** On `main` its census printed the literal it could see as:

```
CENSUS   DML-classified literal: internal/apps/workingcapital/postgres.go:366:30
  INSERT INTO m_wc_loan_balance (wc_loan_id, ) VALUES ($1,…,$14) ON CONFLICT (wc_loan_id) DO UPDATE S…
```

`(wc_loan_id, )` — thirteen column names it could not see, any one of which
could have been a balance column. After the repair it prints them all:

```
CENSUS   DML-classified literal: internal/apps/workingcapital/postgres.go:379:30
  INSERT INTO m_wc_loan_balance (wc_loan_id, principal, principal_paid, principal_adjustment, fee, fee_paid, penalty, penalty_paid, realize…
```

**How it was made readable.** The thirteen columns are spelled out in the write
path's literal. The const stays and still serves the READ path at :405, where an
opaque SELECT cannot violate I-3 or I-4 by construction. The const now carries a
comment saying the two must move together. I verified the transcription against
the live schema with `PREPARE` rather than by eye (§5.3).

### 1.3 `nexus/internal/platform/postgres/migrate.go:75`

**What it executed.** `CREATE TABLE IF NOT EXISTS schema_migrations (version
bigint PRIMARY KEY, name text NOT NULL, applied_at timestamptz NOT NULL DEFAULT
now())` — the version-tracking table, bound to a `const ddl` one line above the
call.

**How it was made readable.** The literal moved into the call. The guard reads
the ARGUMENT, not the declaration; a const name is an identifier like any other.
The SQL text is byte-identical.

### 1.4 `nexus/internal/platform/postgres/migrate.go:93` — the one that needed a decision

**What it executed.** `tx.Exec(ctx, m.SQL)` — arbitrary migration text carried in
a `string` field of `Migration`. **Nothing in this tree calls `RunMigrations` and
no `Migration` value is constructed anywhere**, so today the answer to "what SQL
does it run" is literally "none, ever". That is not reassurance: a `string` field
is a channel through which any statement, including `DELETE FROM
acc_gl_journal_entry`, could reach Postgres from a caller's variable, a file, or
argv, with nothing in the Go tree showing it. The guard's refusal was correct.

**How it was made readable.** `Migration` now carries the STEP, not the TEXT:

```go
Apply func(ctx context.Context, tx Executor) error
```

A migration is written as a Go function whose body holds its own SQL literal,
which the guard walks and reads in place. This **widens** the guard's reach
rather than narrowing it: a future migration that assembles SQL at run time is
refused at its own call site, where the statement actually is, instead of being
permanently invisible behind a runner that DEC-2 had exempted. `Executor` is the
existing seam in the same package; `pgx.Tx` satisfies it.

Side effect worth one line: a step with a nil `Apply` is now an explicit refusal.
Under `SQL string`, a `Migration{SQL: ""}` executed an empty statement, succeeded,
and **recorded the version as applied** — a silent skip that left the schema
behind the version number. That hole is closed.

**Cost, stated rather than buried:** this runner can no longer be handed
migration text loaded from a `.sql` file or a changelog. Nothing does that today
and Fineract's own schema arrives through Fineract's Liquibase, not through here.
If a text loader is ever genuinely needed it is the DEC-2 conversation in §6,
with a bounded scope — not a silent `string` field reintroduced.

---

## 2. `journalentry_postgres.go:59` — does it violate I-4? **No. Answered directly.**

**The statement is an `INSERT INTO acc_gl_journal_entry`. It contains no UPDATE,
no DELETE, no TRUNCATE, no ON CONFLICT clause, and no WHERE clause of any kind.
It cannot modify or remove a committed row. It does not violate DEC-2 I-4.**

The three independent ways I established that, in increasing order of strength:

1. **By reading `main`.** `buildJournalEntryInsert` was a pure function whose only
   verb was the literal prefix `"INSERT INTO acc_gl_journal_entry "`; the dynamic
   part was `($n,$n,…)` tuples and nothing else. There was no branch that could
   emit a different verb.
2. **By the guard, after the repair.** The statement is now a literal the guard
   analyses, and its own classifier agrees: it appears in the census as a
   DML-classified literal at `journalentry_postgres.go:78:30` and produces **no
   `I4-DML` finding**, because `mutatingVerbRe` (update|delete|truncate|drop|alter)
   and `upsertRe` (`on conflict.*do update`) both miss it. INSERT against this
   table is the lawful write and the guard says so explicitly. This is stronger
   than my reading: the guard did not have to take my word for the verb.
3. **By the reference-oracle Postgres planner.** `PREPARE` of the statement
   against the real `acc_gl_journal_entry` — see §5.

The rest of the repository agrees on append-only: `FindByTransactionID` is the
only other statement in the file and it is a `SELECT`. There is **no** UPDATE or
DELETE against `acc_gl_journal_entry` anywhere in `nexus/`; the guard's whole-tree
census is the evidence, and it now names every DML literal it found.

**The narrower claim I am NOT making.** I have not proved the ledger is
append-only end to end. The guard cannot see triggers, stored procedures or
Fineract's own Liquibase, and its own CANNOT-CATCH block says so. What I have
proved is that this Go module's single write path to `acc_gl_journal_entry` is an
INSERT, and that the claim is now checkable by reading source instead of by
trusting a builder.

---

## 3. Test change — disclosed, because it is a fourth file

The brief scoped me to three files plus this handoff. The diff touches **four**.
The fourth is `nexus/internal/apps/ledger/journalentry_test.go`, and here is the
full reason:

`TestBuildJournalEntryInsertPinsTheSQLShape` asserted the OLD dynamic SQL —
`Count(sql, "VALUES") == 1`, `len(args) == 22` (11 per row), `args[8] ==
"250000.25"`. Changing the statement shape necessarily invalidates every one of
those assertions. Leaving it red would breach the bar's own `go test ./...`
requirement. There was no version of this repair that left that test untouched;
"do not edit outside scope" and "keep the tests green" cannot both hold, and
green tests is the one the bar names.

What the test does now (`TestBuildJournalEntryInsertArgsPinsTheColumnArrays`):
asserts eleven column arrays, asserts **every array has one element per entry**
(misalignment there would write a leg against another leg's account — the
failure mode `unnest` introduces and the one worth pinning), and asserts the
transaction-id, amount, account-id, type-enum and entry-date cells in entry
order.

**What it stopped pinning, stated as a loss and not glossed:** the SQL text
itself. That is deliberate. The statement is now a literal at its single call
site, read directly by a reviewer and by the guard; a test that reconstructed it
would be asserting a copy against itself. The old test existed *because* the
statement existed nowhere a reader could see it. That condition is what this task
removed.

---

## 4. The bar

All commands run from the worktree root. `go` is the pinned toolchain at
`/Users/buv/gerege-nbfi/.softhouse/toolchain/go`.

```
go build ./...   → BUILD OK
go vet ./...     → VET OK
go test ./...    → ok, all 20 packages (ledger 2.019s, ledger/conformance 5.265s,
                   loanschedule/conformance 32.118s, platform/postgres 3.439s, …)
                   0 failures.
gofmt -l nexus   → 4 files, ALL PRE-EXISTING and none of them mine:
                   loanschedule/contract/contract.go, parties/client.go,
                   parties/group.go, parties/legalform.go
```

Non-negotiable greps over my diff, both empty:

```
git diff | grep -E '^\+.*(float32|float64|big\.Float)'                    → none
git diff | grep -iE '^\+.*(ojdbc|oracle\.jdbc|:1521|com\.mysql|mariadb|go-sql-driver)' → none
```

**`bash .softhouse/conformance.sh` → EXIT 2, and the four OPAQUE-SQL findings are
gone.** The ledger-invariants section in full:

```
ledger-invariants: the guard REFUSED:
REFUSED — the double-entry invariants DEC-2 §4.4 obliges are violated in the Go tree:
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:196:4
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:207:2
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:224:2
  [I3-FIELD-WRITE] internal/apps/loanproduct/repaymentperiod.go:541:4
  [I3-FIELD-WRITE] internal/apps/savings/postgres.go:243:7
  [I3-FIELD-WRITE] internal/apps/savings/postgres.go:302:5
  [I3-FIELD-WRITE] internal/apps/savings/summary.go:53:2
  [I3-SQL-BALANCE] internal/apps/savings/postgres.go:113:30
  [I3-SQL-BALANCE] internal/apps/savings/postgres.go:113:30
  [I3-SQL-BALANCE] internal/apps/savings/postgres.go:210:54
```

Ten findings, all belonging to T501 (savings) and T502 (loanproduct). **Zero
OPAQUE-SQL. Zero findings in any of my three files.**

Census, before → after:

```
before: 379 SQL-shaped literals / 63 DML verbs / 52 name a table; 22 exec-family (19 mutating). Findings: 14
after : 377 SQL-shaped literals / 64 DML verbs / 53 name a table; 21 exec-family (18 mutating). Findings: 10
```

**The mutating-exec count dropped by one and I am not going to let that pass
unexplained, because "fewer mutating calls" is exactly what evasion looks
like.** The drop is `tx.Exec(ctx, m.SQL)` becoming `m.Apply(ctx, tx)`, which is
a Go function call and not a driver call. The statement did not disappear — it
moved to wherever a migration is written, and **there are zero migrations in this
tree**, so 18 is the honest count of driver-level mutating calls that exist. The
first migration anybody writes puts its Exec back into the census, at its own
site, with its SQL readable. The other two counters move the right way and are
the real evidence: `53` literals now name a table where `52` did (the journal
entry INSERT is newly readable) and the DML-verb count rose to `64`.

The run still exits 2 because a HARD guard failed on T501/T502's ten findings.
Per the brief, I grade on the disappearance of my four lines, not on a green run.
Note also that `ledgerguard`'s own selftest case (n) — "the REAL Go tree must
PASS" — fails for the same reason, on `main` as well as on this branch; I
confirmed that by stashing. It will go green when the other ten findings clear.

---

## 5. MAJOR — the journal-entry INSERT cannot execute against the reference-oracle schema

This is not what I was sent to fix and **I have not fixed it.** It is reported
here with the evidence, per the brief.

All probes below are **read-only**: `PREPARE` parses and plans without executing,
each is wrapped in `BEGIN … ROLLBACK`, and nothing was written to the
reference-oracle database.

### 5.1 The defect, on this branch

```
$ psql -d fineract_default -f t503-prepare.sql       # the statement as T503 ships it
BEGIN
ERROR:  column "createdby_id" of relation "acc_gl_journal_entry" does not exist
LINE 2: ...sed, manual_entry, entry_date, type_enum, amount, createdby_...
```

The reference oracle's `acc_gl_journal_entry` has **`created_by`** and
**`last_modified_by`**, not `createdby_id` / `lastmodifiedby_id`
(`\d acc_gl_journal_entry` on `gerege-oracle-db`, PostgreSQL 18.3).

### 5.2 It is pre-existing, not introduced by T503

The same probe against the statement `main`'s `buildJournalEntryInsert` assembles
for one entry:

```
$ psql -d fineract_default -f t503-prepare3.sql      # main's VALUES form, verbatim column list
BEGIN
ERROR:  column "createdby_id" of relation "acc_gl_journal_entry" does not exist
```

Identical error. My diff does not add, drop or rename a column; it changes only
how the rows are supplied.

### 5.3 And the column names are not the whole of it

Correcting **only** the two audit names, the statement parses and plans cleanly —
so the `unnest` structure, the eleven parameter types, the `::date` and
`::numeric` casts and the thirteen-column target list are all sound against the
real schema:

```
$ psql -d fineract_default -f t503-prepare2.sql
BEGIN
PREPARE
 PREPARE OK with corrected audit column names
```

but the same probe also asked which NOT NULL columns without a default the INSERT
still fails to supply:

```
 still_missing_not_null_no_default
---------------------------------------------------------
 created_on_utc, last_modified_on_utc, submitted_on_date
```

**So even with the names corrected, an execution would fail on three NOT NULL
constraints.** The ledger's write path has therefore never run against the
schema it claims to target.

### 5.4 Why nobody noticed, and why I am not fixing it

`PostgresJournalEntryRepository` has **no callers anywhere in `nexus/`** and no
test exercises `Append` against a database. `grep -rn "PostgresJournalEntryRepository"
nexus/` returns the definition and one prose mention in `doc.go`. The statement
was unreachable, untested and — until this task — unreadable. Three
independent reasons for it to stay wrong indefinitely.

**I am not fixing it, deliberately.** Choosing what goes in `created_on_utc`,
`last_modified_on_utc` and `submitted_on_date`, and whether `transaction_date`
should be written alongside `entry_date`, is a schema-parity decision for the
ledger context that needs oracle vectors behind it — not a side effect of a task
whose brief is "make the SQL readable". Making that call quietly, inside a
readability repair, is the scope wander this program rejects. It is filed as
**B-4** in §7 and it should be a task.

### 5.4b One consolation, and it is a real one

The `unnest` rewrite is now **verified against the actual reference-oracle
schema**, which the old dynamic form never was and could not easily have been.
`PREPARE` type-checked all eleven parameters, both casts and the target column
list. That is a stronger statement about this SQL than anything on `main`.

### 5.5 The working-capital statement, by contrast, is clean

```
$ psql -d fineract_default -f t503-prepare4.sql
BEGIN
PREPARE
 PREPARE OK -- inlined column list matches m_wc_loan_balance
```

Which is the point of running it: the thirteen column names I re-typed by hand
are verified against the live schema, not checked by eye.

---

## 6. The DEC-2 exemption I did NOT take — written out so it can be overruled

The brief allowed an exemption for `migrate.go` and I decided against one. Here
is exactly what I would have proposed, so a reader who disagrees does not have to
reconstruct it. **This is a `user` gate. It is a proposal. Nothing is ratified,
and no guard was edited.**

> **DEC-2 §4.4.2 (proposed, NOT ratified) — migration-runner exemption.**
> `ledgerguard` shall not raise OPAQUE-SQL for a mutating exec whose SQL argument
> is a field of `platform/postgres.Migration`, at the single call site
> `internal/platform/postgres/migrate.go` in `applyMigration`.
>
> **What it would cover:** exactly one call site, reached only from
> `RunMigrations`, executing schema DDL supplied as data by the deployment tool.
>
> **What it would NOT cover:** any other opaque exec anywhere; any exec reached
> from application code; any statement against `acc_gl_journal_entry` from an
> application repository. It would be an exemption for a *runner*, never for a
> *statement*.
>
> **What it would cost:** every migration this program ever runs becomes
> permanently invisible to the I-3/I-4 guard. A `DELETE FROM
> acc_gl_journal_entry` shipped as migration text would pass a green bar. The
> guard's CANNOT-CATCH item 3 already concedes migrations are out of reach;
> ratifying this would make that concession *load-bearing* instead of merely
> honest.

**Why I rejected it.** The exemption buys the runner's convenience and pays with
the ledger's strongest static control, permanently, for every migration in the
program's future. The func-valued `Apply` costs a struct field with zero current
users and gives the guard MORE reach than it had. Amending a guard over a money
non-negotiable so it stops complaining is the shape the brief names as
rejectable, and I did not want to be the task that did it for a runner nobody
calls yet.

**If you overrule me**, the revert is small: restore `SQL string`, restore
`tx.Exec(ctx, m.SQL)`, ratify the text above, and amend `ledgerguard` to skip
that one position. It is one commit.

---

## 7. Backlog — found, out of scope, not edited

* **B-1 (guard heuristic).** `ledgerguard`'s `sqlArgOf` skips a leading context
  only for a bare `*ast.Ident` containing `ctx`, or a selector named
  `Background`. A repository that captures its context as a field and calls
  `db.Exec(r.ctx, <literal>, …)` — a normal shape in this tree — is classed
  OPAQUE-SQL **even though its SQL is a plain literal**. Proposed fix, in
  `sqlArgOf`, adjacent to the existing `Background` arm:
  ```go
  if sel, ok := first.(*ast.SelectorExpr); ok &&
      (sel.Sel.Name == "Background" || strings.Contains(strings.ToLower(sel.Sel.Name), "ctx")) {
      if len(call.Args) < 2 { return nil, false }
      return call.Args[1], true
  }
  ```
  This is fail-CLOSED in the right direction: it can only ever make MORE
  statements readable, never fewer. I did not edit the guard — it is outside my
  scope and the brief says to propose the text here instead.

* **B-2 (I-3, working capital).** `m_wc_loan_balance` is a stored balance table
  and `PostgresWorkingCapitalLoanBalanceRepository.Upsert` writes it. The guard
  does not flag it because its detection surface is the NAME and not one of the
  thirteen columns contains the string `balance` — the table name does, the
  columns do not (`principal`, `principal_paid`, `fee`, `penalty`,
  `overpayment_amount`, …). This is precisely CANNOT-CATCH item 2 ("renaming a
  balance defeats it") occurring naturally rather than maliciously. Whether a
  written `m_wc_loan_balance` is lawful under DEC-2 I-3, or is the
  `m_trial_balance` shape §7 refuses to port, is a real question and I am not
  qualified to close it inside a readability task. It should be looked at
  alongside T501's savings findings, which are the same shape and ARE flagged
  only because their columns happen to be spelled `..._balance_derived`.
  **Consider whether `balanceNameRe` should also test the TABLE name** — that
  single change would surface this site.

* **B-3.** `RunMigrations` has no callers and no `Migration` value is constructed
  anywhere in `nexus/`. Dead infrastructure. Either wire it or drop it; leaving
  an unexercised schema-mutation path in the tree is how §5's defect survived.

* **B-4 (from §5, MAJOR).** The journal-entry INSERT names `createdby_id` /
  `lastmodifiedby_id` (schema has `created_by` / `last_modified_by`) and omits
  three NOT NULL columns with no default (`created_on_utc`,
  `last_modified_on_utc`, `submitted_on_date`). It cannot execute. Needs a task
  with oracle vectors, not a patch.

* **B-5.** `gofmt -l nexus` reports four pre-existing unformatted files
  (`loanschedule/contract/contract.go`, `parties/client.go`, `parties/group.go`,
  `parties/legalform.go`). Not mine, not touched. Noted because a `guard_gofmt`
  exists and currently passes, so whatever it measures is not this.

---

## 8. What a reviewer should attack first

In the order I would attack it:

1. **The `ctx := r.ctx` local in `Append`.** It exists because of a guard
   heuristic, not because of an invariant. Decide whether that is acceptable or
   whether B-1 should land first and the local be reverted. I chose to ship it
   with the reason written beside it rather than leave the site red.
2. **The `Migration.SQL` → `Migration.Apply` change.** It is the largest
   judgement call in the diff and it changes a type. §6 is the argument; §1.4 is
   the mechanism. Overruling me costs one commit.
3. **`unnest` row-order.** I assert `unnest` over N arrays zips positionally so
   row *j* is element *j* of every array. If you doubt it, the test asserts every
   array is the same length (the misalignment failure mode) and §5.3 shows the
   planner accepts the shape — but nothing in CI executes it, because nothing
   calls `Append` at all (B-3).
4. **§5.** If you think a task that touched this file should have fixed the
   column names too, say so — I decided the opposite on scope grounds and the
   reasoning is in §5.4, not hidden.
