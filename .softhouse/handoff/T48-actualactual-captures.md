# T48 — the ACTUAL/ACTUAL cross-year partial-period arm, captured

**Task** T48, branch `softhouse/T48-actualactual-captures`, worker `test_writer`.
**Fire** local `20260819-*`, Buyan's Mac. **The reference oracle (Fineract) WAS reachable and every
number below is an OBSERVATION made on it** — nothing computed, extrapolated, interpolated or authored,
except where a line is explicitly labelled a re-derivation. Oracle Database is prohibited and appears
nowhere; the only engine touched is **PostgreSQL 18.3**.

> ## THIS TASK CAPTURES. IT DOES NOT ADMIT.
> **Nothing here proposes admitting `DaysInYearCustomStrategy`, `DaysInYearType.ACTUAL` or the
> cross-year partial-period arm to DEC-1's graded domain.** Admission would make
> `daysInYearCustomStrategy` live, which **DEC-1 §4.4 states is an AMENDMENT** — a gate no agent may
> cross. This pass produces the evidence a properly-gated decision would need; making that decision is
> not mine. **No file under `docs/adr/**` was touched** (T47 owns DEC-1 revision 10 concurrently).
>
> **RAW OBSERVED FORM ONLY.** Gate **G-1 is open**; nothing is contract-shaped and nothing is promoted
> to the parity vector store.

---

## 0. Headline

**DEC-1 §8's `DayCountActualActual` item can be marked CAPTURED.** The arm that had never been
exercised end to end has now been observed on **three seams**, at production settings, with both
controls passing, determinism proved byte-identical from fresh containers, and the run recipe proved
failable on eight axes.

Seven things were learned that no capture the program holds could see:

1. **The "deliberately exact" multiply at `ProgressiveEMICalculator.java:1975` is NOT observable at its
   sole call site**, and a port that rounded there would **not** diverge. 21 probe sites, **0** where
   `ONE.multiply(f)` differs from `ONE.multiply(f, mc)`. Reason, observed and re-derived: the call site
   passes the literal `BigDecimal.ONE`. Vacuity canary separates 2 of 2, so the probe is not vacuous.
2. **`FEB_29_PERIOD_ONLY`'s second effect is real and observed in pure isolation** — it suppresses the
   cross-year partial arm for a period containing no 29 February, and it moves money.
3. **`FULL_LEAP_YEAR` is behaviourally identical to the field being unset** — confirmed, **0 of 285
   cells** on the production wiring and 0 of 38 rate-factor cells on the calculator seam.
4. **`interestRecognitionOnDisbursementDate` is silently replaced by a different field on the
   progressive schedule path** — a NEW finding, and a second Path A blind spot (T48-N1 below).
5. **`m_charge.amount` never governs**: omitting `amount` is a hard HTTP 400 on every charge type.
6. **`chargeCalculationType` 5 is accepted by the enum's own `validValuesForLoan()` and then rejected by
   the validator for every `chargeTimeType` except 12** — a contradiction inside Fineract (T48-N2).
7. **`RepaymentEvery` 4 / 6 / 12 all work** and are now captured; the `totalRepaymentExpected` defect
   T40 found reproduces there too.

---

## 1. What was captured

| set | seam | file | captures |
|---|---|---|---|
| `seam` | **Path A** — `EmbeddableProgressiveLoanScheduleGenerator` | `capture/actualactual/out/t48-seam.json` | 18 |
| `calc` | **Path A2** — `ProgressiveEMICalculator` (the seam Fineract's own unit tests use) | `capture/actualactual/out/t48-calc.json` | 27 |
| `exact` | Path A2, the exactness probe at `:1975` | `capture/actualactual/out/t48-exact.json` | 28 (incl. the vacuity canary) |
| Path B | the **running server**, tenant `gerege`, production wiring | `capture/actualactual/pathb/out/T48B-*-raw.json` + `-exact.json` sidecars | 13 |
| charges | the running server, T46's open gaps | `capture/charges/out/t48/T48-CH-*-raw.json` + sidecars | 19 |

**Why three seams.** Path A **drops `daysInYearCustomStrategy` entirely** — `LoanApplicationTerms`'s
private `Builder` constructor [VERIFIED: `LoanApplicationTerms.java:304-351`] never copies
`builder.daysInYearCustomStrategy` [VERIFIED: declared `:380`, set by the setter `:567-570`] into the
field [VERIFIED: `:291`], so `assembleFrom`'s `.daysInYearCustomStrategy(…)` call [VERIFIED: `:604`] is
discarded and `toLoanConfigurationDetails()` [VERIFIED: `:1746-1756`] passes `null`. **Observed**, not
just re-derived: `T48-AA-N3` (feeds `FEB_29_PERIOD_ONLY`) and `T48-AA-N4` (feeds `FULL_LEAP_YEAR`) are
**0 of 87 cells** different from `T48-AA-1`, which fed nothing.

---

## 2. The arm, observed — and what each capture discriminates

The rule the oracle actually implements, now confirmed cell for cell:

```
partialPeriodCalculationNeeded                                     [:1505-1507]
  = daysInYearType == ACTUAL
 && interestPeriodDueDate.getYear() - interestPeriodFromDate.getYear() > 0
 && ( !FEB_29_PERIOD_ONLY.equals(strategy)
      || isPeriodContainsFeb29(repaymentPeriod.from, repaymentPeriod.due) )

if it holds:  f = SUM over years  days(segment) / Year.of(year).length()   [:1550-1568]
              rateFactor = setScale(19, HALF_UP)( interestRate x f )       [:1526-1531, :1969-1980]
```

with the year boundary at **31 December**, or **1 January of the next year** when
`isInterestRecognitionOnDisbursementDate()` is true [VERIFIED: `:1578-1584`].

**The formula is not merely re-derived — it is graded against the oracle's own output.** The `exact` set
re-derives `setScale(19, HALF_UP)(rate × f)` from the observed `f` and compares it with the rate factor
the oracle actually produced, read off `InterestPeriod.getRateFactor()`. **15 of 15** sites where the arm
fires **match exactly**; the **6** that do not are exactly the sites where the arm is suppressed, and
their oracle values equal the plain ACT/ACT reading instead. A port with a wrong segmentation rule cannot
land on both sets.

| capture | shape | what a wrong port must get wrong for this to catch it |
|---|---|---|
| `T48-AA-1` / `T48-A2-AA1` | leap → non-leap, monthly, 2024-11-01 | splitting 31 days as `30/366 + 1/365` rather than `31/366`. Observed f `0.08470693914215135863`, rate factor `0.0182966988547046935` |
| `T48-AA-2` / `T48-A2-AA2` | identical, `interestRecognitionOnDisbursementDate = true` | putting the boundary at 1 Jan instead of 31 Dec. **35 of 115 cells move**, rate factor `0.0182950819672131148`, total interest **76,160.63 → 76,158.97** (MNT 1.66) |
| `T48-AA-3` | quarterly, `repayEvery = 3`, period 2 crosses AND holds 29 Feb | threading the product's `repayEvery` into `rateFactorByRepaymentPartialPeriod`'s `repaymentEvery` parameter instead of the literal `ONE` at `:1529-1530` — that would treble the rate factor |
| `T48-AA-4` | `repayEvery = 13` months, 2 periods, each spanning **three** year segments | running the `while` loop [:1558-1567] once instead of three times. Observed: period 1 `2023-12-15 → 2025-01-15`, 397 days, interest **1,301,917.81**; period 2 `2025-01-15 → 2026-02-15`, 396 days, **690,743.82** |
| `T48-AA-5` | non-leap → non-leap (2022→2023) | **nothing.** Both year lengths are 365, so `Σ days_i/365 = totalDays/365` and the arm coincides exactly with the plain branch. **This capture discriminates nothing about the arm** and is recorded as such — see §6 |
| `T48-AA-6` / `-7` | leap→non-leap and non-leap→leap, mid-December | using the from-date's year length for the whole period |
| `T48-AA-8` | period starts **on** 31 December: first segment is **zero** days | mishandling a zero-length segment. Also lands where the readings agree (§6) |
| `T48-AA-9` / `-10` | WEEKLY and DAILY frequency across the boundary | assuming the arm is monthly-only |
| `T48-AA-11` | `DaysInMonthType.DAYS_30` with ACT/ACT | letting `daysInMonthType` reach the crossing period's rate factor — the arm returns at `:1526-1531`, **before** the `daysInMonthType` switch at `:1534-1541` |
| `T48-AA-N1` | same shape at `DaysInYearType.DAYS_365` | firing the arm when the first conjunct is false. **30 of 87 cells move**; total interest 76,160.63 vs 76,271.66 |
| `T48-AA-N2` | ACT/ACT, no year crossing | firing the arm when the second conjunct is false |

---

## 3. Is the exactness at `:1969-1980` confirmed by observation? **No — and that is the answer.**

`rateFactorByRepaymentPartialPeriod` does `repaymentEvery.multiply(cumulatedPeriodRatio)` with **no
`MathContext`**, unlike every neighbouring operation [VERIFIED: `ProgressiveEMICalculator.java:1975`].
The brief called that "the most interesting thing to confirm by observation". It cannot be confirmed,
because **at the sole call site the multiplier is the literal `BigDecimal.ONE`**
[VERIFIED: `:1529-1530` and `:1396-1397` — `rateFactorByRepaymentPartialPeriod(interestRate,
BigDecimal.ONE, cumulatedPeriodFractions, BigDecimal.ONE, BigDecimal.ONE, mc)`].

**Observed, over 21 probe sites spanning both `MathContext`s used in this pass:**

* `cumulatedPeriodFractions` carries **precision 19** at `mc = (19, HALF_UP)` and **precision 12** at
  `(12, HALF_EVEN)` — never more than `mc.getPrecision()`, at any site;
* `ONE.multiply(f)` and `ONE.multiply(f, mc)` are **bit-identical as plain text at 21 of 21 sites**;
* the re-derived rate factor is identical either way at 21 of 21 sites.

The source reason, re-derived: `cumulatedRateFactor` is built by `add(x, mc)` [VERIFIED: `:1565`], so it
can never exceed `mc`'s significant digits, and `BigDecimal.round` is the identity when
`precision() <= mc.getPrecision()`. **So a Go port that rounded at that multiply would NOT diverge.**

**The probe is not vacuous.** A vacuity canary (a locally constructed 25-significant-digit ratio, clearly
labelled as *not* an oracle output) runs the same comparison and **separates on 2 of 2 legs** —
`0.1428571428571428571428571` exact vs `0.1428571428571428571` rounded. A probe that can only ever say
IDENTICAL would be worthless; this one demonstrably can say otherwise.

**What this means for a porter:** implement `:1975` exactly for fidelity, but do not treat it as a
graded distinction — no vector can grade it while the call site passes `ONE`. `TO_BE_CAPTURED` if
Fineract ever changes that argument.

---

## 4. `FEB_29_PERIOD_ONLY`'s second effect — settled

**Effect (b) is real, and it is observed in PURE isolation.**

`T48-F29-B-*` (Path A2) and `T48B-PUREB-p{7,3,4}` (Path B) use two monthly periods,
`2023-11-01 → 2024-01-01`. Effect (a) — the 366→365 substitution — can only fire where
`DaysInYearType.ACTUAL.getNumberOfDays(interestPeriodFromDate)` is 366, i.e. where the **from-date's**
year is leap [VERIFIED: `DaysInYearType.java:81-86` → `referenceDate.lengthOfYear()`]. Both periods start
in **non-leap 2023**, so effect (a) is a provable no-op on every period, and the only thing
`FEB_29_PERIOD_ONLY` can change is the third conjunct of `partialPeriodCalculationNeeded`.

| reading | period 2 rate factor | total interest |
|---|---|---|
| strategy **UNSET** — arm fires, `30/365 + 1/366` | `0.0183435885919604761` | **32,403.86** |
| **`FULL_LEAP_YEAR`** — arm fires, identical | `0.0183435885919604761` | **32,403.86** |
| **`FEB_29_PERIOD_ONLY`** — arm SUPPRESSED, falls through to `31/365` | `0.0183452054794520548` | **32,404.83** |

**23 of 65 cells differ** on Path B; **11 of 43** on Path A2, of which **3 of 8 are rate-factor cells**.
On the one-year shape the gap is **145,118.81 vs 145,413.87** (MNT 295.06); on the quarterly MNT 10 M
shape **760,405.92 vs 761,031.00** (MNT 625.08).

**The companion — a period that DOES contain 29 February.** `T48-F29-Q-*` / `T48B-QTR-p*`: period 2 is
`2023-12-01 → 2024-03-01`, crossing **and** containing 29 Feb 2024, so the third conjunct holds and the
arm fires under **all three** strategies. Its rate factor is `0.0298630136986301370` under all three —
**0 of 14 rate-factor cells** differ on that period. The cells that do move (6 of 14) are periods 3 and 4,
which are inside leap 2024 without a 29 February and are moved by **effect (a)**. This reproduces at
production settings, in MNT, what Fineract's own
`test_feb29_period_only_cross_year_quarterly_period_containing_feb29`
[VERIFIED: `ProgressiveEMICalculatorTest.java:3183-3229`] asserts only qualitatively.

**Effect (a) in pure isolation** is `T48-F29-A-*` (three monthly periods inside leap 2024, no 29 Feb, no
crossing): **10 of 11 rate-factor cells** move, `0.0182950819672131148 → 0.0183452054794520548`.
`T48-F29-C-*` (middle period contains 29 Feb) shows the middle period's rate factor **unchanged**.

**Two effects, two separating shapes, and they do not overlap.**

## 4b. `FULL_LEAP_YEAR` ≡ the field being unset — CONFIRMED

| comparison | seam | result |
|---|---|---|
| `T48B-PUREB-p3` vs `-p7` | **Path B, production wiring** | **0 of 65 cells differ** |
| `T48B-YEAR-p3` vs `-p7` | Path B | **0 of 285 cells differ** |
| `T48B-QTR-p3` vs `-p7` | Path B | **0 of 109 cells differ** |
| `T48B-B03SHAPE-p3` vs `-p7` | Path B | **0 of 285 cells differ** |
| `T48-F29-{Q,M,Y,B,A}-NULL` vs `-FULL` | Path A2 | **0 cells differ** in all five, **0 of 91 rate-factor cells** |
| `T48-A2-CTL-B03` vs `T48-A2-CTL-B03NULL` | Path A2 | **0 of 38 rate-factor cells** |

Source agreement [VERIFIED]: the only test applied to the strategy anywhere on this call graph is
`FEB_29_PERIOD_ONLY.equals(customStrategy)` — at `getNumberOfDays` [`ProgressiveEMICalculator.java:1349`]
and in `partialPeriodCalculationNeeded` [`:1372-1374`, `:1505-1507`]. `FULL_LEAP_YEAR` and `null` both
fail that test identically. **Contract consequence: `FULL_LEAP_YEAR` carries no information, and a port
may represent it as "unset" — but a port must not represent `FEB_29_PERIOD_ONLY` that way.**

---

## 5. The charge gaps (T46's open list)

Path B, tenant `gerege`, **additive**: no existing charge definition modified or deleted, **no product
created**, `m_loan` **0 before and 0 after**, `m_product_loan` **16 before and 16 after**.
**New charge id created: `13`** ("T48 percent of disbursement amount TRANCHE", chargeTimeType 12,
chargeCalculationType 5, amount 1.234500). Four further `POST /charges` attempts were **rejected** and
created nothing. Full record: `capture/charges/out/t48/created-charges.txt`, `CREATED-IDS.txt`.

**Gap 1 — does `m_charge.amount` govern when the request OMITS `amount`? NO. The question is moot.**
Omitting `amount` is a hard **HTTP 400** on **5 of 5** legs — `chargeTimeType` 1, 2, 8 and 12, and both
FLAT and PERCENT_OF_AMOUNT:

```
"The parameter `charges[1][amount]` is mandatory."
validation.msg.loan.charges.amount.cannot.be.blank
```

So `m_charge.amount` is **never** consulted for a loan charge on this endpoint, and T46's finding
("request wins 7 for 7") is the whole story: there is no path on which the definition's amount reaches
the schedule. `TO_BE_CAPTURED` closed.

**Gap 3 — `chargeTimeType` 2 with a DISAGREEING amount: the request wins there too.**

| capture | `m_charge.amount` | request `amount` | observed `totalFeeChargesCharged` |
|---|---|---|---|
| `T48-CH-02` tt 2 FLAT | 9000.000000 | **4444** | **4444.00** |
| `T48-CH-04` tt 8 FLAT | 2500.000000 | **3333** | **39996.00** (= 3333 × 12) |
| `T48-CH-06` tt 1 FLAT | 15000.000000 | **5555** | **5555.00** |
| `T48-CH-08` tt 1 PCT | 1.234500 | **2.5** | **30000.00** (= 2.5 % of 1,200,000) |

**Gap 2 — `chargeCalculationType` 5 and 9.**

* **5 = `PERCENT_OF_DISBURSEMENT_AMOUNT`** is rejected at `chargeTimeType` **1, 2 and 8** with
  *"The parameter `chargeCalculationType` must not be any of [ 5 ]"* and accepted **only** at
  `chargeTimeType` **12 (`TRANCHE_DISBURSEMENT`)**. Root cause [VERIFIED]:
  `ChargeCalculationType.validValuesForLoan()` [`ChargeCalculationType.java:60-64`] **includes** 5 and
  the deserializer accepts it at `:176-179`, and then
  `performChargeTimeNCalculationTypeValidation` [`ChargeDefinitionCommandFromApiJsonDeserializer.java:482-496`]
  rejects it in the `else` branch at `:492-495` for every time type but 12. **Two validators in one
  request disagree** — see finding T48-N2.
* Used on a **single-disbursement** product, charge 13 is applied at disbursement, its `dueDate` is
  **ignored**, and it is **byte-identical to `PERCENT_OF_AMOUNT` (2) at the same 1.2345 %** — **0 of 280
  cells differ**. It did land (9 of 280 cells differ from the zero-charge control, fee `14814.000000`).
  **This comparison discriminates nothing**: a port that implemented type 5 as type 2 would pass it. A
  separating shape needs a **multi-disbursement (tranche) product**, which is `TO_BE_CAPTURED`.
* **`chargeCalculationType` 9 does not exist** — the enum tops out at 5
  [VERIFIED: `ChargeCalculationType.java:25-30`] — and the oracle answers **HTTP 400**
  *"must be one of [ 1, 2, 3, 4, 5 ]"*.
* The other reading of "9" was exercised too: **`chargeTimeType` 9 = `OVERDUE_INSTALLMENT`** is rejected
  with **HTTP 403** (a *domain rule* violation, not a 400 validation error) — a different failure mode,
  recorded verbatim.

**Gap 4 — `RepaymentEvery > 3`: all accepted, all captured.**

| `repaymentEvery` | periods | days per period | total interest |
|---|---|---|---|
| 3 (comparator) | 8 | 90 / 91 / 92 / 92 … | 309,438.57 |
| **4** | 6 | 120 / 123 / 122 … | **319,868.56** |
| **6** | 4 | 181 / 184 … | **340,564.86** |
| **12** | 2 | 365 / 365 | **401,432.49** |

`repaymentEvery 4` vs `3`: **135 of 191 cells differ**. This is `rateFactorByRepaymentPeriod`'s
`repaymentEvery` argument [VERIFIED: `ProgressiveEMICalculator.java:1512-1519`] exercised above 3 for
the first time in the corpus — at `repaymentEvery = 12` the period-1 interest is exactly
`1,200,000 × 21.6 % × (12/12) = 259,200.00`.

**`RepaymentEvery = 4` with an instalment fee** reproduces T40's finding 1 at the new shape:
`sum(totalDueForPeriod)` **1,534,868.56** vs `totalRepaymentExpected` **1,519,868.56** — the six 2,500
instalment fees are **missing from `totalRepaymentExpected`**, exactly 15,000.00.

**N46-1 was NOT attempted**, as instructed: separating the ambient charge rounding mode from the threaded
one needs a **tenant write** on the shared server. Still `TO_BE_CAPTURED`.

---

## 6. Where the captures land on agreement, and therefore prove nothing

Stated because a capture that lands where the readings agree is worth nothing and the honest move is to
say so.

* **`T48-AA-5` (non-leap → non-leap).** When both years have length 365, `Σ days_i/365 = totalDays/365`
  **exactly**, so the partial arm and the plain ACT/ACT branch coincide. Confirmed on the probe:
  `T48-CAL-S5`'s crossing site has `oracleRateFactorMatchesExactRederivation = true` even though the arm
  is suppressed there. **The arm is observable only where the two years differ in length.**
* **`T48-AA-8` / `T48-CAL-S3` / `T48-CAL-S4` (period starts on 31 December).** The first segment is zero
  days, so `f` collapses to `days/L(endYear)` and the two readings coincide again.
* **`T48-CH-10` vs `T48-CH-14`** — calculation type 5 vs 2 on a single-disbursement loan: **0 of 280**.
* **`T48-CH-11` vs `T48-CH-10`** — `dueDate` on a tranche charge: **0 of 280**.
* **`T48-AA-2` on Path A**: 0 of 87 cells, because `interestRecognitionOnDisbursementDate` does not bind
  there — see T48-N1. The A2 twin is where the separation shows up.

---

## 7. Controls

**Calibration against shipped test literals.**

* `T48-CAL` reproduces the embeddable-seam literal on **all 4 asserted values** — 182 days, `100.00`,
  `2.05`, `102.05` [VERIFIED: `EmbeddableProgressiveLoanScheduleGeneratorTest.java:74-77`], at
  `(12, HALF_UP)`.
* `T48-CAL-S1`…`S5` reproduce **five** shipped `ProgressiveEMICalculatorTest` literals — **28 period
  rows, every one digit for digit**, at the settings those tests declare, `(12, HALF_EVEN)`
  [VERIFIED: `ProgressiveEMICalculatorTest.java:76`, `:97-98`]. Literals transcribed with `file:line`
  into `analysis/shipped_literals.json`; none is computed. **This is what makes Path A2 trustworthy as a
  rig** — it drives the oracle exactly as Fineract's own tests do, including the `FEB_29_PERIOD_ONLY`
  cases S1/S3/S4/S5, three of which contain a cross-year period.

**Reproduction of already-committed observations, through different harnesses.**

* `T48-CTL-Q0a` — the pass-3/T37/T39 shape.
* `T48-CTL-B03` (Path A) reproduces committed **Path B** observation **B-03**: `144,659.21` /
  `1,344,659.21`, to the minor unit, through an entirely different seam.
* `T48-A2-CTL-B03` = **144,659.21** and `T48-A2-CTL-B04` = **145,011.43** — both committed Path B
  observations reproduced on the calculator seam.
* `T48B-B03SHAPE-p3` / `-p4` reproduce them on the running server itself.

**Cross-seam agreement, the strongest evidence in this pass.** `analysis/PATHB-CROSSCHECK.txt`: on
**12 of 12** shared shapes, Path B and Path A2 agree on the total interest **and period by period**.
Two independent seams into the same pinned image digest.

**Determinism.** All three Path A/A2 payloads are **byte-identical** on re-run from a fresh
`docker run --rm` container with the harness recompiled inside it. All 19 Path B charge captures are
byte-identical on re-post. Only the log's wall-clock timestamps differ, and they are split off.

**A run recipe proved failable.** `src/negative-tests.sh`, **8 of 8 legs breach** and name the breach —
wrong commit, wrong image, wrong seam digest, an actual seam-class byte drift (restored and re-diffed),
threaded mode forced to `HALF_EVEN`, threaded precision forced to 12, tenant ordinal forced to `DOWN`,
and an expected-ambient mismatch. See `NEGATIVE-TESTS.md`.

---

## 8. Attestation summary

Full text: `capture/actualactual/ATTESTATION.md`, written against the **corrected** eight-point rule.

* **Threaded** and **ambient** are named separately everywhere; neither is called "effective".
* The **threaded** `MathContext` is echoed **off the object** handed to the callee
  (`mc.toString()` / `getPrecision()` / `getRoundingMode()`), and the recipe **fails the run** if intent
  and object ever disagree. `(19, HALF_UP)` on every non-calibration capture.
* The **wiring is stated per path**: Path A via `generate(mc, modelData)` → `:108-109`; Path A2 via
  `generatePeriodInterestScheduleModel(…, mc)` → `scheduleModel.mc()` [`:1487`]; Path B via
  `LoanScheduleAssembler.java:753` / `LoanScheduleGeneratorServiceImpl.java:44`, where the ambient **is**
  the threaded object.
* **One ambient witness, counted once.** The oracle's SLF4J rounding-mode line comes from the same local
  `MoneyHelper` caches [VERIFIED: `MoneyHelper.java:59-64`] and `:74-82` reads back — it is not a second
  independent witness. **The "two independent witnesses that are both ambient" defect found in T37 and
  T39 is not repeated here.**
* **Both known ambient leaks are stated**, and the enumeration is explicitly not an exhaustiveness claim
  (it has been wrong twice): (1) the 0-dp `inMultiplesOf` leak, unreachable at MNT's 2 dp; (2) T46's
  **N46-1 charge-rounding leak, which IS reachable at 2 dp** — no capture under
  `capture/actualactual/` carries a charge, but the T48 charge pass does, and its rounding mode is
  therefore ambient and remains `TO_BE_CAPTURED`.
* **Behavioural canaries, not configuration echoes**: T36's half-cent tie ran before every Path B post
  and passed; on Path A/A2 the canary is the **threaded** negative legs N5/N6.
* Precision 19 is labelled a **provenance** claim here — no capture in this pass separates 19 from 12.

---

## 9. NEW FINDINGS

### T48-N1 (P1) — `interestRecognitionOnDisbursementDate` is silently replaced by a different field on the progressive schedule path

`LoanApplicationTerms.toLoanConfigurationDetails()` passes
**`isInterestChargedFromDateSameAsDisbursalDateEnabled`** into the
**`interestRecognitionOnDisbursementDate`** parameter slot of `LoanConfigurationDetails`'s constructor
[VERIFIED: `LoanApplicationTerms.java:1753` is the 16th argument;
`LoanConfigurationDetails.java:66-77` names that parameter `interestRecognitionOnDisbursementDate`].
The field `LoanApplicationTerms.interestRecognitionOnDisbursementDate` — set from the builder at
[VERIFIED: `:327-328`] and settable through `assembleFrom` at [VERIFIED: `:603`] — is **never read by
this method**. It *is* read by `getLoanProductRelatedDetail()` [VERIFIED: `:1740`], but
`ProgressiveLoanScheduleGenerator.generate` uses `toLoanConfigurationDetails()`
[VERIFIED: `ProgressiveLoanScheduleGenerator.java:109`].

**Consequences.** (a) A **second Path A blind spot** beside `daysInYearCustomStrategy`: `T48-AA-1` and
`T48-AA-2` differ only in that flag and are **0 of 87 cells apart**, while their Path A2 twins are **35
of 115 apart**. (b) On the progressive path the year-boundary rule at `:1578-1584` is governed by
`isInterestChargedFromDateSameAsDisbursalDateEnabled`, **not** by the field of the same name as the
getter. **A Go port that wires `interestRecognitionOnDisbursementDate` to that getter will diverge**
whenever the two product settings differ. `[VERIFIED from source; the Path A observation corroborates
that the flag does not bind there. Whether the server's own `assembleFrom` keeps the two in step is
[UNVERIFIED] and is TO_BE_CAPTURED — every product on `gerege` has
`interest_recognition_on_disbursement_date = f`.]`

### T48-N2 (P2) — two validators disagree about `chargeCalculationType` 5 in one request

`ChargeCalculationType.validValuesForLoan()` **lists** `PERCENT_OF_DISBURSEMENT_AMOUNT` (5)
[VERIFIED: `ChargeCalculationType.java:60-64`], the deserializer accepts it against that list
[VERIFIED: `ChargeDefinitionCommandFromApiJsonDeserializer.java:176-179`], and then
`performChargeTimeNCalculationTypeValidation` rejects it for every `chargeTimeType` except
`TRANCHE_DISBURSEMENT` [VERIFIED: `:482-496`, the `else` at `:492-495`]. **Observed**: the same request
returns both *"must be one of [ 1, 2, 3, 4, 5 ]"*-style acceptance and *"must not be any of [ 5 ]"*.
A porter reading `validValuesForLoan()` alone would build the wrong validator.

### T48-N3 (P2) — the "deliberate exactness" at `:1975` is unreachable

Recorded so no future task spends a fire trying to capture it. See §3.

### T48-N4 (P3) — the partial arm and the plain ACT/ACT branch coincide exactly when both years are the same length

`Σ days_i / 365 = totalDays / 365`. So **no cross-year vector inside a run of non-leap years can grade
the arm**, and a conformance suite built only from such shapes would score a port identically whether it
implemented the arm or not. Any admitted vector for this arm **must** cross a leap-year boundary with a
non-zero first segment.

### T48-N5 (P3) — a `TRANCHE_DISBURSEMENT` charge on a single-disbursement product is applied at disbursement and its `dueDate` is ignored

`T48-CH-10` / `-11` / `-12` are byte-identical to each other and to the `PERCENT_OF_AMOUNT` comparator.
Its `feeChargesDue` is rendered at **scale 6** (`14814.000000`) while every other money field is scale 2,
corroborating T46's **N46-2** (the disbursement-row charge scale is caller-controlled).

---

## 10. What I could NOT capture, and why

* **The exactness at `:1975`** — not capturable at the current call site (§3). Recorded as *not
  capturable*, with the argument, rather than `TO_BE_CAPTURED`.
* **N46-1, the ambient charge rounding mode** — needs a **tenant write** on the shared server.
  Deliberately not attempted, as instructed. `TO_BE_CAPTURED`.
* **A separating shape for `chargeCalculationType` 5** — needs a **multi-disbursement (tranche)
  product**, which would mean creating a product with a different multi-disburse configuration and, to
  be meaningful, a persisted loan with tranches. `TO_BE_CAPTURED`.
* **Whether the server keeps `interestRecognitionOnDisbursementDate` and
  `isInterestChargedFromDateSameAsDisbursalDateEnabled` in step** (T48-N1) — every product on `gerege`
  has the former `false`; separating them needs a **new product** with
  `isInterestRecognitionOnDisbursementDate = true`. `TO_BE_CAPTURED`.
* **Threaded precision 19 vs 12** — no shape in this pass separates them; T39's separating shape
  (50 M / 360 months) was not re-run here. `TO_BE_CAPTURED` for this arm.
* **`chargeTimeType` 9 (`OVERDUE_INSTALLMENT`)** — rejected at HTTP 403 at definition time on this
  configuration; unchanged from T40/T46.
* **`Asia/Hovd`**, multi-disbursement, down payments, `fixedLength`, `minCap`/`maxCap`, the cumulative
  generator, and anything needing a persisted loan — unchanged from T40/T44/T46.

## 11. Unverified

* **T48-N1's server-side consequence** — that a Path B schedule would move if the two aliased product
  settings differed. Re-derived from source; **not observed**, because no product on `gerege` sets
  either flag true. `[UNVERIFIED]`
* **That Path A2 is admissible as a capture path.** It reproduces five shipped literals, two committed
  Path B observations, and agrees with Path B on 12 of 12 shared shapes period by period — but
  *promoting a capture path to a trusted source is a `user` decision*, and this task does not make it.
  `[UNVERIFIED as an admissibility claim; the reproductions themselves are VERIFIED observations.]`
* **That the enumeration of ambient leaks in §8 is complete.** It has been wrong twice in this program.
  `[UNVERIFIED]`
* **That the negative tests would reject a correctly-configured run of a *wrong* oracle.** No fire has a
  second Fineract build to test that against. `[UNVERIFIED]`
* **Anything about `daysInYearCustomStrategy` under multi-disbursement, rescheduling, chargeback, or
  interest recalculation.** Out of this pass's reach entirely. `[UNVERIFIED]`

---

## 12. Write surface actually touched

* `.softhouse/capture/actualactual/**` — created by this task.
* `.softhouse/capture/charges/bin/t48-*.{py,sh}`, `.softhouse/capture/charges/req/calc-T48-CH-*.json`,
  `.softhouse/capture/charges/out/t48/**`, `.softhouse/capture/charges/out/t48-rerun/**` — **new ids, a
  new pass, additive**. No committed observation of T40 or T46 was mutated.
* `.softhouse/handoff/T48-actualactual-captures.md` — this file.

**Not touched:** `docs/adr/**`, `nexus/**`, `.softhouse/capture/{periodratio,mathcontext,dec1-binding,pathb,src,out,audit-t44}/**`,
`.softhouse/reviews/**`, `tasks.json`, `program.json`, `RESUME.md`, `reference-oracle.md`,
`patterns.md`, `gates.md`, `LOCK`. `/Users/buv/fineract` was read-only throughout; no Gradle build ran.

**Server state left exactly as found except for the recorded addition:** `m_charge` **12 → 13**
(new id `13` only; ids 1–12 untouched), `m_product_loan` **16 → 16**, `m_loan` **0 → 0**. The shared
containers were never started, stopped, restarted, re-tenanted or written to.
