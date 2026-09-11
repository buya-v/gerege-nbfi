# OH-DELINQ-U — grade the delinquency day-counts. Observed, ungraded. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-delinq` (branch `feat/OHDELINQu`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout
— do not read or write there, and **never exercise the push gate**. The driver pushes.

## WHERE THIS CAME FROM

`OH-LOANCOV-T` made the loan corpus measurable and triaged every function the graded
vectors never reach (`.softhouse/findings/F-2026-09-11-loan-graded-coverage.md`, §4.2):

> `delinquency.go:96` `OverdueDays` / `delinquency.go:109` `DelinquentDays` —
> **IMPLEMENTED, OBSERVED, UNGRADED.** The committed loan details carry a delinquency
> block and the corpus pins a business date. Gradeable without a capture.

That is the holds shape without needing a capture. **Pure grading — the shape that has
landed every time this programme has run it.**

## THE OBSERVATION — verified by the driver, re-derive it yourself

Committed loan read-backs in `.softhouse/capture/loan/out/`, business date **2026-09-01**:

    capture                    overdueSince   delinquentDays
    loan-2-detail-raw.json      2026-08-01         31
    loan-1-detail-raw.json      2026-07-01         62
    loan-5-detail-raw.json      2026-07-01         62
    loan-4-detail-raw.json      2026-06-01         92
    loan-3-detail-raw.json      (none)              0
    loan-L06-detail-raw.json    (none)              0

**Check each against the file before building on it.** The arithmetic:

    2026-08-01 -> 2026-09-01 = 31          (August has 31)
    2026-07-01 -> 2026-09-01 = 31+31 = 62
    2026-06-01 -> 2026-09-01 = 30+31+31 = 92   (June has 30)

## WHY THIS DISCRIMINATES, AND WHAT IT DOES NOT

**It catches a 30-day-month approximation** — a port computing days as months×30 gets
`30 / 60 / 90` and fails every non-zero row, because June, July and August are not all the
same length. That is a real and common porting shortcut.

**It catches the absent-date case** — `overdueSinceDate` null must yield `0`, not an error
and not a days-since-epoch value.

**It does NOT discriminate the paused/grace subtraction.** `DelinquentDays` is
`overdueDays − pausedDays − graceDays`, floored at 0 [`delinquency.go:109`], but in every
observed row `delinquentDays == pastDueDays`, so paused and grace are both **0**. A port
that ignores them passes. **Do not register a drive for that** — it would kill zero. Record
what a capture would need (a loan with a pause period or a grace setting), exactly as the
last several runs have.

**Nor the negative clamp** in `OverdueDays` (`days < 0 → 0`): no observed loan has an
overdue date after the business date.

## TIMEZONE — this is the rule most likely to bite a day-count

`CLAUDE.md`: two time zones, **no DST** — `Asia/Ulaanbaatar` (+08) and `Asia/Hovd` (+07).
**Never hard-code an offset.** `OverdueDays` works through `dateOnly(...)`
[`delinquency.go:96`]. A day-count taken in UTC instead of the tenant's zone can be off by
one near midnight. **Check how `dateOnly` resolves the zone, and say so in your commit.** If
the observed dates cannot discriminate a UTC-vs-Ulaanbaatar defect (they are all
midnight-aligned calendar dates), say that too rather than claim it is covered.

## The task
1. Promote vector(s) on a loan delinquency seam pinning `delinquentDays` for the rows above
   — at least one of each non-zero month-length combination, plus the absent case.
   **Do not clone**: six rows with three distinct facts is not six vectors' worth of
   coverage. `OH-DEEP-E` produced 18 files carrying 10 facts; eight were discarded.
2. Register a drive for the **30-day-month** defect and one for **absent → non-zero**, and
   measure each against the store **without** your vectors and **with** them.
3. **Confirm with coverage** that the functions are now reached:

       go test -coverpkg=./internal/apps/loan -coverprofile=/tmp/c.cov ./internal/apps/loan/conformance/...
       go tool cover -func=/tmp/c.cov | grep -E 'OverdueDays|DelinquentDays'

   Both read **0.0%** today. The loan committed-store test (`OH-LOANCOV-T`) makes this
   measurement real. If they still read 0.0%, your vectors do not reach the rule — say so.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. Report every kill count. **Do not manufacture coverage.**

## Measuring it
    kills.sh loan loan-wrong-summary-drops-penalty            -> 2
    kills.sh savings savings-wrong-hold-folded-into-balance   -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365 -> 45

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** **FLAGS ARE PER-BINARY.** Use `kills.sh`.

After your change `loan-go` must still pass **all** loan vectors, **all 24** loan drives
must still kill, and the loan committed-store test must still pass.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float anywhere, including day-count intermediates.
- **Two time zones, no DST; never hard-code an offset.**
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

~500 iterations for a pure grading task. **Commit by iteration 120.**
