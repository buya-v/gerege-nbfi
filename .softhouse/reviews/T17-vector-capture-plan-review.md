# T17 — Independent adversarial review: `docs/analysis/tier0-vector-capture-plan.md`

| | |
|---|---|
| **Task** | T17 — transcription audit of the Tier-0 golden-vector capture plan (T16 output) |
| **Artefact under review** | `docs/analysis/tier0-vector-capture-plan.md`, 861 lines, merged to `main` as `1fd1517` (merge `dfeefb5`) |
| **Reviewer** | Independent adversarial reviewer, no planning context; worked only from the artefact and the pinned checkout |
| **Reference oracle (Fineract) commit** | `426a23544e8426a38ae43ae404670a0a7e85b9eb` — **verified**: `/home/user/fineract/.git/HEAD` → `426a23544e8426a38ae43ae404670a0a7e85b9eb`. Matches the pin. Proceeded. |
| **Method** | Every expected value in every claimed-transcribed vector was re-read from the cited `file:line` in the pinned checkout. Every `literal → minor-units` conversion was re-derived mechanically (exact scale-2 reinterpretation, integer arithmetic only). Every principals-sum invariant was recomputed independently. Every `[VERIFIED: …]` supporting citation on the pinning and gap-honesty claims was reopened. Coverage gaps were spot-checked against source by independent greps rather than by re-running the analyst's greps. |
| **Live reference oracle** | **NOT reachable from this sandbox.** No Fineract instance, no PostgreSQL, no `gradlew` execution. Nothing in this review is an observation of oracle behaviour; every statement below is a statement about *source text* at the pinned commit. The plan's own calibration run (C-00) remains the only thing that can settle runtime behaviour, and that is correctly how the plan frames it. |

---

## VERDICT — **ACCEPTED**, with six mandatory corrections that must land before the capture fire executes the plan

**Grounds.** I audited **418 individual expected values** across the 16 claimed-transcribed vectors (10 full schedules V-01…V-10, 3 equal-amortization primitives, 3 rate-factor/`fn` primitives) against their cited `file:line`. **All 418 are literally present at the cited line, unaltered — zero `ALTERED`, zero `NOT-IN-SOURCE`, zero `MISCITED` among vector values.** I re-derived all **248** decimal→minor-unit conversions: every one is an exact scale-2 reinterpretation, none is a floating-point operation, and no `float`/`double` appears anywhere in the plan except as an explicit prohibition or as an accurate description of Fineract's own test convention. All **8** principals-sum invariants recompute correctly. Every capture row C-00…C-10 carries an explicit `MathContext` precision **and** rounding mode. All **four** claimed coverage gaps are real — I confirmed each independently, including the strong claim that `installmentAmountInMultiplesOf` is `null` at **97/97** in-seam declarations plus the embeddable test, with zero non-null occurrences anywhere in the seam. No rejection trigger fires. However, the document contains **three false statements tagged `[VERIFIED:]`** — including one that invalidates the stated *proof* of the program's single most important gap (month-end re-anchoring), though I independently re-established that gap's conclusion by a different route. That is an evidence-discipline failure, not a synthesised vector, so it does not reach REJECTED under the stated rules; it does make the corrections below blocking on *use*, not merely advisory.

---

## 1. Per-vector transcription audit

Notation: **status** is `TRANSCRIBED-OK` (literal present and unaltered at the cited line), `ALTERED`, `NOT-IN-SOURCE`, `MISCITED`.
All source files are under `/home/user/fineract` at the pinned commit.

Short names used below:
- `EMB` = `fineract-progressive-loan-embeddable-schedule-generator/src/test/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGeneratorTest.java`
- `LSG` = `fineract-progressive-loan/src/test/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/LoanScheduleGeneratorTest.java`
- `EMI` = `fineract-progressive-loan/src/test/java/org/apache/fineract/portfolio/loanproduct/calc/ProgressiveEMICalculatorTest.java`

### 1.1 V-01 — `EMB.testGenerate` (the calibration vector)

Helper column order claimed by the plan `(periodNumber, fromDate, dueDate, principal, interest, fee, penalty, totalDue, outstandingBalance, totalOutstandingBalance)` — **confirmed** at `EMB:100-102`. Disbursement overload confirmed at `EMB:95-98`.

| Value | Plan | Source | Cite | Status |
|---|---|---|---|---|
| `MathContext` | precision 12, `HALF_UP` | `new MathContext(12, RoundingMode.HALF_UP)` | `EMB:44` | TRANSCRIBED-OK |
| `currency` | `CurrencyData("usd","US Dollar",2,null,"usd","$")` | identical | `EMB:47` | TRANSCRIBED-OK |
| `startDate` / `disbursementDate` | `2024-01-01` / `2024-01-01` | identical | `EMB:48`, `:49` | TRANSCRIBED-OK |
| `disbursedAmount` | `100` | `BigDecimal.valueOf(100)` | `EMB:50` | TRANSCRIBED-OK |
| `noRepayments` / `repaymentFrequency` / type | `6` / `1` / `"MONTHS"` | identical | `EMB:52`,`:53`,`:54` | TRANSCRIBED-OK |
| `downPaymentPercentage` | `BigDecimal.ZERO` → disabled | identical, `isDownPaymentEnabled` derived at `:56` | `EMB:55-56` | TRANSCRIBED-OK |
| `annualNominalInterestRate` | `7.0` | `BigDecimal.valueOf(7.0)` | `EMB:57` | TRANSCRIBED-OK |
| `daysInMonth` / `daysInYear` | `DAYS_30` / `DAYS_360` | identical | `EMB:58`,`:59` | TRANSCRIBED-OK |
| `installmentAmountInMultiplesOf` / `fixedLength` | `null` / `null` | identical | `EMB:60`,`:61` | TRANSCRIBED-OK |
| `interestRecognitionOnDisbursementDate` | `false` | identical | `EMB:62` | TRANSCRIBED-OK |
| `daysInYearCustomStrategy` | `null` | identical | `EMB:63` | TRANSCRIBED-OK |
| `interestMethod` | `DECLINING_BALANCE` | identical | `EMB:64` | TRANSCRIBED-OK |
| `allowPartialPeriodInterestCalculation` | `true` | identical | `EMB:65` | TRANSCRIBED-OK |
| `allowFullTermForTranche` | `false` (positional last ctor arg) | trailing `false` in ctor call | `EMB:70` | TRANSCRIBED-OK |
| `getLoanTermInDays()` | `182` | `assertEquals(182, …)` | `EMB:74` | TRANSCRIBED-OK |
| `getTotalDisbursedAmount()` | `100.00` → `10000` | `100.00` | `EMB:75` | TRANSCRIBED-OK |
| `getTotalInterestAmount()` | `2.05` → `205` | `2.05` | `EMB:76` | TRANSCRIBED-OK |
| `getTotalRepaymentAmount()` | `102.05` → `10205` | `102.05` | `EMB:77` | TRANSCRIBED-OK |
| `getPeriods().size()` | `7` | `7` | `EMB:79` | TRANSCRIBED-OK |
| Period 0 | `2024-01-01`/`2024-01-01`, principal `100.0`, outstanding `100.0` | identical | `EMB:80` | TRANSCRIBED-OK |
| P1 | `16.43, 0.58, 0.0, 0.0, 17.01, 83.57, 85.04` | identical | `EMB:81-82` | TRANSCRIBED-OK |
| P2 | `16.52, 0.49, 0.0, 0.0, 17.01, 67.05, 68.03` | identical | `EMB:83-84` | TRANSCRIBED-OK |
| P3 | `16.62, 0.39, 0.0, 0.0, 17.01, 50.43, 51.02` | identical | `EMB:85-86` | TRANSCRIBED-OK |
| P4 | `16.72, 0.29, 0.0, 0.0, 17.01, 33.71, 34.01` | identical | `EMB:87-88` | TRANSCRIBED-OK |
| P5 | `16.81, 0.20, 0.0, 0.0, 17.01, 16.90, 17.00` | identical | `EMB:89-90` | TRANSCRIBED-OK |
| P6 | `16.90, 0.10, 0.0, 0.0, 17.00, 0.0, 0.0` | identical | `EMB:91-92` | TRANSCRIBED-OK |

**Second attestation re-verified.** `fineract-progressive-loan-embeddable-schedule-generator/README.md:46-63` documents the sample stdout: `Loan Term in Days: 182`, `Total Disbursed Amount: 100.00`, `Total Interest Amount: 2.05`, `Total Repayment Amount: 102.05`, and per-period `16.43 / 0.58 / 17.01` … `16.90 / 0.10 / 17.00` with balances `83.57, 67.05, 50.43, 33.71, 16.90, 0.00`. **Confirmed twice-attested.** One caveat — see defect **D8**: the README block carries no `totalOutstandingBalance` column, so it attests 9 of the 10 columns, not all 10.

**Third, previously unnoticed attestation — see D7.** `EMI:3259-3265` (`test_leap_year_only_actual_no_effect_on_360_loan`) drives the same product shape (`100.0`, rate `7.0`, `DAYS_360`/`DAYS_30`, 6 monthly periods from `2024-01-01`) through `ProgressiveEMICalculator` directly and asserts `17.01 / 0.58 / 16.43 / 83.57`, `0.49 / 16.52 / 67.05`, `0.39 / 16.62 / 50.43`, `0.29 / 16.72 / 33.71`, `0.2 / 16.81 / 16.90`, `17.00 / 0.1 / 16.9 / 0.0` — **identical per-period figures to V-01**, from a different entry point and under the class `mc` of `(12, HALF_EVEN)` rather than V-01's `(12, HALF_UP)`. The plan does not note this. It materially strengthens V-01 as the calibration anchor and adds a free rounding-mode-insensitivity data point.

**Vector value count: 69. All TRANSCRIBED-OK.**

### 1.2 V-02 — `LSG.testGenerateLoanSchedule`

Helper `checkRepaymentPeriod(period, periodNumber, fromDate, dueDate, principalDue, interestDue, totalDue, outstandingBalance)` confirmed at `LSG:149-151`; `checkDisbursementPeriod` at `LSG:140-141`.

| Value | Plan | Source | Cite | Status |
|---|---|---|---|---|
| `MathContext` | precision 12, `HALF_EVEN` | `new MathContext(12, RoundingMode.HALF_EVEN)` | `LSG:57` | TRANSCRIBED-OK |
| currency | `ApplicationCurrency("USD","USD",2,1,"USD","$")`, dp 2, inMultiplesOf 1 | identical | `LSG:48-49` | TRANSCRIBED-OK |
| `scheduleGenerationStartDate` | `2024-01-01` | `LocalDate.of(2024, 1, 1)` | `LSG:65` | TRANSCRIBED-OK |
| `disbursementAmount` | `192.22` → `19222` | `BigDecimal.valueOf(192.22)` | `LSG:50` | TRANSCRIBED-OK |
| `disbursementDate` | `2024-01-15` | identical | `LSG:56` | TRANSCRIBED-OK |
| `numberOfRepayments` | `6` | identical | `LSG:53` | TRANSCRIBED-OK |
| freq / type | `1` / `"MONTHS"` | identical | `LSG:54-55` | TRANSCRIBED-OK |
| rate | `9.99` | `BigDecimal.valueOf(9.99)` | `LSG:52` | TRANSCRIBED-OK |
| downPaymentEnabled, `DAYS_30`/`DAYS_360`, three `null`s, `interestRecognition=false`, `daysInYearCustomStrategy=null` | all as stated | all present in the ctor call | `LSG:67` | TRANSCRIBED-OK |
| `interestMethod`, `allowPartialPeriod`/`allowFullTermForTranche` | `DECLINING_BALANCE`, `true`/`false` | identical | `LSG:68` | TRANSCRIBED-OK |
| `getPeriods().size()` | `7` | `7` | `LSG:77` | TRANSCRIBED-OK |
| Disb. period | `2024-01-15`, `192.22`, `192.22` | identical | `LSG:79-80` | TRANSCRIBED-OK |
| P1 | `2024-01-01`→`2024-02-01`, `31.97, 0.88, 32.85, 160.25` | identical | `LSG:82-84` | TRANSCRIBED-OK |
| P2 | `31.52, 1.33, 32.85, 128.73` | identical | `LSG:85-87` | TRANSCRIBED-OK |
| P3 | `31.78, 1.07, 32.85, 96.95` | identical | `LSG:88-90` | TRANSCRIBED-OK |
| P4 | `32.04, 0.81, 32.85, 64.91` | identical | `LSG:91-93` | TRANSCRIBED-OK |
| P5 | `32.31, 0.54, 32.85, 32.60` | identical | `LSG:94-96` | TRANSCRIBED-OK |
| P6 | `32.60, 0.27, 32.87, 0` | identical (`BigDecimal.ZERO`) | `LSG:97-98` | TRANSCRIBED-OK |

**Vector value count: 40. All TRANSCRIBED-OK.**

### 1.3 V-03 — `LSG.testGenerateLoanScheduleWithDownPayment`

`checkDownPaymentPeriod(period, periodNumber, fromDate, dueDate, principalDue, totalDue, outstandingBalance)` confirmed at `LSG:161-163` — the plan's rendering of the down-payment row as (principal, totalDue, outstanding) is the correct column order.

| Value | Plan | Source | Cite | Status |
|---|---|---|---|---|
| `disbursementAmount` | `100` → `10000` | `DISBURSEMENT_AMOUNT_100 = BigDecimal.valueOf(100)` | `LSG:51` | TRANSCRIBED-OK |
| `downPaymentPercentage` | `25` | `DOWN_PAYMENT_PORTION = BigDecimal.valueOf(25)` | `LSG:58` | TRANSCRIBED-OK |
| `disbursementDate`, downPaymentEnabled `true` | `2024-01-01`, `true` | identical | `LSG:104`, `:105` | TRANSCRIBED-OK |
| period count | `8` | `8` | `LSG:115` | TRANSCRIBED-OK |
| Disb. period | `2024-01-01`, `100`, `100` | identical | `LSG:117-118` | TRANSCRIBED-OK |
| DP period #1 | `2024-01-01`/`2024-01-01`, `25.0`, `25.0`, `75.0` | identical | `LSG:119-120` | TRANSCRIBED-OK |
| P2 | `12.25, 0.62, 12.87, 62.75` | identical | `LSG:121-123` | TRANSCRIBED-OK |
| P3 | `12.35, 0.52, 12.87, 50.40` | identical | `LSG:124-126` | TRANSCRIBED-OK |
| P4 | `12.45, 0.42, 12.87, 37.95` | identical | `LSG:127-129` | TRANSCRIBED-OK |
| P5 | `12.55, 0.32, 12.87, 25.40` | identical | `LSG:130-132` | TRANSCRIBED-OK |
| P6 | `12.66, 0.21, 12.87, 12.74` | identical | `LSG:133-135` | TRANSCRIBED-OK |
| P7 | `12.74, 0.11, 12.85, 0` | identical (`BigDecimal.ZERO`) | `LSG:136-137` | TRANSCRIBED-OK |

**Vector value count: 45. All TRANSCRIBED-OK.**

### 1.4 `EMI` shared fixtures and helper column orders (§2.4, §2.5 preamble)

| Claim | Source | Cite | Status |
|---|---|---|---|
| class `mc` = precision 12, `HALF_EVEN` | `private static MathContext mc = new MathContext(12, RoundingMode.HALF_EVEN);` | `EMI:76` | TRANSCRIBED-OK |
| `currency = CurrencyData("USD","USD",2,1,"$","USD")` | identical | `EMI:79` | TRANSCRIBED-OK |
| `MoneyHelper.getRoundingMode()` mocked → `HALF_EVEN` | identical | `EMI:97` | TRANSCRIBED-OK |
| `MoneyHelper.getMathContext()` mocked → `MathContext(12, HALF_EVEN)` | identical | `EMI:98` | TRANSCRIBED-OK |
| `isInterestRecognitionOnDisbursementDate()` `false` | identical | `EMI:109` | TRANSCRIBED-OK |
| `getDaysInYearCustomStrategy()` `null` | identical | `EMI:110` | TRANSCRIBED-OK |
| `getInterestMethod()` `DECLINING_BALANCE` | identical | `EMI:112` | TRANSCRIBED-OK |
| `getInterestCalculationPeriodMethod()` `DAILY` | identical | `EMI:113` | TRANSCRIBED-OK |
| `isAllowPartialPeriodInterestCalculation()` `true` | identical | `EMI:114` | TRANSCRIBED-OK |
| grace on principal / interest `0` / `0` | identical | `EMI:115-116` | TRANSCRIBED-OK |
| 7-arg order `(model, repaymentIdx, interestIdx, emi, rateFactor, interestDue, principalDue, outstanding)` | matches declaration | `EMI:5211-5213` | TRANSCRIBED-OK |
| 8-arg order `(…, interestDue, interestDueCumulated, principalDue, outstanding)` | matches declaration | `EMI:5230-5232` | TRANSCRIBED-OK |
| 6-arg order `(model, repaymentIdx, emi, interestDueCumulated, principalDue, outstanding, fullyRepaid)` | matches declaration | `EMI:5218-5220` | TRANSCRIBED-OK |
| `checkDailyInterest(model, dueDate, startDay, dayOffset, dailyIncrement, cumulative)` | matches declaration | `EMI:5191-5199` | TRANSCRIBED-OK |
| rate-factor compared after `setScale(MoneyHelper.getMathContext().getPrecision(), MoneyHelper.getRoundingMode())` | `applyMathContext` applied to `rateFactor` only | `EMI:5241`, `:5256-5258` | TRANSCRIBED-OK |
| `toMoney(double)` uses 2-arg `Money.of(currency, BigDecimal)` | `Money.of(currency, BigDecimal.valueOf(value))` | `EMI:5260-5262` | TRANSCRIBED-OK |
| both helper families convert to `double` before `assertEquals` | confirmed | `EMI:5248-5254`, `EMB:120-122` | TRANSCRIBED-OK |

The plan's warning that a transcribed rate factor is a **12-dp rounding of the engine's value, not the engine's value** is correct and is the single most valuable caveat in the document. `applyMathContext` is applied *only* to `rateFactor` (`EMI:5241`), not to `calculatedDueInterest` (`:5242`) — the plan does not overclaim here.

### 1.5 V-04 — `EMI.test_disbursedAmt100_dayInYears360_daysInMonth30_repayEvery1Month` (`EMI:298`)

Inputs: rate `9.4822` `EMI:308` ✓; `DAYS_360`/`DAYS_30` `:312-313` ✓; `MONTHS`/`1` `:314-315` ✓; multiplesOf `null` `:309` ✓; currency `:316` ✓; six periods `2024-01-01 … 2024-07-01` `:301-306` ✓; disbursement `toMoney(100.0)` at `2024-01-01` `:321-322` ✓. All **TRANSCRIBED-OK**.

| idx | emi | dueInterest | duePrincipal | outstanding | cite | status |
|---:|---:|---:|---:|---:|---|---|
| 0 | `17.13` | `0.79` | `16.34` | `83.66` | `EMI:324-325` | TRANSCRIBED-OK |
| 1 | `17.13` | `0.66` | `16.47` | `67.19` | `EMI:326` | TRANSCRIBED-OK |
| 2 | `17.13` | `0.53` | `16.60` | `50.59` | `EMI:327` | TRANSCRIBED-OK |
| 3 | `17.13` | `0.40` | `16.73` | `33.86` | `EMI:328` | TRANSCRIBED-OK |
| 4 | `17.13` | `0.27` | `16.86` | `17.0` | `EMI:329` | TRANSCRIBED-OK |
| 5 | `17.13` | `0.13` | `17.00` | `0.0` | `EMI:330` | TRANSCRIBED-OK |

Non-money intermediates, all **TRANSCRIBED-OK** as exact decimal strings: `(0,0)` rateFactor `0.0` / calc `0.0`; `(0,1)` rateFactor `0.007901833333` / calc `0.790183333301`; periods 1–5 rateFactor `0.007901833333` with calc `0.66106737664`, `0.530924181643`, `0.399753748317`, `0.267556076655`, `0.134331166661` — all literally at `EMI:325-330`.

**Vector value count: 38. All TRANSCRIBED-OK.**

### 1.6 V-05 — `EMI.test_disbursedAmt1000_NoInterest_repayEvery1Month` (`EMI:1082`) — 0 % rate

Inputs: `BigDecimal.ZERO` `:1090` ✓; `ACTUAL`/`ACTUAL` `:1094-1095` ✓; `MONTHS`/`1` `:1096-1097` ✓; multiplesOf `null` `:1091` ✓; four periods `2024-01-01 … 2024-05-01` `:1084-1088` ✓; `toMoney(1000.0)` at `2024-01-01` `:1103-1104` ✓.

| idx | emi | interestDue | duePrincipal | outstanding | rateFactor | cite | status |
|---:|---:|---:|---:|---:|---|---|---|
| 0 | `250.0` | `0.0` | `250.0` | `750.0` | `0.0` | `EMI:1106` | TRANSCRIBED-OK |
| 1 | `250.0` | `0.0` | `250.0` | `500.0` | `0.0` | `EMI:1107` | TRANSCRIBED-OK |
| 2 | `250.0` | `0.0` | `250.0` | `250.0` | `0.0` | `EMI:1108` | TRANSCRIBED-OK |
| 3 | `250.0` | `0.0` | `250.0` | `0.0` | `0.0` | `EMI:1109` | TRANSCRIBED-OK |

**Vector value count: 20. All TRANSCRIBED-OK.** The plan's caveat that 0 % is pinned only for an evenly divisible principal is correct — `100000 / 4` is exact.

### 1.7 V-06 — `EMI.test_360_30_repayment_schedule_disbursement_month_end` (`EMI:2215`)

⚠ Local `MathContext(12, RoundingMode.HALF_UP)` shadow — **confirmed literally at `EMI:2216`**. The plan flags it. **TRANSCRIBED-OK.**

Inputs: rate `9.99` `:2225` ✓; `DAYS_360`/`DAYS_30` `:2229-2230` ✓; `MONTHS`/`1` `:2231-2232` ✓; multiplesOf `null` `:2226` ✓; `toMoney(2450.0)` at `2023-10-31` `:2238-2241` ✓; period boundaries supplied as input literals `2023-10-31 → 2023-11-30 → 2023-12-31 → 2024-01-31 → 2024-02-29 → 2024-03-31 → 2024-04-30` at `:2217-2223` ✓.

| idx | emi | interestDue | duePrincipal | outstanding | cite | status |
|---:|---:|---:|---:|---:|---|---|
| 0 | `420.31` | `20.40` | `399.91` | `2050.09` | `EMI:2243` | TRANSCRIBED-OK |
| 1 | `420.31` | `17.07` | `403.24` | `1646.85` | `EMI:2244` | TRANSCRIBED-OK |
| 2 | `420.31` | `13.71` | `406.60` | `1240.25` | `EMI:2245` | TRANSCRIBED-OK |
| 3 | `420.31` | `10.33` | `409.98` | `830.27` | `EMI:2246` | TRANSCRIBED-OK |
| 4 | `420.31` | `6.91` | `413.40` | `416.87` | `EMI:2247` | TRANSCRIBED-OK |
| 5 | `420.34` | `3.47` | `416.87` | `0.00` | `EMI:2248` | TRANSCRIBED-OK |

The plan's "crucial limitation" — that the Jan-31 → Feb-29 → Mar-31 sequence here is an *input literal*, not a *derived output* — is **correct and independently confirmed**: `EMI:2217-2223` constructs the boundaries via `periodData(...)` and hands them to `generatePeriodInterestScheduleModel` at `:2235-2236`.

**Vector value count: 31. All TRANSCRIBED-OK.**

### 1.8 V-07 — `EMI.test_actual_actual_repayment_schedule_disbursement_month_end` (`EMI:2326`)

⚠ Local `MathContext(12, RoundingMode.HALF_UP)` — **confirmed at `EMI:2327`**. Flagged by the plan. **TRANSCRIBED-OK.**

Inputs: rate `45.0` `:2336` ✓; `ACTUAL`/`ACTUAL` `:2340-2341` ✓; `MONTHS`/`1` `:2342-2343` ✓; multiplesOf `null` `:2337` ✓; `toMoney(245000.0)` at `2023-10-31` `:2349-2352` ✓; same six literal boundaries `:2328-2334` ✓.

| idx | emi | interestDue | duePrincipal | outstanding | cite | status |
|---:|---:|---:|---:|---:|---|---|
| 0 | `46343.27` | `9061.64` | `37281.63` | `207718.37` | `EMI:2354` | TRANSCRIBED-OK |
| 1 | `46343.27` | `7938.83` | `38404.44` | `169313.93` | `EMI:2355` | TRANSCRIBED-OK |
| 2 | `46343.27` | `6453.36` | `39889.91` | `129424.02` | `EMI:2356` | TRANSCRIBED-OK |
| 3 | `46343.27` | `4614.71` | `41728.56` | `87695.46` | `EMI:2357` | TRANSCRIBED-OK |
| 4 | `46343.27` | `3342.49` | `43000.78` | `44694.68` | `EMI:2358` | TRANSCRIBED-OK |
| 5 | `46343.25` | `1648.57` | `44694.68` | `0.00` | `EMI:2359` | TRANSCRIBED-OK |

"Largest principal carrying a full literal schedule" — **independently confirmed**: the maximum `toMoney(…)` argument anywhere in `EMI` is `245000.0`; the sorted distinct set tops out `5000.0, 7500.0, 10000.0, 15000.0, 245000.0`.

**Vector value count: 31. All TRANSCRIBED-OK.**

### 1.9 V-08 — `EMI.test_dailyInterest_disbursedAmt1000_…_repayIn1Month` (`EMI:1274`)

Inputs: rate `7.0` `:1280` ✓; `DAYS_360`/`DAYS_30` `:1284-1285` ✓; `MONTHS`/`1` `:1286-1287` ✓; multiplesOf `null` `:1281` ✓; **exactly one** period `2024-01-01 → 2024-02-01` `:1278` ✓; `toMoney(1000.0)` at `2024-01-01` `:1293-1294` ✓; class `mc` (12, `HALF_EVEN`) — no shadow present, confirmed.

Schedule row `EMI:1296-1297`: emi `1005.83`, dueInterest `5.83`, duePrincipal `1000.0`, outstanding `0.0`; sub-period `(0,1)` rateFactor `0.005833333333`, calc `5.833333333`. All **TRANSCRIBED-OK**.

**All 31 daily-accrual rows re-read at `EMI:1302-1332` and matched one by one** against the plan's four-column layout:

| day | Δ / cum (plan) | source | status | | day | Δ / cum (plan) | source | status |
|---:|---|---|---|---|---:|---|---|---|
| 1 | 19 / 19 | `0.19, 0.19` | OK | | 17 | 19 / 320 | `0.19, 3.20` | OK |
| 2 | 19 / 38 | `0.19, 0.38` | OK | | 18 | 19 / 339 | `0.19, 3.39` | OK |
| 3 | 18 / 56 | `0.18, 0.56` | OK | | 19 | 19 / 358 | `0.19, 3.58` | OK |
| 4 | 19 / 75 | `0.19, 0.75` | OK | | 20 | 18 / 376 | `0.18, 3.76` | OK |
| 5 | 19 / 94 | `0.19, 0.94` | OK | | 21 | 19 / 395 | `0.19, 3.95` | OK |
| 6 | 19 / 113 | `0.19, 1.13` | OK | | 22 | 19 / 414 | `0.19, 4.14` | OK |
| 7 | 19 / 132 | `0.19, 1.32` | OK | | 23 | 19 / 433 | `0.19, 4.33` | OK |
| 8 | 19 / 151 | `0.19, 1.51` | OK | | 24 | 19 / 452 | `0.19, 4.52` | OK |
| 9 | 18 / 169 | `0.18, 1.69` | OK | | 25 | 18 / 470 | `0.18, 4.7` | OK |
| 10 | 19 / 188 | `0.19, 1.88` | OK | | 26 | 19 / 489 | `0.19, 4.89` | OK |
| 11 | 19 / 207 | `0.19, 2.07` | OK | | 27 | 19 / 508 | `0.19, 5.08` | OK |
| 12 | 19 / 226 | `0.19, 2.26` | OK | | 28 | 19 / 527 | `0.19, 5.27` | OK |
| 13 | 19 / 245 | `0.19, 2.45` | OK | | 29 | 19 / 546 | `0.19, 5.46` | OK |
| 14 | 18 / 263 | `0.18, 2.63` | OK | | 30 | 19 / 565 | `0.19, 5.65` | OK |
| 15 | 19 / 282 | `0.19, 2.82` | OK | | 31 | 18 / 583 | `0.18, 5.83` | OK |
| 16 | 19 / 301 | `0.19, 3.01` | OK | | | | | |

The plan's note that source writes `4.7` at `EMI:1326` (scale 1) and `3.20` at `EMI:1318` (scale 2), both reinterpreting exactly to `470` and `320`, is **correct**.

**Vector value count: 68. All TRANSCRIBED-OK.**

### 1.10 V-09 — `EMI.test_sameAsRepayment_month_repay_every_1_periods_24` (`EMI:3860`) — 24 periods, FLAT

Nested `@BeforeEach` overrides — `InterestMethod.FLAT` `:3609` ✓; `ACTUAL`/`ACTUAL` `:3611-3612` ✓; `SAME_AS_REPAYMENT_PERIOD` `:3613-3614` (the literal is on `:3614`; the plan cites `3614` and the range `3602-3617` — accurate) ✓.

Inputs: rate `12.0` `:3862` ✓; `MONTHS` `:3866`, `numberOfRepayments = 24` `:3867`, repayEvery `1` `:3868` ✓; `allowFullTermForTranche = false` `:3869` ✓; multiplesOf `null` `:3872` ✓; periods via `generateExpectedRepaymentPeriods(disbursementDate)` `:3871` ✓; two disbursements `toMoney(7500.0)` and `toMoney(2500.0)` `:3877-3878` ✓.

| Claim | Source | Cite | Status |
|---|---|---|---|
| idx 0–22 each emi `516.67`, interest `100.00`, principal `416.67` | all 23 lines carry exactly `516.67, 100.00, 416.67` | `EMI:3880-3902` | TRANSCRIBED-OK |
| outstanding descending `9583.33`, `9166.66`, …, `416.59` | `9583.33` `:3880`, `9166.66` `:3881`, `416.59` `:3902` | `EMI:3880-3902` | TRANSCRIBED-OK |
| idx 23 emi `516.59`, interest `100.00`, principal `416.59`, outstanding `0.00` | identical | `EMI:3903` | TRANSCRIBED-OK |
| third disbursement `1000.0` at `disbursementDate.plusMonths(3).plusDays(4)`, left unresolved | `emiCalculator.addDisbursement(interestSchedule, disbursementDate.plusMonths(3).plusDays(4), toMoney(1000.0));` | `EMI:3905` | TRANSCRIBED-OK |

Leaving the third-disbursement date as the **source expression** rather than resolving it to a calendar date is exactly the right discipline — resolving it would have been a derived value. Correctly *not* transcribing the 24 re-asserted rows at `EMI:3907-3930` and saying so is likewise honest.

**Vector value count: 11 distinct asserted literals. All TRANSCRIBED-OK.**

### 1.11 V-10 — `EMI.LeapYear366OnlyForPeriodWith29thOfFebruaryTest` (`EMI:2976`)

Seven-test enumeration **independently confirmed**: `test_leap_year_only_actual_for_loan_S1` `:2983`, `S2` `:3024`, `S3` `:3060`, `S4` `:3101`, `S5` `:3141`, `test_feb29_period_only_cross_year_quarterly_period_containing_feb29` `:3183`, `test_leap_year_only_actual_no_effect_on_360_loan` `:3231`. Seven. ✓

S1 inputs: rate `9.482` `:2992` ✓; `ACTUAL` `:2996`, `FEB_29_PERIOD_ONLY` `:2997-2998`, `ACTUAL` `:2999` ✓; `MONTHS`/`1` `:3000-3001` ✓; `allowFullTermForTranche=false` `:3003` ✓; multiplesOf `null` `:2993` ✓; six periods `2023-12-12 … 2024-06-12` `:2984-2990` ✓; `toMoney(10000.0)` at `2023-12-12` `:3008-3009` ✓; class `mc` — no local shadow in S1, confirmed.

| idx | emi | interestDue | duePrincipal | outstanding | cite | status |
|---:|---:|---:|---:|---:|---|---|
| 0 | `1713.21` | `80.53` | `1632.68` | `8367.32` | `EMI:3011` | TRANSCRIBED-OK |
| 1 | `1713.21` | `67.38` | `1645.83` | `6721.49` | `EMI:3012` | TRANSCRIBED-OK |
| 2 | `1713.21` | `50.50` | `1662.71` | `5058.78` | `EMI:3013` | TRANSCRIBED-OK |
| 3 | `1713.21` | `40.74` | `1672.47` | `3386.31` | `EMI:3014` | TRANSCRIBED-OK |
| 4 | `1713.21` | `26.39` | `1686.82` | `1699.49` | `EMI:3015` | TRANSCRIBED-OK |
| 5 | `1713.18` | `13.69` | `1699.49` | `0.00` | `EMI:3016` | TRANSCRIBED-OK |

S3 differential claim: principal `245000.0`, rate `45.00`, `FEB_29_PERIOD_ONLY`, period-0 emi `46348.39` vs V-07's `46343.27` — **confirmed** at `EMI:3069`, `:3085`, `:3088` against `EMI:2336`, `:2349`, `:2354`. The (V-07, S3) pair is a genuine single-flag differential. **TRANSCRIBED-OK.**

⚠ **The blanket sentence "All set `DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY`" is FALSE** — see defect **D2**.

**Vector value count: 25. All TRANSCRIBED-OK.**

### 1.12 Equal-amortization primitives (`EMI.EqualAmortizationValue`, `EMI:5099`)

| test | amount | installments | multiplesOf | asserted values | cite | status |
|---|---|---:|---|---|---|---|
| `test_AmortizationTotalIsLessThanInstallmentNumber` | `0.04` | `6` | `null` | `0.01, 0.01, 0.01, 0.01, 0.0, 0.0` | `EMI:5104-5111` | TRANSCRIBED-OK |
| `test_AmortizationIsJustBiggerThanInstallmentNumber` | `0.07` | `6` | `null` | `0.01, 0.01, 0.01, 0.01, 0.01, 0.02` | `EMI:5117-5124` | TRANSCRIBED-OK |
| `test_AmortizationNonEdgeCase` | `0.59` | `6` | `null` | `0.1, 0.1, 0.1, 0.1, 0.1, 0.09` | `EMI:5130-5137` | TRANSCRIBED-OK |

Signature `calculateEqualAmortizationValues(Money, int, Integer, MonetaryCurrency)` confirmed; third argument is `null` in all three. **Vector value count: 21. All TRANSCRIBED-OK.**

### 1.13 Rate-factor and `fn` primitives (§2.7)

| Vector | Plan | Source | Cite | Status |
|---|---|---|---|---|
| `interestRate` | `0.094822` | `BigDecimal.valueOf(0.094822)` | `EMI:82` | TRANSCRIBED-OK |
| six monthly periods | built from `2024-01-01` | `createPeriod(1..6, …)` | `EMI:88-94` | TRANSCRIBED-OK |
| `DAYS_365`+`ACTUAL` (test at `:129`) | `0.008053375342, 0.007533802740, 0.008053375342, 0.007793589041, 0.008053375342, 0.007793589041` | identical, character for character | `EMI:133-134` | TRANSCRIBED-OK |
| `ACTUAL`+`ACTUAL` (test at `:144`) | `0.008031371585, 0.007513218579, 0.008031371585, 0.007772295082, 0.008031371585, 0.007772295082` | identical | `EMI:149-150` | TRANSCRIBED-OK |
| `fn` recurrence (test at `:160`) | `1.00000000000, 2.00753380274, 3.02370122596, 4.04726671069, 5.07986086861, 6.11945121660` | identical | `EMI:165-166` | TRANSCRIBED-OK |

These compare `.toString()` (`EMI:139`, `:155`), so the plan's claim that they pin **scale and digits exactly** is correct — including the trailing zero in `0.007533802740` and the 11-dp form `1.00000000000`, both of which the plan reproduced faithfully rather than normalising. That is precisely the discipline being audited for.

**Vector value count: 19. All TRANSCRIBED-OK.**

### 1.14 Transcription audit — totals

| Status | Count |
|---|---:|
| **TRANSCRIBED-OK** | **418** |
| ALTERED | 0 |
| NOT-IN-SOURCE | 0 |
| MISCITED (vector values) | 0 |

**No synthesised vector. No value in the plan that is not literally in the cited source. No value off by a rounding step.** Every "obviously right" number I probed for — the kind an analyst is most tempted to fill in — turned out to be a literal: `17.13` repeated six times in V-04, the `0.0` rate factors in V-05, the exact `0.00` terminal balances, the odd `4.7`/`3.20` scale mismatch in V-08. The one place a derived value would have been easiest and most defensible (resolving `disbursementDate.plusMonths(3).plusDays(4)` in V-09) is explicitly left unresolved.

---

## 2. Minor-unit conversion check

Method: every `` `literal` → `integer` `` pair in the document was extracted mechanically and re-derived with exact integer/decimal arithmetic (`Decimal(literal).scaleb(2)`), with a hard guard rejecting any literal of scale > 2 and any inexact result.

| Check | Result |
|---|---|
| Paired conversions extracted and re-derived | **230** |
| Exact scale-2 reinterpretations | **230 / 230** |
| List-form conversions (§2.6, three rows: `0.01→1`, `0.0→0`, `0.02→2`, `0.1→10`, `0.09→9`) | **18 / 18** exact, verified by hand |
| Bare minor-unit values not written in `→` form (V-08 daily table, 62 values) | **62 / 62** exact |
| **Total conversions verified** | **310 / 310 exact** |
| Literals of scale > 2 wrongly treated as money | **0** |
| Conversions performed by floating-point multiply/divide | **0** |
| `float` / `double` anywhere in the plan as a value representation | **0** |

Every occurrence of `float`/`double` in the document (lines 306, 320-321, 688, 743, 781-783, 814-821) is either a prohibition (`never via double`, `L × 100 as a float64 is prohibited`, `so is strconv.ParseFloat`, `never float32/float64`) or an accurate description of Fineract's own *test* convention which the plan explicitly refuses to reproduce. §5.4 correctly identifies that Fineract's `toDouble` comparison makes the corpus assertions weaker than they look, and mandates `BigDecimal.toPlainString()` in the harness. §5.3 correctly excludes rate factors and unrounded interest intermediates from minor-unit storage, keeping them as exact decimal strings. **Conversion audit: CLEAN.**

Spot-checks on the trickiest reinterpretations, all correct: `100` (scale 0) → `10000`; `4.7` (scale 1) → `470`; `245000.0` (scale 1) → `24500000`; `17.0` (scale 1) → `1700`; `16.9` (scale 1) → `1690`; `0.20` (scale 2) → `20`; `0.09` → `9`.

---

## 3. Principals-sum invariant — independent recomputation

Each sum recomputed from the **source literals**, not from the plan's minor-unit column, in integer arithmetic.

| Vector | Principals (minor units) | Sum | Expected | Holds? |
|---|---|---:|---:|---|
| V-01 | 1643+1652+1662+1672+1681+1690 | **10000** | 10000 (`100.00`) | ✅ |
| V-01 interests | 58+49+39+29+20+10 | **205** | 205 (`2.05`) | ✅ |
| V-01 totals | 1701×5 + 1700 | **10205** | 10205 (`102.05`) | ✅ |
| V-02 | 3197+3152+3178+3204+3231+3260 | **19222** | 19222 (`192.22`) | ✅ |
| V-02 interests | 88+133+107+81+54+27 | **490** | — | ✅ |
| V-02 totals | 3285×5 + 3287 = 19712 | **19712** | 19222+490 = 19712 | ✅ |
| V-03 | 2500 + (1225+1235+1245+1255+1266+1274 = 7500) | **10000** | 10000 (`100`) | ✅ |
| V-04 | 1634+1647+1660+1673+1686+1700 | **10000** | 10000 (`100.0`) | ✅ |
| V-05 | 25000×4 | **100000** | 100000 (`1000.0`) | ✅ |
| V-06 | 39991+40324+40660+40998+41340+41687 | **245000** | 245000 (`2450.0`) | ✅ |
| V-07 | 3728163+3840444+3988991+4172856+4300078+4469468 | **24500000** | 24500000 (`245000.0`) | ✅ |
| V-08 | 100000 (single installment) | **100000** | 100000 (`1000.0`) | ✅ |
| V-08 daily cum. | day-31 cumulative `583` | **583** | period `dueInterest` `583` | ✅ |
| V-09 | 41667×23 + 41659 | **1000000** | 750000+250000 = 1000000 | ✅ |
| V-10 S1 | 163268+164583+166271+167247+168682+169949 | **1000000** | 1000000 (`10000.0`) | ✅ |
| §2.6 splits | 1+1+1+1+0+0 / 1×5+2 / 10×5+9 | **4 / 7 / 59** | 4 / 7 / 59 | ✅ |

**All 16 invariant checks hold. No failed invariant. The plan's claim that it checked them, and that all pass, is TRUE.** Note V-02's totals invariant additionally confirms `totalRepayment = principal + interest` at the schedule level, which the plan asserts but did not have to.

---

## 4. Pinning audit

### 4.1 `MathContext` on every capture row

| Row | Parameter `MathContext` | Precision explicit? | Rounding mode explicit? | Verdict |
|---|---|---|---|---|
| C-00 | stated inline: "precision 12, `RoundingMode.HALF_UP` — pinned explicitly, never defaulted" (§4.0) | ✅ | ✅ | PINNED |
| C-01 | attestation run, no vectors produced; logs "precision AND rounding mode, both logged" | ✅ | ✅ | PINNED (n/a) |
| C-02 … C-10 | §4.2 preamble binds every run: "**`MathContext` explicitly pinned (precision 12, `RoundingMode.HALF_UP`, matching C-00 unless the run says otherwise)**" | ✅ | ✅ | PINNED |

No row in the C-02…C-10 table overrides the `MathContext`, so the section-level binding governs all nine. **No unpinned `MathContext` on any capture row.** The §4.2 preamble also pins currency, `interestMethod`, `allowPartialPeriodInterestCalculation`, `interestRecognitionOnDisbursementDate`, `daysInYearCustomStrategy`, `fixedLength`, `allowFullTermForTranche` and down-payment for every row — a genuinely complete input set.

One structural weakness, recorded as **D9**: the binding is stated once for the table rather than restated per row. That is adequate as written but brittle if any future row is appended without re-reading the preamble. Required change #5 makes it per-row.

### 4.2 The `MoneyHelper` hidden second `MathContext` — claim **VERIFIED**

| Plan claim | Source | Verdict |
|---|---|---|
| `MoneyHelper.PRECISION = 19` in production | `public static final int PRECISION = 19;` — `fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/MoneyHelper.java:35` | ✅ **VERIFIED** |
| production context is `new MathContext(PRECISION, tenantRoundingMode)` | `return mathContextCache.computeIfAbsent(tenantId, k -> new MathContext(PRECISION, getRoundingMode()));` — `MoneyHelper.java:93`, method at `:91` | ✅ **VERIFIED** |
| unit tests mock it to **precision 12** | `moneyHelper.when(MoneyHelper::getMathContext).thenReturn(new MathContext(12, RoundingMode.HALF_EVEN));` — `EMI:98` | ✅ **VERIFIED** |
| `Money.of(currency, amount)` 2-arg silently reaches `MoneyHelper.getMathContext()` | `Money.java:103, 115, 119, 131` — each delegates with `MoneyHelper.getMathContext()`; fallback `return mc != null ? mc : MoneyHelper.getMathContext();` at `Money.java:495` | ✅ **VERIFIED**, all five line cites exact |
| test helper `toMoney(double)` uses that 2-arg form | `Money.of(currency, BigDecimal.valueOf(value))` — `EMI:5260-5262` | ✅ **VERIFIED** |
| `installmentAmountInMultiplesOf` engages `MoneyHelper.getRoundingMode()` | `amountScaled = existingVal.divide(inMultiplesOfValue, 0, MoneyHelper.getRoundingMode()).multiply(inMultiplesOfValue);` — `Money.java:154`, method `:150-157` | ✅ **VERIFIED**, exact |
| tenant rounding mode read from `rounding-mode` global config | `findOneByNameWithNotFoundDetection(GlobalConfigurationConstants.ROUNDING_MODE)` — `MoneyHelperInitializationService.java:102-106` | ✅ **VERIFIED**, exact |
| constant is `"rounding-mode"` | `public static final String ROUNDING_MODE = "rounding-mode";` — `GlobalConfigurationConstants.java:41` | ✅ **VERIFIED**, exact (file lives at `…/infrastructure/configuration/api/`, path not stated in the plan) |
| seeded from `${fineract.tenant.rounding-mode}` | `<column name="name" value="rounding-mode"/>` / `<column name="value" valueNumeric="${fineract.tenant.rounding-mode}"/>` — `0002_initial_data.xml:219-220` | ✅ **VERIFIED**, exact |
| default `6` | `fineract.tenant.config.rounding-mode=${FINERACT_CONFIG_ROUNDING_MODE:6}` — `application.properties:77` | ✅ **VERIFIED**, exact |
| `6` is the ordinal of `RoundingMode.HALF_EVEN` | Java `RoundingMode`: UP=0, DOWN=1, CEILING=2, FLOOR=3, HALF_UP=4, HALF_DOWN=5, **HALF_EVEN=6**, UNNECESSARY=7 | ✅ **VERIFIED** |
| `ProgressiveEMICalculator` contains zero `MoneyHelper` references | `grep -c MoneyHelper …/calc/ProgressiveEMICalculator.java` → **0** | ✅ **VERIFIED** |

**All three claims the mandate singled out are confirmed against source: `PRECISION = 19` in production, mocked to `12` in tests, and a genuine second ambient `MathContext` reachable through the 2-arg `Money.of`.** The plan's derived warning — that a live-server capture executes a different precision from the one that produced the transcribed literals, and that a mismatch is a *capture defect* not a Go-side parity failure — is sound and is the most important operational instruction in the document.

### 4.3 Shadowed class `MathContext` — claim verified, and **understated**

The plan flags **both** of the tests it transcribed that carry a local shadow: V-06 at `EMI:2216` and V-07 at `EMI:2327`, each with a ⚠ and an explicit "transcribing this vector without that shadow is a reproducibility error". **Both confirmed literally. Mandate item 4's final requirement is satisfied.**

However, the shadow is **not** confined to those two. A full sweep of `EMI` finds **eleven** test methods declaring `MathContext mc = new MathContext(12, RoundingMode.HALF_UP);`:

`EMI:2072, 2121, 2166, 2216, 2253, 2290, 2327, 2364, 2401, 2438, 2470`

Nine of these (`2072, 2121, 2166, 2253, 2290, 2364, 2401, 2438, 2470`) sit inside the very line groups §2.8 hands the capture fire for **mechanical transcription** — "`2071/2120/2165` multi-year · `2252/2289/2363/2400` near-month-end and 2-monthly · `2437/2469` `interestRecognitionFromDisbursementDate` false/true pair". §2.8 carries no shadow warning. §2.4's general rule ("these apply to every vector in §2.5 **unless a test shadows them**") is technically sufficient but is stated in a different section and scoped to §2.5. A capture fire working the §2.8 index mechanically would transcribe nine vectors under the wrong rounding mode. This is the highest-consequence gap in the document and is required change #3.

Also confirmed for completeness: the whole `fineract-progressive-loan` test tree contains only two other `MathContext` constructions, both `(12, HALF_EVEN)` class constants (`RepaymentPeriodTest.java:45`, `InterestPeriodTest.java:46`), plus `AdvancedPaymentScheduleTransactionProcessorTest.java:113` mocking `MoneyHelper` to `(12, HALF_EVEN)`. No third precision or rounding mode exists in the seam.

---

## 5. Ordering discipline (mandate item 5)

| Requirement | Present? | Evidence |
|---|---|---|
| A calibration run is required **first** | ✅ | §4.0 "Run C-00 — CALIBRATION. Nothing else is trustworthy until this passes." Ordering restated in §4.4: `C-00 → C-01 → C-02 → … → C-11+`, "C-00 gates everything." |
| It reproduces an already-transcribed **literal** expectation | ✅ | Target is V-01 verbatim; "the first capture run must reproduce an already-transcribed literal test expectation exactly". Inputs are "the complete table in §2.1, verbatim." |
| Gating is explicit — nothing else may be trusted first | ✅ | "If C-00 does not match V-01 digit for digit, the harness is misconfigured and **no** subsequent capture may be entered into the vector store." |
| The designated calibration vector really is twice-attested | ✅ | Confirmed: `EMB:74-92` and `README.md:46-63`. **And in fact thrice** — `EMI:3259-3265` reproduces the same per-period figures through a different entry point (see D7). |
| The plan says what happens on failure | ✅ | "**On failure:** stop. Do not capture anything else. Report the harness configuration, both `MathContext`s (the parameter one and `MoneyHelper`'s, §2.4), and the tenant `rounding-mode` value." Naming *both* contexts in the failure report is exactly right — it is the only diagnostic that distinguishes a harness misconfiguration from a genuine engine difference. |
| Acceptance is objective and complete | ✅ (with D8) | Four named checks, including the full 4 + 6×7 value set, the two counts, all three invariants, and the README cross-check. |

**Ordering discipline: PRESENT and correctly specified.** The only defect is D8: acceptance check 4 asks the capture to match the README stdout, but the README block reports `Balance` (outstanding) only and has no `totalOutstandingBalance` column, so check 4 can corroborate at most 9 of the 10 period columns. The plan should say which columns check 4 covers so a partial match is not read as a full one.

---

## 6. Gap-honesty spot-checks (mandate item 6)

Each of the four claimed gaps was re-established from source independently, not by re-running the analyst's greps.

### Gap 1 — month-end re-anchoring: **GAP CONFIRMED REAL** ✅ (but the plan's *proof* is broken — D1)

- The rule exists in production code, exactly as the plan describes it: `if (frequencyType.isMonthly() && seedDate.get(ChronoField.DAY_OF_MONTH) > 28 && date.get(ChronoField.DAY_OF_MONTH) >= 28) { … Math.min(noOfDaysInCurrentMonth, seedDay) … }` — `fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/DefaultScheduledDateGenerator.java:169-173`. The plan's prose rendering is accurate. (Cite is `167-175`; the method actually spans `168-176` — off-by-one, defect D3.)
- **The plan's stated proof is false.** It asserts `DefaultScheduledDateGenerator` "is instantiated in only three places in scope: `LoanScheduleGeneratorTest.java:70` and `:108`, and `EmbeddableProgressiveLoanScheduleGenerator.java:39`", tagged `[VERIFIED: grep -rn …]`. There are **four**. The fourth is `EMI:72` — `new ProgressiveEMICalculator(new DefaultScheduledDateGenerator())` — and it is a *real* generator, used by `ProgressiveEMICalculator` at three call sites (`ProgressiveEMICalculator.java:848, 1101, 2151`), in a test class whose month-end tests disburse on `2023-10-31`, `2023-10-30`, `2023-10-29`, `2021-10-30`, `2022-10-29`. The plan elsewhere acknowledges this generator exists ("`ProgressiveEMICalculatorTest`'s own generator is used only for interest sub-period splitting"), which makes the "only three" sentence an outright contradiction of its own body text.
- **I re-established the conclusion by a different route, and it holds.** The only in-seam path that *derives* repayment boundaries is `generateExpectedRepaymentPeriods(disbursementDate)`. All 21 of its call sites are at `EMI:3435, 3456, 3496, 3536, 3576, 3630, 3692, 3724, 3758, 3790, 3829, 3871, 3946, 3998, 4036, 4073, 4132, 4179, 4213, 4255, 4316`, and every associated `disbursementDate` literal is `2024-01-01` or `2024-06-01` — **day-of-month 1 in every case**. Every month-end test (`EMI:2215, 2326, 3060` and the near-month-end group) supplies its boundaries as `periodData(...)` input literals. **No test in the seam asserts a derived month-end boundary. The gap is real.**
- Mandate sub-claim, "the in-seam `DefaultScheduledDateGenerator` instantiations all use seed day-of-month 1": true for the three the plan names (`EMB:48` = `2024-01-01`; `LSG:65`/`:104` = `2024-01-01`), **false as a blanket statement** because of the fourth instantiation at `EMI:72`, which is exercised under `2023-10-31` etc. The plan's `> 28`-branch-never-taken conclusion for V-01/V-02/V-03 nonetheless holds — including for `LSG:56` (`DISBURSEMENT_DATE = 2024-01-15`, day 15 ≤ 28), which the plan mis-describes as day 1 (defect D4).
- The plan's proposal to capture the rule through the embeddable entry point by setting the dates to a day > 28 is sound: `DefaultScheduledDateGenerator` lives in `fineract-loan`, and `fineract-loan` is in `requiredModuleNames` for the shadowJar (`build.gradle:28-32`; plan cites `27-31`, off by one — D3).

### Gap 2 — `installmentAmountInMultiplesOf` set: **GAP CONFIRMED REAL, TOTAL** ✅

Independently verified by a different query than the plan's. Across the entire `fineract-progressive-loan/src/test` tree there are **97** declarations of `Integer installmentAmountInMultiplesOf`, and grouping them by right-hand side yields exactly one group: **`null` — 97 occurrences.** Zero non-null. Every other textual occurrence is a pass-through into `generatePeriodInterestScheduleModel(..., installmentAmountInMultiplesOf, mc)`, plus one record-copy accessor at `EMI:5281` (`toCopy.installmentAmountInMultiplesOf()`), which assigns nothing. Adding the embeddable module: `EMB:60` → `null`. **The parameter is `null` at every in-seam occurrence, without exception.** All 19 sample lines the plan cites (`EMI:189, 228, 273, 309, 1091, 1124, 1157, 1190, 1232, 1281, 2226, 2263, 2300, 2337, 2993, 3032, 3070, 3830, 3872`) were reopened and each reads `final Integer installmentAmountInMultiplesOf = null;`. The plan's characterisation of this as "the single largest gap" and "the highest-risk one for the Mongolian market" is correct, and its observation that the path additionally engages `MoneyHelper.getRoundingMode()` (`Money.java:154`) means the behaviour genuinely cannot be reasoned about from source alone.

### Gap 3 — MNT-scale principals: **GAP CONFIRMED REAL, TOTAL** ✅

Largest principal carrying a full literal schedule anywhere in the seam is `245000.0` → `24500000` minor units (V-07, `EMI:2349`; also `EMI:3085` in S3). Independently confirmed: the sorted distinct set of `toMoney(...)` arguments in `EMI` tops out at `245000.0`, with `15000.0` next. A routine `MNT 5,000,000` loan is `500000000` minor units, ~20× larger. Against a precision-12 `MathContext` this is a materially different precision regime. The plan's refusal to extrapolate — "may not be scaled up from the USD vectors by arithmetic. No extrapolation is offered here" — is the correct call and is honoured: no MNT figure appears anywhere as an expected output, only as a capture *input*.

### Gap 4 — long declining-balance terms: **GAP CONFIRMED REAL** ✅

| Term | Method | Full per-period literals? | Verified |
|---|---|---|---|
| 24 periods | FLAT | yes | ✅ `EMI:3880-3903` |
| 20 periods | FLAT | yes | ✅ `EMI:3837-3856` (test at `:3818`, `numberOfRepayments = 20` at `:3825`) |
| 12 periods | DECLINING_BALANCE | **no** — asserts `assertEquals(8.65, toDouble(repaymentPeriod.getEmi()))` for periods 0–10 plus `assertTrue(0 < …)` structural checks and a terminal `assertEquals(0.0, …)` | ✅ `EMI:236-258`, exactly as described |
| 12 periods | DECLINING_BALANCE | post-payment state only, all interest `0.0`, all `fullyPaid = true` | ✅ `EMI:1255-1271` |
| 6 periods | DECLINING_BALANCE | yes | ✅ V-01, V-04, V-06, V-07, V-10 |

**Confirmed: no declining-balance schedule longer than 6 periods carries full literal per-period expectations.** A 36- or 60-month declining-balance schedule is unpinned. The plan's C-05 (36 periods) and C-06 (60 periods) close it.

### Additional finding — a coverage dimension the plan omits (D2)

The plan states, tagged `[VERIFIED: lines 2997-2998, 3036-3037, 3074-3075 and the class default at :110]`, that all seven leap-year tests "set `DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY`". The cited evidence covers only S1, S2 and S3 — three of seven — and the generalisation is **false**. `EMI:3209` reads:

```java
Mockito.when(loanProductRelatedDetail.getDaysInYearCustomStrategy()).thenReturn(DaysInYearCustomStrategyType.FULL_LEAP_YEAR);
```

inside `test_feb29_period_only_cross_year_quarterly_period_containing_feb29` (`EMI:3183`), which builds two schedules and compares them. The **half** of the plan's claim that does survive is the more important one, and I confirmed it: all eight non-null `getDaysInYearCustomStrategy()` stubbings in the seam (`EMI:2997, 3036, 3074, 3116, 3155, 3196, 3209, 3249`) are inside this one nested class; everywhere else the class default `null` at `EMI:110` governs.

Consequence: **`FULL_LEAP_YEAR` is an entirely unmentioned behaviour with no literal expectation anywhere.** That test pins it only *relationally* — `assertEquals` between the two schedules' period-1 interest (`EMI:3219`) and `assertNotEquals` for period 2 (`EMI:3226`) — so no absolute value for `FULL_LEAP_YEAR` exists in the corpus. This is not a *falsely-declared* coverage (the plan never claims `FULL_LEAP_YEAR` is covered; it never mentions the strategy). But §2.5's sentence tells a capture fire that the custom-strategy dimension is exhausted by `FEB_29_PERIOD_ONLY`, and a fire acting on that would never capture `FULL_LEAP_YEAR`. It belongs in §3 as a gap.

### Gap-honesty verdict

**All four gaps the mandate named are REAL. None is falsely declared covered. None is falsely declared missing.** One additional gap (`FULL_LEAP_YEAR`) is missing from the map, and one gap's stated proof is invalid though its conclusion survives.

---

## 7. `[UNVERIFIED]` adjudication

### Marker 1 — provenance of the "~182 LOC" Tier-0 figure: **SETTLED. The analyst gave up too early.**

The orchestrator's hypothesis is **correct, and I confirmed it**:

```
src/main/java/…/EmbeddableProgressiveLoanScheduleGenerator.java   92
misc/Main.java                                                    90
                                                                 ---
                                                                 182
```

`92 + 90 = 182`, exactly. The module contains exactly six files, and its **non-test Java is exactly 182 lines**. This is corroborated by `.softhouse/program.json`, which records the figure under the key **`"main_loc": 182`** for `fineract_paths: ["fineract-progressive-loan-embeddable-schedule-generator"]` — i.e. the figure was measured as *non-test* Java LOC, which is precisely `src/main` + `misc`. The analyst had already opened and cited `misc/Main.java:40-67` in §1.4 and listed all six files in §1.1, yet excluded `misc/Main.java` from the LOC arithmetic, compared `182` only against `92` and `215`, declared no match, and then floated a coincidence with `plan.getLoanTermInDays() == 182` at `EMB:74`.

That speculation is a **red herring and should be struck**. Two unrelated quantities happening to equal 182 is a coincidence; `92 + 90 = 182` with a `main_loc` key in the program manifest is an explanation. The §6 Backlog item "The `CLAUDE.md` '~182 LOC' figure does not reconcile with the measured 92/123/215" is wrong and should be removed. **Adjudication: was reachable by opening a file the analyst had already opened. Settled — no discrepancy exists.**

### Marker 2 — assertion style of the nine `*Progressive*` integration-test classes: **LEGITIMATELY DEFERRED. Upheld.**

These classes live under `integration-tests/`, outside both in-scope modules, and drive the REST API against a running server plus PostgreSQL. Opening them would breach the seam restriction the task set, and their *style* cannot change any conclusion in this document — they are correctly listed as a second-wave source, not mined. I did not open them either. **Adjudication: correctly marked UNVERIFIED; leaving it is the right call, not a failure of effort.**

### Marker 3 — no `MoneyHelper` call anywhere in the embeddable `generate()` transitive call tree: **GENUINELY OUT OF REACH. Upheld, and I can tighten it.**

The plan's framing is exactly right: what is verified is that `ProgressiveEMICalculator.java` contains **zero** `MoneyHelper` references (I re-ran it: `grep -c` → `0`) and that the calculator takes `MathContext` as a parameter; proving the negative across the whole transitive tree needs execution, which this sandbox cannot do. I can add one piece of static evidence that sharpens it into a concrete prediction for C-00: `EMB` does **not** mock `MoneyHelper` at all — unlike `EMI:75, 97-98`, the embeddable test has no `MockedStatic<MoneyHelper>`. So either the embeddable path never touches `MoneyHelper`, or it touches an unmocked one — and since `EMB.testGenerate` is a green CI test producing the README's documented output, the first is far the likelier. **C-00 is precisely the right instrument to settle it, and the plan says so.** Recommend the plan add: *"C-00 must additionally assert that no `MoneyHelper` static initialisation occurs — instrument or stub it to throw — which converts marker 3 from unverified to proven in the same run."*

**Adjudication summary: 1 settled by me (marker 1), 2 correctly upheld as out of reach (markers 2, 3), with a cheap tightening available for marker 3.**

---

## 8. Scope guard (mandate item 8)

The plan was restricted to the progressive-loan schedule-generation seam. **No scope violation found.**

- All transcribed vectors come from `fineract-progressive-loan-embeddable-schedule-generator/src/test` and `fineract-progressive-loan/src/test`, both in-seam.
- `fineract-core` (`Money`, `MoneyHelper`, `CurrencyData`, `GlobalConfigurationConstants`, `MoneyHelperInitializationService`) and `fineract-loan` (`DefaultScheduledDateGenerator`, `LoanRepaymentScheduleModelData`) are consulted **only** to pin the inputs and ambient state of the in-seam vectors. That is not wandering — the embeddable shadowJar bundles both modules by declaration (`build.gradle:28-32`), so their behaviour is part of this seam's observable output. The plan explicitly records the ownership question in §6 Backlog rather than deciding it.
- Out-of-seam test classes (`AdvancedPaymentScheduleTransactionProcessorTest`, `ChangeOperationTest`, the JSON-parser and validator tests) are **catalogued and explicitly excluded**, correctly routed to Backlog, and none of their values is transcribed.
- Integration tests are named and explicitly not mined.
- The deposit-taking note in §4.3 ("nothing in this plan touches savings/deposit behaviour, so no activation gate is engaged") is correct.
- PostgreSQL discipline is respected: §4.1 requires "must be **PostgreSQL** — `postgresql` compose profile. Never MySQL/MariaDB. Oracle Database is prohibited." Terminology is used correctly throughout — "reference oracle (Fineract)" for the test oracle, "Oracle Database" only when naming the prohibited product.
- Money discipline is respected: `int64` / `BIGINT`, integer minor units, MNT = 496 / minor unit 2, 0-decimal postfix display (`1,250,000₮`).

---

## 9. Defect register

| ID | Severity | Defect |
|---|---|---|
| **D1** | **High** | §3.2: "`DefaultScheduledDateGenerator` is instantiated in only three places in scope", tagged `[VERIFIED]`, is **false** — there are four (`EMI:72` is the fourth). This is the stated proof of the program's most important gap; the proof is invalid, though I re-established the conclusion independently. The plan also contradicts itself, acknowledging the fourth generator two paragraphs later. |
| **D2** | **High** | §2.5 V-10: "All set `DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY`", tagged `[VERIFIED]` with evidence covering only 3 of 7 tests, is **false** — `EMI:3209` sets `FULL_LEAP_YEAR`. `FULL_LEAP_YEAR` has **no absolute literal expectation anywhere in the corpus** (only relational `assertEquals`/`assertNotEquals` at `EMI:3219`, `:3226`) and is absent from the §3 coverage map. |
| **D3** | Medium | Three off-by-one citations, all in non-test supporting evidence: `DefaultScheduledDateGenerator.java` "167-175" (actual `168-176`), `LoanRepaymentScheduleModelData.java` "31-38" (actual `32-39`), `build.gradle` "27-31" (actual `28-32`). Content claims are correct in all three; the ranges are not. No vector value is affected. |
| **D4** | Medium | §3.2: "V-01/V-02/V-03 all use seed day-of-month `1` (`2024-01-01`) `[VERIFIED: … LoanScheduleGeneratorTest.java:56 …]`" — `LSG:56` is `DISBURSEMENT_DATE = LocalDate.of(2024, 1, 15)`, day **15**, not day 1. The `> 28`-branch conclusion is unaffected (15 ≤ 28), but the cited evidence does not say what the sentence says. |
| **D5** | Medium | §1.1 and §6: the "~182 LOC" figure is declared irreconcilable when it reconciles exactly (`92 + 90`). The `getLoanTermInDays() == 182` "suspicious coincidence" is a red herring that should not be left in a document a capture fire will act on. |
| **D6** | **High** | §2.8 directs mechanical transcription from indexed line groups that include nine tests carrying the local `MathContext(12, HALF_UP)` shadow (`EMI:2072, 2121, 2166, 2253, 2290, 2364, 2401, 2438, 2470`) with no warning in that section. Eleven shadowing tests exist; the plan flags two. |
| **D7** | Low (positive) | A **third** attestation of V-01's per-period figures exists at `EMI:3259-3265`, through a different entry point and under `(12, HALF_EVEN)` rather than `(12, HALF_UP)`. Unnoticed; it strengthens the calibration vector. |
| **D8** | Low | §4.0 acceptance check 4 asks the capture to match the README stdout, but `README.md:46-63` has no `totalOutstandingBalance` column — the check covers 9 of 10 period columns, not all 10. |
| **D9** | Low | §4.2 binds the `MathContext` once for the whole table rather than per row; and §4.1 *logs* `MoneyHelper.PRECISION` rather than *asserting* it. Adequate as written, brittle on extension. |

---

## 10. Required changes — priority ordered, actionable without me

These do **not** block the merge (the merged content is sound and the 418 vectors are clean). They **do** block the capture fire executing the plan, because #1, #2 and #3 can each cause a wrong vector to be captured or a real behaviour to be missed.

1. **Repair the §3.2 proof (D1).** Replace "instantiated in only three places in scope" with the true count of four, naming `ProgressiveEMICalculatorTest.java:72` as the fourth, and replace the broken argument with the one that actually holds: *the only in-seam path that derives repayment boundaries is `generateExpectedRepaymentPeriods(disbursementDate)`, whose 21 call sites (`EMI:3435, 3456, 3496, 3536, 3576, 3630, 3692, 3724, 3758, 3790, 3829, 3871, 3946, 3998, 4036, 4073, 4132, 4179, 4213, 4255, 4316`) all take a day-of-month-1 disbursement date (`2024-01-01` or `2024-06-01`); every month-end test supplies its boundaries as `periodData(...)` input literals; therefore no test asserts a derived month-end boundary.* Keep the conclusion — it is correct.

2. **Correct the `FULL_LEAP_YEAR` claim and add it to the coverage map (D2).** In §2.5 V-10, change "All set `FEB_29_PERIOD_ONLY`" to: *six of the seven set `FEB_29_PERIOD_ONLY`; `test_feb29_period_only_cross_year_quarterly_period_containing_feb29` (`EMI:3183`) builds one schedule under each strategy, setting `FULL_LEAP_YEAR` at `EMI:3209`.* Retain the surviving half of the claim (all eight non-null stubbings are inside this nested class; `null` everywhere else per `EMI:110`) — that part is verified. Then add to §3.3 and the §3.10 summary a new row: **`DaysInYearCustomStrategyType.FULL_LEAP_YEAR` — GAP.** No absolute literal expectation exists; `EMI:3219` and `:3226` pin it only relative to the `FEB_29_PERIOD_ONLY` schedule. Add a capture run (suggest **C-06b**: C-06's inputs with `daysInYearCustomStrategy = FULL_LEAP_YEAR`, giving a differential against C-06's `null`).

3. **Add a shadow warning to §2.8 (D6).** Insert, immediately before the index: *"⚠ Eleven test methods in this file shadow the class `mc` with a local `MathContext(12, RoundingMode.HALF_UP)` — `EMI:2072, 2121, 2166, 2216, 2253, 2290, 2327, 2364, 2401, 2438, 2470`. Nine of them fall inside the groups indexed below (`2071/2120/2165`, `2252/2289/2363/2400`, `2437/2469`). Any vector transcribed from those groups MUST record `HALF_UP`, not the class default `HALF_EVEN`. Check the first line of the test method before transcribing."*

4. **Fix the three off-by-one citations and the `LSG:56` mis-description (D3, D4).** `DefaultScheduledDateGenerator.java:167-175` → `:168-176` (rule condition at `:169`, body `:170-173`); `LoanRepaymentScheduleModelData.java:31-38` → `:32-39`; `build.gradle:27-31` → `:28-32`. In §3.2, restate as: *"V-01 and V-03 use `2024-01-01` (`EMB:48`, `LSG:104`); V-02 uses `scheduleGenerationStartDate = 2024-01-01` (`LSG:65`) with `disbursementDate = 2024-01-15` (`LSG:56`). Both 1 and 15 are ≤ 28, so the `> 28` branch is never taken in any of the three."*

5. **Restate the `MathContext` per row and upgrade `MoneyHelper` from logged to asserted (D9).** Add an explicit `MathContext` column to the C-02…C-10 table carrying `precision 12 / HALF_UP` on every row, so a future appended row cannot inherit silently. In §4.1, change `MoneyHelper.PRECISION` from "log the value observed at runtime" to *"assert the observed value and record it; a value other than the one C-00 ran under voids the run"*, and apply the same to tenant `rounding-mode`.

6. **Strike the 182-LOC discrepancy (D5).** Replace the §1.1 note and the §6 Backlog bullet with the settled fact: *"the module's non-test Java is exactly 182 lines — `src/main` 92 + `misc/Main.java` 90 — which is the `main_loc: 182` recorded in `.softhouse/program.json`. No discrepancy exists."* Remove the `getLoanTermInDays()` coincidence remark and downgrade `[UNVERIFIED]` marker 1 to resolved, taking the count to 2.

---

## 11. Follow-ups (non-blocking)

- **F1.** Record the third V-01 attestation (D7) at `EMI:3259-3265` in §2.1. It is free evidence, from a different entry point, under a different rounding mode, and it makes C-00 a stronger gate than the plan currently claims.
- **F2.** Scope acceptance check 4 in §4.0 (D8) to the nine columns the README actually reports, so a partial match is not mistaken for a full one.
- **F3.** Add to C-00 an assertion that `MoneyHelper` is never statically initialised on the embeddable path — instrument or stub it to throw. That converts `[UNVERIFIED]` marker 3 from a standing unknown into a proven fact at no extra run cost, and `EMB` mocks no `MoneyHelper` at all (unlike `EMI:75`), so the prediction is testable as stated.
- **F4.** §3.4's caveat is worth promoting: every rate-variation vector is reached through `changeInterestRate` on an existing model (mid-term rescheduling), and no vector exists for a product configured with a rate schedule from origination. That is a Tier-A design question the plan correctly declines to answer, but it should be carried forward rather than left in prose.
- **F5.** The plan's §5.3 correctly stores `calculatedDueInterest` (scale > 2) as a decimal string rather than money. The conformance harness should enforce that classification structurally — any value arriving with scale > 2 routed to the money column is a harness bug, and §4.2's cross-cutting check already says so. Worth making it a hard assertion in the rig rather than a documented expectation.
- **F6.** §2.4's rate-factor caveat deserves promotion to a harness rule: a transcribed rate factor is a 12-dp rounding of the engine value (`applyMathContext`, `EMI:5241, 5256-5258`), so a Go divergence in digits 13+ passes silently. The rig should record rate factors as `TRANSCRIBED-ROUNDED` and treat exact rate-factor parity as `TO_BE_CAPTURED` from the oracle.

---

## 12. Closing note on the artefact's discipline

The thing this review was commissioned to find — a number that was invented rather than observed — is **not present**. 418 expected values, 310 conversions, 16 invariants: all clean. The document also does several things a weaker analyst would not have done: it left `disbursementDate.plusMonths(3).plusDays(4)` unresolved rather than computing a date; it preserved `0.007533802740`'s trailing zero and `1.00000000000`'s scale because `.toString()` comparison makes them load-bearing; it refused to scale USD vectors up to MNT magnitudes and said why; it identified that `MoneyHelper` is a second, ambient `MathContext` that the tests mock away, which is a genuinely non-obvious reproducibility trap and the finding most likely to have saved a future false-parity claim.

The failures are of a different kind: three sentences tagged `[VERIFIED]` that generalise beyond the evidence actually cited (D1, D2, D4), and one gap left open that a file already in hand would have closed (D5). None reached a vector. But the `[VERIFIED:]` tag is the load-bearing convention of this whole document, and a tag that sometimes means "I checked three of seven and generalised" is worth less than one that always means what it says. The corrections above are all that stands between this plan and being executable as written.
