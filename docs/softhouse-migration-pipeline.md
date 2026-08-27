# Softhouse Migration Pipeline — reuse spec

**Adapting the proven Digital Coop Bank `softhouse` pipeline to run the Fineract → Go native migration**

Project: gerege-nbfi · Prepared for: Buyan · Date: 13 August 2026

This document explains the agent-pipeline scaffold now seeded into this repo, what it borrows from the battle-tested `digital_coop_bank` system, and what was changed for a *code* migration. The runnable pieces are:

```
gerege-nbfi/
  CLAUDE.md                              # migration non-negotiables (graded in review)
  .claude/skills/softhouse/SKILL.md      # full 9-step pipeline (code variant)
  .claude/skills/softhouse-plan/SKILL.md # plan-only
  .claude/skills/softhouse-uat/SKILL.md  # verify: build + test + golden-vector conformance
  .softhouse/patterns.md                 # seeded constraints + learned-patterns log
  docs/agent-squad-delivery-and-scheduler.md  # the token-limit scheduler
```

## 1. Why reuse rather than reinvent

`digital_coop_bank` already runs a mature multi-agent "softhouse": ~30 dated runs, a 9-step plan→execute→review→verify→merge→learn pipeline, independent adversarial reviewers, an executor-routing safety model, a real learned-patterns loop, and full resumability. That machinery is exactly what the Fineract migration needs. Rebuilding it would waste the hard lessons already paid for — including the ones about money math that cost that project two review rounds. So this scaffold **ports the pipeline and re-points it at code**.

## 2. What was inherited unchanged

- **The 9-step shape** and the `tasks.json` task-graph schema.
- **Executor routing as a safety boundary** — `agent` (isolated worktree worker), `orchestrator` (git, push, budget, oracle, state), `user` (decisions only the owner/controller/regulator can make).
- **The independent adversarial reviewer**, spawned fresh without planning context, reading the upstream handoff from the branch (`git show <branch>:...`) and diffing against the merge base — because self-review already shipped defects on the sister project.
- **The honesty rule** — `[VERIFIED]` / `[UNVERIFIED]` tagging; a marked gap beats a confident invention.
- **`patterns.md` as the learning loop** — pre-flight reads it; each run's postmortem appends what worked and what the reviewer caught.
- **Resumability** — all state in `.softhouse/`; `/softhouse resume` rebuilds from the repo.
- **The money guardrails** — no float, append-only ledger, derived balances, holds-affect-available-only, idempotency keys — now grepped against Go diffs.

## 3. What changed for a code migration

| Aspect | Digital Coop Bank (docs) | Gerege NBFI (code migration) |
|---|---|---|
| Deliverable | Requirements documents | Go code that reproduces Fineract behavior |
| Active roles | `analyst`, `spec_writer`, `reviewer`, `verifier` | **+ `coder`, `test_writer`** (activated); `analyst` now extracts Fineract behavior + vectors |
| Verification | `verify-docs.sh` (HARD/DRIFT grep) | **`go build` + `go test` + golden-vector conformance vs the live Fineract oracle** + property invariants |
| "Correct" means | Non-negotiables not violated | **Parity with Fineract on captured vectors**, to defined rounding |
| Reviewer's core act | Re-derive numbers, check citations | **Re-derive money math and recompute against the Fineract vector** |
| Highest-risk gate | Ratified DEC-n change | **Context CUTOVER (Fineract → Go)** — a `user` gate |
| Autonomy across sessions | Manual `/softhouse resume` | **+ token-limit scheduler**: checkpoint at the daily soft limit, auto-resume on schedule |

## 4. The verifier is the golden-vector harness

On the bank project the verifier runs `verify-docs.sh` — a text grep proving known-bad patterns are absent. Its structural analog here is the **conformance harness** (`.softhouse/conformance.sh`, to be built in Phase 1 of the engagement plan): it replays golden vectors captured from the live Fineract through the Go module and diffs the outputs. The philosophy carries over exactly — it proves *absence of divergence on covered scenarios*, not correctness for all inputs, which is why the independent re-deriving reviewer still exists. `/softhouse-uat` wires build, unit tests, conformance, and property invariants into one gate.

## 5. The scheduler folds in cleanly

The bank pipeline already persists all state and supports `/softhouse resume` — 90% of what autonomous operation needs. The only missing piece for a long, budget-bounded migration is *automatic* resumption. `docs/agent-squad-delivery-and-scheduler.md` supplies it: the orchestrator meters the daily token budget, checkpoints every worker to `.softhouse/state/*.STATE.json` + `RESUME.md` at the soft limit, and a Cowork scheduled task fires at quota reset to run `/softhouse resume`. No new state model — it reuses the pipeline's existing one.

## 6. How to run it (once code and oracle exist)

1. `git init` this repo, set `origin`, ensure `main` tracks it (the pipeline pushes).
2. Stand up the **Fineract oracle** and the **conformance harness** (engagement-plan Phase 1) — nothing ports before the harness can grade it.
3. `/softhouse-plan "port the embeddable schedule generator"` → review the task graph → `/softhouse resume` to execute. This is the PoC: one small context, through the full pipeline, deliberately crossing a token-limit checkpoint once to prove resume.
4. Then plan the Minimum Portable Core contexts in strangler order (GL → loan → charges/rates/tax → COB → provisioning), each as its own run, each ending at a `user` cutover gate.

## 7. What is scaffold vs what still needs building

**Seeded and runnable now:** the three skills, `CLAUDE.md`, `.softhouse/patterns.md`. The pipeline can plan immediately.

**Still to build (engagement-plan Phase 1):** `.softhouse/conformance.sh` and the golden-vector store; the Fineract oracle environment; the frozen adapter contract; the token-budget metering in the orchestrator. Until the harness exists, `/softhouse-uat conformance` has nothing to grade — treat the current scaffold as the plan/execute/review spine awaiting its oracle.

---

*Companion docs: `agent-squad-delivery-and-scheduler.md`, `softhouse-engagement-plan.md`, `softhouse-skills-requirements.md`, `gerege-nbfi-fineract-as-module-ideation.md`. Source of the reused pipeline: the `digital_coop_bank` project's `.claude/skills/softhouse*` and `.softhouse/`.*
