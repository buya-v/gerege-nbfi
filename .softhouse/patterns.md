# Softhouse learned patterns — Gerege NBFI (Fineract → Go migration)

Softhouse reads this file during pre-flight and applies it when planning. Anything above the markers is hand-written project knowledge; everything between the markers is appended automatically by each run's postmortem.

Seeded from the proven Digital Coop Bank pipeline. The money/Mongolia constraints are inherited; the migration-specific rules are new.

## Project constraints

Rules a worker agent must not violate. These get grepped against diffs during review.

### Money and the ledger (inherited — non-negotiable)

- **No floating-point in any monetary path** — not in struct fields, DB columns, API fields, test fixtures, or intermediate calculation. Integer minor units only (MNT, ISO 4217 numeric 496, minor unit 2).
- **Balances are derived, never written.** Any diff assigning to a balance column directly is a rejection.
- **The ledger is append-only.** Corrections are reversing entries. An `UPDATE`/`DELETE` of a posted entry is a rejection.
- **Holds alter `available` only, never posted `balance`.** This was the exact defect that failed adversarial review twice on the sister project (an inverted hold formula that made pledged collateral spendable). Re-derive hold math with the sign forced.
- **`Idempotency-Key` mandatory on every money-movement POST.** No exceptions for "internal" transfers.

### Migration method (new — non-negotiable)

- **Fineract is the ORACLE and FALLBACK.** No Go context is "correct" until its golden vectors match Fineract's captured outputs to the defined rounding. Prove parity; never assert it.
- **The reviewer re-derives money math, it does not read it.** The sister project's headline lesson: a plausible-but-wrong ledger formula survived two adversarial reviews and fooled one of three fresh auditors — only the ones who recomputed through the source conventions caught it. For a money conflict, the synthesizer re-derives from source, never tallies votes.
- **Contract-first:** the frozen adapter contract is the boundary. Behind it is Fineract-JVM or the Go module, switched per context by config. A worker that needs a contract change STOPs — that is a `user` task.
- **Schema-first:** adopt/prune Fineract's PostgreSQL schema; a shared DB enables shadow/differential testing.
- **Cutover is a `user` gate**, never an `agent` task — requires vectors passing + a clean shadow-parity window + regulatory/parallel-run sign-off.

### Scope (new)

- **Minimum Portable Core only:** GL/accounting, loan product + schedule + lifecycle, charges/rates/tax, COB, provisioning/reporting. Port these.
- **Do NOT port:** savings/deposits (SCC deposit-taking is prohibited — repurpose only tiny internal control-account logic), working-capital-loan, investor, branch — deferred; a requirement needing them surfaces a `user` task.
- Much of `fineract-core` is platform plumbing (auth, tenancy, command bus) that Nexus already provides — map onto Nexus, do not port.

### Mongolia rules (inherited)

- **Never render member savings as insured/protected/guaranteed** — SCC deposits are not covered; misrepresentation carries criminal exposure. Applies to any API-returned string.
- **No US payment rails.** Mongolia: RTGS (Banksuljee) above MNT 5,000,000, ACH+ at or below, NETC for cards. Threshold set by Governor's order — read from config, never hard-code.
- **No Stripe/Plaid/Lithic/Persona** assumptions — not the Mongolian market.
- **Names are three fields** — ovog, patronymic, given name. A diff introducing `first_name`/`last_name` is a rejection. Match on registration number, never name.
- **National ID is 10 characters** (2 Cyrillic letters + 8 digits); month field carries +20 for births from 2000 onward; check digit unpublished — validate structurally.
- **Two time zones, no DST** — `Asia/Ulaanbaatar` (+08), `Asia/Hovd` (+07). Use the tz library; never hard-code an offset.
- **Formatting:** dates `y.MM.dd`, week starts Monday, 24-hour clock. Currency postfix, zero decimals for display (`1,250,000₮`), 2 decimals stored.

### The honesty rule

Every worker prompt carries it; review enforces it. State only what you verified; mark each material claim `[VERIFIED: fineract source / vector id]` or `[UNVERIFIED]`. A confident invention in money code is the worst possible defect. (Origin: a research agent on the sister project fabricated an e-money licensee list and had to retract it.)

## Environment topology

- **Fineract oracle:** runs alongside for vector capture and shadow/differential testing. `/softhouse-uat conformance` needs it reachable; if it is down, conformance reports exit 2, not a false PASS.
- **Go module:** the migration target, in the Nexus tree, behind the frozen adapter contract.
- **Tests:** `go build ./...`, `go test ./...`, plus `.softhouse/conformance.sh` (golden vectors vs oracle) and property invariants. Grep-based HARD checks prove absence of known-bad patterns, never correctness.
- **Budget/scheduler:** the migration is long; the orchestrator meters the daily token budget, checkpoints all workers at the soft limit, and a scheduled task resumes via `/softhouse resume` at quota reset. See `docs/agent-squad-delivery-and-scheduler.md`.
- **Remote:** only the orchestrator pushes; workers commit to their branch.

## Codebase facts

- Fineract measured at ~544k main Java LOC / 5,317 files / ~321k test LOC / 424 changelog files. The ~321k test LOC is the vector-generation goldmine, not overhead.
- `fineract-progressive-loan-embeddable-schedule-generator` is ~182 LOC and self-contained — the designated proof-of-concept first port.
- Companion planning docs: `docs/gerege-nbfi-fineract-as-module-ideation.md`, `docs/softhouse-engagement-plan.md`, `docs/softhouse-skills-requirements.md`, `docs/agent-squad-delivery-and-scheduler.md`, `docs/softhouse-migration-pipeline.md`.

<!-- LEARNED PATTERNS START -->
<!-- Postmortems are appended below by each /softhouse run. -->
<!-- LEARNED PATTERNS END -->
