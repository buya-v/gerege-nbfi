# OH-LEDGER-X — grade the loan→GL posting surface. THE MAP IS BELOW. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-ledgerx` (branch `feat/OHLEDGERx`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.** Everything
here is promotable from captures already committed on `main`.

## `OH-LEDGER-V` DIED DOING THE RESEARCH. DO NOT REPEAT IT.

It burned **503 iterations** and wrote **nothing**, dying while reading `type EntrySide`.
The driver then found everything it needed **in four commands**. That map is below.
**Do not go and rediscover any of it.** If you find yourself grepping for where drives are
registered or what `EntrySide` is, stop — it is here.

### The map

**The port's entry side** — `nexus/internal/apps/ledger/money.go:211-215`:

    type EntrySide int32
    const (
        EntryCredit EntrySide = 1
        EntryDebit  EntrySide = 2
    )

**These ALREADY match the oracle** (`entryType.id`: CREDIT=1, DEBIT=2). So the ordinals are
correct today; a drive must SWAP them to prove anything.

**Where drives are registered** — `nexus/internal/apps/ledger/conformance/impl.go:140`:

    func RegisterWrong(name, defect string, p EntryPoster) { … }

called from `impl.go:1243` onward, with **sixteen worked examples in a row**. Read
`:1243-1300` and copy the shape. The `defect` string is prose explaining what the wrong
implementation does and why it matters — the existing sixteen are the standard.
`Register("ledger-go", NewGoPoster())` at `:1242` is the correct implementation.

**The interface** is `EntryPoster`. `NewGoPoster()` is the correct poster; each wrong
implementation is a small struct with the same method set and one defect.

**The measurement instrument for `ledger` is NOT `kills.sh`.** `ledger` has **no
`cmd/conformance` binary**, so `kills.sh ledger …` and `redcount.sh <wt> ledger` fail —
correctly and loudly: `no conformance binary for context 'ledger' … NOT a zero`. That means
the measurement did not happen; **it is not a zero-kill drive.** Ledger drives are exercised
by `bash .softhouse/conformance.sh`, which prints:

    conformance: CENSUS wrong ledger implementations — discovered 16 registered as DELIBERATELY
    conformance:   KILLED  ledger-wrong-<name> — exit 1, ledger parity FAIL n + oracle-refusal FAIL m
    conformance:   all 16 wrong ledger implementations DIED through this harness, not by hand

**That census is your instrument.** After adding a drive the count must become 17 and your
drive must appear in a `KILLED` line. **A registered drive that does NOT appear killed is
inert** — resolve it, never merge it.

## The data you are grading

`.softhouse/capture/gl-accounting-surface/out/` — the first loan→GL journal entries in this
programme. **Verify every number against the file before building on it.**

`journalentries-loan-12-raw.json` — a disbursement:

    id=23  OHLGR-Loan-Portfolio  DEBIT   100000.0   entryType.id=2
    id=24  OHLGR-Fund-Source     CREDIT  100000.0   entryType.id=1

`journalentries-loan-10-raw.json` is richer — a disbursement pair **plus a fee pair**
(debits 100100.0 == credits 100100.0), so it grades a sum across a multi-pair batch.
`journalentries-all-raw.json` has the full set.

## The properties. PROPERTIES, NOT A COUNT.

**You are measured on defects provably caught, never on file count.**

1. **THE BATCH BALANCES — sum(debits) == sum(credits), exactly, integer minor units.**
   I-1/I-2. Note `ledger-wrong-split-drift` already exists and proves I-2 is not a
   restatement of I-1 — read its defect string before writing anything near this, so you
   do not re-register a defect the corpus already kills.
2. **DIRECTION, which a balance check CANNOT catch.** A disbursement DEBITS the portfolio
   and CREDITS the fund source. **A port that inverts the pair still balances.**
3. **THE SIDE ORDINALS.** `EntryCredit=1, EntryDebit=2` — not zero-based, not alphabetical.
   A drive that swaps them is the `parties-wrong-iota-ordinals` class, which kills 12.
4. **The fee pair posts to a DIFFERENT account pair than principal.** A port routing every
   posting through one mapping still balances AND still gets directions right.

**Check each against the existing sixteen first.** If one is already covered, say so and
move to the next — that is a finding, not a failure.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument**. Say which, per drive. **Prove the
instrument was live** — the census showing the other sixteen still dying.

## BUDGET CHECKPOINT — this is not optional
Four runs have died at the cap. **Commit by iteration 150** even if incomplete: a committed
capture or drive survives a cap-death; an uncommitted one must be salvaged by hand, and one
run's salvage was later reverted entirely. **Run `bash .softhouse/conformance.sh` EARLY** —
a run this week lost everything to a HARD guard discovered at iteration 400.

## Measuring the OTHER contexts (controls)
    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
If a control is wrong, the instrument is wrong — not the tree.

## Rules of evidence
- **Cite `file:line`**, from the FILE, not a comment-stripped view.
- **Never synthesise a value you did not observe.** Vectors carry `capture_ref`,
  `capture_sha256`, `citation`; **re-verify the hash after writing**.
- Captures hold float-formatted money (`100000.0`); vectors hold **integer minor units**
  (`10000000`). That transcription is the one place a residue can enter.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Double-entry, append-only. Balances DERIVED, never written** (I-3/I-4). Corrections are
  reversing entries. This task is that invariant's home ground.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** — it stays at exactly 12
  (class, file) pairs.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**

## The bar
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh`. Expect exit 2 as the
§4.4.2 recorded decision, ledger finding set at **exactly 12 (class, file) pairs**, and the
wrong-ledger census at **17** with yours among the KILLED lines. Report the census block.
