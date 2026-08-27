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
0. **Take the lock — and read the RIGHT freshness signal.** The lock lives at `.softhouse/LOCK`. If it is
   held and live and not yours, print it and **exit** — never run two orchestrators over one repo. Otherwise
   write it (`holder`, `host`, `pid`, `started_at`, `heartbeat`) and delete it before you finish. The local
   wrapper does this for you and pushes it; a hand-run must honour it too.

   **`started_at` IS NOT A FRESHNESS SIGNAL, AND READING IT AS ONE HAS ALREADY CAUSED A DOUBLE-HOLDER
   INCIDENT** (2026-08-22, P-85). A timestamp stamped once at fire start cannot distinguish *"the holder died
   five hours ago"* from *"the holder has been working for five hours."* Raising the 6 h threshold trades one
   failure for the other; it does not fix it. On that day a local fire opened a **second session that reused
   the same fire id and the same `started_at`**, so a live holder wore a six-hour-old timestamp, a cloud fire
   correctly applied the rule as written, and four worker branches were killed with its sandbox.

   **THE AUTHORITATIVE FRESHNESS SIGNAL IS THE HOLDER'S MOST RECENT PUSH TO `origin/main`:**

   ```
   git fetch origin
   git log -1 --format=%ct origin/main        # seconds since epoch of the newest published commit
   ```

   **Why this and not a heartbeat field:** a heartbeat is a thing somebody must remember to refresh, and this
   program has recorded the same lesson five times over — `manifest.py verify`, `t44_float_roundtrip_v3`,
   T173's float guard, `guard_ledger_invariants` — **a guard that only works when someone remembers to run it
   enforces nothing** (P-45). Push recency is *derived from doing the work*, not maintained beside it, so it
   cannot silently fall behind the truth. The 2026-08-22 incident is exactly this: the holder **did** commit
   its lock refresh, its dispatch record and its in-flight manifest (`5f27983`, `ba2d8ed`, `d6dd8d0`) — and
   **never pushed them**, so the only evidence the other orchestrator could read said the opposite of the
   truth. A `heartbeat` field would have been in those same unpushed commits and would have changed nothing.

   **The test, in order:**
   1. `released_at` is non-null → **free**. Take it.
   2. `origin/main`'s newest commit is under 6 h old **and** `released_at` is null → **HELD, WHATEVER
      `started_at` SAYS.** Print it and exit. A holder that is pushing is a holder that is alive.
   3. Both `started_at` and the newest `origin/main` commit are over 6 h old → **stale**. Take it over, and
      say in your first commit message which signal you used and what it read.
   4. The lock names a `pid` on **this** host and that pid is gone → **dead holder**, take over immediately
      regardless of age. (The local wrapper already does this; it is why a hard-killed local fire does not
      cost the next fire six hours.)

   **`heartbeat` is written and refreshed as well** — cheap, and it disambiguates a fire that is thinking
   hard between pushes — but it is corroboration, never the primary. **If `heartbeat` and push-recency
   disagree, believe push-recency**, because the field can be stale for the same reason the incident
   happened.

   **AND THE OBLIGATION THAT ACTUALLY PREVENTS THIS (P-85), which no lock design can substitute for: push
   your lock, your dispatch record and your in-flight `RESUME.md` BEFORE you spawn the first worker.** A
   `HEAD` that says *"closed clean, zero live workers"* while five are running is an **active lie to the next
   orchestrator**, and no freshness rule can read through it.
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
| No active run, no READY context, but ≥1 **READY-FOR-ANALYSIS** context | Plan and run its **contract-independent slice** (analysis / corpus mining / raw capture / Tier-C gap audit). Keep going while the gate waits. |
| No active run, no READY context, no contract-independent work left anywhere, ≥1 blocked on a `user` gate | STEP 5 — surface the gates and exit. This is the only legitimate idle stop, and it now means *every* non-gated task in the program is genuinely exhausted. |
| No active run, every context `done` | Set `program.status = "complete"`, final report, exit. |
| No active run, remaining contexts all `parked` | Print each park reason with its retry precondition and exit. |

**READY** = `status == "pending"` AND every `dependencies` entry is `done` AND it is not blocked by a pending `user` gate of its own.

> **Resolve dependencies against the ARCHIVES too — `tasks.json` is not the whole graph.** Completed tasks
> are archived into `.softhouse/runs/<run-id>.tasks.json` and **dropped** from the current `tasks.json`, so
> an edge pointing into an earlier run resolves to *nothing* there. Read as "cannot ever resolve", that is a
> **permanent** false block. It happened: `T116` — the G-8 option (a) vector promotion, runnable under the
> **ratified** DEC-1 — was carried across several fires under the recorded claim that its dependency `T114`
> "has NO ENTRY in `tasks.json` and can never resolve", while `T114` sat `done` in the run-1 archive with its
> handoff and review both merged on `main`. When the resolver was finally written, **seven** edges pointed
> outside the current file and **all seven** resolved in the archive; none was missing. The program had
> meanwhile been reporting "no vector added for two fires" as though the cause were external. See **P-66**.
>
> **Use `python3 .softhouse/bin/ready-tasks.py`** rather than eyeballing `tasks.json`. It prints where every
> edge resolved (current file / which archive / genuinely nowhere), lists dispatched tasks separately, flags
> an `in_progress` task with no `branch` as a suspected isolation violation, and prints any **OPEN CONTRACT
> gate** beside the ready list — because *dependency-ready* and *permitted to run* are different questions.
> A task can be READY and still forbidden: while a context's DEC-n is unratified, no task may write Go under
> `nexus/` or store a **contract-shaped** vector for it. Raw observed capture stays permitted.
>
> **"Not found" is a statement about the search, never about the world.** Before recording that a
> dependency, file, vector or citation does not exist, state **where you looked**.

**READY-FOR-ANALYSIS** = `status == "pending"` AND its unmet dependencies are only `blocked_on_gate` (not `failed`, not `parked`) — meaning the blocker is a human decision, not missing work. A gate on a *contract* blocks work that **consumes** the contract; it does not block work that produces knowledge the contract decision will need anyway.

Runnable in this state (contract-independent):
- `analyst` — behaviour extraction from the pinned source, with citations.
- `test_writer` — mining the Fineract test corpus into a capture plan; capturing **raw observed** oracle output on an oracle-reaching fire.
- `spec_writer` — the Tier-C platform gap audit (what Nexus already provides).

Forbidden in this state — these are exactly what the gate is for:
- Any `coder` task, or anything writing under `nexus/`. No Go is written against an unratified contract.
- Storing captures in **contract-shaped** form (raw observed form only), since the shape is what is being ratified.
- Amending the gated DEC-n to unblock yourself.

Mark such tasks `"contract_independent": true` so the postmortem can show what advanced during a gate. **An open gate must never mean an idle factory** — it means the factory works on everything the gate does not touch.

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

### Worker isolation is not optional
Every `executor: "agent"` task is spawned **`isolation: "worktree"`**, with `model: task.model`, and commits its handoff to branch `softhouse/<taskid>-<slug>`. This is not ceremony — three later steps depend on the branch existing:
- the reviewer reads the upstream handoff from the branch (`git show <branch>:.softhouse/handoff/...`), which is what keeps it independent of the coder's working tree;
- the scope check is `git diff --stat main..<branch>` against `files_hint`;
- parallel workers would otherwise collide in one tree.

A worker spawned without a worktree, or given an absolute path into the main checkout, is an **isolation violation**. When you detect one (task `in_progress`/`done` with no `softhouse/<taskid>-*` branch):
1. Keep the output — do not discard finished work.
2. Record `isolation_violation` in the task `note` and in the postmortem; this is a process defect worth measuring.
3. If the task's `target` is `code` or `test`, **redo it in a proper worktree before review** — a money-path diff that never existed on a branch cannot be reviewed the way this pipeline requires.
4. If `target` is `docs`, the output may stand, but tell the reviewer explicitly that the handoff is on disk rather than on a branch, so "independent" still means re-deriving from source rather than reading the author's conclusions.

## STEP 4 — Never-halt policy (the point of this skill)

| Event | Program response |
|---|---|
| Task failed | One retry at `opus` (as `/softhouse`). Still failing → mark `parked`, mark dependents `blocked`, **continue with independent tasks in the same run**. |
| >50% of a run's tasks failed | Abort that run only. Park the context with reason `run_aborted`, and re-plan it next fire as smaller slices. The program stays active. |
| UAT red after retry | Park the context. Never `done`. Continue to the next READY context. |
| Merge conflict | Abort that merge, mark `conflict`, continue independent merges; the conflicted task is re-planned next fire. |
| **Oracle unreachable** — `conformance.sh` prints `probe = down` AND exits 2 | Conformance is exit 2, never PASS. Park all vector/conformance tasks. Then **keep working what does not need the oracle**: analyst behavior extraction, spec/ADR drafts, the Tier-C gap audit, Tier-D corpus mining from source. Retry the oracle next fire. |
| **Exit 2, probe line says `up`** | **NOT an oracle outage — park nothing.** Exit 2 also means *the corpus is unusable*: `ZERO VECTORS FOUND`, an inadmissible vector, or (since T110) a **duplicate `case_id`**. The oracle is fine and the fault is in the store. Treat it as a **task failure**, find the corpus defect, fix it, re-run. |
| **Exit 2 and NO probe line at all** | **NOT an oracle outage either — and this is the dangerous one.** Four exit-2 paths run *before* the probe is ever printed: no Go toolchain, `mktemp` failure, build failure, and **a failed HARD guard** (`run_guards` is called at `conformance.sh:281`; the probe prints at `:296`). So a `guard_no_float_in_vectors` failure — a **money non-negotiable** — exits 2 in silence, and "`probe != up`" is *trivially true when nothing printed*. Read the absence of the line, not the value. **Fix the harness or the violation; park nothing.** |
| **Conformance exited 3** | **NOT an oracle outage — do not park anything.** 3 is `conformance.sh`'s wrong-interpreter refusal: the harness never started, no vector was read, the oracle was never contacted. Something invoked it as `sh conformance.sh` (or `dash`/`zsh`/`bash --posix`) instead of `bash conformance.sh`. Fix the invocation and re-run. |
| Token soft limit reached | `/softhouse` checkpoint protocol: workers commit WIP, write `.softhouse/state/<squad>.STATE.json`, write `.softhouse/RESUME.md`, commit, push, exit cleanly. The scheduled fire resumes. |
| Quota/rate-limit error mid-flight | Same checkpoint path, immediately. Never leave a worktree uncommitted. |
| `user` gate reached | Record in `.softhouse/gates.md` + `program.gates_pending`, mark that context `blocked_on_gate`, **and move to the next READY context**. Do not cross it. Do not idle if other work exists. |

> **Read the probe line, never the exit code alone — and check it was printed at all.** When `conformance.sh`
> reaches its oracle check it prints `conformance: reference oracle (<url>) probe = up|down`, and *that* line,
> not the exit status, is what says whether the oracle was reachable. **It is not always reached.** The oracle-is-down stop condition
> is **`exit 2` AND a probe line that was actually PRINTED and reads `down`** — all three. Exit 2 alone is
> ambiguous, because the same code also carries "the corpus is unusable" and "the harness never started", and
> reading it as an outage is the exit-3 mistake reappearing one level up: a **refusal** mistaken for an
> **outage**, parking work that nothing is blocking.
>
> **The probe line is NOT printed unconditionally**, and the first version of this rule said it was — the
> driver's error, caught by T150 (F-T150-1) inside the very paragraph written to close this defect. Four exit-2
> paths precede it, and one of them is **a failed HARD guard**. So the rule as first written would have parked
> vector work as an *oracle outage* on a `guard_no_float_in_vectors` failure — a violation of the first
> non-negotiable in `CLAUDE.md`, silently reclassified as somebody else's server being down. **Test for the
> line's presence first, then its value.** Raised by T119 against this file while reviewing T110; corrected by
> T150 while reviewing T130.

A parked context is never abandoned: every fire re-evaluates parks and unparks any whose precondition now holds (oracle back up, dependency now `done`, conflict resolved).

## STEP 5 — Gates: answer what you can, escalate only what you cannot

Before treating a gate as a stop, **triage every item in it** (CLAUDE.md § Answering gates):

- **LEGAL** — settled by statute/regulation. Cite the article and apply it. Read `.softhouse/gates-proposed-answers.md` first; the deposit-taking position is already settled there.
- **ENGINEERING** — answerable from source, captured vectors, or design reasoning. Propose, record the reasoning, act.
- **RESERVED** — needs a business/licensing/regulatory fact no source can supply. Escalate **these only**.

A gate with no RESERVED items is not a stop. A gate with some RESERVED items still lets every non-reserved item proceed — and the rest of the program keeps running under READY-FOR-ANALYSIS.

Never dress a RESERVED item as ENGINEERING to keep moving. The test is simple: *could any amount of reading source, statute or vectors answer this?* If the answer depends on what Gerege intends to sell, which licence a deployment runs under, or what a regulator has accepted — it is RESERVED.

### Surfacing what remains
Append to `.softhouse/gates.md`, one block per gate: gate id, context, what was proven (conformance table, reviewer re-derivations), what is being asked, what unblocks it, and — for a cutover — the shadow-parity window status and the regulatory sign-off state. Then exit with a one-screen summary of what Buyan must decide.

**Gates that no automation may cross, ever:**
- Any context CUTOVER (needs vectors passing + clean shadow-parity window + regulatory/parallel-run sign-off).
- Any change to a ratified DEC-n or the frozen adapter contract.
- Regulatory acceptance / parallel-run sign-off (FRC, external audit).
- Deposit-taking ACTIVATION (FRC / Bank of Mongolia licensing). Porting savings code proceeds; enabling it does not.

## STEP 5.5 — Exit protocol (MANDATORY on every exit path)

Applies to **every** way this driver ends — success, soft limit, gate, park, error, or "nothing left I can do right now". A fire that ends without this has destroyed work, because the next fire is a fresh session that knows only what is committed.

Before returning, in this order:
1. **Commit every deliverable a worker produced.** An uncommitted file is invisible to the next fire and to the cloud fire. `git status --porcelain` must come back empty.
2. **Make `tasks.json` truthful** — no task left claiming `in_progress` without a `note` saying what actually landed and what has not. If a retry ran at a different model than planned, record it; the `model` field alone becomes stale and misleads the postmortem's cost accounting.
3. **Write `.softhouse/state/<squad>.STATE.json`** for every task not in a terminal state: current item, step, branch, next_action, blocked_on, open_questions, gate_pending.
4. **Rewrite `.softhouse/RESUME.md`** with the real task table, the concrete next action, and an honest `Pause reason`. Leaving a stale manifest is worse than leaving none — the next fire will act on it.
5. **Push.** Then print the report.

Exiting because you are *waiting* on something (a review to be re-run, a gate, a build) is still an exit: checkpoint it. "I'll pick this up in a moment" is not a state the next session can see.

### NEVER exit with live workers — they die with you

A background worker is a child of your session. When your turn ends, it is **killed**, and everything it had not committed is lost inside its worktree where the main-tree sweep cannot see it. This happened on 2026-08-18 at 17:22: the fire ended saying *"three workers are running in locked worktrees, none has committed yet"* and stranded 4,482 insertions — including the entire T4 DEC-1 retry.

Before ending a fire, for every worker you dispatched:

1. **Await it.** Do not end your turn while a dispatch is outstanding. "Holding capacity deliberately" is not a reason to exit — an unfinished worker is not paused, it is dead.
2. If you must stop (token soft limit, quota error), **first** make each worker commit its WIP to its `softhouse/<taskid>-<slug>` branch and write its `.softhouse/state/<squad>.STATE.json`, then verify each branch actually has a commit (`git -C <worktree> log --oneline main..HEAD`).
3. Only dispatch what you have the budget to see through. Dispatching three workers with 10 % of budget left destroys three workers' output.
4. A task whose worker you killed is **not** `in_progress` — mark it `needs_retry` with `note: worker killed mid-flight; rescued WIP on <branch>, completeness unverified`. Leaving it `in_progress` tells the next fire that work is happening when nothing is.

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
