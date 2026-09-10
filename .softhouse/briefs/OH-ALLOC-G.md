# OH-ALLOC-G — the four-bucket allocation, with all FOUR buckets non-zero

Worktree: `/Users/buv/oh-gerege-allocg` (branch `feat/OHALLOCg`)
Work ONLY in that directory. **You hold the oracle.** No other run is using it.

## THE GAP, measured by the driver before dispatch

A repayment allocates across **four** buckets — penalty, fee, interest, principal. The only
vector that grades allocation is `.softhouse/vectors/loan/LN-L03-repayment-allocation.json`,
and **it has `fee = "0"` and `penalty = "0"`**:

    request.repayment.outstanding = {penalty 0, fee 0, interest 100000, principal 788488}
    expect.allocation             = {penalty 0, fee 0, interest 100000, principal 788488}

**So the four-bucket allocation is graded on two buckets.** A port that drops the fee
bucket, or the penalty bucket, or both, passes `LN-L03` — adding zero is indistinguishable
from not adding. This is the *same class* of blindness as
`.softhouse/findings/F-2026-09-09-fee-penalty-blind.md`, which was about the summary SUM;
this one is about the ALLOCATION. **Read that finding first** — it names why the two
non-zero values must also DIFFER from each other (equal values let a bucket-swap survive).

## THE MAP — verified live by the driver; re-verify before relying on it

**Loan 12** (product 3, `OHLGT-L03`, ACCRUAL PERIODIC) currently carries **all four buckets
non-zero and outstanding**:

    principalOutstanding      100000.0
    interestOutstanding         6618.53
    feeChargesOutstanding        100.0
    penaltyChargesOutstanding     57.0
    totalOutstanding          106775.53

Fee (100.00) and penalty (57.00) are non-zero **and different** — exactly what the property
needs. Its accrual rows already show them (`fee=100.0` on one accrual, `pen=57.0` on
another), so the charges are real, not projected.

**The port** — `nexus/internal/apps/loan/allocation.go`: `Allocation{Principal, Interest,
Fee, Penalty}`, `Total()` sums all four (`:25-27`), `For(AllocationType)` selects a bucket
(`:30+`). `allocationtype.go` holds the ordering type.

**Registration** — `nexus/internal/apps/loan/conformance/impl.go`, **eighteen** worked
`loan-wrong-*` examples.

**Vector shape** — copy `LN-L03-repayment-allocation.json`; the seam and request/expect
shape already exist. You are adding an observation with the other two buckets non-zero, not
a new schema.

## The path

1. Verify loan 12's four outstanding buckets above. If they have moved, use what you
   observe and say so.
2. **`pg_dump -Fc` snapshot** to `/Users/buv/gerege-oracle-snapshots/` before any write.
   **Never commit a `.dump`.**
3. **Post a repayment against loan 12** sized so the allocation is INTERESTING — large
   enough to consume penalty and fee and bite into interest or principal, so more than one
   bucket is non-zero in the RESULT. A repayment that only clears the penalty grades much
   less. State the amount you chose and why.
4. Capture the `(request, response)` pair and the transaction read-back showing the
   per-bucket portions.
5. Promote the vector and register the drives.

**If the oracle refuses, the refusal IS the result** — capture the status, the error body
and the source line, record it, and stop there. Do not SQL-insert anything.

## The drives worth registering
`loan-wrong-allocation-drops-fee` and `loan-wrong-allocation-drops-penalty` are the obvious
pair, and with fee ≠ penalty both are discriminated. **Register only what your capture
actually kills**, and report every kill count.

**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. **Prove the instrument was live** (controls below plus an
existing `loan` drive that kills). **Do not manufacture coverage**: three runs in a row have
declined a shape they could not see and recorded what a capture would need. That is the
standard.

## Measuring it
    kills.sh loan loan-wrong-schedule-amortization-uniform-truncated -> 1
    kills.sh loan loan-wrong-summary-drops-penalty                   -> 2
    kills.sh loanschedule loanschedule-wrong-days-in-year-365        -> 45
    kills.sh parties      parties-wrong-iota-ordinals                -> 12
    kills.sh charges      charges-wrong-rounding-half-even           -> 1

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** If a control is wrong, the instrument is wrong.

After your change `loan-go` must still pass **all 16** loan vectors and **all 18** existing
drives must still kill. That is your primary control.

## Rules of evidence
- **Request bodies must be BYTE-STABLE** under a binary-double round trip — integer tokens,
  never `json.dumps` of a parsed number. A salvage was **reverted** this week over
  `100.00 -> 100.0`. **Check your own `req/` before committing.**
- **Beware unterminated quotes** — a `psql -tAc "SELECT …` with no closing quote **hung a
  run to death** this week and `C-c` does not rescue it. Prefer the REST API.
- **SQL is READ-ONLY.** Never write the `default` tenant. All writes via the API.
- Capture directory named for its **SUBJECT** with an `OWNER.md`; names freeze at first
  commit.
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**. Never
  synthesise a value you did not observe. Cite `file:line` from the FILE.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  MNT = ISO 496, minor unit 2.
- **THE SPLITS MUST SUM TO THE WHOLE** — this is a named CLAUDE.md invariant and it is the
  heart of this task: `penalty + fee + interest + principal (+ leftover) == amount paid`.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `loan`.**

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations. **Commit by iteration 120** — the last four runs committed at ~109, ~120,
~92 and ~190. **Commit the CAPTURE as soon as you have it**, before grading: a committed
capture survives a cap-death, an uncommitted one has twice needed a hand salvage this week.
