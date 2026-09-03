# T501 — savings I-3 repair (`softhouse/T501-savings-i3`)

**Verdict: all six assigned findings REPAIRED. None argued away, none escalated as a DEC-2 gate.**
`guard_ledger_invariants` went from 14 findings to 4; the 4 that remain are other tasks'
(`loanproduct` ×4 `I3-FIELD-WRITE`), plus the pre-existing `OPAQUE-SQL` pair.

The organising principle for every site below is one sentence: **the savings balance is a fold
over the append-only transaction stream, computed on demand, held in nothing and stored
nowhere.** Not in a column, not in a struct field, not in a package variable.

---

## 1. What changed, per site

### `I3-SQL-BALANCE` — postgres.go:113, the summary INSERT arm
### `I3-SQL-BALANCE` — postgres.go:113, the `ON CONFLICT DO UPDATE SET` arm

**REPAIRED, by deleting the whole write path.** `PostgresSummaryRepository.Upsert` is gone, and
`Upsert` is gone from the `SummaryRepository` interface. The repository is now read-only.

I did not take the narrower option of dropping only `account_balance_derived` from the two arms,
and the reason is arithmetic rather than stylistic. The remaining twelve columns are
`total_deposits_derived`, `total_withdrawals_derived`, `total_interest_posted_derived`,
`total_fees_charge_derived`, `total_penalty_charge_derived`, `total_withdrawal_fees_derived`,
`total_annual_fees_derived`, `total_withhold_tax_derived` and friends. Deposits plus interest
posted, less withdrawals, fees, penalties and tax, **is the account balance**. A port that wrote
those twelve while piously omitting the thirteenth would be storing the same written balance in
pieces, and would have satisfied the guard's name-matching regex without satisfying the
non-negotiable. That is precisely the "renamed so it dodges the pattern while the write survives"
shape T504 is told to hunt for, so I did not build it.

Second, independent reason the write path had to go rather than be trimmed — see §4 finding A:
**the table it targets does not exist.** A write to a table no schema in this program creates is
dead on arrival; it cannot ever have run.

### `I3-SQL-BALANCE` — postgres.go:210, the transaction INSERT

**REPAIRED.** `running_balance_derived` is dropped from the column list and its argument from the
parameter list. The `INSERT` is now `(savings_account_id, transaction_type_enum, amount)`.

The column is nullable with no default in Fineract's own DDL
[VERIFIED: `fineract-provider/src/main/resources/db/changelog/tenant/parts/0001_initial_schema.xml:3864`
— `<column defaultValueComputed="NULL" name="running_balance_derived" type="DECIMAL(19, 6)"/>`],
so an `INSERT` that omits it is valid and rows this port appends simply carry NULL there. Nothing
about the adopted schema had to change: the column keeps existing and stops being written, which
is exactly the consistent position the task statement describes.

For the sibling column, same check, opposite nullability and the same conclusion:
`account_balance_derived` is `NOT NULL DEFAULT 0.000000`
[VERIFIED: same file, `:3709-3711`], so omitting it from an `INSERT` is likewise valid — the
default applies. **I checked this rather than assuming it**, because if that column had been
`NOT NULL` with no default, omitting it would have been impossible and I would have been in
DEC-2-amendment territory and stopped. It is not, and I was not.

### `I3-FIELD-WRITE` — postgres.go:243, `t.RunningBalance =` in `FindByAccountID`
### `I3-FIELD-WRITE` — postgres.go:302, `s.AccountBalance =` in `decodeSummary`

**REPAIRED, and the honest answer to the question the task asked is: the field should not exist.**

The task invited me to decide whether "derived, never written" is even engaged by a read-back
decode. My answer is that the decode is not the defect but it is not innocent either, and the
distinction that matters is not read-vs-write:

> A decoded balance is a number this port did not derive, arriving through the `SELECT` instead of
> the `INSERT`, and landing in a field callers then treat as authoritative. The invariant's purpose
> is that no balance in this system is trusted unless it was folded from the postings. A read-back
> satisfies "not written" while defeating exactly that purpose.

It is also, here, concretely wrong: now that `Insert` no longer populates `running_balance_derived`,
decoding it would parse NULL — failing, or worse, quietly yielding zero and presenting it as a
balance.

So both fields are deleted outright rather than left unassigned:

- `SavingsAccountTransaction.RunningBalance` — removed. Replaced by `RunningBalancesOf(stream)`, a
  prefix fold. The `SELECT` no longer names the column.
- `SavingsAccountSummary.AccountBalance` — removed. The summary `SELECT` drops
  `account_balance_derived::text`, `decodeSummary`'s arity goes 13 → 12, and the balance is
  `AccountBalanceOf(stream)`.

I also removed `SavingsAccountSummary.RunningBalanceOnInterestPostingTillDate`, which was not one
of my six. It is `@Transient` in the oracle, nothing in this tree read it and nothing wrote it, and
an unwritten balance-shaped hole in a struct is an invitation to fill it later. The daily-interest
running balance is a per-posting-period derivation and belongs to the interest slice.

### `I3-FIELD-WRITE` — summary.go:53, `s.AccountBalance +=` in `Add`

**REPAIRED.** `Add` is deleted. In its place, `summary.go` gains the derivations, all using the
shape the guard's own message names as lawful and `nexus/internal/apps/ledger/money.go`
(`DoubleEntryBalances`) already uses — two bare local accumulators, one per entry side,
differenced once at return:

```go
var debit, credit MinorUnits
...
return credit - debit
```

Four functions, no state:

| function | what it derives |
|---|---|
| `AccountBalanceOf(txns)` | the posted balance |
| `HeldOf(txns)` | outstanding holds (placed less released, floored at zero) |
| `AvailableOf(txns)` | posted balance less holds |
| `RunningBalancesOf(txns)` | the posted balance as at each transaction, in stream order |

**This is not a rename.** There is no field, no package variable and no column behind any of them;
each takes the postings and returns a number. `credit` and `debit` are the per-side sums the
double-entry derivation is *made of*, not a balance under another name — the balance exists only
as the expression `credit - debit` in a `return`.

---

## 2. A non-negotiable the naive fold would have broken

CLAUDE.md: *"Holds are postings and alter `available` only, never posted `balance`."*

Fineract classifies `AMOUNT_HOLD` as a **DEBIT** and `AMOUNT_RELEASE` as a **CREDIT**
[VERIFIED: `SavingsAccountTransactionType.java:36-54`, ported at `transactiontype.go` `EntryType()`].
So `Σ Effect()` over the stream — the obvious implementation — lets **placing a hold reduce the
posted balance**, violating I-6 while looking like a faithful port. `AccountBalanceOf` and
`RunningBalancesOf` therefore skip the hold/release pair before consulting `Effect()`, and the
holds surface only through `HeldOf` / `AvailableOf`. `TestHoldsMoveAvailableAndNeverThePostedBalance`
pins it.

## 3. A defect the fold flushed out — `Effect()` was wrong (now fixed)

`SavingsAccountTransaction.Effect()` read:

```go
if t.Entry.IsDebit() { return -t.Amount }
return t.Amount
```

An `if/else` over a **three-valued** classification. Every transaction type carrying *no* entry
type fell through to the credit arm and **increased** the balance — `ACCRUAL`, `WAIVE_CHARGES`,
the transfer sub-states and `WRITTEN_OFF`, all of which return the zero `TransactionEntryType`
[`transactiontype.go` `EntryType()`, default arm]. `transactiontype.go`'s own doc comment already
described them as *"balance-neutral and non-posting"*. They were not neutral: an accrual of
999.99 moved the balance by +999.99.

Caught by `TestUnclassifiedTypesDoNotMoveTheBalance`, which failed on first run. `Effect()` is now
an exhaustive `switch` with the unclassified case explicitly zero. Fixed in place because it is
inside my scope and my own derivations depend on it; called out here rather than folded silently
into a "refactor".

## 4. Worse than what I was sent to fix — stated, not fixed

**A. `m_savings_account_summary` DOES NOT EXIST IN FINERACT.** Not a naming quibble — a
schema-first violation, and the more serious finding on this branch.

`grep -rli m_savings_account_summary` over the pinned checkout at `/Users/buv/fineract` returns
**nothing**. `SavingsAccountSummary` is `@Embeddable`
[VERIFIED: `fineract-savings/.../savings/domain/SavingsAccountSummary.java:36`] and is `@Embedded`
into `SavingsAccount` [VERIFIED: `SavingsAccount.java:225`], so in the adopted schema all thirteen
`*_derived` columns are columns of **`m_savings_account`**, keyed by `id` — not of a side table
keyed by `savings_account_id`. No migration in `nexus/` creates the table either
(`nexus/internal/platform/postgres/migrate.go` creates only `schema_migrations`).

Consequences: the deleted `Upsert` could never have executed, and the surviving
`FindByAccountID` cannot execute either. CLAUDE.md is explicit that parity is only meaningful when
the oracle instance and the Go module read the *same* PostgreSQL schema; a table Fineract has never
heard of cannot be that.

**Not repaired here**, deliberately. Retargeting the statement (`FROM m_savings_account`,
`WHERE id = $1`) is a schema-first repair, not a ledger-invariant one, and doing it inside this
diff would blend two claims a reviewer has to re-derive separately. It is marked with a `⚠
PRE-EXISTING DEFECT` comment at the site so the next reader cannot miss it. **Backlog: retarget
`PostgresSummaryRepository.FindByAccountID` to `m_savings_account` keyed by `id`, and decide
whether the read model is wanted at all.**

**B. Backlog — the `Insert`/`decodeSummary` column set is unvectored.** No golden vector in
`.softhouse/vectors` exercises a savings row round-trip, so the column lists here are derived from
Fineract's DDL and entity mapping, not from a capture. Nothing in this repair depends on a captured
value, but nobody should read a green bar as parity evidence for savings persistence.

**C. Backlog, other tasks' sites, untouched (in the transcript, outside my scope):**
`loanproduct/interestperiod.go:196,207,224` and `loanproduct/repaymentperiod.go:541`
(`ip.outstandingLoanBalance =`, `ip.balanceCorrectionAmount =`); `OPAQUE-SQL` at
`ledger/journalentry_postgres.go:59` and `workingcapital/postgres.go:366`.

---

## 5. Conformance run — my sites are gone

Run with `bash`, per the harness's interpreter rule.

```
$ bash .softhouse/guards/check-ledger-invariants.sh 2>&1 | grep -E '^\s*\[I[0-9]' | sort -u
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:196:4
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:207:2
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:224:2
  [I3-FIELD-WRITE] internal/apps/loanproduct/repaymentperiod.go:541:4
```

**Before: 14 findings, six of them mine. After: 4, none of them mine.** Gone from the `REFUSED`
block: `savings/postgres.go:113` ×2, `savings/postgres.go:210`, `savings/postgres.go:243`,
`savings/postgres.go:302`, `savings/summary.go:53`.

**Gone by deletion, not by the walk losing sight of the package** — the disappearance is not a
coverage artefact, and the census proves it:

```
CENSUS   covered: internal/apps/savings
CENSUS   DML-classified literal: internal/apps/savings/postgres.go:67:54   INSERT INTO m_savings_account (...)
CENSUS   DML-classified literal: internal/apps/savings/postgres.go:113:30  UPDATE m_savings_account SET status_enum = $1 WHERE id = $2
CENSUS   DML-classified literal: internal/apps/savings/postgres.go:221:54  INSERT INTO m_savings_account_transaction (savings_account_id, transaction_type_enum, amount) VALUES ($1,$2,$3) RETURNING id
```

The package is still walked, its SQL is still classified, and the transaction `INSERT` is still
read by the guard — it simply no longer names a balance column. The summary `INSERT` is absent
because the statement no longer exists.

Full harness:

```
$ bash .softhouse/conformance.sh ; echo EXIT=$?
EXIT=2      (no `probe = ` line — a HARD guard failure, not an oracle outage; not parked)
```

Still `EXIT 2`, as expected and as the task predicted: `guard_ledger_invariants` remains red for the
four `loanproduct` sites and `OPAQUE-SQL`. Graded on the disappearance of my own lines, per the bar.

**One transcript line worth pre-empting for the reviewer**, because it reads alarmingly and is
*not* new:

```
ledger-invariants: the guard FAILED ITS OWN SELFTEST (exit 1, 15 cases observed,
ledger-invariants:   14 drove it RED, 1 drove it GREEN — both are required).
```

Both polarities are present (14 RED, 1 GREEN), so the trip is on `rc != 0`, and the failing case is:

```
FAIL (n) the REAL Go tree at .../nexus — must PASS: expected exit 0, got 1
```

Selftest case (n) runs the guard against the real tree and expects green. It is red *because the
tree is red for the loanproduct sites*. This is a consequence of the tree's state, not an
independent guard defect, and it clears when the remaining `I3-FIELD-WRITE` tasks land. Nothing in
this branch caused it or can fix it.

## 6. Build, tests, and the money rules

```
$ cd nexus && go build ./...        # clean
$ gofmt -l ./internal/apps/savings/ # clean
$ go test ./...                     # all packages ok, incl. savings and both conformance suites
```

- **Integer minor units throughout.** `grep -rn 'float32|float64|big.Float' nexus/internal/apps/savings/`
  returns only the sentence in `balance_test.go` saying there are none. Every accumulator, every
  intermediate and every test fixture is `MinorUnits` (`int64`). No fixture is a decimal literal.
- **PostgreSQL only.** No driver import was added or changed; the package still reaches the database
  solely through `internal/platform/postgres` (pgx/v5). No MySQL/MariaDB/Oracle driver or dialect.
- **Ships disabled.** Untouched. `Config.Enabled` still defaults false and
  `TestDefaultConfigIsDisabled` still passes; nothing here activates deposit-taking, which remains a
  hard `user` gate under Law on Non-Banking Financial Activities Art. 12.1.3 / 12.1.4.
- **No insurance claim.** No user-facing string was added. `grep -rniE 'insured|protected|guaranteed'`
  over the package matches only `doc.go`'s statement of the prohibition and the negative assertion in
  `savings_test.go` — the rule stated, never the claim made.

## 7. Tests added — `nexus/internal/apps/savings/balance_test.go`

Six tests, standing in for the deleted write path by asserting the fold itself:
`TestAccountBalanceIsFoldedFromPostings`, `TestAccountBalanceTreatsAmountAsMagnitude`,
`TestHoldsMoveAvailableAndNeverThePostedBalance`, `TestUnclassifiedTypesDoNotMoveTheBalance`
(this is the one that caught §3), `TestRunningBalancesArePrefixFolds`,
`TestSummaryCarriesNoBalanceField`.

The last one pins `decodeSummary`'s arity at twelve **in both directions** — it asserts that
thirteen fields are *refused*, so the balance column creeping back into the `SELECT` fails a test
rather than passing silently.

Note for T504: the guard's census now lists
`balance_test.go:43 TestHoldsMoveAvailableAndNeverThePostedBalance` as a "hold-named func". That is
a census line, not a finding — `_test.go` files are inspected, not exempted, and a hold-named test
containing no balance-named assignment is correctly counted and not flagged.

## 8. Scope

`git diff --stat main..softhouse/T501-savings-i3` touches only
`nexus/internal/apps/savings/{account.go,postgres.go,summary.go,transaction.go,balance_test.go}`
and this handoff. `account.go`'s only change is two doc comments that had gone stale
(`SavingsAccount.Summary` claimed to carry a running balance; `PostgresAccountRepository.Insert`
told the reader to "call `SummaryRepository.Upsert` afterwards", a method that no longer exists).

Nothing outside `nexus/internal/apps/savings/` was edited. Everything found outside it is in §4.
