# T514 — independent review of T511 (`softhouse/T511-t505-conditions`, `fc35f4eb`)

**The guard patch is now unmistakably withdrawn — C-1 is fully and correctly applied — but the
posting-stream argument does NOT do the work as written: it is refuted by the very function it
annotates (the roll-forward sums `paidPrincipal`, which is accumulated from applied repayment
transactions), and applied literally it clears `m_loan.principal_outstanding_derived`, a real
persisted outstanding-principal column that Fineract folds over schedule installments rather than
over postings.**

**VERDICT: ACCEPT WITH CONDITIONS.**

Conclusion (b) survives — the four sites are not I-3 violations and must stay RED — but it survives
on the *reachability* half of T511's evidence plus the test-pinned snapshot argument, not on the
*provenance* half that T511 promotes to load-bearing. The load-bearing/corroboration ranking in
`doc.go` is inverted, and one artefact still teaches the refuted column test.

Reviewed against oracle commit `426a23544` at `/Users/buv/fineract` (confirmed by `git log`). Every
Java line cited below was opened. Every cardinal was produced by running something and the command
is given (P-104).

Diff scoped with `git diff --stat 0b5e8b81..softhouse/T511-t505-conditions`, never `main..HEAD`.

---

## 0. Summary table

| Item | Claim under review | My finding |
|---|---|---|
| C-1 withdrawal | patch retitled WITHDRAWN, counterexample above it | **FULLY APPLIED** — unmistakable at every entry point |
| C-1 replacement | "stay RED until a `go/types` discriminator exists" | **A DIRECTION, NOT YET A SPEC** — MINOR-5, addressed to T509 |
| C-1 "both fail open" | waiver goes stale in time, check goes stale on layout | **CORRECT**, and sharper than T511 states |
| C-2 evidence | `@JsonExclude` only at `:45`/`:68`; blob read back as state | **VERIFIED EXACT** — every line opened |
| C-2 downstream trace | terminates in DTOs, zero `JournalEntry` in `calc/` | **VERIFIED EXACT** |
| C-2 ground | "there is no posting stream / none could be" | **OVERSTATED AND FALSE AS WRITTEN** — MAJOR-1 |
| C-2 as a test | does it wrongly clear anything? | **YES** — `principal_outstanding_derived` — MAJOR-2 |
| C-2 completeness | refuted column argument removed everywhere | **NO** — survives in `interestperiod_test.go:25` — MAJOR-3 |
| falsifiable test | RED at 70000 vs 90000 under derive-on-read | **RE-DRIVEN RED BY ME**, exact message, exact line |
| four sites RED | `262:4 / 273:2 / 305:2 / 558:4`, comment-driven moves | **CONFIRMED**, guard exit 1 |
| T509 cardinals | 6 composite literals, `…Holder`, `LoanBalanceService` | **3 of 4 EXACT**; the "6 vs 4" census is wrong — MINOR-1 |
| `:906`→`:907` | correction noted not silently applied | **CORRECT**; but "every caller negates" is false — MINOR-2 |
| gates | build / vet / test / gofmt | **ALL GREEN**, re-run by me |

---

## 1. Hygiene, re-confirmed cheaply and then left alone

The driver's measurement holds; I re-ran it rather than assume it.

```
$ git diff -U0 0b5e8b81 softhouse/T511-t505-conditions -- nexus/ > /tmp/t511go.diff
$ grep -cE '^[+-]' /tmp/t511go.diff                                        291
$ grep -E '^[+-]' /tmp/t511go.diff | grep -vE '^\+\+\+|^---' \
      | grep -vE '^[+-][[:space:]]*//' | wc -l                               0
```

291 changed lines in `nexus/`, **zero of them non-comment**. Five files total, `.softhouse/guards/**`
and `.softhouse/tasks.json` untouched. Nothing further on scope.

Gates, run by me on a tree carrying T511's `loanproduct` (main's `loanproduct` differs from T502's
base only by T502's own four files, verified with `git diff --stat main 0b5e8b81 -- .../loanproduct/`):

```
$ go build ./...                          exit 0
$ go vet ./internal/apps/loanproduct/     exit 0
$ gofmt -l internal/apps/loanproduct/     (no output)
$ go test ./...                           exit 0, no failures
```

All money on the touched paths is `int64` minor units (`Minor()`, `maxInt64`, `90000`/`70000`); no
float appears anywhere in the diff or in the test.

---

## 2. C-1 — the withdrawal is unambiguous. Applied correctly.

I went looking for a way to lift the patch without meeting the refutation, and could not find one.
Every route into §5 is gated:

- **§0**, the first thing anyone reads, carries a `[T511 …]` blockquote naming C-1, the file move,
  and the replacement recommendation, before the reader reaches §1.
- **The §5 heading itself** is `WITHDRAWN — the persistence-surface guard patch, and why it must not
  land`, followed immediately by `**Do not implement it.**`
- **Ordering is right.** Replacement recommendation → refutation → patch text. The counterexample is
  physically above the thing it refutes, as C-1 required.
- **Every subheading inside the patch** carries its own marker: `The rule (WITHDRAWN — recorded, not
  recommended)`, `The patch, in five pieces (WITHDRAWN — recorded so it is not re-proposed)`, `Two
  things whoever lands this must do (MOOT — nobody lands this)`.
- **`The alternative the guard itself names`** — the one place that still said "I recommend … the
  patch above" — carries a `[T511]` block retracting exactly that phrase.
- **`doc.go`** carries the same withdrawal in code, with the file move spelled out, so a reader who
  never opens the handoff still meets it.

The only unmarked subheading is `### Measured effect of the patch`, which sits between two marked
ones inside a section whose title is WITHDRAWN. I do not think a reader can reach it without passing
a marker. Not a finding.

**A hurried reader cannot lift this patch.** Keeping the text is the right call: the patch was
plausible enough that it took a constructed counterexample to kill, and deleting it invites
re-derivation.

### 2.1 "Both fail open" — correct, and the reasoning is sound

T511's added claim is that the choice is not patch-vs-DEC-2-exemption but **neither**: a per-package
waiver goes stale the day the package grows a repository; the persistence check goes stale the moment
someone moves a file.

That is right, and the two failure axes are genuinely different — a waiver fails open in **time**, the
heuristic fails open on **layout** — which is why neither dominates the other and neither is safe.

One thing T511 flattens, in its own favour and worth recording rather than correcting: the two are not
equally *detectable*. A DEC-2 waiver is a ratified document entry a human must write and a reviewer
must read; its staleness is at least discoverable by inspecting the document. The persistence
heuristic's failure produces **no artefact at all** — the `git mv` looks like ordinary refactoring and
the guard silently reclassifies. So "both fail open, only the red bar does not" is true, and the
heuristic is the worse of the two, not the equal.

### 2.2 The replacement recommendation — a direction with a named tool, not yet a buildable spec

> *"These four sites stay RED until a `go/types`-based discriminator exists that follows the value
> across the import graph to a persisted column. No rename, no per-package waiver, no
> directory-shaped heuristic."*

**What it genuinely hands T509.** Three real commitments: the tool (`go/types`, hence type-resolved
identity rather than string identity), the relation (reachability across the import graph), and the
terminal (a persisted column). And — this is the part that matters — the refutation that killed the
withdrawn patch **does not apply to it**: type-based reachability is invariant under `git mv`, so the
one-file-move attack fails against it by construction. That is a genuine improvement, not a
restatement of the problem.

**What it does not hand T509, and must before anything is built** (MINOR-5, non-blocking, addressed
to T509 rather than to T511):

1. **The fail direction on unresolved flow is unspecified.** Value flow across an import graph is
   not decidable; any real implementation will hit edges it cannot resolve (interface dispatch,
   reflection, a value stashed in a `map[string]any`, a `[]any` args slice handed to `Exec`). A
   discriminator that answers "not persisted" on an unresolved edge is fail-open — the exact defect
   the withdrawal was about, relocated from directory adjacency to analysis precision. The
   recommendation must say **fail-CLOSED on unresolved flow** or it can be implemented into the same
   hole.
2. **"A persisted column" has no mechanical definition here.** In this tree every query is a literal
   SQL string in a `postgres.go`, so column identity means parsing that literal and matching an
   argument position to a column name. That is tractable for the shapes present and undecidable in
   general; the spec should say it targets the literal-SQL-plus-`pgx`-args shape and refuses
   (fail-closed) on dynamic SQL, which the guard already classes `OPAQUE-SQL`.
3. **No drive-RED/GREEN cases are named.** The guard's own discipline (P-22/P-45, and the withdrawn
   patch's own "Two things whoever lands this must do" item 1) requires a class be shown both to
   refuse and to pass. The recommendation inherits none of that.

So: **not a wish** — the bar is not left red forever, and the direction is implementable against this
tree — but **not yet a specification**. T509 needs items 1–3 decided before it writes the analysis,
and item 1 is the one that decides whether the rebuild repeats the failure.

---

## 3. MAJOR-1 — "there is no posting stream / none could be" is refuted by the function it annotates

This is the finding. The brief asked whether the posting-stream ground actually does the work. Part of
it does; the sentence T511 makes load-bearing does not, and it is false in the oracle.

`doc.go` (and the comment on `UpdateOutstandingLoanBalance`, and the field-declaration block) assert:

> *"computed FORWARD from the preceding segment's terms, never folded BACKWARD over anything that
> happened. **No transaction is summed to produce it and none could be.**"*
> *"This expression sums no postings and could not."*

**It sums one, five lines below the claim.** `InterestPeriod.updateOutstandingLoanBalance` folds the
preceding repayment period's **paid principal**:

```
InterestPeriod.java:178      .plus(previousRepaymentPeriod.get().getPaidPrincipal(), getMc());
```

and the port reproduces it verbatim at `interestperiod.go:266` — `.plus(previous.PaidPrincipal())`,
inside the very function whose doc comment says no transaction is summed.

`paidPrincipal` is an accumulator over applied repayment transactions. I traced the whole path:

```
RepaymentPeriod.paidPrincipal
  <- RepaymentPeriod.addPaidPrincipalAmount            RepaymentPeriod.java:405-407
  <- ProgressiveEMICalculator.payPrincipal             ProgressiveEMICalculator.java:421  (also :2162)
  <- AdvancedPaymentScheduleTransactionProcessor       :929, :967, :2912
       — walking the loan's LoanTransactions
```

Same for the second cell. `balanceCorrectionAmount` is not an abstract delta: at
`ProgressiveEMICalculator.java:922` it is `effectivePaidPrincipal.negated()` and at `:952` it is
`paidPrincipal.negated()` — literally the transaction-derived paid principal, negated. `doc.go`'s own
evidence item 3 cites both lines. **The doc's item 3 refutes the doc's headline claim.**

And `RepaymentPeriod.getOutstandingLoanBalance` (`:389-403`) folds `getPaidPrincipal()` at `:397` as
well, so the property is not confined to the segment cell.

**Why this matters and is not pedantry.** The whole point of the T502→T505→T511 chain is that a
*stated reason* in a comment is what the next author reuses. "No posting stream, and none could be" is
stated absolutely, in capitals, marked as the load-bearing leg, in five places. The next author who
meets a cell that *does* fold transactions — which is every cell in this file — will find the doc
saying it does not, and will either distrust the whole comment or, worse, apply the absolutism
elsewhere. This is the same shape as E-1: individually true citations arranged into a claim stronger
than they support.

**What actually survives, and it is enough.** Two of T511's own legs are intact and I verified both:

- **Reachability.** The cell's entire downstream reach is `InterestPeriod.java:151` (the
  declining-balance interest base) → `RepaymentPeriod.java:389-403` →
  `ProgressiveLoanScheduleGenerator.java:132` → `LoanScheduleModelRepaymentPeriod` and
  `LoanSchedulePlan.java:65,:77`. I opened both terminals: **zero** `@Entity`/`@Table`/`@Column` on
  either. `grep -rn JournalEntry .../loanproduct/calc/` → **0 hits** (the grep does hit three files
  elsewhere in `fineract-progressive-loan`, none on this path). No ledger, no GL account, no posting
  is reachable from this cell.
- **Parity / swept snapshot.** Pinned by a test I drove RED myself (§5).

The defensible formulation is **reachability, not provenance**: *this cell is not read as an
authoritative statement of any party's position and no path from it reaches a ledger, a GL account or
a balance column; it is an input to one interest formula and to two response DTOs, and its staleness
between explicit sweeps is semantically load-bearing.* That claim is true, is what the evidence
supports, and does not collapse the moment someone notices `paidPrincipal`.

**Condition D-1 (blocking).** Delete "no transaction is summed to produce it and none could be" and
"this expression sums no postings and could not" from `doc.go`, `interestperiod.go` (field block and
`UpdateOutstandingLoanBalance`) and `repaymentperiod.go`. Replace with the reachability formulation,
and state explicitly that the roll-forward **does** take a transaction-derived summand
(`paidPrincipal`, `InterestPeriod.java:178`; and `balanceCorrectionAmount` at
`ProgressiveEMICalculator.java:922`/`:952`), which is *why* provenance cannot be the test here.

---

## 4. MAJOR-2 — the posting-stream test, applied literally, clears a real persisted balance column

The brief asked me to try to break the test by finding a case it wrongly clears. Here is one, in the
oracle, at the pinned commit.

**`m_loan.principal_outstanding_derived`** — `LoanSummary.totalPrincipalOutstanding`
[VERIFIED: `LoanSummary.java:62-63` — `@Column(name = "principal_outstanding_derived", scale = 6,
precision = 19)`]. This is the loan's outstanding principal: a persisted, regulator-visible balance
column, exactly the shape I-3 exists to govern.

It is **not** derived by summation over a posting stream. It is derived from the **schedule**:

```
LoanSummary.java:203-204
  this.totalPrincipalOutstanding = principal.plus(capitalizedIncome).plus(this.totalPrincipalAdjustments)
          .minus(this.totalPrincipalRepaid).minus(this.totalPrincipalWrittenOff).getAmount();

LoanSummary.java:339-346  calculateTotalPrincipalRepaid(repaymentScheduleInstallments, currency)
    for (LoanRepaymentScheduleInstallment installment : repaymentScheduleInstallments)
        total = total.plus(installment.getPrincipalCompleted(currency));
```

Every term is folded over `repaymentScheduleInstallments` — the schedule, i.e. precisely the artefact
`doc.go` says "projects the FUTURE" and therefore has no posting stream. Entry point:
`LoanBalanceService.java:124` → `LoanSummary.updateSummary(currency, principal,
loan.getRepaymentScheduleInstallments(), …)`.

**Apply the test as `doc.go` states it** — *"is this value produced by folding a posting stream?"* —
and the answer for `principal_outstanding_derived` is **no**. The test clears a stored outstanding
principal balance. That is a false clear, and it is the kind of column I-3 is written for.

**The loose reading does not rescue it, it condemns the four sites.** One could answer that
`installment.getPrincipalCompleted()` is itself transaction-driven, so there is a stream one hop away.
True — but `RepaymentPeriod.paidPrincipal` is transaction-driven exactly one hop away too (§3). The
transitive reading refuses the four sites; the direct reading clears a real balance column. **The test
as stated is not well-defined at the boundary, and both of its readings give a wrong answer
somewhere.**

Note the contrast T511 draws is with `m_loan_transaction.outstanding_loan_balance_derived`, which I
verified and which *is* a direct fold over transactions (§7). That column is a well-chosen
illustration — but it is the *easy* case. `principal_outstanding_derived` is the hard one, sits in the
same `LoanBalanceService`, and it is the one that breaks the rule.

**Condition D-2 (blocking).** Either (i) demote the posting-stream framing from "THE TEST THAT DECIDES
IT" to a supporting observation and make reachability the operative test, or (ii) keep it and state
the boundary rule explicitly — that the question is *direct* fold, and record
`m_loan.principal_outstanding_derived` (`LoanSummary.java:62-63, :203-204, :339-346`) as a known case
the direct reading gets wrong, so the next author does not clear it. **(i) is the correct repair**, and
it composes with D-1: reachability answers both cases the same way it answers T501's.

Reconciliation with T501/T510 under reachability: `SavingsAccountSummary.AccountBalance` is *read as
the account's authoritative position*, so it is reachable-to-truth and must be derived, not stored —
which is what T501 did, and T510 preserved when it fixed the reversal defect without reinstating a
stored balance. The four schedule cells reach only an interest formula and two DTOs. Same test,
opposite disposition, and no absolutism required.

---

## 5. MAJOR-3 — C-2 is not fully applied: the refuted column argument survives in the test file

T511 rewrote `doc.go` and four per-site comments. It did **not** touch
`nexus/internal/apps/loanproduct/interestperiod_test.go`, which still reads:

```go
// ... this cell is a schedule-projection intermediate that never becomes a
// database column (doc.go carries the oracle evidence), and deriving it on read
// would silently change the numbers ...
                                       — interestperiod_test.go:23-26
```

Two things are wrong with leaving it:

1. It states, verbatim and unqualified, **the exact argument `doc.go` now heads "The column argument
   does not work — do not reuse it."**
2. It **cites `doc.go` as the authority for it** — "doc.go carries the oracle evidence." A reader who
   follows that pointer lands on the section refuting the sentence that sent them there.

I confirmed this is the only such residue in Go code:

```
$ grep -rn 'column\|COLUMN' nexus/internal/apps/loanproduct/*.go
  → interestperiod.go, repaymentperiod.go, doc.go all carry the [T511] correction
  → interestperiod_test.go:25 is the sole uncorrected restatement
```

This artefact is not incidental: it is the doc comment on the *falsifiable test*, i.e. the text a
future author reads at the exact moment they are considering the change the test exists to stop.
T505's C-2 named "`doc.go` and the three in-code comments"; the test file was not enumerated, so this
is arguably a literal-compliance pass. It is not a compliance pass on C-2's stated purpose — "the next
author who applies it will argue away a real balance write with it."

**Condition D-3 (blocking).** Restate `interestperiod_test.go:20-28` on the same ground as the rest,
and drop the "never becomes a database column" clause and its citation of `doc.go` as evidence for it.

### 5.1 The test itself — genuinely falsifiable, re-driven RED by me

Not taken on trust. I injected the derive-on-read accessor T511 describes:

```go
func (ip *InterestPeriod) OutstandingLoanBalance() Money {
	ip.UpdateOutstandingLoanBalance()
	return ip.outstandingLoanBalance
}
```

```
$ go test ./internal/apps/loanproduct/ -run TestOutstandingLoanBalanceIsASweptSnapshot -v
--- FAIL: TestOutstandingLoanBalanceIsASweptSnapshot (0.00s)
    interestperiod_test.go:57: the cell is a SWEPT SNAPSHOT, not an on-demand derivation: reading it
    after a summand changed but before a sweep gave 70000 minor units, want the unchanged 90000. ...
FAIL  exit 1
```

Exact message, exact assertion line, exact numbers T511 reported. Reverted; `go test ./...` back to
exit 0 and the file byte-identical to T511's. **The test pins something and can fail in the direction
of the defect (P-45).** This is the strongest artefact on the branch, and — per §3 — it is the leg
`doc.go` demotes to "corroboration".

---

## 6. The four sites are still RED, and the moves are comment-driven

Guard run by me on my tree:

```
$ bash .softhouse/guards/check-ledger-invariants.sh ; echo EXIT=$?
EXIT=1
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:262:4
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:273:2
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:305:2
  [I3-FIELD-WRITE] internal/apps/loanproduct/repaymentperiod.go:558:4
  [I3-FIELD-WRITE] internal/apps/savings/postgres.go:243:7
  [I3-FIELD-WRITE] internal/apps/savings/postgres.go:302:5
  [I3-FIELD-WRITE] internal/apps/savings/summary.go:53:2
```

Byte-for-byte the four line numbers T511 reports. I opened each and confirmed the **statements** are
unchanged from `main` (`196 / 207 / 224 / 541`) and from T502 (`236 / 247 / 273 / 551`) — same four
writes, `ip.outstandingLoanBalance = …` twice, `ip.balanceCorrectionAmount = …` twice. The moves are
accounted for entirely by inserted comment lines, which the zero-non-comment-lines measurement in §1
independently proves. **Nothing disappeared, nothing was amnestied, no rename.**

---

## 7. The T509 carry-forward — three cardinals exact, one wrong

**(1) The `emi.go` GREEN twin — CONFIRMED, and it is the right thing to escalate.** Opened
`emi.go:62` (`// outstandingMinor is the balance carried INTO this segment.`), `:1688-1690` (the
comment citing `ProgressiveEMICalculator.java:1253-1255 -> InterestPeriod.updateOutstandingLoanBalance`
— the same oracle method), and the two writes at `:1720-1721` and `:1726`. Merged, vector-graded,
GREEN purely on spelling. Exact.

**(2) MINOR-1 — the "6 balance-in-substance assignments vs 4 reported" cardinal is wrong, twice.**
This is a P-104 hit and I would not have found it without running the greps.

```
$ grep -rnE --include='*.go' '\.[a-zA-Z0-9_]*[Bb]alance[a-zA-Z0-9_]* *=[^=]' nexus/ | grep -vE '==|!=|:='
  4 hits (the four loanproduct sites)
```

- The pattern requires ` *=`, so it **cannot match compound assignment**. It silently misses
  `nexus/internal/apps/savings/summary.go:53  s.AccountBalance += effect` — the very write the C-1
  counterexample is built on, in the same handoff. Widening to
  `'\.[a-zA-Z0-9_]*[Bb]alance[a-zA-Z0-9_]* *([-+*/|&^]|<<|>>)?=[^=]'` returns it.
- "the guard reports 4" contradicts **T511's own guard transcript four sections earlier**, which lists
  **7** `I3-FIELD-WRITE` findings. The comparison silently drops the three `savings` findings from the
  guard side while the grep side drops one of the same three.

Corrected: the guard reports **7** balance-field write statements; the tree contains at least **9**
balance-in-substance write statements (those 7 plus the two `outstandingMinor` writes the guard cannot
see), plus **6** composite-literal writes it structurally cannot see. **The conclusion is unaffected
and in fact strengthened** — the guard is name-shaped and understates the tree — but the number as
published is not reproducible and a later reader will not be able to re-derive it. This is exactly the
failure mode the chain exists to punish, in the section that diagnoses that failure mode.

**(3) Composite-literal hole — CONFIRMED, count exact, sites exact.**

```
$ grep -rnE --include='*.go' '^[[:space:]]*(balanceCorrectionAmount|outstandingLoanBalance)[[:space:]]*:' nexus/
  interestperiod.go:362,363,387,388   repaymentperiod.go:96,97      (6)
```

And the mechanism is as described: `ledgerguard/main.go:549-570` dispatches `writeTarget` only on
`*ast.AssignStmt` and `*ast.IncDecStmt`, so a `KeyValueExpr` is invisible. `CANNOT-CATCH` item 8
(`main.go:793-794`) does say *"the fix is a constructor, not an exemption"* — i.e. it recommends the
form that evades the check. **Confirmed bad advice**, exactly as stated.

**(4) `…Holder` over-match — CONFIRMED.** `repaymentperiod.go:486
func (p *RepaymentPeriod) SetReAgedEarlyRepaymentHolder(v bool)`; `holdFuncRe`
(`main.go:175`) matches `[a-z0-9]Hold`; `CANNOT-CATCH` item 7(ii) (`main.go:787-789`) lists only the
`…Holds` shape. Exact.

**(5) `m_loan_transaction.outstanding_loan_balance_derived` — CONFIRMED, and T511's characterisation
of it is TRUE.** `LoanTransaction.java:127` carries
`@Column(name = "outstanding_loan_balance_derived", scale = 6, precision = 19)`.
`LoanBalanceService.updateLoanOutstandingBalances` (`:160-206`) filters to `isNotReversed() &&
!isNonMonetaryTransaction()`, sorts by `LoanTransactionComparator`, and folds a running `outstanding`
across them, writing at `:174`, `:194`, `:203`. **It does have a posting stream and it is derived by
summation over it** — T511's claim is accurate, and it is a good illustration. It is a different
quantity from `InterestPeriod`'s cell, in `loanaccount.domain` rather than `loanproduct.calc.data`,
with no data path between them. T502's conclusion does survive, and "by luck rather than by the check
performed" is the honest way to say it.

The gap is that this is the easy illustration and `principal_outstanding_derived` — the hard one, in
the same service — breaks the rule it is illustrating (§4).

---

## 8. MINOR findings

**MINOR-2 — "every oracle caller adds a NEGATED principal amount to it" is false at two of its eight
citations.** The comment on `AddBalanceCorrectionAmount` (`interestperiod.go:296-303`, inherited from
T502 and re-affirmed by T511 with three citations added) cites
`ProgressiveLoanInterestScheduleModel.java:257, :290`. At both, the argument is the parameter
`correctionAmount`, whose sign is fixed upstream — and upstream it is **not always negated**:

```
ProgressiveEMICalculator.java:991, :993   addOverdueBalanceCorrection(model, …, overduePrincipal)     // positive
ProgressiveEMICalculator.java:1003        addOverdueBalanceCorrection(model, …, …negated())            // negative
ProgressiveEMICalculator.java:489         addCredit(scheduleModel, …, creditedPrincipalAmount, …)      // positive
   -> :500 changeOutstandingBalanceAndUpdateInterestPeriods(…, creditedPrincipalAmount, …)
   -> :257 / :290 addBalanceCorrectionAmount(correctionAmount)
```

A chargeback credit adds a **positive** correction. Separately, three of the six
`ProgressiveEMICalculator` sites (`:907`, `:946`, `:1124`) add `getBalanceCorrectionAmount().negated()`
— they negate *the cell's own value* (a reset to zero), not a principal. So the precise statement is:
six direct call sites negate, two indirect paths can be positive, and the six split three-and-three
between negating a principal and zeroing the cell.

T511's handoff says it "opened all six `addBalanceCorrectionAmount` call sites" — six, while the
comment it left in place carries a universal quantifier over eight. The substantive claim ("a signed
delta, not a balance") is **unharmed and in fact strengthened** by the correction: a quantity that can
be positive or negative is even less like a balance. But the universal is false and should go.
`doc.go`'s version cites only the six and is safe as written.

**MINOR-3 — E-1's refuted conclusion is left unmarked at the end of the superseded section.** The
`[T511]` block at the head of E-1 says the material below "is kept as the record of the citations,
which remain accurate as citations." But E-1's **last line** is not a citation, it is the conclusion:
*"So DEC-2 §4.4 I-3 — 'No write path to any balance column exists in the Go tree' — has no column to
be about here."* A reader who scrolls to the end of E-1 exits on the refuted claim with no marker in
view. One inline `[T511: SUPERSEDED — see the block at the head of E-1]` closes it. This is the exact
symmetric hazard C-1 was so careful about in §5.

**MINOR-4 — a stale oracle citation carried to T509 without noting it is stale.** T511 corrected
`:906`→`:907` in the handoff and corrected the sweep citation to
`ProgressiveEMICalculator.java:1254-1256` in `doc.go` and the test comment (I confirmed
`calculateOutstandingBalance` occupies exactly `:1254-1256`). But the T509 backlog quotes `emi.go`'s
comment citing `:1253-1255` verbatim without flagging that it is the same off-by-one, so `loanschedule`
keeps a citation this branch has already established is wrong. One sentence in the backlog item fixes
it.

**MINOR-5 — the replacement recommendation needs three decisions before T509 builds.** See §2.2.
Item 1 (fail-CLOSED on unresolved flow) is the one that decides whether the rebuild repeats the
withdrawn patch's failure.

---

## 9. Was a comment rewrite the right deliverable?

T511 invites this attack, so I will answer it. **Yes.** The branch's shipped defect was a *stated
reason* that would license a real balance write in a later author's hands — and §4 shows it would have:
"never a column" applied to `principal_outstanding_derived` clears a persisted outstanding-principal
balance. A wrong reason in a package comment on money code is a shipped defect, and correcting it
without touching one line of arithmetic is the cheapest possible repair. The red bar staying red is
the correct outcome, not a shortfall.

What I hold against the branch is not that it only wrote comments. It is that the *replacement* reason
is stated more strongly than its evidence supports (§3), is not well-defined at the boundary (§4), and
is missing from the one artefact a future author reads at the decisive moment (§5) — the same three
shapes T505 found in E-1.

---

## 10. Verdict and conditions

**ACCEPT WITH CONDITIONS.**

C-1 is fully and correctly applied; I could not find a route by which a hurried reader lifts the
withdrawn patch, and "both fail open" is right. The four sites are still RED at the reported lines,
the diff is comments only, the falsifiable test is genuinely falsifiable and I drove it RED myself,
and all gates are green. Three of the four T509 cardinals are exact.

C-2 is applied in form and incomplete in substance.

**D-1 (blocking, MAJOR-1).** Remove the absolutist provenance claims — "no transaction is summed to
produce it and none could be", "this expression sums no postings and could not" — from `doc.go`,
`interestperiod.go` (field block and `UpdateOutstandingLoanBalance`) and `repaymentperiod.go`. They are
refuted by `InterestPeriod.java:178` (`getPaidPrincipal()`) and `ProgressiveEMICalculator.java:922`,
`:952` (`paidPrincipal.negated()`), and the port reproduces the first at `interestperiod.go:266`.
Restate on **reachability**: the cell is not read as anyone's authoritative position and no path from
it reaches a ledger, GL account or balance column — verified terminals `LoanScheduleModelRepaymentPeriod`
and `LoanSchedulePlan`, zero `@Entity`/`@Table`/`@Column`, zero `JournalEntry` in `.../loanproduct/calc/`.
Say plainly that the roll-forward *does* take a transaction-derived summand, and that this is why
provenance cannot be the test.

**D-2 (blocking, MAJOR-2).** Demote "IS THERE A POSTING STREAM?" from *the* test to supporting
observation, and record `m_loan.principal_outstanding_derived` (`LoanSummary.java:62-63`, derived at
`:203-204` from `repaymentScheduleInstallments` via `:339-346`, entered at `LoanBalanceService.java:124`)
as the case the literal reading wrongly clears. Reachability reconciles T501/T510 and these four sites
without needing the boundary to be sharp.

**D-3 (blocking, MAJOR-3).** Restate `interestperiod_test.go:20-28`. It is currently the only artefact
in the package still teaching "never becomes a database column", and it cites `doc.go` as the evidence
for a claim `doc.go` refutes.

**D-4 (non-blocking, MINOR-1).** Correct the "6 vs 4" census in the T509 carry-forward: the pattern
misses compound assignment (`savings/summary.go:53`), and "the guard reports 4" contradicts the
7-finding transcript in the same handoff. Publish the corrected figures (7 reported / ≥9 in substance
/ 6 structurally invisible) — the conclusion strengthens.

**D-5 (non-blocking, MINOR-2/3/4/5).** Drop the false universal on `AddBalanceCorrectionAmount`; mark
E-1's closing sentence; note that `emi.go`'s `:1253-1255` is the same off-by-one this branch corrected;
and hand T509 the three missing decisions from §2.2, of which **fail-CLOSED on unresolved flow** is the
one that keeps the rebuild from repeating the withdrawn patch's defect.

**The four sites stay RED and that remains the correct state.** Conclusion (b) is right. It needs a
reason that survives someone reading the function it is attached to.
