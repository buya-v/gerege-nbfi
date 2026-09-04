# T526 — T519's residuals (cleanup beside T516)

Scope touched: `nexus/internal/apps/loanproduct/repaymentperiod.go`,
`nexus/internal/apps/loanproduct/doc.go`. Nothing else.

Pinned Fineract checkout verified detached at
`426a23544e8426a38ae43ae404670a0a7e85b9eb` [VERIFIED: `/home/user/fineract/.git/HEAD`]
— matches the pinned commit of record `426a23544`.

## Item 1 — two stale `[VERIFIED:]` citations in repaymentperiod.go

Source: `/home/user/fineract/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/data/RepaymentPeriod.java`
at the pinned commit.

### 1a. `OutstandingLoanBalance()` (repaymentperiod.go:342, was citing `:377-389`)

Read `RepaymentPeriod.java:360-429`. `getOutstandingLoanBalance()` actually
spans **lines 389-403** — signature at 389, closing brace at 403
[VERIFIED: RepaymentPeriod.java:389-403]. The old range `:377-389` mostly
covers the *javadoc for the neighboring `getUnrecognizedInterest()`* method
(lines 375-380) plus the `getOutstandingLoanBalance()` signature line only
(389) — it does not resolve to the method body at all.

**Substance check, corrected range vs. the Go port** — holds. Java (389-403):
`lastInterestPeriod.getOutstandingLoanBalance().plus(getBalanceCorrectionAmount()).plus(getCapitalizedIncomePrincipal()).plus(getDisbursementAmount()).plus(getPaidPrincipal()).minus(getDuePrincipal())`,
then `MathUtil.negativeToZero(...)`. Go: `last.OutstandingLoanBalance().plus(last.BalanceCorrectionAmount()).plus(last.CapitalizedIncomePrincipal()).plus(last.DisbursementAmount()).plus(p.PaidPrincipal()).minus(p.DuePrincipal()).negToZero()`
— same five terms, same order, same floor. Fixed the citation to
`:389-403`; no code or doc-comment prose changed.

### 1b. `AddPaidPrincipalAmount()` (repaymentperiod.go:354, was citing `:391-393`)

`addPaidPrincipalAmount(Money paidPrincipal)` actually spans **lines
405-407** [VERIFIED: RepaymentPeriod.java:405-407]. The old range `:391-393`
pointed inside the *body of `getOutstandingLoanBalance()`* (the
`Memo.of(...)` lambda opening and its first two statements) — a different
method entirely.

**Substance check, corrected range vs. the Go port** — holds. Java (405-407):
`this.paidPrincipal = MathUtil.plus(this.getPaidPrincipal(), paidPrincipal, getMc())`.
Go: `p.paidPrincipal = p.PaidPrincipal().plus(paid)` — same accumulation.
Fixed the citation to `:405-407`.

Both stale citations were off by the same cause: the oracle file has since
drifted (or was misread) by a roughly 12-14 line offset in this region: the
method boundaries the old citations pointed at belong to the neighboring
method above/below the one being documented, not to a different substantive
claim. Corrected in place, substance re-confirmed, no other prose touched.

## Item 2 — loose doc claim in doc.go about savings/summary.go

`doc.go`'s "guard patch is not the answer yet" section illustrated why a
directory-based (package-persistence-surface) discriminator was withdrawn, by
pointing at `nexus/internal/apps/savings/summary.go`'s
`s.AccountBalance += effect` and calling it "a genuine ... real balance
write."

Measured directly:

- `Add` is declared `func (s SavingsAccountSummary) Add(effect MinorUnits) SavingsAccountSummary`
  [VERIFIED: nexus/internal/apps/savings/summary.go:52-55] — a **value
  receiver**. `s.AccountBalance += effect` at line 53 mutates the local copy
  `s`, not any stored state; the method returns the copy and the caller must
  reassign it. That is a pure fold, the same shape as the four sites this
  package's doc.go otherwise defends (`interestperiod.go`
  `UpdateOutstandingLoanBalance`/`AddBalanceCorrectionAmount`,
  `repaymentperiod.go`'s equivalents) — none of which write to storage
  either.
- So "genuine real balance write," read as "this line writes stored state,"
  is **not accurate** — same finding T519 made.
- The tension the task flagged is real and I did not paper over it: the
  ledger guard *does* currently flag `savings/summary.go:53` under
  `I3-FIELD-WRITE` (per doc.go's own guard-census cross-reference), and that
  flag is *not* a false positive the way the four in-package sites are argued
  to be. The reason is reachability, not the mutation itself:
  `SavingsAccountSummary.AccountBalance` — the same field `Add` folds into —
  is what `PostgresSummaryRepository.Upsert` sends as the persisted
  `account_balance_derived` column [VERIFIED:
  nexus/internal/apps/savings/postgres.go:113,120,149 — INSERT column list at
  120, `summary.AccountBalance.FormatDecimal(...)` passed as the matching
  exec arg at 149]. So the field this fold produces genuinely does reach a
  persisted balance column elsewhere in the same package — unlike this
  package's four sites, which doc.go already establishes (lines ~95-103)
  reach no such column.

**What I changed:** rewrote the paragraph (doc.go, "Nor is a guard patch the
answer yet...") to say the fold is a value-receiver pure fold over a copy —
not itself a write to stored state — while still correctly arguing the
directory-move discriminator is unsound, because the field IS reachable to a
persisted column via a different call site (`postgres.go`), which is exactly
the LEG-2/reachability criterion doc.go argues for elsewhere. The
rhetorical point survives intact (a file move would still wrongly disarm a
site that should stay guard-flagged); only the inaccurate mechanism
description ("genuine real balance write" happening *at that line*) is
corrected. Diff is in this branch; see `doc.go` around the "Nor is a guard
patch the answer yet" heading.

**Not touched:** `nexus/internal/apps/savings/summary.go` and
`nexus/internal/apps/savings/postgres.go` were read only, never edited, per
the scope guard — the file describing them (`loanproduct/doc.go`) is the only
one in scope.

## Item 3 — gofmt

`cd nexus && gofmt -l .` reports 4 files, **none inside
`nexus/internal/apps/loanproduct/`**:

```
internal/apps/loanschedule/contract/contract.go
internal/apps/parties/client.go
internal/apps/parties/group.go
internal/apps/parties/legalform.go
```

Per the task's instruction these belong to whichever task owns
`loanschedule`/`parties` and are reported, not fixed, here.

## Verification run

From `nexus/`:
- `go build ./...` — clean, no output.
- `go vet ./...` — clean, no output.
- `gofmt -l .` — 4 hits, all outside scope (item 3 above); zero inside
  `loanproduct/`.
- `go test ./internal/apps/loanproduct/...` — `ok`.

Did not run the repo-wide conformance harness (`.softhouse/conformance.sh`)
per the task note that the bar is currently RED for an unrelated guard
repair not on main; not caused by this change and out of scope to fix.

## Files changed

- `nexus/internal/apps/loanproduct/repaymentperiod.go` — two `[VERIFIED:]`
  line-range corrections only, no logic or prose change.
- `nexus/internal/apps/loanproduct/doc.go` — one paragraph restated for
  accuracy (savings/summary.go:53 characterization), rhetorical point
  preserved.
- `.softhouse/handoff/T526-t519-residuals.md` — this file.

## Branch

```
softhouse/T526-t519-residuals
```

Pushed. `git ls-remote --heads origin refs/heads/softhouse/T526-t519-residuals`:

```
7187d6ec221609eb0c371e3d10ffa0e60a1b1859	refs/heads/softhouse/T526-t519-residuals
```

