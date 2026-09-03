# T516 — T514's three blocking C-2 findings on T511

**Branch:** `softhouse/T516-t514-conditions`, based on `softhouse/T511-t505-conditions` (`fc35f4eb`).
**Merge base with main:** `14cf6c1f`. Scope checked with `git diff --stat $(git merge-base main HEAD)..HEAD`.
**Diff of my own work:** four files, all in `nexus/internal/apps/loanproduct/`, plus this handoff.
**Code changed:** none. Every edit is a comment or a test's doc comment. No rename, no arithmetic.

T514's C-1 (the guard-patch withdrawal) is untouched and stays unmistakable. The three blocking
findings were all on C-2, and all three were about *what the package says the argument is*.

---

## Changes Made

### The headline change: the posting-stream test is RETIRED, not reworded

T511 rested the whole I-3 defence on one criterion — *"is there a posting stream?"* — and ranked the
parity/snapshot argument beneath it as "corroboration". T514 showed the criterion is both factually
false and ill-defined. I did not patch its statement. **I retired it**, next to the already-retired
column argument, and re-founded the conclusion on the two legs that survive.

`doc.go`'s section `# THE TEST THAT DECIDES IT` is now **TWO LEGS**, ranked, with LEG 1 first:

- **LEG 1 — PARITY (load-bearing).** Applying I-3's remedy to this cell *changes the money*: the
  oracle refreshes `InterestPeriod.outstandingLoanBalance` only at explicit sweeps and deliberately
  reads it stale in between. This leg is **executable** —
  `TestOutstandingLoanBalanceIsASweptSnapshot` goes red on the derive-on-read shape. It needs no
  taxonomy of what a "balance" is.
- **LEG 2 — REACHABILITY.** The value reaches no journal entry, no GL posting and no column any
  aggregate reads as an account balance. Forward trace terminates in DTOs; the oracle's `calc`
  package emits no journal entry at all.

The promotion T514 asked for is done and *said out loud* in the text: doc.go now records that the
earlier ranking was inverted and why (a test executes LEG 1; a wrong answer is a failing build
rather than a losing argument).

The whole T501/savings reconciliation was rewritten to run on **LEG 2**, because the retired
criterion used to carry it: `SavingsAccountSummary.AccountBalance` *is*
`m_savings_account_summary.account_balance_derived`, a persisted balance column the account is read
from, so I-3 bites there and T501 was right. Same guard class, opposite disposition, one criterion —
and now a criterion that survives the counterexample below.

### MAJOR-1 — the false headline is gone, and its refutation is recorded

Deleted: *"No transaction is summed to produce it and none could be."*
It is **false**, and the function it annotated is where it fails. Now recorded under
`## RETIRED 2` in doc.go with the full chain:

| link | citation | status |
|---|---|---|
| the cell folds the previous period's paid principal | `InterestPeriod.java:178` — `.plus(previousRepaymentPeriod.get().getPaidPrincipal(), getMc())` | [VERIFIED] |
| the Go port reproduces the fold | `interestperiod.go:282` — `plus(previous.PaidPrincipal())`, last summand of the first-segment branch | [VERIFIED] |
| paidPrincipal is accumulated, not projected | `RepaymentPeriod.java:405-407` — `addPaidPrincipalAmount` | [VERIFIED] |
| its only producer | `ProgressiveEMICalculator.java:421` — `rp.addPaidPrincipalAmount(finalPrincipalAmount)` inside `payPrincipal` | [VERIFIED] |
| whose callers walk real LoanTransactions | `AdvancedPaymentScheduleTransactionProcessor.java:929, :967, :2912` — all three are `emiCalculator.payPrincipal(...)`; `:929` sits inside a loop over `installmentToBeProcessed` driven by `loanTransaction`, and `:2912`'s `paidPortion` comes from `processPaymentAllocation(…, loanTransaction, …)` at `:2908` | [VERIFIED] |
| and balanceCorrectionAmount is a negated paid principal at 2 of its 6 sites | `ProgressiveEMICalculator.java:922` `effectivePaidPrincipal.negated()`, `:952` `paidPrincipal.negated()` | [VERIFIED] |

T514 cited the Go fold as `interestperiod.go:266`. **Corrected: it is `:282` after this branch's
comment edits, and it was `:267` on T511's tree** — `:266`/`:281` is the `minus(previous.DuePrincipal())`
line immediately above. The finding is unaffected; the line is. doc.go therefore now cites the
*expression*, `plus(previous.PaidPrincipal())`, and flags the line number as drift-prone.

Evidence item 3 (`balanceCorrectionAmount` is a signed delta) is kept but carries an explicit
"NOTE PRECISELY WHAT THIS ITEM DOES NOT SAY": *signed delta* is a claim about **sign discipline**,
never about **provenance**. Reading it as provenance is exactly what let the false headline sit five
lines above its own refutation.

### MAJOR-2 — how I resolved the boundary problem

**I did not fix the test's statement. I retired the test**, because I could not find a reading of it
that is right at the boundary, and T514's counterexample is why.

`m_loan.principal_outstanding_derived` is a persisted outstanding-principal column
[VERIFIED: `LoanSummary.java:62-63` — `@Column(name = "principal_outstanding_derived", scale = 6, precision = 19)`],
computed at `LoanSummary.java:203-204` from `calculateTotalPrincipalRepaid`, which folds **schedule
installments**, not postings [VERIFIED: `LoanSummary.java:339-346` — the loop is over
`List<LoanRepaymentScheduleInstallment>`].

- **DIRECT reading** ("the cell's own defining expression must fold postings"): the test **clears**
  that column. Plainly the wrong answer — it is exactly the shape I-3 governs.
- **TRANSITIVE reading** ("some ancestor in the dataflow folds postings"): it **condemns** that
  column correctly — the installment's `principal_completed_derived`
  [VERIFIED: `LoanRepaymentScheduleInstallment.java:72-73`] is written by `payPrincipalComponent`
  [VERIFIED: `:672`] from a `LoanTransaction`, called at
  `AdvancedPaymentScheduleTransactionProcessor.java:932, :948, :970`. But it then **condemns the four
  sites too**, because `paidPrincipal` is transaction-driven exactly one hop away by MAJOR-1's chain.

Nothing in the criterion supplies a stopping rule that admits one hop and refuses two. Both readings
are wrong somewhere, so **rewording the premise cannot save it** and the criterion is retired.

**Why LEG 2 does not inherit the defect** — this is the load-bearing distinction and doc.go states it
explicitly, so nobody makes the same mistake a third time:

> The posting-stream test asked a **BACKWARD** question about **ancestry**, with no stopping rule.
> Reachability asks a **FORWARD** question with an **ENUMERABLE TERMINAL SET**: you stop at the
> terminals and you list them.

That is also why LEG 2 is mechanisable, and it names the go/types discriminator doc.go already
prescribes as precisely its mechanisation — which ties the "bar stays red" position to the argument
instead of leaving it a separate assertion.

I also had to defend LEG 2 against the charge that it is the retired column argument renamed.
doc.go now says why it is not: LEG 2 **does not claim the cells are unpersisted** (they are — both go
into `m_loan_progressive_model.json_model` and come back). It claims the persistence is a **closed
loop**: written by the projection, reloaded as the *same* projection's starting state, with nothing
outside `loanproduct.calc` reading a balance out of it.

### MAJOR-3 — the falsifiable test's own doc comment

`interestperiod_test.go` no longer says *"never becomes a database column"*, and no longer cites
doc.go as evidence for a claim doc.go itself refutes. It now:

1. states the surviving reason (parity break — the prescription changes money, and this test is what
   makes that a failing build rather than an argument);
2. carries a **DO NOT SUBSTITUTE EITHER RETIRED ARGUMENT** paragraph naming *both* dead arguments
   with their counterexamples inline, because this comment is the text someone reads at the exact
   moment they consider making the change the test exists to stop.

### The three other places the retired criterion was restated

C-2 was applied to doc.go only; the criterion also lived in three code comments, all corrected:

- `interestperiod.go` — the struct field comment on `balanceCorrectionAmount` / `outstandingLoanBalance`
- `interestperiod.go` — `UpdateOutstandingLoanBalance`'s doc comment (the function that refutes it)
- `interestperiod.go` — `AddBalanceCorrectionAmount`'s doc comment
- `repaymentperiod.go` — the inline comment at the `copyWithoutPaidAmounts` write

A grep for `posting stream` / `never becomes a database column` across the package now returns only
retirement text.

---

## The corrected guard census — and a P-104 hit inside the section diagnosing P-104

T511 §4(1) wrote: **"6 balance-in-substance assignments exist in the tree; the guard reports 4."**
Both halves are wrong, and the section they are in is T511's own diagnosis of the guard's counting
weakness. Every number below was re-run on this branch.

**The guard reports 7, not 4** — and T511's own handoff prints the 7-line transcript at
`.softhouse/handoff/T511-t505-conditions.md:145-151` while its prose at `:217` says 4. The prose
contradicts the transcript eleven lines above it. [VERIFIED: `check-ledger-invariants.sh` re-run on
this branch]

```
[I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:277:4   <- was :262
[I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:288:2   <- was :273
[I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:327:2   <- was :305
[I3-FIELD-WRITE] internal/apps/loanproduct/repaymentperiod.go:562:4  <- was :558
[I3-FIELD-WRITE] internal/apps/savings/postgres.go:243:7
[I3-FIELD-WRITE] internal/apps/savings/postgres.go:302:5
[I3-FIELD-WRITE] internal/apps/savings/summary.go:53:2
```

(The four loanproduct lines moved only because this branch added comment lines above them. Same four
writes, byte-identical.)

**T511's census grep is the thing that measured 4, and it measured its own vocabulary.** The pattern

```
'\.[a-zA-Z0-9_]*[Bb]alance[a-zA-Z0-9_]* *=[^=]'
```

requires optional spaces then `=`, so it cannot match:

- **compound assignment** — `s.AccountBalance += effect` at `nexus/internal/apps/savings/summary.go:53`,
  which is *the write T514's C-1 counterexample is built on* and which doc.go quotes verbatim two
  sections later. The grep walked past the file its own document is arguing about.
- **multi-value assignment** — `if t.RunningBalance, err = …` (`savings/postgres.go:243`) and
  `if s.AccountBalance, err = dec(fields[12])` (`:302`).

Widening the pattern to `… *([-+*/%&|^]|<<|>>)?=[^=]` recovers `summary.go:53`; the two `, err =`
forms need a different pattern again. **That is P-104 in the section diagnosing P-104**: a counted
claim resting on one pattern match measured that pattern's vocabulary, not the code, inside the
paragraph arguing that the guard's counting is unreliable.

**Corrected figures:**

| figure | value | basis |
|---|---|---|
| reported by the guard, class `I3-FIELD-WRITE` | **7** | guard transcript, re-run |
| balance writes in substance | **>= 9** | the 7, plus `loanschedule/emi.go:1720, :1726` — `s.outstandingMinor = maxInt64(0, …)`, the same oracle method, green solely because the field was spelled without "balance" |
| structurally invisible to the guard | **6** | composite-literal keys `writeTarget` never visits: `interestperiod.go:384, :385, :409, :410`; `repaymentperiod.go:96, :97` |

`>= 9` is a **floor**, deliberately. It is what two named greps plus one guard run found; any
renamed balance is invisible to all three, which is `CANNOT-CATCH` item 2 and the whole reason LEG 2
must eventually be mechanised on types rather than names.

The direction of T511's error is worth naming: it claimed the guard **understates the tree**, and the
guard does — but not by the margin it gave, and its own grep understated the guard. The argument
("this calls for a better discriminator, not the withdrawn one") is unaffected. The numbers were not.

---

## Vectors run (pass/fail)

**No golden vectors were run, and none apply.** This branch changes zero executable lines: the diff
is comments plus one test's doc comment. The package's arithmetic is byte-identical to `fc35f4eb`,
so any vector result would be `fc35f4eb`'s result relabelled — a vacuous pass in the P-392 sense.
The reference oracle was used all through as a **source oracle**: every claim above is a `file:line`
citation into `/Users/buv/fineract` @ `426a23544`, opened and read, not recalled.

What was run instead:

| check | result |
|---|---|
| `go build ./...` | PASS |
| `go vet ./internal/apps/loanproduct/` | PASS |
| `gofmt -l ./internal/apps/loanproduct/` | clean (no output) |
| `go test -count=1 ./internal/apps/loanproduct/` | PASS |
| `go test ./...` (whole module) | PASS |
| `check-ledger-invariants.sh` | FAILS, as designed — the four sites are still RED |

### Falsifiability of `TestOutstandingLoanBalanceIsASweptSnapshot`, re-verified by execution

I did not take T514's word for it. Counterfactual: patch `OutstandingLoanBalance()` to derive on read
(`if ip.repaymentPeriod != nil { ip.UpdateOutstandingLoanBalance() }`), i.e. exactly the shape the
guard prescribes. Result:

```
--- FAIL: TestOutstandingLoanBalanceIsASweptSnapshot
    interestperiod_test.go:74: the cell is a SWEPT SNAPSHOT, not an on-demand derivation:
    reading it after a summand changed but before a sweep gave 70000 minor units,
    want the unchanged 90000.
```

**70000 vs 90000**, matching T514's re-verification exactly. The probe was reverted; `gofmt`, `vet`,
`build` and the tests are green on the reverted tree and `grep -c 'FALSIFICATION PROBE'` returns 0.
The test remains a live falsification of LEG 1, which is the whole reason LEG 1 is ranked first.

---

## Money-math notes

- **Nothing moved.** No arithmetic line was touched. The four refused writes, the roll-forward, the
  `negToZero` clamp and the signed-delta accumulation are byte-identical to `fc35f4eb`.
- **All amounts remain integer minor units.** The falsification probe and its revert introduced no
  float; the test's constants (`90000`, `70000`, `-20000`, `100000`) are minor units, as before.
- The one *money-relevant* fact this branch newly pins in prose is that
  `InterestPeriod.outstandingLoanBalance` **does** absorb a transaction-derived quantity
  (`paidPrincipal`) — which is a fact about the oracle's schedule roll-forward that the previous
  comment actively denied. Anyone porting `LoanBalanceService` or the transaction processor needs to
  know that the schedule model is *fed from* the transaction stream even though it *emits* no
  posting; T511's comment would have told them the opposite.

---

## Unverified

- **[UNVERIFIED — bounded]** That the forward trace in doc.go evidence item 1 is *exhaustive*. It is a
  hand-walked closure plus greps at one oracle commit, not a type-checked closure. doc.go now carries
  this limit inline ("THE LIMIT OF THIS ITEM") rather than leaving it implied. I widened the check
  beyond T511's: `grep -rn 'getOutstandingLoanBalance()' --include='*.java'` over the whole oracle,
  excluding `/src/test/`, returns **23** hits — 9 inside the two defining classes
  (`InterestPeriod.java`, `RepaymentPeriod.java`) and **14 elsewhere**. Every one of the 14 is either
  inside `loanproduct.calc` (`ProgressiveEMICalculator` x3), a DTO assembly on the already-traced path
  (`LoanSchedulePlan` x2, `ProgressiveLoanScheduleGenerator` x1), the `misc/Main.java` demo printer
  (x2), or the *different* quantity — `LoanTransaction.getOutstandingLoanBalance()` (3 provider call
  sites) and `LoanProduct`'s tranche cap (2). No new escape found. A different spelling (a direct
  field read, reflection, a Gson path) would not appear in that grep at all.
- **[UNVERIFIED]** That `>= 9` is the true count of balance-in-substance writes in the tree. It is a
  floor from three searches; see the census note. A renamed balance is invisible to all of them.
- **[UNVERIFIED]** That the `LoanTransaction`s these three call sites walk are always *persisted*
  rows rather than in-flight ones. All three are transaction-driven — `:929` sits inside a loop over
  `installmentToBeProcessed` driven by `loanTransaction`, and `:2912`'s `paidPortion` comes straight
  out of `processPaymentAllocation(..., loanTransaction, ...)` at `:2908` [VERIFIED] — but "the
  transaction has been committed at this point" is a lifecycle claim I did not chase. It does not
  affect the finding: the criterion died on *transaction-derived*, not on *persisted*.

---

## Blockers

None. No contract change was needed and none was made; the frozen adapter contract is untouched.
No `user` gate was reached.

---

## Follow-ups

1. **The go/types reachability discriminator is now load-bearing prose, not just a suggestion.**
   doc.go says LEG 2 is the criterion and that its unmechanised state is why the bar stays red. That
   makes the discriminator the single item that would let these four sites go green honestly. It is
   guard work (`.softhouse/guards/**`, T509's territory) and was not touched here.
2. **`CANNOT-CATCH` item 8 still recommends the form that defeats the check** (T511 §4(2)): six
   composite-literal writes to the two refused fields are invisible to `writeTarget`, and item 8
   tells a tripped author "the fix is a constructor, not an exemption". Unchanged, unfixed, guard
   scope.
3. **`loanschedule/emi.go:1720, :1726` ships the identical write green** because the field is spelled
   `outstandingMinor`. Either the guard grows a type-based surface or that package gets the same
   argued-red treatment. Today the tree is inconsistent about the same oracle method.
4. **T511's handoff §4(1) carries two wrong numbers** (`the guard reports 4`; `6 … exist in the
   tree`). Corrected here rather than there — that file is a merged historical record and outside
   this task's edit scope. A reader of T511 alone still gets the wrong figures.
5. **Whoever ports `LoanBalanceService`** meets the real `m_loan_transaction.outstanding_loan_balance_derived`,
   which *is* a ledger balance folded over postings. doc.go keeps that warning.
