# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's session state.

## Current state (cloud catch-up fire `20260817-2000`, 20:00 Asia/Ulaanbaatar)

- **Program**: `fineract-to-go-full-codebase` — **active, blocked at gate G-1**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — `blocked_on_gate`
- **Contexts**: 0 done / 17. Tier 0 is `blocked_on_gate`; **all 16 others declare tier 0 as a transitive dependency**, so G-1 gates the entire program.
- **Reference oracle**: **NOT reachable from the cloud sandbox** — no Docker daemon, PostgreSQL not listening on `:5432`, `actuator/health` silent. Reachability is now recorded **per fire** in `.softhouse/reference-oracle.md`; the "Status: UP" line was a fact about localhost on Buyan's Mac, not about the program.
- **Fineract source**: pinned and verified at `426a23544e8426a38ae43ae404670a0a7e85b9eb` (`/home/user/fineract` in the cloud sandbox).
- **Worker isolation**: all four workers ran in **real worktrees** on `softhouse/*` branches. The previous fire's isolation violation was not repeated.

### What this fire did

Dispatched four opus workers; every analyst task had a paired independent reviewer that re-derived rather than read.

| Task | Verdict | Outcome |
|---|---|---|
| **T3b** re-review of the corrected behaviour extraction | **REJECTED** | 6 of 12 required changes landed; corrections leaked (see below) |
| **T5** review of DEC-1 | **REJECTED** | Found a money defect the corpus cannot detect |
| **T16** vector-capture plan | delivered | 16 vectors transcribed, 9 capture runs specified |
| **T17** transcription audit of T16 | **ACCEPTED** | 418/418 values literally present; zero synthesised |

### The two findings that matter most

1. **DEC-1 would have frozen an ambiguity that changes money.** Fineract threads **one** `MathContext` and consumes it in **two incompatible senses** — significant digits in every `multiply/divide(…, mc)`, and **decimal places** in `setScale(mc.getPrecision(), …)` (`ProgressiveEMICalculator.java:1962`, `:1979`). Over a 560-config grid, **189 configurations diverge**; the first money divergence is at 18 installments / 18.5 % / principal 87,654,321, where a one-minor-unit error appears in period 5 and **never heals**. **The shipped conformance vector does not discriminate between the two readings** — so "the golden test passes" is not evidence here.
2. **Two reviewers converged independently.** T3b (reviewing the analysis) and T5 (reviewing the contract), with no shared context, both refuted the claim that `allowFullTermForTranche` is a dead field. The builder setter reaches it (`LoanApplicationTerms.java:606`) and the guard (`ProgressiveEMICalculator.java:142-144`) never consults `isMultiDisburseLoan()`.

### Task state

| Task | State | Note |
|---|---|---|
| T1 pin reference oracle | **done** | |
| T2 extract schedule behavior | **parked** | Retries exhausted (policy 1). Rejected twice. Unpark = gate **G-2** |
| T3 / T3b independent reviews | **done** | Both REJECTED their subject |
| T4 DEC-1 draft | **needs_retry** | 1 retry left. Deliberately not run this fire — see below |
| T5 review DEC-1 | **done** | REJECTED, 9 required changes |
| T6 **USER GATE** ratify DEC-1 | **blocked** | **Gate G-1 — not yet answerable** |
| T7, T9–T15 | pending | Behind T6 |
| T8 capture golden vectors | **parked** | `oracle_unreachable`. Nothing synthesised |
| T16 capture plan / T17 audit | **done** | Accepted; execution gated on T16b |
| T16b apply T17's 6 corrections | **pending** | **Needs no oracle — good first work for any fire** |

### Next action, in order

1. **T16b** — apply T17's six corrections to `docs/analysis/tier0-vector-capture-plan.md`. Pure source work, no oracle needed. Any fire can do this immediately.
2. **On an oracle-reaching fire only:** capture the **discriminating vector** for the precision-vs-scale question (T5 §1 gives the exact configuration), then run the **C-00 calibration capture** — which must reproduce an already-transcribed literal expectation before any other capture is trusted.
3. **T4 retry (attempt 2 of 2)** against T5's nine required changes — but only after Buyan answers the G-1 decision list, since several changes are choices reserved for him.
4. Re-review, then re-present gate G-1.

### Why the T4 retry was NOT dispatched this fire

Three reasons, all recorded on the task: (a) T3b had not landed, so the factual basis could still move; (b) T5 recommends the discriminating vector be captured **before** ratification and the corpus provably cannot detect this defect class — that capture needs the oracle; (c) several of the nine changes are choices T5 explicitly reserved for the human ratifier, and an agent picking them would pre-empt Buyan.

**Routing fact worth restating:** DEC-1 is an **unratified DRAFT**, so correcting it is agent work. Only a **ratified** DEC-n is a user gate.

### Open decisions for Buyan — `.softhouse/gates.md`

- **G-1 CONTRACT** — six decisions listed, including whether to rename `IntermediatePrecisionDigits`, which of two ordering fixes to take, and what rounding mode the Mongolian tenant will actually run (unresolvable from source: properties default `6`/`HALF_EVEN`, tests mock `HALF_UP`; production `MoneyHelper.PRECISION = 19` vs `12` mocked).
- **G-2 POLICY** — permit a third, *differently shaped* attempt at T2 (surgical edits + a mechanical sweep for restated claims), or treat T3b's review as the specification of record.

### Lead worth following up (not acted on)

The seam has a **dependency-free shadowJar entry point** with a documented `Main.java`, and this sandbox has **JDK 21.0.10 and gradle**. Most Tier-0 capture may need only a JDK — **not a running server and not PostgreSQL** — which would remove the single-machine bottleneck for Tier-0 vectors. **Not attempted this fire on purpose:** gradle writes `build/` into the very module three reviewers were grepping, and polluting a review in flight was not worth the information. Worth a clean attempt on a fire with no reviewers running. Note that a jar built on a different JVM is *not* automatically the pinned oracle — `.softhouse/reference-oracle.md` says a capture against a different build is not comparable, so promoting it to a capture path is Buyan's call, and C-00 calibration would have to pass first.

## Checkpoint protocol (what a real pause looks like here)

1. Every active worker commits WIP to its `softhouse/<taskid>-<slug>` branch.
2. Each squad writes `.softhouse/state/<squad>.STATE.json` — current item, step, branch, next action, blocked_on, open questions, gate_pending.
3. The orchestrator rewrites this file: active squads, their next steps, and the reason for the pause.
4. Orchestrator commits `.softhouse/` and pushes. Nothing else pushes.
5. Next fire runs `/softhouse-program`, which rebuilds everything from this file + `state/*.STATE.json` + `program.json` + the WIP branches.

## Pause reason

`Gate G-1 reached and not answerable; no READY context remains (all 16 declare tier 0 as a transitive dependency). This is the decision table's one legitimate idle stop — reached only after spending the fire on every piece of work that needed no live oracle. No bar was lowered, no vector invented, no gate crossed.`
