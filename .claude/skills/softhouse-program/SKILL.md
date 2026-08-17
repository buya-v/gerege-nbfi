---
name: softhouse-program
description: Program driver above /softhouse for the Gerege NBFI Fineract→Go migration — keeps the migration advancing across run boundaries until every context in .softhouse/program.json is done. Plans the next context the moment a run goes terminal, resumes after a token-limit checkpoint, parks blocked contexts instead of halting, and never crosses a user gate. Use when the user runs /softhouse-program, when a scheduled task fires to continue the migration, or when asked to keep the migration running unattended.
---

# /softhouse-program — the never-stops driver

**Project-scoped.** `/softhouse` executes ONE bounded context and stops. This driver sits above it and decides what happens next, so the migration advances continuously — across run boundaries, across daily token limits, and across blocked contexts — until `.softhouse/program.json` has no `pending` context left.

It changes **nothing** about correctness: every gate, every reviewer, every vector in `/softhouse` still applies. What it removes is the *idle stop*, not a check.

## Usage
- `/softhouse-program` — do the next right thing and keep going until a stop condition
- `/softhouse-program status` — print program state and exit (no work dispatched)
- `/softhouse-program park <context-id> <reason>` — park a context by hand
- `/softhouse-program unpark <context-id>` — return a parked context to `pending`

## Fires — who runs this driver

| Fire | When | Reaches the reference oracle? | Role |
|---|---|---|---|
| **Local launchd** `mn.gerege.nbfi.softhouse-program` → `.softhouse/bin/fire-program.sh` | 08:00 and 14:00 Asia/Ulaanbaatar | **Yes** — Fineract + PostgreSQL on localhost | **Primary.** The only fire that can capture vectors or run conformance. |
| **Cloud routine** `trig_01J7a66YFD7mzSLiKiFsj5XV` | 20:00 Asia/Ulaanbaatar (12:00 UTC) | No | Catch-up: source analysis, specs, Tier-C gap audit, Tier-D mining when the Mac was off. |
| **By hand** `/softhouse-program` | any time | depends where you run it | Same driver, same state. |

Logs: `~/Library/Logs/gerege-nbfi/fire-*.log`. Probe the environment without running anything: `.softhouse/bin/fire-program.sh --probe`.

## STEP 0 — Pre-flight (read, never assume)
0. **Take the lock.** Read `.softhouse/LOCK`. If it exists and `started_at` is under 6 h old and it is not yours, print it and **exit** — never run two orchestrators over one repo. Otherwise write it (`holder`, `host`, `pid`, `started_at`) and delete it before you finish. The local wrapper does this for you and pushes it so the cloud fire sees it; a hand-run must honour it too.
1. `git status` — if dirty, commit `.softhouse/` state only; never stash worker WIP.
2. `git pull --ff-only` — a scheduled fire may be a fresh clone/session; the repo is the only memory.
3. Read `CLAUDE.md`, `.softhouse/patterns.md`, `.softhouse/program.json`, `.softhouse/tasks.json`, `.softhouse/RESUME.md`, `.softhouse/state/*.STATE.json`, `.softhouse/gates.md`, newest `.softhouse/runs/*.json`.
4. Determine the token budget for this fire and the soft limit (`policy.daily_soft_limit_pct`).

## STEP 1 — Decision table (evaluate in order, take the first match)

| State | Action |
|---|---|
| `program.status == "complete"` | Print the final report and exit. |
| A run is active and **not** terminal | `/softhouse resume`. This covers both an interrupted run and a token-limit checkpoint. |
| A run is active and terminal (all tasks `done`/`approved`/`parked`, UAT PASS) | Close it: STEP 8/9 of `/softhouse` (postmortem → archive → cleanup), set that context `done`, append to `program.history`, then **fall through to the next row in the same fire** — do not stop to be asked. |
| A run is active and terminal but UAT FAILED after its retry | Park the context with the verifier output, then fall through. Never mark a red UAT `done`. |
| No active run, and ≥1 context is READY | Plan it (STEP 2), then execute it (STEP 3). |
| No active run, no READY context, ≥1 blocked on a `user` gate | STEP 5 — surface the gates and exit. This is the only legitimate idle stop. |
| No active run, every context `done` | Set `program.status = "complete"`, final report, exit. |
| No active run, remaining contexts all `parked` | Print each park reason with its retry precondition and exit. |

**READY** = `status == "pending"` AND every `dependencies` entry is `done` AND it is not blocked by a pending `user` gate of its own.

**Context selection among several READY:** lowest tier first; within a tier, the one unblocking the most dependents; tie-break on smaller `main_loc` (get a parity win banked before a monster).

## STEP 2 — Plan the next context
Build the `/softhouse-plan` requirement from the context entry — do not invent scope:

> Port `{title}` to Go behind the ratified frozen adapter contract, harness-graded, reusing the conformance harness and vector store. IN SCOPE for this run only: `{fineract_paths}` → `{go_target}`. `test_writer` mines this context's slice of the Fineract test corpus and captures golden vectors from the pinned oracle; `coder` implements against them; a paired INDEPENDENT reviewer RE-DERIVES every money computation against the vectors, not the code. Verify with `/softhouse-uat`: build + tests + this context's conformance vectors + property invariants. SCOPE GUARD: nothing outside `fineract_paths`; record anything discovered elsewhere to backlog. Cutover is a separate `user` gate — do not plan it. `{context.notes}`

**Splitting is mandatory when the context is large.** If `main_loc > 25000` or `files_hint` would span a whole module, split into sub-slices by sub-behavior and plan only the first; append the rest to the context's `slices` array with `status: "pending"`. The context is `done` only when every slice is. `tierA-loan-lifecycle` (106k LOC), `tierB-savings-deposits` (62k), `tierB-working-capital-loan` (34k) and `tierC-platform-map-first` (180k) will always need this.

**Plan gate — auto-approve only if ALL hold** (else park the context and record which check failed):
1. Every `coder`/`analyst` task has a paired `reviewer` depending on it.
2. The context has a `test_writer` (golden vector) task that its `coder` depends on.
3. No task with `executor: "agent"` performs a cutover, a contract change, or a DEC-n amendment.
4. Every `files_hint` path is inside `go_target`, `.softhouse/`, or `docs/`.
5. No task's `files_hint` spans a whole large module (worker-context blowout).
6. `model` routing is right: `reviewer` → `opus`; ledger/interest/schedule/rounding work → `opus`.
7. Overlapping `files_hint` are serialised via `dependencies`.

Auto-approval replaces the human "approve this plan?" prompt in `/softhouse` STEP 2 **only in program mode**, and only against this checklist. It never auto-approves a `user` task's *decision* — those still block.

## STEP 3 — Execute
Run `/softhouse resume` against the fresh plan. All of `/softhouse` STEP 3–9 applies unchanged: worktree-isolated workers, the verbatim worker prompt, independent re-deriving reviewers, conformance gate, merge, postmortem.

## STEP 4 — Never-halt policy (the point of this skill)

| Event | Program response |
|---|---|
| Task failed | One retry at `opus` (as `/softhouse`). Still failing → mark `parked`, mark dependents `blocked`, **continue with independent tasks in the same run**. |
| >50% of a run's tasks failed | Abort that run only. Park the context with reason `run_aborted`, and re-plan it next fire as smaller slices. The program stays active. |
| UAT red after retry | Park the context. Never `done`. Continue to the next READY context. |
| Merge conflict | Abort that merge, mark `conflict`, continue independent merges; the conflicted task is re-planned next fire. |
| **Oracle unreachable** | Conformance is exit 2, never PASS. Park all vector/conformance tasks. Then **keep working what does not need the oracle**: analyst behavior extraction, spec/ADR drafts, the Tier-C gap audit, Tier-D corpus mining from source. Retry the oracle next fire. |
| Token soft limit reached | `/softhouse` checkpoint protocol: workers commit WIP, write `.softhouse/state/<squad>.STATE.json`, write `.softhouse/RESUME.md`, commit, push, exit cleanly. The scheduled fire resumes. |
| Quota/rate-limit error mid-flight | Same checkpoint path, immediately. Never leave a worktree uncommitted. |
| `user` gate reached | Record in `.softhouse/gates.md` + `program.gates_pending`, mark that context `blocked_on_gate`, **and move to the next READY context**. Do not cross it. Do not idle if other work exists. |

A parked context is never abandoned: every fire re-evaluates parks and unparks any whose precondition now holds (oracle back up, dependency now `done`, conflict resolved).

## STEP 5 — Gates: surface, then wait (only if nothing else is runnable)
Append to `.softhouse/gates.md`, one block per gate: gate id, context, what was proven (conformance table, reviewer re-derivations), what is being asked, what unblocks it, and — for a cutover — the shadow-parity window status and the regulatory sign-off state. Then exit with a one-screen summary of what Buyan must decide.

**Gates that no automation may cross, ever:**
- Any context CUTOVER (needs vectors passing + clean shadow-parity window + regulatory/parallel-run sign-off).
- Any change to a ratified DEC-n or the frozen adapter contract.
- Regulatory acceptance / parallel-run sign-off (FRC, external audit).
- Deposit-taking ACTIVATION (FRC / Bank of Mongolia licensing). Porting savings code proceeds; enabling it does not.

## STEP 6 — Persist and push (every fire, even a no-op)
1. Update `.softhouse/program.json`: `cursor`, per-context `status`/`run_id`/`slices`, `gates_pending`, `history` (one entry per closed run: run id, context, tasks, reviewer catches, UAT result, tokens spent).
2. Commit `.softhouse/` and push. Only the orchestrator pushes.
3. Print: what this fire did, program progress (`contexts done / total`, LOC ported / LOC total), what the next fire will pick up, and every pending gate.

## Invariants this driver may never relax
- **PostgreSQL is the only database** — reference oracle, Go module, vector capture, shadow runs, CI. Postgres compose profile only. Oracle Database / MySQL / MariaDB are prohibited (`ojdbc`, `oracle.jdbc`, `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver/mysql` are grep rejections); Go uses `pgx`; money columns are `bigint` minor units. Shadow parity across two different engines is not parity.
- **"The oracle" = the Fineract reference implementation** (`.softhouse/reference-oracle.md`), never Oracle Database. Use "reference oracle (Fineract)" in tasks and prompts.
- Fineract stays the reference oracle and fallback; no context is correct until its vectors match.
- The reviewer **re-derives** money math; a money conflict is settled by re-derivation from source, never by vote.
- Integer minor units, append-only ledger, derived balances, holds→available only, `Idempotency-Key` on money-movement POSTs.
- One bounded context per run; the per-run scope guard is unaffected by the program's full-codebase goal.
- A red conformance run, an unreachable oracle, or a pending `user` gate can pause work — they can never be reclassified as a pass to keep the loop moving. **Continuity is achieved by finding other work, never by lowering a bar.**
