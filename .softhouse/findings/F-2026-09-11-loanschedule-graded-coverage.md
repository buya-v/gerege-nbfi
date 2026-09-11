# F-2026-09-11 — the `loanschedule` graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** The measuring control is committed (`12733021`); no capture
was taken and no vector, drive or port line was written by this run. The triage below names
what the corpus still cannot grade, and for each candidate says whether an observation
already exists.
**Task:** `OH-LSCOV-AK`, bounded context `loanschedule`, branch `feat/OHLSCOVak`.
**Found by:** Go coverage of the `loanschedule` port, measured with the port as `-coverpkg`
and the **conformance package** as the test target. Before this run the map read
**ABSENT** for this context's committed-store test, so no vector could move the number and
coverage from conformance meant nothing.

## 1. The missing control, added

Added `nexus/internal/apps/loanschedule/conformance/committed_store_test.go` (commit
`12733021`). `loanschedule` is the oldest context and did not grow from the savings
template, so only the template's **shape** was reused; every harness call is the
context's own:

* `Admit(v, pin, repoRoot)` — `conformance/admit.go:103`, not an `Options` value;
* the implementations are `contract.ScheduleGenerator`s registered in
  `conformance/registry.go:35` (`Register`) and `:51` (`RegisterWrong`); the reference is
  the port itself, built by `loanschedule.New()` and registered as `"loanschedule-go"` in
  `conformance/cmd/conformance/impl_hook.go:49`;
* `Run` is `conformance/grade.go:380`;
* the verdict is the report's `LOAN SCHEDULE %d mismatch(es)` line
  (`conformance/report.go:687`), **not** savings' `parity_fail=N`.

`cmd/conformance` is a *different package* with no test files, so its `init()`
(`impl_hook.go:48`) never runs under `go test`; the test therefore constructs the same
reference the binary registers rather than relying on a registration side effect.

It drives the **real committed store** through `LoadStore` → `Admit` → `Run` and asserts
the reference passes, with the anti-vacuity guards the brief asks for: zero loaded vectors
fails, every loaded vector must be admissible, `Run` must not be fatal, `ParityPass != 0`,
`graded_cells != 0`, `invariant_violations == 0`, and the whole non-parity counter set
(`ParityFail + ContractFail + SelfTestFail + Refused + Inadmissible + Errored`) must be
zero. It also pins the one meaningful control this context has: `ParityPass` must equal
the number of class-`PARITY` vectors in the store, so dropping a parity vector is a
failing test rather than a silent return to `0.0%`.

**Committing coverage.** The test calls **no port function directly.** The only port symbol
it names is `loanschedule.New()` — the same constructor the grading binary calls at
`impl_hook.go:49`. Every statement it reaches is reached *through the vectors*, so the
coverage it produces is real, not manufactured. Removing a vector removes the coverage.

On the committed store the control loads **50 vectors (46 `parity`, 4
`contract-refusal`)** and passes; `conformance.sh` independently reports the same 46 parity
vectors, `7884` cells compared (`VERDICT: PASS`, `/tmp/ls_conf.log:1354`).

## 2. Measurement — the two reported figures are identical

Prescribed command (from `nexus/`), run as written:

```
go test -count=1 -coverpkg=./internal/apps/loanschedule \
    -coverprofile=/tmp/ls_pkg.cov ./internal/apps/loanschedule/conformance/...
go tool cover -func=/tmp/ls_pkg.cov | awk '$3=="0.0%"'
```

Two readings are reported because the brief asks for the committed-store-test-only figure
separately from the package-wide one, "as the charges finding did".

| run | test target | statements | coverage | functions at 0.0% |
|---|---|---:|---:|---:|
| no control (`-run '^$'`) | whole conformance package | 682 | 0.0% | all |
| **package-wide** (prescribed) | whole conformance package | 682 | **78.4%** | **13** |
| **committed-store-test only** | `-run '^TestCommittedCorpusPassesTheReferenceImplementation$'` | 682 | **78.4%** | **13** |

`diff <(go tool cover -func=/tmp/ls_pkg.cov | sort) <(go tool cover -func=/tmp/ls_vo.cov |
sort)` → **no output**. The two function sets are byte-identical, not merely equal in
percentage.

**Both figures are honest, and here the distinction does not bite.** The other
`_test.go` files in this package (`conformance_test.go`, `coverage_refusal_test.go`,
`exemption_test.go`, `structural_test.go`, the verdict tests, …) do **not** import the
port: `grep -n 'loanschedule\.' conformance/*_test.go` finds no port selector call — the
only matches are the control's own `loanschedule.New()` and a schema string literal at
`structural_test.go:758`. So no test in the package calls the port directly, no probe
manufactures coverage, and the package-wide number carries no inflation to strip out. The
**committed-store-test-only** row is the canonical "what the graded corpus reaches"; the
package-wide row is the command the brief prescribes and the one to compare against future
changes. They coincide because this package has exactly one port-touching test, and that
test grades only through vectors. (Contrast `charges`, whose package-wide figure was 57.5%
while its vector-only figure was 41.2%, because its probes called the port directly.)

## 3. Triage method (the part that turns a number into a finding)

A `0.0%` is a **candidate, not a gap**. Each candidate that implements a **money rule** (not
a getter, a `String()`, an enum decoder, a status predicate, an error constructor) is
checked against one question only:

> **Does an observation behind it already exist in a committed capture?**

If yes: name the file and the figures a vector would take — a grading run the driver can
dispatch next. If no: say what a capture would need. Evidence decides; **no `0.0%` here is
asserted to be a defect.**

Because the port is pure schedule arithmetic with no persistence and no status machine,
the branch level also matters: a money rule can be *reached* yet leave a whole money
branch at zero hits. Those blocks are reported in §5, with the same observation test.

## 4. Triage of the `0.0%` candidates

**No `0.0%` function implements a reference money rule.** All 13 fall into four excluded
classes (full list in Appendix A):

| class | functions (`file:line`) | why it is `0.0%` |
|---|---|---|
| error constructor | `generator.go:123` `invalid` | called only on malformed requests no vector carries |
| dead accessor | `emi.go:1823` `calculatedDueInterestMinor` | **no caller at all** — the only reference is a comment at `emi.go:249`; `dueInterestMinor` (`emi.go:1828`) reads the same chain and is `100.0%` |
| wrong-drive twin of the currency rounding | `rounding.go:163` `minorFromMajorHalfEven`, `rounding.go:171` `roundHalfEvenToInt` | reached only by `loanschedule-wrong-half-even` (`wrongdrives.go:144`); the reference's `minorFromMajor` (`rounding.go:146`) is `100.0%` |
| wrong-drive type and constructors | `wrongdrives.go:122` `Generate`, `:144,:162,:177,:190,:202,:214,:226,:239` | reached only when the binary selects a drive; a test binary does not run `impl_hook.go:48` |

The two shared helpers the wrong drives *do* use — `wrongdrives.go:86` `applyRequest`
(`54.5%`) and `wrongdrives.go:108` `dueDateSeed` (`66.7%`) — are **not** `0.0%`: the
reference's own `generateFor` calls them (`generator.go:88,107`), so the committed corpus
reaches them. Their uncovered blocks are the drive-only variant arms.

The HALF_EVEN pair is the only `0.0%` code that rounds money, and it is **not a gap**: it
is the deliberately wrong twin, it is already discriminated by the corpus
(`kills.sh loanschedule loanschedule-wrong-half-even` → **5**, §8), and no admissible
vector can make the reference execute it because `RoundingMode != HALF_UP` is refused
before any arithmetic (`generator.go:371`, mirrored in the harness at `admit.go:1041`;
vector `REFUSE-02-half-even-ungraded.json`). It is graded as a drive, not as a reference
rule.

## 5. The finding — what the graded corpus never reaches

At the function level: **nothing reachable is ungraded.** Every reference money rule is
already reached by the committed corpus, most at `100.0%` (Appendix B). What the corpus
never reaches is a set of money-rule **branches**, and they split into two kinds.

### 5.1 Money-rule branches that are unreachable by construction

These cannot be graded by any vector or capture because the graded domain refuses the
input shape before the branch is reachable:

* **The maturity-date credit and its zero-length interest segment.**
  `emi.go:1614-1621` (`registerBalanceChange` `onMaturity`) and `emi.go:1749-1751`
  (`segmentCalculatedInterest`, `lengthTillDue == 0`) are 0 hits. The branch is reached
  only for a balance change dated on the last period's due date, and
  `validateGradedDomain` refuses exactly that: `compareDates(d, lastDue) >= 0` at
  `generator.go:404-408` (mirrored at `admit.go:1080-1083`; vector
  `REFUSE-04-disbursement-after-maturity.json`). So no capture can help — the reference
  oracle itself silently discards the shape into an all-zero schedule.
* **The re-adjust no-op guard.** `emi.go:2279-2281` (`adjusted == original`) is 0 hits.
  Under `minorDigits == 2`, enforced at `generator.go:359` / `admit.go:1030`,
  `shouldBeAdjusted` (`emi.go:2231`) admits only a strictly positive gap, and
  `emiAdjustment` (`emi.go:2209`) returns `last - penultimate` from adjacent unpaid
  periods, so the half-up division of `difference` by `n >= 2` cannot round back to
  `original`. Unreachable, not unobserved.
* **The `divisor == 1` shortcut.** `rounding.go:204` is 0 hits. `divideMinorHalfUp` is
  called at `emi.go:2276` only after `emiAdjustment` found an adjacent unpaid pair, so
  `len(related) >= 2` and `divisor = max(1, len(related)) >= 2`. Unreachable.
* **The zero-denominator rate factor.** `emi.go:1971-1973`
  (`rateFactorByRepaymentPeriod`, `calculatedDays == 0`) is 0 hits. No zero-length
  repayment period exists, and the only zero-length segment the model can build is the
  maturity credit refused above. The proration *itself* is reached (`emi.go:1970` is
  `87.5%`); only the degenerate denominator is not.
* **The paid-exceeds-due guard.** `emi.go:2148-2153` (`applyFinalPeriodResidual`) is
  0 hits. `emi.go:2127-2133` records it as ported deliberately and **provably inert on an
  unpaid schedule**: `totalDuePaidDiff` is the sum of every credited amount, and no single
  period's due principal can exceed it. Kept, not dropped; unreachable.
* **The negative money arm.** `rounding.go:63-65` (`roundHalfUpToInt`, `x.Sign() < 0`) is
  0 hits. The graded domain carries no negative money — principal and interest are
  non-negative integers in minor units. Unreachable.
* **The window dead-ends.** `emi.go:1552` (`findPeriodForBalanceChange` returning `nil`),
  `emi.go:1584` (`addDisbursement`, owner `nil`) and the `insertSegment` clamps
  `emi.go:1655-1659` are 0 hits because the same window refusal (`generator.go:404-408`)
  removes every date that could escape the period list.

### 5.2 One reachable path the corpus never samples — structural, not a money rule

`emi.go:1529` — the `inPeriodM1` **non-first** arm — is the one 0-hit branch that a vector
*could* reach inside the graded domain. `inPeriodM1` is M1 membership `(FromDate, DueDate]`,
used by `findPeriodForBalanceChange` (`emi.go:1546`) to decide which repayment period a
balance change registers into, hence the segmentation and the effective due date
(`emi.go:1518-1530`). The first arm covers period 0; the non-first arm fires only for a
balance change dated in a **later** repayment period.

*Observation.* **None in the committed corpus.** All 50 committed vectors disburse within
the first repayment period: the largest disbursement month offset is `1`
(`P-03-disbursement-on-repayment-due-date.json`, 2024-01-01 → 2024-02-01, still period 0
under M1's inclusive `<=`), and the only later date,
`REFUSE-04-disbursement-after-maturity.json` (offset 6), is refused at
`generator.go:404-408`. No committed capture is cited for any other shape.

*What a capture would need.* A single-disbursement loan whose disbursement date falls
strictly inside a later repayment period (`ScheduleStartDate <= d < lastDue`, after the
first period's due date), read back as its schedule. That would exercise the M1 non-first
arm, the resulting segmentation and the pre-disbursement zero rows. This is **not** a
money-rule candidate under the §3 test — `inPeriodM1` is a date-membership predicate, not
an arithmetic rule — so it does not make the corpus unmeasurable. It is recorded because
the brief asks what the corpus never reaches, and because the *proration* money mechanism
it feeds is already reached by the drift/short-period vectors (`emi.go:1970` `87.5%`).

## 6. Summary of triage

| candidate | `file:line` | reference money rule? | observation in corpus? | action |
|---|---|---|---|---|
| `calculatedDueInterestMinor` | `emi.go:1823` | no — dead accessor | n/a (no caller) | none |
| `invalid` | `generator.go:123` | no — error constructor | n/a | none |
| `minorFromMajorHalfEven` | `rounding.go:163` | only in the wrong drive | yes (tie vectors) | none — drive is killed (5) |
| `roundHalfEvenToInt` | `rounding.go:171` | only in the wrong drive | yes (tie vectors) | none — drive is killed (5) |
| `wrongScheduleGenerator.Generate` | `wrongdrives.go:122` | only in the wrong drives | n/a (drive code) | none |
| `NewWrong*` constructors (7) | `wrongdrives.go:144-239` | no — drive registration | n/a | none |
| maturity credit / zero-length segment | `emi.go:1614-1621,1749-1751` | yes | **no — refused by design** | none possible |
| re-adjust no-op | `emi.go:2279-2281` | yes | no — arithmetically unreachable | none possible |
| `divisor == 1` shortcut | `rounding.go:204` | yes | no — unreachable | none possible |
| zero-denominator rate factor | `emi.go:1971-1973` | yes | no — unreachable | none possible |
| paid-exceeds-due guard | `emi.go:2148-2153` | yes | no — provably inert | none possible |
| negative HALF_UP arm | `rounding.go:63-65` | yes | no — no negative money | none possible |
| M1 non-first membership | `emi.go:1529` | no — date predicate | **no** — reachable shape uncaptured | capture if a later-period advance is ever wanted |

**No candidate here is asserted to be a defect.** The loanschedule corpus is the strongest
of the measurable contexts so far: it reaches every reference money rule, and every
`0.0%` is either the wrong-drive corpus, its HALF_EVEN twin, a dead accessor, or a
branch the graded domain refuses. Across seven measured contexts this is the first with no
ungraded reference money rule at all.

## 7. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` issued; the push gate was never exercised.
* No vector and no drive was written. `.softhouse/vectors/loanschedule/` is unchanged (50
  files).
* No port code changed. `.softhouse/guards/` (12 pairs) and `.softhouse/conformance.sh`
  (census 17) are untouched.
* Outside the one committed control, no code was changed.
* No `0.0%` was treated as a defect; the refusal evidence, not the number, decided §5.

## 8. Controls

* `go build ./...` — clean.
* `go test ./...` — all 31 packages pass (exit 0).
* `bash .softhouse/conformance.sh` — **exit 2** with
  `§4.4.2-RECORDED-DECISION-EXIT` (`/tmp/ls_conf.log:1393`); the `loanschedule` graded run
  inside it is `VERDICT: PASS — 46 parity vectors match the pinned reference oracle, 7884
  cells compared`. This is the recorded decision, **not** a "HARD guard failed".
* New test: `go test -run
  '^TestCommittedCorpusPassesTheReferenceImplementation$'` passes on the current tree.
* `kills.sh loanschedule loanschedule-wrong-half-even <wt>` → **5**.
* `kills.sh loanschedule loanschedule-wrong-days-in-year-365 <wt>` → **45** (this binary
  rejects `-root`, so the tool, not the binary, is used).
* `kills.sh parties parties-wrong-iota-ordinals <wt>` → **12**.
* `redcount.sh <wt> loanschedule` → **8** registered wrong drives (non-empty listing).
* `capcount.sh <wt> loanschedule loanschedule-go` is **not usable for this binary**: it
  greps for `parity_fail=N`, which `loanschedule` never prints (its verdict is the
  `LOAN SCHEDULE N mismatch` line, `report.go:687`). It returns `UNUSABLE (exit 2)`. This
  is a tool/flag-shape mismatch, not a failing control; the kills controls above are the
  usable instruments.

## Appendix A — all 13 `loanschedule` functions at 0.0% from the graded corpus

```
emi.go:1823   calculatedDueInterestMinor      dead accessor
generator.go:123 invalid                       error constructor
rounding.go:163  minorFromMajorHalfEven        wrong-drive twin
rounding.go:171  roundHalfEvenToInt            wrong-drive twin
wrongdrives.go:122  Generate                   wrong-drive type
wrongdrives.go:144  NewWrongHalfEven           wrong-drive constructor
wrongdrives.go:162  NewWrongDaysInYear365      wrong-drive constructor
wrongdrives.go:177  NewWrongFrequencyUnitIgnored  wrong-drive constructor
wrongdrives.go:190  NewWrongRepaymentsFixedOne    wrong-drive constructor
wrongdrives.go:202  NewWrongRateZero           wrong-drive constructor
wrongdrives.go:214  NewWrongScheduleStartIgnored  wrong-drive constructor
wrongdrives.go:226  NewWrongDisbursementSeedIgnored   wrong-drive constructor
wrongdrives.go:239  NewWrongDisbursementAmountIgnored wrong-drive constructor
```

## Appendix B — reference money rules the corpus *does* reach

Measured from `/tmp/ls_vo.cov` (`file:line` are lines in the file):

| function | `file:line` | coverage |
|---|---|---:|
| `growthFactor` | `emi.go:1904` | 100.0% |
| `calculateRateFactors` | `emi.go:1918` | 100.0% |
| `periodRatio` | `emi.go:1995` | 100.0% |
| `periodRatioSeed` | `emi.go:2042` | 100.0% |
| `shouldBeAdjusted` | `emi.go:2231` | 100.0% |
| `dueInterestMinor` | `emi.go:1828` | 100.0% |
| `accumulatedInterestMinor` | `emi.go:1843` | 100.0% |
| `minorFromMajor` | `rounding.go:146` | 100.0% |
| `roundScale` | `rounding.go:74` | 100.0% |
| `roundSignificant` | `rounding.go:121` | 100.0% |
| `interestChainUpTo` | `emi.go:1788` | 95.0% |
| `segmentCalculatedInterest` | `emi.go:1747` | 87.5% |
| `rateFactorByRepaymentPeriod` | `emi.go:1970` | 87.5% |
| `calculateLevelInstallment` | `emi.go:2080` | 87.0% |
| `findLastUnpaidPeriod` | `emi.go:2186` | 85.7% |
| `emiAdjustment` | `emi.go:2209` | 85.7% |
| `adjustEMIIfNeeded` | `emi.go:2256` | 85.0% |
| `addDisbursement` | `emi.go:1582` | 80.0% |
| `applyFinalPeriodResidual` | `emi.go:2122` | 72.7% |
| `registerBalanceChange` | `emi.go:1607` | 69.2% |
| `minorFromMajorHalfEven` (wrong drive — not the reference) | `rounding.go:163` | 0.0% |

Total port statements: **682**, covered **535** (`78.4%`); 97 port functions, 13 at
`0.0%`. Every `0.0%` is classified in §4; every uncovered money branch is named in §5.
