# OH-WCCAP-P — CAPTURE ONLY. Create a discounted facility and commit the observation.

Worktree: `/Users/buv/oh-gerege-wccap` (branch `feat/OHWCCAPp`)
Work ONLY in that directory. **You hold the oracle.**

## YOUR ENTIRE DELIVERABLE IS A COMMITTED CAPTURE

**Do NOT write a vector. Do NOT register a drive. Do NOT touch any `.go` file. Do NOT
relax any `ErrNoGradedCapture` refusal.** A later run grades what you capture.

This is deliberate and it is why the previous attempt was killed. `OH-WCDISC-O` was given
this same objective *plus* the grading, had a complete map, and spent **251 iterations
creating nothing** — see `.softhouse/findings/F-2026-09-10-split-capture-from-grading.md`.
An oracle write is a DESIGN problem; grading is transcription. One budget doing both never
starts writing. **You only have the design half. Finish it and commit.**

## THE OBJECTIVE

**Create a working-capital product whose `discount` is NON-ZERO, disburse a facility on it,
and capture the balance read-back so `total_discount_fee` is non-zero.**

`OH-WC-S` established exactly where that lands
[`.softhouse/findings/F-2026-09-10-workingcapital-ungraded-terms.md`]:

    total_discount_fee  <- set from the product `discount` inside applyDisbursement
                           [WorkingCapitalLoanBalance.java:117, :115-121]
                           and WorkingCapitalLoanWritePlatformServiceImpl.java:1074

It is the first operand of a chain nothing has ever exercised:
`UnrealizedIncomeFromDiscountFee = max(totalDiscountFee − adjustment − realized, 0)`.
**That clamp has never had a non-zero operand.**

**Do NOT chase `total_disbursement`** — `OH-WC-S` proved there is **no caller** of
`setTotalDisbursement` anywhere under `src/main`; it is structurally zero and no capture
can grade it. A permanent documented gap; leave it.

## The path — and START AT STEP 3 EARLY

1. Probe the oracle. `.softhouse/capture/workingcapital/` shows how the seeded facility was
   built; **skim its `req/` bodies for the endpoint shapes and move on.** Do not read
   Fineract Java to rediscover an endpoint — that is what consumed the last run.
2. **`pg_dump -Fc` snapshot** to `/Users/buv/gerege-oracle-snapshots/`. **Never commit a
   `.dump`.**
3. **Create the product with a non-zero discount.** Then client (if needed), facility,
   approve, disburse.
4. **Capture every `(request, response)` pair and the balance read-back.**
5. **COMMIT.** Subject-named capture directory with an `OWNER.md`. **Commit as soon as the
   product exists, then again after the disbursement read-back** — do not wait for the
   whole sequence.

**If any step refuses, THE REFUSAL IS THE RESULT.** Capture the status, the error body and
the source line that raised it, commit that, and stop. A documented refusal is a
first-class outcome here — `OH-INV-Q` and `OH-INV-W2` both delivered exactly that and both
merged. **Do not SQL-insert anything.**

## THE ARITHMETIC COMES FIRST

Choose a **NON-ROUND discount** — a round one hides truncation the way `100000.00` did in
the loan schedule and `100.00` did in shares. **But work it out BEFORE you create
anything:** the resulting money cells must land on **whole minor units**, because **G-19
REFUSES sub-minor residue** and a careless choice creates oracle state that **cannot be
vectored at all**, wasting the write. `OH-COLL-L` did this correctly: `41850.08` at `37.5%`
→ `10462520` and `3923445`, both whole.

**State your chosen numbers and the arithmetic in the commit message**, so the grading run
inherits them.

## What the grading run will need from you
Write an `OWNER.md` that says: what you created (ids, names, values), the arithmetic, which
read-backs are in `out/`, and — if you got that far — **how close the clamp came to a
non-zero operand and what remains** (an adjustment or realized income on top). Leave as good
a map as `OH-WC-S` left you.

## Rules of evidence
- **Request bodies must be BYTE-STABLE** under a binary-double round trip — integer tokens
  or strings, never `json.dumps` of a parsed number. A salvage was **reverted** this week
  over `100.00 -> 100.0`. **Check your own `req/` before committing.**
- **Beware unterminated quotes** — one hung a run to death; `C-c` does not rescue it.
  Prefer the REST API over `docker exec psql`.
- **SQL is READ-ONLY.** Never write the `default` tenant.
- Never synthesise a value you did not observe. Cite `file:line` from the FILE.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; MNT = ISO 496, minor unit 2.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Never describe member savings as insured, protected or guaranteed.**
- **Do not touch** `.softhouse/guards/ledger-invariants.baseline`, `.softhouse/conformance.sh`,
  or **any `.go` file**.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**

## The bar and the budget
You change no Go code, so the bar should be untouched: run `bash .softhouse/conformance.sh`
**once at the end** to confirm exit 2 as the §4.4.2 recorded decision, ledger findings
**12 pairs**, census **17**.

~500 iterations for a capture. **If the product does not exist in the oracle by iteration
100, stop and commit whatever you have with a note saying what blocked you.**
