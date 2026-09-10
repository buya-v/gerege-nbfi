# OH-JE-C — ONE property: the multi-pair batch balance, in `loan`. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-jec` (branch `feat/OHJEc`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.** Everything is
promotable from captures already committed on `main`.

## THREE RUNS HAVE FAILED AT THIS. THE TASK HAS BEEN CHANGED, NOT JUST RE-ISSUED.

`OH-LEDGER-V`, `OH-GLVEC-AB` and `OH-GLVEC-B` were asked to grade the loan→GL postings as
**`ledger`** vectors. They produced nothing between them. The cause was not navigation and
not the agents — read
`.softhouse/findings/F-2026-09-10-vector-schema-mismatch.md`:

> A `ledger` vector's `request` models a REST **posting command** — `manual_entry`,
> `transaction_amount_major_text`, `slot_family`, `slot_code`, `legs` the caller SUBMITS.
> A loan-produced posting has none of it. Nobody submits legs; a disbursement **generates**
> them. The observation is purely a **read-back**.

**The driver has decided it: grade this in the `loan` context, as a read-back.** That
decision is made; do not re-open it. Two things follow — `loan` vectors are already
read-back shaped, and `loan` has a working `cmd/conformance` binary, so `kills.sh` is your
ordinary instrument.

## ONE PROPERTY. Not four.

The only run that ever succeeded on this material (`OH-LEDGER-X`) was asked for **one**
property and finished in 92 iterations. You are asked for one:

> **A journal-entry batch containing MORE THAN ONE PAIR still balances:
> sum(debits) == sum(credits), exactly, in integer minor units.**

`.softhouse/capture/gl-accounting-surface/out/journalentries-loan-10-raw.json` is the only
capture that sees this — a **disbursement pair plus a fee pair**:

    OHLGR-Loan-Portfolio     DEBIT   100000.0
    OHLGR-Fund-Source        CREDIT  100000.0
    OHLGR-Income-From-Fees   CREDIT     100.0
    OHLGR-Fund-Source        DEBIT      100.0
    sum debits 100100.0 == sum credits 100100.0

`journalentries-loan-12-raw.json` is a **single** pair (100000.0 each way) and **cannot**
grade this — a one-pair batch balances under almost any defect. **Verify both against the
files before building on them.**

Why this is worth a vector: a port that sums only the FIRST pair, or that drops the fee
pair, or that nets the two `OHLGR-Fund-Source` legs into one before summing, produces a
balanced-looking answer on loan 12 and a wrong one on loan 10. **`ledger-wrong-split-drift`
does not cover it** — that drive proves I-2 is not a restatement of I-1 on a *posted*
command, and it lives in a context whose harness posts. Read its defect string and confirm
this for yourself before writing anything.

## The map

* **Vector shape** — copy `.softhouse/vectors/loan/LN-L07-summary-total-outstanding-fee-and-penalty.json`.
  Its `request` holds observed values, its `oracle.seam` is a descriptive name
  (`loan-summary-outstanding`). Choose an equally descriptive seam for a journal-entry
  read-back.
* **Drive registration** — `nexus/internal/apps/loan/conformance/impl.go`; there are ten
  worked `loan-wrong-*` examples. Copy the shape.
* **Minor units** — captures hold floats (`100100.0`); vectors hold integers (`10010000`).
  That transcription is the one place a residue can enter.
* **Instrument** — `kills.sh loan <impl>` works here. Controls:

      kills.sh loan         loan-wrong-summary-drops-penalty      -> 2
      kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
      kills.sh parties      parties-wrong-iota-ordinals           -> 12
      kills.sh charges      charges-wrong-rounding-half-even      -> 1

  **Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. An empty
  result means the MEASUREMENT FAILED. If a control is wrong, the instrument is wrong.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument**. Report every kill count, and prove
the instrument was live (the controls, plus an existing `loan` drive that still kills).

**Do not manufacture coverage.** If something is not discriminated by these captures, say so
and record what a capture would need. `OH-INV-Z` did exactly that for `totalOverpaid`.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Double-entry, append-only. Balances DERIVED, never written** (I-3/I-4).
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** — exactly 12 pairs. Do not
  touch `.softhouse/conformance.sh` (you are adding no ledger drive, so its census pin
  stays 17).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `loan`.**
- Every vector carries `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash
  after writing**. Never synthesise a value you did not observe.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **exactly 12 pairs**, census **17**. Run it EARLY.

~500 iterations for ONE property. **Commit by iteration 120.** If you are reading past 150
without a file on disk, you have mis-scoped it — commit what you have and say so.
