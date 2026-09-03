# T504 — independent review of T501 (`softhouse/T501-savings-i3`)

Reviewed commits `78a17873`, `2e1a09df`. Reference oracle: pinned Fineract checkout
`/Users/buv/fineract` @ `426a23544`.

## VERDICT: ACCEPT WITH CONDITIONS

**The repair is real, not a silencing.** I set out to prove the opposite and could not. Every
one of the four evasion shapes I was told to hunt came back negative under a test that would
have found it (§1). The six findings are gone by deletion; the guard was not touched; no test
was weakened; the counts reproduce independently; both schema citations are exact to the line;
the `Effect()` defect the author claims to have found is a genuine bug I re-derived from
Fineract source; and the hold classification and its exclusion are both correct against the
oracle — more strongly correct than the author argued.

The conditions are one **MAJOR** and six **MINOR**. The MAJOR is not a leftover of the old
code: it is a property of the *new* fold, and it exists because T501 deleted a reversal-correct
number and replaced it with a reversal-blind one, declaring the replacement authoritative.

---

## 1. The one question that matters — correct, or quiet?

### 1.1 Was the guard amended to carve out the author's own code? **NO.**

```
$ git diff 78a17873^..2e1a09df -- .softhouse/guards/ | wc -l
0
```

Zero. The two commits touch exactly six files: the handoff plus
`nexus/internal/apps/savings/{account.go,balance_test.go,postgres.go,summary.go,transaction.go}`.

> **Correction to the task statement, for the driver.** `git diff --stat main..softhouse/T501-savings-i3`
> reports `.softhouse/tasks.json | 77 +-`. That is **main moving ahead of the branch point**, not
> T501 editing tasks.json. `git show --stat` on each of the two commits confirms tasks.json is not
> in either. T501 did **not** commit tasks.json. The handoff's §8 scope claim is accurate; the
> command in the task statement is what is misleading.

### 1.2 Was a field renamed so the write survives under a name the guard's pattern misses? **NO.**

The guard's matcher is `balanceNameRe = regexp.MustCompile("(?i)balance")` applied to identifier
and column names, and `checkBalanceWrite` fires on a **field**, **dereference** or **index**
target — a bare local (`var debit, credit MinorUnits`) is the shape the guard's own message names
as lawful (`ledgerguard/main.go:364-373, 691-704`). T501's four derivations use exactly that
shape, and the exemption is earned rather than exploited: there is no field, no package variable
and no map behind any of them; the value exists only as `credit - debit` in a `return`, or as an
element of a slice the function returns and does not retain.

I grepped the whole package for a surviving balance-shaped identifier under any name. The only
`balance`-matching identifiers left in non-test code are the four function names and two enum
constants (`CalculationDailyBalance`, `CalculationAverageDailyBalance`). No renamed store.

### 1.3 Is a balance still stored through a path the static walk cannot see? **Not a store — but see MINOR-5.**

No write path of any kind survives in savings: `Upsert` is gone from the struct *and* the
interface, `Add` is gone, both balance fields are gone. `go build` proves the interface removal
is real — a stale caller would not compile.

What *does* survive is a **read** path that decodes the nine columns from which Fineract's
balance is defined by identity. That is not a violation of the letter of I-3, but it is the exact
argument the author used twice to justify its own deletions, not applied to itself. Graded
MINOR-5.

### 1.4 Did the findings disappear because the guard stopped *seeing* savings? **NO — proven by two adversarial probes.**

This is the failure mode that looks identical to progress, so I did not take the census header's
word for it. I materialised the branch tree and planted each of the two deleted shapes back:

**Probe A — put a balance column back in the transaction INSERT** (`amount, running_balance_derived`):

```
$ cd /tmp/t504probe && bash .softhouse/guards/check-ledger-invariants.sh
[I3-SQL-BALANCE] internal/apps/savings/postgres.go:221:54     ← RED
```

**Probe B — put an `AccountBalance` field back on the summary and assign it**
(`func (s *SavingsAccountSummary) Add(...) { s.AccountBalance += t.Effect() }`):

```
$ cd /tmp/t504probeB && bash .softhouse/guards/check-ledger-invariants.sh
[I3-FIELD-WRITE] internal/apps/savings/summary.go:174:2       ← RED
```

Both classes still fire in this package, at the planted line. The disappearance is deletion, not
blindness.

### 1.5 Was a test weakened or deleted? **NO.**

```
$ diff <(main: func Test* in savings) <(T501: func Test* in savings)
```
Nothing removed. 7 → 13 test functions; `savings_test.go` is untouched by the diff. All six new
tests are additions.

---

## 2. Counted claims, re-run (P-104)

I did not accept the author's numbers. I ran the guard against both trees myself, with `bash`.

| tree | census `Findings:` | distinct `[CLASS] path:line:col` | savings |
|---|---|---|---|
| `main` | **14** | 13 | **5 distinct / 6 findings** |
| `softhouse/T501-savings-i3` | **8** | 8 | **0** |

The distinct-site count is 13 on main, not 14, because `postgres.go:113:30` carries *two*
findings (INSERT arm and `ON CONFLICT DO UPDATE` arm) at one position. That is the same
double-count trap the author flagged in the opposite direction, and it is why 14 − 6 = 8 closes
while 13 − 5 = 8 also closes. The census header is the honest denominator and it agrees.

The five distinct savings sites on main, all gone on the branch:
`postgres.go:243:7`, `postgres.go:302:5`, `summary.go:53:2` (`I3-FIELD-WRITE`);
`postgres.go:113:30`, `postgres.go:210:54` (`I3-SQL-BALANCE`).

The author's second commit correcting 14→4 to 14→8 is the right correction; I reproduce 8.
`go build ./...` exit 0, `go vet ./internal/apps/savings/...` exit 0, `go test ./...` exit 0
(savings `ok 2.808s`).

---

## 3. The six claims, independently derived

### Claim 3 — the nullability check. **VERIFIED, exact to the line.**

I opened the file rather than trusting the citation.
`0001_initial_schema.xml:3709-3711`:

```xml
<column defaultValueNumeric="0.000000" name="account_balance_derived" type="DECIMAL(19, 6)">
    <constraints nullable="false"/>
</column>
```

`:3864`:

```xml
<column defaultValueComputed="NULL" name="running_balance_derived" type="DECIMAL(19, 6)"/>
```

Both citations land on the exact lines claimed. `NOT NULL DEFAULT 0.000000` and nullable
respectively, so omitting each from an INSERT is legal. The author's stated discipline — check
first, because if it had been `NOT NULL` with no default this would have been DEC-2 territory —
is the right discipline and it was actually performed.

### Claim 2 — do the twelve remaining `total_*_derived` columns reconstruct the balance? **VERIFIED, and the argument is stronger than the author made it.**

The author argued it arithmetically ("deposits plus interest posted, less withdrawals, fees,
penalties and tax … and friends"). It does not need arguing: **Fineract computes it that way,
verbatim**, in `SavingsAccountSummary.updateSummary`:

```java
this.accountBalance = Money.of(currency, this.totalDeposits).plus(this.totalInterestPosted)
    .minus(this.totalWithdrawals).minus(this.totalWithdrawalFees).minus(this.totalAnnualFees)
    .minus(this.totalFeeCharge).minus(this.totalPenaltyCharge)
    .minus(totalOverdraftInterestDerived).minus(totalWithholdTax).getAmount();
```

All **nine** inputs are among the twelve columns retained. `account_balance_derived` is a
functional dependency of the set. So dropping only the thirteenth column while writing the other
twelve would have satisfied `balanceNameRe` and stored the balance anyway. **The decision to
delete the entire write path rather than trim one column is correct, and correct for the reason
given.** It is complete: I checked each of the nine against the Go struct and all nine are there.

### Claim 5 — was `Effect()` genuinely broken? **VERIFIED. Real bug, real fix, and it was slightly worse than stated.**

Fineract's third enum constructor argument is `null` for `INVALID(0)`, `WAIVE_CHARGES(6)`,
`ACCRUAL(10)`, `INITIATE_TRANSFER(12)`, `APPROVE_TRANSFER(13)`, `WITHDRAW_TRANSFER(14)`,
`REJECT_TRANSFER(15)`, `WRITTEN_OFF(16)`
[`SavingsAccountTransactionType.java:35-54`, and `SavingsAccountTransactionType(value, code)`
delegating to `this(value, code, null)`]. `EntryType()` in the Go port returns the zero
`TransactionEntryType` for exactly those, which I checked constant by constant against the Java —
**all 20 map correctly**.

`main`'s body was:

```go
if t.Entry.IsDebit() { return -t.Amount }
return t.Amount
```

`IsDebit()` is `t == EntryDebit`; the zero value is neither, so every one of those eight types
returned `+amount`. An `ACCRUAL` of `999_99` moved the balance by `+999.99`. Genuine bug,
correctly diagnosed. The new `switch` is exhaustive over the three-valued domain
(`IsDebit` / `IsCredit` / `default: return 0`) — I verified `TransactionEntryType` has exactly
two named values (`EntryCredit=1`, `EntryDebit=2`) so the default arm is the complete complement.
**The author under-reported: `INVALID(0)` is also in the fixed set and is not in its list.**

### Claim 6 — hold is DEBIT, release is CREDIT, and excluding them is required. **VERIFIED, and the exclusion is oracle-faithful too, which the author did not know.**

```java
AMOUNT_HOLD(20, "savingsAccountTransactionType.onHold", TransactionEntryType.DEBIT),
AMOUNT_RELEASE(21, "savingsAccountTransactionType.release", TransactionEntryType.CREDIT);
```

So a naive `Σ Effect()` would indeed let placing a hold reduce the posted balance — an I-6
violation and a CLAUDE.md non-negotiable breach. The exclusion is required.

I then checked whether the exclusion *also* matches the oracle, which the author asserted nothing
about. For `account_balance_derived` it does: neither `AMOUNT_HOLD` nor `AMOUNT_RELEASE` appears
in any of the nine totals in `updateSummary`, and in the incremental path
`updateSummaryWithPivotConfig` both fall to `default: break;` (`SavingsAccountSummary.java:182-183`).
**Fineract's stored account balance does not move on a hold either.** Fineract tracks holds
separately on `m_savings_account.savings_on_hold_amount` / `on_hold_funds_derived`
(`SavingsAccount.java:301,350,3308-3316,3653-3662`). So `AccountBalanceOf` is right on both
authorities. Good outcome, reached for an incomplete reason.

For `running_balance_derived` it does **not** — see MINOR-2.

### Claim 4 — fields deleted, not left unassigned. **VERIFIED.**

`SavingsAccountTransaction.RunningBalance` and `SavingsAccountSummary.AccountBalance` are gone
from the struct definitions, not merely unwritten; `RunningBalanceOnInterestPostingTillDate` too.
The four replacements exist and are exercised. `go build ./...` passing is the proof the removal
is total.

### Claim 1 — "held in nothing, stored nowhere". **MOSTLY. See MINOR-5.**

True of the balance. Not quite true of the nine numbers that determine it, which are still
decoded into struct fields.

### §4A, the author's own backlog claim — **VERIFIED, and it is not this branch's to fix.**

```
$ cd /Users/buv/fineract && grep -rl "m_savings_account_summary" . | wc -l
0
```

`SavingsAccountSummary` is `@Embeddable` at `SavingsAccountSummary.java:36` (exact), and it *is*
`@Embedded` into `SavingsAccount` — **but at `SavingsAccount.java:306-307`, not `:225`**, which is
the `@Embedded MonetaryCurrency currency`. Claim true, citation wrong (MINOR-6). `nexus/` creates
no savings table in any migration (`migrate.go` issues one `CREATE TABLE IF NOT EXISTS
schema_migrations` and otherwise executes a caller-supplied list which is empty; no `.sql` files
exist in the tree). Already routed as **T507**; not re-charged here.

---

## MAJOR-1 — the fold is reversal-blind, and reversal is CLAUDE.md's own correction mechanism

**This is the finding. Nothing else on this branch approaches it, and it is not filed anywhere.**

T501's organising principle is that the balance is a fold over the transaction stream. Fineract's
credit/debit classification — the thing being folded — is **not** `SavingsAccountTransactionType`.
It is `SavingsAccountTransaction.isCredit()` / `isDebit()`:

```java
// SavingsAccountTransaction.java:786-799
public boolean isCredit()     { return isCreditType() && !isReversed() && !isReversalTransaction(); }
public boolean isCreditType() { return getTransactionType().isCredit(); }
public boolean isDebit()      { return isDebitType()  && !isReversed() && !isReversalTransaction(); }
public boolean isDebitType()  { return getTransactionType().isDebit(); }
```

The Go `Effect()` ports `isCreditType()` / `isDebitType()` — the *type-only* half — and drops both
conjuncts. The same two conjuncts appear on **every one** of the twelve calculators in
`SavingsAccountTransactionSummaryWrapper` (`isNotReversed() && !isReversalTransaction()`), and
`recalculateDailyBalances` opens its loop body with
`if (transaction.isReversed() || transaction.isReversalTransaction()) { transaction.zeroBalanceFields(); }`
(`SavingsAccount.java:897-898`). Reversal-exclusion is not a detail of Fineract's balance
derivation; it is half of it.

Both flags are first-class schema columns, not transients:
- `is_reversed` — `0001_initial_schema.xml:3852-3854`, `<constraints nullable="false"/>`
- `is_reversal` — `@Column(name = "is_reversal", nullable = false)`, `SavingsAccountTransaction.java:133-134`

Neither is a field on the Go `SavingsAccountTransaction`, neither is in
`PostgresTransactionRepository.FindByAccountID`'s `SELECT`, and neither is consulted by
`AccountBalanceOf`, `RunningBalancesOf`, `HeldOf` or `AvailableOf`.

**Why this is T501's and not inherited.** Before this branch, the Go tree's savings balance came
from `decodeSummary(fields[12])` → `account_balance_derived`, i.e. from Fineract's own number,
which *is* reversal-correct. T501 deleted that read (correctly, on I-3 grounds) and installed a
fold in its place, and documented the fold as "the replacement for the deleted
`SavingsAccountSummary.AccountBalance` field and for `account_balance_derived`". It replaced a
forbidden-but-correct number with a permitted-but-wrong one, and disclosed nothing. That is the
shape of "made the guard quiet", arrived at honestly.

**Concrete failure scenario.** A member deposits 100,000₮; the teller mis-keys it and the deposit
is undone. Fineract's `undoTransaction` sets `reversed = true` on row 1 and, with `postReversals`,
appends `SavingsAccountTransaction.reversal(...)` — which is `copyTransaction` with
`reversed=false, reversalTransaction=true` (`SavingsAccountTransaction.java:352-358`), i.e. a
**second row of type `DEPOSIT(1)` with the same amount**. State in `m_savings_account_transaction`:

| id | type | amount | is_reversed | is_reversal |
|---|---|---|---|---|
| 1 | DEPOSIT | 100000.000000 | **true** | false |
| 2 | DEPOSIT | 100000.000000 | false | **true** |

- Fineract `account_balance_derived`: `calculateTotalDeposits` excludes both → **0₮**.
- Go `AccountBalanceOf(stream)`: `EntryType(DEPOSIT) = EntryCredit` for both rows → `credit = 200000` → **+200,000₮** — `20_000_000` minor units where Fineract stores `0`.

A 200,000₮ error on a two-row account, in the permissive direction, on the mechanism CLAUDE.md
itself names as the only legal correction: *"Corrections are reversing entries."* `RunningBalancesOf`
and `AvailableOf` inherit it. `HeldOf` inherits it too: a reversed `AMOUNT_HOLD` still holds funds.

Nothing in the tree catches this. `balance_test.go` has no reversal case; the author records
(§4B, which I confirm) that no golden vector exercises a savings row round-trip; and there is no
production caller of any of the four functions, so the whole package is a leaf and `go test`
green says nothing.

**Required.** Carry `is_reversed` and `is_reversal` on `SavingsAccountTransaction`, select them,
and skip any row where either is true — in all four derivations — with a test that plants the
two-row shape above. This is inside the ledger-invariant remit, not a schema question: it is what
"a fold over the append-only stream" has to mean when the stream contains corrections.

---

## MINOR-2 — `RunningBalancesOf` silently diverges from `running_balance_derived`, and a new test now pins the divergence

`RunningBalancesOf` is documented as "the replacement … for `running_balance_derived`". It is not
the same number. Fineract's `recalculateDailyBalances` moves the running balance on holds:

```java
// SavingsAccount.java:902, 912
if ((transaction.isCredit() || transaction.isAmountRelease()))  { ... plus  ... }
else if (transaction.isDebit() || transaction.isAmountOnHold()) { ... minus ... }
```

The Go version skips the hold/release pair. **The Go behaviour is what CLAUDE.md requires** —
holds must never move a posted balance — so I am not asking for it to be changed. The defect is
that a deliberate divergence from the reference oracle is undisclosed and now **enforced by a
test**: `TestRunningBalancesArePrefixFolds` asserts `want := {1_000_00, 1_000_00, 750_00, 753_21}`
across a stream containing an `AMOUNT_HOLD` of 400_00. Fineract's own `running_balance_derived`
for that stream is `{100000, 60000, 35000, 35321}` (in minor units).

**Failure scenario:** the first savings golden vector captured for a hold-bearing account fails
conformance, and the diff will look like a port bug rather than a ratified deviation, because
nothing in the tree records that it is one.

**Required condition:** state the divergence at the function and in the handoff, and route it as
an ENGINEERING gate entry so the vector harness knows to expect it (§2 of the handoff currently
argues that Fineract's *classification* makes the naive fold wrong, which is true; it does not say
that Fineract's *own running balance column* does the wrong thing and that we are knowingly
departing from it).

---

## MINOR-3 — `AccountBalanceOf` subtracts `ESCHEAT`; `account_balance_derived` does not

`EntryType(TxnEscheat) = EntryDebit`, matching `ESCHEAT(19, …, TransactionEntryType.DEBIT)`. But
`ESCHEAT` appears in **none** of the nine totals in `updateSummary`, and falls to `default: break;`
in `updateSummaryWithPivotConfig`. So Fineract's stored balance does not move on escheat, while
its `running_balance_derived` does (`isDebit()`). Fineract is internally inconsistent here; the Go
fold has silently picked one side.

**Failure scenario:** account balance 500,000₮, dormant, escheated. `SavingsAccount.escheat`
(`:3382-3396`) appends one `ESCHEAT` transaction for the full balance, then calls
`updateSummary`. Fineract `account_balance_derived` = **500,000₮**; Go `AccountBalanceOf` =
**0₮**. A 500,000₮ divergence on the exact operation that closes the account.

The Go answer is arguably the economically right one. That is not the standard — "Fineract is the
oracle" is. **Required:** pick a side explicitly, record it as an ENGINEERING gate with the
rationale, and vector it.

---

## MINOR-4 — `AvailableOf` overstates withdrawable funds, in the permissive direction

`AvailableOf(txns) = AccountBalanceOf(txns) - HeldOf(txns)`, documented as "what the account
holder may draw on". Fineract's is:

```java
// SavingsAccount.java:3319-3322
public BigDecimal getWithdrawableBalance() {
    return getAccountBalance().subtract(minRequiredBalanceDerived(getCurrency()).getAmount())
        .subtract(this.getOnHoldFunds()).subtract(this.getSavingsHoldAmount());
}
```

Three subtrahends. `HeldOf` covers only the third (and only its transaction-stream half). Missing:
`min_required_balance` (`m_savings_account`, schema `:3712`) and `on_hold_funds_derived`
(guarantor/loan holds, which produce **no** `AMOUNT_HOLD` transaction at all).

**Failure scenario:** balance 1,000,000₮; `min_required_balance` 100,000₮; a loan guarantee places
200,000₮ in `on_hold_funds_derived`; no `AMOUNT_HOLD` row exists. Go `AvailableOf` = **1,000,000₮**;
Fineract `getWithdrawableBalance()` = **700,000₮**. A caller wired to `AvailableOf` authorises a
900,000₮ withdrawal that Fineract refuses — 300,000₮ of guaranteed and minimum-balance funds
released.

Latent only because nothing calls it. **Required:** either narrow the doc comment to "posted
balance less transaction-stream holds — NOT the withdrawable balance; `on_hold_funds_derived` and
`min_required_balance` are not yet ported", or complete it. As written the comment overclaims.

---

## MINOR-5 — the "stored in pieces" argument is not applied to the surviving read path

The author gave two arguments, both good:

1. writing the twelve totals "would be storing the same written balance in pieces";
2. a read-back decode is "a number this port did not derive … trusted just the same", which is why
   `AccountBalance` was deleted from the struct rather than left unassigned.

Applied to the surviving `FindByAccountID`, either one condemns it. Nine of the twelve columns it
selects are, by Fineract's own source, the complete definition of `account_balance_derived`
(§ Claim 2). `decodeSummary` writes all nine into struct fields. Any caller can then write

```go
b := s.TotalDeposits + s.TotalInterestPosted - s.TotalWithdrawals - s.TotalWithdrawalFees -
     s.TotalAnnualFees - s.TotalFeeCharge - s.TotalPenaltyCharge -
     s.TotalOverdraftInterestDerived - s.TotalWithholdTax
```

and hold Fineract's stored balance in a variable, having gone nowhere near a posting and tripping
no guard — `balanceNameRe` matches none of those nine identifiers. So the answer to claim 1 is
"held in nothing, stored nowhere" for the balance, but **not** for the nine numbers that are the
balance.

This is not a violation of I-3 as written and I do not ask for the read model to be deleted. It is
graded because the branch's central claim is broader than what the code delivers, and because it
is a live reintroduction vector the guard cannot see. **Required:** say so at
`SummaryRepository`, where the doc currently reasons only about the *write* direction ("a port
that wrote them would be storing a balance in pieces") and stops one step short of noticing the
read direction has the same property.

---

## MINOR-6 — a citation that does not land

`SavingsAccount.java:225` is cited in the handoff, in `postgres.go`'s `⚠ PRE-EXISTING DEFECT`
comment, and in the commit message as the `@Embedded` of the summary. Line 225 is
`@Embedded protected MonetaryCurrency currency;`. The summary's is `SavingsAccount.java:306-307`.
The *claim* is true — I verified it — but the line is wrong, and the site comment will send the
next reader (T507) to the wrong field. `SavingsAccountSummary.java:36` is exact.

For completeness, one pre-existing citation in `transactiontype.go` is also off and is **not**
T501's (that file is untouched by this diff): `SavingsAccountTransactionType.java:24-47` for the
value table. The enum constants are at `35-54`; `:24-47` lands in the licence header and the
imports. (The `:36-54` entry-type citation misses only `INVALID` at `35` and is usable.)

---

## MINOR-7 — `HeldOf` masks a data defect and does not pair holds to releases the way the oracle does

Two issues in one function.

**(a) Silent floor.** The doc says "a release without a matching hold is a data defect, not a
negative hold" — and then `if released > placed { return 0 }`. It returns a plausible number
instead of surfacing the defect it just named. `TestHoldsMoveAvailableAndNeverThePostedBalance`
pins the masking. Failure scenario: a release row is duplicated by a retry without an
`Idempotency-Key`; `placed=300_00, released=600_00`; `HeldOf` = 0 and `AvailableOf` reports the
full balance as drawable, with no error anywhere. An error return, or a sentinel the caller must
handle, would surface it.

**(b) Aggregate pairing.** Fineract pairs a release to its hold by foreign key —
`release_id_of_hold_amount` (schema `:3871`), `isAmountOnHoldNotReleased()` is
`isAmountOnHold() && getReleaseIdOfHoldAmountTransaction() == null`
(`SavingsAccountTransaction.java:898-899`). `HeldOf` sums magnitudes and differences them, which
gives the same answer only when every release exactly and completely matches a hold. Combined
with MAJOR-1 (a reversed hold still counts) this is where a hold-tracking divergence will first
appear.

---

## NIT

`nullTime` in `savings/postgres.go:327` is now unreferenced within the package (`nullStr` is still
used). It was already unused on `main`, so this is not T501's, but the branch is the natural place
to drop it.

---

## What I searched, and where I looked (so "not found" is a statement about the search)

- **Guard tampering:** `git diff <base>..<tip> -- .softhouse/guards/` (0 lines) and `git show --stat`
  on both commits (6 files, none under `.softhouse/guards/`, none `tasks.json`).
- **Renamed store:** `grep -rniE 'balance' internal/apps/savings/*.go` excluding tests and comment-only
  lines; read `ledgerguard/main.go:162-169, 234, 303-340, 364-373, 513-535, 691-715` to learn the
  detection surface before deciding what would evade it.
- **Invisible write path:** read every statement in `postgres.go` at the tip; confirmed no INSERT
  names a balance column, no UPDATE assigns one, no SELECT decodes one; confirmed `Upsert` is gone
  from the interface (compile-enforced).
- **Coverage artefact:** two planted-regression probes (§1.4), each in its own copy of the branch
  tree, each driving the guard RED at the planted line.
- **Test weakening:** full `func Test*` inventory diffed between `main` and the branch.
- **Money math:** re-derived from `/Users/buv/fineract` @ `426a23544` —
  `SavingsAccountTransactionType.java`, `SavingsAccountTransaction.java`,
  `SavingsAccountSummary.java`, `SavingsAccountTransactionSummaryWrapper.java`,
  `SavingsAccount.java`, `0001_initial_schema.xml`. All 20 enum entry-type mappings checked
  individually; the nine-term balance formula checked term by term against the Go struct.
- **Integer minor units:** `grep -rnE 'float32|float64|big\.Float' internal/apps/savings/` — one
  hit, the comment in `balance_test.go:8` saying there are none. Every accumulator, intermediate
  and fixture is `MinorUnits` (int64); no decimal literal fixture.
- **PostgreSQL only:** no driver import added or changed; package reaches the DB solely through
  `internal/platform/postgres`. No MySQL/MariaDB/Oracle string anywhere in the diff.
- **Ships disabled:** `config.go:39` — `Config{Enabled: envBool(EnvName, false)}`. Default false,
  untouched by this branch.
- **Insurance strings:** `grep -rniE 'insured|protected|guaranteed'` over the package — three hits,
  all stating the prohibition (`doc.go:25-27`) or asserting its absence (`savings_test.go:179`).
  No user-facing string added by this diff at all.
- **Not searched / out of scope:** the four `loanproduct` `I3-FIELD-WRITE` sites and the four
  `OPAQUE-SQL` sites, per the task statement; the `m_savings_account_summary` retarget, which is
  T507; the journal-entry INSERT, which is T508; the guard's table-name blind spot, which is T509.
  My MAJOR-1 does not overlap any of those four.

## Conditions for merge

1. **MAJOR-1** — carry and honour `is_reversed` / `is_reversal` in all four derivations, with a
   test planting the two-row reversal shape. Blocking.
2. **MINOR-2, MINOR-3** — record each divergence from the reference oracle at the site and as a
   gate entry, so a failing savings vector is read as a ratified deviation rather than a port bug.
3. **MINOR-4** — narrow `AvailableOf`'s doc comment or complete the derivation. It currently
   claims to be the withdrawable balance and is not.
4. **MINOR-5, MINOR-6, MINOR-7, NIT** — non-blocking; fold into the T507 follow-up if not taken
   here.

Everything the author *claimed* about its own work, I checked, and it held — including the two
claims most likely to have been fabricated (the schema line numbers and the finding counts). The
MAJOR is a gap in what it thought about, not a misrepresentation of what it did.
