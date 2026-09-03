# T514 — independent review of T511

Branch: `softhouse/T514-review-t511`, cut from `main`.
Review: `.softhouse/reviews/t514-review-t511/REVIEW.md`.
Target: `softhouse/T511-t505-conditions` (`fc35f4eb`), diffed against its base
`softhouse/T502-loanproduct-i3` (`0b5e8b81`) — never `main..HEAD`.
Oracle: pinned Fineract at `/Users/buv/fineract`, commit `426a23544` (confirmed by `git log`).
`.softhouse/tasks.json` and `.softhouse/guards/**` untouched by me.

## Verdict

**ACCEPT WITH CONDITIONS.**

One sentence: **the guard patch is unmistakably withdrawn (C-1 fully applied), but the
posting-stream argument does not hold as written — it is refuted by the roll-forward it annotates,
which sums transaction-derived `paidPrincipal`, and applied literally it clears
`m_loan.principal_outstanding_derived`, a real persisted balance column Fineract folds over schedule
installments rather than postings.**

Conclusion (b) survives on reachability plus the test-pinned snapshot argument. The four sites stay
RED and that is correct.

## Blocking

- **D-1 (MAJOR)** — remove "no transaction is summed to produce it and none could be" / "this
  expression sums no postings and could not" from `doc.go`, `interestperiod.go` (field block and
  `UpdateOutstandingLoanBalance`), `repaymentperiod.go`. Refuted by `InterestPeriod.java:178`
  (`getPaidPrincipal()`, accumulated via `RepaymentPeriod.java:405` ← `ProgressiveEMICalculator.java:421`
  ← `AdvancedPaymentScheduleTransactionProcessor:929,:967,:2912`) and by
  `ProgressiveEMICalculator.java:922`/`:952` (`paidPrincipal.negated()`). The Go port reproduces the
  first at `interestperiod.go:266`. Restate on reachability.
- **D-2 (MAJOR)** — demote "IS THERE A POSTING STREAM?" from *the* test to supporting observation,
  and record the case it wrongly clears: `m_loan.principal_outstanding_derived`
  [`LoanSummary.java:62-63`, derived `:203-204` from `repaymentScheduleInstallments` via `:339-346`,
  entered at `LoanBalanceService.java:124`].
- **D-3 (MAJOR)** — `interestperiod_test.go:23-26` still teaches "never becomes a database column"
  and cites `doc.go` as evidence for it. Sole uncorrected residue in Go code; it is the doc comment
  on the falsifiable test, i.e. the text read at the decisive moment.

## Non-blocking

- **D-4 (MINOR)** — the "6 balance-in-substance vs 4 reported" census is wrong twice: the grep cannot
  match compound assignment (misses `savings/summary.go:53 s.AccountBalance += effect`), and "the
  guard reports 4" contradicts the 7-finding transcript in the same handoff. Corrected: 7 reported,
  ≥9 in substance, 6 structurally invisible. Conclusion strengthens.
- **D-5 (MINOR)** — drop the false universal "every oracle caller adds a NEGATED principal amount" on
  `AddBalanceCorrectionAmount` (`ProgressiveLoanInterestScheduleModel.java:257,:290` are reached with
  positive amounts from `ProgressiveEMICalculator.java:991,:993,:489`); mark E-1's unmarked closing
  sentence; note `emi.go`'s `:1253-1255` is the same off-by-one this branch corrected to `:1254-1256`;
  hand T509 the three missing decisions on the `go/types` discriminator (fail-CLOSED on unresolved
  flow being the decisive one).

## Verified by running, not by reading

- `git diff -U0 0b5e8b81 softhouse/T511-t505-conditions -- nexus/` → 291 changed lines, **0** non-comment.
- `bash .softhouse/guards/check-ledger-invariants.sh` → EXIT=1, the four sites at
  `interestperiod.go:262:4,273:2,305:2` and `repaymentperiod.go:558:4` — exactly as reported; the
  writes are unchanged and the moves are comment-driven.
- Derive-on-read accessor injected → `TestOutstandingLoanBalanceIsASweptSnapshot` FAILs at
  `interestperiod_test.go:57`, 70000 vs 90000 minor units. Reverted; the test is genuinely falsifiable (P-45).
- `go build ./...`, `go vet ./internal/apps/loanproduct/`, `go test ./...` all exit 0;
  `gofmt -l internal/apps/loanproduct/` empty. Integer minor units throughout; no float on any money path.
- Composite-literal census exact (`interestperiod.go:362,363,387,388`, `repaymentperiod.go:96,97`);
  `…Holder` over-match exact (`repaymentperiod.go:486`); `writeTarget` dispatch confirmed at
  `ledgerguard/main.go:549-570`; `CANNOT-CATCH` item 8 at `main.go:793-794` does recommend the evading form.
- `m_loan_transaction.outstanding_loan_balance_derived` confirmed: `LoanTransaction.java:127`,
  `LoanBalanceService.java:160-206` writing at `:174,:194,:203` from a fold over sorted non-reversed
  monetary transactions. T511's characterisation of it is **true**.
- Every C-2 citation opened and exact: `@JsonExclude` at `:45`/`:68` only; `:65`/`:66` bare;
  `JsonExcludeAnnotationBasedExclusionStrategy.java:31-34`; `getSavedModel:110-128` → `extractModel:95`
  → `recalculateInterestForDate:122`; `InterestPeriod.java:151` → `RepaymentPeriod.java:389-403` →
  `ProgressiveLoanScheduleGenerator.java:132` → `LoanSchedulePlan.java:65,:77`; zero
  `@Entity/@Table/@Column` on both terminals; zero `JournalEntry` in `.../loanproduct/calc/`;
  `:906`→`:907` correct.
