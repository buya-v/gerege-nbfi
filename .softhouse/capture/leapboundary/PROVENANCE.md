# T55 — provenance of the leap-boundary ACTUAL/ACTUAL captures

**Task** T55, branch `softhouse/T55-leap-boundary-capture`, worker `test_writer`.
**Fire** local `20260819-170001` on Buyan's Mac. **The reference oracle (Fineract) was reachable and
every number in this directory is an OBSERVATION made on it** — nothing is computed, extrapolated,
interpolated or authored, except blocks explicitly labelled **RE-DERIVATION**.

---

## THIS TASK CAPTURES. IT DOES NOT PROMOTE.

> Nothing here is promoted into `.softhouse/vectors/**`, and nothing here is stored contract-shaped.
> Promotion is a different task with a schema being defined in parallel. Every artefact is either a
> raw HTTP response body exactly as it came off the wire, or its exact-text sidecar, or an analysis
> file derived from those two by committed code.
>
> Admitting `daysInYearCustomStrategy` to DEC-1's graded domain would be an **AMENDMENT** (DEC-1
> §4.4) — a gate no agent crosses. This pass takes observations so a properly-gated decision has
> evidence. No file under `docs/adr/**` or `nexus/**` was touched.

---

## Why this pass exists — the trap it is built to defeat

Finding **T48-N4**: the ACT/ACT **partial-period arm** computes

```
f_arm = Σ over years  days(segment_y) / Year.of(y).length()
```

[VERIFIED: `ProgressiveEMICalculator.java:1548-1568` `calculatePeriodFractions`, entered from
`:1526-1530`, factor formed by `rateFactorByRepaymentPartialPeriod` `:1969-1980`]

and the **plain** ACT/ACT branch computes

```
f_plain = actualDaysInPeriod / daysInYear
```

[VERIFIED: `:1533-1535` → `rateFactorByRepaymentPeriod` `:1950-1963`].

When **every year in play is 365 days** the segments are contiguous, so `Σ dᵢ/365 = (Σ dᵢ)/365` and
the two are **algebraically identical**. A cross-year vector inside a run of non-leap years
therefore grades the arm **not at all** — a port that ignored the arm entirely would score
identically. That is the promotion trap this pass is built to defeat, and — see `LB-NONLEAP` — to
**observe** rather than merely derive.

Also verified and load-bearing for the shape design:

* `getNumberOfDays` [VERIFIED: `:1346-1353`] substitutes 366 → 365 **only** when the
  `interestPeriodFromDate`'s year is leap **and** the strategy is `FEB_29_PERIOD_ONLY` **and** the
  repayment period does not contain 29 February. This is **effect (a)**, and it acts on
  `f_plain`'s denominator **only** — `f_arm` never reads `daysInYear`, it reads
  `Year.of(actualYear).length()` directly. **So `daysInYearCustomStrategy` does not change the
  arm's denominators at all; it only decides whether the arm is entered.**
* `partialPeriodCalculationNeeded` [VERIFIED: `:1505-1507`] = `daysInYearType == ACTUAL` **and**
  `interestPeriodDueDate.getYear() - interestPeriodFromDate.getYear() > 0` **and**
  (`strategy != FEB_29_PERIOD_ONLY` **or** `isPeriodContainsFeb29(period)`). This is **effect (b)**.
* `isPeriodContainsFeb29` [VERIFIED: `:1330-1340`] uses
  `DateUtils.isDateInRangeFromExclusiveToInclusive`, i.e. `from < 29-Feb <= due` — **from-exclusive**.
* the segment boundary is **31 December** of the year, because
  `getFractionPeriodDueDateForEndOfYear` [VERIFIED: `:1578-1584`] returns `LocalDate.of(year, 12, 31)`
  when `isInterestRecognitionOnDisbursementDate()` is false — and it **is** false on products 3/4/7,
  asserted in PostgreSQL by the capture script. T51 separately observed that the product/request
  flag is inert on this path; T55 does not re-litigate that, it just asserts the column.
* a `SAME_AS_REPAYMENT_PERIOD` product returns at `:1516-1524` **before** the partial-period branch,
  so the arm would be unreachable. All three products are `interest_calculated_in_period_enum = 0`
  (DAILY), asserted before capture.

---

## Which seam — determined from evidence, and the reasoning recorded

**Path B, the running server (`POST /loans?command=calculateLoanSchedule`), tenant `gerege`,
PostgreSQL 18.3.** Not a default; the other two seams were excluded on evidence.

* **Path A (the embeddable seam) is DISQUALIFIED for this pass, because it drops the independent
  variable.** `LoanApplicationTerms`'s private `Builder` constructor
  [VERIFIED: `LoanApplicationTerms.java:304-351`] **never copies** `builder.daysInYearCustomStrategy`
  [VERIFIED: declared `:380`, set by the setter `:567-570`] into the field [VERIFIED: `:291`], so
  `toLoanConfigurationDetails()` [VERIFIED: `:1746-1756`] passes `null` regardless. T48 **observed**
  the drop: feeding `FEB_29_PERIOD_ONLY` or `FULL_LEAP_YEAR` through Path A produced **0 of 87 cells
  different** from feeding nothing. *A capture through a seam that drops your independent variable
  is worthless and looks fine* — that is exactly the failure mode named in the T55 brief, and it is
  why Path A is not used here.
  (Path A has a second, unrelated limit recorded by the driver this fire: at
  `ProgressiveLoanScheduleGenerator.java:83` — `return LoanSchedulePlan.from(generate(mc,
  loanApplicationTerms, null, null));` — both `loanCharges` **and** `holidayDetailDTO` are hard-wired
  `null`. Not relevant to T55: **no T55 capture carries a charge or a holiday**.)
* **Path A2 (the `ProgressiveEMICalculator` seam) was not used.** It does bind the strategy and it
  exposes `rateFactor` directly, but *promoting a capture path to a trusted source is a `user`
  decision* that T48 explicitly did not make, and T55 does not need it: the branch attribution below
  is obtained by **re-derivation against Path B observations** instead, which needs no new seam.
* **Path B is the production wiring, and it is PROVEN to honour the setting.** B-03/B-04 established
  it (`FULL_LEAP_YEAR` total interest `144,659.21` vs `FEB_29_PERIOD_ONLY` `145,011.43`, 12/12
  periods differing), and T55 re-establishes it inside its own set: the same one-setting change
  moves **11 to 27 cells** on the leap shapes while moving **0** on the non-leap controls. The
  two-captures-differ-in-one-setting test is itself the proof that the seam honours the variable,
  which is why it is the deliverable.

**Additive only.** This pass created **no product, no charge, no client and no loan**. It reuses the
products T22/T36 left on `gerege`, asserted out of PostgreSQL before use and re-asserted after:

| id | `days_in_year_enum` | `days_in_month_enum` | `interest_calculated_in_period_enum` | `days_in_year_custom_strategy` | `interest_recognition_on_disbursement_date` |
|---|---|---|---|---|---|
| **7** | 1 (ACTUAL) | 1 (ACTUAL) | 0 (DAILY) | **UNSET** | `f` |
| **3** | 1 | 1 | 0 | **FULL_LEAP_YEAR** | `f` |
| **4** | 1 | 1 | 0 | **FEB_29_PERIOD_ONLY** | `f` |

`m_loan` **0 before and 0 after**; `m_product_loan` **21 before and 21 after**; `m_client` **2 before
and 2 after**. `calculateLoanSchedule` persists nothing. The shared containers were never started,
stopped, restarted, re-tenanted or written to; `RestartCount` **0** on both.

`clientId 2` ("Path B Leap Fixture", activation `2023-01-01`) is used throughout: client 1 activates
`2026-01-01` and the oracle rejects an earlier `submittedOnDate` with HTTP 403
`error.msg.loan.submittal.cannot.be.before.client.activation.date` — observed by T48, and the reason
every T55 request uses client 2.

---

## The shapes, and where each number comes from

All 11 shapes × 3 products = **33 captures**, every one HTTP **200** (`out/HTTP-CODES.txt`).
Principal `1200000` (integer, no decimal point), rate `21.6`/yr, `interestRateFrequencyType 3`,
`amortizationType 1`, `interestType 0`, `interestCalculationPeriodType 0` (DAILY),
`advanced-payment-allocation-strategy`. Requests are authored as **text** by `bin/t55-capture.sh`
and committed under `req/`.

| id | disbursed | n × every | the geometry it exercises |
|---|---|---|---|
| `LB-LEAPIN` | 01 Nov 2023 | 2 × 1mo | period 2 crosses 2023-12-31: **365 → 366**. **ANCHOR** — same shape as T48's `T48B-PUREB` |
| `LB-LEAPOUT` | 01 Nov 2024 | 2 × 1mo | period 2 crosses 2024-12-31: **366 → 365** |
| `LB-NONLEAP` | 01 Nov 2025 | 2 × 1mo | period 2 crosses 2025-12-31: **365 → 365**. **CONTROL for T48-N4** |
| `LB-DEC15IN` | 15 Dec 2023 | 1 × 1mo | 365 → 366, **16-day** first segment |
| `LB-DEC15OUT` | 15 Dec 2024 | 1 × 1mo | 366 → 365, 16-day first segment |
| `LB-DEC15NL` | 15 Dec 2025 | 1 × 1mo | 365 → 365, 16-day first segment. **CONTROL** |
| `LB-DEC31` | 31 Dec 2024 | 1 × 1mo | **ZERO-day** first segment; from-date year is leap |
| `LB-F29CROSS` | 01 Dec 2023 | 1 × 4mo | crossing period **CONTAINS 29 Feb 2024** → `FEB_29_PERIOD_ONLY` enters the arm too |
| `LB-MULTI3` | 01 Jun 2024 | 1 × 24mo | ONE period spanning **TWO** 31-Dec boundaries → **three** loop iterations; **no** 29 Feb in the period |
| `LB-MULTI3F` | 01 Jun 2023 | 1 × 24mo | same three-segment geometry, **CONTAINS 29 Feb 2024** |
| `LB-HALFYR` | 01 Nov 2023 | 2 × 6mo | period 1 crosses **and** contains 29 Feb; period 2 does not cross but starts inside the leap year |

Each shape was chosen by applying the verified source rules above, not by search. `LB-MULTI3`'s
2024-06-01 → 2026-06-01 span contains **no** 29 February because 29 Feb 2024 **precedes** the
from-date and `isPeriodContainsFeb29` is from-**exclusive** — which is what makes it the only
three-segment shape in the set on which `FEB_29_PERIOD_ONLY` suppresses the arm.

## What is an OBSERVATION and what is a RE-DERIVATION

| artefact | status |
|---|---|
| `out/LB-*-raw.json` | **OBSERVATION.** Raw response bytes, unmodified. Canonical. |
| `out/LB-*-exact.json` | **OBSERVATION**, re-encoded losslessly: every number becomes a JSON string of the literal wire characters (`parse_float=str`). No value changed. |
| `out/rerun/LB-*-raw.json` | **OBSERVATION.** The determinism re-post; byte-identical, 33/33. |
| `out/preconditions.txt`, `products-asserted.txt`, `products-matched.txt`, `container-state.txt`, `HTTP-CODES.txt`, `DIGESTS.txt` | **OBSERVATION.** Read off the running oracle and PostgreSQL. |
| the *cells compared / cells differing / minor units* columns | **OBSERVATION**, computed by exact string and `Decimal` comparison of observed values only. |
| the **ARM re-deriv** / **PLAIN re-deriv** / **N365** / **NACT** columns | **RE-DERIVATION.** Computed by `analysis/t55-analyse.py` from the **observed** opening balance and **observed** dates, at `(19, HALF_UP)`, from the cited source formulas. Labelled as such everywhere they appear. |
| the *verdict* column | **INFERENCE** from comparing one observation with two re-derivations. |

**No expected value in this directory was hand-authored.** Where a re-derivation and an observation
agree, that is reported as a reproduction; where they disagree the period is reported
`UNATTRIBUTED` and the analysis **fails** rather than dropping it. On this set there are **zero**
`UNATTRIBUTED` periods.

## The re-derivation's scope, stated as a limit

The re-derivation models the **first interest period** of each repayment period. On a single
disbursement at the schedule start, every repayment period after the first has exactly one interest
period, so the model is exact for those; period 1 additionally carries a zero-length interest period
at the disbursement date, which does not change the factor. It does **not** model the EMI solve — it
takes the **observed** opening balance as its input. That is why it attributes branches and does not
predict schedules, and why a shape's per-period equality does not imply pair-level equality: the EMI
couples all periods, so one differing period shifts every principal split.
