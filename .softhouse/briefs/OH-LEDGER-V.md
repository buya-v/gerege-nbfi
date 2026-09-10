# OH-LEDGER-V — grade the loan→GL posting surface. NO ORACLE NEEDED.

Worktree: `/Users/buv/oh-gerege-ledgerv` (branch `feat/OHLEDGERv`)
Work ONLY in that directory.

## THE ORACLE IS HELD BY ANOTHER RUN. Take no captures.

`OH-INV-W` is creating an asset-owner transfer and running COB. **Issue no POST/PUT/DELETE,
do not advance the business date, take no captures.** A read-only health probe is
permitted. Everything below is promotable from captures **already committed on `main`**.
If you conclude a property needs a fresh capture, that is a **finding to record**.

## What just became available

`OH-GL-T` committed `.softhouse/capture/gl-accounting-surface/`, the first loan→GL
journal-entry observations in this programme. Until yesterday every seeded loan sat on a
product with `accountingRule: NONE`, so this surface did not exist here at all.

`out/journalentries-loan-12-raw.json` — a disbursement, and read it before anything else:

    id=23  OHLGR-Loan-Portfolio  DEBIT   100000.0   entryType.id=2
    id=24  OHLGR-Fund-Source     CREDIT  100000.0   entryType.id=1

`out/journalentries-all-raw.json` and `out/journalentries-loan-10-raw.json` carry more,
including a **fee posting pair**. Read all three. **Verify every number against the file
before you build on it** — this brief is a starting point, not a source of truth.

## TOOLING GOTCHA — this would cost you a budget

**`ledger` has NO `cmd/conformance` binary.** `internal/apps/ledger/conformance/` exists,
but there is no standalone runner, so `kills.sh ledger …` and `redcount.sh <wt> ledger`
both fail — correctly and loudly:

    measure: no conformance binary for context 'ledger' at
    ./internal/apps/ledger/conformance/cmd/conformance. NOT a zero.

That is the repaired tool telling you the measurement did not happen. **It is not a
zero-kill drive.** The ledger context's **16** wrong implementations are exercised through
`bash .softhouse/conformance.sh`, which prints a `CENSUS wrong ledger implementations`
block and a `KILLED <name> — exit 1, ledger parity FAIL n + oracle-refusal FAIL m` line per
drive. **That census is your measurement instrument for ledger.** Read how the existing 16
are registered before adding one.

Decide early and state your reasoning: does the disbursement-posting property belong in
`ledger` (with those 16) or in `loan`? `loan` HAS a working `cmd/conformance` binary and 10
drives. Either is defensible; pick one, say why, and stay in it.

## The properties. PROPERTIES, NOT A VECTOR COUNT.

**You are measured on defects provably caught, never on file count.** `OH-DEEP-E` was given
a count target and produced 18 files carrying 10 facts; eight were discarded.

1. **THE BATCH BALANCES: sum(debits) == sum(credits), exactly, in integer minor units.**
   I-1/I-2, the most important property in this programme. Loan 12: 100000.0 == 100000.0.
   Loan 10 is richer — a disbursement pair **plus** a fee pair, 100100.0 == 100100.0 — so
   it tests the sum across a multi-pair batch, not just a single pair.
2. **DIRECTION, which a balance check cannot catch.** A disbursement DEBITS the loan
   portfolio and CREDITS the fund source. **A port that inverts the pair still balances**
   and passes property 1. Pin which account takes which side.
3. **ENTRY TYPE IS AN ENUM WITH AN ORDINAL: `DEBIT` = 2, `CREDIT` = 1.** Note it is NOT
   zero-based and NOT alphabetical. `parties-wrong-iota-ordinals` kills 12 on exactly this
   class of defect, and it is the single most repeated porting error in this codebase.
4. **The fee pair posts to a DIFFERENT account pair than principal** (income-from-fees vs
   portfolio). A port that routes every posting to one mapping still balances and still
   gets directions right.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument**. Say which, per drive. **Report
every kill count.**

**Prove the instrument was live when a drive scores zero** — for `ledger` that means the
conformance census showing the other 16 still dying; for `loan`, the controls plus an
existing drive that still kills. `OH-INV-Q` did this correctly: it registered four drives,
all scored zero, and it deleted all four with the argument rather than merging them.

## Measuring it
`.softhouse/briefs/tools/kills.sh <ctx> <impl> [worktree]`, `redcount.sh <wt> <ctx>`.
**Repaired 2026-09-09**: no silent `0` — they exit 2 with empty stdout and a reason on
stderr. **An empty result means the MEASUREMENT FAILED.** Controls:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
    kills.sh loan         loan-wrong-summary-drops-penalty      -> 2

If a control is wrong, the instrument is wrong — not the tree.

## Rules of evidence
- **Cite `file:line`.** Line numbers from the FILE, not a comment-stripped view.
- **Never synthesise a value you did not observe.** Every vector carries `capture_ref`,
  `capture_sha256`, `citation`; **re-verify the hash after writing**.
- Captures hold float-formatted money (`100000.0`); vectors hold **integer minor units**
  (`10000000`). That transcription is the one place a residue can enter.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  MNT = ISO 496, minor unit 2.
- **The ledger is double-entry and append-only. Balances are DERIVED, never written**
  (I-3/I-4). Corrections are reversing entries. This task is that invariant's home ground.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. Never vector a residue.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`.** It must stay at exactly
  12 (class, file) pairs.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**

## The bar
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh`. Expect exit 2 as the
§4.4.2 recorded decision with the ledger finding set at **exactly 12 (class, file) pairs**.
**Run it EARLY** — a run this week lost everything to a HARD guard discovered at iteration
400. Report every drive's kill count and every capture's sha256.

## Budget
~500 iterations. Commit incrementally; a committed capture survives a cap-death and an
uncommitted one is salvaged by hand. If 150 iterations in without a commit, commit what
you have.
