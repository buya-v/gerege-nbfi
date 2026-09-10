# OH-MAP-E — ONE property: the fee pair posts to a DIFFERENT account pair. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-mape` (branch `feat/OHMAPe`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

## Third and last property these captures can grade. The seam exists.

`OH-JE-C` built `loan-journal-entry-batch-balance` + `LN-L09`; `OH-DIR-D` added the
per-(transaction, account) **side** expectation. **Read both before anything else** —
you are extending, not inventing:

* `nexus/internal/apps/loan/journalbatch.go` — `JournalEntrySide`
  (`Unknown`=0 refused, `Debit`, `Credit`), `JournalEntryLeg`
  (`transaction_id`, `account`, `side`, `amount minor`), `SumJournalEntryBatch`.
* `.softhouse/vectors/loan/LN-L09-journal-entry-batch-balance.json` — **its `request`
  already carries `account`, `entry_type` and `amount_minor` per leg**, and its `expect`
  already carries the debit/credit totals and the side list. **No new capture, no new
  schema.**
* Registration: `nexus/internal/apps/loan/conformance/impl.go`, **fourteen** worked
  `loan-wrong-*` examples.

## THE PROPERTY

The observed batch (from `journalentries-all-raw.json` — **not**
`journalentries-loan-10-raw.json`, which is not on main):

    L17  OHLGR-Loan-Portfolio     DEBIT   10000000     disbursement pair
    L17  OHLGR-Fund-Source        CREDIT  10000000
    L18  OHLGR-Income-From-Fees   CREDIT     10000     fee pair
    L18  OHLGR-Fund-Source        DEBIT      10000

> **The fee pair posts to a DIFFERENT ACCOUNT PAIR than the disbursement pair.**
> Principal moves through `Loan-Portfolio`/`Fund-Source`; the fee moves through
> `Income-From-Fees`/`Fund-Source`. A port that routes **every** posting through the
> disbursement's account mapping still balances, still gets every side right, and still
> has the correct totals.

**Verify for yourself that the four existing drives cannot catch it** before building:

    loan-wrong-journal-entry-batch-first-pair-only     (sums only L17)
    loan-wrong-journal-entry-batch-drops-fee-pair      (omits L18 entirely)
    loan-wrong-journal-entry-batch-nets-account        (nets the two Fund-Source legs)
    loan-wrong-journal-entry-batch-swaps-first-pair-sides  (reverses L17's sides)

A mapping defect keeps all four legs, all four sides and both totals — it changes only
**which GL account** a leg names. That is the hole.

This is the accounting defect with the most real-world weight of the three: a fee posted
to the loan portfolio instead of income overstates the asset and understates revenue, and
**every total still balances.**

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument**. Report every kill count. **Prove
the instrument was live** — the controls below, plus an existing `loan` drive that kills.

**Do not manufacture coverage.** If a shape is not discriminated by this capture, say so
and record what a capture would need. **Do not re-register a covered defect** — read the
four defect strings first; "already covered" is a finding, not a failure.

## Measuring it
    kills.sh loan loan-wrong-journal-entry-batch-swaps-first-pair-sides -> 1
    kills.sh loan loan-wrong-summary-drops-penalty                      -> 2
    kills.sh loanschedule loanschedule-wrong-days-in-year-365           -> 45
    kills.sh parties      parties-wrong-iota-ordinals                   -> 12
    kills.sh charges      charges-wrong-rounding-half-even              -> 1

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** If a control is wrong, the instrument is wrong.

After your change `loan-go` must still pass **all 15** loan vectors and **all 14** existing
drives must still kill. That is your primary control.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Double-entry, append-only. Balances DERIVED, never written** (I-3/I-4).
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census pin stays **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `loan`.**
- `capture_ref`, `capture_sha256`, `citation` on the vector; **re-verify the hash after
  writing**. Never synthesise a value you did not observe. Cite `file:line` from the FILE.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations for ONE property. **Commit by iteration 120** — `OH-JE-C` committed at
~109 and `OH-DIR-D` at ~120 on this exact shape of task. If you are still reading past 150
with nothing on disk, you have mis-scoped it: commit what you have and say so.
