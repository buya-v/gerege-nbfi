# T3b Independent Re-Review — `docs/analysis/progressive-schedule-behavior.md` (attempt 2)

**Task:** T3b, re-review after a REJECT of attempt 1 (`.softhouse/reviews/T3-progressive-schedule-behavior-review.md`).
**Reviewer:** independent adversarial reviewer, no planning context.
**Source of truth:** `/home/user/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` (verified via `.git/HEAD`; read-only, not modified).
**Document under review:** `docs/analysis/progressive-schedule-behavior.md`, 1091 lines, 138 `[VERIFIED:` tags, 5 `[UNVERIFIED` occurrences.

**Method — and an explicit limitation.** **A live reference oracle (Fineract) is NOT reachable from this sandbox; no
Java was executed. Every figure in this review was derived from source by exact-decimal re-implementation, by me, in
this session.** The `BigDecimal`/`MathContext` pipeline was re-implemented line-by-line from source in a Python
`decimal` emulator with explicit contexts (`multiply(x,mc)`/`divide(x,mc)` = exact op rounded to `mc.precision`
*significant digits*; `setScale(n,rm)` = quantize to `n` *decimal places*; `BigDecimal::add` with no `mc` = exact),
plus a re-implementation of `LocalDate.plusMonths`, `ChronoUnit.MONTHS.between` (Java's packed
`prolepticMonth*32+day` algorithm) and `DefaultScheduledDateGenerator.adjustDate`. The emulator was **validated
against the shipped golden test before being used to probe anything else**: it reproduces
`EmbeddableProgressiveLoanScheduleGeneratorTest.testGenerate()` — term 182 days, EMI 17.01, all six splits, total
interest 2.05, total repayment 102.05 — digit for digit. No number below is read back from the document.

---

# VERDICT: **REJECTED**

The rewrite is a large, genuine improvement: 8 of the 12 required changes landed, the corrected §4.4 month-end rule
and §3.1 `periodRatio` analysis are **correct** (I re-derived both independently, including the `periodRatio = 1` vs
`2` divergence), the §5.1 `setScale`-as-scale correction is **correct and value-changing as claimed**, and the
previously-`[UNVERIFIED]` hosted rounding-mode default was chased to ground and resolved **correctly**
(`MathContext(19, HALF_EVEN)` — I confirmed all four links of that config chain). It is rejected anyway, on money-path
grounds: **§7.4 was never touched.** Lines 931–937 still carry revision 1's factually refuted month-end rule verbatim
("`2026-02-28` + 1 month yields `2026-03-28`, **not** `2026-03-31` — `LocalDate` does not remember the original
day-of-month"), and line 940 still carries the "cancel to `1`" claim — both of which §4.4 and §4.2 now explicitly
refute forty lines earlier, and the wrong version is the one propagated into the vector matrix (§8 row `ls-008`,
line 982: "Feb 28, then Mar 28 not 31"). A document that states both semantics and instructs the implementer with the
wrong one is worse than the original, because the reader has no way to know which section governs. Independently: `mc`
is **still not pinned** in §8 (required change #5, and §4.2 line 507 falsely claims it is), and I found a **new
money-path defect** — §1.2 field 19 and §7.2 declare `allowFullTermForTranche` "dead for the embeddable
single-disbursement path", but it is a caller-settable model-data field that reaches an alternative EMI path through
a guard (`ProgressiveEMICalculator.java:142-144`) that never consults multi-disbursement at all.

---

## The 12-item adjudication

| # | Prior required change | Verdict | Evidence in attempt 2 |
|---|---|---|---|
| 1 | Correct §4.4 **and §7.4** month-end date stepping; restate `ls-008`/`ls-010` | **PARTIAL — rejection ground** | §4.4 (`:530-618`) fully and **correctly** rewritten; `adjustDate` cited at `DSDG:168-176` and its call site `:130-131`; terms 181/182 correct. But **§7.4 `:931-937` is revision 1's text unchanged**, and §8 `ls-008` (`:982`) repeats it |
| 2 | Remove "redundant clamp"; state `setScale(precision-as-scale)` is value-changing; add to §9 inventory | **LANDED** (§9 sub-item not landed) | §5.1 item 2 (`:630-655`) correct; `PEMI:1959-1962` + partial-period leaf `:1976-1979` both verified. §9 inventory still has 9 items, no `setScale` item |
| 3 | Correct §4.2 **and §7.4** "cancels to 1" | **PARTIAL — rejection ground** | §4.2 (`:469-493`) correct, three pre-`setScale` values reproduced exactly. **§7.4 `:940` still says the day counts "cancel to `1` regardless"** |
| 4 | `MoneyHelper` reachability — at least three fallback paths | **LANDED** | §5.2 (`:745-760`) enumerates all three; §5.3 three-overload table (`:783-787`) accurate. All six `Money.java` citations verified |
| 5 | Pin one `MathContext` in §8 | **NOT LANDED — rejection ground** | `:967` still "should be pinned explicitly (e.g. …, or the project's chosen capture precision)". Worse: §4.2 `:507` asserts "§8 therefore pins one MathContext", and the `HALF_UP` example contradicts §5.2's own `HALF_EVEN` finding |
| 6 | §3.1 `repaymentEvery` vs `calculatePeriodRatio` | **LANDED — and correct** | `:274-312`. All 10 citations verified. The `periodRatio = 1` vs `2` claim independently re-derived (see below) |
| 7 | Fix the two bad citations; re-tag `LAT:600`; ban hedges inside `[VERIFIED]` | **LANDED** | §5.2 `:737-743` re-sourced structurally; §5.3 split into three correct citations; §7.2 `:912-913` clean tag; header `:10-11` states the rule |
| 8 | De-degenerate the matrix (tz rows / `ls-001` label / `ls-009` note) | **(a) NOT LANDED, (b) NOT LANDED, (c) PARTIAL** | `ls-001`/`ls-002` (`:975-976`) still byte-identical inputs, no instant, no derived `LocalDate`; `ls-001` still labelled "divides-evenly" (100000000 ÷ 6 = 16666666.67); `ls-009` note exists at `:602-605` but not on the row |
| 9 | §6 `:1162-1174` is not a guard clause | **LANDED — and correct** | `:853-863`; four-row table checked line-by-line against `PEMI:1162-1215` |
| 10 | Strengthen the recurrence note | **LANDED — exceeded** | `:170-194`; all four denominators and all three EMIs independently reproduced exactly |
| 11 | Complete §9 int64 guidance (exact scale-2 reinterpretation, never a division) | **NOT LANDED** | §9 item 1 (`:1011-1014`) is unchanged from revision 1; still "the equivalent `BigDecimal`-shaped value" |
| 12 | Cosmetic (`Money.copy(0.0)`, off-by-one ranges, elided paths) | **PARTIAL** | Module/path contract fixed well (`:86-94`); `PLSG:294-353` and `PEMI:718-728`/`730-751` corrected. `Money.copy(0.0)` at `PEMI:1788` still unnamed; `PLISM:75-92` off-by-one persists |

---

## My independent re-derivations (all figures computed, none read back)

### Regression check — the golden test, re-derived end to end

Inputs from `EmbeddableProgressiveLoanScheduleGeneratorTest.java:44-70`: principal 100, 7.0 % annual, 6 × MONTHS,
`DAYS_30`/`DAYS_360`, `mc = MathContext(12, HALF_UP)`, currency 2 dp, start = disbursement = 2024-01-01,
`installmentAmountInMultiplesOf = null`.

| quantity | my value |
|---|---|
| `interestRate` = 7.0 ÷ 100 @mc | `0.07` |
| `interestFractionPerPeriod` = 30 × 1 ÷ 360 @mc | `0.0833333333333` |
| `interestRate × fraction` @mc | `0.00583333333333` |
| pre-`setScale`, 31-day / 29-day / 30-day period | `0.00583333333332` / `0.00583333333334` / `0.00583333333333` |
| post-`setScale(12, HALF_UP)`, all periods | `0.005833333333` |
| `r = 1 + rf` (exact `BigDecimal::add`, 13 sig digits) | `1.005833333333` |
| `rateFactorPlus1N` = Π(r) @mc | `1.03551440397` |
| `fnResult` via the recurrence | `6.08818353993` |
| raw EMI @mc | `17.0085937321` |
| **EMI after `Money.of` → `setScale(2, HALF_UP)`** | **`17.01`** |

| period | days | balance | raw interest | interest | principal | test |
|---|---|---|---|---|---|---|
| 1 | 31 | 100.00 | 0.583333333300 | **0.58** | **16.43** | 16.43 / 0.58 ✅ |
| 2 | 29 | 83.57 | 0.487491666639 | **0.49** | **16.52** | 16.52 / 0.49 ✅ |
| 3 | 31 | 67.05 | 0.391124999979 | **0.39** | **16.62** | 16.62 / 0.39 ✅ |
| 4 | 30 | 50.43 | 0.294174999983 | **0.29** | **16.72** | 16.72 / 0.29 ✅ |
| 5 | 31 | 33.71 | 0.196641666655 | **0.20** | **16.81** | 16.81 / 0.20 ✅ |
| 6 | 30 | 16.90 | 0.0985833333276 | **0.10** | **16.90** (EMI 17.01 → **17.00**) | 16.90 / 0.10 ✅ |

Loan term = 31+29+31+30+31+30 = **182** days; total interest **2.05**; total repayment **102.05**; residual
`diff = 100.00 + 2.05 − (6 × 17.01 = 102.06) = −0.01`, landed wholly on period 6.
**Nothing the prior review recorded as correct has been lost or corrupted.** Every figure the rewrite retained is right.

### §2.2 recurrence vs closed form — reproduced exactly

| denominator | doc | mine |
|---|---|---|
| recurrence `fn_6` | `6.08818353993` | `6.08818353993` ✅ |
| closed form `(Πr − 1)/(r − 1)` | `6.08818353806` | `6.08818353806` ✅ |
| closed form via a single `pow` | `6.08818353978` | `6.08818353978` ✅ |
| exact rational reference | `6.088183539935125…` | `6.088183539935125140642…` ✅ |
| raw EMIs | `17.0085937321` / `…373` / `…325` | identical ✅ |

Also verified §2.2 `:200-202`: rounding the `+1` to 12 *significant* digits (`1.00583333333`) instead of adding
exactly gives `fn_6 = 6.08818353990` — the document says `6.0881835399`. **Same value; claim holds.**

### §4.4 date stepping — re-derived from `adjustDate`, both semantics

| row | Fineract (`plusMonths` → `adjustDate`) | days | term | naive (§7.4's surviving text) | term |
|---|---|---|---|---|---|
| `ls-008` 2026-01-31 × 6M | 02-28, **03-31**, **04-30**, **05-31**, **06-30**, **07-31** | 28,31,30,31,30,31 | **181** | 02-28, 03-28, 04-28, 05-28, 06-28, 07-28 | 178 |
| `ls-010` 2027-11-30 × 6M | 12-30, 01-30, 02-29, **03-30**, **04-30**, **05-30** | 30,31,30,30,31,30 | **182** | …, 03-29, 04-29, 05-29 | 181 |
| `ls-009` 2028-02-29 × 12M | 03-29 … 2029-01-29, 2029-02-28 | 29,31,30,31,30,31,31,30,31,30,31,30 | **365** | identical | 365 |
| golden 2024-01-01 × 6M | 02-01 … 07-01 | 31,29,31,30,31,30 | **182** | identical | 182 |

**§4.4's table (`:591-594`) is correct in every cell.** §7.4 and §8 `ls-008` describe the right-hand column.
Confirmed that `ls-009` cannot discriminate (`min(lengthOfMonth, 29)` equals the `plusMonths` clamp every month) and
neither can the golden test (seed day 1 never trips the `> 28` guard) — so **no currently-passing test catches this.**

Full `ls-008` money schedule under both semantics (19.99 %, 1,500,000₮, my derivation): EMI `264776.68` and the
per-period interest/principal are *identical* either way — because at 19.99 % the rate factor is day-length
insensitive — but the **due dates differ on periods 2–6 and the term differs 181 vs 178**. Since §8 `:992-994`
requires capturing `periodFromDate`/`periodDueDate` per row, a port built to §7.4 fails those fields on every
month-end loan.

### §3.1 `calculatePeriodRatio` — the month-end `plusDays(1)` branch, re-derived

Re-implementing `calculateSeedDate` (`PEMI:1461-1481`) and `calculatePeriodRatio` (`PEMI:1419-1459`) with and
without the branch at `PEMI:1432-1433`:

| row | `periodRatio` WITH branch | WITHOUT branch |
|---|---|---|
| `ls-008` | `[1,1,1,1,1,1]` | `[1,**2**,1,**2**,1,**2**]` |
| `ls-010` | `[1,1,1,1,1,1]` | `[1,1,1,**2**,1,1]` |
| `ls-009` | all `1` | all `1` |
| golden | all `1` | all `1` |

The document's claim — period 2 of a 2026-01-31 loan gives `periodRatio = 1` with the branch and `2` (double
interest) without — is **exactly right**. Worked mechanism for that period: `calculateSeedDate` returns the schedule
start 2026-01-31; `ChronoUnit.MONTHS.between(2026-01-31, 2026-02-28) = 0` (Java packed arithmetic) but
`…between(2026-01-31, 2026-03-01) = 1`, and the `+1`/`−1` walk then yields `1` vs `2`. **§3.1 is the strongest
section in the document.**

### §5.1 — is `setScale(precision-as-scale)` really value-changing?

Yes. Measured at `MathContext(12, HALF_UP)`, `DAYS_30`/`DAYS_360`:

| annual rate | pre-`setScale` | post-`setScale(12)` | changed? |
|---|---|---|---|
| 7.0 % | `0.00583333333332` (31 d) | `0.005833333333` | **YES** |
| 19.99 % | `0.0166583333333` | `0.016658333333` | **YES** |
| 13.75 % | `0.0114583333333` | `0.011458333333` | **YES** |
| 16.40 % | `0.0136666666667` | `0.013666666667` | **YES** |
| 18.50 % | `0.0154166666667` | `0.015416666667` | **YES** |
| 24.00 / 12.00 / 21.75 / 30.00 / 36.00 % | terminating | unchanged | no |

**The document's correction is right and the prior review's finding is confirmed.** Also confirmed §4.2's precision-19
corollary (`:505`): pre-values `0.005833333333333333332 / …334 / …333`, flattened by `setScale(19)` to
`0.0058333333333333333` — exactly as stated.

*Refinement the document could use (non-blocking):* the multiply/divide pair produces **three distinct** pre-values
only for 7.0 %; for all nine other rates in the §8 matrix the pair is already exactly inverse at 12 digits. §4.2's
sentence is correctly scoped ("…behaves like a fixed convention **here**"), so it holds — but the reader would be
better served knowing the golden test is the unusual case, not the typical one.

### Claims the prior review never examined — two re-derived

- **§3.2** ("`divide(L, mc)` then `multiply(L, mc)` … agree to the cent for all six periods in the golden test, but
  that is an accident"). Re-derived both spellings for all six periods: `0.58/0.49/0.39/0.29/0.20/0.10` under the
  three-operation form and the one-operation form alike. **Claim HELD**, hedge correctly stated.
- **§7.1 / §7.5.** Zero rate: `rf = 0`, `Πr = 1.00000000000`, `fn = 6.00000000000` — exactly integer `N`, **no
  drift**, `EMI = P/N`; for `ls-004` (1,000,001.00 over 7) raw EMI `142857.285714` → `142857.29`, residual `−0.03`,
  so the row genuinely exercises §6. Single period (`ls-007`, 500,000₮ @ 15 %): `fn = 1`, `Πr = r₁`,
  `EMI = 506250.00 = P × (1 + rf)`, interest `6250.00`, principal `500000.00`, residual `0.00`. **Both HELD.**

---

## `[UNVERIFIED]` adjudication — 5 occurrences

| line | what it is | verdict |
|---|---|---|
| 10, 11 | Legend / tagging rule. Not claims. | n/a (per brief) |
| 709 | "Revision 1 marked this `[UNVERIFIED]`. It is reachable in this checkout; chased and resolved" — a **resolution**, not an open marker | **RESOLVED, and the resolution is CORRECT.** I verified all four links independently: `MoneyHelperStartupInitializationService.java:50-71` → `MoneyHelperInitializationService.java:57-80`, `:102-106` → `GlobalConfigurationConstants.java:41` (`"rounding-mode"`) → `0002_initial_data.xml:219-220` → `application.properties:514` → `:77` (`${FINERACT_CONFIG_ROUNDING_MODE:6}`), and `barebones_db.sql:295`'s own comment `6 - HALF_EVEN`. `RoundingMode.valueOf(6)` = `HALF_EVEN`. **Hosted default is `MathContext(19, HALF_EVEN)`. Genuine, well-executed work.** |
| 954 | §7.5 — absence of a `numberOfRepayments == 1` special case, hedged as grep-only over the re-age/reschedule regions | **ACCEPTABLE.** Negative existence claim over ~2,200 lines; hedge proportionate. I settled what is settleable: `DSDG:58-73` and `PLSG:116-145` contain no such guard, and my emulator confirms the single-period math behaves exactly as §7.5 describes. Not a rejection ground |
| 1087 | Backlog: "`MoneyHelper`'s production default `RoundingMode` … flagged `[UNVERIFIED]` above (§5.2)" | **STALE — must be removed.** §5.2 resolved it 378 lines earlier and I confirmed the resolution. An `[UNVERIFIED]` marker in the money path that the *same document* already settles is exactly the kind the brief says to settle. Answer: `HALF_EVEN`, seeded from `FINERACT_CONFIG_ROUNDING_MODE` default `6` |

Net: **1 genuinely open and honestly scoped; 1 stale and self-contradicting; 1 resolved correctly; 2 legend.**

---

## My own citation spot-check — 47 checked, 45 held, 2 did not support their claim

**Held** (opened at the cited line; says what the document claims):
`DSDG:50-75`, `:61-67`, `:116-161`, `:119-122`, `:128-131`, `:168-176`, `:311-333`, `:58-73`;
`PEMI:75`, `:126-135`, `:137-153`, `:142-144`, `:155-174`, `:636-644`, `:718-728`, `:730-751`, `:737-750`,
`:1160-1219`, `:1162-1174`, `:1176-1181`, `:1206-1209`, `:1211-1215`, `:1258-1309`, `:1288`, `:1308`, `:1318-1320`,
`:1342-1353`, `:1355-1417`, `:1403-1413`, `:1413`, `:1419-1459`, `:1425-1437`, `:1443-1455`, `:1453-1454`,
`:1457-1458`, `:1461-1481`, `:1486-1540`, `:1500-1503`, `:1508`, `:1536-1537`, `:1550-1568`, `:1598-1611`,
`:1613-1672`, `:1674-1683`, `:1722-1742`, `:1724`, `:1725-1726`, `:1731-1733`, `:1761-1766`, `:1770-1776`,
`:1816-1820`, `:1822-1828`, `:1830-1833`, `:1838-1841`, `:1846-1849`, `:1922-1927`, `:1950-1963`, `:1959-1962`,
`:1976-1979`, `:1982-1993`;
`Money.java:40-53`, `:48-51`, `:52`, `:102-104`, `:118-120`, `:130-132`, `:134-148`, `:150-157`, `:159-161`,
`:163-170`, `:494-496`, and the `getMc()` sites `:237,250,294,419,487`;
`MoneyHelper.java:35`, `:54-65`, `:74-82`, `:91-94`, `:182-189`;
`LoanApplicationTerms.java:278-279`, `:324`, `:333-335`, `:393-577` (complete setter list — and I confirmed
`calculatedRepaymentsStartingFromDate`, `multiDisburseLoan`, `repaymentStartDateType` and
`interestCalculationPeriodMethod` have **no** Builder setter, exactly as claimed), `:583-589`, `:600`, `:602`,
`:803`, `:812`, `:1774-1776`;
`PLSG:81-84`, `:86-99`, `:94-96`, `:116-145`, `:147-150`, `:294-353`, `:335-338`;
`RepaymentPeriod.java:209-218`, `:216-218`, `:293-296`, `:345-350`;
`InterestPeriod.java:145-158`, `:160-162`, `:164-166`, `:168-179`, `:180-187`;
`MathUtil.java:499-501`; `DateUtils.java:319-321`; `PeriodFrequencyType.java:70-72`;
`DaysInYearType.java:36-40,81-86,85`; `DaysInMonthType.java:34-36,75-80`; `CurrencyData.java:39`;
`LoanRepaymentScheduleModelData.java:32-39` (19 fields, order matches the §1.2 table exactly);
`ProgressiveLoanInterestScheduleModel.java:65`; `EmbeddableProgressiveLoanScheduleGenerator.java:38-43` (correctly
re-sourced — structural, no javadoc claim), `:45-47`;
`Main.java:42`, `:56-57`; `Test:44`, `:48-49`, `:58-59`, `:60`, `:81-83`, `:120-122`;
`MoneyHelperStartupInitializationService.java:50-71`; `MoneyHelperInitializationService.java:57-80`, `:102-106`;
`GlobalConfigurationConstants.java:41`; `0002_initial_data.xml:219-220`; `application.properties:77`, `:514`;
`barebones_db.sql:295`.

**Did not support the claim:**

1. **`PEMI:142-144, 155-174` → §1.2 field 19 / §7.2 "dead for the embeddable single-disbursement path".** The lines
   exist; the conclusion drawn from them is false. See NEW-1 below.
2. **`PEMI:737-750` → §2.1's "fixed post-order", presented as complete with "A Go port must preserve this order".**
   The list omits `applyInterestMoratoriumIfRequired(scheduleModel)`, which is the **first** call in the cited
   range (`:737`), and collapses the `onlyOnActualModelShouldApply` branch (`:740-744`) to its true-arm only.

**Minor drift (not defects):** `ProgressiveLoanInterestScheduleModel.java:75-92` (public constructor starts 74 — the
same off-by-one the prior review flagged as change #12); `PEMI:1502-1503` is named `calculatedDaysInRepaymentPeriod`
in `calculateRateFactorPerPeriod`, not `calculatedDaysInPeriod`. The document cites paths as `/Users/buv/fineract`
while this checkout is `/home/user/fineract` — same convention as revision 1 and the prior review; machine-dependent,
noted only so a future reader is not confused.

---

## NEW money-path defects found in attempt 2

**NEW-1 (most serious). `allowFullTermForTranche` is declared dead; it is reachable and it selects a different EMI
path.** §1.2 field 19 (`:75`) — "Governs tranche re-amortization; **dead for the embeddable single-disbursement
path** — see §7.2" — and §7.2 (`:903-918`), which folds `addFullTermTrancheDisbursement` into a conclusion whose
entire evidence concerns `disbursementDatas` and `multiDisburseLoan`. Traced:

- `LoanRepaymentScheduleModelData.java:39` — `allowFullTermForTranche` is model-data field 19, caller-settable.
- `LoanApplicationTerms.java:606` — `assembleFrom` wires it: `.allowFullTermForTranche(modelData.allowFullTermForTranche())`.
  It **does** have a Builder setter, at `:558-560` (unlike `multiDisburseLoan`).
- `LoanApplicationTerms.java:1755` — carried into `toLoanConfigurationDetails()`.
- `ProgressiveEMICalculator.java:142-144` — the guard is
  `isAllowFullTermForTranche() && numberOfRepayments > 0 && operation.getAction() == DISBURSEMENT`.
  **`isMultiDisburseLoan()` is not consulted, and neither is `disbursementDatas`.** All three conjuncts are satisfied
  by an ordinary single disbursement from the embeddable entry point.
- Consequence: control goes to `addFullTermTrancheDisbursement` (`:155-174`) → `buildLoanApplicationTerms` →
  `generateTemporaryScheduleModel` → `mergeNewScheduleModelWithExistingOne`, instead of the
  `changeOutstandingBalanceAndUpdateInterestPeriods` → `calculateEMIValueAndRateFactors` path §2.1 documents.
- That path also calls the **2-arg `Money.zero(CurrencyData)`** at `ProgressiveEMICalculator.java:182`
  → `MoneyHelper.getMathContext()` → `IllegalStateException` outside an initialised tenant — a fourth `MoneyHelper`
  fallback, inside the very module being ported, which §5.2's three-path list does not contain and which §5.1
  (`:675-677`, "the explicit `mc` passed in every non-trivial case") implicitly denies.

I proved reachability and the guard's actual condition. I did **not** determine whether the merged schedule differs
numerically for a single disbursement — but that is precisely why it needs a vector row, and §8 currently pins
`allowFullTermForTranche = false` for all 16 rows on the strength of a false "dead" claim.

**NEW-2. Three false forward-references from §4 into §8.** §4.2 `:507` — "§8 therefore pins one `MathContext` for the
whole vector matrix" (§8 `:967` does not pin one). §4.4 `:617-618` — "§8 pins them equal for every row and adds one
row that deliberately separates them" (§8 never mentions `scheduleGenerationStartDate` at all, has no such column,
and has no such row). These are load-bearing: §4.4 correctly identifies that `periodStartDate = submittedOnDate =
scheduleGenerationStartDate` while the month-end seed is `disbursementDate` (`PLSG:94-96`, `LAT:583-589`, `:602` —
all verified), which is a real divergence the matrix then fails to cover.

**NEW-3. The "Correction log" does not exist.** The header cites it twice (`:12`, `:21`) as the record substantiating
"All 70 citations in this document were re-opened at their cited lines for revision 2". There is no such section
(headings run §1–§9 then Backlog), and the document actually carries 138 `[VERIFIED:` tags, not 70. Documentation
integrity, not arithmetic — but the header's audit claim is unsupported by the document that makes it.

---

## Non-negotiables scan (CLAUDE.md) — **CLEAN**

- **Float/double on a money path:** none prescribed. Every occurrence (`:304, 683, 790, 998, 1014, 1018, 1060-1066`)
  is a warning against float or a description of Fineract's own code. §9 items 3–5 and 8 are correct and are the right
  instruction. *One overbroad statement:* §9 item 9 (`:1060`) says no `double` was found anywhere in the traced path;
  `ProgressiveEMICalculator.java:1788` calls `Money.copy(0.0)` → `Money.java:220-222` → `BigDecimal.valueOf(double)`,
  on the `getEmiAdjustment` path. Value-safe (exact zero) but worth naming, per prior change #12.
- **Money in integer minor units:** §8 `:963` states it explicitly and every row's principal is minor units. ✅
- **Hard-coded tz offsets:** none. `:976` mentions "+07" descriptively for `Asia/Hovd`, not as an instruction. ✅
- **`first_name`/`last_name`:** zero hits. ✅
- **Deposit-insurance language:** zero hits. ✅
- **MySQL / MariaDB / Oracle Database / `ojdbc` / port 1521:** zero hits. ✅

---

## Required changes, priority order

1. **Rewrite §7.4 (`:928-944`) to match the corrected §4.4 — or delete it and cross-reference §4.4.** Both of its
   bullets are wrong: bullet 1 states the refuted naive `plusMonths` drift ("`2026-03-28`, **not** `2026-03-31`");
   bullet 2 states the refuted "cancel to `1`". Replace with the `adjustDate` re-anchor rule and a pointer to §4.2's
   `setScale` explanation. **After the edit, `grep -n "03-28\|does not \"remember\"\|cancel"` must return nothing that
   contradicts §4.4/§4.2.**
2. **Fix §8 row `ls-008`'s purpose column (`:982`).** It currently reads "(Feb 28, then Mar 28 not 31)". Replace with
   the derived due dates `02-28, 03-31, 04-30, 05-31, 06-30, 07-31`, days `28,31,30,31,30,31`, **term 181**. Add the
   same for `ls-010`: `12-30, 01-30, 02-29, 03-30, 04-30, 05-30`, days `30,31,30,30,31,30`, **term 182**.
3. **Correct §1.2 field 19 and §7.2 on `allowFullTermForTranche` (NEW-1).** State that it is a caller-settable model
   field wired at `LoanApplicationTerms.java:606` (Builder setter `:558-560`, carried at `:1755`) and that the guard
   at `ProgressiveEMICalculator.java:142-144` consults **only** `isAllowFullTermForTranche()`, `numberOfRepayments > 0`
   and `action == DISBURSEMENT` — never `isMultiDisburseLoan()`. Keep the (correct) multi-disbursement-is-unreachable
   argument, but stop letting it cover this flag. Add `Money.zero(CurrencyData)` at
   `ProgressiveEMICalculator.java:182` to §5.2's `MoneyHelper` fallback list as a fourth path, and soften §5.1
   `:675-677` accordingly (`PEMI:2186` is a second 2-arg site). Add one §8 row with
   `allowFullTermForTranche = true`, single disbursement.
4. **Pin `mc` in §8 (`:967`).** One explicit `MathContext(precision, RoundingMode)` as a matrix-level constant, with a
   note that precision doubles as the rate-factor scale (§5.1). Resolve the internal conflict: §5.2 now establishes
   the hosted oracle default is `HALF_EVEN`, so `HALF_UP` may not be offered as the example without saying why. Which
   one the capture pins is already flagged as a `user` decision at `:731-735` — reference that gate from §8 instead of
   leaving the field open.
5. **Remove the stale `[UNVERIFIED]` at `:1087`** and replace the backlog bullet with §5.2's answer
   (`MathContext(19, HALF_EVEN)`; default `6` from `FINERACT_CONFIG_ROUNDING_MODE`), leaving only the genuine open
   item — which capture mode the project pins.
6. **Fix the three false forward-references (NEW-2).** Either make §8 deliver what §4.2 `:507` and §4.4 `:617-618`
   promise — a pinned `mc`, `scheduleGenerationStartDate` pinned equal to `disbursementDate` on every row, and one row
   that deliberately separates them — or reword §4 to stop claiming it does. Delivering is preferable: the
   `submittedOnDate`-vs-`seedDate` split is real and currently uncovered.
7. **De-degenerate the matrix (prior #8, still open).** (a) `ls-001`/`ls-002` must carry a wall-clock instant + zone
   that resolves to *different* civil dates in +08 and +07, with the derived `LocalDate` recorded per row; as written
   they are byte-identical and prove nothing. (b) Relabel `ls-001` — 100000000 ÷ 6 = 16666666.67 minor units, it does
   not divide evenly; `ls-003` is the only genuinely even row. (c) Move the `ls-009`-cannot-discriminate note from
   `:602-605` onto the row itself.
8. **Complete §9 (prior #11, still open).** Item 1: state that the `int64` minor-unit ↔ decimal conversion is an
   **exact scale-2 reinterpretation, never a division**. Add the `setScale(precision-as-scale)` step from §5.1 as its
   own numbered hazard (prior #2's sub-requirement). Note that `:791` already forward-references "§9 item 10", which
   does not exist.
9. **Fix §2.1's post-order list (`:108-112`).** It is presented as the complete fixed order with "A Go port must
   preserve this order", but omits `applyInterestMoratoriumIfRequired` at `PEMI:737` — the first call in the range it
   cites — and collapses the `onlyOnActualModelShouldApply` branch at `:740-744`.
10. **Add the missing "Correction log" (NEW-3), or drop both references to it (`:12`, `:21`), and fix the citation
    count** (138 `[VERIFIED:` tags, not 70).

---

## Follow-ups that do NOT block acceptance

- §4.2 could note that the three-distinct-pre-values behaviour is specific to 7.0 %; for the other nine rates in the
  §8 matrix the multiply/divide pair is already exactly inverse at 12 digits. The `setScale` step remains
  value-changing for 5 of 10 rates tested, so the mandatory Go-port instruction is unaffected.
- Name `Money.copy(0.0)` at `ProgressiveEMICalculator.java:1788` (→ `Money.java:220-222`,
  `BigDecimal.valueOf(double)`) in §9 item 9 and explain why it is not a money-path float (exact zero sentinel).
  Prior change #12, still open; the project non-negotiable makes an unqualified "no `double` anywhere" claim worth
  tightening.
- Off-by-one: `ProgressiveLoanInterestScheduleModel.java:75-92` (constructor starts 74).
- `PEMI:1502-1503` is `calculatedDaysInRepaymentPeriod` in `calculateRateFactorPerPeriod`; §4.2 calls it
  `calculatedDaysInPeriod` (which is its name in the *interest* variant). Worth disambiguating given §3.1 turns on
  exactly that distinction.
- Footnote that `DaysInMonthType.DAYS_30`'s message key is literally `"DaysInMonthType.days360"`
  (`DaysInMonthType.java:36`) — a harmless upstream typo, but a reader grepping for it will be confused.
- The document's `/Users/buv/fineract` path prefix does not match this checkout (`/home/user/fineract`). Harmless,
  but a machine-independent module-relative form would age better.

---

## What attempt 2 got right — recorded so a third revision does not lose it

The full EMI/split arithmetic and residual absorption; the recurrence-vs-closed-form analysis (correct to the last
digit, and stronger than revision 1's); the exact `+1` observation at `RepaymentPeriod:216-218` and its 13-sig-digit
consequence; **§3.1 in its entirety**, including `calculatePeriodRatio`, `calculateSeedDate`, the month-end
`plusDays(1)` branch and the re-derived `periodRatio = 1` vs `2`; **§4.4's date rule and its worked table**;
§4.2's three pre-`setScale` values and the precision-19 corollary; §5.1's `setScale`-as-scale correction and its
Go-port requirement; §5.2's resolution of the hosted `HALF_EVEN` default (four-link config chain, all verified);
§5.3's three-overload `roundToMultiplesOf` table; §6's four-row correction of "guard clauses"; §7.1's zero-rate
collapse; §7.5's single-period algebra; §3.2's warning against simplifying the `divide`/`multiply` pair; and the
whole §9 float/`big.Rat`/`big.Float` analysis. The remaining defects are concentrated in **§7.4 (untouched from
revision 1)**, **§8 (matrix hygiene, still largely unaddressed)**, and the **`allowFullTermForTranche` reachability
claim**.
