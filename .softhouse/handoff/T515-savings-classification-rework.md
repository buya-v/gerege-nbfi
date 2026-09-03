# T515 — REWORK of T510 after T513's REJECT: port the classification all the way, delete two gates

**Branch:** `softhouse/T515-savings-classification-rework`
**Based on:** `softhouse/T510-savings-fold-reversal` @ `5c4233fc` (NOT main — T510's reversal
repair is preserved wholesale).
**Reference oracle:** pinned Fineract checkout `/Users/buv/fineract` @ `426a23544`, plus **two new
live captures** from the running instance (`gerege-oracle-db` / `fineract_default`).

---

## Changes Made

### THE ROOT — one call, and most of the rest collapsed

T510 followed `isCredit()` → `isCreditType()` → `getTransactionType().isCredit()` and **stopped at
the second arrow**, binding the Go classification to the enum's RAW `entryType` field, which
Fineract never folds on. The third arrow is `SavingsAccountTransactionType.java:180-188`
[VERIFIED: read at those exact lines this fire, comments included]:

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

**`transactiontype.go`** — ported it, in the oracle's own shape:

| new method | ports | body |
|---|---|---|
| `EntryType()` | `getEntryType()` (raw) | unchanged, now documented as NOT the balance classification |
| `IsCreditEntryType()` / `IsDebitEntryType()` | `:83-89` | raw-field tests; the zero `TransactionEntryType` is Fineract's `null` |
| `IsEscheat()` | `:164-166` | new |
| `IsCredit()` / `IsDebit()` | **`:180-188`** | **the fold that was missing** |

**`transaction.go`** —
- added `IsCreditType()` / `IsDebitType()` = `Type.IsCredit()` / `Type.IsDebit()`, ports of
  `SavingsAccountTransaction.java:790-791, :798-799`;
- `IsCredit()`/`IsDebit()` = those **and** the two void conjuncts (T510's half, preserved);
- **DELETED the `Entry TransactionEntryType` field.** The oracle's entity has no `entryType` field
  and no such column — every classification method delegates to `getTransactionType()`. The Go
  field was a cached copy of a derived value sitting beside the thing it is derived from, which is
  (a) how the raw entry type got read as the classification in the first place and (b) a way for a
  caller to build a transaction whose `Entry` contradicts its `Type` and get a silently wrong
  balance. Four use sites, all inside `savings/`.

**`summary.go`** —
- **deleted the hand-rolled exclusion list** `if t.Type.IsAmountHold() || t.Type.IsAmountRelease()
  { continue }` from `AccountBalanceOf` **and** `RunningBalancesOf`. Both are now plain folds over
  `Effect()` with no type-specific knowledge in them at all. The list reached the right answer for
  holds by maintenance and the wrong one for ESCHEAT by omission;
- replaced the "THREE RATIFIED DIVERGENCES" block with the capture evidence and the two deletions;
- **added `HoldNetRunningBalancesOf(opening, txns) []RunningBalance`** — the faithful port of
  `running_balance_derived` that T513 said was owed once G-25 collapsed, including the
  `|| isAmountRelease()` / `|| isAmountOnHold()` re-admission terms and the ESCHEAT non-match;
- **added `RunningBalance{Value, Valid}`** — `Valid=false` is the oracle's NULL on a void row.
  This is T513's identified remedy for G-26, implemented. A struct, not `*MinorUnits`: a nil
  pointer on a money path is one dereference from a panic;
- `RunningBalancesOf` keeps its posted-prefix semantics but **stops advertising itself as the
  replacement for `running_balance_derived`** (T513 condition 3);
- `HeldOf` doc corrected — see MINOR-3 below;
- `AvailableOf` doc: the two hold columns' attribution is now VERIFIED rather than assumed
  [`SavingsAccountSummaryData.java:52-64`], settling T513's "incidental correction".

**`postgres.go`** —
- **MINOR-1**: the readability criterion restated as **PROVENANCE, not location** (independent
  input recorded by a command vs output of a fold over other rows), with
  `cumulative_balance_derived` named as the per-row stored balance the old wording admitted;
- **MINOR-2**: the NOT NULL disclosure recounted from `information_schema` — **seven**, not three,
  and `created_date` **dropped** because it is nullable;
- removed `t.Entry = tx.EntryType()` from the decoder;
- the `SummaryRepository` doc no longer points at the deleted D-1/D-3.

**`.softhouse/gates.md`** — G-25 and G-27 **DELETED**, G-26 **DOWNGRADED**; see below.

### PRESERVED FROM T510, UNTOUCHED

Everything T513 verified and flagged for preservation: the reversal repair itself, `Reversed` /
`Reversal` / `ReleaseIDOfHoldAmount` on the struct and in the SELECT, `IsVoid()`, the rerooting of
`Effect()` through one classification, identity-based hold pairing, `ErrOrphanRelease`, the
negative control, `TestReversedAndReversalRowsAreVoidInEveryDerivation`,
`TestAReversedHoldHoldsNothing`, and the derive-don't-store posture (no balance field, no balance
column written or read).

---

## Vectors run (pass/fail)

### Two NEW live oracle captures, taken this fire

Created through the stock API on savings **product 2 — MNT, `currency_digits` 2,
`nominal_annual_interest_rate` 0.000000** [VERIFIED: `m_savings_product` row], so no interest
posting perturbs any row.

**CAPTURE-B — account 3, `deposit` → `holdAmount` → `withdrawal`:**

| txn id | type | amount | `running_balance_derived` |
|---|---|---|---|
| 14 | 1 DEPOSIT | 1000.000000 | 1000.000000 |
| 15 | 20 AMOUNT_HOLD | 400.000000 | **600.000000** |
| 16 | 2 WITHDRAWAL | 250.000000 | **350.000000** |

`account_balance_derived` = **750.000000**, `total_savings_amount_on_hold` = **400.000000**,
`on_hold_funds_derived` = NULL.

**CAPTURE-A — account 2, escheated for its whole balance** by the stock `Update Savings Dormant
Accounts` job (jobId 21), the only caller of `SavingsAccount.escheat`
[VERIFIED: `UpdateSavingsDormantAccountsTasklet.java:63`]:

| txn id | type | amount | `running_balance_derived` |
|---|---|---|---|
| 12 | 1 DEPOSIT | 500000.000000 | 500000.000000 |
| 13 | **19 ESCHEAT** | 500000.000000 | **500000.000000 — UNMOVED** |

`account_balance_derived` = **500000.000000 — UNMOVED**; `status_enum` 600 (CLOSED),
`sub_status_enum` 300 (ESCHEAT).

**⚠ Neither is a parity vector — see Blockers.** They are exact-quantity / classification
evidence, not rounding- or date-sensitive, and neither was written to `.softhouse/vectors/`.

### Go test results

| suite | result |
|---|---|
| `go build ./...` | exit 0 |
| `go vet ./...` | exit 0, no output |
| `go test ./... -count=1` (whole module, 18 packages) | **all ok** |
| `go test ./internal/apps/savings/... -count=1` | **ok**, 20 tests |
| `gofmt -l internal/apps/savings/` | clean |
| `bash .softhouse/guards/check-ledger-invariants.sh` | **Findings: 8**, `covered: internal/apps/savings`, **ZERO savings sites** — identical to T513's baseline on the T510 tree (4 × `loanproduct` `I3-FIELD-WRITE`, 4 × `OPAQUE-SQL`) |

New tests, all passing:

| test | what it pins |
|---|---|
| `TestAccountBalanceMatchesTheCapturedOracleColumn` | `AccountBalanceOf` == `account_balance_derived` on both captures |
| `TestHoldNetRunningBalancesMatchTheCapturedOracleRows` | `HoldNetRunningBalancesOf` == `running_balance_derived`, row for row, both captures + opening-balance carry |
| `TestAVoidRowStatesNoRunningBalanceAndDoesNotAdvanceTheChain` | the NULL representation and the non-advancing chain |
| `TestRunningBalancesArePostedPrefixFoldsAndDifferFromTheHoldNetChain` | the two chains differ **by exactly the outstanding hold** — an arithmetic relation, not bare inequality |
| `TestEscheatMovesNeitherBalance` | **inversion of T510's wrong-number test** |
| `TestTheFoldedClassificationExcludesTheThreeBalanceNeutralTypes` | raw vs folded classification for all three types, with controls |
| `TestAReversedReleaseStillDischargesItsHold` | MINOR-3, the accepted fail-open |

### Negative controls (P-45) — three planted, all discriminate

A control that cannot fail is not a control, so each was run RED:

1. **drop `!t.IsEscheat()`** (reintroduce T510's exact defect) → **4 tests fail**, headline
   `CAPTURE-A: AccountBalanceOf = 0, oracle account_balance_derived = 50000000`. That is T510's
   defect reproduced to the digit and caught.
2. **drop the hold/release exclusions** → **5 tests fail**, incl.
   `CAPTURE-B: AccountBalanceOf = 35000, oracle = 75000` and
   `row 1: posted 60000 - hold-net 60000 = 0, want 40000`.
3. **drop the `||` re-admission terms from the hold-net chain** → **2 tests fail**,
   `CAPTURE-B hold: running_balance_derived[1] = 100000, oracle = 60000`.

All three reverted; control 1 re-run after the const/func refactor and still fails 4.

### ESCHEAT — before / after

For `{DEPOSIT 500,000.00; ESCHEAT 500,000.00}`:

| | `AccountBalanceOf` | per-row chain | oracle |
|---|---|---|---|
| **T510 (before)** | **0** | `RunningBalancesOf` = `[50000000, 0]` | `account_balance_derived` 50000000; `running_balance_derived` `[50000000, 50000000]` |
| **T515 (after)** | **50000000** | `RunningBalancesOf` = `[50000000, 50000000]`; `HoldNetRunningBalancesOf` = `[50000000, 50000000]` | identical |

(T510 had no hold-net function; `HoldNetRunningBalancesOf` is new in T515. The T510 figures are
T513's measurements on that tree, and I reproduced the `AccountBalanceOf = 0` half by planting
negative control 1.)

A **500,000₮ error on the operation that closes the account**, previously pinned as correct by
`TestEscheatDebitsThePostedBalance`.

---

## Money-math notes

- **Integer minor units throughout.** Every accumulator, intermediate, fixture and constant is
  `MinorUnits` (int64). `grep -rnE 'float32|float64|big\.Float|decimal\.'` over
  `internal/apps/savings/` returns **one** hit: the comment asserting their absence.
- **Holds alter `available` only** — and this is now the oracle's own rule rather than a
  re-derivation of it. `AccountBalanceOf` excludes AMOUNT_HOLD/AMOUNT_RELEASE because
  `SavingsAccountTransactionType.isCredit()/isDebit()` exclude them, and it equals the captured
  `account_balance_derived` (750.00) on a hold-bearing account.
- **Two quantities, named apart.** `account_balance_derived` is the POSTED balance;
  `running_balance_derived` is a HOLD-NET, available-shaped chain. CAPTURE-B measures the gap as
  exactly the hold (750.00 − 350.00 = 400.00 = `total_savings_amount_on_hold`). G-25 invoked
  "holds alter available only" to refuse the one column that implements it.
- **Amount stays a magnitude**; direction comes from the classification, so a negative amount
  cannot double-negate a debit. Unchanged from T510, still tested.
- **No rounding is performed anywhere in this diff.** Every operation is `+`/`-` on int64 minor
  units. No `MathContext`, no division, no scale change — so the tenant rounding-mode problem in
  Blockers does not reach this code.
- **Balances still derived, never written.** No INSERT names a balance column, no UPDATE assigns
  one, no SELECT reads one back. `HoldNetRunningBalancesOf` computes the column on demand and
  stores nothing; the guard reports zero savings sites.
- **Ships disabled.** `config.go:39` `Config{Enabled: envBool(EnvName, false)}`, untouched. NBFI
  (ББСБ) licence — deposit-taking activation prohibited, Law on Non-Banking Financial Activities
  Art. 12.1.3/12.1.4. No string in this package describes savings as insured, protected or
  guaranteed; the only hits are the prohibition in `doc.go:25-27` and the test asserting absence
  at `savings_test.go:179`.

### Gates

- **G-25 DELETED.** Premise false. The two columns are different quantities, not contradictory
  answers; the non-negotiable is satisfied by `AccountBalanceOf`; the hold-net column is now
  ported faithfully rather than refused.
- **G-27 DELETED.** Not a design choice — a live money bug. Both derivations agree that escheat
  moves nothing, confirmed by CAPTURE-A. Zero of T510's "three authorities" agreed with it.
- **G-26 DOWNGRADED** to a MINOR note. Fineract is unambiguous (NULL via `zeroBalanceFields()`)
  and no second derivation disagrees, so it was never a divergence in the answer — only a
  representation gap, and the remedy is implemented (`RunningBalance.Valid`). The note records
  that the two functions represent a void row differently, and why. It authorises no divergence.

**No `user` gate was crossed or needed.** All three rested on a checkable source claim.

### One thing I did that the task did not ask for, flagged for the reviewer

I **implemented** `HoldNetRunningBalancesOf` + `RunningBalance` rather than filing them as
backlog. T513's condition 3 says a faithful port of `running_balance_derived` "is owed (backlog is
acceptable)". I built it because I had a capture to grade it against and it is ~25 lines in the
same file; without it, deleting G-25 would leave a claim ("we could reproduce the column") that
nothing checks. If the reviewer judges this scope creep, it is severable — the gate deletions and
the ESCHEAT repair do not depend on it, though three tests do.

---

## Unverified

- **Both captures are `[UNVERIFIED at the ratified (19, HALF_UP) / Asia-Ulaanbaatar setting]`** —
  see Blockers. Labelled as such at every one of the five sites where a captured number appears
  (`transactiontype.go`, `summary.go`, `balance_test.go`, `postgres.go`, `gates.md`).
- **`balance_number_of_days_derived = 243` and `cumulative_balance_derived = 85050.000000`** are
  time-zone dependent (+05:30). Quoted in `postgres.go` only to show the column's SHAPE (a balance
  × days product); nothing derives or asserts them. `[UNVERIFIED at Asia/Ulaanbaatar.]`
- **T513's earlier hold/release/interest capture on account 1** is cited as background. I
  re-verified the rows exist and read as reported (`running_balance_derived` 600.00 on the hold
  row against `account_balance_derived` 1000.00, release row 1072.18, FK back-filled to 11), but I
  did not re-derive its interest finding.
- **The overdraft and interest arms of `recalculateDailyBalances` are NOT ported** —
  `overdraft_amount_derived`, the interest-recalculation copy path, and
  `balance_end_date_derived` / `balance_number_of_days_derived`. Stated at
  `HoldNetRunningBalancesOf`. They do not affect the balance chain it returns; I did not verify
  that claim against a capture exercising an overdraft.
- **No caller anywhere.** `AccountBalanceOf`, `RunningBalancesOf`, `HoldNetRunningBalancesOf`,
  `HeldOf` and `AvailableOf` have no reference outside `savings/`. Every behaviour in this diff is
  latent.
- **`AvailableOf` still overstates** — it covers only the transaction-stream half of one of
  Fineract's three subtrahends. Unchanged from T510; the ⚠ block is still the first paragraph of
  its doc.
- **`m_savings_account_summary` does not exist in Fineract** (`SavingsAccountSummary` is an
  `@Embeddable`), so `PostgresSummaryRepository.FindByAccountID` cannot succeed. Pre-existing,
  routed as T507, not touched.

---

## Blockers

### THE ORACLE INSTANCE IS NOT AT THE RATIFIED TENANT SETTINGS — measured, not reported

Raised by the coordinator mid-task; I re-measured it independently rather than accepting it
[VERIFIED: psql against `gerege-oracle-db`, this fire]:

```
select identifier, name, timezone_id from tenants;
  -> default | Default Demo Tenant | Asia/Kolkata          (ONE row, that is all)
select datname from pg_database;
  -> fineract_default, fineract_tenants, postgres, root, template0, template1
select name, value, enabled from c_configuration where name ilike '%round%';
  -> rounding-mode | 6 | t
```

There is **no `gerege` tenant and no `fineract_gerege` database**, and `rounding-mode = 6` is
**HALF_EVEN** (`java.math.RoundingMode`: UP=0, DOWN=1, CEILING=2, FLOOR=3, HALF_UP=4, HALF_DOWN=5,
HALF_EVEN=6, UNNECESSARY=7). CLAUDE.md ratifies **HALF_UP (4)**, precision 19,
**Asia/Ulaanbaatar**. This contradicts `.softhouse/reference-oracle.md`, which records tenant
`gerege` / `Asia/Ulaanbaatar` / `HALF_UP` and a `fineract_gerege` database.

**Effect on this task: none on the finding, some on the captures.**

- The core of T515 is a **source port** from `/Users/buv/fineract` @ `426a23544`. Unaffected.
- **No rounding occurs anywhere in this diff** — every operation is `+`/`-` on int64 minor units.
- The two captures **do not engage either setting**: amounts were supplied at two decimals or
  fewer, at 0% interest, so no midpoint arises for a rounding mode to decide; and nothing asserted
  is a date. What they establish is *which transaction types move a balance at all* — a
  classification fact. The ESCHEAT numbers (0 vs 50000000) in particular are exact whole-unit
  quantities with no midpoint involved, so the headline finding does not rest on the mode.
- **What I did NOT do:** promote either capture to `.softhouse/vectors/`, or pin any
  rounding- or date-sensitive value. Every captured number carries an explicit
  `[UNVERIFIED at (19, HALF_UP) / Asia-Ulaanbaatar]` label at its site.

**Blocked until a correctly configured tenant exists:** any savings **interest-posting** vector.
Interest is exactly where HALF_UP and HALF_EVEN diverge, and a capture taken now would be a
discrimination probe wearing a parity vector's name. Left unpinned deliberately. The coordinator
is filing tenant restoration as its own task.

### Oracle-instance data footprint

I created, in `fineract_default`: **savings product 2** (`T515 Escheat Probe MNT`, dormancy
tracking active, days 1/2/3), **savings account 2** (now CLOSED/ESCHEAT) and **savings account 3**
(active, 400.00 on hold), on the existing client 1, plus transactions 12–16. **T513's account 1
was not touched** — product 1 has `is_dormancy_tracking_active = false`, so the escheat job's
inner join excluded it; I re-read its eleven rows afterwards and they are unchanged. Nothing under
`/Users/buv/gerege-nbfi` or `/Users/buv/fineract` was modified by the capture.

⚠ **Account 3 is now escheat-eligible.** It sits on product 2 with `days_to_escheat = 3` and its
last deposit/withdrawal is dated January 2026, so the next run of jobId 21 **will escheat it** and
CAPTURE-B's rows will gain an ESCHEAT row. The captured values are recorded here and in
`balance_test.go`, so the evidence survives; but anyone re-reading account 3 from the database
should check for a type-19 row first.

---

## Follow-ups

1. **Re-capture at the ratified tenant** once `gerege` / `Asia/Ulaanbaatar` / HALF_UP / precision
   19 exists, and only then promote CAPTURE-A and CAPTURE-B into `.softhouse/vectors/`. Also
   reconcile `.softhouse/reference-oracle.md`, which currently describes a tenant and database
   that are not on this instance.
2. **Savings interest posting** — blocked on (1). It is the rounding-sensitive path and must not
   be vectored at HALF_EVEN.
3. **`PostgresTransactionRepository.Insert` cannot succeed against the adopted schema** — seven
   NOT NULL no-default columns unsupplied (`office_id`, `transaction_date`, `created_by`,
   `submitted_on_date`, `last_modified_by`, `created_on_utc`, `last_modified_on_utc`). Needs an
   office model, a business-date clock and an authenticated-user context. Account-model slice.
4. **`release_id_of_hold_amount` is never written**, so `HeldOf` refuses a hold/release stream
   this port appended itself. Needs a hold/release service.
5. **`AvailableOf` is not the withdrawable balance** — needs `min_required_balance`,
   `on_hold_funds_derived`, `total_savings_amount_on_hold`, `enforce_min_required_balance`,
   `allow_overdraft`, `overdraft_limit` on `SavingsAccount` (none present) plus a port of
   `minRequiredBalanceDerived`.
6. **The overdraft / interest arms of `recalculateDailyBalances`** — `overdraft_amount_derived`,
   `balance_end_date_derived`, `balance_number_of_days_derived`, `cumulative_balance_derived`.
   `HoldNetRunningBalancesOf` ports only the balance arm.
7. **`m_savings_account_summary` retarget** (T507) — the table does not exist; the columns live on
   `m_savings_account` keyed by `id`.
8. **A pattern worth recording:** *a `[VERIFIED:]` tag on a derivation that stops one call short of
   the definition is worse than no tag* — it converts an unfinished port into three ratified
   divergences and a wrong money number, and the next reader trusts the citation. The check is to
   follow the delegation chain to a method that does not delegate.
9. **A second one:** *when a port needs a hand-maintained exclusion list to reproduce the oracle's
   behaviour, that is evidence the classification underneath it is mis-ported.* The list is the
   symptom; it will be right for the types someone thought of and wrong for the rest.
