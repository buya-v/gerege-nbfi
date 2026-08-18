# Tier 0 — Golden-Vector Capture Plan (Progressive Loan Schedule Generation)

**Task:** T16. **Purpose:** hand the scheduled capture fire — which runs on a machine that *can* reach a live
reference oracle (Fineract) + PostgreSQL — an executable plan, so it never has to re-do this corpus analysis.

**Pinned checkout.** `/home/user/fineract` at `426a23544e8426a38ae43ae404670a0a7e85b9eb`
`[VERIFIED: cat /home/user/fineract/.git/HEAD → 426a23544e8426a38ae43ae404670a0a7e85b9eb]`

**Seam.** `fineract-progressive-loan-embeddable-schedule-generator/**` and `fineract-progressive-loan/**`,
restricted to schedule generation. Anything else is in the Backlog and was not chased.

**Companion document.** `docs/analysis/progressive-schedule-behavior.md` covers the *arithmetic* of this seam.
This document does not re-derive it and deliberately contains **no derived arithmetic** at all.

---

## 0. The rule this document is written under

> **A golden vector is only valid when it is observed from the reference oracle.**

Two — and only two — kinds of numeric content appear below:

| Label | Meaning | Trust |
|---|---|---|
| `TRANSCRIBED` | A literal that a Fineract source file already asserts, copied with `file:line`. | Usable as a vector **only after** the calibration run in §4.0 confirms the harness reproduces it. |
| `TO_BE_CAPTURED` | Not present in the source. A run against the oracle must produce it. | No number is stated. |

Nothing here was computed, extrapolated, interpolated or inferred. Where a behaviour has no literal in the
corpus, this document says so and stops — it does not supply a plausible number. The one arithmetic operation
performed is an **exact scale-2 reinterpretation of a decimal literal into integer minor units** (§5), which
adds no information and can be checked by eye.

**Instruction to the capture fire:** when you transcribe a row, open the cited line and copy it mechanically.
Do not retype a value you believe you remember. A single wrong digit here poisons every parity claim built on it.

---

## 1. Corpus inventory

### 1.1 Measured size

```
find fineract-progressive-loan/src/main -name '*.java' | wc -l          →   81
find fineract-progressive-loan/src/main -name '*.java' | xargs wc -l    → 14308 total
find fineract-progressive-loan/src/test -name '*.java' | wc -l          →   13
find fineract-progressive-loan/src/test -name '*.java' | xargs wc -l    →  7863 total
```
`[VERIFIED: commands above run in /home/user/fineract during this session]`

The "~7,863 test LOC in `fineract-progressive-loan`" figure on record is **confirmed exactly**: 7863.
`[VERIFIED: find /home/user/fineract/fineract-progressive-loan/src/test -name '*.java' | xargs wc -l → 7863 total]`

The embeddable module is **92 main LOC** (`src/main/java/.../EmbeddableProgressiveLoanScheduleGenerator.java`)
plus **90 LOC** of sample driver (`misc/Main.java`) plus **123 test LOC**, across exactly 6 files.
`[VERIFIED: find /home/user/fineract/fineract-progressive-loan-embeddable-schedule-generator -type f → 6 files; wc -l on the three .java files → 92, 90, 123]`

**The Tier-0 "~182 LOC" figure reconciles exactly — no discrepancy exists.** The module's *non-test* Java is
`92` (`src/main`) + `90` (`misc/Main.java`) = **182** lines, which is precisely the figure
`.softhouse/program.json` records for this context as `"main_loc": 182`. An earlier draft of this document
compared `182` only against the 92-line main file and the 215-line main+test total, omitted `misc/Main.java`
from the arithmetic, and floated a coincidence with `plan.getLoanTermInDays() == 182`. That coincidence is a
red herring and is **struck**; the figure is settled.
`[VERIFIED: wc -l /home/user/fineract/fineract-progressive-loan-embeddable-schedule-generator/misc/Main.java → 90; …/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java → 92; 92 + 90 = 182, and these are the only two non-test .java files in the module]`
`[VERIFIED: .softhouse/program.json — the Tier-0 context whose fineract_paths is ["fineract-progressive-loan-embeddable-schedule-generator"] carries "main_loc": 182]`

### 1.2 Test classes in scope

`M` = minable here (unit test, inline literal expectations, no server). `N` = not minable here.

| # | Path (relative to `/home/user/fineract`) | LOC | Kind | Covers | Minable |
|---|---|---:|---|---|---|
| 1 | `fineract-progressive-loan-embeddable-schedule-generator/src/test/java/.../EmbeddableProgressiveLoanScheduleGeneratorTest.java` | 123 | unit | End-to-end schedule plan through the public embeddable entry point; 1 test, fully pinned inputs, full literal schedule | **M** |
| 2 | `fineract-progressive-loan/src/test/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/LoanScheduleGeneratorTest.java` | 171 | unit | `ProgressiveLoanScheduleGenerator.generate` incl. real `DefaultScheduledDateGenerator` date derivation; 2 tests (plain, down-payment), full literal schedules | **M** |
| 3 | `fineract-progressive-loan/src/test/java/org/apache/fineract/portfolio/loanproduct/calc/ProgressiveEMICalculatorTest.java` | 5414 | unit | The EMI/interest engine. 110 `@Test`, 8 `@Nested` groups, 898 `checkPeriod` rows + 94 `checkDailyInterest` rows + 7 `checkEmi`/`checkTotalInterestDue` rows | **M** |
| 4 | `.../loanproduct/calc/data/RepaymentPeriodTest.java` | 141 | unit | Null-safety/structural getters on `RepaymentPeriod`; no golden schedule values | M (no vectors) |
| 5 | `.../loanproduct/calc/data/InterestPeriodTest.java` | 143 | unit | `InterestPeriod` data class | M (not inspected in depth — see UNVERIFIED count) |
| 6 | `.../transactionprocessor/impl/AdvancedPaymentScheduleTransactionProcessorTest.java` | 790 | unit | Payment **allocation/reprocessing**, not schedule generation | out of seam → Backlog |
| 7 | `.../transactionprocessor/impl/ChangeOperationTest.java` | 165 | unit | Change-operation ordering | out of seam → Backlog |
| 8 | `.../loanproduct/domain/AdvancedPaymentAllocationsJsonParserTest.java` | 234 | unit | JSON parsing | out of seam |
| 9 | `.../loanproduct/domain/AdvancedPaymentAllocationsValidatorTest.java` | 231 | unit | Validation | out of seam |
| 10 | `.../loanproduct/domain/CreditAllocationsValidatorTest.java` | 132 | unit | Validation | out of seam |
| 11 | `.../loanproduct/domain/CreditAllocationsJsonParserTest.java` | 122 | unit | JSON parsing | out of seam |
| 12 | `.../loanproduct/service/LoanProductPaymentAllocationRuleMergerTest.java` | 136 | unit | Rule merging | out of seam |
| 13 | `.../loanproduct/service/LoanProductCreditAllocationRuleMergerTest.java` | 106 | unit | Rule merging | out of seam |
| 14 | `.../rescheduleloan/data/ProgressiveLoanRescheduleRequestDataValidatorTest.java` | 78 | unit | Validation | out of seam |

`[VERIFIED: find /home/user/fineract/fineract-progressive-loan/src/test -name '*.java' | xargs wc -l | sort -rn — all 13 files and LOC]`
`[VERIFIED: grep -c "@Test" .../ProgressiveEMICalculatorTest.java → 110; grep -c "checkPeriod(interestSchedule\|checkPeriod(interestModel" → 898; grep -c "checkDailyInterest(" → 94; grep -c "checkEmi(\|checkTotalInterestDue(" → 7]`
`[VERIFIED: grep -n "@Nested" .../ProgressiveEMICalculatorTest.java → 8 occurrences at lines 2501, 2976, 3409, 3602, 3972, 4161, 4380, 5099]`

**There are no test fixture resources in either module** — every expectation is a Java literal.
`[VERIFIED: find <both modules>/src/test -not -name '*.java' -type f → empty]`

### 1.3 Integration tests — NOT minable here

Nine integration-test classes matching `Progressive` live in `integration-tests/src/test/java/org/apache/fineract/integrationtests/`
(e.g. `ProgressiveLoanTrancheTest.java`, `ProgressiveLoanMoratoriumIntegrationTest.java`,
`AdvancedPaymentAllocationLoanRepaymentScheduleTest.java`).
`[VERIFIED: ls integration-tests/src/test/java/org/apache/fineract/integrationtests/ | grep -ic "progressive" → 9]`

These drive the REST API against a running server + PostgreSQL. They are **out of reach from this sandbox** and
are listed only so the capture fire knows they exist; they are a *second-wave* source, after the unit seam.
`[UNVERIFIED: their internal assertion style — not opened, would exceed the seam]`

### 1.4 The critical structural finding for the capture fire

**The schedule-generation seam has a standalone, dependency-free Java entry point.** The embeddable module
builds a shadowJar bundling only `fineract-core`, `fineract-loan`, `fineract-progressive-loan`, with a documented
sample `Main.java` and a documented expected stdout.
`[VERIFIED: /home/user/fineract/fineract-progressive-loan-embeddable-schedule-generator/build.gradle:28-32 (the `requiredModuleNames` list — `fineract-core`, `fineract-loan`, `fineract-progressive-loan`) and README.md "There is no extra dependency."]`
`[VERIFIED: /home/user/fineract/fineract-progressive-loan-embeddable-schedule-generator/misc/Main.java:40-67]`

Consequence: **most Tier-0 capture does not require a running server or PostgreSQL** — only a JDK ≥ 17 and
`./gradlew :fineract-progressive-loan-embeddable-schedule-generator:shadowJar`. This is still the reference
oracle (it *is* Fineract code at the pinned commit), and it removes the largest source of capture-environment
variance. The full server is only needed for the API-shaped behaviours in §4.3.

Supporting evidence that the calculator is not coupled to ambient tenant state:
`grep -c "MoneyHelper" fineract-progressive-loan/src/main/java/.../calc/ProgressiveEMICalculator.java → 0`
`[VERIFIED: command above]` — i.e. the EMI engine takes its `MathContext` as a parameter rather than reading
the tenant-global one. See §2.4 for the caveat that keeps this from being a complete guarantee.

---

## 2. Directly-transcribable expectations

Notation: money is given as `<source literal> → <integer minor units>` (conversion defined in §5).
Rate factors and unrounded interest intermediates are **not money** and are kept as exact decimal strings.

### 2.1 V-01 — `EmbeddableProgressiveLoanScheduleGeneratorTest.testGenerate` — **THE CALIBRATION VECTOR**

File: `/home/user/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/test/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGeneratorTest.java`

**Inputs — every field of `LoanRepaymentScheduleModelData` is explicitly pinned in this test. Nothing is defaulted.**

| Parameter | Value | Line |
|---|---|---|
| `MathContext` | **precision 12, `RoundingMode.HALF_UP`** | 44 |
| `currency` | `CurrencyData("usd", "US Dollar", decimalPlaces=2, inMultiplesOf=null, "usd", "$")` | 47 |
| `scheduleGenerationStartDate` | `2024-01-01` | 48 |
| `disbursementDate` | `2024-01-01` | 49 |
| `disbursementAmount` | `100` → `10000` | 50 |
| `numberOfRepayments` | `6` | 52 |
| `repaymentFrequency` | `1` | 53 |
| `repaymentFrequencyType` | `"MONTHS"` | 54 |
| `downPaymentPercentage` | `BigDecimal.ZERO` → down payment disabled | 55–56 |
| `annualNominalInterestRate` | `7.0` | 57 |
| `daysInMonth` | `DaysInMonthType.DAYS_30` | 58 |
| `daysInYear` | `DaysInYearType.DAYS_360` | 59 |
| `installmentAmountInMultiplesOf` | `null` | 60 |
| `fixedLength` | `null` | 61 |
| `interestRecognitionOnDisbursementDate` | `false` | 62 |
| `daysInYearCustomStrategy` | `null` | 63 |
| `interestMethod` | `InterestMethod.DECLINING_BALANCE` | 64 |
| `allowPartialPeriodInterestCalculation` | `true` | 65 |
| `allowFullTermForTranche` | `false` (positional literal, last ctor arg) | 70 |

`[VERIFIED: all rows above, EmbeddableProgressiveLoanScheduleGeneratorTest.java:44-70]`
`[VERIFIED: CurrencyData positional argument order (code, name, decimalPlaces, inMultiplesOf, displaySymbol, nameCode) — /home/user/fineract/fineract-core/src/main/java/org/apache/fineract/organisation/monetary/data/CurrencyData.java:58-67]`
`[VERIFIED: LoanRepaymentScheduleModelData field order — /home/user/fineract/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/LoanRepaymentScheduleModelData.java:32-39 (the record header; the type declares 19 components ending in `allowFullTermForTranche`)]`

**TRANSCRIBED outputs.**

Plan-level (line 74–77):

| Field | Source literal | Minor units |
|---|---|---|
| `getLoanTermInDays()` | `182` | *(not money — days)* |
| `getTotalDisbursedAmount()` | `100.00` | `10000` |
| `getTotalInterestAmount()` | `2.05` | `205` |
| `getTotalRepaymentAmount()` | `102.05` | `10205` |
| `getPeriods().size()` | `7` | *(not money)* |

Period 0 is the disbursement period (line 80): from `2024-01-01`, due `2024-01-01`, principal `100.0` → `10000`,
outstanding `100.0` → `10000`.

Repayment periods (lines 81–92). Column order follows the `checkPeriod` overload at lines 100–102:
`(periodNumber, fromDate, dueDate, principal, interest, fee, penalty, totalDue, outstandingBalance, totalOutstandingBalance)`.

| # | from | due | principal | interest | fee | penalty | totalDue | outstanding | totalOutstanding | line |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 2024-01-01 | 2024-02-01 | `16.43`→`1643` | `0.58`→`58` | `0` | `0` | `17.01`→`1701` | `83.57`→`8357` | `85.04`→`8504` | 81–82 |
| 2 | 2024-02-01 | 2024-03-01 | `16.52`→`1652` | `0.49`→`49` | `0` | `0` | `17.01`→`1701` | `67.05`→`6705` | `68.03`→`6803` | 83–84 |
| 3 | 2024-03-01 | 2024-04-01 | `16.62`→`1662` | `0.39`→`39` | `0` | `0` | `17.01`→`1701` | `50.43`→`5043` | `51.02`→`5102` | 85–86 |
| 4 | 2024-04-01 | 2024-05-01 | `16.72`→`1672` | `0.29`→`29` | `0` | `0` | `17.01`→`1701` | `33.71`→`3371` | `34.01`→`3401` | 87–88 |
| 5 | 2024-05-01 | 2024-06-01 | `16.81`→`1681` | `0.20`→`20` | `0` | `0` | `17.01`→`1701` | `16.90`→`1690` | `17.00`→`1700` | 89–90 |
| 6 | 2024-06-01 | 2024-07-01 | `16.90`→`1690` | `0.10`→`10` | `0` | `0` | `17.00`→`1700` | `0.0`→`0` | `0.0`→`0` | 91–92 |

`[VERIFIED: EmbeddableProgressiveLoanScheduleGeneratorTest.java:74-92 and helper signature at :100-102]`

**Independent second attestation of the same outputs.** The module README documents the CI sample run's stdout
with the identical figures (`Total Interest Amount: 2.05`, per-period `16.43 / 0.58 / 17.01` … `16.90 / 0.10 / 17.00`).
`[VERIFIED: /home/user/fineract/fineract-progressive-loan-embeddable-schedule-generator/README.md — "This code has the following output" block]`
Two independent statements of the same expected output in the repository make V-01 the strongest anchor in the
corpus. **This is why it is the calibration vector.**

**Invariant check on the transcribed set** (a check, not a source of new numbers): the six principals sum to
`10000`; the six interests sum to `205`, matching the transcribed total; the six totals sum to `10205`, matching
the transcribed total. All three hold. Any transcription error would very likely break one of them, so the
capture harness should re-run these three checks after ingest.

### 2.2 V-02 — `LoanScheduleGeneratorTest.testGenerateLoanSchedule`

File: `/home/user/fineract/fineract-progressive-loan/src/test/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/LoanScheduleGeneratorTest.java`

**Why this one matters separately from V-01:** it constructs a real `DefaultScheduledDateGenerator` (line 70) and
has `scheduleGenerationStartDate` (`2024-01-01`) **differ** from `disbursementDate` (`2024-01-15`), so it pins
the mid-period-disbursement path as well as date derivation.

| Parameter | Value | Line |
|---|---|---|
| `MathContext` | **precision 12, `RoundingMode.HALF_EVEN`** | 57 |
| currency | `ApplicationCurrency("USD","USD",2,1,"USD","$").toData()` → decimalPlaces 2, inMultiplesOf 1 | 48–49 |
| `scheduleGenerationStartDate` | `2024-01-01` | 65 |
| `disbursementAmount` | `192.22` → `19222` | 50 |
| `disbursementDate` | `2024-01-15` | 56 |
| `numberOfRepayments` | `6` | 53 |
| `repaymentFrequency` / type | `1` / `"MONTHS"` | 54–55 |
| `annualNominalInterestRate` | `9.99` | 52 |
| downPaymentEnabled | `false` | 67 |
| `daysInMonth` / `daysInYear` | `DAYS_30` / `DAYS_360` | 67 |
| `downPaymentPercentage`, `installmentAmountInMultiplesOf`, `fixedLength` | `null, null, null` | 67 |
| `interestRecognitionOnDisbursementDate` | `false` | 67 |
| `daysInYearCustomStrategy` | `null` | 67 |
| `interestMethod` | `DECLINING_BALANCE` | 68 |
| `allowPartialPeriodInterestCalculation` / `allowFullTermForTranche` | `true` / `false` | 68 |

`[VERIFIED: LoanScheduleGeneratorTest.java:47-68]`

**TRANSCRIBED outputs.** `getPeriods().size() == 7` (line 77). Disbursement period: date `2024-01-15`,
principal `192.22`→`19222`, outstanding `192.22`→`19222` (lines 79–80).

| # | from | due | principal | interest | totalDue | outstanding | line |
|---|---|---|---:|---:|---:|---:|---|
| 1 | 2024-01-01 | 2024-02-01 | `31.97`→`3197` | `0.88`→`88` | `32.85`→`3285` | `160.25`→`16025` | 82–84 |
| 2 | 2024-02-01 | 2024-03-01 | `31.52`→`3152` | `1.33`→`133` | `32.85`→`3285` | `128.73`→`12873` | 85–87 |
| 3 | 2024-03-01 | 2024-04-01 | `31.78`→`3178` | `1.07`→`107` | `32.85`→`3285` | `96.95`→`9695` | 88–90 |
| 4 | 2024-04-01 | 2024-05-01 | `32.04`→`3204` | `0.81`→`81` | `32.85`→`3285` | `64.91`→`6491` | 91–93 |
| 5 | 2024-05-01 | 2024-06-01 | `32.31`→`3231` | `0.54`→`54` | `32.85`→`3285` | `32.60`→`3260` | 94–96 |
| 6 | 2024-06-01 | 2024-07-01 | `32.60`→`3260` | `0.27`→`27` | `32.87`→`3287` | `0` | 97–98 |

`[VERIFIED: LoanScheduleGeneratorTest.java:77-98, helper signature at :149-151]`
Invariant check: principals sum to `19222`; totals sum to `19712` = `19222 + 490` where `490` is the sum of the
transcribed interests. Both hold.

### 2.3 V-03 — `LoanScheduleGeneratorTest.testGenerateLoanScheduleWithDownPayment`

Same file. Inputs identical to V-02 **except**: `disbursementAmount` `100`→`10000` (line 51),
`disbursementDate` `2024-01-01` (line 104), `downPaymentEnabled` `true` and `downPaymentPercentage` `25`
(lines 58, 105). `[VERIFIED: LoanScheduleGeneratorTest.java:51,58,103-106]`

**TRANSCRIBED outputs.** 8 periods (line 115). Disbursement `2024-01-01`, `100`→`10000` (117–118).
Down-payment period #1, `2024-01-01`→`2024-01-01`, principal `25.0`→`2500`, totalDue `25.0`→`2500`,
outstanding `75.0`→`7500` (119–120).

| # | from | due | principal | interest | totalDue | outstanding | line |
|---|---|---|---:|---:|---:|---:|---|
| 2 | 2024-01-01 | 2024-02-01 | `12.25`→`1225` | `0.62`→`62` | `12.87`→`1287` | `62.75`→`6275` | 121–123 |
| 3 | 2024-02-01 | 2024-03-01 | `12.35`→`1235` | `0.52`→`52` | `12.87`→`1287` | `50.40`→`5040` | 124–126 |
| 4 | 2024-03-01 | 2024-04-01 | `12.45`→`1245` | `0.42`→`42` | `12.87`→`1287` | `37.95`→`3795` | 127–129 |
| 5 | 2024-04-01 | 2024-05-01 | `12.55`→`1255` | `0.32`→`32` | `12.87`→`1287` | `25.40`→`2540` | 130–132 |
| 6 | 2024-05-01 | 2024-06-01 | `12.66`→`1266` | `0.21`→`21` | `12.87`→`1287` | `12.74`→`1274` | 133–135 |
| 7 | 2024-06-01 | 2024-07-01 | `12.74`→`1274` | `0.11`→`11` | `12.85`→`1285` | `0` | 136–137 |

`[VERIFIED: LoanScheduleGeneratorTest.java:115-137]`
Invariant check: `2500` + the six principals = `10000`. Holds.

### 2.4 `ProgressiveEMICalculatorTest` — shared setup and the implicit inputs

File: `/home/user/fineract/fineract-progressive-loan/src/test/java/org/apache/fineract/portfolio/loanproduct/calc/ProgressiveEMICalculatorTest.java`

Class-level fixtures — these apply to **every** vector in §2.5 unless a test shadows them:

| Fixture | Value | Line |
|---|---|---|
| `mc` (class field) | **precision 12, `RoundingMode.HALF_EVEN`** | 76 |
| `currency` | `CurrencyData("USD","USD", decimalPlaces=2, inMultiplesOf=1, "$","USD")` | 79 |
| `MoneyHelper.getRoundingMode()` | mocked → `HALF_EVEN` | 97 |
| `MoneyHelper.getMathContext()` | mocked → `MathContext(12, HALF_EVEN)` | 98 |
| `isInterestRecognitionOnDisbursementDate()` | `false` | 109 |
| `getDaysInYearCustomStrategy()` | `null` | 110 |
| `getInterestMethod()` | `DECLINING_BALANCE` | 112 |
| `getInterestCalculationPeriodMethod()` | `DAILY` | 113 |
| `isAllowPartialPeriodInterestCalculation()` | `true` | 114 |
| `getGraceOnPrincipalPayment()` / `getGraceOnInterestPayment()` | `0` / `0` | 115–116 |

`[VERIFIED: ProgressiveEMICalculatorTest.java:76,79,97-98,107-117]`

**Four inputs that are implicit or defaulted and MUST be pinned explicitly by the capture harness:**

1. **`MoneyHelper` is a hidden second `MathContext`.** In production it is `new MathContext(PRECISION=19, tenantRoundingMode)`.
   `[VERIFIED: /home/user/fineract/fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/MoneyHelper.java:35 (PRECISION = 19) and :91-93 (getMathContext)]`
   The unit tests **mock it to precision 12**, which is *not* the production value. A capture run against a live
   server therefore executes different precision from the one that produced the transcribed literals.
   **The capture harness must record which of the two it ran under**, and a mismatch is a capture defect, not a
   Go-side parity failure.
2. **Tenant rounding mode is global configuration, not a call parameter.** It is read from the
   `rounding-mode` global config row.
   `[VERIFIED: MoneyHelperInitializationService.java:102-106 → GlobalConfigurationConstants.ROUNDING_MODE]`
   `[VERIFIED: GlobalConfigurationConstants.java:41 → "rounding-mode"]`
   Seeded from `${fineract.tenant.rounding-mode}`
   `[VERIFIED: fineract-provider/src/main/resources/db/changelog/tenant/parts/0002_initial_data.xml:219-220]`
   whose default is `6`.
   `[VERIFIED: fineract-provider/src/main/resources/application.properties:77 → fineract.tenant.config.rounding-mode=${FINERACT_CONFIG_ROUNDING_MODE:6}]`
   `6` is the ordinal of `RoundingMode.HALF_EVEN`, consistent with what the tests mock — but it is a *default*,
   settable per environment, and **must be asserted, not assumed, at capture time.**
3. **`Money.of(currency, amount)` (2-arg) silently reaches for `MoneyHelper.getMathContext()`.**
   `[VERIFIED: /home/user/fineract/fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/Money.java:103,115,119,131 and the fallback at :495 — `mc != null ? mc : MoneyHelper.getMathContext()`]`
   The test helper `toMoney(double)` uses exactly this 2-arg form
   `[VERIFIED: ProgressiveEMICalculatorTest.java:5260-5262]`, so every disbursement amount in §2.5 was built
   under the mocked context. Any capture harness that constructs `Money` must pass an explicit `MathContext`.
4. **`installmentAmountInMultiplesOf` engages `MoneyHelper.getRoundingMode()`.**
   `[VERIFIED: Money.java:154 — divide(inMultiplesOfValue, 0, MoneyHelper.getRoundingMode())]`
   This is a further reason the §3 gap on that parameter cannot be closed from source.

**A rate-factor caveat.** The `rateFactor` argument asserted by `checkPeriod` is compared **after**
`value.setScale(MoneyHelper.getMathContext().getPrecision(), MoneyHelper.getRoundingMode())`
`[VERIFIED: ProgressiveEMICalculatorTest.java:5241 and applyMathContext at :5256-5258]`. A transcribed rate factor
is therefore a **12-decimal-place rounding of the engine's value**, not the engine's value. Vectors must record
it as such, or the Go side will be graded against a rounding of the truth and a genuine divergence in digits
13+ will pass silently.

**`toDouble` is a comparison artefact, not a storage format.** Both minable helper families convert `BigDecimal`
to `double` before `assertEquals`
`[VERIFIED: ProgressiveEMICalculatorTest.java:5248-5254; EmbeddableProgressiveLoanScheduleGeneratorTest.java:120-122]`.
The vector store must **not** replicate this — see §5.

### 2.5 `ProgressiveEMICalculatorTest` — transcribed schedule vectors

Helper column orders, both verified at `ProgressiveEMICalculatorTest.java:5211-5246`:
- **7-arg**: `(model, repaymentIdx, interestIdx, emi, rateFactor, interestDue, principalDue, outstanding)`
- **8-arg**: `(model, repaymentIdx, interestIdx, emi, rateFactor, interestDue, interestDueCumulated, principalDue, outstanding)`
- **6-arg**: `(model, repaymentIdx, emi, interestDueCumulated, principalDue, outstanding, fullyRepaid)`

---

#### V-04 — `test_disbursedAmt100_dayInYears360_daysInMonth30_repayEvery1Month` (line 298)

Inputs: rate `9.4822` (308); `DAYS_360` / `DAYS_30` (312–313); `MONTHS`, repayEvery `1` (314–315);
`installmentAmountInMultiplesOf = null` (309); currency at 316; six explicit monthly periods
`2024-01-01 … 2024-07-01` (301–306); one disbursement `100`→`10000` at `2024-01-01` (321–322);
class `mc` (12, HALF_EVEN). `[VERIFIED: lines 298-322]`

Per-repayment-period money, TRANSCRIBED (minor units):

| idx | emi | dueInterest | duePrincipal | outstanding | line |
|---:|---:|---:|---:|---:|---|
| 0 | `17.13`→`1713` | `0.79`→`79` | `16.34`→`1634` | `83.66`→`8366` | 324–325 |
| 1 | `17.13`→`1713` | `0.66`→`66` | `16.47`→`1647` | `67.19`→`6719` | 326 |
| 2 | `17.13`→`1713` | `0.53`→`53` | `16.60`→`1660` | `50.59`→`5059` | 327 |
| 3 | `17.13`→`1713` | `0.40`→`40` | `16.73`→`1673` | `33.86`→`3386` | 328 |
| 4 | `17.13`→`1713` | `0.27`→`27` | `16.86`→`1686` | `17.0`→`1700` | 329 |
| 5 | `17.13`→`1713` | `0.13`→`13` | `17.00`→`1700` | `0.0`→`0` | 330 |

Non-money intermediates, TRANSCRIBED as exact decimal strings: repayment period 0 has two interest periods —
idx (0,0) rateFactor `0.0`, calculatedDueInterest `0.0`; idx (0,1) rateFactor `0.007901833333`,
calculatedDueInterest `0.790183333301`. Periods 1–5 each carry rateFactor `0.007901833333` with
calculatedDueInterest `0.66106737664`, `0.530924181643`, `0.399753748317`, `0.267556076655`, `0.134331166661`.
`[VERIFIED: lines 324-330]`
Invariant check: principals sum to `10000`. Holds.

---

#### V-05 — `test_disbursedAmt1000_NoInterest_repayEvery1Month` (line 1082) — **0% rate**

Inputs: rate `BigDecimal.ZERO` (1090); `ACTUAL` / `ACTUAL` (1094–1095); `MONTHS`, repayEvery `1` (1096–1097);
`installmentAmountInMultiplesOf = null` (1091); four monthly periods `2024-01-01 … 2024-05-01` (1084–1088);
disbursement `1000`→`100000` at `2024-01-01` (1103–1104); class `mc`. `[VERIFIED: lines 1082-1104]`

| idx | emi | interestDue | duePrincipal | outstanding | rateFactor | line |
|---:|---:|---:|---:|---:|---|---|
| 0 | `250.0`→`25000` | `0.0`→`0` | `250.0`→`25000` | `750.0`→`75000` | `0.0` | 1106 |
| 1 | `250.0`→`25000` | `0.0`→`0` | `250.0`→`25000` | `500.0`→`50000` | `0.0` | 1107 |
| 2 | `250.0`→`25000` | `0.0`→`0` | `250.0`→`25000` | `250.0`→`25000` | `0.0` | 1108 |
| 3 | `250.0`→`25000` | `0.0`→`0` | `250.0`→`25000` | `0.0`→`0` | `0.0` | 1109 |

`[VERIFIED: lines 1106-1109]` — 0% rate is **covered** by literal expectations, but only for an *evenly divisible*
principal (`100000 / 4`). 0%-with-uneven-division is a gap (§3).

---

#### V-06 — `test_360_30_repayment_schedule_disbursement_month_end` (line 2215) — month-end **as pinned input**

⚠ **This test shadows the class `mc` with a local `MathContext(12, RoundingMode.HALF_UP)` at line 2216.**
`[VERIFIED: line 2216]` Transcribing this vector without that shadow is a reproducibility error.

Inputs: rate `9.99` (2225); `DAYS_360` / `DAYS_30` (2229–2230); `MONTHS`, repayEvery `1` (2231–2232);
`installmentAmountInMultiplesOf = null` (2226); disbursement `2450.0`→`245000` at `2023-10-31` (2238–2241).
Period boundaries are **supplied literally** (2217–2223): `2023-10-31 → 2023-11-30 → 2023-12-31 → 2024-01-31 →
2024-02-29 → 2024-03-31 → 2024-04-30`. `[VERIFIED: lines 2215-2241]`

| idx | emi | interestDue | duePrincipal | outstanding | line |
|---:|---:|---:|---:|---:|---|
| 0 | `420.31`→`42031` | `20.40`→`2040` | `399.91`→`39991` | `2050.09`→`205009` | 2243 |
| 1 | `420.31`→`42031` | `17.07`→`1707` | `403.24`→`40324` | `1646.85`→`164685` | 2244 |
| 2 | `420.31`→`42031` | `13.71`→`1371` | `406.60`→`40660` | `1240.25`→`124025` | 2245 |
| 3 | `420.31`→`42031` | `10.33`→`1033` | `409.98`→`40998` | `830.27`→`83027` | 2246 |
| 4 | `420.31`→`42031` | `6.91`→`691` | `413.40`→`41340` | `416.87`→`41687` | 2247 |
| 5 | `420.34`→`42034` | `3.47`→`347` | `416.87`→`41687` | `0.00`→`0` | 2248 |

`[VERIFIED: lines 2243-2248]` Invariant check: principals sum to `245000`. Holds.

**Crucial limitation — read before treating this as month-end coverage.** The Jan-31 → Feb-29 → Mar-31
sequence here is an *input literal*, not a *derived output*. This vector does **not** exercise the month-end
re-anchoring rule. See §3.2.

---

#### V-07 — `test_actual_actual_repayment_schedule_disbursement_month_end` (line 2326) — largest principal in the corpus

⚠ Local `MathContext(12, RoundingMode.HALF_UP)` at line 2327. `[VERIFIED: line 2327]`

Inputs: rate `45.0` (2336); `ACTUAL` / `ACTUAL` (2340–2341); `MONTHS`, repayEvery `1` (2342–2343);
`installmentAmountInMultiplesOf = null` (2337); disbursement `245000.0`→`24500000` at `2023-10-31` (2349–2352);
same six literal month-end boundaries as V-06 (2328–2334). `[VERIFIED: lines 2326-2352]`

| idx | emi | interestDue | duePrincipal | outstanding | line |
|---:|---:|---:|---:|---:|---|
| 0 | `46343.27`→`4634327` | `9061.64`→`906164` | `37281.63`→`3728163` | `207718.37`→`20771837` | 2354 |
| 1 | `46343.27`→`4634327` | `7938.83`→`793883` | `38404.44`→`3840444` | `169313.93`→`16931393` | 2355 |
| 2 | `46343.27`→`4634327` | `6453.36`→`645336` | `39889.91`→`3988991` | `129424.02`→`12942402` | 2356 |
| 3 | `46343.27`→`4634327` | `4614.71`→`461471` | `41728.56`→`4172856` | `87695.46`→`8769546` | 2357 |
| 4 | `46343.27`→`4634327` | `3342.49`→`334249` | `43000.78`→`4300078` | `44694.68`→`4469468` | 2358 |
| 5 | `46343.25`→`4634325` | `1648.57`→`164857` | `44694.68`→`4469468` | `0.00`→`0` | 2359 |

`[VERIFIED: lines 2354-2359]` Invariant check: principals sum to `24500000`. Holds.

This is the largest principal carrying a full literal schedule anywhere in the corpus: `24,500,000` minor units
(~9 significant digits). Relevant to the MNT-scale gap in §3.9.

---

#### V-08 — `test_dailyInterest_disbursedAmt1000_dayInYears360_daysInMonth30_repayIn1Month` (line 1274) — **single installment**

Inputs: rate `7.0` (1280); `DAYS_360` / `DAYS_30` (1284–1285); `MONTHS`, repayEvery `1` (1286–1287);
`installmentAmountInMultiplesOf = null` (1281); **exactly one** period `2024-01-01 → 2024-02-01` (1278);
disbursement `1000.0`→`100000` at `2024-01-01` (1293–1294); class `mc` (12, HALF_EVEN).
`[VERIFIED: lines 1274-1294]`

Schedule: idx 0 — emi `1005.83`→`100583`, dueInterest `5.83`→`583`, duePrincipal `1000.0`→`100000`,
outstanding `0.0`→`0`; interest sub-period (0,1) rateFactor `0.005833333333`, calculatedDueInterest `5.833333333`.
`[VERIFIED: lines 1296-1297]`

**Daily accrual, TRANSCRIBED (minor units), 31 rows** — `checkDailyInterest(model, dueDate=2024-02-01,
startDay=2024-01-01, dayOffset, dailyIncrement, cumulative)`, lines 1302–1332:

| day | Δ | cum | day | Δ | cum | day | Δ | cum | day | Δ | cum |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 19 | 19 | 9 | 18 | 169 | 17 | 19 | 320 | 25 | 18 | 470 |
| 2 | 19 | 38 | 10 | 19 | 188 | 18 | 19 | 339 | 26 | 19 | 489 |
| 3 | 18 | 56 | 11 | 19 | 207 | 19 | 19 | 358 | 27 | 19 | 508 |
| 4 | 19 | 75 | 12 | 19 | 226 | 20 | 18 | 376 | 28 | 19 | 527 |
| 5 | 19 | 94 | 13 | 19 | 245 | 21 | 19 | 395 | 29 | 19 | 546 |
| 6 | 19 | 113 | 14 | 18 | 263 | 22 | 19 | 414 | 30 | 19 | 565 |
| 7 | 19 | 132 | 15 | 19 | 282 | 23 | 19 | 433 | 31 | 18 | 583 |
| 8 | 19 | 151 | 16 | 19 | 301 | 24 | 19 | 452 | | | |

`[VERIFIED: lines 1302-1332; helper signature at :5191-5199]`
Note the source writes `4.7` at line 1326 (scale 1) and `3.20` at line 1318 (scale 2); both reinterpret exactly
(`470`, `320`). Cumulative day 31 = `583` matches the transcribed period `dueInterest` of `583`.

---

#### V-09 — `test_sameAsRepayment_month_repay_every_1_periods_24` (line 3860) — 24 periods, but **FLAT**

Inside `@Nested class InterestTypeFlatAndCalculationPeriodSameAsRepaymentPeriod`, whose `@BeforeEach` overrides
the class defaults: `InterestMethod.FLAT` (3609), `ACTUAL`/`ACTUAL` (3611–3612),
`InterestCalculationPeriodMethod.SAME_AS_REPAYMENT_PERIOD` (3614). `[VERIFIED: lines 3602-3617]`

Inputs: rate `12.0` (3862); `MONTHS`, `numberOfRepayments = 24`, repayEvery `1` (3866–3868);
`allowFullTermForTranche = false` (3869); `installmentAmountInMultiplesOf = null` (3872); periods derived by
`generateExpectedRepaymentPeriods(2024-01-01)`; **two** disbursements on `2024-01-01`: `7500.0`→`750000` and
`2500.0`→`250000` (3877–3878). `[VERIFIED: lines 3860-3878]`

TRANSCRIBED first block (lines 3880–3903): idx 0–22 each emi `516.67`→`51667`, interest `100.00`→`10000`,
principal `416.67`→`41667`, with outstanding descending `9583.33`→`958333`, `9166.66`→`916666`, … ,
`416.59`→`41659`; idx 23 emi `516.59`→`51659`, interest `10000`, principal `416.59`→`41659`, outstanding `0.00`→`0`.
`[VERIFIED: lines 3880-3903]` Invariant check: `41667 × 23 + 41659 = 1000000`. Holds.

Lines 3905–3930 then add a third disbursement `1000.0`→`100000` at the date written in source as
`disbursementDate.plusMonths(3).plusDays(4)` (line 3905) and re-assert all 24 periods — a mid-term-disbursement
re-amortisation vector. Transcribe mechanically from those lines if wanted; the date is left as the source
expression here rather than resolved, so nothing in this document is a derived value.

**This is the longest fully-asserted schedule in the corpus, but it is FLAT, not declining balance.** See §3.7.

---

#### V-10 — `LeapYear366OnlyForPeriodWith29thOfFebruaryTest` (nested class, line 2976)

Seven tests, S1–S5 plus `test_feb29_period_only_cross_year_quarterly_period_containing_feb29` (3183) and
`test_leap_year_only_actual_no_effect_on_360_loan` (3231). `[VERIFIED: grep of test method names, lines 2983-3231]`

All set `DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY` — this is the **only** place in the corpus where
`getDaysInYearCustomStrategy()` is non-null; everywhere else it is `null` (class default at line 110).
`[VERIFIED: lines 2997-2998, 3036-3037, 3074-3075 and the class default at :110]`

Fully transcribed here — **S1** (line 2983, February split across periods): rate `9.482` (2992), `ACTUAL`/`ACTUAL`
(2996, 2999), `MONTHS`/`1` (3000–3001), `allowFullTermForTranche=false` (3003), multiples `null` (2993),
six periods `2023-12-12 … 2024-06-12` (2984–2990), disbursement `10000.0`→`1000000` at `2023-12-12` (3008–3009),
class `mc` (12, HALF_EVEN):

| idx | emi | interestDue | duePrincipal | outstanding | line |
|---:|---:|---:|---:|---:|---|
| 0 | `1713.21`→`171321` | `80.53`→`8053` | `1632.68`→`163268` | `8367.32`→`836732` | 3011 |
| 1 | `1713.21`→`171321` | `67.38`→`6738` | `1645.83`→`164583` | `6721.49`→`672149` | 3012 |
| 2 | `1713.21`→`171321` | `50.50`→`5050` | `1662.71`→`166271` | `5058.78`→`505878` | 3013 |
| 3 | `1713.21`→`171321` | `40.74`→`4074` | `1672.47`→`167247` | `3386.31`→`338631` | 3014 |
| 4 | `1713.21`→`171321` | `26.39`→`2639` | `1686.82`→`168682` | `1699.49`→`169949` | 3015 |
| 5 | `1713.18`→`171318` | `13.69`→`1369` | `1699.49`→`169949` | `0.00`→`0` | 3016 |

`[VERIFIED: lines 3011-3016]` Invariant check: principals sum to `1000000`. Holds.

**S3** (line 3060) is the leap-Feb-29 month-end variant of V-07 with the same principal `245000.0`→`24500000`,
rate `45.00`, but `FEB_29_PERIOD_ONLY` — and its numbers differ from V-07's (e.g. period 0 emi `46348.39`→`4634839`
vs V-07's `4634327`), which makes the pair (V-07, S3) a **differential vector for the custom-strategy flag alone**.
`[VERIFIED: lines 3060-3093 vs 2326-2359]`

### 2.6 Uneven-split primitive — `EqualAmortizationValue` (nested class, line 5099)

Three tests pin `emiCalculator.calculateEqualAmortizationValues(amount, installments, installmentAmountInMultiplesOf, currency)`:

| test | amount | installments | multiplesOf | asserted per-installment values | line |
|---|---|---:|---|---|---|
| `test_AmortizationTotalIsLessThanInstallmentNumber` | `0.04`→`4` | 6 | `null` | `0.01,0.01,0.01,0.01,0.0,0.0` → `1,1,1,1,0,0` | 5103–5113 |
| `test_AmortizationIsJustBiggerThanInstallmentNumber` | `0.07`→`7` | 6 | `null` | `0.01,0.01,0.01,0.01,0.01,0.02` → `1,1,1,1,1,2` | 5116–5126 |
| `test_AmortizationNonEdgeCase` | `0.59`→`59` | 6 | `null` | `0.1,0.1,0.1,0.1,0.1,0.09` → `10,10,10,10,10,9` | 5129–5137 |

`[VERIFIED: lines 5099-5139]`

This is the corpus's **only direct coverage of uneven division / residual absorption**, and it is at the
sub-cent primitive level. It confirms the "splits sum to whole" invariant in all three cases (`4`, `7`, `59`).
It does **not** cover uneven division at MNT scale, and `installmentAmountInMultiplesOf` is `null` in all three.

### 2.7 Rate-factor and `fn`-recurrence primitives (not money)

`test_rateFactorByRepaymentEveryMonthMethod_DayInYear365_DaysInMonthActual` (line 129) and
`..._DayInYearActual_DaysInMonthActual` (line 144) assert exact 12-dp decimal **strings** for six periods,
with `interestRate = 0.094822` (line 82) and the six monthly periods built at lines 88–94:

- `DAYS_365` + `ACTUAL`: `0.008053375342, 0.007533802740, 0.008053375342, 0.007793589041, 0.008053375342, 0.007793589041` `[VERIFIED: lines 133-134]`
- `ACTUAL` + `ACTUAL`: `0.008031371585, 0.007513218579, 0.008031371585, 0.007772295082, 0.008031371585, 0.007772295082` `[VERIFIED: lines 149-150]`

`test_fnValueFunction_RepayEvery1Month_DayInYear365_DaysInMonthActual` (line 160) asserts
`1.00000000000, 2.00753380274, 3.02370122596, 4.04726671069, 5.07986086861, 6.11945121660` `[VERIFIED: lines 165-166]`.

These compare `.toString()` on the `BigDecimal`, so they pin **scale and digits exactly**, not just value — the
strongest form of expectation in the corpus, and the right first target for a Go unit-level parity test.

### 2.8 Index of the remaining ProgressiveEMICalculatorTest expectations (NOT transcribed here)

898 `checkPeriod` rows exist; the sections above transcribe roughly 90 of them. The remainder are indexed by
test-method line so the capture fire can transcribe mechanically without re-analysing. Groups, by first line:

`262` emi-adjustment · `334` multi-disbursement on due date · `380/422/471/519` mid-term rate change ·
`565` balance correction · `681/763` payoff · `851/900/949` multi-disbursement variants · `996` actual/actual ·
`1032` total repay 1st · `1113/1149` weekly · `1179` 15-day · `1215` due-principal after payments ·
`1336/1403` daily-interest chargeback / 2-month · `1473–1906` interest pause (13 tests) ·
`1942/1985/2029` reschedule · `2071/2120/2165` multi-year · `2252/2289/2363/2400` near-month-end and 2-monthly ·
`2437/2469` `interestRecognitionFromDisbursementDate` false/true pair · `2501` nested chargeback (3) ·
`2692–2917` chargeback (5) · `2976` nested leap year (7) · `3270` S5 chargeback · `3335` model serialization ·
`3409` nested FLAT+DAILY (5) · `3602` nested FLAT+SAME_AS_REPAYMENT (9) · `3972` nested DECLINING+SAME_AS_REPAYMENT (4) ·
`4161` nested reschedule/extend term (4) · `4380` nested re-age equal amortization (11) · `5099` nested equal
amortization (3) · `5285/5317` principal/interest grace · `5348` full-term tranche.
`[VERIFIED: grep -n "public void test_\|void test_" ProgressiveEMICalculatorTest.java — full method list read this session; per-nested-class @Test counts obtained by an awk range count over the same file this session]`

---

## 3. Coverage map — what parity needs vs what the corpus pins

Legend: **PINNED** = a literal expectation exists in the corpus. **GAP** = no literal anywhere in the seam;
must be captured.

### 3.1 Uneven principal division — **PARTIALLY PINNED**

Pinned at the primitive level only (§2.6, `0.04`/`0.07`/`0.59` over 6 installments) and implicitly in every
6-period schedule where the last EMI differs (V-01 `1700` vs `1701`; V-06 `42034` vs `42031`; V-07 `4634325`
vs `4634327` — note the last EMI is *smaller* here, the opposite direction from V-06).
**GAP:** uneven division at MNT scale, and uneven division at 0% rate.

### 3.2 Month-end disbursement (Jan 31) and the month-end re-anchoring rule — **GAP (the important one)**

The rule exists in production code: for monthly frequency, when the seed day-of-month is `> 28` and the
candidate date's day is `>= 28`, the day is set to `min(lengthOfMonth(date), seedDay)` — i.e. Jan 31 → Feb 29 →
**back to** Mar 31, rather than Java's `plusMonths` clamping which would stick at Mar 29.
`[VERIFIED: /home/user/fineract/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/DefaultScheduledDateGenerator.java:168-176 — method `adjustDate`; the `> 28` condition is at :169 and the re-anchoring body at :170-173]`

**No test in the seam exercises it as a derived output:**
- `DefaultScheduledDateGenerator` is instantiated in only three places in scope: `LoanScheduleGeneratorTest.java:70`
  and `:108`, and `EmbeddableProgressiveLoanScheduleGenerator.java:39`.
  `[VERIFIED: grep -rn "DefaultScheduledDateGenerator" over both in-scope src trees]`
- V-01/V-02/V-03 all use seed day-of-month `1` (`2024-01-01`), so the `> 28` branch is never taken.
  `[VERIFIED: EmbeddableProgressiveLoanScheduleGeneratorTest.java:48; LoanScheduleGeneratorTest.java:56,65,104]`
- V-06/V-07/S3 contain the Jan-31 → Feb-29 → Mar-31 sequence but **supply it as input literals**
  (`ProgressiveEMICalculatorTest.java:2217-2223, 2328-2334, 3061-3067`); `ProgressiveEMICalculatorTest`'s own
  generator is used only for interest sub-period splitting, not for deriving these boundaries.

**Therefore: the re-anchoring rule is unpinned by any golden vector and must be captured.** Given the rule lives
in `fineract-loan` and is bundled into the embeddable shadowJar (`build.gradle:28-32`), it is capturable through
the embeddable entry point by setting `scheduleGenerationStartDate` / `disbursementDate` to a day > 28.

### 3.3 Leap-year Feb 29 — **PINNED**

Seven tests under `FEB_29_PERIOD_ONLY` (§2.5 V-10) plus the V-06/V-07 month-end schedules that traverse
`2024-02-29`. **GAP:** Feb 29 with `daysInYearCustomStrategy = null` under `DAYS_365` (the leap tests all pair
Feb-29 handling with `ACTUAL`, or with `DAYS_360` in the no-effect test at 3231).

### 3.4 Multi-period rate variation — **PINNED, structurally**

`emiCalculator.changeInterestRate(...)` appears at lines 410, 459, 505, 549, 1725–1726, 1770–1773, 1814–1815 and
beyond, each with literal post-change schedules. `[VERIFIED: grep -n "changeInterestRate" → those lines]`
**Caveat:** every one is reached through `changeInterestRate` on an existing model — i.e. mid-term *rescheduling*.
There is no vector for a product configured with a *rate schedule* from origination. Whether that distinction
matters for the Go port is a design question, not a corpus question.

### 3.5 `installmentAmountInMultiplesOf` set — **GAP, total**

`grep -n "installmentAmountInMultiplesOf" over the whole in-scope test tree returns **zero** assignments to a
non-null value; every occurrence is either `= null` or the pass-through into
`generatePeriodInterestScheduleModel(..., installmentAmountInMultiplesOf, mc)`.
`[VERIFIED: grep -rn "installmentAmountInMultiplesOf" fineract-progressive-loan/src/test/ | grep -v "= null" → only pass-through call sites]`
`[VERIFIED: EmbeddableProgressiveLoanScheduleGeneratorTest.java:60 → null; LoanScheduleGeneratorTest.java:67 → null; ProgressiveEMICalculatorTest.java:189,228,273,309,1091,1124,1157,1190,1232,1281,2226,2263,2300,2337,2993,3032,3070,3830,3872 → null]`

This is the single largest gap. It is also the highest-risk one for the Mongolian market, where round-to-the-
nearest-1,000₮ instalments are a normal product feature. It additionally engages `MoneyHelper.getRoundingMode()`
(§2.4 point 4), so it cannot even be reasoned about from the transcribed values.

### 3.6 Single installment (`numberOfRepayments == 1`) — **PINNED**

V-08 (§2.5), one period, with 31 daily accrual rows. **GAP:** single installment with a non-zero rate at MNT
scale, and single installment at 0%.

### 3.7 Long terms — **PARTIALLY PINNED**

| Term | Interest method | Full per-period literals? | Where |
|---|---|---|---|
| 24 periods | **FLAT** | yes | V-09, lines 3880–3930 |
| 20 periods | **FLAT** | yes | lines 3837–3856 |
| 12 periods | DECLINING_BALANCE | **no** — only `emi == 8.65` for periods 0–10 and structural `> 0` assertions | `test_emi_calculator_performance`, lines 211–258 |
| 12 periods | DECLINING_BALANCE | post-payment state only, all interest `0.0` | line 1215 |
| 6 periods | DECLINING_BALANCE | yes | V-01, V-04, V-06, V-07, V-10 |

`[VERIFIED: lines 211-258, 1215-1271, 3818-3857, 3860-3931]`

**GAP: there is no declining-balance schedule longer than 6 periods with full literal per-period expectations.**
A 36-month or 60-month declining-balance schedule — the ordinary Mongolian consumer-loan shape — is unpinned.

### 3.8 0% rate — **PINNED** (V-05), for evenly divisible principal only. See §3.1.

### 3.9 Large MNT-scale principals in integer minor units — **GAP, total**

Largest principal with a full literal schedule: `245000.0` → `24500000` minor units (V-07, USD-denominated).
`[VERIFIED: grep of toMoney(...) / disbursedAmount across the file; 245000.0 at lines 2349 and 3085 is the maximum]`
A routine Mongolian consumer loan of `MNT 5,000,000` is `500000000` minor units — ~20× larger, ~10 significant
digits before any rate multiplication. Against a **precision-12** `MathContext`, MNT-scale intermediates consume
a materially larger share of the available precision than any USD-100 test ever does.
**This is precisely why MNT-scale values must be captured and may not be scaled up from the USD vectors by
arithmetic.** No extrapolation is offered here.

### 3.10 Coverage summary

| Behaviour | Status |
|---|---|
| Uneven principal division | PARTIAL (primitive only) |
| 0% rate | PINNED (even division only) |
| Month-end disbursement (Jan 31) + re-anchoring | **GAP** (rule exists in code, no vector) |
| Leap-year Feb 29 | PINNED (under `FEB_29_PERIOD_ONLY` / `ACTUAL`) |
| Multi-period rate variation | PINNED (as mid-term change) |
| `installmentAmountInMultiplesOf` set | **GAP (total)** |
| Single installment | PINNED |
| Long terms | PARTIAL (FLAT only ≥ 12; declining balance capped at 6) |
| MNT-scale principals | **GAP (total)** |

---

## 4. The capture plan

### 4.0 Run C-00 — CALIBRATION. Nothing else is trustworthy until this passes.

**Read this first: the first capture run must reproduce an already-transcribed literal test expectation exactly.**
If C-00 does not match V-01 digit for digit, the harness is misconfigured and **no** subsequent capture may be
entered into the vector store — a wrong harness produces plausible wrong numbers, which is the worst failure
mode available to this program.

- **Target:** `EmbeddableProgressiveLoanScheduleGenerator.generate(mc, modelData)`.
- **Build:** `./gradlew :fineract-progressive-loan-embeddable-schedule-generator:shadowJar` at commit
  `426a23544e8426a38ae43ae404670a0a7e85b9eb`; record the commit and the jar's SHA-256 in the capture record.
- **Inputs:** the complete table in §2.1, verbatim. **`MathContext` = precision 12, `RoundingMode.HALF_UP`** —
  pinned explicitly, never defaulted.
- **Record:** all four plan-level fields and all seven periods, as `BigDecimal.toPlainString()` at the source
  scale — **never** via `double`.
- **Acceptance check (all four must hold):**
  1. Every one of the 4 plan-level and 6 × 7 period values equals the corresponding §2.1 TRANSCRIBED value after
     exact scale-2 reinterpretation.
  2. `getLoanTermInDays() == 182` and `getPeriods().size() == 7`.
  3. Principals sum to `10000`; interests sum to `205`; totals sum to `10205`.
  4. The captured output also matches the README's documented CI stdout (§2.1) — a second, independent
     attestation of the same figures.
- **On failure:** stop. Do not capture anything else. Report the harness configuration, both `MathContext`s
  (the parameter one and `MoneyHelper`'s, §2.4), and the tenant `rounding-mode` value.

### 4.1 Run C-01 — Environment attestation (no vectors produced)

Purpose: make every later capture reproducible. Record, and store alongside every vector:

| Item | How to obtain |
|---|---|
| Fineract commit | `git rev-parse HEAD` — must be `426a23544e8426a38ae43ae404670a0a7e85b9eb` |
| JDK version | `java -version` |
| `MathContext` parameter | explicit in the harness — precision AND rounding mode, both logged |
| `MoneyHelper.PRECISION` | `19` in source (§2.4); log the value observed at runtime |
| tenant `rounding-mode` | `SELECT value FROM c_configuration WHERE name = 'rounding-mode'` on the PostgreSQL tenant DB; default is `6` = `HALF_EVEN` (§2.4 point 2) |
| DB engine | must be **PostgreSQL** — `postgresql` compose profile. Never MySQL/MariaDB. Oracle Database is prohibited. |
| Harness path used | `embeddable-jar` or `live-server` |

A vector captured without this block attached is not admissible.

### 4.2 Runs C-02 … C-10 — Gap closure via the embeddable jar

Each run: **`MathContext` explicitly pinned (precision 12, `RoundingMode.HALF_UP`, matching C-00 unless the run
says otherwise); currency `MNT` with `decimalPlaces = 2`; `interestMethod = DECLINING_BALANCE`;
`allowPartialPeriodInterestCalculation = true`; `interestRecognitionOnDisbursementDate = false`;
`daysInYearCustomStrategy = null`; `fixedLength = null`; `allowFullTermForTranche = false`; down payment
disabled — unless the run's row overrides.** Record every period: `periodNumber`, `fromDate`, `dueDate`,
`principal`, `interest`, `fee`, `penalty`, `totalDue`, `outstandingBalance`, `totalOutstandingBalance`, plus the
four plan-level fields.

| Run | Closes gap | Distinguishing inputs | Acceptance check |
|---|---|---|---|
| **C-02** | §3.2 month-end re-anchoring | `startDate = disbursementDate = 2024-01-31`; 6 monthly; principal `MNT 1,000,000` → `100000000`; rate `9.99`; `DAYS_30`/`DAYS_360` | Derived due dates are `2024-02-29, 2024-03-31, 2024-04-30, 2024-05-31, 2024-06-30, 2024-07-31` — i.e. period 3 **re-anchors to 31**, not 29. If it stops at 29 the harness bypassed `adjustDate` (§3.2) and the run is void. Principals sum to `100000000`. |
| **C-03** | §3.2 near-miss control | identical to C-02 but `2024-01-30` | Due dates `…-02-29, -03-30, -04-30, -05-30, -06-30, -07-30`. Differential vs C-02 isolates the `seedDay > 28` branch. |
| **C-04** | §3.9 MNT scale | `2024-01-01`; 6 monthly; principal `MNT 5,000,000` → `500000000`; rate `9.4822`; `DAYS_30`/`DAYS_360` (same shape as V-04, only the principal changes) | Principals sum to `500000000`; final `outstandingBalance == 0`. Records whether precision-12 behaves at ~10 significant digits (§3.9). |
| **C-05** | §3.9 + §3.7 | `2024-01-01`; **36** monthly; principal `MNT 20,000,000` → `2000000000`; rate `18.0`; `DAYS_30`/`DAYS_360` | 37 periods; principals sum to `2000000000`; final balance `0`. |
| **C-06** | §3.7 long declining balance | `2024-01-01`; **60** monthly; principal `MNT 50,000,000` → `5000000000`; rate `24.0`; `ACTUAL`/`ACTUAL` | 61 periods; principals sum to `5000000000`; final balance `0`; traverses two Feb-29s (2028 is a leap year) with `daysInYearCustomStrategy = null` — also closes part of §3.3. |
| **C-07** | §3.5 `installmentAmountInMultiplesOf` | as C-04 but `installmentAmountInMultiplesOf = 100000` (= `MNT 1,000`) | Every EMI except the last is an exact multiple of `100000` minor units; principals still sum to `500000000`. **Also record the tenant `rounding-mode` in force — this path reads it (§2.4 point 4).** |
| **C-08** | §3.5 × §3.1 | as C-07 but principal `MNT 5,000,001` → `500000100` (deliberately not divisible) | Residual is absorbed in exactly one period; principals sum to `500000100`. |
| **C-09** | §3.1 + §3.8 | `2024-01-01`; 7 monthly; principal `MNT 1,000,000` → `100000000`; **rate `0`** | Zero interest in every period; principals sum to `100000000` with the residual visible (7 does not divide `100000000` evenly). |
| **C-10** | §3.6 MNT single installment | `2024-01-01`; **1** period; principal `MNT 5,000,000` → `500000000`; rate `7.0`; `DAYS_30`/`DAYS_360` | 2 periods (disbursement + 1); principal = full amount; balance `0`. |

Cross-cutting acceptance checks applied to **every** run C-02…C-10:
- Sum of period principals equals the disbursed amount, in integer minor units, exactly.
- Final `outstandingLoanBalance` is exactly `0`.
- `totalRepaymentAmount == totalDisbursedAmount + totalInterestAmount`, in integer minor units.
- Every recorded monetary value has scale exactly 2 before reinterpretation; a value arriving with scale > 2 is
  an intermediate that has escaped rounding and must be recorded as a decimal string, not as money (§5).
- No value passes through a `float` or `double` at any point in the harness (§5).

### 4.3 Runs C-11+ — Live-server captures (require Fineract + PostgreSQL)

Only these genuinely need the running instance, because their inputs are not expressible through
`LoanRepaymentScheduleModelData`: multi-tranche disbursement, mid-term interest-rate change, interest pause,
chargeback, re-ageing, reschedule, and grace periods. Each is *structurally* pinned in the corpus (§2.8), so the
capture plan for them is: pick the corpus test, replicate its inputs at MNT scale through the API, and record the
resulting schedule. Deferred here rather than specified, because they are Tier-A scope, not Tier 0.

**Deposit-taking note:** nothing in this plan touches savings/deposit behaviour, so no activation gate is engaged.

### 4.4 Ordering

`C-00` → `C-01` → `C-02` → `C-03` → `C-04` → `C-05` → `C-06` → `C-07` → `C-08` → `C-09` → `C-10` → `C-11+`.
C-00 gates everything. C-02/C-03 are a matched pair and must both run or neither.

---

## 5. Money representation

**MNT = ISO 4217 alphabetic `MNT`, numeric `496`, minor unit `2`.** Every monetary quantity in this plan and in
the resulting vector store is an **integer count of minor units** (`int64` in Go, `BIGINT` in PostgreSQL).
Display is 0 decimals with a postfix symbol (`1,250,000₮`); storage is 2.

### 5.1 The conversion, stated exactly

For a Fineract source literal `L` written as a decimal with scale `s ≤ 2`:

```
minorUnits = L.setScale(2, <exact — no rounding needed since s ≤ 2>).unscaledValue()
```

This is an **exact scale-2 reinterpretation**: it re-reads the same decimal at a fixed scale of 2 and takes the
unscaled integer. It is a change of representation, not a computation — no information is added or lost, and no
rounding decision is made. Concretely: `100` (scale 0) → `100.00` → `10000`; `0.58` (scale 2) → `58`;
`4.7` (scale 1) → `4.70` → `470`; `245000.0` (scale 1) → `245000.00` → `24500000`.

**It is never a floating-point division or multiplication.** `L × 100` as a `float64` is prohibited; so is
`strconv.ParseFloat`. In Go, parse the decimal string and shift the scale integrally
(`math/big.Int` or a fixed-point decimal type), never `float32`/`float64`.

### 5.2 Why USD-denominated literals are usable as scale-2 vectors

The test currencies are `decimalPlaces = 2` — `CurrencyData("usd","US Dollar",2,null,"usd","$")` in the
embeddable test `[VERIFIED: EmbeddableProgressiveLoanScheduleGeneratorTest.java:47]` and
`CurrencyData("USD","USD",2,1,"$","USD")` in `ProgressiveEMICalculatorTest`
`[VERIFIED: ProgressiveEMICalculatorTest.java:79]`. MNT is also minor unit 2. The transcribed values therefore
transfer as **scale-2 arithmetic facts**.

Two limits on that, both material:

1. The transcribed values are **not MNT-denominated oracle output**. They are USD-denominated Fineract test
   data reinterpreted at the same scale. MNT-denominated vectors are `TO_BE_CAPTURED` (§4.2), and §3.9 explains
   why the magnitudes cannot simply be scaled up.
2. The two minable classes differ in `inMultiplesOf`: `null` in the embeddable test, `1` in
   `ProgressiveEMICalculatorTest`, `1` in `LoanScheduleGeneratorTest`
   `[VERIFIED: LoanScheduleGeneratorTest.java:48]`. Since `inMultiplesOf` feeds
   `Money.roundToMultiplesOf` `[VERIFIED: Money.java:150-157]`, capture runs must pin it explicitly rather than
   inherit it.

### 5.3 Fields that are NOT money

Three kinds of value in the transcribed set must not be stored as minor-unit integers:

| Kind | Example | Storage |
|---|---|---|
| Rate factor | `0.007901833333` (V-04) | exact decimal **string**; and see the 12-dp rounding caveat in §2.4 |
| Unrounded interest intermediate (`calculatedDueInterest`) | `0.790183333301` (V-04) | exact decimal **string** — it has scale > 2 and is *not* a settled money amount |
| Counts and dates | `182` days, `7` periods, `2024-02-01` | integer / ISO-8601 date |

### 5.4 The `toDouble` trap

Both minable helper families convert `BigDecimal` → `double` before `assertEquals`
`[VERIFIED: ProgressiveEMICalculatorTest.java:5248-5254; EmbeddableProgressiveLoanScheduleGeneratorTest.java:120-122]`.
That is Fineract's *test* convention and must **not** be reproduced. It also means the corpus's own assertions
are slightly weaker than they look — two `BigDecimal`s differing beyond `double` resolution would compare equal.
The capture harness must read `BigDecimal.toPlainString()` directly from the API objects, never the `double`
projection, and must never emit a `float`/`double` into the vector store.

---

## 6. Backlog — observed, out of seam, not chased

- `AdvancedPaymentScheduleTransactionProcessorTest` (790 LOC) is the richest **transaction-allocation** vector
  source in this module; it belongs to the payment-allocation context, not schedule generation.
- Nine `*Progressive*` integration-test classes under `integration-tests/` encode API-level expectations and are
  a second-wave vector source once a live instance is available.
- `DefaultScheduledDateGenerator` and `LoanRepaymentScheduleModelData` live in `fineract-loan`, not in either
  in-scope module, yet are bundled into the embeddable shadowJar. Whichever context owns `fineract-loan` inherits
  the month-end re-anchoring rule; the ownership boundary should be recorded before that context is planned.
- `MoneyHelper`'s tenant-scoped, globally-configured rounding mode is ambient state reached from many call sites.
  Porting it as an implicit global into Go would be a mistake; it should become an explicit parameter. Flagging
  only — a design decision for the Tier-C mapping, not this task.
- The `CLAUDE.md` "~182 LOC" figure for the Tier-0 module does not reconcile with the measured 92/123/215 (§1.1).
- `MoneyHelper.PRECISION = 19` vs the tests' mocked precision 12 is a discrepancy that will resurface in every
  live-server capture, not just this seam.

---

## 7. Evidence ledger

**`[UNVERIFIED]` count: 3.**

1. The provenance of the "~182 LOC" Tier-0 figure in `CLAUDE.md` (§1.1) — not traceable from the checkout.
2. The assertion style of the nine `*Progressive*` integration-test classes (§1.3) — not opened; doing so would
   leave the seam.
3. That no `MoneyHelper` call is reached anywhere in the embeddable `generate()` call tree (§1.4). What **is**
   verified is that `ProgressiveEMICalculator.java` contains zero `MoneyHelper` references and that the
   calculator takes `MathContext` as a parameter. Proving the negative for the whole transitive call tree
   requires executing the jar, which this sandbox cannot do — this is exactly what calibration run C-00 settles.

`InterestPeriodTest.java` (143 LOC, row 5 of §1.2) was catalogued from the LOC listing but not read line by line;
it is marked accordingly in that table rather than counted as a separate UNVERIFIED claim about a factual
assertion, since no claim is made about its contents beyond its existence and size.

Every other factual claim in this document carries a `[VERIFIED: …]` tag naming either a file and line opened in
this session or a command run in this session against `/home/user/fineract` at
`426a23544e8426a38ae43ae404670a0a7e85b9eb`.
