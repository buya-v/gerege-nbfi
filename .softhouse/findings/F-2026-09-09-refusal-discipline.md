# F-2026-09-09 — loanschedule REFUSES what it cannot grade. No other context does.

**Status:** OPEN, program-level. Supersedes nothing; extends
[`F-2026-09-09-fee-penalty-blind.md`](F-2026-09-09-fee-penalty-blind.md), which turns out
to be one instance of a general shape.
**Found by:** the driver, extending the fee/penalty census across all 15 contexts, and
then checking — before reporting — whether each always-zero field drives real code.

## The census

A money-named field whose ONLY observed value across every vector that carries it is zero
is a term the corpus **cannot discriminate**: a port that drops it, or returns a constant
zero for it, passes every vector that mentions it.

Instrument control-tested before use, both directions:
`loan.fee_outstanding_minor` → `{0}` (expected all-zero) and
`loan.principal_outstanding_minor` → `{10000000, 10005050, 4185009}` (expected NOT
all-zero). It discriminates.

| context | always-zero money field | in N vectors |
|---|---|---|
| loanschedule | `installment_rounding_multiple_minor` | **50** |
| loan | `fee_outstanding_minor` | 5 |
| loan | `penalty_outstanding_minor` | 5 |
| shares | `total_pending_shares` | 4 |
| workingcapital | `total_disbursement` | 3 |
| workingcapital | `total_repayment` | 3 |
| workingcapital | `principal_paid` | 3 |
| workingcapital | `total_discount_fee` | 3 |
| workingcapital | `unrealized_income_from_discount_fee` | 3 |
| loan | `fee`, `penalty` | 2 |
| loan | `charges_due_at_disbursement_minor`, `leftover_minor` | 1 |

## THE LOANSCHEDULE ROW IS NOT A DEFECT — and this is the finding

`installment_rounding_multiple_minor` is zero in all **50** loanschedule vectors, which
looks like the worst row in the table. It is the best one. The port **refuses** the input
it cannot grade, in code, naming the reason [`loanschedule/generator.go:384-387`]:

    if req.InstallmentRoundingMultipleMinor != 0 {
        return ungraded("InstallmentRoundingMultipleMinor is %d; the capture seam DROPS this
            field silently, so no capture taken through it can grade it", ...)
    }

with the same treatment four lines above for `DownPaymentPercentage` ("no capture has ever
produced a down-payment row") [`:380-382`]. A request carrying a non-zero value is
**refused, not silently computed**. The blind spot is declared, in the code, at the seam.

**That discipline exists in exactly one context.** Count of `ungraded(`/`unsupported(`
call sites, non-test, per context:

    loanschedule    19
    workingcapital   0
    loan             0
    charges          0
    shares           0

## The concrete cost, in workingcapital

`workingcapital/balance.go:87-92` ports `getUnrealizedIncomeFromDiscountFee`:

    max(TotalDiscountFee - TotalDiscountFeeAdjustment - RealizedIncomeFromDiscountFee, 0)

All five of that context's money terms are zero in all three vectors that carry them. So:

* the subtraction is never exercised with non-zero operands, and
* **the `max(…, 0)` clamp is never exercised at all** — a clamp is only observable when the
  expression it guards goes negative, which requires non-zero operands.

A port that omits the clamp passes all three vectors. A port that returns a constant zero
passes all three vectors. And unlike loanschedule, **nothing refuses the input** — a
non-zero discount fee would be silently computed by an ungraded path.

The discount fee is not incidental to this product. It is the revenue of a discounting
facility; `TotalDiscountFee` is the term `ApplyDisbursement` sets [`balance.go:38`].

## What would close it

Per context, one of two things — and the second is a legitimate, cheap, oracle-free answer:

1. **A capture that exercises the term**, then a vector, then a drive that dies on it.
   For workingcapital: a facility with a non-zero discount fee, and an adjustment or
   realized income large enough to drive the clamp expression **negative**, since that is
   the only observation that grades the clamp.
2. **An `ungraded()` refusal at the seam**, matching `loanschedule/generator.go:384`,
   naming what the capture seam cannot produce. This does not grade the term — it stops
   the port from silently answering a question no vector has ever asked.

**Option 2 is available today, needs no oracle, and is the one loanschedule already
chose.** A context with zero refusals is not thereby a context with no blind spots; it is
a context whose blind spots are undeclared.

## Caveats, stated

* The 19-vs-0 count is raw. Contexts differ in surface area, and loanschedule is the
  largest and oldest. The count is evidence of a *discipline gap*, not a defect tally.
* An always-zero field may be structurally zero for MNT rather than under-captured. That
  distinction is exactly what an `ungraded()` refusal, or a one-line argument, should
  record — and today, outside loanschedule, neither exists.
* `shares.total_pending_shares` and the single-vector loan rows are weak evidence on their
  own; they are listed for completeness, not as claims.

## Note

`OH-PROM-O` was live on `loan` and `workingcapital` while this was written, and its brief
(P4) points it at the workingcapital captures. If it reaches this independently, that is
corroboration. If it does not, this is the gap in that run, and the comparison is the
reason this was recorded before the run landed rather than after.

---

## UPDATE, same day — `loan` adopted the discipline, in a SECOND DIALECT

`OH-PROM-O` merged (`03b4aefb`) while this finding was open, and did something it was
never asked to do: `loan/outstandingbalance.go` returns **`ErrNotTranscribed`** for a
posting type no committed capture observes — *"The derivation ports the transcribed subset
of the oracle's rule; behaviour for an untranscribed type is refused, never guessed."*

That is this finding's remedy (2), arrived at independently, and it corroborates the
finding rather than being prompted by it: the run's brief said nothing about refusals, and
the agent had no access to this file.

**Re-measured after the merge:**

    loanschedule    ungraded()/unsupported() 19   NotTranscribed 0
    loan            ungraded()/unsupported()  0   NotTranscribed 6
    workingcapital  ungraded()/unsupported()  0   NotTranscribed 0
    charges         ungraded()/unsupported()  0   NotTranscribed 0
    shares          ungraded()/unsupported()  0   NotTranscribed 0

**And a correction to how this finding must be measured from now on.** The original census
counted `ungraded(`/`unsupported(` — **loanschedule's spelling**. That is a dialect, not
the property. The property is "does the port refuse an input it cannot grade", and `loan`
now satisfies it through a Go error sentinel instead. A census that counts only one
spelling will report a context as undisciplined the moment it chooses the other idiom.

The original table is **not** retracted: measured at `955499ec`, the commit where this
finding was written, `loan` had **0 of both** dialects (control: loanschedule 19 at the
same commit, matching the working tree). The finding was true when written. It is the
*method* that needed widening, not the result.

*(That control matters: the first attempt to measure this at a past commit used a
`git grep <rev> -- <pathspec>` form that returned 0 for loanschedule too. Reported as
written it would have "shown" that loanschedule had no refusals either. The known control
— loanschedule must read 19 — caught it. Third time in this session that a control
changed a conclusion.)*

**`workingcapital` is unchanged and remains the live instance**: five always-zero money
terms, an unexercised `max(…, 0)` clamp, and no refusal in either dialect.
