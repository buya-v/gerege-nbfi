# First-run prompt — kicking off the softhouse migration

**Copy-paste prompts to drive the Fineract → Go migration through the `softhouse` pipeline, in order.**

Project: gerege-nbfi · Prepared for: Buyan · Date: 13 August 2026
Read alongside `softhouse-migration-pipeline.md`, `agent-squad-delivery-and-scheduler.md`, and `.softhouse/patterns.md`.

---

## Why the first plan is scoped to a PoC, not the whole goal

The pipeline plans **one bounded context per run**, and nothing can be verified until the golden-vector conformance harness exists (Fineract is the oracle; the Go output is "correct" only when it matches captured vectors). So the first `/softhouse-plan` is **harness-first + the 182-line schedule-generator PoC** — the cheapest slice that exercises the full plan → code → re-derive-review → conformance → checkpoint/resume loop and de-risks the whole program. Everything else is recorded to backlog in strangler order and planned in later runs.

---

## Prerequisites (once, before the first plan)

`/softhouse-plan` STEP 0 aborts on a dirty tree, and the pipeline pushes. So:

1. `git init` this repo; commit the scaffold (`CLAUDE.md`, `.claude/skills/`, `.softhouse/`, `docs/`).
2. Set an `origin` remote and make `main` track it.
3. Remove `_to_delete/` (the skill-install staging folder).
4. The **Fineract oracle does not need to exist yet** — planning only reads `CLAUDE.md` + `.softhouse/patterns.md` and writes a task graph. The oracle is needed later, when `/softhouse resume` runs and `/softhouse-uat conformance` grades output.

---

## Run 1 — Foundation + schedule-generator PoC (paste this)

```
/softhouse-plan Prove the Fineract→Go migration pipeline end-to-end on the smallest real slice, harness-first. IN SCOPE for THIS run only:
(1) Build the golden-vector conformance harness (.softhouse/conformance.sh) and a vector store, capturing vectors for the progressive-loan schedule generator from the live Fineract oracle.
(2) Define the minimal frozen adapter interface needed to invoke a schedule generator (spec_writer) — mark its ratification a user gate.
(3) Port fineract-progressive-loan-embeddable-schedule-generator (~182 LOC) to Go behind that interface (coder), integer-minor-units only, no float in any path.
(4) Verify via /softhouse-uat: go build + the schedule-generator conformance vectors must pass, and property invariants (schedule principal amortizes to exactly zero, rounding matches Fineract) must hold.
Every coder/analyst task gets a paired INDEPENDENT reviewer that RE-DERIVES the schedule arithmetic against the Fineract vector, not reads it. SCOPE GUARD: Minimum Portable Core, PoC slice only — do NOT plan GL posting logic, COB, charges/rates/tax, provisioning, or ANY context cutover in this run; record them to backlog in strangler order (GL → loan lifecycle → charges/rates/tax → COB → provisioning). Route as user gates: adapter-contract ratification and any cutover. This run also exercises the token-limit checkpoint/resume once.
```

Review the task graph it prints, then execute with `/softhouse resume`.

---

## Follow-on runs (one `/softhouse-plan` each, after the prior run is green)

Plan these in strangler order — each ends at a `user` cutover gate, and each reuses the harness, the frozen contract, and the scheduler from Run 1.

**Run 2 — General Ledger / accounting**
```
/softhouse-plan Port the Fineract General Ledger / accounting context to Go behind the frozen adapter contract, harness-graded. In scope: double-entry posting rules, chart-of-accounts behavior, journal entries/items. test_writer captures GL vectors + trial-balance invariants from the oracle; coder implements; independent reviewer re-derives every posting and balance. Verify: /softhouse-uat conformance passes for GL vectors; double-entry always balances; append-only enforced; no direct balance writes. Scope guard: GL only — no loan lifecycle, no COB, no cutover in this run. The cutover of GL is a separate user gate after a clean shadow-parity window.
```

**Run 3 — Loan product + schedule + lifecycle**
```
/softhouse-plan Port the Fineract loan lifecycle to Go behind the frozen contract, reusing the schedule generator from Run 1. In scope: loan products, interest methods, disbursement, repayment, penalties, rescheduling, write-off. test_writer captures loan vectors across the product-config matrix; coder implements; independent reviewer re-derives schedules, accruals, and rounding at each step against the vectors. Verify: /softhouse-uat conformance passes across the loan vector matrix; principal amortizes to zero; no float. Scope guard: loan context only; cutover is a separate user gate.
```

**Run 4 — Charges / rates / tax**
```
/softhouse-plan Port the Fineract charges, rates, and tax context to Go behind the frozen contract, including the VAT/e-Barimt tie-in. test_writer captures fee/rate/tax vectors from the oracle; coder implements; independent reviewer re-derives every fee and tax computation. Verify: /softhouse-uat conformance passes; no float; thresholds read from config, never hard-coded. Scope guard: charges/rates/tax only; cutover is a separate user gate.
```

**Run 5 — Close-of-business (COB) batch**
```
/softhouse-plan Port the Fineract close-of-business batch to Go, reusing Nexus's scheduler rather than porting Fineract's job framework. In scope: daily accrual/aging/posting, idempotency, restart-after-failure. test_writer captures end-of-day vectors (day-over-day balances) from the oracle; coder implements; independent reviewer re-derives EOD postings. Verify: /softhouse-uat conformance shows EOD parity day-over-day on the shared dataset. Scope guard: COB only; cutover is a separate user gate.
```

**Run 6 — Provisioning / reporting (Tier-A completion)**
```
/softhouse-plan Port provisioning and the FRC-reporting data feeds to Go behind the frozen contract, completing the Minimum Portable Core. test_writer captures provisioning-threshold vectors from the oracle; coder implements; independent reviewer re-derives thresholds. Verify: /softhouse-uat conformance passes; compliance-spine capital and 30%/70% limit figures reconcile against the native GL. Scope guard: provisioning/reporting only; Tier-A cutover and regulatory acceptance are user gates (parallel run required).
```

---

## Remember

- **The `user` gates are real stop points.** No context is cut over from Fineract to Go without vectors passing, a clean shadow-parity window, and — for Tier-A — regulatory/parallel-run sign-off. Agents plan and build; humans approve the switch.
- **The reviewer re-derives money math.** That single discipline is what the sister project proved catches plausible-but-wrong ledger formulas.
- **The scheduler keeps it running.** At the daily token soft-limit the orchestrator checkpoints and a scheduled task resumes via `/softhouse resume` — the long migration advances unattended without a big-bang bet.
