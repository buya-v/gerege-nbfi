# F-2026-09-10 — workingcapital now REFUSES the money terms no capture can grade

**Status:** CLOSED for the discipline gap (the port refuses); OPEN for the terms
themselves (no capture grades them yet).
**Extends:** [`F-2026-09-09-refusal-discipline.md`](F-2026-09-09-refusal-discipline.md).
**Scope:** one bounded context, `workingcapital`. No vector added, changed or
deleted; `.softhouse/guards/ledger-invariants.baseline` untouched.

## What was measured before anything was changed

Every number below was re-measured on the tree, with the instrument's own known
controls, not copied from the earlier finding.

Refusal census, non-test Go, both dialects (`ungraded(`/`unsupported(` and
`ErrNotTranscribed`):

    loanschedule     ungraded/unsupported=19  ErrNotTranscribed=0   (control: must be 19)
    workingcapital   ungraded/unsupported=0   ErrNotTranscribed=0
    loan             ungraded/unsupported=0   ErrNotTranscribed=3
    charges          ungraded/unsupported=0   ErrNotTranscribed=0
    shares           ungraded/unsupported=0   ErrNotTranscribed=0

The known control (loanschedule == 19) held, so the instrument discriminates;
`workingcapital` was genuinely 0 of both **before** this change.

A note for the next census: `workingcapital` now refuses through a *third*
spelling, `ErrNoGradedCapture`, so a census that counts only the two dialects
above will freshly report it as 0. The doc comment that introduces the sentinel
deliberately avoids the literal tokens of the other idioms — an earlier draft
contained them and the raw grep counted the comment, briefly making
`workingcapital` read as 2 `ungraded(`/`unsupported(` sites and 1
`ErrNotTranscribed`. The census counts substrings in comments, so prose about a
dialect is indistinguishable from a call site of it. Measured after the change:

    workingcapital   ungraded/unsupported=0   ErrNotTranscribed=0   ErrNoGradedCapture=3

Money-cell scan over `.softhouse/vectors/workingcapital/*.json`. Five terms are
zero in all three vectors that carry them (WC-02, WC-03, WC-04), while the
principal and the outstanding aggregates are non-zero:

    total_disbursement                 0   x3   (WC-02/03/04)
    total_repayment                    0   x3   (WC-02/03/04)
    principal_paid                     0   x3   (WC-02/03/04)
    total_discount_fee                 0   x3   (WC-02/03/04)
    unrealized_income_from_discount_fee 0  x3   (WC-02/03/04)
    principal (balance)             100051 x3   (WC-02/03/04)
    disbursement.principal          100051 x1   (WC-03; a different seam)
    principal_outstanding           100051 x3
    total_expected_repayment        100051 x3
    total_outstanding               100051 x3

Nine further stored terms — `principal_adjustment`, `fee`, `fee_paid`,
`penalty`, `penalty_paid`, `realized_income_from_discount_fee`,
`overpayment_amount`, `total_discount_fee_adjustment`,
`breach_pastdue_amount` — appear in **no committed vector at all**; the vectors
transcribe only nine balance cells. They are present only in the raw capture
(`wc-loan-detail-raw.json`), which serialises each as `0.0`. A term absent from
the vectors is discriminated by no vector, so it is ungraded a fortiori.

The capture itself (`wc-loan-detail-raw.json`, cited by WC-02/03/04) records
`principal 1000.51` and every other balance column `0.0`, including
`totalDiscountFee 0`, `totalDiscountFeeAdjustment 0`, `realizedIncomeFromDiscountFee 0`.
So the finding's premise holds: the `max(…, 0)` clamp in
`UnrealizedIncomeFromDiscountFee` has never had a non-zero operand and has never
been exercised.

## The change: refuse at the seam, in a Go-error idiom

`workingcapital/balance.go` now declares

    ErrNoGradedCapture = errors.New("workingcapital: money term not graded by any committed capture")

and `WorkingCapitalLoanBalance.ValidateGradedDomain()` `[balance.go:78-98]`
refuses a balance carrying a non-zero value in any money term the committed
captures cannot discriminate, naming the term and the reason the capture seam
cannot produce it. It is wired into both seams that admit a balance state:

* `ApplyDisbursement` now returns `error` and validates the would-be state
  **before** touching the receiver, so a refused disbursement is a no-op
  `[balance.go:111-121]`. The graded seed `(100051, 0)` is admitted.
* `FindByLoanID` (the read of `m_wc_loan_balance`) validates the decoded row
  before returning it `[postgres.go:441-445]`.

**Why this idiom, not `loanschedule`'s `ungraded()` string.** `workingcapital`'s
seam is a value seam, not a request seam: the input is a `WorkingCapitalLoanBalance`
struct, and every getter is a total function with no error channel. A Go sentinel
is the spelling `loan` already chose (`ErrNotTranscribed`, `loan/outstandingbalance.go`)
for exactly this shape — "the derivation ports the transcribed subset; behaviour
for an untranscribed input is refused, never guessed" — and it is `errors.Is`-able,
so a caller (or the conformance harness) can distinguish a refusal from a decode
failure. `loanschedule`'s free-form `ungraded(...)` would lose both properties
here. The property the finding asks for is the refusal, not the spelling.

**Boundary drawn.** `Principal` is the one stored money term the pinned capture
observes non-zero (100051), so it is the one stored term *not* refused. Every
other stored term is refused; the derived folds remain pure over a state the
seam has admitted. This is the narrowest boundary that keeps all five existing
vectors passing.

## What each refusal would need in order to be graded

Every write path below is a `file:line` in the reference oracle
(`/Users/buv/fineract`, pinned `426a23544e8426a38ae43ae404670a0a7e85b9eb`), found
by locating the setter call site — not synthesised.

| term | committed vectors | oracle write path that sets it | capture that would grade it |
|---|---|---|---|
| `principal_paid` | 0 in WC-02/03/04 | `WorkingCapitalLoanBalanceUpdater.java:46` (repayment allocation) | a repayment posted to the seeded loan, then the balance read-back |
| `principal_adjustment` | absent (capture `0.0`) | `WorkingCapitalLoanTransactionReprocessingServiceImpl.java:343` (excess principal) | a reprocessing / excess-principal event, then read-back |
| `fee` | absent (capture `0.0`) | `WorkingCapitalLoanChargeWritePlatformServiceImpl.java:466` (non-penalty charge added) | a fee charge added to the loan, then read-back |
| `fee_paid` | absent (capture `0.0`) | `WorkingCapitalLoanBalanceUpdater.java:47` | a repayment whose allocation has a fee portion |
| `penalty` | absent (capture `0.0`) | `WorkingCapitalLoanChargeWritePlatformServiceImpl.java:464` (penalty charge added) | a penalty charge added to the loan, then read-back |
| `penalty_paid` | absent (capture `0.0`) | `WorkingCapitalLoanBalanceUpdater.java:48` | a repayment whose allocation has a penalty portion |
| `realized_income_from_discount_fee` | absent (capture `0.0`) | `WorkingCapitalLoanDiscountFeeAmortizationServiceImpl.java:116` (COB), `WorkingCapitalLoanWritePlatformServiceImpl.java:1099` | a non-zero product discount amortized through at least one COB/repayment |
| `overpayment_amount` | absent (capture `0.0`) | `WorkingCapitalLoanBalanceUpdater.java:49` | a repayment larger than the amount due |
| `total_disbursement` | 0 in WC-02/03/04 | **no caller of `setTotalDisbursement` anywhere under `src/main`** | none producible: the column is structurally zero in the reference, so no capture can grade it |
| `total_discount_fee` | 0 in WC-02/03/04 | `WorkingCapitalLoanBalance.java:117` (set from the product `discount` inside `applyDisbursement`, `:115-121`), `WorkingCapitalLoanWritePlatformServiceImpl.java:1074` | a product whose `discount` is non-zero, disbursed, then read-back |
| `total_discount_fee_adjustment` | absent (capture `0.0`) | `WorkingCapitalLoanWritePlatformServiceImpl.java:1056` (discount change) | a discount change on a discounted, disbursed facility |
| `breach_pastdue_amount` | absent (capture `0.0`) | `WorkingCapitalLoanBreachScheduleServiceImpl.java:553` | a seed configuring a breach/delinquency range and a past-due breach |

`total_disbursement` deserves its own line: it is not merely under-captured, it
has **no write path in the oracle's working-capital module** (the generated
mapper only reads it). The port already never sets it; the refusal protects
against a divergent database row, and the record says no capture can close it.
This is the "structurally zero for MNT rather than under-captured" distinction
the parent finding's caveat asked for, now stated per term.

Two of the parent finding's five always-zero terms are **derived**, not stored:
`total_repayment` is the fold `principal_paid + fee_paid + penalty_paid`
(`WorkingCapitalLoanBalance.java:147-149`) and
`unrealized_income_from_discount_fee` is the clamp over the discount terms
(`:151-154`). Neither can be non-zero unless a stored operand is, and every
stored operand is refused above, so the derived folds are refused transitively;
there is no separate column and therefore no separate refusal to add.

## The clamp, specifically

`UnrealizedIncomeFromDiscountFee` ports the oracle at
`WorkingCapitalLoanBalance.java:151-155` (the `.max(BigDecimal.ZERO)`
clamp is the statement at `:154`):
`max(totalDiscountFee - totalDiscountFeeAdjustment - realizedIncomeFromDiscountFee, 0)`.

Nothing grades a clamp unless the guarded expression goes **negative**. With all
three operands zero, both the correct `max(…, 0)` and a clamp-less subtraction
return 0; so do a constant-zero port and a dropped-term port. All pass every
committed vector.

The capture that would grade it must therefore contain a balance in which

    totalDiscountFeeAdjustment + realizedIncomeFromDiscountFee > totalDiscountFee

so the un-clamped expression is negative and the clamp is the only thing making
the result 0. The oracle reaches that state through a non-zero product discount
(`totalDiscountFee` set at disbursement, `WorkingCapitalLoanBalance.java:117`),
amortization raising `realizedIncomeFromDiscountFee`, and a discount change
raising `totalDiscountFeeAdjustment` and reducing `principal`
(`WorkingCapitalLoanWritePlatformServiceImpl.java:1056-1057`). A discount
reduction after some income is realized, or any adjustment exceeding the
remaining discount, drives it negative. **Nothing short of a negative un-clamped
expression grades the clamp.**

## No new vectors, and no new drives — deliberately

There is no oracle in this run, so no vector could be honestly produced.
`Zero new vectors` is the correct outcome. By the same token no drive was
registered: a wrong implementation that omits the clamp, or returns a constant
zero, still passes all three committed vectors (that is precisely the hole), so
a drive for it would be inert by construction. Registering one and reporting a
zero kill would be manufacturing a measurement that cannot discriminate. The
refusal itself is covered by unit tests (`TestApplyDisbursementRefusesUngradedDiscount`,
`TestValidateGradedDomain`), which are not drives and make no parity claim.

## Controls and kill counts (re-measured after the change)

Instrument controls, all still exact:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
    redcount.sh <worktree> workingcapital                       -> 4

The four existing `workingcapital` drives all still kill, re-measured after the
change. No drive was added or removed by this change, and none is inert:

    workingcapital-wrong-list-row-mapping   -> 1
    workingcapital-wrong-status-ordinal     -> 1
    workingcapital-wrong-total-outstanding  -> 3
    workingcapital-wrong-tranche-dropped    -> 1

## Bar

`go build ./...` clean; `go test ./...` clean; `bash .softhouse/conformance.sh`
still exits 2 as the §4.4.2 recorded decision with the ledger finding set at
exactly the 12 `(class, file)` pairs in
`.softhouse/guards/ledger-invariants.baseline` (untouched), and all 46 parity
vectors still match.
