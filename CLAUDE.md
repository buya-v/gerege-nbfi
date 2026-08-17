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
- **PostgreSQL is the only database.** Every environment — the Fineract reference instance, the Go module, vector capture, shadow/differential runs, CI — runs on **PostgreSQL**. Fineract's own default is already Postgres (`org.postgresql.Driver`, `jdbc:postgresql://…:5432/fineract_tenants`); bring it up with the `postgresql` compose profile, never `docker-compose-mysql*.yml` / `docker-compose-mariadb*.yml`. **Oracle Database is prohibited** — no `ojdbc`, no `oracle.jdbc.*`, no Oracle dialect, no port 1521 anywhere in this program. Go talks to Postgres via `pgx`; a diff introducing a MySQL/MariaDB/Oracle driver or dialect is a rejection. Parity is only meaningful when oracle-instance and Go module read the *same PostgreSQL schema*.

### Terminology — "oracle" (read this before writing any task)

In this project **"the oracle" means the Fineract reference implementation** we grade Go output against (test-oracle sense), recorded in `.softhouse/reference-oracle.md`. It has **nothing to do with Oracle Database**, which is prohibited (above). When writing tasks, docs or prompts, say "**reference oracle (Fineract)**" for the reference implementation and "**Oracle Database**" only to name the prohibited product.

## Migration scope — the whole Fineract codebase, in tiers

**Ratified 17 August 2026 (supersedes the earlier "Minimum Portable Core only" scope).** The target is the **complete Fineract codebase** ported to Go behind the frozen adapter contract, worked in strangler order. Nothing is out of scope for *porting*; the tiers set the ORDER, and the gates below control what may be *switched on*.

Authoritative context inventory, LOC and per-context state: **`.softhouse/program.json`** (measured from the pinned Fineract checkout — ~544k main Java LOC, 5,317 files).

- **Tier 0 — harness + PoC.** Golden-vector conformance rig, frozen contract DEC-1, `fineract-progressive-loan-embeddable-schedule-generator` (~182 LOC).
- **Tier A — money core.** GL/accounting, loan product + schedule + lifecycle, charges/rates/tax, COB, provisioning/reporting.
- **Tier B — remaining business contexts.** Savings/deposits, working-capital-loan, investor, branch, loan-origination, share accounts/products, collateral, clients/groups/collection sheet, transfers, funds. **Porting is in scope; see the activation gate below.**
- **Tier C — platform.** `fineract-core`, `fineract-provider/infrastructure`, security, command bus, organisation, user administration, notification, documents, interoperation, batch, SPM, DB migrations. **Map onto Nexus first; port only the genuine gaps** — re-porting plumbing Nexus already provides is waste, and the reviewer treats an unjustified plumbing port as a rejection.
- **Tier D — test corpus.** Fineract's ~321k test LOC and e2e suites are converted into golden vectors, not ported as tests.

**Scope guard, still enforced per run:** one bounded context per run. A worker that wanders outside its assigned context's `fineract_paths` is a rejection. "All of Fineract is in scope" is a statement about the *program*, never about a single task.

## Blocking questions — `user` decision gates

Do not let an agent decide these; route as `executor: "user"`:
- Any context CUTOVER from Fineract to the Go module.
- Any change to a ratified DEC-n or the frozen adapter contract.
- Regulatory acceptance / parallel-run sign-off (FRC, external audit).
- **Deposit-taking ACTIVATION.** Porting `fineract-savings` / deposit code is in scope; **enabling deposit-taking behavior in any live environment is not**, until the FRC/Bank of Mongolia licensing position is signed off. Ported deposit code ships disabled by config, and the "never insured/protected/guaranteed" rule applies to every string it returns. This is a licensing gate on the *activation*, not a scope block on the *port*.

## How work is executed

Via the `softhouse` pipeline (`/softhouse`, `/softhouse-plan`, `/softhouse-uat`) — parallel isolated-worktree agents, independent adversarial review that re-derives money math, golden-vector conformance vs the Fineract oracle, and a token-limit-aware scheduler that checkpoints and resumes. See `docs/softhouse-migration-pipeline.md` and `docs/agent-squad-delivery-and-scheduler.md`. Learned patterns and the full constraint list live in `.softhouse/patterns.md`.

**The program does not stop at a run boundary.** `/softhouse-program` is the driver above `/softhouse`: it plans the next context from `.softhouse/program.json` the moment a run goes terminal, resumes after a token-limit checkpoint, and keeps advancing until every context is `done`. It **never** crosses a `user` gate — a pending gate parks that one context in `.softhouse/gates.md` and the driver moves to the next unblocked context instead of halting. A scheduled task fires it daily so the migration advances unattended. Stop conditions are exactly three: program complete, a `user` gate is the *only* remaining work, or the oracle is unreachable for vector work (analysis/spec tasks continue).

## Verification

`/softhouse-uat`: `go build ./...`, `go test ./...`, the golden-vector conformance run vs Fineract, and property invariants (double-entry balances; principal amortizes to zero; splits sum to whole). A PASS means "builds, tests green, known-bad patterns absent, matches Fineract on captured vectors" — never "safe to cut over."
