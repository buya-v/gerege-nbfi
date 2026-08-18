# T29 handoff — independent re-review of DEC-1 revision 4

**VERDICT: ACCEPTED WITH REQUIRED CHANGES — NOT ratifiable.** P-2 is not satisfied; gate **G-1** stays open.

**P0 outstanding: 2.**

> **The driver must not ratify:** revision 4 still fails its own from-text test — reading only DEC-1, an implementer gets `n` in the EMI re-adjust loop wrong (it is `relatedRepaymentPeriods.size()`, not `NumberOfRepayments`, and they differ inside the graded domain the Run-1 corpus already samples) and has no formula at all for the per-period interest split, and each of those returns different money on ~1.6–1.8 % of in-graded-domain shapes that no committed observation can discriminate.

| id | one line | grade |
|---|---|---|
| **P0-T29-1** | ADR §4.3.1 line 280 / `contract.go:1052-1054`: "`n` … inside the graded domain is `NumberOfRepayments`" is **false** — `n` is `relatedRepaymentPeriods.size()` [`EmiAdjustment.java:54-56`, `ProgressiveEMICalculator.java:732`, `:749`, `:250-263`, `ProgressiveLoanInterestScheduleModel.java:195-197`]; the cited `:191-194` is the unreachable `null` branch. 2,143 / 120,000 (1.79 %) in-graded-domain later-disbursement shapes return different money. | P0 |
| **P0-T29-2** | The per-period interest computation is specified **nowhere** in DEC-1. The oracle does `balance × rateFactor ÷ lengthTillPeriodDueDate × length`, three separately mc-rounded operations [`InterestPeriod.java:145-158`]; the textbook reading DEC-1's prose describes diverges on 699 / 43,992 (1.59 %) in-graded-domain shapes, and **all 13 committed observations pass either way**. | P0 |
| P1-T29-1 | §4.4's "only effect" reason for the `daysInYearCustomStrategy` pin is incomplete — `FEB_29_PERIOD_ONLY` also **suppresses** the cross-year partial-period arm [`:1505-1507`], which qualifies §4.10's "`case ACTUAL` `:1534-1535` is unreachable". No money changes (the field is pinned null). T30's fact 1, independently re-derived. | P1 |
| P1-T29-2 | `contract.go:557-561` still carries the weak calibration inference that ADR §4.1 (P2-T26-2) now declares insufficient — the two artefacts of one contract disagree. | P1 |
| P2-T29-1 | §8 item 5 / §4.10's "largest un-re-derived hole" is stale: T30 re-derived the cross-year partial arm and B-03/B-04 reproduce. Citation update. T30's fact 2, independently verified. | P2 |

**No regression.** Revision 3's P0-2 (disbursement window; deleted ordering clause) and P0-3 (`FrequencyYears`; error precedence) are clean in both artefacts — the deleted clause appears only quoted-as-deleted, the window predicate is intact and identical, precedence is total and deterministic, and T28's `NumberOfRepayments < 1 → ErrInvalidRequest` is consistent and stated identically in both.

**Positive result worth recording.** T28's §4.3.1 is *substantively* right: every step and all ~20 `file:line` citations verify against the pinned checkout, and an independently written from-text model reproduces **13 of 13** committed observations digit-for-digit — including all three named triples, and only with the loop body present.

**Vector question.** I agree with T26 / ADR §8 items 3 and 3a: **do not** bind ratification to capturing the guard and adoption-test vectors (no oracle is reachable, and §3.1 makes graded-domain growth a non-amendment); keep the binding on conformance PASS and cutover. **But widen it to four**: add **3b** (separates the per-period interest round-trip — candidate MNT 13,202 / 6 × 16.8 %, start = disbursement 2024-01-01) and **3c** (a later-disbursement shape that trips the guard — candidate MNT 10,548,069 / 6 × 16.8 %, start 2024-01-01, disbursement 2024-02-01). Both candidates are **re-derived**, not observed.

**No live oracle was reachable and none was contacted.** Every figure is a source re-derivation or a quoted committed observation. Build / vet / gofmt / tests clean; non-negotiable scan clean.

Full review: `.softhouse/reviews/T29-DEC-1-v4-rereview.md`. Scripts + transcript: `.softhouse/reviews/t29-probe/` (the attempt-1 WIP files are deleted).
