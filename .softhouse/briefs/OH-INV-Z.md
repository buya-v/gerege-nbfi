# OH-INV-Z — promote the SETTLED transfer. NO ORACLE NEEDED.

Worktree: `/Users/buv/oh-gerege-invz` (branch `feat/OHINVz`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE. Do not run COB
or advance the business date.** Everything here is promotable from captures **already
committed on `main`**. A read-only health probe is permitted.

## What five runs bought you

The investor details seam was unobservable for weeks: the details table was empty, and
`OH-INV-Q` correctly **deleted four candidate drives** rather than merge them inert. It is
observable now. `OH-INV-Y` created the `ASSET_TRANSFER(100)` mapping (authorised by Buyan)
and COB **settled transfer 28** on loan 12.

Committed at **`.softhouse/capture/investor-asset-transfer-100/`** (subject-named, has an
`OWNER.md`). **Verify every number against the file before building on it.**

`out/transfer-28-je-post.json` has two top-level keys, `transferData` and
`journalEntryData` — **note the nesting, the entries are NOT at the top level**:

    transferData.status = ACTIVE, purchasePriceRatio = "97.25"
    transferData.details = {
      totalPrincipalOutstanding 100000.0   totalInterestOutstanding 6618.53
      totalFeeChargesOutstanding   100.0   totalPenaltyChargesOutstanding 57.0
      totalOutstanding         106775.53   totalOverpaid                   0.0 }

    journalEntryData → 10 entries, ids 119-128, debits 213551.06 == credits 213551.06
      119 CREDIT Loan-Portfolio 100000.0   124 DEBIT  Loan-Portfolio 100000.0
      120 CREDIT Interest-Recv    6618.53  125 DEBIT  Interest-Recv    6618.53
      121 CREDIT Fees-Recv         100.0   126 DEBIT  Fees-Recv         100.0
      122 CREDIT Penalties-Recv     57.0   127 DEBIT  Penalties-Recv     57.0
      123 DEBIT  Transfers-Susp 106775.53  128 CREDIT Transfers-Susp 106775.53

`out/db-transfer-je-mapping-ohinvy.txt` proves all ten entries belong to
`owner_transfer_id = 28` — that is the provenance linking postings to the transfer.

## THE MAP — do not go looking for these

**The port's derivation** — `nexus/internal/apps/investor/transfer.go:38-53`:

    type ExternalAssetOwnerTransferDetails struct {
        PrincipalOutstanding, InterestOutstanding,
        FeeChargesOutstanding, PenaltyChargesOutstanding,
        TotalOutstanding, TotalOverpaid MinorUnits
    }
    func (d …) DeriveTotalOutstanding() MinorUnits {
        return d.PrincipalOutstanding + d.InterestOutstanding +
               d.FeeChargesOutstanding + d.PenaltyChargesOutstanding
    }

**It already excludes `TotalOverpaid`, and it is already correct.** A drive must BREAK it.

**Where drives register** — `nexus/internal/apps/investor/conformance/impl.go:46`
(`RegisterWrong(name, defect string, e InvestorEvaluator)`), called from `impl.go:205-215`.
Two worked examples are there: `investor-wrong-blank-status` and
`investor-wrong-fabricates-transfer`. Copy their shape; the `defect` string is prose saying
what the wrong implementation does and which cell it turns red.

**`investor` HAS a working `cmd/conformance` binary**, so `kills.sh investor <impl>` works —
unlike `ledger`. Existing vectors: `.softhouse/vectors/investor/INV-01-transfer-read.json`
(read one for the schema) and `INV-02-transfer-read-empty.json`.

## The properties

1. **`totalOutstanding` is the sum of the FOUR buckets.**
   `10000000 + 661853 + 10000 + 5700 = 10677553` minor units. **Fee (10000) and penalty
   (5700) are non-zero AND DIFFERENT**, so a drive that drops the fee term and a drive that
   drops the penalty term are BOTH discriminated, and a term-swap cannot hide.
2. **The status transition.** `INV-01` pins a `PENDING` transfer; transfer 28 is `ACTIVE`
   with `details` present, where PENDING has `details` absent. **Absent vs present is a
   distinct fact** from the value of any cell.
3. **The journal entries balance** — debits 213551.06 == credits 213551.06 — and the posted
   amount is the **full outstanding**, never `ratio × outstanding`.

## WHAT IS **NOT** OBSERVABLE — do not vector it, and say so

**`totalOverpaid` is `0.0`.** So this capture **cannot** discriminate whether overpaid is
excluded from the total: including or excluding zero both give `106775.53`. A drive that
folds overpaid in **would kill ZERO on this corpus**. That is the finding `OH-GAP-M`'s agent
got wrong by guessing "− overpaid", and it stays **unobservable** until a capture exists
with a non-zero overpaid.

**Do not register that drive and then delete it to look thorough** — the driver already
recorded this limitation in `a617001a`. Record what a capture would need (a loan overpaid at
transfer time) and move on.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument**. Say which, per drive; report every
kill count. **Prove the instrument was live** — controls below, plus
`investor-wrong-blank-status` and `investor-wrong-fabricates-transfer`, which each kill 1.

## Measuring it
    kills.sh investor     investor-wrong-blank-status           -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** If a control is wrong, the instrument is wrong.

## Rules of evidence
- **Never synthesise a value you did not observe.** Every vector carries `capture_ref`,
  `capture_sha256`, `citation`; **re-verify the hash after writing**.
- Captures hold float-formatted money (`106775.53`); vectors hold **integer minor units**
  (`10677553`). That transcription is the one place a residue can enter.
- **Cite `file:line`**, from the FILE, not a comment-stripped view.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Double-entry, append-only. Balances DERIVED, never written** (I-3/I-4).
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. The details columns are
  `scale = 6`; if a residue value appears, **REFUSE it**, never vector it.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** — exactly 12 pairs.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `investor`.**

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **exactly 12 pairs**, wrong-ledger census **17**. **Run
it EARLY.**

~500 iterations. **Commit by iteration 150** even if incomplete. Five runs have died at the
cap or had their terminal killed; every one that committed early kept its work.
