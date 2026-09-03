# T510 — the savings fold learns about reversals (`softhouse/T510-savings-fold-reversal`)

**Base: `softhouse/T501-savings-i3` @ `2e1a09df`, not `main`.** T510 applies `T504`'s review
conditions on top of T501 without undoing T501's I-3 repair.

**Verdict: MAJOR-1 fixed. All six MINORs addressed — five applied, one applied in the cheaper of
the two forms its reviewer offered, with the reason stated and the expensive form raised as
backlog. Nothing refuted: I went looking for something to argue with in T504 and found nothing
that survived contact with the pinned source.**

`guard_ledger_invariants`: **8 findings, ZERO in savings** — unchanged from T501, and proved to
be a real zero rather than a blind spot by two planted-regression probes (§3).

The one-sentence version: **T501 was right that the balance is a fold over the append-only
stream; it was wrong about what the stream says.** Fineract's fold is over
`isCredit()`/`isDebit()`, and the Go port had ported only `isCreditType()`/`isDebitType()` — the
type half. The two dropped conjuncts are the correction mechanism CLAUDE.md names as the only
legal one.

---

## 1. The RED test, and its output before and after

### The failure, re-derived from the pin rather than taken from the task statement

`undoTransaction` sets `reversed = true` on the ORIGINAL row and, with `postReversals`, appends
`SavingsAccountTransaction.reversal(original)` — which is `copyTransaction` with
`reversed = false, reversalTransaction = true` [VERIFIED: `SavingsAccountTransaction.java:352-358`].
The correction row is a **SAME-TYPE, SAME-AMOUNT copy**. So a fold that consults only the
transaction TYPE does not fail to cancel the error — it **doubles** it.

| id | type | amount | `is_reversed` | `is_reversal` |
|---|---|---|---|---|
| 1 | DEPOSIT | 100000.000000 | **true** | false |
| 2 | DEPOSIT | 100000.000000 | false | **true** |

Fineract: `calculateTotalDeposits` requires
`(isDepositAndNotReversed() || isDividendPayoutAndNotReversed()) && !isReversalTransaction()`
[`SavingsAccountTransactionSummaryWrapper.java:34-41`] and excludes both rows → **0₮**.

### BEFORE — RED

A temporary probe (`t510red_test.go`, deleted once the fix landed) run against the **unmodified
T501 tree**. The probe's whole content is two `TxnDeposit` fixtures, because before the fix
`is_reversed` and `is_reversal` are on no struct and in no SELECT — the two rows are, to this
port, *indistinguishable from two genuine deposits*, and that indistinguishability IS the defect:

```
$ go test ./internal/apps/savings/ -run TestT510Red -v
=== RUN   TestT510Red
    t510red_test.go:18: AccountBalanceOf(undone deposit) = 20000000, want 0
--- FAIL: TestT510Red (0.00s)
FAIL	github.com/gerege/nexus/internal/apps/savings	0.535s
```

`20000000` minor units = **+200,000₮ where Fineract stores 0₮**, on a two-row account.

### AFTER — GREEN

The permanent test is `TestReversedAndReversalRowsAreVoidInEveryDerivation`
(`balance_test.go`). It is strictly stronger than the probe: it asserts **all four derivations**
on the two-row shape, then asserts that a good deposit either side of the undone one still folds
(`{DEPOSIT 50,000; reversed DEPOSIT 100,000; reversal DEPOSIT 100,000; WITHDRAWAL 20,000}` →
`30,000₮`, running `{50000_00, 50000_00, 50000_00, 30000_00}`) — because a fix that voids
everything would also pass a test that only checks the zero. A second test,
`TestAReversedHoldHoldsNothing`, covers the reversed-hold case the review flagged as inherited.

```
$ go build ./...            # exit 0
$ go vet ./...              # exit 0
$ gofmt -l internal/apps/savings/    # no output
$ go test ./...             # all packages ok; savings ok 0.529s
```

### The fix, and why it is not a stored balance

Carried on `SavingsAccountTransaction`: `Reversed` (`is_reversed`), `Reversal` (`is_reversal`)
and `ReleaseIDOfHoldAmount` (`release_id_of_hold_amount`, see MINOR-7b). Added to
`FindByAccountID`'s SELECT and — for the two NOT NULL flags — to `Insert`.

Fineract's classification is then ported where Fineract puts it, on the transaction:

```go
func (t SavingsAccountTransaction) IsVoid() bool   { return t.Reversed || t.Reversal }
func (t SavingsAccountTransaction) IsCredit() bool { return t.Entry.IsCredit() && !t.IsVoid() }
func (t SavingsAccountTransaction) IsDebit() bool  { return t.Entry.IsDebit()  && !t.IsVoid() }
```

`Effect()` now switches on `IsDebit()`/`IsCredit()` instead of `Entry.IsDebit()`/`Entry.IsCredit()`,
which fixes all four derivations at their common root rather than at four call sites. `HeldOf`
does not go through `Effect()` and so carries the void test explicitly.

**I did not reinstate a stored balance, and the reviewer is invited to grade that by grepping.**
`account_balance_derived` and `running_balance_derived` are still in no INSERT, no UPDATE, no
SELECT and no struct field. The distinction the diff rests on, stated at
`postgres.go` under "A FACT ABOUT A POSTING IS NOT A BALANCE": the three columns added to the
SELECT are **per-row facts** — two booleans and a foreign key, not sums, not aggregates, not
derivable from any other row. The two columns still refused are **aggregates of other rows**.
Reading a fact is what a fold over an append-only stream is made of; reading a total is what I-3
refuses. A fold that cannot see which postings count is not a fold, it is a guess.

---

## 2. T504's six MINORs, one by one

**None refuted.** Each was re-derived from `/Users/buv/fineract` @ `426a23544` before being
acted on; every citation below is one I opened myself.

### MINOR-2 — `RunningBalancesOf` diverges from `running_balance_derived`, and a test pinned it — **APPLIED**

Confirmed: `recalculateDailyBalances` moves the running balance on holds
(`isCredit() || isAmountRelease()` / `isDebit() || isAmountOnHold()`,
[`SavingsAccount.java:902,912`]) and we do not. The reviewer is right that the Go behaviour is
the required one (CLAUDE.md non-negotiable) and that the defect was the *silence*.

Three things done, because a doc comment alone would have left the bad test in place:

1. **Documented at the site.** `summary.go` now opens with "THE THREE RATIFIED DIVERGENCES FROM
   THE REFERENCE ORACLE, STATED ONCE" (D-1/D-2/D-3), and `RunningBalancesOf` carries the worked
   example with both columns.
2. **Routed as a gate.** `.softhouse/gates.md` **G-25** (ENGINEERING, `chosen_by: agent`), with
   the vector consequence spelled out in minor units so the harness expects it.
3. **The test now pins the divergence AS a divergence.** `TestRunningBalancesArePrefixFolds` is
   renamed `…AndDivergeFromTheOracleOnHolds` and carries a second fixture,
   `oracleRunningBalanceDerived = {100000, 60000, 35000, 35321}`, re-derived by hand from
   `:902,912`. It asserts our column AND asserts that the two differ — so if a later edit makes
   the fold reproduce `running_balance_derived`, the test fails and tells the reader that either
   the fold started moving on holds (forbidden) or G-25 must be retired. The reviewer's
   objection was "a test that pins a wrong number is worse than no test"; a test that pins the
   *gap between two numbers* is the repair.

**One thing the review did not name, found while doing this — D-2 / G-26.** Fineract calls
`zeroBalanceFields()` on a void row, which sets `runningBalance` to **NULL**, not zero
[`SavingsAccount.java:897-898`; `SavingsAccountTransaction.java:586-591`]. `[]MinorUnits` has no
NULL and a zero would read as "the account emptied here", so a void row carries the unchanged
prefix balance. Same rule as D-1 — a posting that does not move the posted balance leaves the
running value alone — so it is one rationale covering two divergences rather than two.

### MINOR-3 — `ESCHEAT` diverges by the whole balance — **APPLIED, side picked explicitly**

Confirmed on both legs: `EntryType(TxnEscheat) = EntryDebit` matches
`ESCHEAT(19, …, TransactionEntryType.DEBIT)`, and `ESCHEAT` appears in **none** of the nine terms
of `updateSummary` and falls to `default: break;` in `updateSummaryWithPivotConfig`
[`SavingsAccountSummary.java:110-112`, `:182-183`] — I enumerated the eight `case` labels of that
switch to be sure. `SavingsAccount.escheat` [`:3382-3396`] appends an `ESCHEAT` for the *whole*
balance and then calls `updateSummary`, so Fineract's stored balance survives the escheat intact.

**Decision: ESCHEAT debits.** Recorded as **G-27** with the rejected alternative. Reasoning, and
I want to be explicit that "Fineract is the oracle" does not settle it: **there is no option that
matches Fineract**, because Fineract's two balance derivations disagree with each other. Given
that, (a) two of its three authorities — the entry-type classification and the running-balance
derivation — agree with us and only the stored aggregate does not; (b) that stored aggregate is
exactly the artefact DEC-2 §4.4 I-3 refuses, so "match it" is the one instruction this port
cannot follow; (c) the other side leaves 500,000₮ readable on a CLOSED account whose funds have
gone to the state — an overstatement, in the permissive direction, on the operation that closes
the account. Pinned by `TestEscheatDebitsThePostedBalance`.

### MINOR-4 — `AvailableOf` overstates withdrawable funds — **APPLIED in the reviewer's first form; second form raised as backlog**

Confirmed exactly: `getWithdrawableBalance()` has **three** subtrahends
[`SavingsAccount.java:3319-3322`] — `min_required_balance` (schema `:3712`),
`on_hold_funds_derived` (`:3718`) and `total_savings_amount_on_hold` (`:3727`, the column behind
`getSavingsHoldAmount()`, `SavingsAccount.java:349-350`). `HeldOf` covers the third and only its
transaction-stream half.

T504 offered two remedies. **I took "narrow the doc comment", not "complete it", and the reason
is scope rather than effort.** Completing it needs six columns on `SavingsAccount` that do not
exist there (`min_required_balance`, `on_hold_funds_derived`, `total_savings_amount_on_hold`,
`enforce_min_required_balance`, `allow_overdraft`, `overdraft_limit`) plus a faithful port of
`minRequiredBalanceDerived`, which subtracts the overdraft limit when overdraft is allowed. That
is an **account-model** slice. CLAUDE.md's scope guard treats wandering outside the assigned
context's remit as a rejection, and a ledger-invariant repair task is not where the savings
account aggregate should grow six fields.

What the doc now does instead of overclaiming: the warning is the **first** paragraph, not the
last; it prints Fineract's three-subtrahend formula with the column each term reads; it names the
concrete overstatement (100,000₮ minimum balance + 200,000₮ guarantor hold → **300,000₮ more
released than Fineract would allow**); and it says in terms that this must not be wired to a
withdrawal authorisation. It also names *why* `on_hold_funds_derived` cannot be recovered from
the stream: guarantor and loan holds produce **no `AMOUNT_HOLD` row at all**.

**Backlog, raised not fixed:** port the account-level withdrawable balance. Until then this
function fails **open** on money, which is the one thing about it I am not comfortable with, and
the doc says so at the top rather than the bottom.

### MINOR-5 — the "stored in pieces" argument is not applied to the read path — **APPLIED**

Confirmed, and it is a fair charge: the nine-term formula at
`SavingsAccountSummary.java:110-112` is reconstructible from nine of the twelve columns
`FindByAccountID` decodes, and the guard's `(?i)balance` matcher matches none of those nine
identifiers.

`SummaryRepository`'s doc now states the symmetry, prints the nine-term formula, and says
plainly that the read model is retained *anyway* — the strangler window needs it, and the
balance-shaped answer it enables is Fineract's number correctly labelled rather than this port's
number wrongly labelled. It also states that the two are **not interchangeable** and points at
D-1/D-3 for exactly where they disagree, which is the fact a caller reaching for the shortcut
would be missing.

### MINOR-6 — a citation that does not land — **APPLIED**

`SavingsAccount.java:225` is `@Embedded protected MonetaryCurrency currency;`. The summary's
`@Embedded` is at `:306-307`. Corrected in `postgres.go` (with a note that T501's number was
wrong, so T507 is not sent to the wrong field) and in `summary.go`.

The pre-existing citation T504 flagged is fixed too, and its diagnosis was right: the enum
constants are at `SavingsAccountTransactionType.java:35-54`, and `:24-47` lands in the licence
header. Both `:24-47` and `:36-54` are replaced by `:35-54` across `transactiontype.go`,
`doc.go` and `summary.go`.

### MINOR-7 — `HeldOf` masks a data defect and mis-pairs holds — **BOTH HALVES APPLIED**

**(a) The silent floor is gone.** `HeldOf` and `AvailableOf` now return `(MinorUnits, error)`.
The reviewer's scenario is the right one — a release duplicated by a retry without an
`Idempotency-Key` gave `placed=300_00, released=600_00`, `HeldOf` = 0, and the whole balance
reported as drawable with no error anywhere. On money a derivation that cannot be computed must
fail closed and say so. The error is a typed `*ErrOrphanRelease` carrying the offending
transaction id and amount, so a caller can log the row rather than the fact.

**(b) Pairing is now by identity, as the oracle pairs it.** `HeldOf` sums holds satisfying
`IsHoldNotReleased()` — the port of `isAmountOnHoldNotReleased()`
[`SavingsAccountTransaction.java:898-899`] with the void conjunct added — instead of summing hold
magnitudes and subtracting release magnitudes. The FK is reliably present on Fineract's own data:
it is written at all three production release sites
[`SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953`;
`InteropServiceImpl.java:451,494`] and the validator refuses a second release against an
already-paired hold [`SavingsAccountTransactionDataValidator.java:321`]. A release row that no
hold claims is now the `ErrOrphanRelease` from (a), which is what unifies the two halves: the
error case stopped being an arithmetic underflow and became a real referential orphan.

Two derivation notes the reviewer should check:

- The **void conjunct on a hold is not invented.** `recalculateDailyBalances` tests
  `isReversed() || isReversalTransaction()` **before** the `isAmountOnHold()` branch and zeroes
  the row [`SavingsAccount.java:897-912`], so a reversed hold moves nothing in Fineract's own
  derivation either. `isAmountOnHoldNotReleased()` itself does not test it — but it has **zero
  callers in Fineract** (I grepped the whole tree), so it is a definition, not the operative
  path; the operative path is the stored `total_savings_amount_on_hold`, which is a written
  balance this port refuses.
- The **claimed-release set is built from ALL hold rows, including void ones**, because the
  pairing is a fact about two rows and does not stop being true when the hold is reversed.
  `TestAnUnclaimedReleaseIsRefusedRatherThanFlooredToZero` covers that case explicitly.

### NIT — `nullTime` unused — **APPLIED.** Dropped, along with the now-unused `"time"` import.

---

## 3. The guard still reports ZERO savings sites — and it is a real zero

```
$ bash .softhouse/guards/check-ledger-invariants.sh
CENSUS … Findings: 8
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:196:4
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:207:2
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:224:2
  [I3-FIELD-WRITE] internal/apps/loanproduct/repaymentperiod.go:541:4
```

All four are `loanproduct`, outside this task. Savings: **0**, unchanged from T501.

I did not take that at face value, because my diff **adds columns to a savings INSERT**, and
"the guard stopped seeing the file" looks identical to "the file got clean". Two planted
regressions, each reverted:

| probe | planted | guard |
|---|---|---|
| A′ | `running_balance_derived` in the transaction **INSERT** | `[I3-SQL-BALANCE] internal/apps/savings/postgres.go:278:54`, Findings **8 → 9** |
| B | `AccountBalance` field + `s.AccountBalance += t.Effect()` on the summary | `[I3-FIELD-WRITE] internal/apps/savings/summary.go:68:2`, Findings **8 → 9** |

Both fire at the planted line, so the guard still sees this package after the change. Census
confirms `covered: internal/apps/savings` and lists my modified INSERT by name. Tree reverted to
clean between and after; the final run above is post-revert.

**Non-negotiables, grepped on the diff:** no `float32`/`float64`/`big.Float` anywhere in the
package (the single hit is the comment asserting their absence); every accumulator, intermediate
and fixture is `MinorUnits` (int64) and every fixture is written in minor units. No
MySQL/MariaDB/Oracle driver, dialect or port. `config.go` default still `false` — savings ships
disabled, NBFI, Art. 12.1.3/12.1.4. No user-facing string added by this diff at all; the only
`insured|protected|guaranteed` hits remain the prohibition text in `doc.go` and the test that
asserts their absence.

---

## 4. Worse than what I was sent to fix — RAISED, NOT FIXED

### 4A — `PostgresTransactionRepository.Insert` cannot succeed against the adopted schema

Found while adding `is_reversed` to the INSERT. `m_savings_account_transaction` has **four**
NOT-NULL-with-no-default columns the statement omitted: `is_reversed` (`:3852-3854`),
`office_id` (`:3845-3847`), `transaction_date` (`:3855-3857`) and `created_date` (`:3866-3868`).

I fixed the one in my remit (`is_reversed`, plus `is_reversal` which is NOT NULL DEFAULT false
[`0005_savings_transaction_reversal.xml:27-30`]). **The other three I did not touch**: supplying
them needs an office model and a business-date clock, neither of which exists in this package,
and inventing values on a money row would be worse than the omission. Noted at the site.

**Severity:** the statement is dead code today (no production caller), but it is dead code that
*looks* alive. `m_savings_account`'s INSERT is worth the same audit — I did not do it, being
outside this task.

### 4B — this port has no hold/release service, so `HeldOf` refuses its own writes

`Insert` does not write `release_id_of_hold_amount` — it cannot, because Fineract sets that FK
*after* the release row exists, which is an UPDATE and a service this package does not have. So a
hold and a release appended **by this port** are unpaired, and `HeldOf` returns
`ErrOrphanRelease` rather than a number.

That is deliberate and it fails **closed** — it over-holds rather than over-releases — and
reading Fineract's own rows, which is what the strangler window actually does, is exact. But it
is a functional gap and I am flagging it rather than letting the next reader discover it from a
failing integration test. Documented at both `HeldOf` and `Insert`.

### 4C — the guard's `I3-SQL-BALANCE` class does not fire on a SELECT, only on a write — MEASURED

My first probe planted `running_balance_derived::text` in the transaction **SELECT** and the
guard stayed at 8 findings. Re-planting the same column in the **INSERT** fired immediately
(probe A′ above). Reading `ledgerguard/main.go`, the class has exactly two triggers: a balance
column populated at INSERT, and an `UPDATE … SET <balance column>`.

This is consistent with I-3 being a rule about writes, so it is **not a guard bug** — but it is
the precise mechanical reason T504's MINOR-5 is invisible to automation, and it means the
`SummaryRepository` doc I wrote is the *only* thing standing between a future reader and
`SELECT account_balance_derived`. Recorded here so T509 (the guard's blind-spot task) has the
measurement rather than the inference. **Not fixed: amending the guard is not this task's remit,
and I was told not to touch `.softhouse/guards/`.**

---

## 5. Files changed

```
.softhouse/gates.md                            +  G-25 / G-26 / G-27
nexus/internal/apps/savings/transaction.go        the two flags, the FK, IsVoid/IsCredit/IsDebit/
                                                  IsHoldNotReleased, Effect() rerooted
nexus/internal/apps/savings/summary.go            D-1/D-2/D-3 block; HeldOf rewritten + errors;
                                                  AvailableOf narrowed + errors; ErrOrphanRelease
nexus/internal/apps/savings/postgres.go           SELECT +3 cols, INSERT +2 cols, read-path
                                                  symmetry note, citation fixes, nullTime dropped
nexus/internal/apps/savings/transactiontype.go    citation fixes; INVALID(0) added to the
                                                  no-entry-type list
nexus/internal/apps/savings/doc.go                citation fix
nexus/internal/apps/savings/balance_test.go       the reversal tests, the escheat test, the
                                                  orphan-release test, the divergence pin
```

No file outside `nexus/internal/apps/savings/` and `.softhouse/gates.md`. `.softhouse/tasks.json`
and `.softhouse/guards/` untouched — verify with `git show --stat`, **not**
`git diff main..HEAD`, which reports main's own movement as though it were mine.
