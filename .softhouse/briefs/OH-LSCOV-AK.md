# OH-LSCOV-AK — make the `loanschedule` corpus measurable, then find what it never reaches. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-lscov` (branch `feat/OHLSCOVak`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout —
do not read or write there, and **never exercise the push gate**. The driver pushes.

## Read the map first — do not search
`.softhouse/maps/loanschedule.md` lists every seam, vector, drive (file:line), port function
(file:line), capture, and the measuring commands for this binary. It is generated from the
tree. **Use it instead of grep/find.** If something you need is not in it, say so in your report.

## Why
Six contexts can now say what their graded corpus reaches. For them, Go coverage
measured from the conformance package found six ungraded rules in two days — each then
graded by one short run. `loanschedule` has **no committed-store test**, so its coverage from
conformance means nothing yet (its map says ABSENT).

## The task
**1. Add `nexus/internal/apps/loanschedule/conformance/committed_store_test.go`.** Template, copy its
shape exactly: `nexus/internal/apps/savings/conformance/committed_store_test.go` — it drives the
REAL committed corpus through `LoadStore` → `Admit` → `Run` and asserts the reference
implementation passes, with a guard that ZERO vectors loaded fails. **`loanschedule`'s harness is SHAPED DIFFERENTLY** — it is the oldest context and did not grow from the
same template: `Admit(v, pin, repoRoot)` (`admit.go:103`), implementations are `contract.ScheduleGenerator`s in
`registry.go`, `Run` is `grade.go:380`, and the verdict line is `LOAN SCHEDULE N mismatch`, not
`parity_fail=N`. Read those four places and adapt the template's SHAPE, not its code. `conformance_test.go`
and several other `_test.go` files already exist here — some may call the port directly; **report the
committed-store-test-only figure separately from the package-wide one** (as the charges finding did) and say
which is honest.
**Call no port function directly** — coverage reached only through vectors is real; coverage from a
test that calls the port itself is manufactured and voids the measurement.
**Commit this as soon as it passes.**

**2. Measure** (from `nexus/`):

    go test -count=1 -coverpkg=./internal/apps/loanschedule -coverprofile=/tmp/c.cov ./internal/apps/loanschedule/conformance/...
    go tool cover -func=/tmp/c.cov | awk '$3=="0.0%"'

**3. Triage** — the finding. A 0.0% function is a CANDIDATE, not a gap. For each candidate that
implements a money rule (not a getter, String(), status predicate, error constructor): does an
observation behind it already exist in a committed capture? (The map lists them, with the warning
about earlier-instance captures.) If one exists, name the file and the figures a vector would take —
that is a grading run the driver can dispatch next. If none exists, say what a capture would need.
**Write it to `.softhouse/findings/F-2026-09-11-loanschedule-graded-coverage.md`** with `file:line` for every
function. Prior art to match: `.softhouse/findings/F-2026-09-11-loan-graded-coverage.md`.

## What you must NOT do
* **No vectors, no drives, no port changes.** This run measures and triages.
* **Do not manufacture coverage.** **Do not call a 0.0% a defect** — evidence decides.

## Measuring / controls
    kills.sh loanschedule loanschedule-wrong-half-even <worktree>          # must still read 5
    kills.sh loanschedule loanschedule-wrong-days-in-year-365 -> 45   (FLAGS: this binary REJECTS -root; use kills.sh)
    kills.sh parties parties-wrong-iota-ordinals              -> 12

**An empty result means the MEASUREMENT FAILED** (exit 2). **FLAGS ARE PER-BINARY.** Your new test
must PASS on the current tree, and every `loanschedule` drive must still kill.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float anywhere, including intermediates.
- **Do not touch `.softhouse/guards/`** (12 pairs) or `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference; **Oracle Database is prohibited.**
- **One bounded context: `loanschedule`.** Cite `file:line` from the FILE.

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY with the line
`§4.4.2-RECORDED-DECISION-EXIT`; **"a HARD guard failed" is a failure, not the recorded decision.**
~300 iterations. **Commit the test by iteration 80**, the finding after. **Write commit messages to a
file and use `git commit -F <file>`**. **Never commit TASK.md.**
