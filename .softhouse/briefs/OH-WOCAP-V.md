# OH-WOCAP-V — CAPTURE ONLY. Write off a loan and read it back.

Worktree: `/Users/buv/oh-gerege-wocap` (branch `feat/OHWOCAPv`)
Work ONLY in that directory. **You hold the oracle.** A parallel run (`OH-DELINQ-U`) is
promoting from COMMITTED captures only and will not touch the oracle.

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout
— do not read or write there, and **never exercise the push gate**. The driver pushes.

## YOUR ENTIRE DELIVERABLE IS A COMMITTED CAPTURE
**Do NOT write a vector. Do NOT register a drive. Do NOT touch any `.go` file.** A later run
grades what you capture. An oracle write is a DESIGN problem and grading is transcription;
a run asked for both was killed at 251 iterations having produced nothing, while the same
objective split in two finished in ~64 + ~150
(`.softhouse/findings/F-2026-09-10-split-capture-from-grading.md`).

## WHY
`OH-LOANCOV-T`'s triage (`.softhouse/findings/F-2026-09-11-loan-graded-coverage.md` §4.1):

> `writeoff.go:36` `WriteOffOutstanding` — **observation ABSENT.** A write-off discharges
> the whole outstanding principal/interest/fee/penalty and returns it so the caller can
> post the reversing entry. No loan in the corpus is ever written off; a full-text scan for
> a non-zero `writtenOff` in any capture finds nothing. **This is the holds case with a
> different rule.**

## THE OBJECTIVE
**Write off an active loan that has a non-zero outstanding balance, and capture the loan
detail and its transactions before and after.**

* **Choose a loan with fee AND penalty outstanding, not just principal** — so the write-off
  discharges all four buckets and a port that writes off only principal is catchable.
  **Loan 11** (product 3) carried principal 100000.00, interest 6618.53, fee 100.00, penalty
  57.00 when last read — **verify its current state first**; do NOT use loan 12 (its state
  is pinned by `LN-L11`/`LN-L12`, and changing it would move the oracle under committed
  vectors' feet — those vectors cite files, not live state, but keep the oracle legible).
* If product 3 loans post journal entries on write-off, **capture those too** — the reversing
  entry is half of what `WriteOffOutstanding` returns the caller for.

## The path
1. Probe the oracle; confirm the candidate loan and its four outstanding buckets. **Skim
   existing `req/` bodies under `.softhouse/capture/` for endpoint shapes and move on** — do
   NOT read Fineract Java to rediscover an endpoint; that consumed a whole run this week.
2. **`pg_dump -Fc` snapshot** to `/Users/buv/gerege-oracle-snapshots/`. **Never commit a
   `.dump`.**
3. Capture before-state (detail + transactions + journal entries if accounting is on).
4. Write off. Capture after-state.
5. **COMMIT AS YOU GO** — before-state as soon as you have it, then the write-off.

**If the oracle refuses, THE REFUSAL IS THE RESULT** — capture status, error body, source
line; commit; stop. `OH-INV-Q` and `OH-INV-W2` both delivered exactly that and both merged.
**Do not SQL-insert anything.**

## What the grading run needs
An `OWNER.md` with: the loan, the four buckets before, what the write-off transaction
carried, the four buckets after, and any journal entries — so the next run can pin them
without re-deriving. Leave a map as good as `OH-WC-S` left.

## Rules of evidence
- **Request bodies must be BYTE-STABLE** under a binary-double round trip. A salvage was
  **reverted** this week over `100.00 -> 100.0`. **Check your own `req/` before committing.**
- **Beware unterminated quotes** — one hung a run to death; `C-c` does not rescue it.
- **SQL is READ-ONLY.** Never write the `default` tenant.
- Capture directory named for its **SUBJECT** with an `OWNER.md`.

## Non-negotiables
- Money is **integer minor units**; MNT = ISO 496, minor unit 2.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not touch** `.softhouse/guards/ledger-invariants.baseline`, `.softhouse/conformance.sh`,
  or **any `.go` file**.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**

## The bar and the budget
No Go change, so the bar should be untouched: run `bash .softhouse/conformance.sh` **once at
the end** — exit 2 (§4.4.2), ledger findings **12 pairs**, census **17**.

~500 iterations. **If the write-off is not done by iteration 100, stop and commit what you
have with a note on what blocked you.**
