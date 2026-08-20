# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

> **THIS IS AN INTERIM CHECKPOINT, WRITTEN AT DISPATCH, NOT AT EXIT.** It exists so that a fire killed
> mid-flight leaves a truthful manifest instead of a stale one. If you are reading this and the fire's
> exit section below still says "IN FLIGHT", the fire did not complete its exit protocol: go to
> **"If this fire died"** at the bottom and rescue the branches before doing anything else.

## Current state (local fire `20260820-200002`, oracle REACHABLE)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0
- **Contexts**: 0 done / 17 · `tier0-harness-schedule-poc` **active**
- **Oracle**: UP at entry, `https://localhost:8443/fineract-provider/actuator/health` → `{"status":"UP"}`.
  Pinned checkout `426a23544` clean at entry. PostgreSQL only; no prohibited-engine port open.
- **Entry state**: main `83ceb79`, tree clean, 42 parity vectors / 5576 graded cells, conformance PASS
  re-verified by the previous fire on merged main.

## Dispatched this fire — FIVE workers, all isolated worktrees, all opus

| task | branch | oracle? | what it is |
|---|---|---|---|
| **T79** | `softhouse/T79-review-t78` | no | INDEPENDENT review of T78 — attack whether the CLOSED FORM closes |
| **T83** | `softhouse/T83-nonamortizing-boundary` | **yes** (in-JVM seam) | Measure the **G-8** non-amortizing boundary — the fire's highest-value work |
| **T80** | `softhouse/T80-pathb-recipe-hardening` | **yes** (REST, tenant `gerege`) | Retry of T76 — reachable abort, non-tautological canary |
| **T81** | `softhouse/T81-conformance-shell-guard` | yes (harness) | Stop a `sh` typo masquerading as exit-2 "oracle unusable" |
| **T82** | `softhouse/T82-pass3i-defects` | no | T75's seven defects — two are guards that cannot go red |

Paired reviewers **T84 (of T83), T85 (of T80), T86 (of T81), T87 (of T82)** are registered in
`tasks.json` as `pending` and dispatch in wave 2 as each worker lands. T79 *is* the reviewer of T78.
`T15` (archive) now depends on `T14, T71, T73, T75, T77, T79, T84, T85, T86, T87`.

**Oracle non-collision, instructed to every worker:** T83 uses the in-JVM Path A seam (no server, no DB);
T80 owns the REST/tenant side; nobody restarts, rebuilds, `docker compose down`s or re-seeds the
containers. T82 stays out of `capture/pathb/` and `capture/t83-nonamortizing/` entirely.

## STANDING INSTRUCTIONS still in force

- **Invoke the harness as `bash .softhouse/conformance.sh`, NEVER `sh`.** Under `sh` it dies at line 104 on
  process substitution and exits **2** — the harness's "oracle unusable" code and this driver's third stop
  condition. A shell-selection typo currently masquerades as a legitimate oracle-down park. **T81 is
  closing this gap this fire**; the instruction lapses only when T81 is merged and T86 has approved it.
- **Never `gofmt -w` `contract.go`** (gate G-3, CLOSED-Option A). `gofmt -l` naming *exactly* that one file
  is the EXPECTED state and must not fail a UAT.
- **A `parked` list inside a task note is evidence of what was true when it was written, not a work queue**
  (P-17). Check whether a later commit already closed the items before dispatching against it.

## Open gates — none of them blocks work today

- **G-4** (OPEN, ENGINEERING) — DEC-1's ACT/ACT promotion condition is provably too strong; wording-only fix.
- **G-5** (OPEN, ENGINEERING) — DEC-1 contradicts itself on a zero interest rate; wording-only fix.
- **G-8** (OPEN, ENGINEERING to measure) — the non-amortizing region. **T83 is measuring it this fire.**

G-4 and G-5 each propose amending a **ratified** DEC-1. This driver does **not** cross that: the skill's
never-cross list names *any change to a ratified DEC-n or the frozen adapter contract*, and it is the
stricter of the two readings in play. Both corrected readings are already operationally in force, so
neither gate blocks anything — only DEC-1's own sentence is outstanding. **Buyan decides.**

## If this fire died mid-flight — rescue procedure

A background worker is a child of the orchestrator session and **dies when the session ends**. If the exit
report below is absent, assume up to five worktrees hold uncommitted work:

1. `git branch -a | grep -E 'softhouse/T(79|80|81|82|83)-'` — a branch that exists with commits is safe.
2. For each of the five with **no** branch or **no** commit: find its worktree under
   `.claude/worktrees/`, commit whatever is there to `softhouse/<taskid>-<slug>`, and mark the task
   `needs_retry` with `note: worker killed mid-flight; rescued WIP on <branch>, completeness unverified`.
   **Do not leave it `in_progress`** — that tells the next fire work is happening when nothing is.
3. Only then plan new work.

## Exit report

**IN FLIGHT** — this section is rewritten at exit with what actually landed.
