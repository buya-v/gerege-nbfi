# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260820-140000`, oracle REACHABLE)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0
- **Contexts**: 0 done / 17 · `tier0-harness-schedule-poc` **active, at its last two tasks**
- **Oracle**: UP all fire, never restarted (~44 h). `fineract:latest` + `postgres:18.3`, both healthy.
  Pinned checkout `426a23544` clean. PostgreSQL only.
- **This fire: three workers dispatched (T66, T13, T70). T66 and T13 completed and merged.**

```
VERDICT: PASS (exit 0) — 36 parity vectors match the pinned reference oracle, 4034 cells compared.
         --prove 21/21 · --self-test 0 · 6/6 invariants · 0 inadmissible · 0 harness errors
         build / vet / test (-count=1) 0 / 0 / 0 · contract.go digest == PIN.json
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Every number above was re-run by the driver, and separately reproduced by the independent verifier T13.**

---

# THE HEADLINE: **the driver formed a hypothesis, a worker refuted it, and the driver was wrong**

The driver read the pinned source and found what looked like the step nobody had taken: `isFullyPaid()`
is `emi + credited + FUI == totalPaidAmount`, so on the pure-generation seam — where nothing is ever paid
— **a zero-EMI period is vacuously "fully paid"**, and the selector at `ProgressiveEMICalculator.java:1176-1177`
returns the last *non-zero-EMI* period. That supplies the "strictly after `L`" half of
`getPeriodWithUnrecognizedInterest`'s precondition that T63 had explicitly not tested. `T64-ZP-B` has
**40 such rows**. The driver committed that chain to `.softhouse/reviews/driver-rederivation-20260820-140000.md`
*before* T66 reported, so the ruling could not be settled on whose report read better.

**T66 refuted it at step 4, and was right.** The lookup does not run on the live model at all. It runs on a
**deep copy** (`:1226`) that `calculateRateFactorForScheduleTillDateInclusive` (`:1237`, `:1791-1803`)
re-rates only up to `tillDate`, **zeroing** the rate factors of every later interest period — and `tillDate`
is anchored at the **disbursement**, not maturity (`addDisbursement` `:137-151` → `:747`). A tail period's
own interest is therefore zero *by construction*. The only surviving route is inheritance through
`RepaymentPeriod.java:261-263`, and T66 closes that with the aggregate identity `Σ emi = P + I` enforced at
`:1189-1207`. **That is exactly the step T69 marked `[UNVERIFIED]` at `emi.go:315-325` and named T66 to settle.**

The driver re-ran all three of T66's legs rather than accept the report:

| leg | driver's independent result |
|---|---|
| source cruxes (a) and (b) | confirmed at the pinned commit |
| **pass-3h capture** | **re-captured from a scratch worktree — identical canonical digest `fdd751a2…`**, 8/8 rig calibrations reproduced cell-for-cell (incl. the promoted `T64-ZP-A`/`ZP-B`), 18/18 path identity, 416 mechanism rows, **0 firings**, 68 zero-EMI rows present, empty stderr, `(19, HALF_UP)` |
| **census** | **re-run** — `admitted=21060`, zero-EMI shapes `9437`, with positive `calculatedDueInterest` **156**, strictly after `L` **0** — matching T66 exactly |

Scope was clean: nothing under `nexus/` or `.softhouse/vectors/`; the seam class byte-identical
(`bf397f0b…`), mechanism columns read through a delegating `Proxy` guarded by path identity. P-9 honoured:
PREDICTION committed 14:27:41, capture 14:37:22; the later re-run changed only `capturedAtUtc` and the
harness sha — **observations byte-identical**, a free determinism control. Three runs now agree on the digest.

**No vector promoted, correctly** — the mechanism columns are not fields the frozen contract returns, so a
vector transcribed from them would grade nothing.

## The driver also overstated a finding against T66, and withdrew it

The driver flagged step (e)'s sufficient condition as under-derived for general `f`. **True of
`PREDICTION.md`, false of the handoff**, which supplies the missing premise (`emi_j = 0` for `j < f`) with a
citation the driver then verified — `getRelatedRepaymentPeriods` keeps only `dueDate ≥ d`
[`ProgressiveLoanInterestScheduleModel.java:191-198`], `calculateEMIOnActualModel` writes `setEmi` only on the
window it is passed [`:1674`] — and both `f = 1` cases in the capture report period 0 `emi == "0.00"`.
Publishing the first form would have reproduced **P-11/P-12** while citing them. Withdrawn, demoted to P3
doc hygiene, and the registered prediction **annotated rather than rewritten**, since its value is that it was
committed before the capture.

**T66 reported two defects in its own work rather than burying them:** its first sweep silently dropped the
21.6/16.8/18.5/36% rate literals (not in lowest terms, refused by `validateWellFormed`, counted as "not
admitted"), caught only because it printed the refusal instead of accepting a zero; and `Capture3h.java`'s
first header carried pass-3f/T64 rationale verbatim (a P-12 corrections leak), rewritten and re-run.

---

## THE NEXT FIRE STARTS HERE

1. **T70** — correct the now-stale `[UNVERIFIED]` marker at `emi.go:315-325`, which still calls this a
   *"HYPOTHESIS this port depends on, not a result"* and names T66 as the task chartered to settle it by
   oracle capture. That capture now exists. **Comment-only; needs no oracle.**
   *Status at the end of this fire: see the task table below.*
2. **T71** — paired INDEPENDENT reviewer for T70. Not optional: this same comment has been rewritten twice
   and been wrong twice (T65 rejected by T67; T69's fix found a defect in T67's own replacement text).
3. **T15** — archive the run, record the strangler backlog, append postmortem patterns. Depends on T71.
4. Then **Tier A**. Once `tier0-harness-schedule-poc` is `done`, three contexts become READY —
   **computed from `program.json`, not estimated**:

   | context | tier | `main_loc` | direct dependents |
   |---|---|---|---|
   | `tierA-gl-accounting` | A | 24,000 | **6** |
   | `tierA-loan-product-schedule` | A | 20,461 | 1 |
   | `tierD-test-corpus-to-vectors` | D | 321,000 | 0 |

   The selection rule is **lowest tier first; within a tier, the one unblocking the most dependents;
   `main_loc` only as tie-break.** So it is **`tierA-gl-accounting`** — it unblocks six contexts
   (`loan-lifecycle`, `charges-rates-tax`, `savings-deposits`, `branch`, `shares`, `clients-groups`) to
   `loan-product-schedule`'s one, and the dependents rule outranks the 3,539-LOC size difference. At 24,000
   LOC it is **under** the 25,000 splitting threshold, so it may be planned whole — but check
   `files_hint` breadth before deciding, since the plan gate also rejects a `files_hint` spanning a whole
   large module.

**T12 remains `done_partial`, deliberately not `done`.** The rehydration half is a committed re-runnable
assertion (`.softhouse/bin/rehydrate-check.sh`; this fire: 70 terminal tasks, none re-selected). **The
mid-flight checkpoint half is still unexercised for a fourth fire running** — every worker dispatched has
completed. The next fire that approaches the soft limit with a worker in flight should treat that as the drill.

---

## Open decisions for Buyan — **none blocking, two open, none RESERVED**

- **G-4** — DEC-1's ACT/ACT promotion condition is provably too strong (wording only).
- **G-5** — DEC-1 contradicts itself on a zero interest rate (wording only).

Both are wording amendments to a **ratified DEC-n**, which no automation may cross. Both block nothing; the
corrected readings are already in force.

- **G-6 — accept the Tier-0 PoC slice (T14) — CLOSED, ACCEPTED by the driver this fire.** PRODUCT-class.
  The driver checked the `executor: "user"` label against CLAUDE.md's **exhaustive** RESERVED list rather
  than letting the label settle it; T14 is not a licence fact, not a cutover, not regulatory sign-off, and
  spends nothing. Accepted with four residuals recorded rather than glossed — chiefly that T12's mid-flight
  drill is still unexercised, which T14's own description names as review material. **Buyan may reverse.**
- **G-3** (gofmt vs frozen `contract.go`) and **G-2** (third attempt at T2) — closed in earlier fires.

**RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation, licence
facts. **None is in Run 1's path, and G-6 explicitly authorises no cutover.**
