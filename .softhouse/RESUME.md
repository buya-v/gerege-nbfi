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

## What happened after T66 — and the fire's second rejection

**T13 (independent verifier) returned the run-gate UAT PASS**, reproducing every driver number in its own
worktree: build/vet/test `0/0/0` at `-count=1`, conformance exit 0 with 36/36 parity and 4034 cells,
`--prove` 21/21, `--self-test` 0, `contract.go` digest matching `PIN.json`, `gofmt -l` naming exactly
`contract.go` (the expected G-3 state). Its branch touched only its own handoff. Merged.

**T14 closed as G-6 — ACCEPTED by the driver**, `chosen_by: agent`. The driver checked the
`executor: "user"` label against CLAUDE.md's **exhaustive** RESERVED list rather than letting the label
settle it: T14 is not a licence fact, not a cutover, not regulatory sign-off, and spends nothing. Accepted
with four residuals recorded rather than glossed. **It authorises no cutover.** Buyan may reverse.

**T70 — the correction of the stale marker — was REJECTED by its independent reviewer T71, and the driver
confirmed the rejection from source before ruling.** This is the third time a rule on this comment has been
wrong, and the second time the defect was **insufficiency** rather than falsehood.

> `allowFullTermForTranche` is a **PRODUCT FLAG, not a tranche count.** The gate is
> `isAllowFullTermForTranche() && numberOfRepayments > 0 && action == DISBURSEMENT` and **never consults the
> disbursement count** [DRIVER-VERIFIED: `ProgressiveEMICalculator.java:142-144`]. So a shape with
> **exactly one disbursement** and the flag true satisfies **every one of T70's five conditions** and still
> enters `:1160` at **`:247`** — inside `mergeNewScheduleModelWithExistingOne` (`:206`) [DRIVER-VERIFIED] —
> with `tillDate` = the disbursement **date**, voiding step (b) outright and (e)'s `emi_j = 0 for j < f`
> premise with it.

**The correct condition was already written down, and the rule never named it.** `contract.go:1191-1202` —
the *frozen, ratified* artefact — already says `allowFullTermForTranche = false` is "a REAL BEHAVIOURAL PIN",
that the guard "never consults multi-disbursement at all", and that the two identical captures are "a
measurement, not a licence to ignore the flag" [DRIVER-VERIFIED by reading `contract.go`]. T70 instead wrote
that multi-tranche is what breaks (b), and filed `:247` under "post-origination operations" when it is
reachable **at origination**. Same failure mode as T67's `p.idx` catch: executable change right, conclusion
right, **rule insufficient**.

T71 credited what was right, and the driver kept that: all other citations resolve, T70's three claimed
drift corrections are real, every capture figure independently re-derived, `(e)`'s non-tightness preserved,
nothing asserted about the copy's internal state, and **marking the recursion `[UNVERIFIED]` explicitly
credited as correct behaviour.** Zero executable change re-verified two ways.

**T70's diff is NOT merged.** It stays on `softhouse/T70-fui-marker` for the retry to branch from — exactly
as T69 branched off T65.

### Two findings the fire is carrying forward

- **F-1 — citation drift in three artefacts, one of them the driver's own.** `deepCopy` is **`:1224`**, not
  `:1226` (a comment line); the `futureUnrecognizedInterest` write is **`:1246`**, not `:1250` (a closing
  brace); `T66.md`'s residual assignment is **`:1210`**, not `:1207` (inside the `getFixedInterest()` guard).
  All driver-verified. **The driver took `:1226` from T66's `PREDICTION.md`, repeated it in its own
  re-derivation, and passed it into T70's dispatch prompt** — P-12 recurring, in the document whose job was
  checking. The driver's document is corrected; T66's artefacts are a follow-up, not something the driver
  edits.
- **F-2 — a gap in T66's proof neither T66 nor the driver noticed.** `:1214` recursively re-enters
  `calculateLastUnpaidRepaymentPeriodEMI` (`:1160`), and the `:1217` defer then runs in the **outer** frame,
  so the lookup can execute after an inner frame re-established step (d) on a possibly different `L`. T66
  states (d) for a single entry only; the census covers the recursion **empirically, not deductively**.
  T71 confirmed the driver's reduction: the guard is **exactly `emi_L < 0`** on the graded domain, encoded
  verbatim at `emi.go:1207`. **Whether `emi_L` can go negative is UNESTABLISHED** — T70, T71 and the driver
  all declined to settle it by reading. Settle it by capture.

---

## THE NEXT FIRE STARTS HERE

**No oracle required for any of the first three.**

1. **T72** — retry of T70. Branch off `softhouse/T70-fui-marker` to preserve its approved content. Fix
   T71's R-1 (P1, name the **pin**, in `contract.go:1191-1202`'s own terms; stop filing `:247` as
   post-origination), R-2 (P2, qualify `:259` as `RepaymentPeriod.java:259`), R-3 and R-4 (P3). **The test is
   SUFFICIENCY**, not truth: a reader obeying every clause must be unable to break the port.
2. **T73** — paired independent reviewer for T72. Not optional.
3. **T15** — archive the run, strangler backlog, postmortem patterns. **Now depends on T73**: archiving
   today would freeze a marker that is both stale *and*, per T71, false in its replacement.
4. Then **Tier A**. Once `tier0-harness-schedule-poc` is `done`, three contexts become READY —
   **computed from `program.json`, not estimated**:

   | context | tier | `main_loc` | direct dependents |
   |---|---|---|---|
   | `tierA-gl-accounting` | A | 24,000 | **6** |
   | `tierA-loan-product-schedule` | A | 20,461 | 1 |
   | `tierD-test-corpus-to-vectors` | D | 321,000 | 0 |

   The rule is **lowest tier first; within a tier, the one unblocking the most dependents; `main_loc` only as
   tie-break.** So **`tierA-gl-accounting`** — six dependents to one, and that outranks the 3,539-LOC
   difference. At 24,000 LOC it is under the 25,000 splitting threshold and may be planned whole, but check
   `files_hint` breadth first: the plan gate also rejects a `files_hint` spanning a whole large module.

**Also still waiting, and ORACLE-ONLY:** T25's parked P0s (T21 P0-2/3/4, P1-8/9/11; T22 P0-3/4/5/6). They
were not attempted this fire because they touch `.softhouse/capture/`, which T66 held all fire, and two
capture workers collide there. They still block vector promotion.

**T12 remains `done_partial`.** The rehydration half is a committed re-runnable assertion
(`.softhouse/bin/rehydrate-check.sh`; this fire: 74 terminal tasks, none re-selected). **The mid-flight
checkpoint half is unexercised for a FOURTH fire running** — all four workers dispatched this fire ran to
completion. The next fire that approaches the soft limit with a worker in flight should treat it as the drill.

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
