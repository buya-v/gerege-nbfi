# OH-GLVEC-AB — vector the loan→GL postings. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-glvecb` (branch `feat/OHGLVECb`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.** Another run
holds the machine's oracle access. A read-only health probe is permitted.

## The gap, measured

The loan→GL journal-entry captures have been committed since `OH-GL-T`, and **not one
vector cites them**:

    journalentries-loan-10-raw.json   cited by 0 vectors
    journalentries-loan-12-raw.json   cited by 0 vectors
    journalentries-all-raw.json       cited by 0 vectors

Meanwhile **all 17 `ledger` vectors** grade the seam `ledger_rest_posting` — the direct
journal-entry API. **Nothing grades a posting that a LOAN produced.** Until yesterday that
was impossible here: every seeded loan sat on an `accountingRule: NONE` product, so the
surface did not exist. It exists now and is ungraded.

## THE MAP — do not go looking for these

**Captures**, in `.softhouse/capture/gl-accounting-surface/out/`. **Verify every number
against the file before building on it.**

`journalentries-loan-12-raw.json` — a disbursement:

    id=23  OHLGR-Loan-Portfolio  DEBIT   100000.0   entryType.id=2
    id=24  OHLGR-Fund-Source     CREDIT  100000.0   entryType.id=1

`journalentries-loan-10-raw.json` is richer — a disbursement pair **plus a fee pair**,
debits 100100.0 == credits 100100.0. That one grades a **sum across a multi-pair batch**,
which a single pair cannot.

**The port's entry side** — `nexus/internal/apps/ledger/money.go:211-215`:

    type EntrySide int32
    const ( EntryCredit EntrySide = 1 ; EntryDebit EntrySide = 2 )

These already match the oracle's `entryType.id`.

**Vector schema** — read `.softhouse/vectors/ledger/LDG-01-manual-je-3leg-minor-units.json`.
Top-level keys: `schema, case_id, context, class, title, dec2_revision, _note,
capabilities_required, provenance, oracle, request, expect, graded_against,
invariant_exemptions`. `oracle.seam` is `ledger_rest_posting` for all 17 existing vectors —
**your seam is different and must be named differently**, because these postings come from
a loan disbursement, not a REST posting command. Choose the name and justify it in one line.

**Drive registration** — `nexus/internal/apps/ledger/conformance/impl.go:140`
(`RegisterWrong(name, defect string, p EntryPoster)`), called from `:1243` onward with
**seventeen** worked examples. `Register("ledger-go", NewGoPoster())` at `:1242`.

**THE INSTRUMENT FOR `ledger` IS NOT `kills.sh`.** `ledger` has **no `cmd/conformance`
binary**; `kills.sh ledger …` fails loudly (`NOT a zero` — meaning the measurement did not
happen, not that the drive is inert). Ledger drives are exercised by
`bash .softhouse/conformance.sh`, which prints a `CENSUS wrong ledger implementations` block
and one `KILLED …` line per drive. **The census is your instrument.** It currently reads
**17**; if you add a drive it must read 18 with yours among the KILLED lines, and you must
update `EXEMPTION_PIN_LEDGER_WRONGIMPLS` in `.softhouse/conformance.sh` (that pin is the
**only** line of the bar you may touch — `OH-LEDGER-X` changed exactly that one line).

## The properties

1. **The batch BALANCES — sum(debits) == sum(credits), exactly, integer minor units.**
   I-1/I-2. `ledger-wrong-split-drift` already proves I-2 is not a restatement of I-1 —
   **read its defect string before writing anything near this**, and do not re-register a
   defect the corpus already kills.
2. **DIRECTION, which a balance check CANNOT catch.** A disbursement DEBITS the portfolio
   and CREDITS the fund source. **A port that inverts the pair still balances.** Note
   `ledger-wrong-side-ordinals-swapped` (added by `OH-LEDGER-X`) swaps *sides globally*;
   a **per-account direction** defect is a different shape — decide whether it is genuinely
   distinct, and **say so either way**.
3. **The fee pair posts to a DIFFERENT account pair than principal.** A port routing every
   posting through one mapping still balances AND still gets directions right. Loan 10 is
   the capture that sees this; loan 12 cannot.

**Check each against the existing seventeen first.** "Already covered" is a finding, not a
failure.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument**. Say which, per drive. **Prove the
instrument was live** — the census showing the other seventeen still dying.

**And do not manufacture coverage.** If a property is not discriminated by these captures,
say so and record what a capture would need. `OH-INV-Z` did exactly that for
`totalOverpaid` and it was the right call.

## Measuring the other contexts (controls)
    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. If a
control is wrong, the instrument is wrong — not the tree.

## Rules of evidence
- **Never synthesise a value you did not observe.** `capture_ref`, `capture_sha256`,
  `citation`; **re-verify the hash after writing**.
- Captures hold float-formatted money (`100000.0`); vectors hold **integer minor units**
  (`10000000`). That transcription is the one place a residue can enter.
- **Cite `file:line`**, from the FILE, not a comment-stripped view.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Double-entry, append-only. Balances DERIVED, never written** (I-3/I-4). Corrections are
  reversing entries. This task is that invariant's home ground.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** — exactly 12 pairs.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **exactly 12 pairs**, census 17 (or 18 with your drive).
**Run it EARLY** — a run this week lost everything to a HARD guard found at iteration 400.
~500 iterations; **commit by iteration 150** even if incomplete.
