# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's session state.

## Current state (reconstructed by hand 2026-08-17 19:56 +08)

- **Program**: `fineract-to-go-full-codebase` — active
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — **executing**, mid-flight
- **Reference oracle**: **UP** — `fineract:latest` built from pinned commit `426a23544` on **PostgreSQL 18.3**, healthy at `https://localhost:8443/fineract-provider/actuator/health` (containers `fineract-fineract-1`, `fineract-db-1`). Facts: `.softhouse/reference-oracle.md`. Vector capture is possible on a LOCAL fire from now on.
- **Go toolchain**: installed by the 19:17 fire at `~/sdk/go` (go1.23.4 darwin/arm64) — `nexus/` builds and vets clean (re-verified independently).

### Task state

| Task | State | Note |
|---|---|---|
| T1 pin reference oracle | **done** | Driver assertions made against the running container; 0 `ojdbc`/`oracle.jdbc` in the jar |
| T2 extract schedule behavior | **in_progress, attempt 2** | Attempt 1 REJECTED by T3; corrected doc landed 19:53 (81 KB, 5 `[UNVERIFIED]` left) and is **not yet re-reviewed** |
| T3 independent review | **done** | Verdict **REJECTED** — re-derived EMI 17.01 + all 6 periods, caught 3 money-path defects and 4 bad citations. `.softhouse/reviews/T3-progressive-schedule-behavior-review.md` |
| T4 DEC-1 draft | **done** | `docs/adr/DEC-1-…md` + `nexus/…/contract/contract.go` (534 lines, int64 minor units, `Rate{Numerator,Denominator}`, IANA tz) |
| T5 review DEC-1 | pending | Deliberately held until the corrected T2 lands — reviewing against known-wrong facts wastes the review |
| T6 **USER GATE** ratify DEC-1 | pending | Blocks T7, T8, T10 |
| T7–T15 | pending | |

### Next action

1. Re-review the corrected T2 document against `.softhouse/reviews/T3-progressive-schedule-behavior-review.md` — confirm all 3 rejection grounds are fixed, the 4 bad citations corrected, and adjudicate the 5 remaining `[UNVERIFIED]` markers (T3's brief rejects `[UNVERIFIED]` in a money path).
2. Dispatch **T5** — and make it settle the open contract question below.
3. Then stop at **T6**, the DEC-1 ratification gate, and surface it in `.softhouse/gates.md`.

### Open question for T5 (contract-level, parity-critical)

DEC-1 defines `IntermediatePrecisionDigits` as **significant decimal digits**, but T3 found Fineract's `setScale(mc.getPrecision(), …)` truncating rate factors at a fixed **scale**. Significant-digits vs scale is exactly the mismatch that passes review and then fails bit-exact parity. Settle it against source before ratification.

### Known defects in the loop itself (fix before trusting an unattended fire)

1. **The 19:17 fire exited `rc=0` mid-run without running the checkpoint protocol** — T2's deliverable was left uncommitted, `.softhouse/state/` empty, and this file stale, i.e. the corrected work would have been invisible to the next fire. Recovered by hand; the exit protocol is now mandatory in the skill and enforced by the wrapper.
2. **Every worker ran with `isolation: NONE`** in the main working tree — no `softhouse/*` branch, so branch-based handoffs and `git diff main..<branch>` scope checks were unavailable. Recorded per task; the skill now defines the remedy (code/test tasks redone in a worktree before review).

## Checkpoint protocol (what a real pause looks like here)

1. Every active worker commits WIP to its `softhouse/<taskid>-<slug>` branch.
2. Each squad writes `.softhouse/state/<squad>.STATE.json` — current item, step, branch, next action, blocked_on, open questions, gate_pending.
3. The orchestrator rewrites this file: active squads, their next steps, and the reason for the pause (token soft limit / quota error / oracle down / gate).
4. Orchestrator commits `.softhouse/` and pushes. Nothing else pushes.
5. Next fire runs `/softhouse-program`, which rebuilds everything from this file + `state/*.STATE.json` + `program.json` + the WIP branches.

## Pause reason

`fire 20260817-191707 exited rc=0 with the run mid-flight and no checkpoint (loop defect #1 above); state reconstructed by hand at 19:56`
