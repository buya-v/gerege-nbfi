# T522 — INDEPENDENT review of T515 (`84dc208e`)

**Subject:** commit `84dc208e7c104bda1608a7aa9d620ebadc6306ee`, "T515: port the third arrow of the
savings classification; delete G-25 and G-27".
**Stack:** T501 `78a17873`/`2e1a09df` → T510 `5c4233fc` → **T515 `84dc208e`**.
**Reference oracle (Fineract) checkout:** `/home/user/fineract`, `.git/HEAD` =
`426a23544e8426a38ae43ae404670a0a7e85b9eb` — the commit of record. Revision not changed.
**Reviewer stance:** T515's handoff (`.softhouse/handoff/T515-savings-classification-rework.md`)
was **not read as evidence**. Every claim below was re-derived from the pinned Java, from
`git show 84dc208e`, or from a command whose output is in
`.softhouse/capture/t522-review-t515/RUNLOG.md`.

---

## Coverage — what this review did and did not grade

**THIS IS A PARTIAL REVIEW. Do not read it as a clean bill on T515.**

The reference oracle (Fineract) is **UNREACHABLE** from this cloud sandbox — re-verified this
fire, not taken from the dispatch:

```
$ curl -sk -o /dev/null -w '%{http_code}\n' --max-time 8 https://localhost:8443/fineract-provider/actuator/health
000        (curl exit 7 = CURLE_COULDNT_CONNECT)
```

### GRADED

| brief item | what was graded | how |
|---|---|---|
| **1 — the third arrow** | **FULLY GRADED.** `SavingsAccountTransactionType.java:180-188` re-derived; the Go port checked against the Java for **all 20 enum constants**; the deleted hand-rolled list checked for uncovered behaviour by exhaustive difference. | Source read + a 20-row enumeration probe whose expectations are transcribed from the Java, not from the Go under review. |
| **2 — the gate deletions** | **FULLY GRADED.** G-25, G-26, G-27 premises each re-derived from source. RESERVED-component test applied to each. | Source read of `SavingsAccount.java:882-924`, `SavingsAccountSummary.java:93-113`, `SavingsAccountTransactionSummaryWrapper.java`, `SavingsAccountTransaction.java:586-591`. |
| **4 — reversal repair survived** | **GRADED** (needs no oracle). Every named piece present; discrimination re-proved by planting the defect. | NC-3 in RUNLOG. |
| **6 — the severable extra** | **GRADED, and it produced this review's MAJOR.** | NC-4, NC-5, and the per-type branch probe. |
| **7 — live-oracle state drift** | **GRADED.** | The captures are Go literals and prose in-repo; nothing re-reads the DB. |
| BAR — build / vet / test / gofmt / ledger-invariants / prohibited strings / integer minor units / savings-disabled / frozen contract | **GRADED.** | RUNLOG. |

### NOT GRADED — named residuals, each with why

| # | not graded | why | who must pick it up |
|---|---|---|---|
| **R-1** | **Item 3 — the escheat number `0 → 50000000` re-computed AGAINST THE REFERENCE ORACLE.** | Oracle unreachable. **`[UNVERIFIED: oracle_unreachable]`.** See §"What I can and cannot say about 50000000" — the *arithmetic* is confirmed from source; the *observation* CAPTURE-A is not. | next oracle-reaching fire |
| **R-2** | **Whether CAPTURE-A and CAPTURE-B were OBSERVED or CONSTRUCTED** (brief item 5's first half). | Oracle unreachable, **and no raw transcript exists in the repo** — see F-6. I can confirm they are internally consistent with the Java and that nothing re-reads the DB; I cannot confirm a psql session ever produced those rows. **`[UNVERIFIED: oracle_unreachable]`** | next oracle-reaching fire |
| **R-3** | Product 2's `nominal_annual_interest_rate = 0.000000`, `currency_digits = 2`, and the `m_savings_account_transaction` `information_schema` recount (SEVEN NOT NULL no-default columns; `created_date` nullable). | All are live-DB measurements. **`[UNVERIFIED: oracle_unreachable]`** | next oracle-reaching fire |
| **R-4** | The golden-vector conformance run (`.softhouse/conformance.sh`). | Oracle unreachable; also explicitly out of my scope — another worker is live on `conformance.sh` this fire. | next oracle-reaching fire |
| **R-5** | Whether `AccountBalanceOf` equals `account_balance_derived` for a `PAY_CHARGE` row with a null `chargePaidBy` (F-5). | Needs an oracle row to settle. **`[UNVERIFIED: oracle_unreachable]`** | next oracle-reaching fire |

**Go tests skipped for want of a database: none.** The entire `internal/apps/savings` suite is
pure in-memory folds over slice literals; `go test ./...` ran all 26 packages green with no
database. No `-short`, no build tag, no skip was needed anywhere.

---

## VERDICT on the slice I did grade

# ACCEPT WITH CONDITIONS (PARTIAL)

**The two highest-stakes items are CLEAN, and I confirmed them by re-derivation rather than by
reading T515's argument.**

- **Item 1 — the third arrow is a correct and COMPLETE port.** All 20 enum constants agree with
  the Java. The hand-rolled `IsAmountHold() || IsAmountRelease()` list and the new derivation
  differ on **exactly one type, `ESCHEAT`** — measured, not argued. Deleting the list leaves **no
  behaviour uncovered**.
- **Item 2 — both gate deletions are RIGHT, on premises I verified TRUE from source.** G-25's
  premise ("Fineract contradicts itself") is false; T513's "two different quantities" reading is
  correct and I re-derived it. G-27 was a live money bug, not a design choice. **No deleted gate
  had a surviving RESERVED component** — see §Gate deletions. Nothing needs restoring.

**The conditions are one MAJOR and five MINORs, all listed below.** The MAJOR is not that the code
is wrong — I verified it is right — but that a money path T515 shipped is **graded by nothing**,
while T515's stated justification for shipping it was that it *was* graded.

**This verdict covers items 1, 2, 4, 6, 7 and the BAR. It says nothing about item 3 or about the
provenance of the captures.** A later reader must not upgrade it.

---

## Findings

### F-1 — MAJOR. `HoldNetRunningBalancesOf`'s AMOUNT_RELEASE arm is graded by NO test and NO capture

**Where:** `nexus/internal/apps/savings/summary.go:517` (added by `84dc208e` — this is T515's own
line, not inherited).

```go
case t.IsCredit() || t.Type.IsAmountRelease():   // <- the `|| release` term
	running += amount
case t.IsDebit() || t.Type.IsAmountHold():
	running -= amount
```

**The measurement.** Delete the `|| t.Type.IsAmountRelease()` term — i.e. remove the exact
re-admission Fineract carries at `SavingsAccount.java:902` — and the **entire savings suite stays
green**:

```
$ go test ./internal/apps/savings/          # with the release re-admission DELETED
ok  	github.com/gerege/nexus/internal/apps/savings	0.005s
```

Contrast the hold arm, where the same mutation is caught immediately (NC-4):

```
--- FAIL: TestHoldNetRunningBalancesMatchTheCapturedOracleRows
    CAPTURE-B hold: running_balance_derived[1] = 100000, oracle = 60000
```

**Why it is ungraded.** Neither capture contains an `AMOUNT_RELEASE` row — CAPTURE-B is
DEPOSIT/HOLD/WITHDRAWAL, CAPTURE-A is DEPOSIT/ESCHEAT — and no test passes a release row through
`HoldNetRunningBalancesOf`:

```
$ grep -n "HoldNetRunningBalancesOf" nexus/internal/apps/savings/balance_test.go
273:  HoldNetRunningBalancesOf(0, c.stream)      # captureBStream / captureAStream
292:  HoldNetRunningBalancesOf(100_00, captureBStream())
298:  HoldNetRunningBalancesOf(0, nil)
315:  HoldNetRunningBalancesOf(0, stream)        # deposit / reversed / reversal / withdrawal
356:  HoldNetRunningBalancesOf(0, captureBStream())
402:  HoldNetRunningBalancesOf(0, captureAStream())
```

Every one of those six streams is release-free.

**Why it is MAJOR and not MINOR.** This bears directly on brief item 6. T515 shipped
`HoldNetRunningBalancesOf` as self-declared scope creep and justified keeping it on the ground
that *"it had a capture to grade it against"*. That justification is **two-thirds true**: the hold
arm is graded by CAPTURE-B, the no-branch (ESCHEAT) case by CAPTURE-A, and the **release arm by
nothing at all** — while the function's own doc-comment names the release re-admission as one of
the two halves of the asymmetry it exists to reproduce. A release is the operation that gives held
funds back; the failure direction (a release that never restores) leaves an available-shaped
figure permanently depressed by the hold.

**It is NOT a correctness defect.** I verified the shipped code is right, per type, against the
Java: `TestT522HoldNetBranchPerType` re-implements `recalculateDailyBalances`'s branch selection
from `SavingsAccount.java:896-920` and agrees with the Go on all 20 constants, release included.
The defect is in the **grading**, and in the claim made about the grading.

**CONDITION (accept if either is done, cheapest first):**
1. **Now, no oracle needed:** add a release row to the test corpus — a source-derived unit test
   (`{DEPOSIT 1000.00; AMOUNT_HOLD 400.00; AMOUNT_RELEASE 400.00}` → hold-net chain
   `{100000, 60000, 100000}`, posted chain `{100000, 100000, 100000}`) labelled explicitly as
   **source-derived from `SavingsAccount.java:902`, not a capture**. This makes NC-5 red.
2. **Next oracle-reaching fire:** capture a real release row (CAPTURE-C) on the restored `gerege`
   tenant and promote the unit test's expectation to it.

Do **not** sever the function: it is additive, called by no production code
(`grep HoldNetRunningBalancesOf` finds only tests and doc comments), correct per type, and
severing it re-opens G-25 with nothing to answer it. **KEEP, and grade the third arm.**

---

### F-2 — MINOR. `updateReleaseId` has THREE non-test callers, not four

**Where:** `summary.go:305-310`, `HeldOf`'s doc — **which contradicts itself inside one sentence**:

```
:305   ... never cleared — the three assignment sites are
:306   SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953 and
:307   InteropServiceImpl.java:451,494, and `updateReleaseId`
:310   /Users/buv/fineract, 4 non-test sites, all passing a transaction id].
```

*Three* at `:305`, *4* at `:310`, five lines apart. `balance_test.go:479` repeats the wrong one:
*"the four non-test callers of `updateReleaseId` all pass a transaction id"*.

**Measured:**

```
$ grep -rn "updateReleaseId" /home/user/fineract --include=*.java | grep -v /build/
SavingsAccountTransaction.java:466                      <- the DECLARATION, not a caller
SavingsAccountWritePlatformServiceJpaRepositoryImplTest.java:329   <- a TEST
SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953
InteropServiceImpl.java:451
InteropServiceImpl.java:494
```

Five hits: one declaration, one test, **three** non-test callers — so `:305` is right and `:310`
and `balance_test.go:479` are wrong; the count of four appears to have counted the declaration
as a caller.

**The conclusion is unaffected and I confirm it independently:** all three callers pass a
transaction id, the declaration is `updateReleaseId(Long releaseId)`
[VERIFIED: `SavingsAccountTransaction.java:466-468`], and no site passes null — so the FK is never
cleared and `HeldOf`'s identity-based pairing is oracle-faithful. Only the number is wrong.

---

### F-3 — MINOR. "twelve calculators" vs "thirteen calculators" — T515's own files disagree, and thirteen is right

`transactiontype.go:277` says *"none of the thirteen calculators"*; `transaction.go:78` says
*"every one of the twelve calculators"*. (`.softhouse/gates.md` says only *"no calculator"* — it
carries no count and is not part of this finding.)

**Measured:**

```
$ grep -c "public .* calculate" SavingsAccountTransactionSummaryWrapper.java
13
```

Thirteen methods (two are overloads of `calculateTotalInterestPosted` /
`calculateTotalOverdraftInterest`); `updateSummary` calls eleven of them
[VERIFIED: `SavingsAccountSummary.java:96-106`]. Cosmetic, but it is a count in a money file that
three separate comments state differently.

---

### F-4 — MINOR. A live-instance measurement is frozen into permanent source and is now STALE

`summary.go` and `.softhouse/gates.md` both assert, in the present tense:

> *"no `gerege` tenant and no `fineract_gerege` database exist on it [VERIFIED: psql against
> `gerege-oracle-db`, this fire]"*

That was **true when written (2026-09-03)** and matches
`.softhouse/reference-oracle.md:1250-1293`. It is **no longer true**: OH-1 restored the tenant on
2026-09-05 [VERIFIED: `.softhouse/reference-oracle.md:1304-1351` — `gerege`, tenants id 2,
`Asia/Ulaanbaatar`, `c_configuration.rounding-mode = 4` (HALF_UP), `fineract_gerege`, with a live
HALF_UP/HALF_EVEN discrimination proof at `1,162,502.50 × 0.018` → `20925.05` vs `20925.04`].

T515 is not at fault — the claim is dated and was correct — but this is `patterns.md`'s
"a measurement that goes stale, not a fact" hazard sitting in a Go source comment where nothing
will re-run it. **The good news is that it makes R-1/R-2 cheap:** the correctly configured tenant
now exists, so the re-capture the next fire owes can be taken at the ratified settings.

**CONDITION:** when R-2 lands, update those two passages to say
*"as at 2026-09-03 there was no `gerege` tenant; restored 2026-09-05 by OH-1"*.

---

### F-5 — MINOR, ATTRIBUTED TO THE STACK AND NOT TO T515. `AccountBalanceOf ≡ account_balance_derived` is not universal

`AccountBalanceOf` folds the **type-level** `isCredit()`/`isDebit()`. Fineract's
`account_balance_derived` is a **nine-term wrapper sum**
[VERIFIED: `SavingsAccountSummary.java:110-112`]. The two agree on the type sets I enumerated —
credit {DEPOSIT, INTEREST_POSTING, DIVIDEND_PAYOUT}, debit {WITHDRAWAL, WITHDRAWAL_FEE,
ANNUAL_FEE, PAY_CHARGE, OVERDRAFT_INTEREST, WITHHOLD_TAX} — **with one exception**:

`PAY_CHARGE(7)` is `DEBIT` in the enum, so `IsDebit()` is true unconditionally. But it reaches
`account_balance_derived` only via `calculateTotalFeesCharge` / `calculateTotalPenaltyCharge`,
which test `isFeeChargeAndNotReversed()` / `isPenaltyChargeAndNotReversed()` — and those are
`isPayCharge() && chargePaidBy != null && chargePaidBy.isFeeCharge()` (resp. `isPenaltyCharge()`)
[VERIFIED: `SavingsAccountTransaction.java:845-858`]. **A `PAY_CHARGE` row with a null
`chargePaidBy` reduces `AccountBalanceOf` and does not reduce `account_balance_derived`.**

**Attribution, deliberately:** this is **not T515's line**. T510's `Effect()` classified
`PAY_CHARGE` as a debit through the raw entry type identically, and T501's before it. `84dc208e`
changed nothing here. Blaming T515 for it would be the base-drift defect T512 was filed to stop.

**What T515 DID do that touches it:** `summary.go` now says *"THIS FUNCTION EQUALS
`account_balance_derived`, MEASURED"* and `postgres.go` says *"SINCE T515 THE TWO AGREE"*. Both
are true **of the two captures** and both are stated more broadly than the two captures support.
**CONDITION:** narrow those two sentences to "equal on CAPTURE-A and CAPTURE-B", and record the
`PAY_CHARGE`/null-`chargePaidBy` case as backlog (R-5). No code change.

---

### F-6 — MINOR (process, but it is why R-1 and R-2 exist). No raw capture transcript is committed anywhere

```
$ ls -d .softhouse/capture/*t515* .softhouse/capture/*t513*
(nothing)
$ git show --stat 84dc208e
gates.md | handoff/T515-....md | balance_test.go | postgres.go | summary.go | transaction.go | transactiontype.go
```

CAPTURE-A and CAPTURE-B exist **only** as prose in `summary.go`/`gates.md` and as Go literals in
`balance_test.go`. There is no psql transcript, no query output, no timestamped log. An
independent reviewer therefore **cannot distinguish an observation from a construction without
re-running the oracle** — which is exactly the position this review is in, and exactly the
circularity the dispatch warned against.

Note this is the same failure shape as the one T515 correctly diagnosed in
`TestEscheatDebitsThePostedBalance`: a number pinned by a test that cannot be checked against
anything outside itself. T515 fixed the instance and did not fix the class.

**CONDITION:** the next oracle-reaching fire commits the raw capture output under
`.softhouse/capture/<task>/`, and future capture-bearing tasks do so as a matter of course.

---

### Where I looked and found NOTHING — so that silence is distinguishable from not looking

| checked | result |
|---|---|
| Float on any money path in `nexus/internal/apps/savings/` | **CLEAN.** Only hit is `balance_test.go:11`, a comment asserting the rule. `MinorUnits` is `int64` (`money.go:14`). |
| Any string calling savings insured / protected / guaranteed | **CLEAN.** Only hits are the guard test (`savings_test.go:179`) and the doc stating the rule (`doc.go:25-27`). |
| Savings ships disabled | **CLEAN.** `config.go:22,39` — `Enabled bool` zero value false; `DefaultConfig` returns `envBool(EnvName, false)`. |
| `check-ledger-invariants.sh` savings sites | **ZERO.** 34 findings tree-wide, all in `loanproduct` / `loan` / `investor` / `loanschedule`. See attribution note below. |
| Direct balance writes / stored balances introduced by `84dc208e` | **NONE.** The functional diff adds one struct (`RunningBalance`) and one pure function; deletes an exclusion list and a cached `Entry` field. Nothing writes. |
| Frozen adapter contract | **UNTOUCHED.** `grep -riE "savings" nexus/internal/apps/loanschedule/contract/` → no hits. `84dc208e` does not contain that file. |
| Vector store | **UNTOUCHED.** `git diff --stat 5c4233fc..84dc208e -- .softhouse/vectors/` empty; capture numbers appear nowhere under `.softhouse/vectors/`. Brief item 5's "confirm nothing was promoted" — **CONFIRMED**. |
| Item 4 — the reversal repair | **INTACT AND DISCRIMINATING.** `Reversed`, `Reversal`, `ReleaseIDOfHoldAmount`, `IsVoid()`, the rerooted `Effect()`, identity-based hold pairing, `ErrOrphanRelease` all present. NC-3 (removing `!IsVoid()`) goes RED and reproduces the T510 doubling: `AccountBalanceOf(undone deposit) = 20000000, want 0`. |
| Item 7 — live-oracle state drift | **RECORDED EVIDENCE SURVIVES.** `captureAStream()`/`captureBStream()` are Go slice literals and the balances are `const` (`balance_test.go:187-233`). Nothing in the package reads a database. A future escheat of account 3 cannot move these numbers. **Confirmed safe.** |
| Item 5's load-bearing "engages neither setting" claim | **HOLDS, and by a stronger argument than T515 gave** — see below. |
| Idempotency-Key | Not engaged: `84dc208e` adds no HTTP handler and no money-movement POST. |

---

## Item 1 — the third arrow, re-derived

**The Java, read at the pinned checkout** [VERIFIED:
`/home/user/fineract/fineract-core/src/main/java/org/apache/fineract/portfolio/savings/SavingsAccountTransactionType.java:180-188`]:

```java
public boolean isCredit() {
    // AMOUNT_RELEASE is not credit, because the account balance is not changed
    return isCreditEntryType() && !isAmountRelease();
}
public boolean isDebit() {
    // AMOUNT_HOLD, ESCHEAT are not debit, because the account balance is not changed
    return isDebitEntryType() && !isAmountOnHold() && !isEscheat();
}
```

Exactly as the dispatch states, comments included. The Go
(`transactiontype.go`, added by `84dc208e`) is verbatim:

```go
func (t SavingsAccountTransactionType) IsCredit() bool {
	return t.IsCreditEntryType() && !t.IsAmountRelease()
}
func (t SavingsAccountTransactionType) IsDebit() bool {
	return t.IsDebitEntryType() && !t.IsAmountHold() && !t.IsEscheat()
}
```

**Both exclusions are reproduced.** But the dispatch is right that verbatim-ness is not the test —
so I enumerated instead of arguing from the shape of the code.

### The 20-type enumeration

`.softhouse/capture/t522-review-t515/zz_t522_enum_test.go.txt` builds an expectation table
transcribed **directly from the Java enum's constructor arguments**
[`SavingsAccountTransactionType.java:35-54`] and re-implements `isCredit()`/`isDebit()` from
`:180-188` in Go. It never reads the port under review.

```
=== RUN   TestT522EveryTypeAgreesWithTheJavaEnum
--- PASS
```

All 20 constants agree on `StoredValue()`, `IsCreditEntryType()`, `IsDebitEntryType()`,
`IsCredit()` and `IsDebit()`. The three-way split is:

| | types |
|---|---|
| `isCredit()` true | DEPOSIT(1), INTEREST_POSTING(3), DIVIDEND_PAYOUT(8) |
| `isDebit()` true | WITHDRAWAL(2), WITHDRAWAL_FEE(4), ANNUAL_FEE(5), PAY_CHARGE(7), OVERDRAFT_INTEREST(17), WITHHOLD_TAX(18) |
| neither | INVALID(0), WAIVE_CHARGES(6), ACCRUAL(10), INITIATE_TRANSFER(12), APPROVE_TRANSFER(13), WITHDRAW_TRANSFER(14), REJECT_TRANSFER(15), WRITTEN_OFF(16) — the eight `null`-entryType constructors — plus **ESCHEAT(19), AMOUNT_HOLD(20), AMOUNT_RELEASE(21)**, subtracted by the third arrow |

Note the Go's `EntryType()` table also matches the Java's third constructor argument exactly, and
the Go's missing values (no 9, no 11) are preserved in `savingsTxnStoredValue` with an
injectivity check at `init()`.

### Does deleting the hand-rolled list leave behaviour uncovered? — NO, and it is measured

T510's form [VERIFIED: `git show 5c4233fc:.../summary.go:149-163`]:

```go
if t.Type.IsAmountHold() || t.Type.IsAmountRelease() { continue }
switch e := t.Effect(); { ... }        // Effect() then classified by the RAW entry type
```

`TestT522OldListVsNewDerivationDiffSet` runs both forms over all 20 types:

```
=== RUN   TestT522OldListVsNewDerivationDiffSet
    DIFF ESCHEAT: T510 form = -10000, T515 shipped = 0
--- PASS   (difference set is EXACTLY {ESCHEAT})
```

**The difference set is exactly one type.** Every other type — including all eight
no-entry-type constants, which the maintenance list never mentioned — is unchanged. So the
maintenance-correct list is replaced by a derivation that is **complete**, and the one behaviour it
changes is the one it was meant to change. **Item 1: CLEAN.**

---

## Item 2 — the gate deletions, graded as if each deletion were wrong

### G-25 — DELETED. The premise was false; T513's reading is CORRECT; I re-derived it

G-25 was refused on CLAUDE.md's *"holds alter `available` only, never posted `balance`"*. T513
argued the hold row's `running_balance_derived` and the account's `account_balance_derived` are
two DIFFERENT QUANTITIES, not contradictory answers. **I verified that reading against the source
myself, and it is right.**

**`account_balance_derived` — the POSTED balance.** Nine terms, none of them a hold or a release
[VERIFIED: `SavingsAccountSummary.java:110-112`]:

```java
this.accountBalance = Money.of(currency, this.totalDeposits).plus(this.totalInterestPosted)
    .minus(this.totalWithdrawals).minus(this.totalWithdrawalFees).minus(this.totalAnnualFees)
    .minus(this.totalFeeCharge).minus(this.totalPenaltyCharge)
    .minus(totalOverdraftInterestDerived).minus(totalWithholdTax).getAmount();
```

**`running_balance_derived` — a HOLD-NET chain.** The loop **re-admits by name** the two types the
type-level classification just subtracted [VERIFIED: `SavingsAccount.java:902,912`]:

```java
if ((transaction.isCredit() || transaction.isAmountRelease())) {      // :902  release ADDS BACK
    ...
} else if (transaction.isDebit() || transaction.isAmountOnHold()) {   // :912  hold SUBTRACTS
```

These are two different formulas over two different type sets. They are **not** two answers to one
question, and Fineract is **not** internally inconsistent about holds. G-25's whole premise
("Fineract contradicts itself, so we must pick a side") is false, and the gate cited a
non-negotiable about `available` to refuse the one Fineract column that *is* available-shaped.
**Deleting it was right.**

**RESERVED test:** G-25 was ENGINEERING — answerable from source, which is how it was in fact
answered. It touches no licence fact, no cutover, no regulatory sign-off, and nothing that spends
money, exposes an endpoint or binds a third party. **No surviving RESERVED component. Nothing to
restore.**

**And nothing was quietly loosened by the deletion:** `AccountBalanceOf` still excludes holds — I
proved it by mutation (NC-2 goes RED) — so "holds alter available only" is still enforced, now by
the oracle's own classification instead of a hand-written list. The hold's effect appears only via
`HeldOf` → `AvailableOf`.

### G-26 — DOWNGRADED to a MINOR note. Correct

[VERIFIED: `SavingsAccount.java:897-898` calls `zeroBalanceFields()` on
`isReversed() || isReversalTransaction()`; `SavingsAccountTransaction.java:586-591` sets
`runningBalance = null` plus three other fields.] Fineract is unambiguous; no second derivation
disagrees; so this was a representation gap in Go, never a divergence in the answer.
`RunningBalance{Value, Valid}` carries the NULL. `Valid == false` on a void row and the chain does
not advance — both pinned by `TestAVoidRowStatesNoRunningBalanceAndDoesNotAdvanceTheChain`, and
I confirmed the Go matches the Java's "does not advance" behaviour. **Downgrade is right.**

### G-27 — DELETED. It was a live money bug, and I re-derived that from source

`ESCHEAT(19)` carries `TransactionEntryType.DEBIT` as its raw constructor argument
[`SavingsAccountTransactionType.java:52`] and is excluded from `isDebit()` **by name**
[`:185-188`]. Then:

- **`recalculateDailyBalances` matches neither branch.** `:902` re-admits `isAmountRelease()`,
  `:912` re-admits `isAmountOnHold()`, and **there is no `|| isEscheat()` term anywhere in the
  loop** [VERIFIED by reading `SavingsAccount.java:882-924` end to end]. The asymmetry is the
  proof the exclusion is deliberate: the loop knows how to re-admit an excluded type and chose not
  to for escheat.
- **`updateSummary` has no escheat term** — none of the nine [`SavingsAccountSummary.java:110-112`]
  and no calculator in `SavingsAccountTransactionSummaryWrapper` mentions it [VERIFIED: all 13
  calculator methods read; the file names no type outside DEPOSIT, DIVIDEND_PAYOUT, WITHDRAWAL,
  INTEREST_POSTING, WITHDRAWAL_FEE, ANNUAL_FEE, the fee/penalty charge and waiver pairs,
  OVERDRAFT_INTEREST and WITHHOLD_TAX].

**Both derivations agree that escheat moves nothing.** G-27's stated reason — *"two of Fineract's
three authorities agree with us"* — was false on both legs. There was no choice to make, so there
was no gate. **Deleting it was right, and the same RESERVED test comes back clean.**

**And the bug was real.** T510's `TestEscheatDebitsThePostedBalance` pinned `AccountBalanceOf == 0`
while its own comment conceded *"Fineract's stored `account_balance_derived` would still read
50000000"* [VERIFIED: `git show 5c4233fc:.../balance_test.go:192-206`, func at `:197`]. A test that states the
oracle's number in prose and asserts a different one is the exact failure T510 said it was
repairing.

---

## What I can and cannot say about `50000000` (brief item 3)

**The dispatch forbids reading the value out of the test and calling it verified. I have not.**
Here is the honest split.

**CONFIRMED FROM SOURCE — the arithmetic.** For a stream `{DEPOSIT X; ESCHEAT X}` on an account
escheated by the stock job, Fineract's two stored balances both come out at **X**, and I derived
that without the oracle:

1. `escheat()` appends a transaction whose amount is `savingsAccount.getSummary().getAccountBalance()`
   — the balance **at the moment of escheat** [VERIFIED: `SavingsAccountTransaction.java:319-328`].
2. It then calls `recalculateDailyBalances(Money.zero(currency), …)` and
   `summary.updateSummary(…)` [VERIFIED: `SavingsAccount.java:3382-3396`], i.e. **both columns are
   recomputed from the transaction list**, not decremented.
3. In that recompute, ESCHEAT matches neither branch (above), so the chain carries X forward onto
   the ESCHEAT row; and it appears in none of the nine summary terms, so `accountBalance` = X.
4. `escheat()` is called only from `savingsAccountWritePlatformService.escheat`
   [VERIFIED: `UpdateSavingsDormantAccountsTasklet.java:63`].

So for X = 500,000.00 MNT = **50000000 minor units**, the source says both columns read 50000000
after the escheat, and `TestEscheatMovesNeitherBalance` asserts exactly that. Its predecessor
asserted 0. **The direction of the fix is confirmed and the magnitude is confirmed from source.**

**`[UNVERIFIED: oracle_unreachable]` — the observation.** What I cannot confirm is that CAPTURE-A
was ever *taken*: that a running Fineract instance actually wrote rows 12 and 13 on savings account
2 with those amounts. That is an empirical claim about a database I cannot reach, and there is no
transcript in the repo (F-6). **I have NOT synthesised a golden vector and I have NOT ratified
one.** A source derivation and an oracle observation are different evidence, and item 3 asked for
the second.

**Exactly what the next oracle-reaching fire must run (R-1 / R-2):**

1. Confirm the oracle is up and **on tenant `gerege`**, not `default`:
   `GET /fineract-provider/actuator/health` → 200; `select id, identifier, timezone_id from tenants;`
   → `gerege` / `Asia/Ulaanbaatar`; `select value from c_configuration where name='rounding-mode';`
   → **4**. (Restored 2026-09-05 by OH-1 — `.softhouse/reference-oracle.md:1304-1351`.)
2. **Re-take CAPTURE-A** on `gerege`: create an MNT 0%-interest savings product, an account,
   deposit a whole-unit amount, make it escheat-eligible, run `jobId 21`, then
   `select id, transaction_type_enum, amount, running_balance_derived from
   m_savings_account_transaction where savings_account_id = <id> order by id;` and
   `select account_balance_derived, status_enum, sub_status_enum from m_savings_account where id = <id>;`
   **Commit the raw output** under `.softhouse/capture/<task>/`.
3. **Re-take CAPTURE-B** on `gerege` (deposit / holdAmount / withdrawal), same two queries plus
   `total_savings_amount_on_hold` and `on_hold_funds_derived`.
4. **Take CAPTURE-C, which does not yet exist and which F-1 needs:** deposit / holdAmount /
   **releaseAmount**, and record the `running_balance_derived` chain across the release row.
5. Re-run the `information_schema` recount for R-3 (SEVEN NOT NULL no-default columns on
   `m_savings_account_transaction`; `created_date` nullable) and product 2's
   `nominal_annual_interest_rate` / `currency_digits`.
6. Only then may any of these be promoted to `.softhouse/vectors/`, and each entry must carry the
   tenant label per `reference-oracle.md:1286-1290`.

---

## Item 5's load-bearing claim, tested — it HOLDS, and by a stronger argument

T515 argues the captures license themselves because they engage neither the wrong rounding mode
(`HALF_EVEN`, ordinal 6) nor the wrong zone (`Asia/Kolkata`). This is the claim the dispatch calls
load-bearing. **It holds, and structurally, not just numerically:**

- **Time zone — cannot be engaged, structurally.** `SavingsAccountTransaction` (`transaction.go`)
  carries **no date field at all**: `ID`, `AccountID`, `Type`, `Amount`, `Reversed`, `Reversal`,
  `ReleaseIDOfHoldAmount`. There is no clock and no date in the package, so **no assertion in it
  can be time-zone sensitive.** That is stronger than T515's "nothing here asserts a date" — it is
  "nothing here *can*".
- **Rounding — not engaged, and the argument does not need the product claim.** All pinned values
  are exact two-decimal quantities (1000.00, 400.00, 250.00, 500000.00) folded by integer addition
  and subtraction in `int64` minor units. HALF_UP and HALF_EVEN differ only at a midpoint of the
  rounding unit, and integer addition of 2dp quantities at 2 currency digits never produces one.
  **Note this survives independently of `nominal_annual_interest_rate = 0.000000`** (which I
  cannot verify — R-3): even on an interest-bearing product, the *pinned streams contain no
  INTEREST_POSTING row*, so no rounding-sensitive value is asserted either way.
- **The one +05:30-dependent number is quoted and not asserted.** `postgres.go` quotes
  `balance_number_of_days_derived = 243` and `cumulative_balance_derived = 85050`, flags them
  `[UNVERIFIED at Asia/Ulaanbaatar]`, and nothing derives from them. I checked the internal
  consistency: 350 × 243 = 85,050. ✓ No assertion anywhere depends on it.

**Verdict on the caveat handling: adequate.** The captures are correctly labelled as
non-representative, correctly kept out of `.softhouse/vectors/`, and the licensing argument
survives independent scrutiny. What it does **not** license is their *provenance* — R-2.

---

## Attribution — what is T515's and what is not

Per the dispatch, blaming T515 for the stack's lines is the base-drift defect T512 was filed to
stop. `git show --stat 84dc208e` — **seven files**: `gates.md`, one handoff, and five
`nexus/internal/apps/savings/*` files.

**T515's own:** the third-arrow port and `IsEscheat()`; the deletion of the exclusion lists from
`AccountBalanceOf`/`RunningBalancesOf`; the deletion of the `Entry` field; `IsCreditType`/
`IsDebitType`; `RunningBalance` and `HoldNetRunningBalancesOf`; the escheat test inversion; the
G-25/G-27 deletions and the G-26 downgrade. **F-1, F-2, F-3 are T515's.**

**NOT T515's — measured, so a later reader does not re-blame it:**

| observed | actually whose |
|---|---|
| `gofmt -l` reports `internal/apps/loanschedule/contract/contract.go` | Last touched by `253cfe33` / `e966ed06` / `aaa6ed00`, all long before this stack. Not in `84dc208e`. |
| `check-ledger-invariants.sh` reports **34** findings where the driver measured **8** at `84dc208e` | `23966a65` (T509) merged after T515 and broadened `balanceSynonymRe`. All 34 sites are in `loanproduct` / `loan` / `investor` / `loanschedule`; **zero in savings**, under the broader guard. |
| `PAY_CHARGE` with null `chargePaidBy` (F-5) | Present identically in T510 and T501. `84dc208e` changed nothing there. |
| The `/Users/buv/fineract` path in some in-code citations | Inherited from the T510-era text and from the task description; the driver's correction records the real path as `/home/user/fineract`. Cosmetic. |

---

## Residual for the next local fire, in one place

1. **R-1** — re-compute the escheat number **against the reference oracle**; source derivation is
   done and agrees, the observation is not. `[UNVERIFIED: oracle_unreachable]`
2. **R-2** — re-take CAPTURE-A and CAPTURE-B on tenant **`gerege`** at (19, HALF_UP) /
   Asia-Ulaanbaatar, **and commit the raw transcript** (F-6).
3. **CAPTURE-C** — a deposit/hold/**release** chain. This is what F-1's condition 2 needs and it
   does not exist today.
4. **R-3** — the `information_schema` recount and product-2 facts.
5. **R-4** — the golden-vector conformance run.
6. **R-5** — settle `PAY_CHARGE` with a null `chargePaidBy` against a real oracle row.
7. **F-1 condition 1** is available **now, with no oracle**: add the source-derived release-row
   unit test so `HoldNetRunningBalancesOf`'s third arm stops being ungraded.

---

*Reviewer artefacts: `.softhouse/capture/t522-review-t515/RUNLOG.md` (every command and its
output), `ledger-invariants.txt` (full guard run), `zz_t522_enum_test.go.txt` (the 20-type
enumeration probe). The probe was run against a scratch copy of the module; `nexus/` in this
worktree was never modified.*
