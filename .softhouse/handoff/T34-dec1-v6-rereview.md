# T34 handoff — independent re-review of DEC-1 revision 6

**Branch:** `softhouse/T34-dec1-v6-rereview`
**Review:** `.softhouse/reviews/T34-DEC-1-v6-rereview.md`
**Probes:** `.softhouse/reviews/t34-probe/`
**Verdict:** **ACCEPTED WITH REQUIRED CHANGES** — 1 P0, 2 P1s, 1 P2.

**No live oracle was contacted. No observation was taken, synthesised or
implied.** Every number produced by this task is a re-derivation from the pinned
checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` (verified with
`git -C /Users/buv/fineract log -1 --format=%H` before any citation) or a
transcription of an already-committed capture file. Nothing here may be promoted
to the vector store.

## Scope touched

Only `.softhouse/reviews/` and `.softhouse/handoff/`. `docs/adr/`, `nexus/`,
`.softhouse/program.json`, `.softhouse/tasks.json`, `.softhouse/RESUME.md` and
`.softhouse/capture/` were **read only** and are unmodified — confirm with
`git diff --stat main..softhouse/T34-dec1-v6-rereview`.

## What was done

1. Transcribed DEC-1 revision 6 **from its text alone** into a runnable model
   (`t34_model.py`) — exact `Decimal` at `MathContext(19, HALF_UP)` and integer
   minor units, no `float` on any path.
2. Reproduced **13 of 13** committed observations digit-for-digit, then ran a
   stricter check nobody had run: **row by row** (due date, principal, interest,
   outstanding balance, loan term) against **all 12** committed Path-A captures —
   11 of 12 clean.
3. Attacked the four surfaces T32 named unexamined: period/date generation and
   the month-end re-anchor, the down-payment arm, the balance roll-forward and
   its zero clamp, and currency/scale handling. Two of the four yielded defects.
4. Ran every regression check the brief asked for, and opened every `file:line`
   T33 cited.

## Findings the next author must apply

### P0-T34-1 — the rate factor's multiplier is `periodRatio`, not `RepaymentEvery`

DEC-1 §4.3.2 writes, normatively (and `contract.go:1455-1459` repeats it):

```
rateFactorTillPeriodDueDate = setScale( (rate × 30 × RepaymentEvery ÷ 360) × actual ÷ calculated, RateFactorScale )
```

The pinned oracle does **not** pass `RepaymentEvery` on that entry point:

```java
1404   BigDecimal periodRatio = switch (repaymentFrequency) { ...
1406       case MONTHS -> calculatePeriodRatio(scheduleModel, repaymentPeriod, ChronoUnit.MONTHS, mc); ... };
1412   return calculateRateFactorPerPeriodBasedOnRepaymentFrequency(interestRate, repaymentFrequency, periodRatio,
1413           BigDecimal.valueOf(30), daysInYear, actualDaysInPeriod, calculatedDaysInPeriod, mc);
```

[VERIFIED: `ProgressiveEMICalculator.java:1404-1413`]. The recurrence's entry
point does pass `repaymentEvery` [VERIFIED: `:1536-1537`]. §4.1.1's call-chain
sentence cites `:1403-1412` — the very block that computes `periodRatio` — and
describes the two sites as differing only in *span*. The words `periodRatio` /
`calculatePeriodRatio` appear nowhere in DEC-1, nowhere in `contract.go`, and in
no probe of T23/T26/T29/T31/T32/T33.

`periodRatio` equals `RepaymentEvery` only while every repayment period is
`ScheduleStartDate + k months`. The **month-end re-anchor breaks that** whenever
the disbursement seed and the schedule start disagree near month end, because the
re-anchor is seeded on the disbursement date [`LoanApplicationTerms.java:585-589`]
while `calculateSeedDate` reads the schedule start
[`:1460-1479` → `ProgressiveLoanInterestScheduleModel.java:209-211`].

Re-derived (never observed):
- 55 of 5,767 (0.95 %) same-month `(ScheduleStartDate, Disbursement.Date)` pairs
  in 2024 have a non-unit `periodRatio`; all have `ScheduleStartDate` day
  28, 29 or 30.
- On those date shapes, **480 of 480 (100 %)** swept requests return different
  money. Worst total-interest gap **MNT 398,967.73**.
- **0 of 12** committed captures and **0 of 13** observations can see it.

**Concrete capture candidate (re-derived, not an observation):** MNT 1,200,000 /
6 × 21.6 %, schedule start 2024-01-28, single disbursement 2024-01-31, MNT 2 dp,
(19, HALF_UP), 30/360 — total interest **74,607.33** as DEC-1 is written against
**76,984.00** from the pinned source, gap **MNT 2,376.67**.

Required edits are enumerated in review §1.6: define `periodRatio` normatively in
§4.1.1 with `file:line`; add a multiplier column to the two-call-sites table;
correct §4.3.2's formula; extend §9's rate-factor obligation; mirror both in
`contract.go`; add §8 item **3e** and widen the item-3 binding from five vectors
to six, keeping "conformance PASS and cutover, **not** ratification".

### P1-T34-1 — §4.3.2 step 4's roll-forward contradicts its own segmentation table

For a disbursement dated on repayment period *j*'s `DueDate`, step 4 read
literally returns the **whole principal** as period *j*'s
`OutstandingPrincipalMinor`; committed capture `P-03` records `0.00`. The
segmentation table's row 2 ("enters period *j+1*'s balance") says the opposite of
step 4 and matches the capture. Mechanism for the corrected text: the generator
writes the row's balance at `ProgressiveLoanScheduleGenerator.java:132`, during
period *j*'s iteration, while `addDisbursement` at `:351` only fires when the
date is in the **half-open** window `[from, due)` [`:307-308`] — period *j+1*.

P1 not P0 because the corpus **does** discriminate it.

### P1-T34-2 — the disbursement row's outstanding balance is NOT graded

Revision 6's new §4.5 / `contract.go:1105-1113` claim "Every committed capture
contains a disbursement row, so this **is** graded". All three Path-A harnesses
emit only `type`/`dueDate`/`principal` for a `DISBURSEMENT` row
[`Capture.java:180-181`, `Capture2.java:231-232`, `Capture3.java:251-252`] — each
of which *does* emit `balance` on the down-payment and repayment branches. The
source claim [`LoanSchedulePlan.java:52-56`] is exact; the coverage claim is not.
Mark it UNGRADED by Path A and add the column to §8 item 1's missing-columns list
(it is a fourth, not one of the stated three).

### P2-T34-1 — what "13 of 13" grades

`t33_spec_check.py` compares three scalars per shape. It never compares a due
date or `OutstandingPrincipalMinor`, which is why P1-T34-1 survived it. Recommend
the Provenance paragraph say so and adopt the row-level check
(`t34_capture_check.py`, no oracle required).

## Verified clean — do not re-litigate

- Every `file:line` in T33's new §4.1.1 (`:1367-1368`, `:1369-1370`,
  `:1500-1501`, `:1502-1503`, `:1953-1955`, `:1961-1962`, `:638-643`,
  `:639-640`, `:641-642`): **exact**.
- The false "ratio is exactly 1 … every period in the graded domain" clause:
  **deletion complete**; nothing in either artefact depends on it.
- §4.3.1 loop steps 1–8: **byte-identical** to revision 5 (SHA-256
  `2ccf0f040428570c…` both).
- §4.3.2's three-operation interest block: **byte-identical** (SHA-256
  `f45eac5891685e4f…` both).
- `n = |relatedRepaymentPeriods|`: intact everywhere; the only
  `NumberOfRepayments` statements are the correct biconditionals.
- §8 item 3d break-out present; binding widened four → five and still gates
  **conformance PASS and cutover, NOT ratification**.
- Month-end rule, growth-factor sum, currency layer (`Money.java:40-53`,
  `:48-51`, `:52`), `MoneyHelper` 19/HALF_UP, `Money.copy(double)`,
  `Money.dividedBy(long)`, the whole down-payment arm, and `FrequencyYears`
  throwing on the 30/360 arm from both entry points: all re-verified against the
  pinned checkout, all exact.

## Suggested next task

**T35 — DEC-1 revision 7:** apply P0-T34-1, P1-T34-1, P1-T34-2 and P2-T34-1. It
is prose plus one backlog item; no type, field set or graded-domain predicate
moves, so it is not a contract amendment and not a `user` gate. Ratification
should follow one more independent re-review.

Separately, the capture programme now owns six §8 item-3 vectors, not five:
3, 3a, 3b, 3c, 3d and the new **3e** (drifted-boundary / non-unit `periodRatio`).
