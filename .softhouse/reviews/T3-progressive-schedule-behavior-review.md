# T3 Independent Review — `docs/analysis/progressive-schedule-behavior.md`

**Reviewer:** independent adversarial reviewer, no planning context.
**Run:** `2026-08-17-run1-harness-schedule-poc`, task T3.
**Source of truth:** `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` (read-only; not modified).
**Method:** every arithmetic claim re-derived from source, not read back. Java runtime is unavailable on this box,
so the BigDecimal/`MathContext` pipeline was re-implemented from the source line-by-line in an exact decimal
emulator (`/tmp/t3rev/derive.py`, `prec.py`, `dates.py`) and validated against the shipped golden test's
published expectations before being used to probe further.

---

# VERDICT: **REJECTED**

The document's headline numbers are **correct** — I reproduce EMI = 17.01 and the first three splits digit for
digit, plus periods 4–6, the residual absorption, total interest and loan term, all matching
`EmbeddableProgressiveLoanScheduleGeneratorTest`. The analyst genuinely did the arithmetic.

It is rejected anyway, on four independent grounds, each of which is a listed rejection criterion:

1. **A rounding step in the money path is mischaracterised as a no-op** (§5.1 "redundant clamp"). It is not
   redundant; it changes every rate factor. A Go port built from this document omits it and diverges.
2. **The day-count "cancels to 1" claim is arithmetically false** at the BigDecimal level (§4.2). It is only
   *made* true by the very step §5.1 declares redundant. The two errors are individually plausible and jointly
   fatal.
3. **The month-end date-stepping claim is factually refuted by source** (§4.4/§7.4). Fineract re-anchors to the
   seed day-of-month via an uncited `adjustDate`; the document asserts the opposite and instructs Go
   implementers accordingly. Vector rows `ls-008` and `ls-010` are described with wrong due dates.
4. **Undeclared unverified claims sitting in money paths**, and citations that do not support their claim
   (4 of 24 spot-checked).

---

## (a) EMI and the first three periods — RE-DERIVED

Inputs from the shipped test (`EmbeddableProgressiveLoanScheduleGeneratorTest.java:44-70`): principal 100,
annual nominal 7.0 %, 6 × MONTHS, `DAYS_30`/`DAYS_360`, `mc = MathContext(12, HALF_UP)`, currency 2 dp,
start = disbursement = 2024-01-01, `installmentAmountInMultiplesOf = null`.

Algorithm re-implemented exactly as sourced:
`calcNominalInterestRatePercentage` (`:1318-1320`) → `calculateRateFactorPerPeriod` (`:1486-1540`) →
`rateFactorByRepaymentEveryMonth` (`:1922-1927`) → `rateFactorByRepaymentPeriod` (`:1950-1963`) →
`getRateFactorPlus1` (`RepaymentPeriod.java:216-218`) → `calculateRateFactorPlus1NForEmi` (`:1816-1820`) /
`calculateFnResultForEmi` (`:1822-1828`) + `fnValue` (`:1991-1993`) → `calculateEMIValue` (`:1838-1841`) →
`Money.of` (`Money.java:40-53`) → `getCalculatedDueInterest` (`InterestPeriod.java:145-158`) →
`getDuePrincipal` (`RepaymentPeriod.java:345-350`) → `calculateLastUnpaidRepaymentPeriodEMI` (`:1160-1219`).

Intermediates I obtain:

| quantity | my value |
|---|---|
| `interestRate` = 7.0 ÷ 100 @mc | `0.07` |
| `interestFractionPerPeriod` = 30×1 ÷ 360 @mc | `0.0833333333333` |
| `interestRate × fraction` @mc | `0.00583333333333` |
| rate factor **before** `setScale(12)`, 31-day period | `0.00583333333332` |
| rate factor **before** `setScale(12)`, 29-day period | `0.00583333333334` |
| rate factor **before** `setScale(12)`, 30-day period | `0.00583333333333` |
| rate factor **after** `setScale(12, HALF_UP)` — all periods | `0.005833333333` |
| `rateFactorPlus1N` = Π(1+rf) @mc | `1.03551440397` |
| `fnResult` via the recurrence | `6.08818353993` |
| raw EMI = `rateFactorPlus1N × 100 ÷ fnResult` @mc | `17.0085937321` |
| **EMI after `Money.of` → `setScale(2, HALF_UP)`** | **`17.01`** |

Schedule (balance, raw interest, `Money`-rounded interest, principal = EMI − interest):

| period | my balance | my raw interest | my interest | my principal | doc / test |
|---|---|---|---|---|---|
| 1 | 100.00 | 0.583333333300 | **0.58** | **16.43** | 16.43 / 0.58 ✅ |
| 2 | 83.57 | 0.487491666639 | **0.49** | **16.52** | 16.52 / 0.49 ✅ |
| 3 | 67.05 | 0.391124999979 | **0.39** | **16.62** | 16.62 / 0.39 ✅ |
| 4 | 50.43 | 0.294174999983 | 0.29 | 16.72 | test: 16.72 / 0.29 ✅ |
| 5 | 33.71 | 0.196641666655 | 0.20 | 16.81 | test: 16.81 / 0.20 ✅ |
| 6 | 16.90 | 0.098583333328 | 0.10 | 16.90 (EMI adjusted 17.01 → **17.00**) | test: 16.90 / 0.10, total 17.00 ✅ |

Also independently reproduced: loan term = 31+29+31+30+31+30 = **182 days** (test asserts 182), total interest
**2.05**, total repayment **102.05**, closing balance **0.00**, and the §6 residual: `diff = 100.00 + 2.05 −
(17.01 × 6 = 102.06) = −0.01`, landed entirely on the last period.

**Finding (a): CONFIRMED, digit for digit.** The document's §9 claim of hand-matching to the cent holds, and
extends to periods 4–6 and the balancing step, which the document did not claim but which I checked anyway.

### Recurrence vs closed form — the claim held, and is stronger than the document states

Source confirms the recurrence: `calculateFnResultForEmi` (`:1822-1828`) is `stream().skip(1).reduce(ONE,
fnValue)` and `fnValue` (`:1991-1993`) is `1 + prev × r`. `.skip(1)` does seed `fn_1 = 1`. Algebraically, for
constant `r`, `fn_N = Σ_{j=0}^{N-1} r^j = (r^N − 1)/(r − 1)`, so `EMI = P·r^N(r−1)/(r^N−1)` — the standard
annuity formula. The document's algebra is right, and the code genuinely never computes the closed form.

But the document says they are "algebraically equivalent … via the geometric-series identity" and leaves the
reader to infer that the distinction only matters "under time-varying rates, interest-rate changes, or
interest-pause periods". **That is understated.** Under `MathContext(12, HALF_UP)`, with a *constant* rate,
I get:

| denominator | value |
|---|---|
| recurrence `fn_6` (what Fineract computes) | `6.08818353993` |
| closed-form `(r^6 − 1)/(r − 1)` @ same mc | `6.08818353806` |
| raw EMI, recurrence | `17.0085937321` |
| raw EMI, closed form | `17.0085937373` |

They diverge at the **10th significant digit even in the simplest possible case**. Both happen to round to
17.01 here, but nothing guarantees that; the document should state that the two are *not* numerically
interchangeable at any precision, not merely under exotic rate scenarios. **Claim held; wording needs
strengthening.**

---

## (b) Rounding — mode AND scale. **PARTLY REFUTED. This is a rejection ground.**

Traced, and correct in the document:
- `mc` is caller-supplied, threaded, never re-created. `grep -c "new MathContext"` in
  `ProgressiveEMICalculator.java` = **0** ✅ (document's claim verified independently).
- `scheduleModel.mc()` is the single field `ProgressiveLoanInterestScheduleModel.java:65`, assigned from the
  constructor `mc` ✅.
- `Money`'s private constructor (`Money.java:40-53`) ends in `setScale(currency.getDecimalPlaces(),
  getMc().getRoundingMode())` — currency-scale rounding, 2 dp for MNT/USD ✅.
- `MoneyHelper.PRECISION = 19` (`:35`), `getRoundingMode()` throws if the tenant is uninitialised (`:74-82`),
  `getMathContext()` = `new MathContext(19, getRoundingMode())` (`:91-94`), rounding mode populated by
  `initializeTenantRoundingMode` (`:54-65`) ✅. All four citations open exactly where claimed.

### B1 — `.setScale(mc.getPrecision(), …)` is NOT a "redundant clamp" (§5.1, item 1)

Source, `ProgressiveEMICalculator.java:1959-1962`:

```java
return interestRate.multiply(interestFractionPerPeriod, mc).multiply(actualDaysInPeriod, mc)
        .divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode());
```

`mc.getPrecision()` is **significant digits**; `setScale(n, …)` takes **decimal places**. Fineract feeds the
precision into the *scale* slot. For a rate factor of magnitude 10⁻³, 12 significant digits is 14 decimal
places, so `setScale(12)` **truncates two digits off every single rate factor**:

| | value |
|---|---|
| after `.divide(calculatedDaysInPeriod, mc)` | `0.00583333333332` (14 dp) |
| after `.setScale(12, HALF_UP)` | `0.005833333333` (12 dp) |

That is a real, value-changing rounding step in the money path, and the document tells a Go implementer it is
redundant. I ran the pipeline with the step omitted: the per-period rate factors become **three distinct
values** instead of one (`0.00583333333332` / `0.00583333333334` / `0.00583333333333`) — see B2.

**Verdict: rounding scale asserted rather than traced. Rejection ground.**

### B2 — "the ratio is exactly 1 and calendar days cancel out" is false (§4.2 / §7.4)

The document says that when `actualDaysInPeriod == calculatedDaysInPeriod` the ratio "is exactly `1`" and
"the real calendar-day counts cancel out". In exact arithmetic, yes. In Fineract's arithmetic, **no**:
`multiply(actual, mc)` then `divide(calculated, mc)` are two separately-rounded operations and are not
mutually inverse. My table above shows the 31-day, 29-day and 30-day periods producing three *different*
pre-`setScale` values from identical inputs.

The cancellation the document asserts is not a property of the formula — it is an artifact of the `setScale`
step the document simultaneously dismisses. Believe both §4.2 and §5.1 and you build a Go port whose rate
factors vary by calendar month under a supposedly fixed 30/360 convention. **Rejection ground.**

Corollary the document misses entirely: because `setScale` uses `mc.getPrecision()` as a *scale*, the choice
of capture `MathContext` changes intermediates non-trivially. I verified at precision 19 (the document's own
suggested capture setting): pre-`setScale` values `0.005833333333333333332` / `…334` / `…333`, clamped by
`setScale(19)` to `0.0058333333333333333`. It happens to collapse again here, but that is luck, not design,
and the document offers no analysis of it while recommending precision 19 for capture.

### B3 — the `installmentAmountInMultiplesOf` divergence is REAL but the document gets the mechanism wrong

Real, and correctly flagged: `safeRoundingForEMI` (`:1770-1776`) calls the **2-arg**
`Money.roundToMultiplesOf`, which is `roundToMultiplesOf(existingVal, inMultiplesOf,
MoneyHelper.getMathContext())` (`Money.java:159-161`) — the tenant-global context, not the threaded `mc`.
The down-payment site (`ProgressiveLoanScheduleGenerator.java:336-337`) passes `mc` explicitly. Outside an
initialised tenant this throws `IllegalStateException`. That is a genuine parity/capture hazard and the
document is right to gate it. ✅

But §5.3's supporting sentence — *"Both variants of `roundToMultiplesOf` do the same arithmetic —
`amountScaled.divide(inMultiplesOfValue, 0, mc.getRoundingMode())…`"* — is **wrong**. There are three
overloads (`Money.java:150,159,163`):
- `roundToMultiplesOf(BigDecimal, Integer)` @150 hard-wires **`MoneyHelper.getRoundingMode()`**, no `mc` in
  sight — and it is the one called from `Money`'s own constructor at `:45`.
- `roundToMultiplesOf(Money, Integer, MathContext)` @163 uses `mc.getRoundingMode()` for the divide, then
  returns **`Money.of(currencyData, amountScaled)`** — the **2-arg** `of`, which is
  `of(currency, amount, MoneyHelper.getMathContext())` (`Money.java:102-104`).

So the "explicit `mc`" down-payment path *also* lands in `MoneyHelper` for its final scale rounding. And
`Money.getMc()` (`:494`) is `mc != null ? mc : MoneyHelper.getMathContext()` — a third silent fallback.
§5.2's assertion that *"there is exactly one path where it still transitively reaches the tenant-scoped
`MoneyHelper`"* is therefore **false**: there are at least three. This is a money-path assertion presented as
traced fact. **Rejection ground (undeclared unverified claim).**

---

## (c) Day-count convention — traced, not assumed, but the conclusion is wrong in one place

The convention itself **is** properly traced, and I re-verified every link:
- `DaysInYearType.java:36-40` (enum values incl. `DAYS_360(360, …)`) and `:81-86` (`getNumberOfDays` returns
  `this.getValue()` unless `ACTUAL`) ✅
- `DaysInMonthType.java:34-36` / `:75-80` ✅ (note: `DAYS_30`'s message key is literally
  `"DaysInMonthType.days360"` — a Fineract typo, harmless, worth a footnote)
- `calculateRateFactorPerPeriod` `:1533-1539` dispatches `DAYS_30 → calculateRateFactorPerPeriodBasedOnRepaymentFrequency`
  with `daysInMonth = 30` ✅; `:1598-1611` → `MONTHS → rateFactorByRepaymentEveryMonth` ✅
- test/CI config is `DAYS_30` + `DAYS_360` (`Test:58-59`, `Main.java:56-57`) ✅
- `DateUtils.getDifferenceInDays` = `ChronoUnit.DAYS.between` (`DateUtils.java:319-321`) ✅
- `interestCalculationPeriodMethod` is never set by the `assembleFrom(modelData, mc)` Builder → null → the
  `isSameAsRepaymentPeriod()` shortcut is unreachable, as the document claims ✅ (verified: no
  `.interestCalculationPeriodMethod(...)` in the Builder chain at `LoanApplicationTerms.java:591-606`)

**Not traced / wrong:**

### C1 — the two rate factors are NOT "structurally near-identical" (§3.1)

`calculateRateFactorPerPeriod` (EMI) passes **`repaymentEvery`** into the `repaymentEvery` slot
(`:1536-1537`). `calculateRateFactorPerPeriodForInterest` (booked interest) passes a computed **`periodRatio`**
from `calculatePeriodRatio` (`:1404-1413`). `calculatePeriodRatio` (`:1419-1459`) contains its own explicit
month-end rule at `:1430-1436`:

```java
// In case target date is the last day of the month and the seed date day is later than the target date
// day, we need to move it by 1 days
if (targetDateLastDay == targetDateDay && seedDateDay > targetDateDay) { … plusDays(1) … }
```

and can return a **fractional** ratio (`:1453-1454`). For any irregular period — month-end starts,
`fixedLength`, stub first periods — the EMI rate factor and the interest rate factor are computed from
different multipliers. The document collapses them into one formula and never mentions `calculatePeriodRatio`
or its month-end rule. This is precisely the territory row `ls-008` is supposed to cover. **Money-path gap.**

### C2 — "cancels to 1": refuted above (B2).

---

## (d) Floating point — CONFIRMED CLEAN, guidance incomplete

- No `double`/`float` anywhere in the traced path. I re-checked `ProgressiveEMICalculator.java`,
  `RepaymentPeriod.java`, `InterestPeriod.java`, `Money.java`. The only `double` is the test helper
  `toDouble(BigDecimal)` at `Test:120-122` ✅ — and the document is right to warn that the golden-vector
  harness must not round-trip through it. Good catch, correctly cited.
- `Money.copy(0.0)` at `ProgressiveEMICalculator.java:1788` takes a `double` literal but is a zero-sentinel on
  a non-money-path (`getEmiAdjustment` early return) — not a violation, but the document's flat statement
  "no `double`/`float` was found anywhere in the money-arithmetic call path" would be more defensible with
  this named and dismissed.
- The document **does** say the right thing about Go: `big.Rat` is exact but has no
  "N-significant-digits + round" notion, `big.Float` is binary not decimal, neither is a drop-in for
  `BigDecimal`+`MathContext`, and rounding must be applied *at each call site in the same order* (§9 items
  3–5). That is correct and is the right instruction.
- **Incomplete, and it matters:** §9 never tells the implementer to reproduce the `setScale(precision-as-scale)`
  step (because §5.1 called it redundant), and never states concretely how int64 minor units interoperate
  with the ratio-precision type — it says "convert `int64` minor units → the equivalent `BigDecimal`-shaped
  value" without specifying that this is an exact scale-2 decimal, not a division. Nothing in the document
  pushes a reader toward `float64`, so there is **no float violation** — but the guidance as written does not
  yet get a Go implementer to a bit-exact port.

**Verdict (d): no floating-point violation. Guidance materially incomplete.**

---

## (e) Vector matrix — required coverage present, three degenerate rows, one unpinned parameter

| requirement | row(s) | my check |
|---|---|---|
| principal not dividing evenly by term | `ls-004` 100000100 ÷ 7 = 14285728.57…; `ls-005` 100000099 ÷ 9 = 11111122.11…; `ls-006` 733333337 ÷ 24 = 30555555.708… | ✅ all genuinely uneven |
| rate exactly 0 % | `ls-003`, `ls-004` | ✅ |
| month-end (Jan 31) disbursement | `ls-008` 2026-01-31 | ✅ present — **but described with wrong due dates**, see (f)/F1 |
| leap-year 2028-02-29 disbursement | `ls-009` 2028-02-29 | ⚠️ present but **degenerate for its stated purpose** — seed day 29 clamps identically with and without Fineract's `adjustDate`, so it cannot catch the real month-end rule. `ls-008`/`ls-010` are the rows that can. |
| `Asia/Ulaanbaatar` **and** `Asia/Hovd` | `ls-001`/`ls-002` and others | ⚠️ **degenerate.** The generator consumes a bare `LocalDate`; `ls-001` and `ls-002` are byte-identical inputs. Two rows that cannot differ prove nothing about tz handling. |

Other matrix defects I found by checking its own arithmetic:

- **`ls-001` is mislabelled** "Baseline **divides-evenly** case". 100000000 minor units ÷ 6 = 16666666.67 —
  it does **not** divide evenly (1,000,000₮ ÷ 6 = 166,666.67₮). `ls-003` (120000000 ÷ 6 = 20000000) is the
  only genuinely even row. Cosmetic, but it is exactly the kind of unchecked arithmetic this review exists to
  catch.
- **`mc` is not pinned.** §8 says "should be pinned explicitly (e.g. `MathContext(19, HALF_UP)` … or the
  project's chosen capture precision)". Given B1 — precision is used as a *scale* — an unpinned `MathContext`
  makes every row's intermediates undefined. A golden-vector matrix with an unpinned rounding context is a
  coverage gap, not a formatting nit.
- To make the tz rows non-degenerate they must specify a **wall-clock instant plus zone** that actually
  resolves to different civil dates in +08 and +07 (e.g. an instant at 23:30 `Asia/Hovd` = 00:30 next day
  `Asia/Ulaanbaatar`), and record the derived `LocalDate` per row.

---

## (f) The three declared `[UNVERIFIED]` items, and what was not declared

Exactly three tags exist (`grep -n UNVERIFIED` → lines 10 (the legend), 473, 639, 772 (backlog restatement of
473)). Judgement on each:

| # | claim | honest? |
|---|---|---|
| 1 | §5.2 — production default `RoundingMode` passed to `initializeTenantRoundingMode` at bootstrap | **Honest.** It genuinely lives in tenant/DB config outside this module. `MoneyHelper.java:54-65` confirms there is no compiled-in default and `getRoundingMode()` throws without one. Correctly out of reach. |
| 2 | §7.5 — absence of a `numberOfRepayments == 1` special case, verified by grep not exhaustive reading | **Honest and appropriately scoped.** A negative claim over ~2,200 lines; the hedge is proportionate. |
| 3 | §7.2 — `LoanApplicationTerms.assembleFrom` sets an empty `disbursementDatas()` list | **Gave up too early — and mis-tagged.** This is tagged `[VERIFIED: …LoanApplicationTerms.java:600 — cited by upstream research agent, not independently re-read in this session]`. A `[VERIFIED]` tag whose own text says it was not verified is a process failure. I opened line 600 in three seconds: `.inArrearsTolerance(Money.zero(…)).disbursementDatas(new ArrayList<>())`. The claim is **true**; there was no reason not to check. (I also confirmed the stronger part: `multiDisburseLoan` has no Builder setter at all → `isMultiDisburseLoan()` is `false`. §7.2's conclusion stands.) |

### Undeclared unverified claims — independent scan

**F1 (most serious defect in the document). §4.4 / §7.4 month-end date stepping is factually wrong.**

The document asserts, tagged `[VERIFIED: DefaultScheduledDateGenerator.java:50-75, 117-161, 311-333]`:

> `2026-01-31 + 1 month` yields `2026-02-28`, and further `+1 month` from `2026-02-28` yields `2026-03-28`,
> **not** `2026-03-31` — `LocalDate` does not "remember" the original day-of-month once clamped.

Source says otherwise. `generateNextRepaymentDate` (`DefaultScheduledDateGenerator.java:128-131`) does:

```java
dueRepaymentPeriodDate = getRepaymentPeriodDate(freq, repaymentEvery, lastRepaymentDate);   // plusMonths
dueRepaymentPeriodDate = (LocalDate) adjustDate(dueRepaymentPeriodDate,
        loanApplicationTerms.getSeedDate(), loanApplicationTerms.getRepaymentPeriodFrequencyType());
```

and `adjustDate` (`:168-176`, **never cited in the document**) explicitly re-anchors:

```java
if (frequencyType.isMonthly() && seedDate.get(DAY_OF_MONTH) > 28 && date.get(DAY_OF_MONTH) >= 28) {
    int adjustedDay = Math.min(YearMonth.from(date).lengthOfMonth(), seedDate.get(DAY_OF_MONTH));
    return date.with(DAY_OF_MONTH, adjustedDay);
}
```

The seed is the disbursement date (`LoanApplicationTerms.java:585-589`, `.seedDate(seedDate)` at `:602`), and
`calculatedRepaymentsStartingFromDate` is never set by this Builder (assigned only at `:803`), so the
`isFirstRepayment` shortcut is bypassed and `adjustDate` applies to **every** period including the first.

I simulated both semantics:

| row | Fineract (with `adjustDate`) | document's stated semantics |
|---|---|---|
| `ls-008` 2026-01-31, 6 × M | 02-28, **03-31**, **04-30**, **05-31**, **06-30**, **07-31** — days `[28,31,30,31,30,31]`, term **181** | 02-28, 03-28, 04-28, 05-28, 06-28, 07-28 — days `[28,28,31,30,31,30]`, term 178 |
| `ls-010` 2027-11-30, 6 × M | 12-30, 01-30, 02-29, **03-30**, **04-30**, **05-30** — term **182** | …, 03-29, 04-29, 05-29 — term 181 |
| `ls-009` 2028-02-29, 12 × M | identical either way (seed day 29 clamps the same) |
| golden test 2024-01-01 | identical either way — **which is why the passing golden test does not catch this** |

Severity: this is a `[VERIFIED]`-tagged claim, in the section that defines period boundaries (which feed
`actualDaysInPeriod`/`calculatedDaysInPeriod` and therefore interest), stated as an explicit instruction to Go
implementers ("this is a first-class golden-vector target"), and used to specify two vector rows. A Go port
built to this specification produces wrong due dates and a wrong loan term on every month-end loan. The cited
line range `117-161` *contains* the `adjustDate` call at 130-131 — the analyst read past it.

**F2.** §5.2: *"the embeddable generator is documented as Spring-free `[VERIFIED:
EmbeddableProgressiveLoanScheduleGenerator.java:38-43]`"*. Lines 38–43 are the no-arg constructor. **There is
no javadoc anywhere in that file.** The citation does not support the claim. (The claim is arguably true in
spirit — the class wires its collaborators by hand — but it is not "documented", and the file it points at
says nothing of the sort.)

**F3.** §5.3 "both variants … `mc.getRoundingMode()`" and §5.2 "exactly one path … reaches `MoneyHelper`" —
both false, see B3. Money path, presented as fact.

**F4.** §6 describes `ProgressiveEMICalculator.java:1162-1174` as "guard clauses". It is not a guard: it is an
active mutation loop that *reduces* `setEmi(...)` on any period whose outstanding principal exceeds
`totalDuePaidDiff`, with its own `minimumEMI` floor. Mischaracterising an EMI-mutating step as a guard is a
money-path omission, even though it is inert for a fresh single-disbursement schedule.

### Citation spot-check — **24 checked, 20 held, 4 did not support their claim**

Held (opened at the cited line, says what the document claims): `EmbeddableProgressiveLoanScheduleGenerator.java:45-47`;
`Test:44`, `:58-59`, `:60`, `:81-83`, `:120-122`; `Main.java:42`, `:56-57`; `MoneyHelper.java:35`, `:54-65`,
`:74-82`, `:91-94`; `Money.java:40-53`; `ProgressiveEMICalculator.java:75`, `:636-644`, `:1318-1320`,
`:1674-1683`, `:1722-1734`, `:1816-1828`, `:1838-1841`, `:1950-1963`, `:1982-1993`, `:1160-1219`, `:1258-1309`,
`:126-153`, `:1500-1503`, `:1342-1353`, `:1550-1568`, `:1613-1672`; `RepaymentPeriod.java:209-218`, `:293-296`,
`:345-350`; `InterestPeriod.java:145-158`, `:160-166`, `:168-179`; `DaysInYearType.java:36-40,81-86`;
`DaysInMonthType.java:34-36,75-80`; `CurrencyData.java:39`; `DateUtils.java:319-321`;
`ProgressiveLoanScheduleGenerator.java:81-84`, `:116-145`, `:147-150`, `:336-337`;
`ProgressiveLoanInterestScheduleModel.java:65`; `LoanRepaymentScheduleModelData.java:32-39` (19 components,
order matches); `LoanApplicationTerms.java:600`.

Did **not** support the claim:
1. `EmbeddableProgressiveLoanScheduleGenerator.java:38-43` → "documented as Spring-free" (F2).
2. `Money.java:150-170` → "both variants … `mc.getRoundingMode()`" (B3/F3).
3. `DefaultScheduledDateGenerator.java:117-161` → the month-end drift claim; the range contains the very call
   that refutes it (F1).
4. `ProgressiveEMICalculator.java:1962-1963, 1979-1980` → "redundant clamp"; the lines exist, they are not
   redundant (B1).

Minor citation drift (range off by one, not a defect): `ProgressiveLoanScheduleGenerator.java:294-353`
(method starts 293); `ProgressiveLoanInterestScheduleModel.java:75-92` (constructor starts 74);
`ProgressiveEMICalculator.java:718-751` (method starts 720). Also: §2.1 and §5.3 cite
`ProgressiveLoanScheduleGenerator.java` with an elided `.../` path, violating the document's own
"absolute path" contract — and the file is in `fineract-progressive-loan`, not `fineract-loan` where the
neighbouring citations point.

---

## Required changes, priority order

1. **Correct §4.4 and §7.4 month-end date stepping.** Cite `DefaultScheduledDateGenerator.adjustDate`
   (`:168-176`) and its call site (`:130-131`), and `LoanApplicationTerms.java:585-589,602` for
   `seedDate = disbursementDate`. State the actual rule: *`plusMonths`, then if the frequency is monthly and
   the seed day-of-month > 28 and the resulting day ≥ 28, re-anchor to `min(lengthOfMonth, seedDay)`.*
   Restate the `ls-008` and `ls-010` expected due dates and terms (181 and 182 days respectively). Also state
   that `calculatedRepaymentsStartingFromDate` is null on this path so the rule applies from period 1.
2. **Correct §5.1.** Remove "redundant clamp". State that `setScale(mc.getPrecision(), mc.getRoundingMode())`
   uses precision as a **decimal-place scale**, that it is value-changing, and that a Go port must reproduce
   it verbatim at each rate-factor leaf. Add it to the §9 hazard inventory as its own numbered item.
3. **Correct §4.2 and §7.4's "cancels to 1".** Replace with: in exact arithmetic the ratio is 1, but
   `multiply(actual, mc)` / `divide(calculated, mc)` are separately rounded and are not mutually inverse —
   show the three distinct pre-`setScale` values — and note that the collapse to a single rate factor is
   produced by the `setScale` step, not by the ratio.
4. **Correct §5.2 and §5.3 on `MoneyHelper` reachability.** There are at least three fallbacks:
   2-arg `Money.of` (`:102-104`), static `roundToMultiplesOf(BigDecimal, Integer)` (`:150-158`, hard-wired
   `MoneyHelper.getRoundingMode()`, called from `Money`'s own constructor at `:45`), and `Money.getMc()`
   (`:494`). Note that the 3-arg `roundToMultiplesOf` returns via the 2-arg `Money.of`, so the down-payment
   path is not `mc`-clean either. Escalate to the `user` gate as the document already recommends.
5. **Pin `mc` in §8.** One explicit `MathContext(precision, RoundingMode)` for the whole matrix, recorded as a
   matrix-level constant, with a note that precision doubles as the rate-factor scale (per change 2).
6. **Fix §3.1.** Document that the EMI rate factor uses `repaymentEvery` (`:1536-1537`) while the interest
   rate factor uses the computed `periodRatio` (`:1404-1413`), and describe `calculatePeriodRatio`
   (`:1419-1459`) including its month-end `plusDays(1)` rule (`:1430-1436`) and fractional return
   (`:1453-1454`).
7. **Fix the two bad citations.** Drop or re-source
   `EmbeddableProgressiveLoanScheduleGenerator.java:38-43` for "documented as Spring-free"; re-source
   `Money.java:150-170`. Re-tag `LoanApplicationTerms.java:600` as genuinely `[VERIFIED]` (it is) and remove
   the "not independently re-read" hedge from inside a `[VERIFIED]` tag — that pattern must never appear
   again.
8. **De-degenerate the matrix.** (a) Give the tz rows a wall-clock instant + zone that resolves to *different*
   civil dates in +08 and +07, and record the derived `LocalDate`. (b) Relabel `ls-001` — it does not divide
   evenly. (c) Note that `ls-009` cannot exercise the `adjustDate` re-anchor and that `ls-008`/`ls-010` are
   the rows that do.
9. **Fix §6's "guard clauses".** `:1162-1174` is an active EMI-reduction pass with a `minimumEMI` floor, not a
   guard.
10. **Strengthen the recurrence note (§2.2).** State that the recurrence and the closed form are equivalent
    only in exact arithmetic, and give the measured divergence at `MathContext(12, HALF_UP)` with a constant
    rate (`6.08818353993` vs `6.08818353806`) so no implementer is tempted to "optimise" it.
11. **Complete the §9 int64 guidance.** Specify that the minor-unit ↔ decimal conversion is an exact scale-2
    reinterpretation (never a division), and add the `setScale(precision-as-scale)` step from change 2.
12. *(Optional, cosmetic)* Note `Money.copy(0.0)`'s `double` sentinel at `:1788` and why it is not a money-path
    float; fix the three off-by-one citation ranges and the elided `.../` paths for
    `ProgressiveLoanScheduleGenerator.java` (which lives in `fineract-progressive-loan`).

---

## What the document got right — recorded so the rewrite does not lose it

The EMI/split arithmetic, the recurrence identification, the `fn_1 = 1` `.skip(1)` seed reading, the
per-period order of operations (EMI → interest → principal-as-remainder), the residual-absorption mechanism
and its 9 call sites, the zero-rate collapse to `principal / N`, the multi-disbursement unreachability
argument, the `installmentAmountInMultiplesOf` tenant-context hazard, the `stripTrailingZeros` warning, the
`big.Rat`/`big.Float` non-equivalence analysis, and the "never assert golden vectors through `toDouble`"
warning are all correct and independently confirmed. The defects are concentrated in §4.4/§7.4 (dates),
§5.1–5.3 (rounding mechanics) and §8 (matrix hygiene).
