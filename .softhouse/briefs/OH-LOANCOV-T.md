# OH-LOANCOV-T — make the loan corpus measurable, then find what it never reaches. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-loancov` (branch `feat/OHLOANCOVt`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout
— do not read or write there, and **never exercise the push gate**. The driver pushes.

## WHY THIS TASK EXISTS

The last three runs found and closed a genuinely ungraded `CLAUDE.md` non-negotiable
(savings holds). The instrument that found it was **Go coverage of the port, measured from
the conformance package**:

    go test -coverpkg=./internal/apps/<ctx> -coverprofile=/tmp/c.cov ./internal/apps/<ctx>/conformance/...

It showed `HeldOf` / `AvailableOf` / `AccountBalanceOf` at 92.9–100% under unit tests and
**0.0% from conformance** — unit-tested, never GRADED against the oracle.

**But that instrument has a hole, and the driver found it before dispatching on it.** It
measures what the conformance package's **`go test` files** reach, not what the **grading
binary** reaches when it runs the vectors. `loanschedule` reads **0.0%** from conformance
while its 50 vectors PASS against the oracle — because its conformance package has no test
that drives the committed corpus. So the numbers are only meaningful for a context that has
such a test.

`OH-HOLDGRADE-S` built exactly that for savings:
`nexus/internal/apps/savings/conformance/committed_store_test.go` — it calls the real
harness, **`LoadStore` → `Admit` → `Run`**, over the real committed corpus, and asserts the
reference implementation passes. **It calls none of the port functions directly** — they
are reached only through the vectors. That is what makes the coverage *real* rather than
*manufactured*. **Read that file first. It is your template.**

## The task

**1. Add the same committed-store test to `loan`.** Copy the savings pattern: drive the real
committed loan corpus through `LoadStore` → `Admit` → `Run` and assert `loan-go` passes.
**Call no port function directly** — if a test calls `SumJournalEntryBatch` itself, the
coverage is manufactured and the whole measurement is void.

**2. Measure what the graded corpus actually reaches:**

    go test -coverpkg=./internal/apps/loan -coverprofile=/tmp/loan.cov ./internal/apps/loan/conformance/...
    go tool cover -func=/tmp/loan.cov | awk '$3=="0.0%"'

Report the before/after total, and the list of loan functions still at **0.0% from the
graded corpus**.

**3. Triage that list the way the holds case was triaged — this is the finding.** A
0.0% function is a **candidate**, not a gap. For each candidate that implements a money rule
(not a getter, a String(), an error constructor), **ask whether any observation behind it
exists in the committed corpus**. The holds case was confirmed because every apparent "hold"
in the captures turned out to be a *field* (`withholdTax`, `amountOnHold`) and no capture
carried a hold-flagged transaction. **That confirmation is what turns a number into a
finding.**

**Write the triage to `.softhouse/findings/F-2026-09-11-loan-graded-coverage.md`**: for the
top candidates, the function, `file:line`, what money rule it implements, whether an
observation exists, and — if none does — what a capture would need.

## What you must NOT do

* **Do not write vectors or drives.** This run makes the corpus measurable and triages the
  result. Grading any gap it finds is a later run's work, after a capture if one is needed.
* **Do not manufacture coverage** by calling port functions from the test.
* **Do not treat a 0.0% as a defect.** Report candidates and your triage; let the evidence
  decide which are real. The driver's own first attempt at this measurement over-claimed by
  conflating "not referenced" with "not exercised", and that is recorded in
  `.softhouse/findings/F-2026-09-10-savings-holds-ungraded.md` so it is not repeated.

## Measuring / controls
    kills.sh loan loan-wrong-summary-drops-penalty            -> 2
    kills.sh savings savings-wrong-hold-folded-into-balance   -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365 -> 45

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** **FLAGS ARE PER-BINARY.** Use `kills.sh`.

After your change, `loan-go` must still pass **all** loan vectors and **all 24** loan drives
must still kill. Your new test must PASS on the current tree.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `loan`.**
- Cite `file:line` from the FILE, not a comment-stripped view.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations. **Commit the test as soon as it passes**, then the finding.
