# T32 — independent adversarial re-review of DEC-1 revision 5

| | |
|---|---|
| Subject | `docs/adr/DEC-1-schedule-generator-adapter.md` **revision 5** and `nexus/internal/apps/loanschedule/contract/contract.go` |
| Reviewer | task **T32**, isolated worktree `/home/user/wt-T32`, branch `softhouse/T32-dec1-v5-rereview` |
| Reference oracle | Fineract, pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` (verified: `git -C /home/user/fineract rev-parse HEAD`) |
| Live oracle | **UNREACHABLE.** No Fineract instance, no PostgreSQL, no Docker. **No new observation was taken, synthesised or implied.** |
| Predecessors | T5 (v1, REJECTED) · T23 (v2, 3 P0) · T26 (v3, 1 P0) · T29 (v4, 2 P0) |

---

## 1. VERDICT

> ## ACCEPTED WITH REQUIRED CHANGES — **NOT ratifiable**
>
> **Outstanding P0: 1.** The driver may **not** ratify DEC-1 under standing policy **P-2**, and gate **G-1** does **not** close on revision 5.

**P0-T32-1 — the rate factor's day-count proration is undefined in the ADR and affirmatively MISSTATED in `contract.go`; on a disbursement dated strictly inside a repayment period — an in-graded-domain shape revision 5 itself admits — the two readings the artefacts license return different money on 2,913 of 2,913 re-derived shapes, by up to MNT 1,816,050.11 in total interest.**

Everything revision 5 set out to do, it did. **P0-T29-1 (`n`) and P0-T29-2 (the per-period interest computation) are both cleanly and correctly resolved**, every `file:line` I relied on checks out against the pinned checkout, and nothing earlier reviews confirmed clean has regressed. The one P0 is in an area no previous review examined — the area T31's handoff itself flagged as unmodelled — and it is the same failure mode as its three predecessors: a step of the arithmetic that the corpus cannot see, specified by a phrase rather than by an equation.

Also raised: **2 P1** and **1 P2** (§6). None of them alone blocks ratification.

---

## 2. Method, and how independence was preserved

- The model in `.softhouse/reviews/t32-probe/t32_model.py` was **written from the revision-5 text** (`docs/adr/…` §§2.1, 3.1, 4.1, 4.2, 4.3, 4.3.1, 4.3.2, 4.5, 4.6 and `contract.go`'s doc comments), then run against the **thirteen already-committed observations**. Where the text is silent, the model records the gap in a header block (`G-1`, `G-2`, `G-3`) and takes both readings as switchable parameters — that is the experiment's output, not a workaround.
- **`.softhouse/capture/out/t21-probe-rederive.py` was not opened** (retracted, defective). `t26_rederive.py`, `t28_spec_check.py`, `t29_rederive.py` and `t31_spec_check.py` were **not** imported, copied or consulted for arithmetic; the only thing re-used from prior art is the **list of 13 expectations** in `t29_validate.py`, which quotes committed capture files. T32's model shares no line of code with any of them.
- T31's `t31_spec_check.py` was written by the author of revision 5's text. That is exactly the shared-misreading risk the task names, and it is where the P0 sits: `t31_spec_check.py` models a full-period interest period only, so its ratio is 1 by construction and its own check cannot see the defect. **T32's model exposes the day ratio as a parameter**, which is what makes the defect visible.
- Every citation this review relies on was read in `/home/user/fineract` at the pinned commit. Line numbers are quoted as read.

**Evidence labelling used throughout.** (a) *source re-derivation*, (b) *committed prior observation*, (c) *needs a fresh observation*. Nothing is presented as observed that was not already captured and committed.

---

## 3. The from-text transcription experiment

`.softhouse/reviews/t32-probe/t32_validate.py`, output in `t32-validate-output.txt`.

| model run | reproduces the 13 committed observations |
|---|---|
| **DEC-1 revision 5 as transcribed** (source day ratio, three-operation interest) | **13 / 13** |
| control A — the *ratio-is-always-1* reading `contract.go` states outright | **13 / 13** |
| control B — the textbook `balance × rateFactor` reading §4.3.2 exists to exclude | **13 / 13** |

Two conclusions, and the second is the finding.

1. **The transcription reproduces every committed observation digit-for-digit**, including Q0b's later-disbursement shape (level `253114.12`, final `253114.10`, total interest `65570.58`) — reached by an independently written model. Revision 5's §4.3.1 and §4.3.2 are, on every shape the corpus samples, sufficient to determine the money. That is a real advance over revision 4.
2. **The corpus is blind to two separate questions, not one.** Control B re-confirms T29/T31's finding on the interest round-trip (§8 item 3b). **Control A is new**: the corpus is *equally* blind to the rate factor's day-count proration, because no committed observation places a disbursement anywhere but on a period boundary. Revision 5 closed the first hole and left the second — and, worse, `contract.go` closed the second in the *wrong* direction (§4).

---

## 4. P0-T32-1 — the day-count proration (the strictly-inside-a-period shape)

### 4.1 What the artefacts say

`docs/adr/…:171-179` (§4.1) reproduces the oracle's rate-factor code:

```java
return interestRate.multiply(interestFractionPerPeriod, mc)
        .multiply(actualDaysInPeriod, mc)
        .divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode());
```

**Neither `actualDaysInPeriod` nor `calculatedDaysInPeriod` is defined anywhere in either artefact.** Verified mechanically: the two identifiers occur only at `docs/adr/…:177-178` and `contract.go:503-504` (inside the same reproduced snippet) and at `contract.go:318`.

§4.3.2 (`docs/adr/…:438`) defines the quantity that produces every interest figure in the response as:

> `rateFactorTillPeriodDueDate` = the §4.1 rate factor computed over `[interest period FromDate, repayment period DueDate]`

— a span, and nothing else. The plain reading is that *both* day counts come from that span, so the ratio is 1.

`contract.go:317-321` then says so explicitly, and is the only sentence in either artefact that assigns the ratio a value:

> Real calendar days do enter, but only as the proportional correction `actualDaysInPeriod / calculatedDaysInPeriod` (`ProgressiveEMICalculator.java:1500-1503`, `:1961-1962`), **which is exactly 1 when the interest sub-period spans the whole repayment period — which is every period in the graded domain.**

The clause after the dash is **false in revision 5**, and it is false *because of a change revision 5 itself made*. §4.3.2's own segmentation table (`docs/adr/…:426-431`) lists a third shape:

> | **strictly inside** period *j* | `[FromDate, D]` with a zero balance, then `[D, DueDate]` carrying the amount |

and §4.3.2 (`:467`) states that this shape "is admissible under §3.1's window predicate". It is: §3.1's window is `ScheduleStartDate ≤ Disbursements[0].Date < the last repayment period's DueDate`, and a mid-period date satisfies it. So revision 5 admits, inside the graded domain, interest periods that do **not** span the whole repayment period — while `contract.go` continues to assert that none exist.

### 4.2 What the source says [source re-derivation]

`ProgressiveEMICalculator.calculateRateFactorPerPeriodForInterest` — the method §4.3.2 itself cites through `:641-642 → :1355-1356`:

```
1367:        final BigDecimal actualDaysInPeriod = BigDecimal
1368:                .valueOf(DateUtils.getDifferenceInDays(interestPeriodFromDate, interestPeriodDueDate));
1369:        final BigDecimal calculatedDaysInPeriod = BigDecimal
1370:                .valueOf(DateUtils.getDifferenceInDays(repaymentPeriod.getFromDate(), repaymentPeriod.getDueDate()));
```

and the identical pair in `calculateRateFactorPerPeriod` (the recurrence's rate factor):

```
1500:        final BigDecimal actualDaysInPeriod = ... getDifferenceInDays(interestPeriodFromDate, interestPeriodDueDate)
1502:        final BigDecimal calculatedDaysInRepaymentPeriod = ... getDifferenceInDays(repaymentPeriod.getFromDate(), repaymentPeriod.getDueDate())
```

**`calculatedDaysInPeriod` is the ENCLOSING REPAYMENT PERIOD's day count, never the span's own.** The `× actual ÷ calculated` term is therefore a **proration of a partial segment against the full repayment period** — it is the entire mechanism by which a mid-period disbursement is charged less than a full month's interest. `contract.go:318` cites `:1500-1503` — the very lines that refute its own sentence.

The shape is fully reachable through the capture seam: `ProgressiveLoanScheduleGenerator.java:307-308` admits a disbursement on the half-open window `[FromDate, DueDate)`, emits the disbursement row at `:318` and calls `emiCalculator.addDisbursement` at `:351`; `ProgressiveLoanInterestScheduleModel.insertInterestPeriod` (`:280-296`) then splits the repayment period exactly as §4.3.2 describes.

### 4.3 How much money [source re-derivation — NOT an observation]

`.softhouse/reviews/t32-probe/t32_inside_period.py`, `t32_sweep.py`; outputs committed alongside.

MNT 1,200,000 / 6 × 21.6 %, schedule start 2024-01-01, **disbursement 2024-01-15**, everything else strictly inside the graded domain:

| | period-1 interest | level | final | total interest |
|---|---|---|---|---|
| `contract.go`'s ratio-1 reading | **21,600.00** | 212,786.91 | 212,789.26 | **76,723.81** |
| the source's prorated reading | **11,845.16** | 211,087.95 | 211,088.97 | **66,528.72** |

The segment rate factors make the mechanism plain: `[2024-01-15 .. 2024-02-01]` carries `0.0098709677419354839` under the source reading (`= 0.018 × 17/31`) against `0.0180000000000000000` under the ratio-1 reading — **a full month's interest charged on a 17-day exposure.**

Swept over 3,000 random requests, keeping only those whose single disbursement falls strictly inside a repayment period:

```
strictly-inside-a-period shapes drawn: 2913
  ratio-1 reading vs source day ratio DIVERGES on : 2913  (100.0%)
  largest total-interest gap seen: 1816050.11
    MNT 82,836,233 / 36 x 21.6%, schedule start 2024-01-01, disbursement 2024-05-30
      source day ratio : 3369076.72 / 3461468.52 / 25066613.84
      ratio-1 reading  : 3425629.17 / 3524392.68 / 26882663.95
```

This is not the minor-unit class of divergence the previous three P0s were. It is **proportional**, it reaches millions of tugrik, and mid-month disbursement is the ordinary case in retail lending, not an edge case.

### 4.4 Why no previous review or check caught it

- **No committed observation covers the shape.** Every one of the thirteen places its disbursement either on `ScheduleStartDate` (period 1's from-date) or on repayment 1's due date. On both, `actualDaysInPeriod == calculatedDaysInPeriod` and the two readings are numerically identical — confirmed by control A above reproducing all 13.
- **`t31_spec_check.py`, revision 5's own check, cannot see it**, because it models the shape the corpus samples and so never constructs an interest period shorter than its repayment period. A check written from the same reading as the text cannot falsify that reading. This is precisely the shared-misreading hazard the task warned about, and it materialised.
- Revision 5 *created* the exposure: revision 4 had no §4.3.2 and made no claim about interest-period segmentation at all. Adding the correct segmentation table without correcting `contract.go`'s "every period in the graded domain" left the two artefacts in direct contradiction.

### 4.5 Required correction (the ADR must take **one** of these arms and say so in **both** artefacts)

**Arm A — specify it (recommended).**

1. **§4.1**, normatively, at the point the snippet is reproduced:
   - `actualDaysInPeriod` = whole days from the interest period's `FromDate` to the end of the span the rate factor is computed over;
   - **`calculatedDaysInPeriod` = whole days from the ENCLOSING REPAYMENT period's `FromDate` to its `DueDate`** — never the span's own length —
   citing `ProgressiveEMICalculator.java:1367-1370` (the `rateFactorTillPeriodDueDate` call) and `:1500-1503` (the interest period's own rate factor).
2. **§4.3.2**: after the `rateFactorTillPeriodDueDate` definition, state that the factor is **prorated by `days(interest period FromDate → repayment period DueDate) ÷ days(repayment period FromDate → DueDate)`**, that this ratio is 1 only when the interest period opens on the repayment period's `FromDate`, and that on the third segmentation row it is strictly less than 1. Add the worked contrast above, labelled a **re-derivation**.
3. **`contract.go:317-321`**: delete "— which is every period in the graded domain" and replace it with the true statement: the ratio is 1 only when the interest period spans the whole repayment period, which a disbursement dated strictly inside a repayment period makes false, and on such a period the correction is `days(segment) ÷ days(repayment period)`.
4. **§9**, obligation clause (c)/(d): the Go module must reproduce the day-count proration of `rateFactorTillPeriodDueDate`, with the enclosing repayment period as the denominator.

**Arm B — refuse it (cheap, honest, available if a capture cannot be taken).** Narrow §3.1's disbursement window, in both artefacts, to `Disbursements[0].Date ∈ {ScheduleStartDate} ∪ {DueDate of repayment periods 1 … N−1}`, refuse every other in-window date with `ErrNoDiscriminatingVector`, and move §4.3.2's third segmentation row out of the in-graded-domain list. Narrowing an ungraded region of the graded domain is behaviour, not shape, so it needs no amendment.

**Recommendation: Arm A.** Arm B refuses the most ordinary retail shape there is — a loan disbursed on a date that is not a repayment boundary — and a contract that cannot answer it is not usable for Run 1's successors. Arm A costs three paragraphs and one deleted clause; the *capture* for it is already backlogged under §8 item 3c.

Either arm closes P0-T32-1. Neither is a shape change, so neither is an amendment.

---

## 5. The strictly-inside-a-period shape, in full (task item 3)

Beyond the P0, I modelled the shape end to end and checked every other rule revision 5 states about it:

| rule | verdict |
|---|---|
| §4.3.2 segmentation, row 3: `[FromDate, D]` zero balance, then `[D, DueDate]` carrying the amount | **correct** — `ProgressiveLoanInterestScheduleModel.java:280-296`, `calculateNewDueDate` `:439-442`, balance into the later segment `InterestPeriod.java:168-188` |
| §4.3.2's claim that on every balance-carrying interest period `lengthTillPeriodDueDate == length` | **correct** for all three rows; the zero-balance `[FromDate, D]` segment differs but contributes exactly 0 |
| the `lengthTillPeriodDueDate == 0` short circuit | **correct**, and correctly *not* taken by the zero-length `[FromDate, FromDate]` segment of row 1 (its `LTPDD` is the full period, its balance is 0) |
| §4.3.1 related periods for the shape: `related = j … N`, `n = N − j + 1` | **correct** — `getEffectiveRepaymentDueDate` `:250-263` returns the matched period's own `DueDate` when `D` is strictly inside it |
| §4.6 window-key ordering for the shape | **correct** — `[FromDate, DueDate)` contains `D`, so the key is `Due_j` and the disbursement row precedes repayment *j*, matching `:121` vs `:141` |
| the rate factor's day-count proration | **WRONG — P0-T32-1** |
| composition of two segments' rate factors into one growth factor | **understated — P1-T32-1** |

---

## 6. Other findings

### P1-T32-1 — the growth factor of a multi-segment repayment period is stated as `1 + rateFactor`, but is `1 + Σ rateFactor`

§2.1 (`:67`, `:69`) and `contract.go:448-451` both describe the recurrence's growth factor as **one** rate factor per repayment period — `fnₖ = 1 + fnₖ₋₁ × (1 + rateFactorₖ)`, "the addition `1 + rateFactor` … is exact [`RepaymentPeriod.java:216-218`]". The cited lines are:

```
216:    private BigDecimal calculateRateFactorPlus1() {
217:        return interestPeriods.stream().map(InterestPeriod::getRateFactor).reduce(BigDecimal.ONE, BigDecimal::add);
```

— i.e. `1 +` **the sum over the period's interest periods**, exact. The citation is right; the sentence omits the summation. As soon as a repayment period carries more than one interest period (every shape in §4.3.2's table), an implementer following the text has to invent a rule.

**Severity P1, not P0, and measured rather than assumed:** over 2,913 strictly-inside shapes, `1 + Σ rf(segments)` and `1 + rf(whole period)` returned **identical** money on **0 divergences** (`t32_sweep.py`), because under the correct day ratio the segment factors sum exactly to the whole-period factor at scale 19 on these shapes. It is inert today and would stop being inert the moment interest pauses, mid-term rate changes or multi-tranche enter the domain — all named in §6.2/§6.3 as foreseeable.

**Required correction:** state in §2.1 and on `contract.go`'s `Rounding` that a repayment period's growth factor is `1 +` the **sum** of its interest periods' rate factors, added exactly, citing `RepaymentPeriod.java:216-217`.

### P1-T32-2 — `OutstandingPrincipalMinor` is unspecified on disbursement and down-payment rows

`contract.go:1007-1019` fixes `FromDate`, `DueDate`, `PrincipalMinor`, `InterestMinor` and `InstallmentNumber` for `PeriodKindDisbursement` and `PeriodKindDownPayment`, and says nothing about `OutstandingPrincipalMinor`, whose own doc (`:1471-1483`) speaks only of "after this row is applied". The oracle emits the **disbursed amount** on a disbursement row (`LoanSchedulePlan.java:52-56` passes `disbursementPeriod.getPrincipalDisbursed().getAmount()` as both principal and outstanding balance). Every committed capture contains a disbursement row, so this **is** graded and a wrong implementation would be caught — hence P1, not P0. But `contract.go`'s doc comments are declared to *be* the specification, and this one has a hole.

**Required correction:** state on `PeriodKindDisbursement` that `OutstandingPrincipalMinor` is the amount advanced, citing `LoanSchedulePlan.java:52-56`, and state the down-payment row's value (`outstandingBalance + disbursed − downPayment`, `ProgressiveLoanScheduleGenerator.java:340-343`) or mark it explicitly ungraded.

### P2-T32-1 — §4.3.2 step 5 says the residual makes principal recomputed, not interest re-capped

§4.3.2 step 5 says "the final period's installment is then adjusted by the §4.3 residual, and its principal recomputed from step 3". The oracle re-evaluates `getDueInterest` too (`RepaymentPeriod.java:272-286` is memoised on `emi`), so if the residual pushed the final installment below its own calculated due interest the cap would bite and the interest would move as well. **Measured: it never bites** — over 1,500 in-graded-domain schedules the last row's interest never equalled its installment. Editorial only; say "and its split recomputed from steps 2–4".

---

## 7. Per-item disposition of what revision 5 changed

Every item verified against the pinned checkout, not taken on T31's word.

| item | claim | verdict |
|---|---|---|
| **P0-T29-1** `n` | `n = relatedRepaymentPeriods.size()` | **RESOLVED.** `EmiAdjustment.java:54-56` ✓; list built `ProgressiveEMICalculator.java:732` ✓, passed `:749` ✓; filter `ProgressiveLoanInterestScheduleModel.java:195-197` ✓; the `null` branch `:191-194` is unreachable because `getEffectiveRepaymentDueDate` `:250-263` always returns a date ✓. Citation correctly moved `:191-194 → :195-197`. |
| P0-T29-1 | membership rule, first period inclusive both ends | **CORRECT** — `:238-245` via `isInPeriod(..., isFirstRepaymentPeriod)` ✓ |
| P0-T29-1 | effective due date = next period's due date when `D` equals the matched due date | **CORRECT** — `:252-262` ✓, including the "no next period" note ✓ |
| P0-T29-1 | the `n` table (3 rows) | **CORRECT** on all three rows; re-derived independently |
| P0-T29-1 | level installment computed over and written to the related periods only | **CORRECT** — `:741`, `:1722-1741`; `calculateRateFactorForPeriods` at `:738` is likewise scoped to the related list ✓ |
| P0-T29-1 | step 6 overwrites the related periods only | **CORRECT** — `:1279-1286`; the predicate `!fromDate.isBefore(firstRelated.fromDate) && !dueDate.isBefore(firstRelated.dueDate)` selects exactly the related list ✓. "ALL n periods" is gone ✓ |
| P0-T29-1 | `uncountablePeriods` counted over the related list | **CORRECT** — `getUncountablePeriods(relatedRepaymentPeriods, …)` `:2027-2031`, argument at `:1785` ✓ |
| **P0-T29-2** interest | base amount `getOutstandingLoanBalance()` under DECLINING_BALANCE | **RESOLVED** — `InterestPeriod.java:149-152` ✓ |
| P0-T29-2 | exact-zero short circuit at `lengthTillPeriodDueDate == 0` | **CORRECT** — `:146-148` ✓ |
| P0-T29-2 | three separately mc-rounded operations in order | **CORRECT** — `:154-157` ✓, and the order is `× rf`, `÷ LTPDD`, `× length` exactly as written |
| P0-T29-2 | `length` / `lengthTillPeriodDueDate` definitions | **CORRECT** — `:160-162`, `:164-166` ✓ |
| P0-T29-2 | segmentation rules and "amount enters the later segment" | **CORRECT** — `:251-262`, `:264-278`, `:280-296`, `:439-442`, `InterestPeriod.java:168-188` ✓ |
| P0-T29-2 | sum then one conversion to money, clamped at zero | **CORRECT** — `RepaymentPeriod.java:252-257` (`Money.of(…, Σ, mc)`), `:264` `negativeToZero` ✓, scale at `Money.java:52` ✓ |
| P0-T29-2 | cap, balancing principal, clamped roll-forward | **CORRECT** — `:272-286` (min at `:280`), `:345-350`, `:389-403` (clamp `:399`) ✓ |
| P0-T29-2 | `rateFactorTillPeriodDueDate` provenance `:641-642 → :1355-1356` | **CORRECT as a pointer**, but the target's day-count semantics are the P0 (§4) |
| P1-T29-1 | `FEB_29_PERIOD_ONLY`'s second effect (third conjunct of `partialPeriodCalculationNeeded`) | **CORRECT** — `:1505-1507` reads `… && (!FEB_29_PERIOD_ONLY.equals(customStrategy) || isPeriodContainsFeb29(…))` ✓; §4.10's qualification follows |
| P1-T29-2 | `contract.go` now carries the source argument, not the capture inference | **APPLIED** — `contract.go:555-575` ✓ |
| P2-T29-1 | §4.10/§8-5 caveat retired on T30's re-derivation | **APPLIED**; consistent with `calculatePeriodFractions` / `rateFactorByRepaymentPartialPeriod` as cited |
| §8 items 3b, 3c | added, binding widened to four vectors | **APPLIED**, and correctly framed as conformance/cutover, not ratification |

---

## 8. No-regression check

| earlier finding | check | result |
|---|---|---|
| the deleted revision-2 ordering clause must not have returned | grep for every phrasing ("after every repayment row", "sorts after every", "key after every", "on or after the last due date … key") across both artefacts | **Two hits, both the historical record of the deletion** (`docs/adr/…:521`, `contract.go:1513`). The clause itself is **not** operative anywhere. ✓ |
| disbursement-window predicate intact | ADR §3.1 line 128 vs `contract.go:667` | identical modulo `≤`/`<=` ✓ |
| graded-domain blocks identical | all twelve lines compared mechanically | **identical** ✓ (my first pass reported spurious diffs from a naive line grep; re-checked line by line) |
| `NumberOfRepayments < 1 → ErrInvalidRequest` in both artefacts | ADR §3.1 `:131`; `contract.go:669-673` and `:849-853` | identical ✓ |
| error precedence total and deterministic | ADR §4.11 `:599-605`; `contract.go:1598-1622` | three levels, "first applicable", multiple reasons at one level collapse to one sentinel; **total and deterministic** ✓ |
| T28's loop steps preserved (T31 says only the parameterisation changed) | `git diff eb67b19 HEAD -- docs/adr/…` | confirmed: the removals are the `n` definition, "ALL n periods", the `uncountablePeriods` scope and provenance/backlog wording. **Steps 1–8, the three guard conjuncts, the adjustment divisor, the strict adoption test and the three-iteration bound are byte-for-byte preserved** ✓ |
| the loop's own citations | `:1258-1310`, `:1262`, `:1265-1273`, `:1274-1291`, `:1293-1308`, `:1778-1789`, `EmiAdjustment.java:31-56`, `Money.java:52`, `:220-222`, `:352-358` | **every one exact** ✓ |
| month-end rule | `DefaultScheduledDateGenerator.java:128-131 → :168-176`, `:311-333`; seed = disbursement date `LoanApplicationTerms.java:583-589` | **exact** ✓ |

**Nothing regressed.**

---

## 9. Non-negotiable scan

| non-negotiable | scan | result |
|---|---|---|
| no `float32` / `float64` / `big.Float` on a money path | `grep -rnE "float32\|float64\|big\.Float" nexus/` | 4 hits, **all prohibition prose** (`contract.go:66`, `:1288-1289`, `:1402`) ✓ |
| money is `int64` minor units | every `…Minor` field is `int64`; no decimal string, no float-backed decimal ✓ | ✓ |
| no Oracle Database / MySQL / MariaDB tokens | `ojdbc`, `oracle.jdbc`, `OracleDialect`, `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver/mysql` over `docs/`, `nexus/`, `t32-probe/` | one hit, in `docs/analysis/tier0-vector-capture-plan.md:839`, **prohibiting** them ✓ |
| "the oracle" used only in the test-oracle sense | DEC-1 §Terminology `:22`; `contract.go:13-16` | ✓ |
| no US payment rails / vendors | Stripe / Plaid / Lithic / Persona / NACHA | none ✓ |
| three-field Mongolian names | `first_name` / `last_name` appear only where **prohibited** (`docs/adr/…:486`, `contract.go:86-87`) ✓ | ✓ |
| no hard-coded time-zone offsets | `+08:00` / `+07:00` / `UTC+8` appear only in `contract.go:789`, as examples of what **must be rejected** ✓ | ✓ |
| no hard-coded payment threshold | none in scope ✓ | ✓ |
| never insured / protected / guaranteed | none ✓ | ✓ |
| PostgreSQL only | no database dependency in this contract ✓ | ✓ |

## 10. Build, vet, format, test

```
cd /home/user/wt-T32/nexus
go build ./...   -> BUILD_OK
go vet ./...     -> VET_OK
gofmt -l .       -> (no output) CLEAN
go test ./...    -> ?  github.com/gerege/nexus/internal/apps/loanschedule/contract  [no test files]
```

A contract-only package with no test files is correct at this stage: the conformance harness, not a unit test, is what grades it.

---

## 11. On the vector binding (§8 item 3 and its 3a / 3b / 3c)

**I agree, with one boundary made explicit.**

Vectors **3** (trip the guard), **3a** (separate the adoption test), **3b** (separate the per-period interest round-trip) and **3c** (trip the guard in the later-disbursement window) each name a rule that revision 5 **states correctly** and the corpus **cannot yet grade**. That is a grading gap, and a grading gap is exactly what a conformance-PASS / cutover precondition is for. Binding them to ratification would be wrong: §3.1's whole design is that the graded domain grows as vectors land, with no amendment, and cutover is a hard `user` gate regardless. Revision 5's framing — "a UAT/cutover precondition, not a ratification precondition" — is right.

**T31's strictly-inside-a-period shape belongs on that list too, as a fifth vector** — and revision 5 has already put it there, folded into item 3c ("A capture of a disbursement dated strictly inside a repayment period belongs with this item too"). I would rather see it broken out as **item 3d**, because it is a different rule from 3c's `n` question and a single capture is unlikely to discriminate both.

**But the boundary matters and revision 5 crosses it.** A *missing vector* is a conformance gate. A *wrong normative sentence* is a ratification blocker, because ratification freezes the sentence and correcting it afterwards costs a `user` gate. §4.3.2 calls the strictly-inside case "specified from source and ungraded"; §4 of this review shows it is **mis**specified. So the **capture** goes on the conformance binding, and the **specification** must be fixed before ratification. That is the entire distance between revision 5 and a clean verdict.

---

## 12. What needs a fresh oracle observation

No live oracle was reachable, so the following are listed as **(c) needing a fresh observation** and are recorded as *candidate shapes to capture*, never as results:

1. **A disbursement dated strictly inside a repayment period** — the P0's shape. Candidate: MNT 1,200,000 / 6 × 21.6 %, schedule start 2024-01-01, disbursement 2024-01-15. Under the source reading this re-derives to level 211,087.95 / final 211,088.97 / total interest 66,528.72; under `contract.go`'s ratio-1 reading to 212,786.91 / 212,789.26 / 76,723.81. **Both figures are re-derivations. Neither may be promoted to the vector store.** One capture settles P0-T32-1 empirically and simultaneously discharges the item-3d backlog.
2. **A shape separating `1 + Σ rf(segments)` from `1 + rf(whole period)`** (P1-T32-1). My sweep found none inside the graded domain; a capture would only be needed once interest pauses or rate changes enter the domain.
3. §8's existing items **3**, **3a**, **3b**, **3c** — unchanged, all still outstanding.
4. **`OutstandingPrincipalMinor` on a down-payment row** (P1-T32-2) — the down-payment path is outside the graded domain, so this is settled from source or left explicitly ungraded, not captured.

Everything else in this review rests on **(a) source re-derivation** from the pinned checkout or **(b) observations already committed** under `.softhouse/reviews/t23-probe/`.

---

## 13. Summary for the driver

| | |
|---|---|
| **Verdict** | **ACCEPTED WITH REQUIRED CHANGES — NOT ratifiable** |
| **Outstanding P0** | **1** — P0-T32-1 |
| P1 | 2 — P1-T32-1, P1-T32-2 |
| P2 | 1 — P2-T32-1 |
| G-1 | **stays open** |
| T29's two P0s | both **resolved**, verified independently |
| Regressions | **none** |
| Build / vet / gofmt | clean |
| Live oracle | unreachable; **no observation taken, synthesised or implied** |

Revision 5 is close. Its loop specification, its `n`, its interest arithmetic and its citation discipline all survive an independent re-derivation intact, and the from-text transcription reproduces 13 of 13 committed observations. One sentence in `contract.go` — "which is every period in the graded domain" — is false under revision 5's own §4.3.2, and one definition missing from §4.1 is what lets it be false. Fix those and revision 6 should be ratifiable.

## 14. Probe scripts

Under `.softhouse/reviews/t32-probe/`, all written by this task, **none run against a live oracle**:

- `t32_model.py` — the from-text transcription. Exact-decimal / integer minor units, no float. Its header records the three places the text is silent (`G-1` day counts, `G-2` growth-factor composition, `G-3` recurrence addition rounding) and exposes each as a switchable reading.
- `t32_validate.py` / `t32-validate-output.txt` — 13 committed observations × three readings.
- `t32_inside_period.py` / `t32-inside-output.txt` — the strictly-inside-a-period shape, with period-1 interest-period detail.
- `t32_sweep.py` / `t32-sweep-output.txt` — 2,913 strictly-inside shapes: day-ratio divergence 100 %, growth-factor-composition divergence 0 %.
