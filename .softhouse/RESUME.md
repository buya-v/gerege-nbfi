# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's session state.

## Current state (local fire `20260818-152328`, oracle REACHABLE, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active, blocked at gate G-1 (ratification signature only)**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — `blocked_on_gate`; contract-independent work advanced all fire
- **Contexts**: 0 done / 17. Tier 0 `blocked_on_gate`; the other 16 are **READY-FOR-ANALYSIS**.
- **Reference oracle**: **REACHABLE**. Image `sha256:e596339626bf…`, commit **build-attested** by the jar's own `git.properties` (`git.dirty=false`), Zulu 21.0.11, PostgreSQL 18.3. `caffeinate` held sleep off — the first fire today to exit cleanly.
- **Production `MathContext` = `(19, HALF_UP)`** — ratified. `MoneyHelper.PRECISION = 19` is a compile-time constant; only the mode was ever a choice.

## The headline: G-1 is now one signature away

Buyan answered every G-1 decision this fire (`.softhouse/gates-proposed-answers.md`) and ratified **HALF_UP** and the **NBFI (ББСБ) licence** — which also closes the deposit-taking activation gate as *prohibited* (Art. 12.1.3 / 12.1.4): savings code ports, ships disabled, no endpoint exposed.

What remains before the signature is agent work, not human: **T4's retry**, then a re-review.

## What this fire did

**1. Rescued the previous fire's abandoned work.** Fire `20260818-080003` built a capture harness, ran it against the oracle and died mid-run; the wrapper committed its output but nobody had read it. It contained **the discriminating vector G-1 had been waiting for**.

**2. Ran two more capture passes** (orchestrator-only — capture touches the oracle):
- **Pass 2** added a tenant context, closing pass 1's `D-04` error.
- **Pass 3** re-captured at production settings after the ratification — **12 parity candidates**, the first that exist.

**3. Dispatched three opus reviewers in worktrees.** Nothing produced this fire was accepted on its author's say-so — including the orchestrator's own captures, which were audited and found wanting in three places.

## Findings that matter

1. **DEC-1 as drafted is empirically wrong by one minor unit** (T18, re-derived independently at p8/p12/p19 and reproduced against the oracle exactly). At precision 12 the oracle emits period-5 principal `4,531,420.25`; the significant-digits-only reading DEC-1's text describes emits `…26`. This is no longer arguable.
2. **The conformance rig has a structural defect.** The capture seam accepts a **19-component contract and honours 17**. `installmentAmountInMultiplesOf` is never read by `assembleFrom`; `daysInYearCustomStrategy` is read but never copied by the `Builder` copy-constructor (`:304-351`). For both, the corpus has **zero discriminating power** — a Go port could honour or ignore them and score identically. Buyan's answer: expose them, specify server semantics normatively, and **refuse** with "unsupported: no discriminating vector" until Path-B vectors exist. Never silently drop.
3. **Two capture paths are now distinguished** (`.softhouse/reference-oracle.md`): **Path A** (embeddable seam, in-process, no database — all three passes) and **Path B** (running server + PostgreSQL, unused). Path B is now a *prerequisite* for the parity corpus, not an optimisation.
4. **Precision is load-bearing only above a size threshold** — the same precision change that is a no-op on a 100-unit loan moves money at principal 87,654,321. A corpus topping out at 245,000 could never have caught it. **Unaudited orchestrator claim — T21 should test it.**
5. **The rig is calibrated across three independent harnesses**, and all 12 pass-3 captures satisfy all six property invariants, integer-exact.

### Three errors the reviewers caught in the orchestrator's own work

Recorded because they are the reason the review step exists, and because the write-ups were cited in `gates.md`:

- **An over-claim about the precision sweep** (T18): it cannot separate the two `MathContext` *senses* — one integer drives both — and the sense-1 schedule at p12 is *identical* to the oracle's at p19, so reading the `D-01`/`D-01-p19` delta as "the sense difference" is wrong. `gates.md` corrected.
- **A false headline argument** (T19): "a `17.01` EMI rounded to multiples of 100 cannot be a no-op" — it can; `safeRoundingForEMI` returns the unrounded EMI when rounding would zero it.
- **A false corroboration** (T19): the `CurrencyData.inMultiplesOf` channel is gated on `decimalPlaces == 0` and the harness hard-codes `2`, so it proved nothing.

The conclusions survived — and the central one was upgraded from *inferred* to *proved* by the auditor's reflective read — but the arguments did not, and are withdrawn on the record.

## Task state

| Task | State | Note |
|---|---|---|
| T1 pin reference oracle | done | |
| T2 extract schedule behavior | **parked** | Retries exhausted. Unpark = gate **G-2** (Buyan: *yes, once, reshaped*) |
| T3 / T3b independent reviews | done | Both REJECTED their subject |
| **T4 DEC-1 draft** | **needs_retry — NOW UNBLOCKED** | 1 retry left. Every decision feeding it is answered. **This is the next fire's main event.** |
| T5 review DEC-1 | done | REJECTED, 9 required changes |
| T6 **USER GATE** ratify DEC-1 | **blocked** | **G-1 — signature only, once T4's retry is re-reviewed** |
| T7, T9–T12, T14, T15 | pending | Behind T6 |
| T8 capture golden vectors | in_progress | 3 passes captured; passes 1–2 audited; **no vector promoted to the store** |
| T13 verify (UAT) | pending | Gated on T9/T11/T12/T18/T19/T21 |
| T16 / T17 capture plan + audit | done | |
| T16b apply T17's corrections | **done, merged** | Arrival state was 1.5 of 6, not the ~5 estimated |
| T18 audit capture pass 1 | **done** | ACCEPTED WITH REQUIRED CHANGES (4 P0 blockers) |
| T19 audit capture pass 2 | **done** | ACCEPTED WITH REQUIRED CHANGES (10 required changes) |
| **T21** audit capture pass 3 | **pending** | **Run this first next fire** — pass 3 is the corpus conformance would grade against |
| T20 fold F2–F6 into the harness | pending | Behind T7 |

## Next action, in order

1. **T21** — audit capture pass 3. It inherits `Capture2.java`'s defects and is unaudited; nothing should be graded against it until this lands.
2. **T4 retry** (attempt 2 of 2) against T5's nine required changes **plus** every answer in `gates-proposed-answers.md`. Nothing human blocks it any more.
3. **Re-review T4**, then present G-1 for signature.
4. **G-2**: Buyan approved one reshaped T2 attempt — surgical edits plus a mechanical restatement sweep. T16b just proved that shape works.
5. **Apply T18's P0 list and T19's ten required changes** to all three passes before any capture becomes a vector: environment-attestation block, `fromDate`/`fee`/`penalty` emission, committed run recipes, retained stack traces.
6. **Path B** (server + PostgreSQL capture) — now a prerequisite for the parity corpus. Not started; needs planning, not just execution.

## Open decisions for Buyan

- **G-1** — only the **ratification signature** on the corrected DEC-1 remains. Everything feeding it is answered.
- **RESERVED, still open**: none blocking Run 1. (Licence and rounding mode are both now decided.)

## Checkpoint protocol (what a real pause looks like here)

1. Every active worker commits WIP to its `softhouse/<taskid>-<slug>` branch.
2. Each squad writes `.softhouse/state/<squad>.STATE.json` — current item, step, branch, next action, blocked_on, open questions, gate_pending.
3. The orchestrator rewrites this file: active squads, their next steps, and the reason for the pause.
4. Orchestrator commits `.softhouse/` and pushes. Nothing else pushes.
5. Next fire runs `/softhouse-program`, which rebuilds everything from this file + `state/*.STATE.json` + `program.json` + the WIP branches.

## Pause reason

`Clean exit. All three dispatched workers landed and merged; all deliverables committed; no worker WIP outstanding. Not an idle stop — the fire ended with work queued (T21, then T4's retry), and the next fire should start on T21 immediately. No vector was promoted, no bar lowered, no gate crossed.`
