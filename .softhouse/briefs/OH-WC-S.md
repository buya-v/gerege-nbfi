# OH-WC-S — declare workingcapital's blind spots. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-wcs` (branch `feat/OHWCs`)
Work ONLY in that directory.

## THE ORACLE IS HELD BY ANOTHER RUN. YOU MAY NOT CAPTURE.

`OH-GL-R` is creating loan products, clients and loans, and re-running COB. Oracle state is
MOVING for this entire run. **Take no captures. Issue no POST/PUT/DELETE. Do not advance
the business date.** A read-only health probe is permitted; nothing else. If you conclude a
property needs a fresh capture, that is a **finding to record, not a capture to take**.

Everything below is answerable from the tree.

## The finding you are closing

Read `.softhouse/findings/F-2026-09-09-refusal-discipline.md` first. Its measurement:

**`loanschedule` refuses inputs it cannot grade. `workingcapital` refuses nothing.**

    ungraded()/unsupported() call sites, non-test:
      loanschedule    19
      workingcapital   0
      loan             0  (but see below — loan now refuses in a SECOND DIALECT)
      charges          0
      shares           0

`loanschedule/generator.go:384-387` is the model:

    if req.InstallmentRoundingMultipleMinor != 0 {
        return ungraded("InstallmentRoundingMultipleMinor is %d; the capture seam DROPS this
            field silently, so no capture taken through it can grade it", ...)
    }

with the same treatment for `DownPaymentPercentage` at `:380-382`. The blind spot is
**declared in code, at the seam**, and a non-zero value is refused rather than silently
computed.

`loan` has since adopted the discipline in a different idiom — `ErrNotTranscribed` in
`loan/outstandingbalance.go` — so **the property is "does the port refuse an input it
cannot grade", NOT a particular spelling.** Pick whichever idiom fits `workingcapital`'s
existing style and say why.

## The concrete hole

`workingcapital/balance.go:87-92`:

    // UnrealizedIncomeFromDiscountFee ports getUnrealizedIncomeFromDiscountFee:
    // max(totalDiscountFee - totalDiscountFeeAdjustment - realizedIncomeFromDiscountFee, 0)

**All five of this context's money terms are zero in all three vectors that carry them** —
`total_disbursement`, `total_repayment`, `principal_paid`, `total_discount_fee`,
`unrealized_income_from_discount_fee` (WC-02, WC-03, WC-04).

Therefore:

* the subtraction never sees a non-zero operand, and
* **the `max(…, 0)` clamp is NEVER EXERCISED** — a clamp is observable only when the
  expression it guards goes negative, which requires non-zero operands.

A port that omits the clamp passes all three vectors. So does one returning a constant
zero. And nothing refuses the input, so a non-zero discount fee would be **silently
computed by a path no vector grades**. The discount fee is the revenue of a discounting
facility, not an incidental term.

## Your task

**Verify the above against the tree before acting on it.** The driver's census could be
wrong; a control-tested re-measurement is the first thing you do. If any part of it does
not hold, **say so and stop** — a corrected finding is a better outcome than a change built
on a bad premise.

Then, for each `workingcapital` money term the committed captures cannot discriminate:

1. **Refuse it at the seam**, in the idiom that fits, naming *what the capture seam cannot
   produce and why* — the way `loanschedule` does. This does not grade the term; it stops
   the port silently answering a question no vector has ever asked.
2. **Record what a capture would have to contain** to grade it, so the next agent with the
   oracle knows exactly what to take. For the clamp specifically that means an adjustment
   or realized income large enough to drive the expression **negative** — nothing else
   grades a clamp.

**Do not weaken or delete an existing vector to make anything look better.** Do not touch
`.softhouse/guards/ledger-invariants.baseline`.

## What SUCCESS looks like

A `workingcapital` port that **refuses** every money input no committed capture can grade,
with the reason stated at the seam, plus a written record of the captures that would close
each one. **Zero new vectors is a perfectly good outcome** — you have no oracle, so you
cannot honestly produce one.

If a refusal you add would fire on an input an EXISTING vector supplies, you have
mis-drawn the boundary: the vectors must all still pass. That is your primary control.

## Measuring it

`.softhouse/briefs/tools/kills.sh`, `redcount.sh`. **Repaired 2026-09-09**: no silent `0` —
they exit 2 with empty stdout and a reason on stderr. **An empty result means the
MEASUREMENT FAILED.** Controls:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
    redcount.sh <worktree> workingcapital                       -> 4

If a control is wrong, the instrument is wrong — not the tree. The four existing
`workingcapital` drives must still kill after your change; re-measure and report each.

## THE RULE ON INERT DRIVES
If you register a drive, **a zero kill is a finding to resolve** — promote a vector that
sees it, or delete it with the argument. Never merge one inert. Report every kill count.

## Rules of evidence
- **Cite `file:line`** for every claim. Line numbers from the FILE, not from a
  comment-stripped view — the driver got that wrong once this week and an agent caught it.
- Never synthesise a value you did not observe.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- Balances **derived, never written** (I-3); append-only (I-4).
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `workingcapital`.** Wandering outside it is a rejection — in
  particular do NOT touch `loan`, `investor` or `ledger`; another run holds them.

## The bar
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh`. Expect exit 2 as the
§4.4.2 recorded decision with the ledger finding set at **exactly 12 (class, file) pairs**.
All existing vectors must still pass. Report every drive's kill count.
