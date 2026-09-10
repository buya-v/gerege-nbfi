# OH-WCDISC-O — make `total_discount_fee` non-zero, and start the clamp chain

Worktree: `/Users/buv/oh-gerege-wcdisc` (branch `feat/OHWCDISCo`)
Work ONLY in that directory. **You hold the oracle.** No other run is using it.

## THE PREVIOUS RUN LEFT YOU A MAP. USE IT.

`OH-WC-S` closed the *refusal* half of this problem: `workingcapital/balance.go` now
returns `ErrNoGradedCapture` for every stored balance term the pinned captures cannot
discriminate, naming the term. It then did something better than its brief asked and wrote
a table in `.softhouse/findings/F-2026-09-10-workingcapital-ungraded-terms.md` giving, for
each term, **the oracle write path (`file:line`) that sets it** and **exactly what capture
would grade it**. **Read that table first.** It is the map; do not rebuild it.

Two of its entries matter here:

| term | oracle write path | capture that would grade it |
|---|---|---|
| `total_discount_fee` | `WorkingCapitalLoanBalance.java:117` (set from the product `discount` inside `applyDisbursement`, `:115-121`); `WorkingCapitalLoanWritePlatformServiceImpl.java:1074` | **a product whose `discount` is non-zero, disbursed, then read-back** |
| `total_discount_fee_adjustment` | `WorkingCapitalLoanWritePlatformServiceImpl.java:1056` | a discount change on a discounted, disbursed facility |

And one entry you must NOT chase, because that run already proved it impossible:

> `total_disbursement` — **no caller of `setTotalDisbursement` anywhere under `src/main`**.
> The column is structurally zero in the reference, so **no capture can grade it.** That is
> a permanent, documented gap. Leave it alone.

## The task — ONE thing

**Create a working-capital product whose `discount` is NON-ZERO, disburse a facility on it,
and capture the balance read-back** so `total_discount_fee` is finally non-zero.

That is the first link in a chain nothing has ever exercised:
`UnrealizedIncomeFromDiscountFee` = `max(totalDiscountFee − totalDiscountFeeAdjustment −
realizedIncomeFromDiscountFee, 0)` [`workingcapital/balance.go:87-92`]. **The `max(…, 0)`
clamp has never had a non-zero operand.** You are not required to drive the clamp negative
in this run — that needs an adjustment or realized income on top — but **say how close you
got and what remains**, so the next run inherits a map as good as the one you were given.

**Choose a NON-ROUND discount.** A round one hides truncation exactly as `100000.00` did in
the loan schedule and `100.00` did in shares. **Work the arithmetic out BEFORE creating
anything**: the resulting money cells must land on whole minor units, because **G-19 REFUSES
sub-minor residue** and a careless choice creates oracle state that cannot be vectored at
all. State your numbers and the arithmetic.

## The path
1. Verify the oracle state and the existing `workingcapital` captures.
2. **`pg_dump -Fc` snapshot** to `/Users/buv/gerege-oracle-snapshots/`. **Never commit a
   `.dump`.**
3. Create the product, a client if needed, and the facility; approve and disburse.
4. Capture every `(request, response)` pair and the balance read-back. **COMMIT THE CAPTURE
   IMMEDIATELY, before grading** — it is a state change; `OH-SHARES-K` was killed mid-run
   and lost nothing because its capture was already in.
5. Promote the vector, and **relax the `ErrNoGradedCapture` refusal for `TotalDiscountFee`
   only** — that term is now graded, the rest are not. **Do not remove refusals you have not
   earned**; each one still standing is a true statement about the corpus.
6. Register a drive and measure it against the store **without** your vector and **with** it.

**If the oracle refuses, the refusal IS the result** — capture status, error body, source
line; record it; stop. **Do not SQL-insert anything.**

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. Report every kill count and prove the instrument was live.
**Do not manufacture coverage.**

## Measuring it
    kills.sh workingcapital <impl>                              (existing: 4 drives)
    kills.sh provisioning provisioning-wrong-sum-then-round     -> 1
    kills.sh collateral   collateral-wrong-pct-hardcoded        -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** **FLAGS ARE PER-BINARY** — `-root` is required by
most and rejected by loanschedule's; `-oracle-probe` exists on some only. Use `kills.sh`.

After your change `workingcapital-go` must still pass **all** its vectors and the four
existing drives must still kill. That is your primary control.

## Rules of evidence
- **Request bodies must be BYTE-STABLE** under a binary-double round trip. A salvage was
  **reverted** this week over `100.00 -> 100.0`. **Check your own `req/` before committing.**
- **Beware unterminated quotes** — one hung a run to death; `C-c` does not rescue it.
- **SQL is READ-ONLY.** Never write the `default` tenant.
- Capture directory named for its **SUBJECT** with an `OWNER.md`.
- `capture_ref`, `capture_sha256`, `citation`; **re-verify after writing**. Never synthesise
  a value you did not observe. Cite `file:line` from the FILE.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Never describe member savings as insured, protected or guaranteed.**
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `workingcapital`.**

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations. **Commit the capture by iteration 120 at the latest.**
