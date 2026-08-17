# Agent-Squad Delivery Model & Scheduler Agent

**Running the Fineract → Go migration as squads of AI agents, kept alive across daily token limits by a scheduler agent**

Project: gerege-nbfi · Prepared for: Buyan · Date: 13 August 2026
Revises the staffing model in `softhouse-engagement-plan.md` and `softhouse-skills-requirements.md`: the delivery unit is now an **agent squad**, and the "software house" is a set of such squads plus human oversight. All correctness gates from the engagement plan remain unchanged.

---

## 1. The idea, stated precisely

The "squad" is no longer a group of human engineers — it is an **orchestrated squad of AI agents**, and the software house is **several such squads** ("softhouse squads"), one per bounded context, plus a **conformance squad** and a single **scheduler/orchestrator agent** above them all.

The migration is long (a large regulated port) and agents consume tokens against a **daily budget/limit**. So the whole point of the scheduler agent is continuity: when the day's token limit is reached, it **checkpoints every squad, pauses cleanly, and resumes all squads on a schedule** when the quota resets — so a multi-month port runs day after day without a human manually restarting it, and without losing or duplicating work across the boundary.

Two things do **not** change from the human-team plan: correctness is still proven against golden vectors, and **no money-critical context is cut over without the human gate**. Agents build and verify; humans (and the automated conformance harness) approve. Autonomy is for *producing and testing* code, not for *deciding the ledger is correct*.

---

## 2. Anatomy of an agent squad

Each squad maps the human roles from the skills document onto agent roles, coordinated by the scheduler:

| Agent role | Does | Human analogue |
|---|---|---|
| **Planner agent** | Decomposes the context into work items; maintains the squad backlog | Tech lead |
| **Coder agents** (1–N) | Port/implement Go code for the assigned work items | Go engineers |
| **Conformance agent** | Runs golden vectors + property tests; reports parity/diffs | SDET |
| **Reviewer/verifier agent** | Adversarially checks the coder output for correctness, especially money math and rounding | Senior reviewer |
| **Scribe agent** | Writes the per-context documentation, vectors, decisions | — |

The **reviewer/verifier agent is mandatory and adversarial** — its job is to try to break the coder's output, because an AI coder will produce plausible-but-wrong financial code confidently. In money math, a second independent agent whose incentive is to refute is worth more than another coder.

---

## 3. Squad topology (who runs, on what)

One squad per bounded context from the engagement plan, so the strangler sequencing is preserved:

- **Harness squad** — builds/maintains the golden-vector + shadow rig (runs first; everything depends on it).
- **GL / accounting squad**
- **Loan + schedule + lifecycle squad** (largest)
- **Charges / rates / tax squad**
- **COB batch squad**
- **Provisioning / reporting squad**
- **Conformance squad** — cross-cutting; owns the oracle comparison and the parity dashboards.
- **Scheduler / orchestrator agent** — singular, above all squads (§4).

Squads work the sequence the plan defines; the harness and GL squads gate the rest.

---

## 4. The Scheduler / Orchestrator Agent — the core of this request

### 4.1 Responsibilities
1. Hold the **global backlog** and dispatch work items to the right squad, respecting the strangler order and dependencies.
2. **Track token consumption** against the daily budget in real time.
3. When the budget threshold is reached (or a quota/rate-limit error is hit), **checkpoint and pause** every active squad cleanly.
4. **Resume all squads on schedule** when the quota window resets, from their checkpoints — no lost or duplicated work.
5. Stop and **wait for a human** whenever a squad reaches a correctness/cutover gate — never auto-approve those.

### 4.2 The token-limit loop (the mechanism you asked for)

```
loop (each working session):
  1. orchestrator pulls next work item(s) → dispatches to squad(s)
  2. squads work; orchestrator meters cumulative tokens used today
  3. IF tokens_used ≥ DAILY_SOFT_LIMIT (e.g. 90% of quota)
        OR a quota/rate-limit error is returned:
        a. signal all active agents to CHECKPOINT NOW:
             - commit work-in-progress to the squad's branch
             - write STATE.json (current item, step, next action, open questions)
             - update the shared task list
        b. write RESUME.md manifest: which squads were active + their next step
        c. orchestrator stops (graceful, not mid-write)
  4. a SCHEDULED TASK fires at the quota-reset time →
        starts a FRESH orchestrator session →
        reads RESUME.md + each squad's STATE.json →
        re-dispatches squads to continue exactly where they stopped
  5. repeat until backlog empty OR a human gate is reached (then WAIT)
```

The key discipline is that **all durable state lives in the repository**, not in an agent's memory. A fresh scheduled session can reconstruct everything from `RESUME.md` + `STATE.json` + the WIP branches. That is what makes "resume all agents by schedule" reliable rather than hopeful.

### 4.3 Checkpoint / state model (per squad)

```json
// docs/orchestrator/state/<squad>.STATE.json
{
  "squad": "gl-accounting",
  "context": "General Ledger",
  "current_item": "port journal-entry posting rules",
  "step": "3 of 6 — reconcile rounding on multi-currency splits",
  "branch": "wip/gl/journal-posting",
  "next_action": "run vector set GL-014..GL-032, fix diffs",
  "blocked_on": null,
  "open_questions": ["day-count basis for cross-ccy accrual?"],
  "gate_pending": false,
  "last_checkpoint": "<timestamp injected at write time>"
}
```

`RESUME.md` is a short human-readable manifest listing active squads and pointing at each `STATE.json` — so both the next scheduled session *and* a human can see, at a glance, exactly where the factory paused.

---

## 5. Implementing the scheduler on real primitives

Two viable substrates; pick by where the factory runs.

**A. Inside Cowork (scheduled tasks).** Use a **daily scheduled task** set to fire shortly after your quota-reset time. Its prompt: *"Resume the gerege-nbfi migration orchestrator: read `docs/orchestrator/RESUME.md` and each `state/*.STATE.json`, and continue each squad from its next_action until the daily budget threshold, then checkpoint and stop."* Each firing is a fresh session that rebuilds state from the repo — exactly the resume protocol in §4.2. For within-session pacing (stopping at the soft limit before a hard error), the orchestrator uses a self-scheduled wake-up so it pauses proactively rather than crashing into the limit.

**B. Self-hosted Claude Agent SDK.** An orchestrator process using the SDK: it reads `usage` tokens off each API response, enforces `DAILY_SOFT_LIMIT`, catches quota/rate-limit errors, persists the checkpoints, and a system **cron** at reset time relaunches it. This gives you full control of budgets, parallelism (the SDK can fan out squads), and observability, at the cost of running the harness yourself.

In both, the invariants are identical: **soft-limit before hard-limit, checkpoint to repo, resume from repo on schedule, human gates halt the loop.**

---

## 6. Guardrails — non-negotiable for a regulated ledger

- **The conformance harness is the guardrail that makes agent autonomy safe.** Because agents produce confident-but-wrong financial code, *nothing* advances without golden vectors + property invariants passing. The harness is built first and is the hard gate.
- **Adversarial verification** on every money-critical change (the reviewer agent, ideally multiple independent verifier passes that try to refute correctness before it's accepted).
- **Human gate at every cutover.** Agents may reach "parity proven, ready to cut over" and then **stop and wait**; a human + the regulatory liaison approve the switch. The scheduler never crosses a gate autonomously.
- **Fineract stays live as oracle and fallback** throughout, per the engagement plan — agent work is always graded against the incumbent.
- **Everything in version control**, every agent action auditable — which also serves the Article 12.3 / Article 16 audit obligations.

---

## 7. What this changes about time and cost

The agent-squad model changes the *shape* of throughput, not the correctness bar:

- **Calendar is now gated by daily token budget, not headcount.** More budget/day → more work items cleared/day → shorter calendar; a small budget stretches the same work over more days. The scheduler makes that stretch *continuous and unattended* rather than stop-start.
- **Human effort shifts from writing to reviewing and gating.** You still need the human Architect, Domain SME and regulatory liaison — now as reviewers and gatekeepers of agent output, not as the primary typists.
- **The correctness tail does not shrink.** Agents accelerate producing and testing code; they do not remove the rounding/edge-case/reconciliation work or the regulatory parallel-run. Phase 3 (loan math) and Phase 7 (acceptance) remain the long poles.

Net: the agentic model can compress the *build* portion substantially if the token budget is generous, but the plan's gates, oracle and human sign-offs are unchanged — which is exactly what keeps it safe.

---

## 8. Risks specific to autonomous agents on financial code

| Risk | Mitigation |
|---|---|
| Confident-but-wrong money math | Golden vectors + property tests as hard gate; adversarial reviewer agent; human gate at cutover |
| Silent drift across a resume boundary (lost/duplicated work) | All state in repo; `RESUME.md` + `STATE.json`; idempotent work items; commit-before-checkpoint |
| Agent "finishes" by weakening a test to pass | Tests owned by a separate conformance squad; test changes require human/reviewer approval |
| Runaway token spend | `DAILY_SOFT_LIMIT` enforced by orchestrator; stop-and-checkpoint before hard limit |
| Scheduler resumes into a human-gate item and proceeds anyway | Gates are explicit stop states; scheduler waits, does not cross |
| Context loss between fresh sessions | Durable repo state + concise `RESUME.md`; never rely on agent memory |

---

## 9. To operationalize a pilot (next step)

1. Create `docs/orchestrator/` in the project with `RESUME.md` and an empty `state/` folder (the scheduler's home).
2. Stand up the **harness squad first** — no other squad may advance until the golden-vector rig grades their output.
3. Run the **schedule-generator PoC** (from the ideation doc) as the first work item through one squad + the scheduler, deliberately crossing a daily-limit boundary once, to prove the checkpoint/resume loop before scaling to all squads.
4. Only then fan out the remaining squads in strangler order.

The pilot's real purpose is to prove two things cheaply: that the **resume-on-schedule loop is reliable**, and that the **conformance gate actually stops bad agent output** — before you trust the factory with the ledger.

---

*Companion docs in this project: `softhouse-skills-requirements.md`, `softhouse-engagement-plan.md`, `gerege-nbfi-fineract-as-module-ideation.md`. If you want, this can be wired into a live Cowork scheduled task and an `docs/orchestrator/` scaffold so the loop is runnable, not just specified.*
