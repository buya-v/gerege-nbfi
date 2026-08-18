# T32 — handoff: independent re-review of DEC-1 revision 5

| | |
|---|---|
| Verdict | **ACCEPTED WITH REQUIRED CHANGES — NOT ratifiable** |
| Outstanding **P0** | **1** (plus 2 P1, 1 P2) |
| Gate **G-1** | **stays open**; the driver may **not** ratify under P-2 |
| Full review | `.softhouse/reviews/T32-DEC-1-v5-rereview.md` |
| Probes | `.softhouse/reviews/t32-probe/` — **no live oracle was contacted** |

**The one sentence the driver needs:** revision 5 resolved both of T29's P0s cleanly and an independently written transcription of its text reproduces 13 of 13 committed observations, but `contract.go:317-321` still asserts that the rate factor's `actualDaysInPeriod / calculatedDaysInPeriod` correction is "exactly 1 … every period in the graded domain" — which revision 5's own §4.3.2 makes false by admitting a disbursement dated strictly inside a repayment period, and which the ADR nowhere corrects because §4.1 never defines either day count; the two readings the artefacts license diverge on **2,913 of 2,913** re-derived in-graded-domain shapes by up to **MNT 1,816,050.11** in total interest, so DEC-1 must be corrected once more before ratification.

**P0-T32-1 in one line.** `calculatedDaysInPeriod` is the ENCLOSING REPAYMENT period's day count [`ProgressiveEMICalculator.java:1367-1370`, `:1500-1503`], not the span's own, so a partial interest period is prorated — the text says nothing and `contract.go` says the opposite.

**Required correction — one of two arms, applied to BOTH artefacts:**
- **Arm A (recommended)** — define both day counts normatively in §4.1, state the proration in §4.3.2 and §9(c)/(d), and delete `contract.go`'s "— which is every period in the graded domain".
- **Arm B** — narrow §3.1's disbursement window to `{ScheduleStartDate} ∪ {DueDates 1…N−1}` and refuse the rest with `ErrNoDiscriminatingVector`.

Neither arm is a shape change, so neither is an amendment.

**P1-T32-1** — a repayment period's growth factor is `1 + Σ rateFactor` over its interest periods [`RepaymentPeriod.java:216-217`], not the singular `1 + rateFactor` §2.1 and `contract.go:448-451` state. Measured inert today (0 divergences in 2,913 shapes); live the moment interest pauses or rate changes arrive.
**P1-T32-2** — `OutstandingPrincipalMinor` is unspecified on disbursement and down-payment rows; the oracle emits the amount advanced [`LoanSchedulePlan.java:52-56`].
**P2-T32-1** — §4.3.2 step 5 should say the final row's **split** is recomputed, not only its principal (never bites in the sampled domain).

**Verified clean, independently:** P0-T29-1 (`n` = `relatedRepaymentPeriods.size()`, membership, effective due date, level-installment scope, step-6 overwrite set, `uncountablePeriods` scope) and P0-T29-2 (base amount, zero short circuit, three mc-rounded operations in order, segmentation, sum-then-money, cap, balancing principal, clamped roll-forward) — every cited `file:line` exact. T28's loop steps 1–8 preserved byte-for-byte. Deleted revision-2 ordering clause has **not** returned. Graded-domain blocks identical in both artefacts. Error precedence total and deterministic. `NumberOfRepayments < 1 → ErrInvalidRequest` identical in both.

**Vector binding:** agreed — items **3, 3a, 3b, 3c** (and the strictly-inside shape, which I recommend breaking out as **3d**) gate **conformance PASS and cutover**, not ratification. But a *missing vector* is a conformance gate whereas a *wrong normative sentence* is a ratification blocker, and P0-T32-1 is the latter.

**Build:** `go build ./...` OK · `go vet ./...` OK · `gofmt -l .` clean · `go test ./...` (no test files, correct for a contract-only package). Non-negotiable scan clean — every float / Oracle-Database / `first_name` / offset hit is prohibition prose.

**Next task:** T33 — DEC-1 revision 6 applying P0-T32-1 (Arm A), P1-T32-1, P1-T32-2, P2-T32-1; then an independent re-review of revision 6.
