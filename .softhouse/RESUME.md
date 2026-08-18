# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's session state.

> **This file was written MID-FIRE on purpose.** Both 2026-08-18 fires before this one were killed by the Mac sleeping and left stale state behind. It is rewritten again at clean exit; if it still says "in flight" below, this fire died too and the branches named are where the work is.

## Current state (local fire `20260818-152328`, oracle REACHABLE)

- **Program**: `fineract-to-go-full-codebase` — **active, blocked at gate G-1**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — `blocked_on_gate`, but contract-independent work is running
- **Contexts**: 0 done / 17. Tier 0 is `blocked_on_gate`; the other 16 are **READY-FOR-ANALYSIS** under `policy.gate_scope`.
- **Reference oracle**: **REACHABLE** — image `sha256:e596339626bf…`, Fineract `426a23544`, Zulu 21.0.11, PostgreSQL 18.3 on `:5432`. `caffeinate` now holds sleep off during a fire.

### What this fire did

**1. Rescued and processed the previous fire's abandoned work.** Fire `20260818-080003` built a golden-vector capture harness and ran it against the pinned oracle, then died mid-run; its output was committed by the wrapper but never read by anyone. It turned out to contain **the discriminating vector gate G-1 was waiting for**.

**2. Ran capture pass 2** (orchestrator, oracle-only work) adding a tenant context, which pass 1 lacked.

**3. Dispatched three opus reviewers in worktrees** — nothing produced this fire is accepted on its author's say-so.

### Findings that matter

1. **Precision is load-bearing, observed.** Pass 1 ran T5's exact configuration (18 × 18.5 %, principal 87,654,321) at precisions 8 / 12 / 19. p8 vs p12 differ in **every period** (EMI `5,613,766.95` vs `5,613,766.78`); p12 vs p19 differ by one minor unit in period 5 and in the final period. The shipped corpus cannot see this; the oracle can.
2. **`installmentAmountInMultiplesOf` is silently dropped by the capture seam.** `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)` reads 18 of the record's 19 components and never reads that one. The server path honours it. **A Go port could honour or ignore it and score identically against every vector this path can produce** — the same undiscriminable-input defect class T5 found for precision, in a second field, on a parameter Mongolian products would routinely use. Raised as **G-1 decision 7**.
3. **`allowFullTermForTranche` is live — confirmed by the running oracle**, a third independent confirmation and the first that is not a source reading. Pass 1's `D-04` crashed for want of a tenant, proving the `true` branch reaches `MoneyHelper`; with a tenant it runs and is schedule-identical to `false` on single-disbursement loans.
4. **C-00 calibration passes** from two independent harnesses, with and without a tenant.
5. **Two capture paths are now distinguished** in `.softhouse/reference-oracle.md`: **Path A** (embeddable seam, in-process, no database — what both passes used, and which has the proven blind spot above) and **Path B** (running server + PostgreSQL, unused, the only way to reach what Path A drops).

### Task state

| Task | State | Note |
|---|---|---|
| T1 pin reference oracle | done | |
| T2 extract schedule behavior | **parked** | Retries exhausted. Unpark = gate **G-2** |
| T3 / T3b independent reviews | done | Both REJECTED their subject |
| T4 DEC-1 draft | **needs_retry** | 1 retry left. Blocked on Buyan answering G-1 decisions 1–7 |
| T5 review DEC-1 | done | REJECTED, 9 required changes |
| T6 **USER GATE** ratify DEC-1 | **blocked** | **Gate G-1 — still not answerable, but the evidence now exists** |
| T7, T9–T12, T14, T15 | pending | Behind T6 |
| T8 capture golden vectors | **in_progress** | Unparked. Passes 1 + 2 captured, raw observed, **no vector promoted** |
| T13 verify (UAT) | pending | Now also gated on T18, T19 |
| T16 / T17 capture plan + audit | done | |
| **T16b** apply T17's 6 corrections | **in flight** | branch `softhouse/T16b-capture-plan-corrections`; WIP commit `1a9c3c8` has ~5 of 6; correction #2 (FULL_LEAP_YEAR) verifiably not applied |
| **T18** audit capture pass 1 | **in flight** | opus, worktree |
| **T19** audit capture pass 2 | **in flight** | opus, worktree — audits the orchestrator's own work |

### Next action, in order

1. **Land T18 / T19 / T16b**; act on their verdicts. A REJECTED capture means the finding above is not yet fact.
2. **Buyan answers G-1 decisions 1–7** (`.softhouse/gates.md`). Decision 7 is new this fire and is the most consequential.
3. **T4 retry** (attempt 2 of 2) once 1–7 are answered.
4. Re-review, re-present G-1.
5. **Not before someone decides it:** Path B capture (server + PostgreSQL) is the only way to close what Path A drops. The orchestrator recommends **against** building it inside Tier 0 — Tier 0 exists to prove the pipeline on the smallest real slice.

### Open decisions for Buyan — `.softhouse/gates.md`

- **G-1 CONTRACT** — now **seven** decisions. Four of the original six are newly evidenced by observation; decision 7 (`installmentAmountInMultiplesOf` inert on the grading path) is new and the orchestrator recommends (b) or (c) over (a).
- **G-2 POLICY** — permit a third, differently-shaped attempt at T2, or treat T3b's review as the specification of record.

## Checkpoint protocol (what a real pause looks like here)

1. Every active worker commits WIP to its `softhouse/<taskid>-<slug>` branch.
2. Each squad writes `.softhouse/state/<squad>.STATE.json` — current item, step, branch, next action, blocked_on, open questions, gate_pending.
3. The orchestrator rewrites this file: active squads, their next steps, and the reason for the pause.
4. Orchestrator commits `.softhouse/` and pushes. Nothing else pushes.
5. Next fire runs `/softhouse-program`, which rebuilds everything from this file + `state/*.STATE.json` + `program.json` + the WIP branches.

## Pause reason

`In flight at time of writing — three reviewers running (T16b, T18, T19). Rewritten at clean exit. If this text survives, the fire died mid-run and the work is on the branches named above.`
