# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's session state.

## Current state

- **Program**: `fineract-to-go-full-codebase` — active
- **Driver**: `/softhouse-program`, fired three ways over the same repo state, serialised by `.softhouse/LOCK`:
  - **Primary — local launchd** `mn.gerege.nbfi.softhouse-program` → `.softhouse/bin/fire-program.sh`, **08:00 and 14:00 Asia/Ulaanbaatar**. Reaches the Fineract reference oracle + PostgreSQL on localhost, so this is the only fire that can capture vectors or run conformance. Logs: `~/Library/Logs/gerege-nbfi/fire-*.log`.
  - **Catch-up — cloud routine** [`trig_01J7a66YFD7mzSLiKiFsj5XV`](https://claude.ai/code/routines/trig_01J7a66YFD7mzSLiKiFsj5XV), **20:00 Asia/Ulaanbaatar**. No oracle access: source analysis, specs, Tier-C gap audit, Tier-D mining only.
  - **By hand** — `/softhouse-program` any time.
- **Database**: **PostgreSQL only**, everywhere. Oracle Database / MySQL / MariaDB prohibited. "The oracle" = the Fineract reference implementation (`.softhouse/reference-oracle.md`), never Oracle Database.
- **Current environment probe** (17 Aug 2026, 19:11 local): PostgreSQL **not** running on `localhost:5432`, Fineract reference oracle **not** running on `:8443`. Both are stood up by run 1 task **T1** — until then even local fires park vector work.
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
