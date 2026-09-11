# F-2026-09-11 — the `loanproduct` graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** The committed-store control was added and committed
(this is the run's one code change); no capture was taken, no `POST`/`PUT`/`DELETE` was
issued, and **no vector and no drive was written**. Grading the gap this triage names is a
later run's work.
**Task:** `OH-LPCOV-AL`, one bounded context `loanproduct`, branch `feat/OHLPCOVal`,
worktree `/Users/buv/oh-gerege-lpcov`.
**Companions:** `F-2026-09-11-loan-graded-coverage.md` (OPEN — this run does not resolve
it) and `F-2026-09-11-charges-graded-coverage.md` (RESOLVED by `OH-CHCAP-AF`); the §2
two-figure discipline and the §5 triage rule are copied from the charges one.

## 1. The missing control, added

`loanproduct` had no test that drove the committed corpus through the grading path, so
Go coverage measured from `conformance` measured only the hand-built probes and the
map recorded the committed-store test **ABSENT**. Added
`nexus/internal/apps/loanproduct/conformance/committed_store_test.go` (commit
`b2099129`, `test(loanproduct): add committed-store coverage control`), modelled on
`nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it drives the **real committed store** through `LoadStore` → `Admit` → `Run` against
  the reference `loanproduct-go`, exactly as the grading binary does;
* it **calls no port function directly** — `Run`/`Admit`/`LoadStore` are the conformance
  package's own functions and every port statement is reached *through the vectors*, so
  the coverage is real, not manufactured;
* anti-vacuity (P-35): it fails if `LoadStore` returns ZERO vectors or any load error;
* it also fails if the committed corpus loses every vector naming one of
  the six vocabularies, because the decode behind that vocabulary would then silently
  fall back to `0.0%`.

The committed corpus passes (read-only local run):

    go run ./internal/apps/loanproduct/conformance/cmd/conformance -root ..
    → VERDICT: PASS
      vectors_loaded=15 parity_pass=15 parity_fail=0 refused=0 inadmissible=0
      harness_error=0 graded_cells=45 invariant_violations=0
      nofloat: packages=48 files=385 tokens=402116 imports=1132 violations=0

`capcount.sh <worktree> loanproduct loanproduct-go` → **0** (the reference fails no vector).

## 2. Coverage — both figures, and which is honest

From `nexus/`, exactly the prescribed command plus the same command narrowed to the new
test, and the same command narrowed to everything *but* the new test:

| profile | command | statements | coverage | functions at `0.0%` |
|---|---|---:|---:|---:|
| package-wide (prescribed) | `go test -count=1 -coverpkg=./internal/apps/loanproduct -coverprofile=/tmp/c.cov ./internal/apps/loanproduct/conformance/...` | — | **8.5%** | **213** |
| committed-store-only | same, `-run '^TestCommittedCorpusPassesTheReferenceImplementation$'` | — | **8.5%** | **213** |
| probe-only (everything else) | same, all other `Test*` selected | — | **8.5%** | **213** |

All three `0.0%` sets are **byte-identical** (`go tool cover -func | awk '$3=="0.0%"'`,
sorted and diffed). 26 functions are non-zero: the six vocabularies'
`FromStoredValue`/`StoredValue`/`Code`/`String` (24) plus the two package `init()`
functions — i.e. exactly the enum-decode surface `conformance/doc.go:8-16` declares.

**Which figure is honest, and why they are equal here.** In the charges run the two
figures differed (package-wide 57.5%, committed-store-only 41.2%) because
`charges/conformance_test.go` calls port functions **directly**, manufacturing reach the
vectors never give; there the committed-store-only figure is the honest one. Here they
are equal: the pre-existing `loanproduct` probes do not call port functions directly,
they call `NewGoEvaluator().Evaluate` (`conformance/conformance_test.go:159,168,181,202,206,233,243`),
which goes through the same `decodeVocabulary` (`conformance/admit.go:159`) that the
vectors do. So both figures are honest and equal, and **8.5% is the honest number**; the
new control's contribution is not a higher percentage but that this 8.5% is now *proven*
to be reached by the committed corpus through `LoadStore`/`Admit`/`Run`, not merely
claimed by hand-built probes. (Had the probes reached anything the vectors did not, the
committed-store-only figure would be the honest one and the probes' extra reach would be
recorded as manufactured — that is the charges situation, not this one.)

## 3. Triage rule

A `0.0%` is a **candidate, not a gap**. For each candidate that implements a **money
rule** (not a getter, a `String()`, a status predicate, an error constructor) exactly one
question is asked:

> **Does an observation behind it already exist in a committed capture?**

If yes, name the capture and the figures a vector would take — that is a grading run the
driver can dispatch next. If no, say what a capture would need. **No candidate is
asserted to be a defect.** Evidence decides.

## 4. Corpus scope — why 213 functions read `0.0%`

The `loanproduct` graded corpus is the 15 vectors in `.softhouse/vectors/loanproduct/`.
Every one cites the single capture `.softhouse/capture/loanproduct/out/loanproducts-template-raw.json`
(sha256 `6168b177ec87a259015aa5a2cd8eb93a838de571765a0a3d16a66a6683c523fe`;
`PIN-loanproduct.json` pins commit `426a23544` under tenant `gerege`, so this is the
current instance, not an earlier one).

The seam can only ask one question. `Request` carries **only** `{Vocabulary string;
Stored int32}` (`conformance/vector.go:112-115`); `goEvaluator.Evaluate` calls only
`decodeVocabulary` (`conformance/impl.go:95-101`); `decodeVocabulary` switches over the
**six enum vocabularies** and calls only their `FromStoredValue`/`StoredValue`/`Code`/`String`
(`conformance/admit.go:159-199`). Nothing else in the package is addressable by a vector.
`conformance/doc.go:28-34` states the scope explicitly:

> The loan schedule, interest/repayment-period arithmetic and every money rounding
> surface the schedule produces live in `loanschedule`, not here. … there is no
> minor-unit money cell to pin and no HALF_UP/HALF_EVEN tie; the MANIFEST records
> `"roundingSurface": "none"`.

The two product-detail captures (`loanproduct/out/loanproduct-1-raw.json`,
`loanproduct-2-raw.json`) exist but are cited by **no vector**.

## 5. Triage of the `0.0%` inventory (213 functions)

Inventory by file (full `file:line` list in Appendix A):

| file | `0.0%` functions | class |
|---|---:|---|
| `repaymentperiod.go` | 62 | schedule/EMI money rules + accessors/mutators |
| `schedulemodel.go` | 41 | schedule recomputation/insertion/totals + accessors |
| `interestperiod.go` | 32 | interest-period money rules + accessors/mutators |
| `calculator.go` | 23 | rate-factor recomputation kernel |
| `money.go` | 22 | rounding + integer-money kernel |
| `dates.go` | 15 | calendar kernel |
| `frequency.go` | 6 | enum `Is*` predicates |
| `method.go` | 6 | enum `Is*` predicates |
| `relateddetail.go` | 5 | value-object accessors/mutations |
| `interestrate.go` | 1 | rate `compare` |

### 5.1 The progressive-recomputation kernel — money rules, but the seam cannot reach them and no loanproduct observation exists

This is the entire `calculator.go`/`money.go`/`dates.go`/`interestperiod.go`/
`interestrate.go`/`repaymentperiod.go`/`schedulemodel.go` money arithmetic — the port of
Fineract's progressive EMI / rate-factor recomputation (introduced by `6d43d2f3`,
"port progressive schedule recomputation arithmetic"). It is unquestionably money-rule
code, but it is **not reachable through this context**, on four independent pieces of
evidence:

1. **The seam is enum-only.** §4: `Request` cannot carry a schedule input, and
   `decodeVocabulary` (`conformance/admit.go:159-199`) calls none of these functions.
2. **The port package is unwired.** `grep '"github.com/gerege/nexus/internal/apps/loanproduct"'`
   over the whole module returns only `loanproduct/conformance/admit.go:10` and
   `loanproduct/conformance/impl.go:9` — its own conformance package. **No application
   imports the `loanproduct` port**; its schedule arithmetic is dead relative to the
   running product. No `loanproduct.CalculateRateFactor*`, `loanproduct.CalculateOutstandingBalance`
   or `loanproduct.NewScheduleModel` reference exists outside the package.
3. **Ownership is elsewhere.** `conformance/doc.go:18-20,29-30` and
   `capture/loanproduct/MANIFEST.json` defer this arithmetic to `loanschedule` under
   DEC-1; `PIN-loanproduct.json` and `MANIFEST.json` stamp the same decision.
4. **The observation that does exist belongs to `loanschedule`.** The committed tree
   *does* carry in-process Path-A observations of exactly this arithmetic at the pinned
   commit — `capture/periodratio/out/t39-*.json` (the `rateFactorTillPeriodDueDate`
   = periodRatio question), `capture/actualactual/out/t48-*.json`,
   `capture/dec1-binding/out/t37-binding*.json`, `capture/out/capture-prod3d-raw.json`
   — and `loanschedule` already has **50 vectors** whose `P-DRIFT-*`/`P-LAT-*` cases
   transcribe that same pass-3e/3d schedule output. `loanschedule` is the DEC-1 owner
   and the place those cells are graded.

*Verdict.* **Observed, but out of the `loanproduct` context and owned by `loanschedule`.**
These `0.0%` are an artefact of a duplicate, unwired port, not an ungraded `loanproduct`
rule. A `loanproduct` capture would not help: the blocker is the enum-only `Request`
schema, and grading the arithmetic here would duplicate `loanschedule`'s DEC-1 ownership
(manufactured coverage of a second copy). **Not a defect and not a grading run** — a
scope/ownership decision (drop/relocate the duplicate, or keep it as a private reference
that coverage accounting excludes).

### 5.2 `relateddetail.go` — value-object accessors/mutations; observations exist for 3 of 5 but the schema cannot carry them

`conformance/doc.go:10-12` does include the `LoanProductRelatedDetail` value object in
this context, so these five are the only in-domain `0.0%`. They are not money rules in
the triage sense (accessors/mutations over a carried value object), but the observation
question still has an answer:

* `relateddetail.go:111` `AnnualNominalInterestRateMajor` — **observation exists.**
  `capture/loanproduct/out/loanproduct-1-raw.json` carries `annualInterestRate 21.6`
  (scale-6 → `21_600_000` → rational `108/5`); `loanproduct-2-raw.json` carries `12.0`
  (→ `12_000_000` → `12`). **But** `doc.go:32-34` and `MANIFEST.json` defer the
  annual-nominal-rate derivation to `loanschedule` under DEC-1, so grading it here would
  duplicate the owner; and the enum-only `Request` cannot carry the figure.
* `relateddetail.go:120` `GetInterestPeriodFrequencyType` — identity accessor; both
  product captures carry `interestRateFrequencyType {id:3, years}` / `{id:2, months}`.
* `relateddetail.go:129` `GetDaysInYearType` — both product captures carry only
  `daysInYearType {id:1, ACTUAL}`; the invalid-fallback arm has no product observation.
* `relateddetail.go:141` `ResetToInvalid` — a **mutation** performed during product
  update (`clearLoanProductRelatedDetails`); no committed capture observes the pre/post
  state (the raw detail read-back is post-assembly). Needs an update round-trip capture.
* `relateddetail.go:23` `IsFeb29PeriodOnly` — a status predicate; the template enumerates
  `daysInYearCustomStrategyOptions` but no captured product uses `FEB_29_PERIOD_ONLY`.

*Verdict.* Observations exist for the three carried getters, but **no vector can carry
them without extending `Request`**, and the rate derivation is DEC-1-owned; the mutation
and the predicate need a capture. **No defect.**

### 5.3 `frequency.go` / `method.go` — enum predicates, outside the filter

`frequency.go:89,90,91,92,168,232` (`IsMonthly/IsYearly/IsWeekly/IsDaily/IsActual/IsDaysInMonth30`)
and `method.go:72,73,136,137,202,203`
(`IsDecliningBalance/IsFlat/IsEqualInstallment/IsEqualPrincipal/IsDaily/IsSameAsRepaymentPeriod`)
are status predicates. The decoders themselves
(`PeriodFrequencyTypeFromStoredValue`, etc.) are reached and non-zero; no seam calls the
predicates, so their `0.0%` is by construction, not a gap. **Outside the triage filter.**

## 6. Beyond the `0.0%` filter — the one reachable, observed, ungraded surface

Coverage cannot see this, and that is the point. `PeriodFrequencyType` has five stored
members (`frequency.go:32-37`), but the 15 vectors request only **stored 2 (MONTHS)**,
**3 (YEARS)** and **4 (WHOLE_TERM)**. Stored **0 (DAYS)** and **1 (WEEKS)** are *never
requested* — yet both are **observed in the very same capture every period-frequency
vector cites**:

    loanproducts-template-raw.json  repaymentFrequencyTypeOptions
      id 0  code repaymentFrequency.periodFrequencyType.days   value Days
      id 1  code repaymentFrequency.periodFrequencyType.weeks  value Weeks
    (capture_sha256 6168b177ec87a259015aa5a2cd8eb93a838de571765a0a3d16a66a6683c523fe)

The port's own tables already carry both (`frequency.go:32-33` stored, `:41-42` code,
`:50-51` name), and the template option list is the current-instance observation pinned by
`PIN-loanproduct.json` (tenant `gerege`, commit `426a23544`). This is **implemented,
observed, ungraded** — holds-shaped, and gradeable without a new capture. Two vectors, a
near-copy of `LP-freq-months.json`, would take both decode branches:

| vector | `request.vocabulary` | `request.stored` | `expect.stored` | `expect.code` | `expect.name` |
|---|---|---:|---:|---|---|
| `LP-freq-days` | `period-frequency` | `0` | `0` | `periodFrequencyType.days` | `DAYS` |
| `LP-freq-weeks` | `period-frequency` | `1` | `1` | `periodFrequencyType.weeks` | `WEEKS` |

with `capabilities_required: ["period-frequency"]`, `provenance.capture_ref` =
`.softhouse/capture/loanproduct/out/loanproducts-template-raw.json`, the sha above, and a
citation of `repaymentFrequencyTypeOptions id 0/1 → PeriodFrequencyType.java getCode()`.

*Why coverage missed it.* The decoder has no per-member branch: `StoredValue`/`Code`/`String`
execute the same statements whether the request is `DAYS`, `MONTHS` or `WEEKS`. Their
`75.0%`/`100%`/`66.7%` readings are the panic/default arms (never taken), **not** member
coverage. So a coverage-only audit cannot find this; it was found by diffing the vectors'
`stored` values against the capture's option list. That method is the transferable result
of this run: **enumerate observed option ids, then enumerate graded stored values, and
diff** — for this context a vocabulary is only "graded" when every observed member is
requested, and the committed-store test's capability guard (§1) only checks the
vocabulary, not each member.

*Verdict.* This is the one grading run the driver can dispatch next; no capture needed.
It is an enum decode, not a money rule, so it sits outside §5's filter — reported here
because it is what the corpus actually never reaches.

## 7. Summary of triage

| candidate | `file:line` | money rule? | observation in corpus? | action |
|---|---|---|---|---|
| progressive recomputation kernel | `calculator.go` (23), `money.go` (22), `dates.go` (15), `interestperiod.go` (32), `interestrate.go:22`, `repaymentperiod.go` (62), `schedulemodel.go` (41) — Appendix A | **yes** | **yes, but `loanschedule`'s** (`t39-*`, `t48-*`, `t37-binding*`, `capture-prod3d-raw`; 50 loanschedule vectors) | **out of context** — DEC-1 owner is `loanschedule`; duplicate/unwired port |
| `AnnualNominalInterestRateMajor` | `relateddetail.go:111` | rate derivation | yes (`loanproduct-1-raw` 21.6, `loanproduct-2-raw` 12.0) | schema can't carry it; DEC-1-owned → not this corpus |
| `GetInterestPeriodFrequencyType` | `relateddetail.go:120` | no (accessor) | yes (both product captures, freq id 3/2) | needs `Request` extension |
| `GetDaysInYearType` | `relateddetail.go:129` | no (accessor) | partial (ACTUAL only) | needs a capture for the invalid arm |
| `ResetToInvalid` | `relateddetail.go:141` | no (mutation) | no | needs an update round-trip capture |
| `IsFeb29PeriodOnly` | `relateddetail.go:23` | no (predicate) | no | needs a `FEB_29_PERIOD_ONLY` capture |
| enum `Is*` predicates | `frequency.go:89-92,168,232`; `method.go:72-73,136-137,202-203` | no | n/a | out of scope |
| **period-frequency DAYS/WEEKS** | `frequency.go:32-33` (data), seam `admit.go:179` | no (enum decode) | **yes** — `loanproducts-template-raw.json` ids 0/1 | **grade now** (§6) |
| 213 functions at `0.0%` | Appendix A | mixed | see above | — |

**No candidate is asserted to be a defect.** The only dispatchable grading run this
measurement produces is §6; the large money-rule `0.0%` block is a duplicate, unwired
port whose arithmetic is owned and graded by `loanschedule` under DEC-1.

## 8. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` was issued; the oracle was not exercised.
* No vector and no drive was written; `.softhouse/vectors/loanproduct/` is unchanged.
* No port code changed; the only change is the added `committed_store_test.go` (§1).
* `.softhouse/guards/` and `.softhouse/conformance.sh` (census 17) are untouched.
* `F-2026-09-11-loan-graded-coverage` remains OPEN (triage only); this run neither
  resolves it nor touches its subject context.

## 9. Controls

* `go build ./...` — clean.
* `go test -count=1 ./...` — all packages pass; the new test passes `-count=1`.
* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit line is
  `conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded
  run completed and the bar is refused by that recorded decision`. No `HARD guard failed`.
  Census wrong ledger implementations = 17.
* `kills.sh loanproduct loanproduct-wrong-dim-sibling-name <worktree>` → **1** (as before).
* `kills.sh loanschedule loanschedule-wrong-days-in-year-365 <worktree>` → **45**.
* `kills.sh parties parties-wrong-iota-ordinals <worktree>` → **12**.
* `redcount.sh <worktree> loanproduct` → **4** (all 4 `loanproduct-wrong-*` drives kill).
* `capcount.sh <worktree> loanproduct loanproduct-go` → **0**.
* `loanproduct-go` on the committed store: `vectors_loaded=15 parity_pass=15 parity_fail=0`.

## Appendix A — all 213 functions at `0.0%` in the prescribed run

`file:line` are lines in each file; the same set at the committed-store-only and
probe-only profiles.
- `calculator.go:110` `calculateRateFactorPerPeriod`
- `calculator.go:159` `calculateRateFactorPerPeriodForInterest`
- `calculator.go:205` `calculateRateFactorPerPeriodBasedOnRepaymentFrequency`
- `calculator.go:219` `rateFactorByRepaymentEveryDay`
- `calculator.go:224` `rateFactorByRepaymentEveryWeek`
- `calculator.go:229` `rateFactorByRepaymentEveryMonth`
- `calculator.go:243` `rateFactorByRepaymentPeriod`
- `calculator.go:25` `ratInt64`
- `calculator.go:26` `ratOne`
- `calculator.go:261` `rateFactorByRepaymentPartialPeriod`
- `calculator.go:277` `calculatePeriodFractions`
- `calculator.go:302` `getFractionPeriodDueDateForEndOfYear`
- `calculator.go:31` `calcNominalInterestRatePercentage`
- `calculator.go:311` `calculateSeedDate`
- `calculator.go:333` `calculatePeriodRatio`
- `calculator.go:37` `CalculateRateFactorForPeriods`
- `calculator.go:375` `plusPeriods`
- `calculator.go:45` `CalculateRateFactorForRepaymentPeriod`
- `calculator.go:54` `CalculateOutstandingBalance`
- `calculator.go:65` `daysInYearNumberOfDays`
- `calculator.go:75` `isPeriodContainsFeb29`
- `calculator.go:89` `numberOfDaysFeb29PeriodOnly`
- `calculator.go:99` `getNumberOfDays`
- `dates.go:106` `isDateInRangeInclusive`
- `dates.go:114` `isDateInRangeFromExclusiveToInclusive`
- `dates.go:122` `isInPeriod`
- `dates.go:13` `isLeapYear`
- `dates.go:132` `exactDifferenceInDays`
- `dates.go:141` `exactDifference`
- `dates.go:15` `daysInMonthOf`
- `dates.go:32` `lengthOfYear`
- `dates.go:41` `compareDates`
- `dates.go:54` `plusDays`
- `dates.go:60` `plusMonths`
- `dates.go:74` `floorDivInt`
- `dates.go:82` `floorModInt`
- `dates.go:88` `monthsBetween`
- `dates.go:99` `isAfterInclusive`
- `frequency.go:168` `IsActual`
- `frequency.go:232` `IsDaysInMonth30`
- `frequency.go:89` `IsMonthly`
- `frequency.go:90` `IsYearly`
- `frequency.go:91` `IsWeekly`
- `frequency.go:92` `IsDaily`
- `interestperiod.go:119` `daysBetween`
- `interestperiod.go:125` `dateOnly`
- `interestperiod.go:212` `zero`
- `interestperiod.go:222` `CreditedPrincipal`
- `interestperiod.go:226` `CreditedInterest`
- `interestperiod.go:230` `DisbursementAmount`
- `interestperiod.go:234` `BalanceCorrectionAmount`
- `interestperiod.go:238` `OutstandingLoanBalance`
- `interestperiod.go:242` `CapitalizedIncomePrincipal`
- `interestperiod.go:246` `RateFactorValue`
- `interestperiod.go:256` `RateFactorTillPeriodDueDateValue`
- `interestperiod.go:270` `Length`
- `interestperiod.go:278` `LengthTillPeriodDueDate`
- `interestperiod.go:284` `IsFirstInterestPeriod`
- `interestperiod.go:293` `CalculatedDueInterest`
- `interestperiod.go:314` `CalculatedDueInterestFor`
- `interestperiod.go:342` `ratNegativeToZero`
- `interestperiod.go:425` `UpdateOutstandingLoanBalance`
- `interestperiod.go:453` `CreditedAmounts`
- `interestperiod.go:548` `AddBalanceCorrectionAmount`
- `interestperiod.go:554` `AddDisbursementAmount`
- `interestperiod.go:560` `AddCreditedPrincipalAmount`
- `interestperiod.go:566` `AddCreditedInterestAmount`
- `interestperiod.go:574` `AddCapitalizedIncomePrincipalAmount`
- `interestperiod.go:580` `IsPaused`
- `interestperiod.go:585` `SetDueDate`
- `interestperiod.go:589` `SetPaused`
- `interestperiod.go:593` `SetRateFactor`
- `interestperiod.go:598` `SetRateFactorTillPeriodDueDate`
- `interestperiod.go:604` `copy`
- `interestperiod.go:630` `withEmptyInterestPeriod`
- `interestperiod.go:650` `ratCopy`
- `interestrate.go:22` `compare`
- `method.go:136` `IsEqualInstallment`
- `method.go:137` `IsEqualPrincipal`
- `method.go:202` `IsDaily`
- `method.go:203` `IsSameAsRepaymentPeriod`
- `method.go:72` `IsDecliningBalance`
- `method.go:73` `IsFlat`
- `money.go:111` `decimalExponent`
- `money.go:122` `compareAgainstPow10`
- `money.go:134` `roundSignificant`
- `money.go:162` `moneyOf`
- `money.go:168` `moneyZero`
- `money.go:175` `NewMoney`
- `money.go:181` `major`
- `money.go:187` `Minor`
- `money.go:195` `IsZero`
- `money.go:197` `plus`
- `money.go:202` `minus`
- `money.go:207` `negToZero`
- `money.go:214` `compare`
- `money.go:219` `isGreaterThan`
- `money.go:220` `isLessThan`
- `money.go:221` `isEqualTo`
- `money.go:223` `checkCurrency`
- `money.go:232` `moneyMin`
- `money.go:239` `moneyMax`
- `money.go:54` `pow10`
- `money.go:64` `roundToInt`
- `money.go:95` `roundScale`
- `relateddetail.go:111` `AnnualNominalInterestRateMajor`
- `relateddetail.go:120` `GetInterestPeriodFrequencyType`
- `relateddetail.go:129` `GetDaysInYearType`
- `relateddetail.go:141` `ResetToInvalid`
- `relateddetail.go:23` `IsFeb29PeriodOnly`
- `repaymentperiod.go:106` `Previous`
- `repaymentperiod.go:109` `Zero`
- `repaymentperiod.go:113` `Currency`
- `repaymentperiod.go:116` `InterestMethod`
- `repaymentperiod.go:119` `Emi`
- `repaymentperiod.go:123` `OriginalEmi`
- `repaymentperiod.go:126` `PaidPrincipal`
- `repaymentperiod.go:129` `PaidInterest`
- `repaymentperiod.go:133` `FutureUnrecognizedInterest`
- `repaymentperiod.go:136` `TotalDisbursedAmount`
- `repaymentperiod.go:140` `TotalCapitalizedIncomeAmount`
- `repaymentperiod.go:143` `FixedInterest`
- `repaymentperiod.go:146` `CreditedPrincipalMovedDueReAge`
- `repaymentperiod.go:151` `CreditedInterestMovedDueReAge`
- `repaymentperiod.go:156` `FirstInterestPeriod`
- `repaymentperiod.go:161` `LastInterestPeriod`
- `repaymentperiod.go:166` `interestPeriodIndex`
- `repaymentperiod.go:180` `RateFactorPlus1`
- `repaymentperiod.go:190` `CalculatedDueInterest`
- `repaymentperiod.go:199` `CalculateCalculatedDueInterest`
- `repaymentperiod.go:218` `CalculateFixedInterestTillDate`
- `repaymentperiod.go:241` `DueInterest`
- `repaymentperiod.go:257` `EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest`
- `repaymentperiod.go:263` `CalculatedDuePrincipal`
- `repaymentperiod.go:270` `CreditedPrincipal`
- `repaymentperiod.go:280` `CreditedInterest`
- `repaymentperiod.go:290` `CapitalizedIncomePrincipal`
- `repaymentperiod.go:300` `DuePrincipal`
- `repaymentperiod.go:308` `TotalCreditedAmount`
- `repaymentperiod.go:317` `TotalPaidAmount`
- `repaymentperiod.go:323` `IsFullyPaid`
- `repaymentperiod.go:329` `UnrecognizedInterest`
- `repaymentperiod.go:335` `CreditedAmounts`
- `repaymentperiod.go:346` `OutstandingLoanBalance`
- `repaymentperiod.go:358` `AddPaidPrincipalAmount`
- `repaymentperiod.go:364` `AddPaidInterestAmount`
- `repaymentperiod.go:371` `InitialBalanceForEmiRecalculation`
- `repaymentperiod.go:389` `OutstandingInterest`
- `repaymentperiod.go:395` `OutstandingPrincipal`
- `repaymentperiod.go:401` `ResetDerivedComponents`
- `repaymentperiod.go:410` `calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod`
- `repaymentperiod.go:426` `MoveOutstandingDueToReAging`
- `repaymentperiod.go:433` `IsFirstRepaymentPeriod`
- `repaymentperiod.go:560` `FindInterestPeriod`
- `repaymentperiod.go:570` `SetEmi`
- `repaymentperiod.go:573` `SetOriginalEmi`
- `repaymentperiod.go:576` `SetFutureUnrecognizedInterest`
- `repaymentperiod.go:579` `SetFixedInterest`
- `repaymentperiod.go:582` `SetTotalDisbursedAmount`
- `repaymentperiod.go:585` `SetTotalCapitalizedIncomeAmount`
- `repaymentperiod.go:590` `SetCreditedPrincipalMovedDueReAge`
- `repaymentperiod.go:595` `SetCreditedInterestMovedDueReAge`
- `repaymentperiod.go:60` `NewRepaymentPeriod`
- `repaymentperiod.go:600` `SetInterestMovedUpward`
- `repaymentperiod.go:603` `SetInterestMovedDownward`
- `repaymentperiod.go:606` `SetInterestPaymentGrace`
- `repaymentperiod.go:609` `SetReAged`
- `repaymentperiod.go:612` `SetReAgedEarlyRepaymentHolder`
- `repaymentperiod.go:615` `SetCurrency`
- `repaymentperiod.go:620` `copy`
- `repaymentperiod.go:655` `copyWithoutPaidAmounts`
- `repaymentperiod.go:88` `NewInterestPeriod`
- `schedulemodel.go:105` `FindRepaymentPeriodByFromAndDueDate`
- `schedulemodel.go:125` `GetRelatedRepaymentPeriods`
- `schedulemodel.go:141` `LoanTermInDays`
- `schedulemodel.go:155` `StartDate`
- `schedulemodel.go:164` `MaturityDate`
- `schedulemodel.go:175` `ChangeOutstandingBalanceAndUpdateInterestPeriods`
- `schedulemodel.go:189` `UpdateInterestPeriodsForInterestPause`
- `schedulemodel.go:211` `findRepaymentPeriodForBalanceChange`
- `schedulemodel.go:227` `updateInterestPeriodOnRepaymentPeriod`
- `schedulemodel.go:247` `findInterestPeriodForBalanceChange`
- `schedulemodel.go:269` `insertInterestPeriod`
- `schedulemodel.go:291` `insertInterestPausePeriods`
- `schedulemodel.go:307` `insertInterestPausePeriodsByAdjustedDates`
- `schedulemodel.go:321` `hasSegmentWithFromDate`
- `schedulemodel.go:330` `hasSegmentWithDueDate`
- `schedulemodel.go:342` `findPreviousInterestPeriod`
- `schedulemodel.go:357` `calculateNewDueDate`
- `schedulemodel.go:371` `TotalDueInterest`
- `schedulemodel.go:381` `TotalDuePrincipal`
- `schedulemodel.go:391` `TotalPaidInterest`
- `schedulemodel.go:40` `NewScheduleModel`
- `schedulemodel.go:401` `TotalPaidPrincipal`
- `schedulemodel.go:411` `TotalCreditedPrincipal`
- `schedulemodel.go:421` `TotalOutstandingPrincipal`
- `schedulemodel.go:429` `FindRepaymentPeriod`
- `schedulemodel.go:440` `IsEmpty`
- `schedulemodel.go:451` `LastRepaymentPeriod`
- `schedulemodel.go:457` `IsLastRepaymentPeriod`
- `schedulemodel.go:465` `DeepCopy`
- `schedulemodel.go:471` `CopyWithoutPaidAmounts`
- `schedulemodel.go:475` `copy`
- `schedulemodel.go:503` `DisableEMIRecalculation`
- `schedulemodel.go:506` `IsEMIRecalculationEnabled`
- `schedulemodel.go:509` `IsCopy`
- `schedulemodel.go:56` `RepaymentPeriods`
- `schedulemodel.go:59` `Rounding`
- `schedulemodel.go:62` `Currency`
- `schedulemodel.go:65` `Detail`
- `schedulemodel.go:68` `Zero`
- `schedulemodel.go:74` `GetInterestRate`
- `schedulemodel.go:89` `AddInterestRate`
