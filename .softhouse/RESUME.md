# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's session state.

## Current state (cloud catch-up fire `cloud-20260818-2000`, oracle UNREACHABLE, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active, blocked at gate G-1**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — `blocked_on_gate`
- **Contexts**: 0 done / 17. Tier 0 `blocked_on_gate`; the other 16 are **READY-FOR-ANALYSIS**.
- **Reference oracle**: **UNREACHABLE all fire** — expected for a cloud fire. Every vector-capture and conformance task stayed parked `oracle_unreachable`. **No vector was synthesised, promoted, or implied.**
- **Ten workers dispatched, nine completed and merged, one killed by an infrastructure error and re-run to completion.**

## Read this first: the local fire is losing its workers

The **local fire `20260818-200001` dispatched T24 and T25 at 20:01:23 and checkpointed 104 seconds later** with both still marked `in_flight`. No `softhouse/T24-*` or `softhouse/T25-*` branch was ever created. Two opus workers cannot finish in 104 seconds — **both died and their work was lost.**

This is the **second consecutive recurrence** of the failure mode `SKILL.md` STEP 5.5 exists to prevent (the first, at 17:22, stranded 4,482 insertions). **`.softhouse/bin/fire-program.sh` on the Mac appears to dispatch and exit without awaiting its workers.** Until that is fixed, every local fire burns opus budget and lands nothing. This cloud fire re-did both tasks from scratch and awaited every worker.

**A premise in the last manifest was also wrong.** It said T24 "needs the oracle". It did not: T23's P0-1 requires *re-scoping* backlog item 8.3, not capturing the vectors now, and every figure T24 needed was already committed by T23. **All ten tasks this fire ran turned out to need no live oracle.** Before parking a task `oracle_unreachable`, check whether it needs a *new observation* or merely *an observation already committed*.

## The headline: DEC-1 went v2 → v6, and G-1 is still open — correctly

Four independent re-reviews ran this fire and **not one came back clean**, so the driver never ratified. Standing policy **P-2** licenses ratification only on a clean review.

| Review | Subject | Verdict | New P0s |
|---|---|---|---|
| T26 | DEC-1 v3 | ACCEPTED WITH REQUIRED CHANGES | 1 — EMI re-adjust loop specified by *trigger*, never *effect* |
| T29 | DEC-1 v4 | ACCEPTED WITH REQUIRED CHANGES | 2 — `n` misdefined; **per-period interest specified nowhere** |
| T32 | DEC-1 v5 | ACCEPTED WITH REQUIRED CHANGES | 1 — rate-factor **day counts** undefined; `contract.go` asserted a falsehood |
| — | **DEC-1 v6 (T33)** | **applied, awaiting review** | v6 now discriminates **all three** readings the corpus is blind to |
| T34 | DEC-1 v6 | **not yet run — NEXT FIRE'S FIRST CONTRACT TASK** | ? |

### The pattern that matters more than any single finding

**Every one of those P0s was invisible to the corpus.** By T32 the committed corpus passed **three distinct wrong readings at 13/13 each** — ratio-is-always-1, textbook `balance × rateFactor`, and wrong-`n`. "The golden vectors pass" has so far been **no evidence of correctness in this contract**. That is precisely the failure DEC-1 exists to prevent: a port that passes its corpus and is wrong.

The document **is** converging, though — this is not thrash. T32 verified T28's loop steps 1–8 preserved **byte-for-byte** and T29's two P0s genuinely resolved with every cited `file:line` exact. Each new P0 has been **fresh ground**, not re-opened ground. A clean verdict is a live possibility.

### Sharpest single finding

T32's, on a shape revision 5 itself admits: a disbursement dated **strictly inside** a repayment period. Across 2,913 such in-graded-domain shapes the two readings the artefacts licensed **diverge on 100 %**, worst total-interest gap **MNT 1,816,050.11** — one reading charges **a full month's interest on a 17-day exposure**. No committed observation and no probe in this program had modelled that shape.

## Task state

| Task | State | Note |
|---|---|---|
| T1, T3, T3b, T5, T16–T19, T21–T23 | done | earlier fires |
| T2 extract schedule behavior | **parked** | Unpark = gate **G-2** (Buyan: *yes, once, reshaped*) |
| T6 **USER GATE** ratify DEC-1 | **blocked** | **G-1** — all remaining work is ENGINEERING; nothing needs Buyan |
| T8 capture golden vectors | in_progress | 3 Path A passes + 4 Path B captures; **no vector promoted** |
| T13 verify (UAT) | pending | Needs the harness + live oracle |
| **T24** DEC-1 v3 | **done** | Re-done by this fire after the local fire lost it |
| **T25** corpus corrections | **done_partial** | Oracle-free slice only; re-capture items parked |
| **T26** re-review v3 | **done** | NOT ratifiable — 1 new P0 |
| **T27** promotability audit | **done** | Nothing promotable; caught T25 dropping and mis-parking items |
| **T28** DEC-1 v4 | **done** | Loop *effect* specified; spec-check reproduces 3/3 |
| **T29** re-review v4 | **done** | NOT ratifiable — 2 new P0. Attempt 1 killed by API 521, WIP rescued |
| **T30** corpus remainder | **done** | B-03/B-04 re-derived from source, **CONSISTENT**; T22 P0-5 closed |
| **T31** DEC-1 v5 | **done** | `n` + interest computation specified; discriminates both wrong readings |
| **T32** re-review v5 | **done** | NOT ratifiable — 1 new P0 |
| **T33** DEC-1 v6 | **done** | Day counts defined, false clause deleted; spec-check discriminates all three wrong readings |
| **T34** re-review v6 | **pending** | **Next fire's first contract task** |

## Next action, in order

1. **T34 — independent re-review of DEC-1 v6.** T33 landed and merged (`1f2ed62`), so v6 is on `main` and reviewable. T34 needs **no oracle**. If it comes back clean, **the driver ratifies under P-2 and G-1 closes without ever reaching Buyan.** Tell the reviewer the four-round pattern below, and point it at the surface T32 named as least examined: period/date generation and the month-end re-anchor, the down-payment path, the balance roll-forward and its zero clamp, and currency/scale handling.
2. **Oracle work, local fire only** — the six outstanding P0 admissibility items (T21 P0-2/3/4, T22 P0-3/4/6) and backlog vectors **3, 3a, 3b, 3c, 3d**. Until those land, nothing is promotable and there is no `loanschedule` conformance PASS.
3. **G-2** — Buyan approved one reshaped T2 attempt.

## What only the local fire can do

Everything needing a **new observation**: the attestation blocks, the missing capture columns, the run recipes, and all five backlog vectors. **The cloud fire has now exhausted the oracle-free contract work down to T34.** If the local fire's dispatch bug is not fixed, that queue does not move.

## Open decisions for Buyan

- **None blocking Run 1.** G-1's remaining work is entirely ENGINEERING and agent-decidable.
- **One process decision:** the local `fire-program.sh` dispatch-and-exit bug. That is a real fix on the Mac, not something a cloud fire can repair.
- **RESERVED and untouched**: cutover, regulatory / parallel-run sign-off, deposit-taking activation, licence facts. None is in Run 1's path.

## Checkpoint protocol (what a real pause looks like here)

1. Every active worker commits WIP to its `softhouse/<taskid>-<slug>` branch — and the orchestrator **awaits it**. A worker still running when the turn ends is dead, not paused.
2. Each squad writes `.softhouse/state/<squad>.STATE.json`.
3. The orchestrator rewrites this file.
4. Orchestrator commits `.softhouse/` **and pushes every branch**, not just `main`.
5. Next fire runs `/softhouse-program`, rebuilding from this file + `state/*.STATE.json` + `program.json` + the branches.

## Pause reason

`Clean exit. Ten workers dispatched, nine completed and merged, one killed by a transient API 521 and re-run to completion — its WIP was rescued to its branch rather than discarded. Every deliverable is committed and pushed, on main and on every worker branch. The fire spent itself entirely on work needing no live oracle, as a cloud fire must, and exhausted that queue down to T34. G-1 was deliberately NOT closed four times over, because no re-review came back clean. No vector promoted, no bar lowered, no gate crossed.`
