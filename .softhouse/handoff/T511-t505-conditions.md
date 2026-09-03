# T511 — applying T505's blocking conditions to T502

Branch: `softhouse/T511-t505-conditions`, cut from `softhouse/T502-loanproduct-i3` (`0b5e8b81`), **not** `main`.
Scope: `nexus/internal/apps/loanproduct/` + `.softhouse/handoff/`.
Oracle: pinned Fineract at `/Users/buv/fineract`, commit `426a23544` (confirmed by `git log` in that tree).
`.softhouse/tasks.json` and `.softhouse/guards/**` untouched — T509 owns the guard.

Scope-check the diff with `git show --stat` or `git diff --stat $(git merge-base main HEAD)..HEAD`,
**never** `git diff main..HEAD`: `main` moves while a branch is open and the naive form already
produced one false scope accusation in this fire.

```
$ git diff --stat 0b5e8b81
 .softhouse/handoff/T502-loanproduct-i3.md          | 174 +++++++++++++++++-
 nexus/internal/apps/loanproduct/doc.go             | 204 ++++++++++++++++-----
 nexus/internal/apps/loanproduct/interestperiod.go  |  66 +++++--
 nexus/internal/apps/loanproduct/repaymentperiod.go |  15 +-
```

**Every Go line changed on this branch is a comment line.** Measured, not asserted:

```
$ git diff -U0 0b5e8b81 -- nexus/ | grep -E '^[+-]' | grep -vE '^\+\+\+|^---' \
      | grep -vE '^[+-][[:space:]]*//' | wc -l
0
```

Zero identifiers renamed, zero arithmetic changed, no new test, no test deleted.

---

## 1. C-1 as applied — the refuted guard patch is withdrawn

T502 §5 proposed discriminating `I3-FIELD-WRITE` on a package's **persistence surface** — a db
import, an SQL-shaped literal or a column struct tag somewhere in the same directory — moving
everything else into a new `I3-FIELD-WRITE-NONPERSISTENT` class that prints and never sets `rc`. It
claimed the three `savings` sites would "stay refused — nothing amnestied."

T505 rebuilt the patch, **reproduced that output exactly** (so the measurement was honest), and then
broke it with one file move: relocating `nexus/internal/apps/savings/summary.go` — which carries
`s.AccountBalance += effect` at `:53`, one of the three writes claimed safe — into
`internal/apps/savings/model/` reclassifies that real account-balance write to the never-refusing
class. Zero code change, byte-identical but for the `package` clause, and `model/` beside a
`postgres.go` repository is conventional Go layering, not an exotic evasion.

The defect is structural, not a tuning error: **"the package imports a db driver" tracks *shares a
directory with a string containing SQL*, not *reaches a balance column*. A guard that a file move
disarms is not a guard.** And for a money non-negotiable, "printed but not refused" is not
enforcement — the bar is the exit code (P-45).

`.softhouse/handoff/T502-loanproduct-i3.md` §5 is retitled **"WITHDRAWN — the persistence-surface
guard patch, and why it must not land"**, carries the counterexample and its commands beside the
proposal so nobody re-proposes it, and the patch text is kept in full and marked "recorded, not
recommended." §0 and "The alternative the guard itself names" carry the same correction.

### The new §5 recommendation, quoted verbatim

> **These four sites stay RED until a `go/types`-based discriminator exists that follows the value
> across the import graph to a persisted column. No rename, no per-package waiver, no
> directory-shaped heuristic. A red bar that is understood and argued is a better state than a green
> bar bought with a check that a file move defeats.**

That is T502's own §7 fallback, promoted from alternative to recommendation; T505 endorses it.
**Building the discriminator is T509's, not this branch's** — nothing under `.softhouse/guards/` was
touched here.

One correction to T502's framing that is worth keeping: the choice is not "persistence-surface patch
vs DEC-2 exemption." It is **neither**. A per-package waiver goes stale the day the package grows a
repository; the persistence-surface check goes stale the moment somebody moves a file. Both fail
open. Only the red bar does not.

---

## 2. C-2 as applied — the argument is restated on the posting-stream ground

T502's E-1 argued **"never a column — it is a `text` blob."** Its citations are individually true;
the conclusion does not follow, and I opened the evidence that kills it:

- **Both cells ARE serialised into `m_loan_progressive_model.json_model`.** `InterestPeriod` carries
  `@JsonExclude` on exactly two fields — `repaymentPeriod` (`:45`) and `mc` (`:68`).
  `balanceCorrectionAmount` (`:65`) and `outstandingLoanBalance` (`:66`) carry none, and
  `JsonExcludeAnnotationBasedExclusionStrategy.shouldSkipField` skips **only** annotated fields
  [VERIFIED: `JsonExcludeAnnotationBasedExclusionStrategy.java:31-34` — `return annotation != null`].
- **The blob is read back as starting state.** `getSavedModel` (`:110-128`) loads it through
  `extractModel` (`:95`) and, when the stored business date is stale, calls
  `recalculateInterestForDate` **onto the loaded model** (`:122`) rather than rebuilding it
  [VERIFIED: `InterestScheduleModelRepositoryWrapperImpl.java`].

On T501's ratified standard — which deleted a **field**, not a column, holding that "a decoded
balance is a number this port did not derive, arriving through the `SELECT` instead of the `INSERT`"
— "it's a blob, not a typed column" does not survive. Left as written, T501 and T502 would
contradict each other in the record.

**The sound ground, which reconciles them: THERE IS NO POSTING STREAM.**

> I-3 governs ledger balances, and a ledger balance is defined by the posting stream it folds. The
> prescribed remedy "derive by summation over the postings" presupposes that stream.
> `SavingsAccountSummary.AccountBalance` has one, so T501's remedy was available and obligatory. A
> schedule cell has none: a schedule projects the FUTURE, postings record the PAST. The remedy names
> **no computation** — definitionally inapplicable, not merely inconvenient.

This is a **category** argument. E-4's "deriving on read turns 900.00 into 700.00" is a **parity**
argument. Both are kept, and `doc.go` now says explicitly which is load-bearing.

Rewritten on that ground, all opened at `426a23544`:

- `nexus/internal/apps/loanproduct/doc.go` — new sections "THE TEST THAT DECIDES IT: IS THERE A
  POSTING STREAM?", "The rest of the evidence, which supports that test", "The column argument does
  not work — do not reuse it", "The bar is red on purpose".
- `interestperiod.go` — the field-declaration block, `UpdateOutstandingLoanBalance` (the two writes)
  and `AddBalanceCorrectionAmount`.
- `repaymentperiod.go` — `copyWithoutPaidAmounts`.

The downstream trace T505 verified is now in `doc.go` and in the field comment, **re-opened by me
line by line**:

```
InterestPeriod.outstandingLoanBalance
  -> InterestPeriod.java:151              case DECLINING_BALANCE -> getOutstandingLoanBalance().getAmount()
  -> RepaymentPeriod.java:389-403         period-level cell, Memo'd on {paidPrincipal, paidInterest,
                                          interestPeriods, totalDisbursedAmount}
  -> ProgressiveLoanScheduleGenerator.java:132
       repaymentPeriod.setOutstandingLoanBalance(interestRepaymentPeriod.getOutstandingLoanBalance())
       -> LoanScheduleModelRepaymentPeriod       (0 hits for @Entity/@Table/@Column)
  -> LoanSchedulePlan.java:65, :77              (0 hits for @Entity/@Table/@Column)
```

**No journal entry, no GL account, no posting.** `grep -rn JournalEntry
fineract-progressive-loan/src/main/java/.../loanproduct/calc/` returns **0**.

The `:906` → `:907` citation is corrected in the handoff, with the correction noted rather than
silently applied. I opened all six `addBalanceCorrectionAmount` call sites: `:907` (was cited as
`:906`), `:922`, `:946`, `:952`, `:1124`, `:1129` — the other five were exact, and the substance
(every caller adds a negated amount) holds at all six.

---

## 3. The four sites are still RED, and the test still falsifies

**RED, verified by running the guard on this branch:**

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

Same four writes as at `main` (`196:4 / 207:2 / 224:2 / 541:4`) and as on T502 (`236 / 247 / 273 /
551`); the line numbers moved only because comments were added above them. The `savings` sites are
not mine and are untouched — they are shown to make the point that this branch amnestied nothing.

**FALSIFIABLE, driven RED by me and then reverted.** With the derive-on-read shape driven into the
accessor:

```go
func (ip *InterestPeriod) OutstandingLoanBalance() Money {
	ip.UpdateOutstandingLoanBalance()
	return ip.outstandingLoanBalance
}
```

```
--- FAIL: TestOutstandingLoanBalanceIsASweptSnapshot (0.00s)
    interestperiod_test.go:57: the cell is a SWEPT SNAPSHOT, not an on-demand derivation: reading it
    after a summand changed but before a sweep gave 70000 minor units, want the unchanged 90000. ...
```

The exact message T505 quoted, at the exact assertion. The probe was reverted; `git diff -U0` against
`0b5e8b81` shows zero non-comment lines, so the revert is complete. 90000 vs 70000 integer minor
units — no float on the path.

**Gates:**

```
$ cd nexus && go build ./...                                # clean
$ go vet ./internal/apps/loanproduct/                       # clean
$ go test ./...                                             # all packages ok
$ gofmt -l internal/apps/loanproduct/                       # no output
```

---

## 4. Carried forward for T509 — guard backlog, recorded not fixed

These belong to the guard, which this task must not touch. Every count below was re-run by me on
this branch.

**(1) MAJOR-3 — the identical write ships GREEN in `loanschedule`.**
`nexus/internal/apps/loanschedule/emi.go:1720-1721` and `:1726`:

```go
s.outstandingMinor = maxInt64(0, prevSeg.outstandingMinor+prevSeg.disbursedMinor-due)
s.outstandingMinor = maxInt64(0, prevSeg.outstandingMinor+prevSeg.disbursedMinor)
```

inside `updateOutstandingBalances`, whose own comment at `:1688-1690` cites *"calculateOutstandingBalance
[VERIFIED: ProgressiveEMICalculator.java:1253-1255 -> InterestPeriod.updateOutstandingLoanBalance,
InterestPeriod.java:166-186]"* — the same oracle method the four refused sites port — and whose field
declaration at `emi.go:62` reads *"`outstandingMinor` is **the balance** carried INTO this segment."*
Merged, reviewed, vector-graded, and green solely because of the spelling.

Census, tree-wide:

```
$ grep -rnE --include='*.go' '\.[a-zA-Z0-9_]*[Bb]alance[a-zA-Z0-9_]* *=[^=]' nexus/ | grep -vE '==|!=|:='
  4 hits — loanproduct interestperiod.go:262,273,305; repaymentperiod.go:558
$ grep -rn 'outstandingMinor *=' nexus/ | grep -v ':='
  2 hits — loanschedule/emi.go:1720, :1726
```

**6 balance-in-substance assignments exist in the tree; the guard reports 4.** The refusal list
understates the tree, and the ones it names are the ones that were named honestly. This argues for a
better discriminator — not for the withdrawn one.

**(2) B-2 — the composite-literal hole, and the `CANNOT-CATCH` advice that points at it.** Exactly
six writes to the two refused fields go unflagged, all in `loanproduct`:

```
$ grep -rnE --include='*.go' '^[[:space:]]*(balanceCorrectionAmount|outstandingLoanBalance)[[:space:]]*:' nexus/
  interestperiod.go:362,363,387,388   repaymentperiod.go:96,97      (count: 6)
```

`writeTarget` is applied only to `*ast.AssignStmt` and `*ast.IncDecStmt`, so a `KeyValueExpr` is
invisible. **The guard objects to the statement form, not the concept** — and `CANNOT-CATCH` item 8
tells a tripped author *"the fix is a constructor, not an exemption"*, i.e. it **recommends the form
that defeats the check**. Either `writeTarget` covers composite-literal keys, or item 8 stops
recommending that move. It is currently bad advice.

**(3) B-3 — a third undocumented `holdFuncRe` over-match.**
`nexus/internal/apps/loanproduct/repaymentperiod.go:486
func (p *RepaymentPeriod) SetReAgedEarlyRepaymentHolder(v bool)`. `CANNOT-CATCH` item 7(ii) lists one
measured over-match (`…Holds`); `…Holder` is a second shape and is unlisted. Harmless on its own —
the whole point of item 7 is that nobody rediscovers these as bugs.

**(4) MINOR-2 — the column T502 missed, and why saying so matters.**
`m_loan_transaction.outstanding_loan_balance_derived`
[VERIFIED: `LoanTransaction.java:127` — `@Column(name = "outstanding_loan_balance_derived", scale = 6,
precision = 19)`] is a **real stored balance column bearing the same name as the cell under review**.
E-1's downstream sweep checked only `m_loan_repayment_schedule` and never looked at it.

It is written by `LoanBalanceService.updateLoanOutstandingBalances`
[VERIFIED: `LoanBalanceService.java:160-208`; writes at `:174`, `:194`, `:203`] from a **separate
running accumulator** folded over the loan's sorted, non-reversed, monetary `LoanTransaction`s — a
different quantity in a different package (`loanaccount.domain` vs `loanproduct.calc.data`), with no
data path from `InterestPeriod`. **T502's conclusion survives — but by luck rather than by the check
it performed, and that should be said plainly.**

It is also the best available illustration of the corrected test: that column **has** a posting
stream and **is** derived by summation over it, which is precisely why it is a ledger balance and the
four schedule cells are not. It is the `m_trial_balance` shape, and whoever ports
`LoanBalanceService` will meet the real one.

**(5) MINOR-3 — an unperformed check that happened to hold.** T502 called the `sqlShapedRe`
over-match "fail-CLOSED … the safe side" without testing whether it was load-bearing for the packages
that must stay refused. T505 tested it: it is not, for `savings` (`postgres.go:42` carries real SQL
and marks the package anyway). The claim held; the check that should have supported it was never run.
Recorded because the pattern — a true claim with no measurement behind it — is the same failure mode
as E-1.

---

## 5. What a reviewer should attack here

- **Attack the posting-stream test itself.** If you can name a posting stream that
  `InterestPeriod.outstandingLoanBalance` folds — any transaction sequence whose summation produces
  it — then "derive by summation" is available after all, the category argument collapses, and (a)
  becomes the right answer. I traced the cell's full reach to DTOs and found none, and the calc
  package posts nothing.
- **Attack the reconciliation with T501.** I claim one test decides both cases in opposite
  directions. If `SavingsAccountSummary.AccountBalance` and these four cells differ on some *other*
  dimension that the posting-stream test does not capture, the reconciliation is decorative.
- **Attack whether a comment rewrite was the right deliverable.** The bar is still red and the code
  is byte-identical. The defence is that the branch's shipped defect was a *stated reason* that would
  license a real balance write in a later author's hands, and a wrong reason in a package comment is
  a shipped defect. If you think a red bar plus a corrected argument is not worth a branch, say so.
