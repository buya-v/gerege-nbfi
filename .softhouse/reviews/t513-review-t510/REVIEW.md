# T513 — independent review of T510 (`softhouse/T510-savings-fold-reversal`)

Reviewed commit `5c4233fc` against its base `softhouse/T501-savings-i3` @ `2e1a09df`.
Reference oracle: pinned Fineract checkout `/Users/buv/fineract` @ `426a23544`, plus a **live
capture** from the running oracle instance (`gerege-oracle-db` / `fineract_default`).

## VERDICT: REJECT

**The three oracle divergences are not justified as reasoned. Their shared load-bearing premise —
"Fineract contradicts itself" — is false. G-27 collapses outright and ESCHEAT must match the
oracle; G-25's *fact* is confirmed by capture but its *justification* inverts the CLAUDE.md
non-negotiable it cites; G-26 rests on a contradiction that does not exist.**

The reversal repair itself (MAJOR-1 of T504) is **sound, well-evidenced and must be preserved**
in the rework. What fails is everything built on top of it: a mis-ported credit/debit
classification, a wrong money number pinned by a new test, and three gate entries that would
enter the program's durable record on a false reading of the source.

---

## PRIORITY ONE — the three deliberate divergences

### The load-bearing claim, attacked first: **"Fineract contradicts itself" is FALSE**

T510 rests all three gates on this (gates.md, G-25/G-26/G-27 preamble):

> Fineract is **internally inconsistent** across all three: its `account_balance_derived` and its
> `running_balance_derived` are computed by different code that disagrees. There is no option that
> matches "Fineract" — only options that match one of Fineract's two answers.

I verified this in the pinned source. It does not hold, and it fails for a specific, fixable
reason: **T510 ported Fineract's credit/debit classification only halfway.**

Fineract's classification is TWO levels deep. T510 read the first and stopped:

```java
// SavingsAccountTransaction.java:786-799   <- T510 cites this, correctly
public boolean isCredit()     { return isCreditType() && !isReversed() && !isReversalTransaction(); }
public boolean isCreditType() { return getTransactionType().isCredit(); }   // <- and stops here
public boolean isDebit()      { return isDebitType()  && !isReversed() && !isReversalTransaction(); }
public boolean isDebitType()  { return getTransactionType().isDebit(); }
```

`getTransactionType().isCredit()` is **not** the enum's `entryType` field. It is
`SavingsAccountTransactionType.java:180-188`, and Fineract's own inline comments state the
conclusion T510 spent three gate entries arguing against:

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

Go's `EntryType()` returns the **raw third constructor argument** (`isCreditEntryType()` /
`isDebitEntryType()`), and `IsCredit()`/`IsDebit()` are `Entry.IsCredit()/IsDebit() && !IsVoid()`.
Fineract never folds on the raw field.

**Measured** (probe compiled against the branch tree at `/tmp/t513tree`, temporary, not committed):

```
T510     IsDebit(ESCHEAT)              = true      Fineract isDebitType(ESCHEAT)      = false
T510     IsDebit(AMOUNT_HOLD)          = true      Fineract isDebitType(AMOUNT_HOLD)  = false
T510     IsCredit(AMOUNT_RELEASE)      = true      Fineract isCreditType(AMOUNT_RELEASE) = false
```

The `[VERIFIED: SavingsAccountTransaction.java:786-799]` tag in `transaction.go` sits on a
derivation that stops one call short of the definition. That is the root of all three gates.

---

### G-25 — a hold moves `running_balance_derived` — **FACT CONFIRMED BY CAPTURE; JUSTIFICATION REJECTED**

I did not settle this by argument. I captured it from the live oracle: a client, a savings
product, an activated account, a deposit of 1000, a `holdAmount` of 400, an interest posting, and
a `releaseAmount`. Raw rows:

| step | txn id | type | amount | `running_balance_derived` | `account_balance_derived` | `total_savings_amount_on_hold` |
|---|---|---|---|---|---|---|
| deposit | 1 | 1 | 1000.00 | 1000.00 | 1000.00 | NULL |
| **hold** | 2 | **20** | 400.00 | **600.00** | **1000.00** | **400.00** |
| after postInterest | 3–10 | 3 | … | 609.25 … 672.18 | 1072.18 | 400.00 |
| **release** | 11 | **21** | 400.00 | **1072.18** | **1072.18** | **0.00** |

The hold row carried 600.00 **immediately after the bare `holdAmount` call**, before any interest
posting, and `recalculateDailyBalances` re-derived the same treatment and propagated it forward.
The hold's `release_id_of_hold_amount` was back-filled with `11`. So T510's factual premise —
Fineract's running balance moves on a hold — is **observed, not merely argued**. Credit where due:
the oracle fixture in `TestRunningBalances…DivergeFromTheOracleOnHolds`,
`{100000, 60000, 35000, 35321}`, matches the capture on the hold row exactly.

**But the capture also refutes the interpretation.** These are not two contradictory answers to
one question. They are **two different, well-defined quantities**, and the gap between them is
exactly the hold (1072.18 − 672.18 = 400.00):

- `account_balance_derived` — the **posted** balance. Holds never touch it. Fineract says why, in
  source: *"AMOUNT_HOLD … not debit, because the account balance is not changed."*
- `running_balance_derived` — a **hold-net**, i.e. **available-shaped**, per-row chain. Holds are
  subtracted, releases added back.

Now read the non-negotiable T510 invokes to refuse it:

> **Holds are postings and alter `available` only, never posted `balance`.**

Correctly applied, it is already satisfied — by `AccountBalanceOf`, which excludes holds and
matches `account_balance_derived` exactly. It does **not** forbid reproducing
`running_balance_derived`; it *describes* it. **G-25 cites the non-negotiable to refuse the one
Fineract column that implements it.** That is the distinction the task statement warned might be
elided, and it is elided: `running_balance_derived` on a transaction row is not the account's
posted balance, and T510 treats them as the same object.

**Which governs — oracle fidelity or the non-negotiable?** The question does not arise, because
they do not conflict. Oracle fidelity governs `RunningBalancesOf`; the non-negotiable governs
`AccountBalanceOf`; each has its own Fineract column and the port already gets one of them right.

**Blast radius, stated honestly from the capture rather than inflated.** I expected this to
corrupt interest, since `SavingsAccountInterestPostingServiceImpl.java:382,399` reads
`tx.getRunningBalance()`. The capture says otherwise: the April posting of 10.34 corresponds to
~1009.25 over 31 days at 12%, **not** to the running balance of 609.25. So interest was computed
on the balance *including* the held amount and the divergence does **not** corrupt interest
amounts. The cost is statement rendering and row-level vector parity. I record this because it
makes G-25 less severe than my source reading first suggested.

**Verdict: MUST MATCH THE ORACLE — via a correctly named derivation.** `RunningBalancesOf` may
keep its posted-balance-prefix semantics, but it must stop advertising itself as "the replacement
… for `running_balance_derived`", and a faithful port of that column is owed (backlog is
acceptable; a ratified "we will never reproduce it" is not).

### G-26 — a void row states NULL — **NOT A DIVERGENCE; THE PREMISE DOES NOT APPLY AT ALL**

Verified: `zeroBalanceFields()` sets `this.runningBalance = null`
(`SavingsAccountTransaction.java:586-591`), called from `SavingsAccount.java:897-898`. Fineract is
**unambiguous** here. There is no second, disagreeing derivation — `account_balance_derived`
simply excludes the row, which is not a contradiction of "this row states no running balance".

So G-26 is filed under a preamble ("Fineract contradicts itself") that has **no application to
it**. What it actually is: a **representation gap** — `[]MinorUnits` has no NULL. The gate text
even identifies the correct remedy (`[]*MinorUnits` or a validity mask) and rejects it on the
ground that "nobody renders a balance for that row anyway" — an argument that the divergence is
*harmless*, not that it is *right*.

**Verdict: DIVERGENCE UNJUSTIFIED AS REASONED, but low severity.** Downgrade from "ratified
divergence" to "known representation gap, remedy identified". The entry must stop citing a
contradiction that does not exist. Graded MINOR, not MAJOR.

### G-27 — `ESCHEAT` — **COLLAPSES. MUST MATCH THE ORACLE.**

This is the sharpest failure. Trace ESCHEAT through `recalculateDailyBalances`
(`SavingsAccount.java:895-919`):

- `transaction.isCredit()` → false (not a credit entry type)
- `transaction.isAmountRelease()` → false
- `transaction.isDebit()` → **false** — `isDebitType()` is `type.isDebit()`, which is
  `isDebitEntryType() && !isAmountOnHold() && !isEscheat()`
- `transaction.isAmountOnHold()` → false

**Neither branch is taken.** `transactionAmount` stays `Money.zero`, `runningBalance` is
unchanged, and `transaction.setRunningBalance(runningBalance)` writes the unchanged prefix. Note
the asymmetry that settles it: the loop carries an explicit `|| transaction.isAmountOnHold()` term
to re-admit holds after `isDebit()` excludes them, and carries **no `|| isEscheat()` term**. The
exclusion of ESCHEAT is deliberate and complete.

And `account_balance_derived` does not move either: I read all twelve calculators in
`SavingsAccountTransactionSummaryWrapper` — none mentions ESCHEAT — and the
`updateSummaryWithPivotConfig` switch has no ESCHEAT case.

**Both derivations agree. There is no contradiction, and therefore no choice to make.**

G-27's stated reason (a) — *"two of Fineract's three authorities — the entry-type classification
and the running-balance derivation — agree with us, and only the stored aggregate does not"* — is
**factually false on both legs**. The entry-type classification (`isDebitType()`) excludes ESCHEAT
by name; the running-balance derivation does not move on it. **Zero of the three agree.**

Measured on the branch tree, `{DEPOSIT 500,000.00; ESCHEAT 500,000.00}`:

```
T510     AccountBalanceOf   = 0             Fineract account_balance_derived = 50000000
T510     RunningBalancesOf  = [50000000 0]  Fineract running_balance_derived = [50000000 50000000]
```

A **500,000₮ divergence on the operation that closes the account**, now locked in by
`TestEscheatDebitsThePostedBalance`. This is precisely the failure T510 said it was repairing for
MINOR-2: *"a test that pins a wrong number is worse than none."* It wrote one.

Reason (b) — "that stored aggregate is exactly the artefact I-3 refuses, so 'match it' is the one
instruction this port cannot follow" — does not survive either. Matching the oracle here means
**folding ESCHEAT to zero**, i.e. computing a number, not reading `account_balance_derived`. I-3
is not engaged at all.

**Verdict: MUST MATCH THE ORACLE.** Delete G-27, fold ESCHEAT to zero, invert the test.

---

## MAJOR findings

### MAJOR-1 — `isCreditType()` / `isDebitType()` are ported incompletely, and it is the root of all three gates

Detailed above. The practical shape of the defect: because the classification is wrong,
`AccountBalanceOf` hand-rolls an exclusion list —

```go
if t.Type.IsAmountHold() || t.Type.IsAmountRelease() {
    continue
}
```

— which reaches the **right** answer for holds by maintaining a list, and the **wrong** answer for
ESCHEAT because ESCHEAT is missing from that list. `RunningBalancesOf` carries the same list with
the same omission.

Porting the classification properly fixes both at one root and **deletes the special case**, which
is exactly the virtue T510 claims for rerooting `Effect()` ("fixes all four derivations at their
common root rather than at four call sites"). It applied that principle to the reversal conjuncts
and not to the type conjuncts.

**Failure scenario:** a dormant account with 500,000₮ is escheated. Fineract reports 500,000₮ on a
CLOSED account; this port reports 0₮. Any reconciliation or FRC report built on the Go module
disagrees with the oracle by the full balance on every escheated account, and the golden vector
that catches it will be "fixed" toward the Go number, because G-27 tells the next reader the
divergence is ratified.

### MAJOR-2 — three gate entries would enter the program record on a false source claim

G-25/G-26/G-27 share a preamble asserting internal inconsistency in Fineract. It is false for
G-26 (no second derivation exists), false for G-27 (both derivations agree), and a
mischaracterisation for G-25 (two different quantities, not two answers). Gate entries are
durable and are cited by later agents as settled reasoning; CLAUDE.md makes a ratified gate
un-amendable by an agent without raising a new one. Shipping these as written licenses further
"Fineract contradicts itself, so we choose" divergences on a premise that does not hold.

### MAJOR-3 — G-25 mis-states the non-negotiable it invokes

Detailed above. `running_balance_derived` is an available-shaped chain, not the posted balance.
Invoking *"holds alter `available` only"* to refuse moving it inverts the rule. The gate's closing
line — "Overrule if a vector-parity policy should outrank a CLAUDE.md non-negotiable (G-25)" —
frames a conflict that does not exist and invites Buyan to adjudicate a false dilemma.

---

## MINOR findings

### MINOR-1 — the per-row-fact / aggregate criterion is unsound as written

T510's governing rule, written into `postgres.go` under "A FACT ABOUT A POSTING IS NOT A BALANCE":

> These three columns are facts about a single row — flags and a foreign key, not sums, not
> aggregates … `account_balance_derived` and `running_balance_derived` are **aggregates of other
> rows**, which is exactly why they stay unread.

**Counterexample, as requested — a per-row fact that is nonetheless a stored balance.** From the
live adopted schema, `m_savings_account_transaction` carries four derived columns, all stored
per-row:

```
 balance_end_date_derived       | date
 balance_number_of_days_derived | integer
 running_balance_derived        | numeric
 cumulative_balance_derived     | numeric
```

`cumulative_balance_derived` is a **stored balance living on a single row**. Under the stated rule
("per-row facts are readable; aggregates of other rows are not") it is readable. It must not be.
And the rule misdescribes its own primary example: `running_balance_derived` is *not* an aggregate
*of other rows* in the storage sense — it is one number on one row.

The sound criterion is **provenance, not location**: `is_reversed`, `is_reversal` and
`release_id_of_hold_amount` are **independent inputs** recorded by a command; the refused columns
are **outputs of a fold over other rows** that happen to be stored per-row. The conclusion T510
reaches is right; the rule it writes down for future readers is not, and it is written at the site
precisely so it will be reused.

### MINOR-2 — the NOT NULL disclosure undercounts by more than half, and one named column is nullable

The task asked me to confirm the INSERT still omits three NOT NULL columns. I measured it against
the **live adopted schema**, not the changelog:

```sql
select column_name, is_nullable, column_default from information_schema.columns
where table_name='m_savings_account_transaction' and is_nullable='NO';
```

NOT NULL **with no default** and omitted from `PostgresTransactionRepository.Insert`:
`office_id`, `transaction_date`, `created_by`, `submitted_on_date`, `last_modified_by`,
`created_on_utc`, `last_modified_on_utc` — **seven**, not three.

And `created_date`, which T510 names as one of its three blockers, is **nullable** in the adopted
schema:

```
 created_date | YES |
```

**Credit where due:** the disclosure is *prominent*, not buried — it is a `⚠` block on `Insert`
itself, states the statement "cannot succeed against the adopted schema", and explains why the
author declined to invent values. That is the right shape and it is not the T508 failure mode. But
the **count is wrong**, and it is wrong because it was taken from the Liquibase XML rather than
from the schema the statement must satisfy. P-104: the cardinal rested on reading a changelog, not
on querying the database.

### MINOR-3 — `HeldOf` fails OPEN on a reversed release, contradicting its own "fails closed" claim

Measured on the branch tree: hold id 2 paired to release id 3, with the **release** carrying
`Reversed = true`:

```
HeldOf(hold paired to a REVERSED release) = 0, err = <nil>
AvailableOf                               = 100000, err = <nil>
```

The void conjunct is applied on the orphan-detection side (`t.Type.IsAmountRelease() && !t.IsVoid()`)
but **not** on the discharge side: `IsHoldNotReleased()` only tests `ReleaseIDOfHoldAmount == 0`.
So a release that was voided still discharges its hold, and the funds read as drawable.

T510 reasoned explicitly about the void **hold** case ("the pairing … does not stop being true
when the hold is reversed") and did not consider the void **release** case. In mitigation this is
**oracle-faithful** — `isAmountOnHoldNotReleased()` also ignores the release's reversal — so I am
not asking for a divergence. But the function is advertised as failing closed on money and on this
input it fails open, and the doc should say which.

---

## PRIORITY TWO — what I verified and upheld

### The RED evidence — **REPRODUCED EXACTLY, not taken on trust**

I materialised the unmodified T501 tree and planted the two-plain-deposit probe T510 describes:

```
$ go test ./internal/apps/savings/ -run TestT513RedReproduction -v
    t513red_test.go:14: AccountBalanceOf(undone deposit) = 20000000, want 0
--- FAIL
```

`20000000` minor units — T510's figure to the digit. The claim that the two rows are
*indistinguishable* before the fix is also true: `Reversed`/`Reversal` exist on no struct and in
no SELECT on that tree, so two plain `TxnDeposit` fixtures are the honest encoding of the RED
state. Claim upheld.

### The negative control (P-45) — **EXISTS AND GENUINELY DISCRIMINATES**

A control that cannot fail is not a control, so I made it fail. Planting the degenerate "fix"
`func (t SavingsAccountTransaction) IsVoid() bool { return true }`:

```
=== RUN   TestReversedAndReversalRowsAreVoidInEveryDerivation
    balance_test.go:346: AccountBalanceOf(mixed) = 0, want 3000000
    balance_test.go:352: running[0] = 0, want 5000000
    balance_test.go:352: running[1] = 0, want 5000000
    balance_test.go:352: running[2] = 0, want 5000000
    balance_test.go:352: running[3] = 0, want 3000000
--- FAIL
```

Five assertions fire on the mixed stream. A fix that voids everything cannot pass. Claim upheld.

### `Effect()` rerooted — **VERIFIED**

One root (`IsDebit()`/`IsCredit()`) serves `AccountBalanceOf`, `RunningBalancesOf` and, through
them, `AvailableOf`; `HeldOf` carries the void test explicitly because it does not go through
`Effect()`. The switch is exhaustive over the three-valued domain with `default: return 0`.
`INVALID(0)` is correctly added to the no-entry-type list — and the reasoning given for it (it is
the Go zero value, so it is what an uninitialised struct carries) is right and better than T504's.
**Caveat:** the rerooting is correct in structure but the root itself is the wrong function —
MAJOR-1.

### MINOR-2's divergence-pinning test — **CHECKED, AND IT PINS THE RIGHT NUMBER**

`TestRunningBalancesArePrefixFoldsAndDivergeFromTheOracleOnHolds` asserts our column, asserts the
oracle's alongside, and fails if they ever agree. The mechanism is sound. And the oracle fixture
`{100000, 60000, 35000, 35321}` is **confirmed by my capture** on the hold row (1000 − 400 = 600).
This is the one place T510's oracle number is right and it was right for the right reason.

### MINOR-4's scope reasoning — **HONEST, NOT CONVENIENT**

I checked rather than accepted it. `SavingsAccount` in Go has exactly **seven** fields — `ID`,
`ExternalID`, `Status`, `DepositType`, `CurrencyCode`, `Summary`, `InterestRateChart`. **None** of
the six the completion needs (`min_required_balance`, `on_hold_funds_derived`,
`total_savings_amount_on_hold`, `enforce_min_required_balance`, `allow_overdraft`,
`overdraft_limit`) is present, and `minRequiredBalanceDerived` subtracts the overdraft limit, so a
faithful port needs the overdraft pair too. Completing `AvailableOf` **is** an account-model slice
and the scope guard does forbid it in a ledger-invariant task. The weaker form was the right call.

The warning is the **first** paragraph of the doc, names the concrete 300,000₮ overstatement,
prints Fineract's three-subtrahend formula with the column behind each term, and states that it
must not be wired to a withdrawal authorisation. **Nothing calls it**: there is no reference to
`AvailableOf`, `HeldOf`, `AccountBalanceOf` or `RunningBalancesOf` anywhere outside the savings
package. Defect is latent.

*Incidental correction from the capture:* `on_hold_funds_derived` stayed NULL throughout while
`total_savings_amount_on_hold` moved 400 → 0. The savings-hold column is the latter. This does not
change the conclusion — both are unported — but the doc attributes guarantor/loan holds to
`on_hold_funds_derived` and that attribution is untested here.

### `ErrOrphanRelease` — fails closed on the case it was built for

Pairing by `release_id_of_hold_amount` is oracle-faithful (`isAmountOnHoldNotReleased()`,
`:898-899`), and the capture confirms Fineract really does back-fill the FK onto the hold row
(hold id 2 → `release_id_of_hold_amount = 11`). The duplicated-release scenario returns a typed
error, `AvailableOf` propagates it, and the disclosed §4B gap (this port cannot write the FK, so it
refuses its own writes) over-holds rather than over-releases. **Except on a reversed release** —
MINOR-3.

### Counts and non-negotiables — re-run, not read (P-104)

| check | command | result |
|---|---|---|
| guard | `bash .softhouse/guards/check-ledger-invariants.sh` (branch tree) | **Findings: 8**, `covered: internal/apps/savings`, **zero savings sites** — 4 × `loanproduct` `I3-FIELD-WRITE`, 4 × `OPAQUE-SQL` |
| build | `go build ./...` | exit 0 |
| tests | `go test ./internal/apps/savings/...` | `ok` |
| float | `grep -rnE 'float32\|float64\|big\.Float' internal/apps/savings/` | 1 hit — the comment asserting their absence |
| insurance strings | `grep -rniE 'insured\|protected\|guaranteed'` | 4 hits — the prohibition in `doc.go:25-27` and the test asserting absence in `savings_test.go:179`. No user-facing string added by this diff |
| ships disabled | `config.go:39` | `Config{Enabled: envBool(EnvName, false)}` — default false, untouched |
| scope | `git show --stat` | 8 files: savings package + `.softhouse/gates.md` + handoff. **No `tasks.json`, no `.softhouse/guards/`** |

Integer minor units hold throughout: every accumulator, intermediate and fixture is `MinorUnits`
(int64); no decimal literal on a money path. Holds alter `available` only in `AccountBalanceOf`,
which is correct and matches the captured `account_balance_derived`.

---

## Conditions for merge

1. **MAJOR-1 — port `isCreditType()` / `isDebitType()` completely.** Add the three type-level
   exclusions (`!isAmountRelease()` on credit; `!isAmountOnHold() && !isEscheat()` on debit) at the
   classification, and delete the hand-rolled `IsAmountHold() || IsAmountRelease()` special case
   from `AccountBalanceOf` and `RunningBalancesOf`, which it makes redundant. Blocking.
2. **G-27 — delete the gate; fold ESCHEAT to zero.** Invert `TestEscheatDebitsThePostedBalance` to
   assert `AccountBalanceOf == 50000000`, citing
   `SavingsAccountTransactionType.java:185-188` and its comment. Blocking.
3. **G-25 — rewrite.** Drop "Fineract contradicts itself". State the two quantities and the
   captured evidence. Remove the claim that matching would breach a non-negotiable; the
   non-negotiable is satisfied by `AccountBalanceOf`. Stop advertising `RunningBalancesOf` as the
   replacement for `running_balance_derived`, and raise a faithful port of that column as backlog.
   Record that interest is **not** computed on the running balance (captured), so the divergence
   costs vector parity, not interest. Blocking.
4. **G-26 — reclassify** as a representation gap with an identified remedy, not a ratified
   divergence. Non-blocking if 1–3 are done.
5. **MINOR-1** — restate the readability criterion as provenance (independent input vs derived
   output), and name `cumulative_balance_derived` as the per-row column the old wording would have
   let through.
6. **MINOR-2** — correct the count to seven, drop `created_date`, and take the list from
   `information_schema`.
7. **MINOR-3** — either test the release's void flag on the discharge side, or state at `HeldOf`
   that a reversed release still discharges its hold and that this is oracle-faithful.

**Preserve in the rework:** the reversal repair, the two flags and the FK on the struct and in the
SELECT, `IsVoid()`, the rerooting of `Effect()`, the identity-based hold pairing, `ErrOrphanRelease`,
the negative control, and the divergence-pinning mechanism in
`TestRunningBalances…DivergeFromTheOracleOnHolds`. All of these are correct and independently
verified above. The rejection is about what was built on top of a half-ported classification, not
about the repair T510 was sent to make.

---

## What I searched, so "not found" is a statement about the search

- **The contradiction claim:** read `SavingsAccountSummary.updateSummary` and
  `updateSummaryWithPivotConfig` in full; read all twelve calculators of
  `SavingsAccountTransactionSummaryWrapper` end to end; read `recalculateDailyBalances`
  (`SavingsAccount.java:882-940`) statement by statement; read
  `SavingsAccountTransaction.isCredit/isDebit/isCreditType/isDebitType/zeroBalanceFields/isAmountOnHoldNotReleased/updateReleaseId`;
  read `SavingsAccountTransactionType` in full including the enum table and the type-level
  `isCredit()`/`isDebit()` that T510 did not reach. Enumerated the callers of
  `recalculateDailyBalances` (14 non-test sites) and of `getRunningBalance()`.
- **Live capture:** built a savings account on the oracle instance from scratch (the savings tables
  were empty) and dumped `m_savings_account_transaction` and `m_savings_account` after deposit,
  after hold, after interest posting and after release. All figures in the G-25 table are raw psql
  output. Footprint: client 1, savings product 1, savings account 1, 11 transactions in
  `fineract_default`. Nothing under `/Users/buv/gerege-nbfi` or `/Users/buv/fineract` modified.
- **Schema:** queried `information_schema.columns` on the adopted schema for NOT NULL columns and
  for every balance-shaped per-row column, rather than reading the Liquibase changelog.
- **RED / control / edge probes:** three temporary Go tests, in throwaway copies of the T501 and
  T510 trees under `/tmp`, each run and each reported above with its actual output. All reverted;
  none committed.
- **Callers:** `grep` for all four derivations across `nexus/` outside the savings package — zero.
  Every money defect found here is latent.
- **Not re-done, per the task statement:** the stored-balance reinstatement check, the guard-count
  census and the build/test/float sweep were verified independently anyway (table above) and agree
  with the driver.
- **Not searched / out of scope:** the four `loanproduct` `I3-FIELD-WRITE` sites; the four
  `OPAQUE-SQL` sites; the `m_savings_account_summary` retarget (T507); the journal-entry INSERT
  (T508); the guard's SELECT blind spot (T509, for which T510's §4C measurement is a genuine
  contribution and is correct as far as I checked it).
