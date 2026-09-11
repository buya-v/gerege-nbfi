# OH-REVERSAL-X — the first reversing entry: port it, grade it. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-reversal` (branch `feat/OHREVERSALx`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout
— do not read or write there, and **never exercise the push gate**. The driver pushes.

## Why this run exists

`CLAUDE.md` makes it a non-negotiable: **"Corrections are reversing entries."** No port in this
store reverses anything, and no vector grades a reversal. The ledger's own capability row says
why: `ledger.reversal.entry` (`.softhouse/vectors/capabilities-ledger.json`) is out of the graded
domain because "distinguishing 'flags and adds' from 'flags and rewrites' needs the WRITE path,
not a snapshot."

**The write-off capture has the write path.** It read the loan's journal entries BEFORE and
AFTER the write-off, and the write-off reversed the loan's last accrual as a side effect.

## THE OBSERVATION — verify every figure against the files

`.softhouse/capture/loan11-writeoff-four-bucket/` — read `OWNER.md` §"Side effect observed".
Files: `out/loan-11-before-journalentries-raw.json` (24 entries), `out/loan-11-after-journalentries-raw.json` (31).

    accrual txn 46 (2026-09-02, interest 11.56) — before the write-off:
      JE 84  L46  OHLGR-10012 Interest-Receivable  DEBIT   11.56  reversed=false
      JE 86  L46  OHLGR-40010 Interest-On-Loans    CREDIT  11.56  reversed=false
    after the write-off, ADDED:
      JE 134 L46  OHLGR-10012 Interest-Receivable  CREDIT  11.56  reversed=false  transactionDate 2026-09-02
      JE 135 L46  OHLGR-40010 Interest-On-Loans    DEBIT   11.56  reversed=false  transactionDate 2026-09-02
    and JE 84 and 86 are UNCHANGED — every one of the 24 before-entries is byte-identical
    in the after read-back (the driver checked; you check again).

## THE RULE — port it, it is twenty lines

`JournalEntryWritePlatformServiceJpaRepositoryImpl.createJournalEntryForReversedLoanTransaction`
[pinned source `/Users/buv/fineract`, commit `426a23544`,
`fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/JournalEntryWritePlatformServiceJpaRepositoryImpl.java:359-378`],
reached from `AccrualBasedAccountingProcessorForLoan.createJournalEntriesForLoan` when
`loanTransactionDTO.isReversed()` [`AccrualBasedAccountingProcessorForLoan.java:68-72`].
**Read it yourself.** For every existing journal entry of transaction `"L" + id` it creates ONE
new entry: same office, same GL account, same currency, **same transaction id**, manual entry
**false**, the reversed transaction's **transaction date**, the **OPPOSITE side**, the **same
amount**. It does not modify, flag or delete any original.

Port it into `nexus/internal/apps/loan/` as a pure function over the leg type the loan JE seams
already use (`JournalEntryLeg`, `journalbatch.go`) — integer minor units, no float. Cite
`file:line` from the FILE in the doc comment.

## The task — ONE property

> **A loan-transaction reversal ADDS one counter-leg per original leg — same account, same
> amount, same transaction id, same transaction date, OPPOSITE side — and changes no original.**

Promote ONE vector: request = the before-legs of `L46` and the reversed transaction's date;
expect = the full after-leg list for `L46` (originals as they were, then the two counter-legs).
Every leg's side, account, amount and transaction id is graded.

Drives worth registering — each is a port a reasonable reader might write, and the observation
discriminates every one:
* **duplicates instead of reverses** — same side. Totals still balance (2312 = 2312), so
  `SumJournalEntryBatch` cannot see it; the side cells do.
* **flags and rewrites** — marks the originals reversed (the MANUAL-reversal semantics, below).
  Only works as a drive if your vector grades each original's `reversed` flag — so grade it.
* **posts on a fresh transaction id** — also the manual semantics.
* **dates the counter-legs at the business date 2026-09-03** instead of the transaction date
  2026-09-02.

**Measure each drive against the store WITHOUT your vector and WITH it.** Report every count.

## Know the OTHER reversal — do NOT port it here

The manual path, `revertJournalEntry` [`:380-429`], is DIFFERENT: it posts counter-entries on a
FRESH transaction id AND flags each original `reversed = true` (`:423`). Observed and committed:
`.softhouse/capture/tierA-a2/out/A2-350-je-office1-june.json` (originals 45/46/47 flagged,
counter-entries 50/51/52 not). **That is the ledger context's, not yours.** The two drives above
that borrow its semantics are exactly why the loan path needs a vector: a porter who has read
the manual path first will write the wrong loan reversal.

Also recorded, NOT yours: `.softhouse/findings/F-2026-09-11-trialbalance-excludes-reversed.md`.
Do not touch `nexus/internal/apps/ledger/`.

## Coverage — the proof the grading reaches the rule

    go test -count=1 -coverpkg=./internal/apps/loan -coverprofile=/tmp/c.cov ./internal/apps/loan/conformance/...
    go tool cover -func=/tmp/c.cov | grep -i revers

`-count=1` is required (the test cache can return a stale profile). Your new function must read
well above 0% from the committed-store test. If it does not, the vector does not reach it — say so.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or **delete
it with the argument**. **Do not manufacture coverage.**

## Measuring it
    kills.sh loan loan-wrong-writeoff-drops-fee               -> 1
    kills.sh loan loan-wrong-delinquency-thirty-day-month     -> 3
    kills.sh loan loan-wrong-summary-drops-penalty            -> 2
    kills.sh loanschedule loanschedule-wrong-days-in-year-365 -> 45

**An empty result means the MEASUREMENT FAILED** (exit 2, reason on stderr). **FLAGS ARE
PER-BINARY.** Use `kills.sh <context> <impl> <worktree>`.

After your change `loan-go` must pass **all 25** loan vectors plus yours, **all 31** loan drives
must still kill, and the loan committed-store test must pass.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Append-only**: the port must never mutate an input leg. Test it.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle Database
  is prohibited.**
- **One bounded context: `loan`.**
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**. Never
  synthesise a value you did not observe.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations. **Commit by iteration 120** — a finished commit you amend beats perfect work lost.
