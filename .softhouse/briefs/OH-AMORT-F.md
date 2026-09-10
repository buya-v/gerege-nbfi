# OH-AMORT-F — ONE property: principal amortizes to ZERO. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-amortf` (branch `feat/OHAMORTf`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.** Everything is
promotable from captures already committed on `main`.

## THE PROPERTY — it is a named non-negotiable, and nothing grades it

`CLAUDE.md` lists the property invariants the bar exists to defend: *"double-entry balances;
**principal amortizes to zero**; splits sum to whole."* The first and third are graded. **The
second is not** — no `loan` vector grades a whole schedule.

> **Over a full repayment schedule, the sum of the per-period principal components equals
> the disbursed principal EXACTLY, and the final outstanding principal balance is EXACTLY
> zero — in integer minor units, with no residue.**

Two committed captures see it, and the driver has verified both:

    .softhouse/capture/loan/out/loan-2-schedule-raw.json
      13 periods, principalDisbursed 100000.0, sum(principalDue) 100000.0,
      final principalLoanBalanceOutstanding 0.0

    .softhouse/capture/loan/out/loan-5-schedule-raw.json
      13 periods, principalDisbursed  41850.09, sum(principalDue)  41850.09,
      final principalLoanBalanceOutstanding 0.0

**Prefer loan 5.** `41850.09` is **not a round number**: 4185009 minor units over 13 periods
does not divide evenly, so the schedule must carry the remainder somewhere. That is exactly
where a truncating or drifting port fails, and `100000.0` would hide it. Grade loan 2 as
well only if it carries a fact loan 5 does not — and say which.

**Verify both numbers against the files before building on them.** Three of this driver's
briefs have been factually wrong today and every one was caught by the agent that checked.

## THE MAP

* **Schedule shape** — `repaymentSchedule.periods[]`; the fields that matter are
  `principalDisbursed`, `principalDue`, `principalLoanBalanceOutstanding`. Period 0 is the
  disbursement row and carries no `principalDue`; **check this yourself** rather than
  assuming an index.
* **Vector shape** — copy `.softhouse/vectors/loan/LN-L09-journal-entry-batch-balance.json`.
  Its `request` holds observed legs and its `expect` holds derived totals; yours holds the
  observed per-period principal components and expects the sum and the final balance.
* **Registration** — `nexus/internal/apps/loan/conformance/impl.go`, **fifteen** worked
  `loan-wrong-*` examples.
* **Existing schedule coverage, so you do not duplicate it:**
  `LN-L06-schedule-interest-period-1` grades ONE period's INTEREST. The `loanschedule`
  context's 50 vectors grade the schedule GENERATOR at a different seam. **Neither grades
  whole-schedule principal amortization on a loan read-back.** Confirm that yourself.

## Defect shapes worth a drive — pick what the capture DISCRIMINATES

A port can amortize wrongly in ways a single period cannot reveal:

* the final balance left non-zero by a residue (the remainder never placed);
* the remainder placed in the FIRST period instead of the LAST, so the sum is right and
  every period is wrong;
* a truncated per-period principal, so the sum falls short of the disbursed amount.

**Register only what this capture actually kills.** A drive that kills ZERO is a finding to
resolve — promote a vector that sees it, or **delete it with the argument**. Report every
kill count and **prove the instrument was live** (controls below, plus an existing `loan`
drive that still kills).

**Do not manufacture coverage.** If a shape is not discriminated, say so and record what a
capture would need. `OH-INV-Z` did exactly that and it was the right call.

## Measuring it
    kills.sh loan loan-wrong-journal-entry-batch-maps-fee-to-disbursement-accounts -> 1
    kills.sh loan loan-wrong-summary-drops-penalty                                 -> 2
    kills.sh loanschedule loanschedule-wrong-days-in-year-365                      -> 45
    kills.sh parties      parties-wrong-iota-ordinals                              -> 12
    kills.sh charges      charges-wrong-rounding-half-even                         -> 1

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** If a control is wrong, the instrument is wrong.

After your change `loan-go` must still pass **all 15** loan vectors and **all 15** existing
drives must still kill. That is your primary control.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  `41850.09` transcribes to `4185009`. MNT = ISO 496, minor unit 2.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. If a period carries more
  than 2 decimal places of significance, **REFUSE it — never vector a residue value.**
  Record the observation and move on.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- Balances **derived, never written** (I-3); append-only (I-4).
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census stays **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `loan`.** Do NOT touch `loanschedule` — it grades the generator at
  a different seam and is not yours.
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**. Never
  synthesise a value you did not observe. Cite `file:line` from the FILE.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations for ONE property. **Commit by iteration 120** — the last three runs on this
shape committed at ~109, ~120 and ~92. If you are reading past 150 with nothing on disk,
you have mis-scoped it: commit what you have and say so.
