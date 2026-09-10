# OH-DIR-D — ONE property: WHICH account takes WHICH side. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-dird` (branch `feat/OHDIRd`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.** Everything is
promotable from captures already committed on `main`.

## This is a direct follow-on to OH-JE-C. The seam already exists.

`OH-JE-C` built the `loan-journal-entry-batch-balance` seam and `LN-L09`. **Read both
before anything else** — you are extending, not inventing:

* `nexus/internal/apps/loan/journalbatch.go` — `JournalEntrySide` (`Unknown`=0 refused,
  `JournalEntryDebit`, `JournalEntryCredit`), `JournalEntryLeg`
  (`transaction_id`, `account`, `side`, `amount minor`), `SumJournalEntryBatch`.
* `.softhouse/vectors/loan/LN-L09-journal-entry-batch-balance.json` — **its `request`
  already carries `account` and `entry_type` on every leg.** Your property is expressible
  on the existing shape; **no new capture and no new request schema is needed.**
* Registration: `nexus/internal/apps/loan/conformance/impl.go`, thirteen worked
  `loan-wrong-*` examples.

## THE PROPERTY — and why the existing four drives cannot catch it

The observed batch (loan 10, `journalentries-all-raw.json`, the capture `LN-L09` cites —
**note: NOT `journalentries-loan-10-raw.json`, which is not on main**; see
`F-2026-09-10-journalentries-loan-10-capture-location.md`):

    L17  OHLGR-Loan-Portfolio     DEBIT   10000000     (disbursement pair)
    L17  OHLGR-Fund-Source        CREDIT  10000000
    L18  OHLGR-Income-From-Fees   CREDIT     10000     (fee pair)
    L18  OHLGR-Fund-Source        DEBIT      10000

> **Each ACCOUNT takes a SPECIFIC SIDE. A port that swaps the two legs of the
> disbursement pair — crediting the portfolio and debiting the fund source — STILL
> BALANCES.**

Check this yourself before building on it: swapping both legs of a pair leaves
`sum(debits) == sum(credits)` untouched, so it passes `LN-L09` and every one of:

    loan-wrong-journal-entry-batch-first-pair-only   (sums only L17)
    loan-wrong-journal-entry-batch-drops-fee-pair    (omits L18)
    loan-wrong-journal-entry-batch-nets-account      (nets the two Fund-Source legs)

None of them looks at **which account got which side**. That is the hole.

Note also that `OHLGR-Fund-Source` appears on **both** sides across the two transactions —
CREDIT in L17, DEBIT in L18 — so the property is per-(transaction, account), not
per-account globally. A drive that assumes an account has one fixed side would be wrong
about the oracle, not just about the port.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument**. Report every kill count. **Prove
the instrument was live** — the controls below, plus an existing `loan` drive that still
kills.

**Do not manufacture coverage.** If a defect shape is not discriminated by this capture,
say so and record what a capture would need. `OH-INV-Z` did exactly that for
`totalOverpaid`; it was the right call and it is the standard.

**And do not re-register a defect already covered.** Read the three defect strings above
first. "Already covered" is a finding, not a failure.

## Measuring it
`kills.sh loan <impl>` works for this context. Controls:

    kills.sh loan         loan-wrong-journal-entry-batch-nets-account  -> 1
    kills.sh loan         loan-wrong-summary-drops-penalty             -> 2
    kills.sh loanschedule loanschedule-wrong-days-in-year-365          -> 45
    kills.sh parties      parties-wrong-iota-ordinals                  -> 12
    kills.sh charges      charges-wrong-rounding-half-even             -> 1

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED, not a zero-kill drive.** If a control is wrong, the
instrument is wrong — not the tree.

After your change, `loan-go` must still pass **every** loan vector, and **all** existing
loan drives must still kill. That is your primary control.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  MNT = ISO 496, minor unit 2.
- **Double-entry, append-only. Balances DERIVED, never written** (I-3/I-4).
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (exactly 12 pairs) or
  `.softhouse/conformance.sh` (you add no ledger drive; its census pin stays **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `loan`.**
- Every vector carries `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash
  after writing**. Never synthesise a value you did not observe.
- **Cite `file:line`** from the FILE, not a comment-stripped view.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **exactly 12 pairs**, census **17**. Run it EARLY.

~500 iterations for ONE property. **Commit by iteration 120.** `OH-JE-C` did this same
shape of task and committed at ~109. If you are still reading past 150 with nothing on
disk, you have mis-scoped it — commit what you have and say so.
