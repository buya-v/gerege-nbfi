# OH-REPAYJE-H — the repayment's FIVE-LEG posting mirrors the allocation. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-repayjeh` (branch `feat/OHREPAYJEh`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.** Everything is
promotable from captures already committed on `main`.

## THE OBSERVATION — the richest in the corpus, and nothing grades it

`OH-ALLOC-G` posted a repayment on loan 12 and captured the journal entries after it.
Transaction **L53** in
`.softhouse/capture/loan12-four-bucket-allocation/out/journalentries-loan-12-after-raw.json`:

    L53  OHLGR-Loan-Portfolio        CREDIT  91203.12     <- principal bucket
    L53  OHLGR-Interest-Receivable   CREDIT   6618.53     <- interest bucket
    L53  OHLGR-Fees-Receivable       CREDIT    100.00     <- fee bucket
    L53  OHLGR-Penalties-Receivable  CREDIT     57.00     <- penalty bucket
    L53  OHLGR-Fund-Source           DEBIT   97978.65     <- cash received

> **A repayment posts FIVE legs: one CREDIT per allocation bucket, each to a DIFFERENT
> account, and ONE DEBIT equal to their sum.**

**Verify all five against the file before building on it.**

Three things make this worth a vector, and each is a defect a simpler check misses:

1. **FIVE legs, an ODD count.** Every posting graded so far has been pairs. Logic that
   assumes leg-pairs — walks two at a time, or matches each debit to one credit — breaks
   here and nowhere else in the corpus.
2. **One credit per bucket, to a DISTINCT account.** A port that collapses the four credits
   into a single `Loan-Portfolio` credit of 97978.65 **still balances**, still has the
   right total, and is wrong. `LN-L09`'s totals and `LN-L10`'s sides cannot see it.
3. **IT MIRRORS `LN-L11`.** The four credits are exactly the allocation buckets that vector
   pins: `9120312 / 661853 / 10000 / 5700`, summing to `9797865` — the debit. This is the
   first property that ties the ALLOCATION seam to the GL POSTING seam, so a port that
   allocates correctly and posts wrongly (or vice versa) is caught.

## THE MAP

* **Existing seam to extend** — `loan-journal-entry-batch-balance`, built by `OH-JE-C`,
  extended by `OH-DIR-D` (per-(transaction, account) sides) and `OH-MAP-E` (account
  mapping). Vector: `.softhouse/vectors/loan/LN-L09-journal-entry-batch-balance.json`.
  Its `request.journal_entries` already carries `transaction_id`, `account`, `entry_type`,
  `amount_minor` per leg — **the shape already fits five legs; no new schema is needed.**
  Check whether `LN-L09`'s admission rule (it refuses a batch with fewer than two distinct
  transaction ids) admits a single-transaction five-leg batch. **If it does not, say so and
  decide** — a new vector alongside LN-L09 is fine; weakening LN-L09's admission is NOT.
* **The port** — `nexus/internal/apps/loan/journalbatch.go` (`SumJournalEntryBatch`,
  `JournalEntryLeg`, `JournalEntrySide`).
* **Registration** — `nexus/internal/apps/loan/conformance/impl.go`, **twenty** worked
  `loan-wrong-*` examples.
* **Allocation cross-reference** —
  `.softhouse/vectors/loan/LN-L11-repayment-allocation-fee-and-penalty.json`.

## Drives worth registering — only what the capture DISCRIMINATES

* collapses the four credits into one account (balances, wrong accounts);
* pairs legs two-at-a-time and drops the fifth (odd-count defect);
* posts the debit as the sum of only the first two credits.

**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. Report every kill count. **Prove the instrument was live**
(controls below plus an existing `loan` drive that kills). **Do not manufacture coverage** —
four runs in a row have declined a shape they could not see and recorded what a capture
would need; that is the standard, not an excuse.

**Do not re-register a covered defect.** Read the defect strings of the four
`loan-wrong-journal-entry-batch-*` drives first. "Already covered" is a finding.

## Measuring it
    kills.sh loan loan-wrong-allocation-drops-penalty            -> 1
    kills.sh loan loan-wrong-summary-drops-penalty               -> 2
    kills.sh loanschedule loanschedule-wrong-days-in-year-365    -> 45
    kills.sh parties      parties-wrong-iota-ordinals            -> 12
    kills.sh charges      charges-wrong-rounding-half-even       -> 1

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** If a control is wrong, the instrument is wrong.

After your change `loan-go` must still pass **all 17** loan vectors and **all 20** existing
drives must still kill. That is your primary control.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  `97978.65` transcribes to `9797865`. MNT = ISO 496, minor unit 2.
- **Double-entry, append-only. Balances DERIVED, never written** (I-3/I-4).
- **The splits sum to the whole** — here the four credits sum to the one debit.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `loan`.**
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**. Never
  synthesise a value you did not observe. Cite `file:line` from the FILE.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations for ONE property. **Commit by iteration 120** — the last five runs on this
shape committed at ~109, ~120, ~92, ~190 and ~115.
