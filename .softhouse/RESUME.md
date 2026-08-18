# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's session state.

## Current state (local fire `20260818-173900`, oracle REACHABLE, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active, blocked at gate G-1**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — `blocked_on_gate`
- **Contexts**: 0 done / 17. Tier 0 `blocked_on_gate`; the other 16 are **READY-FOR-ANALYSIS**.
- **Reference oracle**: **REACHABLE** all fire. Image `sha256:e596339626bf…`, commit build-attested `426a23544`, Zulu 21.0.11, PostgreSQL 18.3. A second tenant **`gerege`** (`fineract_gerege`, `Asia/Ulaanbaatar`, rounding-mode 4 = HALF_UP) now exists, provisioned by the T22 auditor.
- **Four opus workers dispatched, four completed, four merged, none killed.** The previous fire's failure mode did not recur.

## The headline: G-1 is no longer waiting on a question — it is waiting on three corrections

DEC-1 **v2 exists** and was independently re-reviewed. The driver **did not ratify**: standing policy **P-2** allows ratification on a *clean* review, and T23's verdict is `ACCEPTED WITH REQUIRED CHANGES — NOT ratifiable`. Three P0 defects, every one observed against the oracle rather than argued.

**Nothing in G-1 needs Buyan.** All three P0s are ENGINEERING, and the local fire can reach the oracle.

## What this fire did

**1. Rescued the previous fire's work — again, and properly this time.** The 17:00 fire's rescue had committed 4,482 insertions to three `softhouse/*-rescued` branches that were **never pushed**, so neither the cloud fire nor a fresh clone could see them. All three are now on `origin`, and the useful probe artifacts are on `main`.

**2. Re-dispatched both killed audits, and both landed.**
- **T21** (capture pass 3) — `ACCEPTED WITH REQUIRED CHANGES`.
- **T22** (Path B) — `ACCEPTED WITH REQUIRED CHANGES`.

**3. Delivered DEC-1 v2** (T4 attempt 2) and **had it re-reviewed** (T23) in the same fire.

**4. Declined to ratify.** The single most consequential thing this fire did was not close G-1.

## Findings that matter

1. **The contract-domain / graded-domain split survived adversarial review.** DEC-1 v2's organising idea — freeze every value the types admit, but grade only the subset a capture can discriminate — answers the defect that rejected v1. T23 confirmed the graded domain can widen **without amending a ratified DEC-n**, so it is not a loophole around a hard gate.
2. **The "silently dropped component" worry is closed as a class.** T23 mechanically diffed all 37 `Builder` fields against the 36 copied and all 19 record components: **no third dropped component exists.** T19's fear of an open-ended defect class is retired.
3. **The EMI re-adjust loop is live inside the graded domain** — the sharpest finding of the fire. DEC-1 §4.3 says it is reachable only outside. It is called at `ProgressiveEMICalculator.java:749` on **every** generation, and its guard does not depend on installment rounding at all, because `Money.copy(double)` **replaces** the amount. **7 of 10 graded-domain requests diverge from the contract as specified, and no vector in the corpus trips it.**
4. **Path B grades what Path A drops** — `installmentAmountInMultiplesOf` moves 12/12 periods (`B-02`); `daysInYearCustomStrategy` moves the schedule only via `FEB_29_PERIOD_ONLY` (`B-04`), because `FULL_LEAP_YEAR` is **byte-identical to the field being unset**.
5. **A false rounding rule was caught one step before it froze.** The oracle rounds the EMI to the **nearest** multiple under the tenant mode, not up (`Money.java:163-171`) — observed rounding **down**, `111,148.35 → 111,100.00`.
6. **The size-threshold claim is refuted.** Divergence at principal **4.00** on the 36×16.8% shape; **none** at 50,000,000 or 87,654,321. Sensitivity is a rounding boundary of `(principal, n, rate)`, not a size effect. All four MNT captures are p12/p19-identical.
7. **The Path B captures ran at HALF_EVEN**, not the ratified HALF_UP. They are mode-insensitive — but that was established by **re-observing** them at HALF_UP, not assumed.

### Errors the reviewers caught in earlier work

- The killed T21 worker's "P-03 fails invariant X2" was a **false alarm**: `X2` is not one of the six invariants, and its formulation is invalid for a schedule whose first row precedes disbursement.
- That worker's `threshold` and `rederive` scripts are **wrong** — the model never applies the EMI smoothing pass and misreads `Money.copy(double)` as a multiply. They are on `main` and **must be retracted** (T25).
- The prior Path B `invariants.py` had **`I5` hard-coded to PASS**.

## Task state

| Task | State | Note |
|---|---|---|
| T1 pin reference oracle | done | |
| T2 extract schedule behavior | **parked** | Unpark = gate **G-2** (Buyan: *yes, once, reshaped*) |
| T3 / T3b reviews | done | Both REJECTED their subject |
| **T4 DEC-1 draft** | **done** | v2 delivered and merged. Not ratified. |
| T5 review DEC-1 v1 | done | REJECTED, 9 required changes — **8 now SATISFIED, 1 PARTIAL** |
| T6 **USER GATE** ratify DEC-1 | **blocked** | **G-1** — now scoped to T23's three P0s |
| T7, T9–T12, T14, T15 | pending | Behind T6 |
| T8 capture golden vectors | in_progress | 3 Path A passes + 4 Path B captures; **no vector promoted** |
| T13 verify (UAT) | pending | Now also gated on T21, T22, T23 |
| T16 / T16b / T17 | done | |
| T18 / T19 capture audits 1–2 | done | Both ACCEPTED WITH REQUIRED CHANGES |
| T20 fold F2–F6 into harness | pending | Behind T7 |
| **T21** audit pass 3 | **done** | ACCEPTED WITH REQUIRED CHANGES — 4 P0, 7 P1 |
| **T22** audit Path B | **done** | ACCEPTED WITH REQUIRED CHANGES — 6 P0, 8 P1 |
| **T23** re-review DEC-1 v2 | **done** | ACCEPTED WITH REQUIRED CHANGES — **not ratifiable**, 3 P0 |
| **T24** apply T23's P0s | **pending** | **Next fire's first task** |
| **T25** apply T21+T22 P0s to the corpus | **pending** | Contract-independent; may run alongside T24 |

## Next action, in order

1. **T24** — apply T23's three P0 corrections to DEC-1 v2. P0-1 also requires **capturing vectors that trip the EMI re-adjust loop**, which the corpus currently cannot do, so this needs the oracle.
2. **Raise and run the re-review of T24.** DEC-1 must not be ratified on the drafter's say-so.
3. **Ratify under P-2 and close G-1** — the driver's call, not Buyan's, once the re-review is clean.
4. **T25** — apply the T21/T22 P0 lists and retract the three defective scripts on `main`. **Until this lands, no capture may be promoted to the vector store.**
5. **G-2**: Buyan approved one reshaped T2 attempt — surgical edits plus a mechanical restatement sweep.

## Open decisions for Buyan

- **None blocking Run 1.** G-1's remaining work is all ENGINEERING. Licence (NBFI ББСБ) and rounding mode (HALF_UP) are decided.
- **RESERVED and untouched**: cutover, regulatory/parallel-run sign-off, deposit-taking activation. None is in Run 1's path.

## Checkpoint protocol (what a real pause looks like here)

1. Every active worker commits WIP to its `softhouse/<taskid>-<slug>` branch — and the orchestrator **awaits it**. A worker still running when the turn ends is dead, not paused.
2. Each squad writes `.softhouse/state/<squad>.STATE.json`.
3. The orchestrator rewrites this file.
4. Orchestrator commits `.softhouse/` **and pushes every branch**, not just `main`. An unpushed branch is invisible to the cloud fire and to a fresh clone.
5. Next fire runs `/softhouse-program`, rebuilding from this file + `state/*.STATE.json` + `program.json` + the WIP branches.

## Pause reason

`Clean exit at the token checkpoint. Four workers dispatched, four awaited, four merged, none killed — the previous fire's failure mode did not recur. Every deliverable is committed and pushed; no worker WIP is outstanding. Not an idle stop: the fire ended with T24 and T25 queued and fully specified. G-1 was deliberately NOT closed, because the re-review that would have licensed ratification under P-2 was not clean. No vector promoted, no bar lowered, no gate crossed.`
