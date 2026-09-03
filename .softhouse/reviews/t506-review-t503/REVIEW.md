# T506 — INDEPENDENT REVIEW of T503 (`softhouse/T503-opaque-sql`, commit `c482b07d`)

Reviewer: T506. Reviewed branch: `softhouse/T503-opaque-sql` @ `c482b07d`.
Base at review time: `main` @ `cd277641`. Merge-base: `1762794b`.
Reference oracle: Fineract + PostgreSQL 18.3, container `gerege-oracle-db`, db `fineract_default`.
Pinned Fineract checkout: `/Users/buv/fineract` @ `426a23544`.

---

## VERDICT: **ACCEPT WITH CONDITIONS**

**The one question that matters — did T503 make the SQL readable, or merely make it
invisible to the guard? — is answered: READABLE. Measured, not read.**

I did not take that from the handoff. I planted six defects into T503's own repaired
shapes and ran the guard on each; every one was refused, four of them *by name and at
the offending line*. I then planted the same defects into `main`'s shapes and two of
them were **invisible**. Detection power went UP, not sideways. The transcript is §2.

The conditions are four, none of which blocks the merge of `c482b07d`. The largest
finding in this review is **not against T503 at all** — it is that the scope violation
the driver recorded against T503 in `main`'s `tasks.json` **did not happen**, and the
instrument that produced it will produce the same false accusation on every future task
whose branch is one commit stale. That is F-1, graded MAJOR, and it is the driver's to
fix, not T503's.

| # | Grade | Against | One line |
|---|---|---|---|
| F-1 | **MAJOR** | driver / process | The `tasks.json` "scope violation" is base drift. `c482b07d` touches 5 files and `tasks.json` is not one of them. |
| F-2 | MINOR | T503 | `workingcapital/postgres.go:361-363` promises a coupling between the const and the write literal that does not exist. |
| F-3 | MINOR | T503 | The rewritten ledger test does not pin the array→column mapping; two same-typed adjacent pairs are silently transposable. |
| F-4 | MINOR | T503 | The new `m.Apply == nil` refusal — a real hole T503 closed — has no test driving it red. |
| F-5 | MINOR | T503 (backlog B-1) | B-1's proposed guard fix is labelled "fail-CLOSED". Measured, it is purely refusal-*reducing*. Matters because T509 will implement it. |
| F-6 | MINOR | reviewer-found, for T509 | A third guard blind spot T503 did not find: `postgres.InsertReturningInt64` is a mutating wrapper the exec-family regex does not name. 20+ call sites. |

Conditions on ACCEPT:

- **C-1 (driver).** Correct T503's `note` in `main`'s `.softhouse/tasks.json`: it records a
  scope violation that the commit does not contain. Replace the scope instrument
  (`git diff --stat main..<branch>`) with one that cannot confuse "the worker wrote it"
  with "main moved on". Recommended: `git show --name-only --format= <branch> ^$(git merge-base main <branch>)`.
- **C-2.** Fix or delete the false-coupling comment at `workingcapital/postgres.go:361-363`
  (F-2). One line. May ride in any microfix.
- **C-3.** T508's `files_hint` already includes `journalentry_test.go`; it must extend the
  test to pin array→column alignment for the transposable pairs named in F-3 while it is
  correcting the column names.
- **C-4.** T509 must carry F-5's correction and F-6's third blind spot into its scope.

Everything T503 claimed in §1–§7 of its handoff that I could test, I tested. **Every
substantive claim held.** Where I differ it is on labels and on one comment, never on
the arithmetic, the SQL, or the schema evidence — and on §5 I found *stronger* evidence
than T503 did (§4.3).

---

## 1. What I ran (P-104 — cardinals verified by running something)

Every number in this review was produced by a command in this section, on this host,
against the branch under review. Nothing is quoted from the handoff.

```
git show --name-only --format= c482b07d                       # 5 files, no tasks.json
git merge-tree --write-tree main softhouse/T503-opaque-sql    # clean, tree c20c3c95
git diff --stat main c20c3c95                                 # 5 files, tasks.json absent
bash .softhouse/guards/check-ledger-invariants.sh             # in a worktree detached at c482b07d
bash /Users/buv/gerege-nbfi/.softhouse/guards/check-ledger-invariants.sh   # same script, main's tree
go -C <worktree>/nexus build ./...    rc=0
go -C <worktree>/nexus vet ./...      rc=0
go -C <worktree>/nexus test ./...     20 packages ok, 0 FAIL
gofmt -l <worktree>/nexus             4 files, all pre-existing, none of T503's
go build -C .softhouse/guards/ledgerguard -o /tmp/t506-ledgerguard .   # for the probes in §2
docker exec -i gerege-oracle-db psql -U root -d fineract_default …     # §4, all in BEGIN…ROLLBACK
```

Toolchain: the pinned `go1.26.6 darwin/arm64` at `.softhouse/toolchain/go`. The guard shim
was run with **`bash`**, never `sh`/`zsh`.

### 1.1 The guard, both trees, both exit codes read

| | `main` @ `cd277641` | `T503` @ `c482b07d` |
|---|---|---|
| exit | 1 | 1 |
| findings | **14** | **10** |
| `OPAQUE-SQL` | **4** | **0** |
| SQL-shaped literals | 379 | 377 |
| carry a DML verb | 63 | **64** |
| name an actual table | 52 | **53** |
| exec-family calls | 22 | 21 |
| …of which mutating | 19 | **18** |
| Go files inspected | 210 | 210 |
| selftest | 15 cases, 14 RED, 1 GREEN, **1 failure: case (n)** | identical |

The four `OPAQUE-SQL` lines on `main` are exactly
`ledger/journalentry_postgres.go:59:15`, `workingcapital/postgres.go:366:15`,
`platform/postgres/migrate.go:75:12`, `platform/postgres/migrate.go:93:16` — T503's four
sites, and **only** those four. On the branch they are gone and **no new finding of any
class replaces them**. The residual ten are byte-identical on both trees and belong to
T501 (savings) and T502 (loanproduct), as the brief said to expect.

**Every census cardinal T503 reported reproduces exactly.** So does the selftest failure:
case (n) "the REAL Go tree must PASS" fails on `main` too, for the same ten findings.
That claim was checkable and it checks out.

### 1.2 The two movements that could have been evasion, resolved

*The mutating-exec count fell 19→18.* T503 named this itself and called it "exactly what
evasion looks like". It is not evasion. The single removed mutating exec is
`tx.Exec(ctx, m.SQL)` in `applyMigration`, replaced by `m.Apply(ctx, tx)` — a Go call, not
a driver call. §2.4 measures what that trade actually bought and it is a net gain.

*The two counters that moved the other way are the real evidence.* Literals naming a real
table rose 52→53 and DML verbs 63→64, both because the journal-entry `INSERT` became
readable for the first time. I confirmed the mechanism directly: on `main` the census
prints the working-capital statement as

```
INSERT INTO m_wc_loan_balance (wc_loan_id, ) VALUES ($1,…,$14) ON CONFLICT …
```

— `(wc_loan_id, )`, thirteen column names the guard could not see — and on the branch it
prints all thirteen. That is a measured improvement in what the guard can read, in the
guard's own words, not the author's.

---

## 2. The decisive test: six planted defects, two trees

A repair that relocates a statement out of the guard's reach scores identically on the
bar. The only way to tell relocation from repair is to plant the defect and see whether
the guard still names it. I copied each tree to scratch, planted, ran
`/tmp/t506-ledgerguard --root <scratch>/nexus`, and reverted between probes.

| Probe | planted | on **T503** | on **main** |
|---|---|---|---|
| A | `DELETE FROM acc_gl_journal_entry WHERE 1=1;` prefixed to the ledger statement | `[I4-DML] journalentry_postgres.go:78:30` | (would also fire — literal prefix) |
| B | `ON CONFLICT (id) DO UPDATE SET amount = EXCLUDED.amount` appended to the ledger `INSERT` | `[I4-DML] journalentry_postgres.go:78:30` | n/a (no such clause existed) |
| C | `office_running_balance` added to the ledger `INSERT` column list | **`[I3-SQL-BALANCE] journalentry_postgres.go:78:30`** | **`[OPAQUE-SQL]` only — the guard is BLIND to the planted balance column** |
| D | a migration that builds its SQL with `fmt.Sprintf` | **`[OPAQUE-SQL] probe_migration.go:11:13` — at the migration's own line** | **NOTHING. Completely invisible.** |
| E | a migration whose literal is `DELETE FROM acc_gl_journal_entry WHERE reversed = true` | `[I4-DML] probe_migration.go:19:26` | `[I4-DML] probe_migration.go:7:53` |
| F | `ctx := r.ctx` removed, `r.db.Exec(r.ctx, <fixed literal>, …)` restored | `[OPAQUE-SQL] journalentry_postgres.go:77:15` | — |

### 2.1 Probe C is the answer to the question the brief asked

On `main`, planting a running-balance column into the ledger `INSERT` produces **no
I3-SQL-BALANCE finding at all**. The only line is the generic `OPAQUE-SQL` that was
already there before the plant — the guard cannot say *what* is wrong, only that it
cannot look. The reason is mechanical: `main` assembled the statement as
`"INSERT INTO acc_gl_journal_entry " + columns + " VALUES " + strings.Join(rows, ",")`,
and `concatLiterals` drops the `columns` identifier, so the text the guard analysed was
`INSERT INTO acc_gl_journal_entry  VALUES` — with no parenthesised column list,
`reInsertCols` never matched, and the I-3 INSERT arm was never even reached.

On the branch the same plant produces a precise `[I3-SQL-BALANCE]` naming the column and
the table. **That is a strict increase in detection power on the append-only ledger's own
write path, demonstrated rather than argued.** It is also the single fact that most
distinguishes "made readable" from "made invisible", and it lands on the right side.

### 2.2 Probes A and B — I-4 on the new shape

Both fire. The guard's classifier is operating on the new `INSERT … SELECT … FROM unnest`
statement, not skipping it. Note in particular that `upsertRe` catches probe B: the
`unnest` form is not a hiding place for an upsert.

### 2.3 Probe F — the `ctx := r.ctx` local is load-bearing, and T503 said so first

Restoring `r.ctx` at the call site brings `OPAQUE-SQL` straight back **even though the SQL
is a fixed literal**. So the one-line local is not stylistic and not cosmetic: without it,
this repair would not have cleared the bar at all. T503 disclosed this in §1.1 and filed
it as B-1 rather than letting a reviewer find it. That disclosure is the correct behaviour
and I record it as such. See F-5 for the one thing B-1 gets wrong.

### 2.4 Probe D settles claim 3 — the `Apply` change **widens**, measured

T503's claim was that carrying the step instead of the text means a run-time-built
migration is refused *at its own call site* instead of being invisible behind the runner.
That is exactly what probe D measures, and it is true:

- Under `main`'s `SQL string`: `Migration{SQL: fmt.Sprintf("DELETE FROM %s", table)}`
  produces **no finding whatsoever** at its own site. The runner's single standing
  `OPAQUE-SQL` at `migrate.go:93` was present with or without it and names nobody.
- Under `Apply func`: the same dynamic migration produces `[OPAQUE-SQL]` **at
  `probe_migration.go:11:13`**, naming the file and line of the offending migration.

Probe E shows the *literal* case was already covered on both trees — the guard analyses
every string literal group in every file regardless of how it is executed, so a literal
`DELETE FROM acc_gl_journal_entry` inside a `Migration{SQL: …}` was always caught. **The
widening is specifically in the dynamic case, which is the dangerous one.**

One honest caveat, which T503 also stated: under `Apply` the *standing* refusal at
`migrate.go:93` is gone, so a tree with zero migrations now carries one fewer red line.
That is correct — there is nothing to refuse — but it converts unconditional noise into
conditional coverage. T503 named this in its own words ("18 is the honest count of
driver-level mutating calls that exist"). Not a defect; recorded so nobody re-discovers
it as one.

**Verdict on claim 3: true as stated, and stronger than stated. It widens.**

---

## 3. Claim 2 — does the `unnest` rewrite preserve semantics?

I checked the column list, the SELECT list, the `unnest` alias list and the Go argument
order against each other by hand, then against the live schema by execution.

Target list (13) at `journalentry_postgres.go:78` —
`account_id, office_id, currency_code, transaction_id, reversed, manual_entry, entry_date,
type_enum, amount, createdby_id, lastmodifiedby_id, created_date, lastmodified_date`.
The SELECT list is the same 13 in the same order, with `CURRENT_TIMESTAMP` twice for the
two audit timestamps. The `AS e(...)` alias list is the first 11 in the same order. The
`[]any` returned by `buildJournalEntryInsertArgs` (`:129`) is the same 11 in the same
order, and each Go element type matches its cast:

| $n | alias column | cast | Go type |
|---|---|---|---|
| 1 | account_id | `bigint[]` | `[]int64` |
| 2 | office_id | `bigint[]` | `[]int64` |
| 3 | currency_code | `text[]` | `[]string` |
| 4 | transaction_id | `text[]` | `[]string` |
| 5 | reversed | `boolean[]` | `[]bool` |
| 6 | manual_entry | `boolean[]` | `[]bool` |
| 7 | entry_date | `text[]` (→ `::date`) | `[]string` |
| 8 | type_enum | `integer[]` | `[]int32` |
| 9 | amount | `text[]` (→ `::numeric`) | `[]string` |
| 10 | createdby_id | `bigint[]` | `[]int64` |
| 11 | lastmodifiedby_id | `bigint[]` | `[]int64` |

**No column added, none dropped, order identical to `main`'s.** The three running-balance
columns (`is_running_balance_calculated`, `office_running_balance`,
`organization_running_balance`) remain absent, as G-12 requires — and probe C proves the
guard would now *catch* their reintroduction, which it would not have before.

**Money stays integer minor units.** `MinorUnits` is `int64`
(`ledger/money.go:85`) and `FormatDecimal` renders it with `strconv.FormatInt` and integer
`/` and `%` only — no `strconv.ParseFloat`, no `big.Float`, no division into a float.
The rendered exact decimal text is cast to `numeric` **by Postgres**, so nothing on this
path is ever a float in Go or on the wire. `git diff main..c482b07d -- nexus/ | grep -E
'^\+.*(float32|float64|big\.Float)'` → no match. The forbidden-driver grep
(`ojdbc|oracle\.jdbc|:1521|com\.mysql|mariadb|go-sql-driver`) → no match. PostgreSQL via
`pgx` only.

### 3.1 Row order is array order — verified by execution, not by assertion

T503 asserts `unnest` over N arrays zips positionally. I did not take that on trust. I
executed the corrected statement against the real table inside `BEGIN … ROLLBACK` with a
one-row batch and read the failing row Postgres printed back:

```
DETAIL: Failing row contains (1, 1, 1, null, MNT, tx-t506, null, null, null, f, null, t,
        2026-09-03, 2, 1250000.000000, null, null, null, 1, 1, …)
```

Every value is in its own column: `account_id=1`, `office_id=1`, `currency_code=MNT`,
`transaction_id=tx-t506`, `reversed=f`, `manual_entry=t`, `entry_date=2026-09-03`,
`type_enum=2`, `amount=1250000.000000`, `created_by=1`, `last_modified_by=1`. The
positional zip holds and the alignment is correct as shipped. (The row failed on a NOT NULL
constraint — that is §4, and the transaction was rolled back.)

I also measured the *unequal-length* case, because it decides how dangerous a length
mismatch is: `SELECT * FROM unnest(ARRAY[1,2,3], ARRAY['a','b'])` yields three rows with
the short array **padded with NULL**. So a length mismatch surfaces as a NOT NULL violation
— **loud**. The silent failure mode is transposition, not length. That is F-3.

### 3.2 One unremarked improvement

`main` bound 11 parameters per entry, so a batch was capped by the wire protocol's 65535
parameter limit at roughly 5,957 legs. The new form binds 11 parameters regardless of
batch size. Not claimed by T503; worth recording as a real gain.

---

## 4. Claim 5 — T503's MAJOR. **Confirmed, and I found stronger evidence than it did.**

All probes below were run against the live reference oracle inside `BEGIN … ROLLBACK`.
Nothing was committed to `fineract_default`.

### 4.1 The statement as shipped cannot be prepared

```
BEGIN
ERROR:  column "createdby_id" of relation "acc_gl_journal_entry" does not exist
ROLLBACK
```

### 4.2 With the two audit names corrected it plans clean — and still cannot execute

`PREPARE` succeeds with `created_by` / `last_modified_by`, which independently validates
the `unnest` structure, all eleven parameter types, both casts and the thirteen-column
target list against the real schema. But `information_schema` over the same table returns
the NOT NULL columns with no default that the statement still fails to supply:

```
 still_missing_not_null_no_default
---------------------------------------------------------
 created_on_utc, last_modified_on_utc, submitted_on_date
```

and executing it fails on the first of them, as quoted in §3.1. `id` is
`is_identity = YES, BY DEFAULT`, so its omission is correct.

`main`'s `VALUES` form fails identically on `createdby_id`. **Pre-existing. Not introduced
by T503.** Its restraint in reporting rather than patching is endorsed: choosing values for
those three columns is a schema-parity decision that needs oracle vectors.

### 4.3 The evidence T503 did not have — the pinned Fineract source says the same thing

T503 rested this finding on the live database alone. A live database can drift. I went to
the pinned checkout, and the source is unambiguous —
`/Users/buv/fineract/fineract-provider/src/main/resources/db/changelog/tenant/parts/0025_add_audit_entries_to_journal_entry.xml`
at commit `426a23544`:

```xml
<changeSet id="journal-entry-3" author="fineract">
    <renameColumn tableName="acc_gl_journal_entry" oldColumnName="createdby_id"
                  newColumnName="created_by" columnDataType="BIGINT"/>
    <renameColumn tableName="acc_gl_journal_entry" oldColumnName="lastmodifiedby_id"
                  newColumnName="last_modified_by" columnDataType="BIGINT"/>
</changeSet>
```

and in the same file, `journal-entry-1` adds `created_on_utc` / `last_modified_on_utc`
(`TIMESTAMP WITH TIME ZONE` under the `postgresql` context), `journal-entry-5` makes both
NOT NULL, and `journal-entry-6` adds `submitted_on_date` NOT NULL. **All three of T503's
schema claims are corroborated from Fineract source, independent of the running instance.**

This also names the *origin* of the defect, which T503 did not diagnose and T508 will want:
the Go port copied Fineract's **pre-rename** column spellings. It was written against a
schema Fineract itself had already migrated away from.

### 4.4 Why nobody noticed — confirmed

```
$ grep -rn "NewPostgresJournalEntryRepository" nexus/
nexus/internal/apps/ledger/journalentry_postgres.go:35:   (doc comment)
nexus/internal/apps/ledger/journalentry_postgres.go:38:   func NewPostgresJournalEntryRepository(...)
```

The constructor appears **only at its own definition**. Zero callers anywhere in `nexus/`.
No test in the tree opens a database. So the write path of the append-only ledger — the
money core of this migration — is unreachable, untested and was until this task unreadable.
A green `go test ./...` said nothing about it, and still says nothing about it.

(One trivial correction to T503's §5.4: it says `grep` also returns "one prose mention in
`doc.go`". `doc.go:93` mentions Fineract's *Java* `JournalEntryRepository.java`, not the Go
type. Immaterial to the finding.)

**This is the more important finding than the repair, and I concur with that framing.**
T508 is correctly filed.

---

## 5. Claim 4 — no DEC-2 exemption taken, no guard amended

```
$ git diff --name-only main..softhouse/T503-opaque-sql | grep -E 'guards|docs/adr|conformance.sh|patterns.md'
NONE
```

Nothing under `.softhouse/guards/`, nothing in `docs/adr/`, nothing in `conformance.sh`.
The exemption T503 would have proposed is written out in handoff §6 as the **rejected**
alternative, explicitly unratified, with its cost stated ("every migration this program ever
runs becomes permanently invisible to the I-3/I-4 guard"). That is exactly the right shape:
the argument is preserved so a reader can overrule it without re-deriving it, and no code
was bent to accommodate the author.

The rejection reasoning is also correct on the merits, and probe D is the proof: the
exemption would have bought a runner's convenience and paid with the ability to see any
dynamic migration ever written. §2.4 measures that the chosen path buys the opposite.

**Claim 4 verified. This is the single most important thing T503 did not do.**

---

## 6. The scope note — F-1, and it goes the other way

### F-1 — MAJOR (against the driver's record and its scope instrument, **not** against T503)

**The scope violation recorded against T503 did not happen.** T503 committed no
`.softhouse/tasks.json`.

```
$ git show --name-only --format= c482b07d
.softhouse/handoff/T503-opaque-sql.md
nexus/internal/apps/ledger/journalentry_postgres.go
nexus/internal/apps/ledger/journalentry_test.go
nexus/internal/apps/workingcapital/postgres.go
nexus/internal/platform/postgres/migrate.go
```

Five files. `tasks.json` is not among them, and `c482b07d` is the branch's **only** commit
(`git log --oneline main..softhouse/T503-opaque-sql` returns one line).

The `tasks.json` divergence that appears in `git diff main..softhouse/T503-opaque-sql` is
**base drift**. T503 branched from merge-base `1762794b`; `main` has since advanced two
commits (`e0d8fbec`, `cd277641`) which themselves edited `tasks.json`. The two-dot diff
shows main's own later edits as if they were the branch's deletions.

**The stated merge risk does not exist under a normal merge**, and I proved that rather
than reasoning about it:

```
$ git merge-tree --write-tree main softhouse/T503-opaque-sql   # rc=0, no conflict
c20c3c9505134707d537fbc5e703540e9932e261
$ git diff --stat main c20c3c95
 .softhouse/handoff/T503-opaque-sql.md              | 503 +++++++
 nexus/internal/apps/ledger/journalentry_postgres.go|  95 ++--
 nexus/internal/apps/ledger/journalentry_test.go    |  58 ++-
 nexus/internal/apps/workingcapital/postgres.go     |  18 +-
 nexus/internal/platform/postgres/migrate.go        |  57 ++-
 5 files changed, 680 insertions(+), 51 deletions(-)
```

A three-way merge produces a tree differing from `main` in exactly the five files T503
wrote, with `tasks.json` **untouched and unconflicted** — because a three-way merge
correctly attributes main's `tasks.json` edits to main's side of the merge base. The
`tasks.json` reversion is reachable only by `git checkout <branch> -- .` or by
reconstructing the branch from a two-dot diff.

**Concrete failure scenario, and it is not hypothetical — it already fired.** The scope
check that `tasks.json` itself prescribes to every worker is
`git diff --stat main..<branch>`. That instrument reports *every* file main has touched
since the branch point as a violation by the branch. So:

1. Any branch that sits unmerged while main advances accrues phantom scope violations
   proportional to how long it waited — and the worst offender is always `tasks.json`,
   because the driver edits it on every dispatch.
2. A worker reading this rule will start defensively rebasing onto a moving main mid-task,
   which is exactly the churn worktree isolation exists to prevent.
3. A permanent, false accusation of process misconduct is now in `main`'s `tasks.json`
   against a task that behaved correctly. Records like that are load-bearing here: the
   next reviewer to grade a worker's scope discipline will read it as precedent.

**The driver already knows this shape and applied it correctly one note earlier.** T502's
note in `main`'s `tasks.json` reads: *"the tasks.json/incident divergence it disclosed is
base-vs-main drift from merge-base 14cf6c1f, not its writing."* The identical distinction
was available for T503 and was not made. The defect is the instrument, not the judgement:
a two-dot diff against a moving tip cannot answer "what did this worker write?", and it
should be replaced by
`git show --name-only --format= <branch> ^$(git merge-base main <branch>)` or the
equivalent three-dot form.

*(I was instructed by my own brief to "record it as a finding — a worker writing shared
orchestration state from inside a worktree is a process defect, not a typo." I am recording
the opposite, because that is what the repository says. If an independent reviewer will not
contradict the brief on a checkable fact, the review is not independent.)*

#### F-1 reproduced live, on this branch, during this review

I do not have to argue that this will recur. It recurred while I was writing it down.

I branched this review at `cd277641`. While I worked, `main` advanced to `e8ecae75` (the
T502 disposition), which edited `tasks.json`. My commit contains two files. The prescribed
scope check now reports three:

```
$ git diff --stat main..softhouse/T506-review-t503
 .softhouse/handoff/T506-review-t503.md        | 159 ++++++
 .softhouse/reviews/t506-review-t503/REVIEW.md | 694 ++++++++++++++++
 .softhouse/tasks.json                         |  14 +-        <-- NOT MINE

$ git show --name-only --format= HEAD
 .softhouse/handoff/T506-review-t503.md
 .softhouse/reviews/t506-review-t503/REVIEW.md
```

**The reviewer who filed this finding has been accused of the same violation by the same
instrument, in the same session, for a commit that does not contain the file.** One driver
commit was enough. The instrument does not measure what a worker wrote; it measures how
long the branch waited.

### The fifth file — `journalentry_test.go` — was a real out-of-`files_hint` edit, and it was disclosed

`files_hint` for T503 names three code files and the handoff. `journalentry_test.go` is
not among them. T503 edited it, **disclosed it in handoff §3 with the full reason**, and
the reason holds: `TestBuildJournalEntryInsertPinsTheSQLShape` asserted
`strings.Count(sql, "VALUES") == 1`, `len(args) == 22` and `args[14]`/`args[19]` — every
one of which the change necessarily invalidates. There is no version of this repair that
leaves that test green untouched, and "keep the tests green" is the bar's own requirement.
Disclosed, argued, and correct. **Not a finding.** (Judgement of the *replacement* test is
F-3.)

---

## 7. The remaining findings

### F-2 — MINOR: a comment promising a safety net that does not exist

`nexus/internal/apps/workingcapital/postgres.go:360-363`:

> *"the two must move together, and a column added here without being added there **will
> fail against the placeholder count in Upsert**."*

**This is false.** After the repair `Upsert` (`:378`) no longer reads `wcBalanceColumns` at
all — its column list is spelled out literally at `:379` and its 14 placeholders are
hard-coded in the same literal. Nothing links the const to the write path any more. The
promised failure cannot occur.

**Concrete failure scenario.** A later task adds `interest_accrued` to
`m_wc_loan_balance`, adds it to `wcBalanceColumns` so `FindByLoanID` reads it, and relies
on the comment to tell it whether `Upsert` needs touching. It compiles. `go test ./...`
stays green (nothing in the tree exercises either path against a database). At runtime the
`SELECT` now returns 14 columns into a 13-variable `Scan` and fails there, while `Upsert`
silently never writes the new column — leaving a working-capital balance row permanently
missing a component. The comment actively points the maintainer away from the write path.

The duplication itself is the right call and T503 argued it correctly ("thirteen column
names repeated once is the price of a statement a reader and a guard can both check").
Only the sentence claiming an automatic failure is wrong. Fix: say the two are
**decoupled** and must be changed together **by hand**, or drop the const and spell the read
path out too.

### F-3 — MINOR: the rewritten test does not pin array→column alignment

The brief asked whether the new test is *as strong*, and told me parallel-array `unnest`
makes a transposition silent and catastrophic. It is stronger in one dimension and weaker
in another.

**Stronger:** it pins the arg count at 11 and asserts every array has exactly one element
per entry. **But §3.1 measured that a length mismatch is the *loud* failure** — `unnest`
pads with NULL and the NOT NULL constraint refuses it. The test pins the safe failure mode.

**Weaker, and this is the gap:** nothing in the tree ties an array *index* to a *column
name*. The 13-column list now lives in a string literal in `Append` (`:78`) and the 11-array
order lives in `buildJournalEntryInsertArgs` (`:129`), roughly fifty lines apart, **with no
test, no type and no compiler check linking them**. On `main` both were produced by one
function from one `args = append(args, …)` list adjacent to the column const; the coupling
was weak but local. It is now non-local and unasserted.

The test asserts cells at indices 0, 3, 6, 7, 8. **Indices 1, 2, 4, 5, 9, 10 are
unasserted**, and two adjacent pairs among them share a Go type *and* a Postgres type, so a
swap is invisible to the compiler, to the test, and to Postgres:

- **`args[4]` `reversed` ↔ `args[5]` `manual_entry`** — both `[]bool` → `boolean[]`.
- **`args[9]` `createdby_id` ↔ `args[10]` `lastmodifiedby_id`** — both `[]int64` → `bigint[]`.

The fixture makes the first pair doubly undetectable: both entries have `Reversed` and
`ManualEntry` at their zero value, so even a value-level assertion on the current fixture
could not distinguish them.

**Concrete failure scenario.** T508 must edit both `Append` and
`buildJournalEntryInsertArgs` (it has to rename two columns and add three). Someone
reorders the arg slice to group the audit fields, or inserts the new `created_on_utc`
array between elements 4 and 5. `go build` passes. `go test ./...` passes — every array is
still length-2 and indices 0/3/6/7/8 still hold. `PREPARE` passes — the types still match.
Postgres writes `manual_entry` into `reversed`. Every journal entry the port ever posts is
then flagged reversed-or-not by the wrong bit, on the append-only ledger, where the
correction is a reversing entry and there is no UPDATE to fix it with. **Nothing in the
program would catch this before a parity run.**

Fix, and it is cheap: assert all eleven cells against a fixture whose values are pairwise
distinct (`Reversed: false, ManualEntry: true` on one leg; `createdByID: 7,
lastModifiedByID: 9`), and add a test that reads the SQL literal's `AS e(...)` alias list
and asserts it equals the documented array order. This belongs in T508 (C-3), which already
owns this file.

### F-4 — MINOR: the `Apply == nil` refusal is untested

`migrate.go:131` closes a real hole that T503 found and named: under `SQL string`, a
`Migration{SQL: ""}` executed an empty statement, succeeded, and **recorded the version as
applied**, leaving the schema behind its own version number. Closing it is a genuine
improvement and it was not asked for.

But `migrate_test.go` is unchanged (`git diff main..c482b07d -- .../migrate_test.go` is
empty) and covers only `planMigrations`. There is no test for `applyMigration` at all, so
nothing drives the new refusal red. **Concrete scenario:** a later refactor that "tidies"
the nil check into `if m.Apply != nil { … }` silently restores the exact silent-skip hole,
with a green bar. A guard clause with no test driving it red is a comment.

(Note the two existing tests construct `Migration{Version: 30, Name: "third"}` with no
third field, so they compiled before and after — no test was weakened to accommodate the
type change. I checked.)

### F-5 — MINOR: B-1 is correctly *found* but incorrectly *labelled*

B-1 is real: probe F proves `db.Exec(r.ctx, <plain literal>, …)` is classed `OPAQUE-SQL`
because `sqlArgOf` (`ledgerguard/main.go:479-497`) skips a leading context only for a bare
`*ast.Ident` containing `ctx`, or a `*ast.SelectorExpr` whose `Sel.Name` is exactly
`Background`. `r.ctx` is a `SelectorExpr` with `Sel.Name == "ctx"`, matches neither arm,
and is returned **as** the SQL argument. Correctly characterised, and the shape is normal
in this tree.

**The label is wrong.** T503 writes: *"This is fail-CLOSED in the right direction: it can
only ever make MORE statements readable, never fewer."*

Measured, the fix's **only** effect is to *remove* `OPAQUE-SQL` findings. It adds no
detection whatsoever, because the I-3/I-4 classifier does not run at exec sites — it runs
over **every string literal group in every file**, independent of any call. Probe E is the
proof: `Migration{SQL: "DELETE FROM acc_gl_journal_entry …"}` produced `[I4-DML]` on
`main` even though that literal sits in a struct literal and never reaches an
`Exec` argument position at all.

So `OPAQUE-SQL` is a **refusal-to-certify** class, not a detection class, and widening
`sqlArgOf` is purely refusal-reducing — fail-**open**, though harmlessly so, since it
removes only *false* refusals over statements the classifier was already reading. The
distinction matters because T509 will implement this patch, and "fail-closed" is the
justification a reviewer would use to wave it through without measuring it. It should be
justified as "removes a measured false positive", which is true and sufficient.

### F-6 — MINOR, reviewer-found: a third guard blind spot, for T509

T503 found two (B-1, B-2). Here is a third, in the same class as B-2 and arguably wider.

`postgres.InsertReturningInt64(ctx, db, sql, args...)`
(`nexus/internal/platform/postgres/insert.go:12`) is a package-level **mutating wrapper**.
`mutatingExecRe` (`ledgerguard/main.go:184`) matches
`Exec|ExecContext|MustExec|MustExecContext|SendBatch|CopyFrom|Prepare|PrepareContext`.
`InsertReturningInt64` matches nothing, and internally it reaches the database through
`QueryRows` → `db.Query`, which is in `readExecRe` and is **never flagged**.

There are 20+ call sites across `branch`, `savings`, `origination`, `collateral`,
`parties`, `investor` and `workingcapital`. Every one is safe *today* only because its SQL
happens to be a string literal, which the BasicLit walk analyses on its own. **A single
`postgres.InsertReturningInt64(ctx, r.db, buildInsert(cols), args...)` would be totally
invisible: no `OPAQUE-SQL` (the call name is unrecognised), and no literal to read.**

This is illustrated by a site the program is already acting on:
`savings/postgres.go:210` — one of the three live `I3-SQL-BALANCE` findings — is exactly
such a call. It is flagged *only* because its SQL is a literal, not because the guard
recognised the call as mutating. Had its author spliced in a column const, as
`workingcapital` did, the finding would have vanished with no `OPAQUE-SQL` to replace it.

**Concrete failure scenario.** T507 retargets savings onto the real Fineract schema. To
keep the read and write column lists in sync it factors the column list into a const and
splices it — the very shape T503 was sent to remove — but at an `InsertReturningInt64` call
rather than an `Exec`. The `I3-SQL-BALANCE` finding disappears. The bar goes green. The
balance column is still written on every transaction. **That is the exact "converts an I-3
finding into an OPAQUE-SQL one and looks like progress" failure my brief told me to hunt
for — except worse, because it converts it into *nothing at all*.**

Fix belongs with T509: `mutatingExecRe` should cover the repository's own mutating
wrappers, or the wrapper should take a type that only a literal can produce.

### F-7 — the backlog items T509 already owns, graded

- **B-2 is correct and I demonstrated its mechanism rather than agreeing with it.**
  `balanceNameRe` (`main.go:165`) is applied to `splitCols(m[3])` — the INSERT's **column**
  list — and to `setColumns(low)` for UPDATE. `m[2]`, the **table** name, is captured and
  used only in the finding text. It is never tested for `balance`. Confirmed by probe G:
  adding a column named `closing_balance` to the *same* `m_wc_loan_balance` statement makes
  the guard fire `[I3-SQL-BALANCE] workingcapital/postgres.go:379:30` immediately, while
  the thirteen real columns (`principal`, `principal_paid`, `fee`, `penalty`,
  `overpayment_amount`, …) produce nothing at all. Detection is keyed on the **spelling of
  a column**; a table literally named `m_wc_loan_balance` written by an
  `ON CONFLICT … DO UPDATE` is invisible.

  T503's stronger inference is also right and worth restating in the driver's words:
  **every I-3 finding this program has acted on is the subset whose columns happen to be
  spelled that way.** T501's savings sites are flagged only because Fineract spells them
  `account_balance_derived` and `running_balance_derived`. That is not a property of the
  tree; it is a property of Fineract's naming.

  Also note the repair *improved* this site even though it produced no finding: on `main`
  the guard could see `(wc_loan_id, )` and thirteen invisible names, any one of which could
  have been a balance column. It can now see all thirteen and say so. Making a statement
  readable is worth doing even when the answer is "clean".

- **B-1** — correct as a finding, mislabelled as fail-closed. See F-5.
- **B-3** (`RunMigrations` dead), **B-4** (=T508), **B-5** (4 pre-existing gofmt files, which
  I reproduced exactly and none of which is T503's) — all accurate as stated.

---

## 8. What I searched and did **not** find

"Not found" is a statement about the search, so here is the search.

- **A rename that dodges the guard's pattern while keeping the write.** None. The diff
  renames exactly one Go identifier — `buildJournalEntryInsert` → `buildJournalEntryInsertArgs`
  — and that name is not on any guard detection surface (`balanceNameRe`,
  `protectedGoNameRe`, `holdFuncRe`, `mutatingCallRe`). No struct field is renamed. The
  thirteen SQL column names are byte-identical to `main`'s, which I verified by diffing the
  column lists directly, and probe C proves the guard would now catch a balance column
  being *added*.
- **A balance still stored through a path the static walk cannot see.** None introduced.
  `git diff main..c482b07d -- nexus/ | grep '^+' | grep -E '\.Exec\(|\.Query\(|QueryRows\(|InsertReturningInt64\('`
  returns four lines: rewrites of the two pre-existing `Exec` calls at their own sites, one
  doc-comment example, and nothing else. **No new call site is opened**, and one is removed
  (`tx.Exec(ctx, m.SQL)`). The one pre-existing instance of this shape is F-6, which the
  diff neither creates nor worsens.
- **A guard or DEC amended to carve out the author's code.** None — §5, by
  `git diff --name-only`.
- **A test weakened or deleted.** One test rewritten, disclosed, judged at F-3; one test
  file (`migrate_test.go`) left untouched and still passing. No test deleted:
  `TestBuildJournalEntryInsertPinsTheSQLShape` was **replaced**, not removed. Counted:
  `grep -c '^func Test'` is **4 on both trees**. The replacement adds four assertions the
  original did not have (per-array length; `account_id`, `type_enum` and `entry_date` in
  entry order) and drops the two that pinned the SQL text (`HasPrefix "INSERT INTO
  acc_gl_journal_entry "`, `Count(sql, "VALUES") == 1`). Net it is broader on the
  arguments and blind on the statement — which is the trade F-3 grades.
- **An `UPDATE` or `DELETE` against `acc_gl_journal_entry` anywhere in `nexus/`.** None
  executable. `grep -rniE "(update|delete|truncate)[^\"]{0,40}(acc_gl_journal_entry|journal_entr)" nexus/`
  returns five hits, **all of them comments** — three explaining Fineract's own
  `UPDATE acc_gl_journal_entry SET is_running_balance_calculated=…`
  (`ledger/runningbalance.go:11`, `ledger/conformance/oraclederived.go:24`) and two in
  T503's new doc comments explaining what the guard refuses. The guard agrees: zero
  `I4-DML` findings over 210 files. **I-4 holds over the Go tree as far as a source-level
  guard can see, and probes A/B/E show the guard can still see it.**
- **Float in a money path, or a non-Postgres driver.** None, in the diff or in the two
  packages the diff touches. §3.
- **`entry_date` handling regressions.** `text[]` → `::date` on the server, same as `main`'s
  implicit coercion of a text parameter into a `date` column. Verified by execution (§3.1).

---

## 9. Bottom line

T503 was sent to make four unreadable statements readable. It did, and I measured that the
guard's power over the ledger's own write path went **up** as a result (probe C), not
sideways. It refused a DEC-2 exemption it was explicitly permitted to take, wrote the
rejected argument down anyway so it could be overruled, and — because it made the statement
readable — found that the append-only ledger's only write path **cannot execute against the
schema it targets**, has no callers, and never could have run. That finding is worth more
than the repair, and I confirmed it three ways including from Fineract source that T503 did
not consult.

The four conditions are cheap and three of them already have tasks. Nothing here blocks the
merge of `c482b07d`, and the merge is clean.

**ACCEPT WITH CONDITIONS.**
