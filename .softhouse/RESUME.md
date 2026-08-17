# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's session state.

## Current state

- **Program**: `fineract-to-go-full-codebase` — active
- **Driver**: `/softhouse-program` — fires daily at **08:00 Asia/Ulaanbaatar** (cron `0 0 * * *` UTC) as cloud routine [`trig_01J7a66YFD7mzSLiKiFsj5XV`](https://claude.ai/code/routines/trig_01J7a66YFD7mzSLiKiFsj5XV); also runnable by hand any time
- **Oracle reachability**: cloud fires cannot see a Fineract oracle on Buyan's machine — vector/conformance tasks park `oracle_unreachable` there and advance on a local fire (or once the oracle is deployed at a reachable address)
- **Program state**: `.softhouse/program.json` (authoritative context list, tiers, per-context status)
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — planned, not yet executed
- **Active squads**: none (no worker has started)
- **Next action**: `/softhouse-program` → no active work → resumes run 1 at task **T1** (stand up + pin the Fineract oracle)
- **Blocked on**: nothing yet. T6 (ratify DEC-1) is the first `user` gate.

## Checkpoint protocol (what a real pause looks like here)

1. Every active worker commits WIP to its `softhouse/<taskid>-<slug>` branch.
2. Each squad writes `.softhouse/state/<squad>.STATE.json` — current item, step, branch, next action, blocked_on, open questions, gate_pending.
3. The orchestrator rewrites this file: active squads, their next steps, and the reason for the pause (token soft limit / quota error / oracle down / gate).
4. Orchestrator commits `.softhouse/` and pushes. Nothing else pushes.
5. Next scheduled fire runs `/softhouse-program`, which rebuilds everything from this file + `state/*.STATE.json` + `program.json` + the WIP branches.

## Pause reason

`none — awaiting first execution`
