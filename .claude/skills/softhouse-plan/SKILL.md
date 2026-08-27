---
name: softhouse-plan
description: Planning-only phase of the Gerege NBFI migration pipeline — breaks a Fineract→Go migration change into a reviewable task graph with executor routing, paired independent reviewers, golden-vector test tasks, and dependencies, writes it to .softhouse/tasks.json, and stops. Never spawns worker agents or edits code. Use when the user runs /softhouse-plan or wants to review a plan before executing it with /softhouse resume.
---

# /softhouse-plan — plan only (Gerege NBFI variant)

**Project-scoped; overrides any global `softhouse-plan` inside this repository.** Planning rules are IDENTICAL to this project's `/softhouse` STEP 2 — a plan written here must execute unmodified under `/softhouse resume`. This command never spawns workers and never edits code or contracts. It only reads.

## Usage
- `/softhouse-plan <requirement>` — generate a task plan

## STEP 0 — Pre-flight
1. `git status` — abort if dirty.
2. Read `CLAUDE.md` — migration non-negotiables and Minimum Portable Core scope. Planning without it produces scope-wrong tasks.
3. Read `.softhouse/patterns.md`.
4. Read `.softhouse/tasks.json`. If a run is in progress, warn. If the previous run is terminal, archive it to `.softhouse/runs/` before replacing.
5. Read the newest `.softhouse/runs/*.json` and pull its `backlog` into planning input.
6. Environment facts are fixed — do not re-derive: Fineract is the oracle/fallback; the frozen adapter contract is the boundary; schema-first shared DB; only the orchestrator pushes.

## STEP 1 — Mode
Always plans. If a run is in progress, ask whether to replace or abort.

## STEP 2 — Plan

Schema (identical to `/softhouse`):

```json
{
  "id": "T1",
  "title": "Short title",
  "description": "What to change, in which package, and which golden vectors are the acceptance criteria",
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

**Roles — active:** `analyst` (extract Fineract behavior + vector list, cite source), `spec_writer` (design/ADR/contract docs), `coder` (port Go), `test_writer` (golden vectors + invariants), `reviewer` (independent adversarial, re-derives money math, `opus`), `verifier` (runs `/softhouse-uat`).

**Roles — inactive:** `designer`, `cx_reviewer`. Do not plan these.

**Executor routing:**
- `"agent"` — repo-contained code/test/doc work. Default.
- `"orchestrator"` — any git op, any push, running/refreshing the Fineract oracle, capturing vectors, budget, token-limit checkpoint/resume.
- `"user"` — **any context CUTOVER, any change to a ratified DEC-n or the frozen contract, regulatory acceptance / parallel-run sign-off.**

**Rules:**
- Overlapping `files_hint` **must** be serialised via `dependencies`.
- **Every `coder`/`analyst` task gets a paired `reviewer` task depending on it.** Not optional.
- **Every ported context has a `test_writer` (golden vectors) task that its `coder` task depends on.**
- **Never plan a CUTOVER as `agent`** — it is `executor: "user"`, gated on vectors + clean shadow window + sign-off.
- **Never plan work outside the Minimum Portable Core** (GL, loan+schedule, charges/rates/tax, COB, provisioning). Savings/deposits, working-capital, investor, branch → surface a `user` task instead.
- Apply `.softhouse/patterns.md`.
- `model`: `coder`/`analyst`/`spec_writer` → `sonnet`; `reviewer` → `opus`; `haiku` for mechanical edits; **`opus` for ledger mechanics, interest/schedule math, rounding, or a ratified DEC-n.**

**Scale check before you finalise:** a task whose `files_hint` spans a whole large context (e.g. all of loan) will exhaust its worker's context. Split by package or by sub-behavior (schedule generation vs repayment vs penalties).

## After planning
1. Write `.softhouse/tasks.json` with `run_id`, `feature`, `requirement`, `status: "planning"`, `backlog: []`, `tasks`.
2. Print the table: `| ID | Title | Role | Executor | Model | Context | Deps | Files |`.
3. Show the dependency/parallelism structure, and call out every `orchestrator` and `user` task — the `user` ones (cutovers, contract/DEC changes, regulatory sign-off) are decision gates that block their dependents.
4. Commit `.softhouse/tasks.json` and push.

## Output
> Plan saved to `.softhouse/tasks.json`. Review the task graph above.
> To execute: `/softhouse resume`
> To re-plan: `/softhouse-plan <updated requirement>`

## Notes
- Never spawns workers; never edits code or the contract.
- Safe to re-run — each run replaces the previous plan; prior runs live in `.softhouse/runs/` and git history.
