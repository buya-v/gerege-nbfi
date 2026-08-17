---
name: softhouse
description: Gerege NBFI migration pipeline — plans a Fineract→Go migration change into a task graph, executes it with parallel isolated worktree agents, reviews every branch with an INDEPENDENT reviewer agent that re-derives money math, verifies against the golden-vector conformance harness (Fineract as oracle), then merges and records learned patterns. Token-limit aware: checkpoints and resumes on schedule. Use when the user runs /softhouse, asks to run the softhouse pipeline, or wants a migration change planned and executed end-to-end. "/softhouse resume" continues an interrupted run.
---

# /softhouse — Gerege NBFI migration pipeline (project variant)

**Project-scoped variant; overrides any global `softhouse` inside this repository.** The pipeline shape (9 steps, `tasks.json` schema, executor routing, resumability) is inherited from the Digital Coop Bank pipeline. What differs: **this project's deliverable is Go code that must reproduce Apache Fineract's behavior bit-for-bit**, verified against a golden-vector conformance harness with Fineract kept live as oracle and fallback.

Adaptations, and why each exists:

| Change | Reason |
|---|---|
| `coder` and `test_writer` roles are ACTIVE (they were inactive in the docs-only bank project) | This repo has real Go code to compile, port, and test. |
| UAT = `/softhouse-uat` → `go build`, `go test`, **golden-vector conformance vs the live Fineract oracle**, and property invariants | The deliverable is money-correct code, not documents. `verify-docs.sh` is replaced by the harness. |
| **Review re-derives money math; it does not read it** | Inherited hard lesson: a plausible-but-wrong ledger formula survived two adversarial reviews on the bank project. For any ledger/interest/rounding change, the reviewer re-computes. |
| Token-limit scheduler in STEP 3 | The migration is long. When the daily token budget is hit, the orchestrator checkpoints all workers and a scheduled task resumes them — see `docs/agent-squad-delivery-and-scheduler.md`. |
| No cutover without a `user` gate | Replacing a Fineract context with the Go module is a `user` decision, gated on parity + regulatory acceptance. |

## Usage
- `/softhouse <requirement>` — plan and execute a full run
- `/softhouse resume` — resume an interrupted run (or resume after a daily-token-limit checkpoint)

## STEP 0 — Pre-flight
1. `git status` — abort if the tree is dirty. **Exception:** on `resume`, a tree dirty *only* under `.softhouse/` is expected and does not abort.
2. Read `CLAUDE.md` — the migration non-negotiables (money integer minor units, append-only ledger, Fineract-as-oracle, Minimum Portable Core scope, Mongolia rules). Planning without it produces scope-wrong tasks.
3. Read `.softhouse/patterns.md` — learned patterns + grepable constraints.
4. Read `.softhouse/tasks.json`; read the newest `.softhouse/runs/*.json` and pull its `backlog` into planning input.
5. Environment facts (fixed — do not re-derive):
   - **Fineract runs as the ORACLE and FALLBACK.** The Go module under construction lives in the Nexus tree; every ported context is graded against Fineract's golden vectors before cutover.
   - **The frozen adapter contract is the boundary.** Callers talk to the contract; behind it is Fineract-JVM or the Go module, switchable per context by config. Workers never break the contract.
   - **Schema-first:** Fineract's PostgreSQL schema is adopted/pruned; a shared DB enables shadow/differential testing.
   - **Remote:** only the orchestrator pushes; workers commit to their branch.

## STEP 1 — Mode
`resume` → STEP 4. Otherwise treat the argument as the requirement → STEP 2.

## STEP 2 — Plan

Task schema:

```json
{
  "id": "T1",
  "title": "Short title",
  "description": "What to change, in which package, and the acceptance criteria (which vectors must pass)",
  "agent_role": "coder",
  "executor": "agent",
  "model": "sonnet",
  "target": "code",
  "files_hint": ["nexus/internal/apps/ledger/journal.go"],
  "context": "GL",
  "dependencies": [],
  "status": "pending",
  "attempts": 0,
  "note": ""
}
```

### Roles

**Active:**
- `analyst` — extracts the behavior of a Fineract context from its Java + tests and produces the spec + the golden-vector list the Go port must satisfy. Cites the exact Fineract source. Honesty rule applies.
- `spec_writer` — writes/updates design docs and ADRs (the frozen contract, schema decisions). Preserves IDs and cross-references.
- `coder` — ports/implements the Go module for a bounded context. Decimal money only, never float. Must not break the frozen adapter contract.
- `test_writer` — authors the golden-vector fixtures (captured from Fineract) and property-based invariant tests. Tests are owned separately from the coder.
- `reviewer` — **independent adversarial review, spawned fresh without planning context.** For any money path, RE-DERIVES the arithmetic. Default `model: "opus"`.
- `verifier` — runs `/softhouse-uat` (build, test, conformance vs oracle, invariants) and reports.

**Inactive until relevant:** `designer`, `cx_reviewer` (no end-user UI in the migration scope).

### Executor routing (safety boundary, not a label)

- `"agent"` — repo-contained code/test/doc work in an isolated worktree, verifiable by diff + harness. Default.
- `"orchestrator"` — any git operation, any push, running/refreshing the Fineract oracle, capturing golden vectors, spending budget, and **the token-limit checkpoint/resume**.
- `"user"` — decisions only the product owner / controller / regulatory liaison can make: **any context CUTOVER (switching a context from Fineract to the Go module), any change to a ratified DEC-n or the frozen contract, and regulatory acceptance / parallel-run sign-off.**

### Planning rules

- Overlapping `files_hint` **must** be serialised via `dependencies`. Two agents editing the same Go package concurrently produce contradictory state.
- **Every `coder` or `analyst` task gets a paired `reviewer` task that depends on it.** No money code lands unreviewed.
- **Every ported context gets a `test_writer` task (golden vectors) that a `coder` task depends on** — vectors before/with the port, never after as an afterthought.
- **Do not plan a CUTOVER as an `agent` task.** Cutover is `executor: "user"`, gated on: vectors pass + a clean shadow-parity window + human/regulatory sign-off.
- **Do not plan work outside the Minimum Portable Core** (GL, loan+schedule, charges/rates/tax, COB, provisioning). Savings/deposits (prohibited), working-capital, investor, branch are out of scope — surface a `user` task if a requirement seems to need them.
- `model`: `coder`/`analyst`/`spec_writer` → `sonnet`; `reviewer` → `opus`; `haiku` for mechanical edits (renames, formatting); **`opus` for anything touching ledger mechanics, interest/schedule math, rounding, or a ratified DEC-n.**

### The honesty rule (project non-negotiable)

Every worker prompt carries this, and review enforces it:

> State only what you verified. If you could not verify a Fineract behavior, a vector, or an arithmetic result, write that you could not — do not supply a plausible value to fill the gap. Mark each material claim `[VERIFIED: <fineract source / vector id>]` or `[UNVERIFIED]`. A confident invention in money code is the worst possible defect.

### After planning
1. Write `.softhouse/tasks.json` (`run_id`, `feature`, `requirement`, `status: "planning"`, `backlog: []`, `tasks: [...]`).
2. Print the task graph: `| ID | Title | Role | Executor | Model | Context | Deps | Files |`.
3. **Wait for approval** — "Approve this plan? (yes/edit/abort)".
4. On approval: commit `.softhouse/tasks.json` and push.

## STEP 3 — Execute

Process in dependency order, routed by `executor`. Orchestrator and user tasks run inline; agent tasks spawn workers.

**Before any batch:** commit and push main — workers fork from current main.

Spawn with the **Agent tool**, `isolation: "worktree"`, `model: task.model`. A retry (`attempts > 0`) upgrades to `opus`.

### Token-limit scheduler (orchestrator)
Meter cumulative tokens against the daily budget. When `tokens_used ≥ DAILY_SOFT_LIMIT` (≈90%) or a quota error returns:
1. Signal all active workers to checkpoint: commit WIP to their branch, write `.softhouse/state/<squad>.STATE.json` (current item, step, next action).
2. Write `.softhouse/RESUME.md` (active squads + next steps).
3. Stop cleanly. A scheduled task fires at the quota-reset time and runs `/softhouse resume`, which rebuilds all state from the repo. See `docs/agent-squad-delivery-and-scheduler.md`.

**Every worker prompt begins with:**

> CONTEXT — Fineract → Go native migration into Gerege Nexus.
> - Fineract is the ORACLE. Your Go output is correct only when its golden vectors match Fineract's captured outputs to the defined rounding. Do not assert correctness; prove it against vectors.
> - Money is integer minor units — NEVER float/double/decimal-float in any path, including intermediate calculation. The ledger is append-only; balances are derived; holds affect available only; money-movement POSTs carry an Idempotency-Key.
> - Do NOT break the frozen adapter contract. If your change requires a contract change, STOP and report — that is a `user` task.
> - Do NOT `git push` from a worktree. Commit to branch `softhouse/<taskid>-<slug>` only; the orchestrator pushes.
> - You are in an ISOLATED GIT WORKTREE forked from current main. Never touch main.
> - Read `CLAUDE.md` and `.softhouse/patterns.md` first — their non-negotiables are graded in review; violating one is a rejection.
> - Write your handoff to `.softhouse/handoff/{run_id}/{task.id}.md` **and commit it to your branch**. The reviewer runs in a DIFFERENT worktree and reads your handoff from git; a branch with no commit is treated as unchanged and its worktree is pruned — your output is destroyed.
> - {the honesty rule, verbatim}

**`coder` additionally receives:**
> - Edit only the packages in `files_hint`. Keep the adapter contract stable.
> - Run `go build ./...` and the relevant golden-vector + property tests before finishing; they must pass. If a vector cannot pass, report the diff — do not weaken the test.
> - Handoff sections: `## Changes Made` / `## Vectors run (pass/fail)` / `## Money-math notes` / `## Unverified` / `## Blockers` / `## Follow-ups`.

**`test_writer` additionally receives:**
> - Capture golden vectors from the Fineract oracle for the assigned context; do not hand-author expected values you did not observe from Fineract. Add property invariants (double-entry balances; principal amortizes to zero; splits sum to whole).

**`reviewer` agents receive** (spawned fresh — do NOT pass the planning rationale):
> You are an INDEPENDENT reviewer. You did not plan this work; assume defects exist, especially in money math.
> - Read `CLAUDE.md` and `.softhouse/patterns.md` from your own worktree.
> - Read the upstream handoff from the BRANCH, not disk: `git show <branch>:.softhouse/handoff/{run_id}/{dep_task.id}.md`.
> - Read the diff with `git diff main...<branch>` (three dots).
> - **RE-DERIVE every money computation the change touches** — schedules, postings, rounding at each step, hold/available. Do not accept the coder's arithmetic; recompute it and compare to the Fineract vector. A plausible formula that is wrong is the exact failure this role exists to catch.
> - Check: (1) every non-negotiable in CLAUDE.md/patterns.md (no float, append-only, derived balances, idempotency); (2) the frozen contract is intact; (3) every `[VERIFIED]` claim traces to real Fineract source/vector; (4) golden vectors actually pass and are non-vacuous; (5) no ratified DEC-n silently changed.
> - Verdict: APPROVED / MICRO-FIX (≤10 lines, mechanical only — never a number, never money logic) / REJECTED with specifics.
> - If you find nothing, state what you checked, so silence is distinguishable from not looking.

## STEP 4 — Resume
Read `tasks.json`; find tasks not `done`/`approved`; read `.softhouse/RESUME.md` and `.softhouse/state/*.STATE.json` and each partial handoff; resume at the earliest incomplete dependency level. This is the same path used after a token-limit checkpoint.

## STEP 5 — Review
1. **Scope check** — `git diff --stat main..<branch>` vs `files_hint`.
2. **Fork-freshness** — `git merge-base main <branch>`; if behind, scrutinise co-edited packages.
3. **Read the independent reviewer's handoff and adjudicate it** — for a money-math conflict, RE-DERIVE from source yourself; never settle it by majority vote.
4. **Non-negotiables grep** against `CLAUDE.md` and `patterns.md` (float in money paths, direct balance writes, missing idempotency key).
5. Verdict: APPROVED / MICRO-FIX (mechanical only) / REJECTED (one retry, model → opus, reviewer notes injected).

## STEP 5.5 — Verification
Run `/softhouse-uat` against merged state: `go build ./...`, `go test ./...`, the **golden-vector conformance run vs the Fineract oracle**, and property invariants. Gate: must PASS before the run completes. Failure marks the responsible task `uat_failed` — one retry, model → opus.

## STEP 6 — Merge
`git merge --no-ff <branch>` in dependency order. On conflict: abort that merge, mark `conflict`, continue with independent tasks. Re-run the verifier and push after each merge batch.

## STEP 7 — Integration
Run `/softhouse-uat` on final merged main. Re-run the full conformance suite for any context whose package another merged task touched — cross-context ledger interactions are the characteristic failure.

## STEP 8 — PostMortem
Append between the markers in `.softhouse/patterns.md`:

```markdown
### Run {run_id} — {feature} ({date})
- **What worked**:
- **What the independent reviewer caught** (measure it — especially re-derived money-math catches):
- **Vectors added / contexts at parity**:
- **Claims marked UNVERIFIED** (carried forward as open questions):
- **New knowledge**:
- **Verifier**: build · test N · conformance pass/fail · invariants
- **Backlog carried forward**:
```

## STEP 9 — Cleanup
1. Archive `tasks.json` → `.softhouse/runs/{run_id}.json` (preserves `backlog`).
2. Reset `tasks.json` to idle; clear `.softhouse/state/` and `RESUME.md`.
3. Worktree/branch hygiene: `git worktree remove` + `prune`; delete merged `softhouse/*` branches; list unmerged ones.
4. Commit `.softhouse/` and push.
5. Report: tasks by executor, reviewer findings, verifier state, contexts at parity, backlog, patterns learned.

## STEP 10 — Program continuation (do not stop at the run boundary)
If `.softhouse/program.json` exists and `status == "active"`:
1. Mark this run's context `done` (or `parked`, if UAT ended red after its retry — never `done` on red), set `run_id`, append the run to `program.history`.
2. Advance `cursor` and **immediately hand control to `/softhouse-program`**, which plans and starts the next READY context in the same session if budget remains. Reaching the end of a run is not a reason to idle.
3. If the token soft limit was hit, do the checkpoint protocol instead and stop cleanly — the scheduled fire calls `/softhouse-program`, which resumes.
4. A pending `user` gate parks that context only. Move to the next READY context; never cross the gate.

Without a `program.json`, a completed run still ends here.

## Error handling
- Catastrophic agent failure → mark `failed`, continue independent tasks, **mark every dependent task `blocked`** with the blocking id in `note`.
- >50% of tasks failed → abort and report.
- All state in `.softhouse/`; any interruption (including a daily-token-limit checkpoint) resumes with `/softhouse resume`.
