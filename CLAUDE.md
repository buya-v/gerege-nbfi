# Gerege NBFI — project context

## What this is

The composition layer for a Mongolian NBFI core platform, and the home of the **Fineract → Go native migration** into a module of Gerege Nexus. The `softhouse` agent pipeline in `.claude/skills/` plans and executes that migration; this file carries the non-negotiables it grades against.

Primary market: **Mongolia.** Regulator: **FRC** (Financial Regulatory Commission) for the NBFI; Bank of Mongolia for payment/e-money licensing.

## Non-negotiables

Grep diffs against these. Violating one is a rejection, not a discussion.

- **Money is integer minor units.** No floating-point in any monetary code path, struct field, schema column, API field, or test fixture — including intermediate calculation. Display 0 decimals (`1,250,000₮`, postfix); store 2 (ISO). MNT = ISO 4217 numeric 496, minor unit 2.
- **The ledger is double-entry and append-only.** Balances are derived, never written. Corrections are reversing entries. Holds are postings and alter `available` only, never posted `balance`.
- **`Idempotency-Key` is mandatory on every money-movement POST.**
- **Fineract is the oracle and fallback.** No ported Go context is correct until its golden vectors match Fineract's captured outputs to the defined rounding. **No context is cut over** (Fineract → Go) without vectors passing, a clean shadow-parity window, and regulatory/parallel-run sign-off — a `user` gate.
- **Contract-first, schema-first, strangler.** The frozen adapter contract is the boundary; adopt Fineract's PostgreSQL schema; reimplement one bounded context at a time. A change to the contract is a `user` task.
- **Never describe member savings as insured, protected, or guaranteed.** SCC deposits are not covered by Mongolian deposit insurance.
- **Names are three fields** — ovog (clan), patronymic, given name. Never `first_name`/`last_name`. Match on registration number.
- **National ID is 10 characters** — 2 Cyrillic letters + 8 digits; month +20 for births from 2000 onward; check digit unpublished — validate structurally.
- **Two time zones, no DST** — `Asia/Ulaanbaatar` (+08) and `Asia/Hovd` (+07). Never hard-code an offset.
- **No US payment rails / vendors.** Mongolia: RTGS (Banksuljee) above MNT 5,000,000, ACH+ at or below, NETC for cards; threshold from config, never hard-coded. No Stripe/Plaid/Lithic/Persona.

## Migration scope — Minimum Portable Core

**Port:** GL/accounting, loan product + schedule + lifecycle, charges/rates/tax, COB, provisioning/reporting.
**Do NOT port:** savings/deposits (deposit-taking prohibited for an SCC/NBFI — only tiny internal control-account logic), working-capital-loan, investor, branch (deferred). Much of `fineract-core` is plumbing Nexus already provides — map, don't port.

Proof-of-concept first port: `fineract-progressive-loan-embeddable-schedule-generator` (~182 LOC) against the golden-vector harness.

## Blocking questions — `user` decision gates

Do not let an agent decide these; route as `executor: "user"`:
- Any context CUTOVER from Fineract to the Go module.
- Any change to a ratified DEC-n or the frozen adapter contract.
- Regulatory acceptance / parallel-run sign-off (FRC, external audit).

## How work is executed

Via the `softhouse` pipeline (`/softhouse`, `/softhouse-plan`, `/softhouse-uat`) — parallel isolated-worktree agents, independent adversarial review that re-derives money math, golden-vector conformance vs the Fineract oracle, and a token-limit-aware scheduler that checkpoints and resumes. See `docs/softhouse-migration-pipeline.md` and `docs/agent-squad-delivery-and-scheduler.md`. Learned patterns and the full constraint list live in `.softhouse/patterns.md`.

## Verification

`/softhouse-uat`: `go build ./...`, `go test ./...`, the golden-vector conformance run vs Fineract, and property invariants (double-entry balances; principal amortizes to zero; splits sum to whole). A PASS means "builds, tests green, known-bad patterns absent, matches Fineract on captured vectors" — never "safe to cut over."
