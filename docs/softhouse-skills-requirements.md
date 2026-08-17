# Software House — Skills & Team Requirements

**For the full-native migration of Apache Fineract into a Go module of Gerege Nexus**

Project: gerege-nbfi · Prepared for: Buyan · Date: 13 August 2026
Scope of this document: the capabilities a software house must field to reimplement Fineract's core-banking domain natively in Go (Option 4, executed as a strangler). Companion: *Software House — Engagement & Delivery Plan*.

---

## 1. Why this needs an unusual team

This is not a CRUD application build. It is the reimplementation of ~544,000 lines of mature, regulator-facing financial logic — loan mathematics, double-entry accounting, end-of-day batch, provisioning — where the failure mode is not a broken screen but **silently wrong money**. The team you engage must be selected for *financial correctness discipline* first and raw coding speed second. A generic Go web shop, however competent, will not succeed here without the specialist roles below.

The single most important consequence: the team's value is concentrated in three scarce competencies — **core-banking domain knowledge, ledger-grade correctness engineering, and Go systems depth** — and any candidate software house must demonstrably have all three, not two of three.

---

## 2. Team composition

Headcount is for the steady-state build. The engagement ramps into and out of this (see the delivery plan); it does not need everyone from day one.

| # | Role | FTE | Seniority | Provided by |
|---|---|---|---|---|
| 1 | Engagement / Delivery Lead | 1 | Senior | Software house |
| 2 | Technical Architect — Go + core-banking | 1 | Principal | Software house |
| 3 | Senior Go Domain Engineers | 3–4 | Senior | Software house |
| 4 | Core-Banking Domain Analyst (loan math + accounting SME) | 1 | Expert | Software house or joint |
| 5 | SDET / Conformance Test Engineers | 2 | Senior | Software house |
| 6 | Data & Migration Engineer | 1 | Senior | Software house |
| 7 | DevOps / Platform Engineer (CI, shadow infra, observability) | 1 | Senior | Software house |
| 8 | Security Engineer | 0.5 | Senior | Software house |
| 9 | Product Owner / Regulatory liaison | 1 | — | **Client (you)** |
| 10 | Fineract SME advisor | 0.25 | Expert | Software house or external |

Effective steady-state squad: **~8–9 FTE from the software house**, plus your product owner and regulatory liaison, whom you must supply — the vendor cannot own the FRC relationship or the Mongolian-NBFI product intent for you.

The two roles people under-resource and shouldn't: the **Domain Analyst (#4)** and the **Conformance SDETs (#5)**. They are the difference between a port that looks done and one that is provably correct.

---

## 3. Role-by-role skill requirements

**Engagement / Delivery Lead.** Runs a milestone-based, incremental (strangler) delivery; fluent in T&M and milestone governance, not just fixed-scope waterfall. Must be comfortable with "cut over one bounded context at a time" and with acceptance gates defined by test parity rather than feature demos. Manages continuity risk on a multi-year engagement.

**Technical Architect (the linchpin).** Deep Go (concurrency, memory model, error handling, module design) *and* real core-banking exposure — has built or ported a ledger, understands transactional integrity, idempotency, and the anti-corruption pattern. Owns the frozen adapter contract, the schema-first data strategy, and the Fineract↔Go switchability. This person's absence is a project-ending risk; require a named individual and a deputy.

**Senior Go Domain Engineers.** Production Go at scale; disciplined about numeric correctness (decimal arithmetic, never floats for money), rounding, and deterministic behavior. Able to read Java (Spring/Hibernate) well enough to use Fineract as the specification. Test-first by habit. Prior fintech/ledger/payments experience strongly preferred over generic backend breadth.

**Core-Banking Domain Analyst / SME.** Expert in loan mechanics (interest methods — declining balance, flat, progressive/amortized; day-count conventions; accrual; penalties; rescheduling; write-off), double-entry accounting, provisioning, and IFRS-aligned reporting. Translates Fineract behavior and Mongolian FRC rules into the golden vectors the engineers build against. This is the role that keeps the money correct; it is rarer than the Go skill and harder to substitute.

**SDET / Conformance Test Engineers.** Own the golden-vector harness and the shadow/differential testing rig. Skills: property-based testing, deterministic replay, test-data generation across product-config permutations, comparing two systems' outputs to defined tolerances, and building the CI that blocks a cutover until parity holds. They effectively make Fineract the automated grader of the Go implementation.

**Data & Migration Engineer.** PostgreSQL depth; owns adopting/pruning Fineract's schema and its 424 migrations, the shared-DB dual-run, reconciliation, and per-context cutover data integrity. Understands online migration and back-out.

**DevOps / Platform Engineer.** CI/CD, containerization, GraalVM/JVM co-running during the strangler period, observability (metrics/tracing/log correlation across the Go module and the surviving Fineract), and the shadow-traffic plumbing. Integrates with Nexus's existing deploy pipeline.

**Security Engineer (part-time).** AppSec for financial systems: secrets, access control, audit-log integrity, dependency/vuln scanning; supports the Article 12.3 confidentiality and Article 16 audit obligations.

---

## 4. Competency matrix (must-have M / desirable D)

| Competency | Arch | Go Eng | Domain SME | SDET | Data | DevOps |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| Go systems & concurrency | M | M | – | D | D | M |
| Core-banking / loan mathematics | M | D | M | D | D | – |
| Double-entry accounting / GL | M | D | M | D | D | – |
| Decimal money arithmetic & rounding rigor | M | M | M | M | D | – |
| Reading Java/Spring (as spec) | M | M | D | D | D | D |
| Property-based / golden-vector testing | D | D | D | M | – | D |
| Differential / shadow testing | D | D | – | M | D | M |
| PostgreSQL & online data migration | D | D | – | D | M | D |
| Regulatory/audit awareness (IFRS, FRC-type) | D | – | M | D | – | – |
| Observability & CI/CD for finance | D | D | – | D | D | M |
| Mongolian NBFI / e-Barimt / eID context | D | D | D | – | D | D |

The columns that must be strong for the project to be safe: **Domain SME** and **SDET**. If a vendor is deep in Go but thin in those two, they can build fast and be confidently wrong — the worst outcome for a lender.

---

## 5. Vendor selection criteria

Evaluate candidate software houses against evidence, not slideware:

1. **A shipped ledger or core-banking build in their history** — ask for a reference where they owned money-movement correctness, ideally in Go.
2. **Named key people, not "a team."** The Architect and Domain SME must be identified individuals with relevant CVs, and contractually retained (anti-bait-and-switch clause).
3. **They pass the paid PoC** (see delivery plan): port the 182-line embeddable schedule generator and hit Fineract's golden vectors within a 3–4 week trial. This single filter is worth more than any RFP response.
4. **Test culture is native, not bolted on** — they propose the conformance harness themselves; if they don't raise correctness-testing unprompted, disqualify.
5. **Comfort with incremental cutover and T&M/milestone contracting** — a vendor pushing a fixed-price big-bang for this is either naïve or transferring risk back to you dishonestly.
6. **Continuity commitment** — staffing stability plan and knowledge-transfer obligations for a multi-year engagement.

**Red flags:** promises of a fixed total price and date for the whole port; float/double for money; "we'll figure out testing later"; no one on the team who can read Fineract's Java; enthusiasm for rewriting *everything* (including the plumbing Nexus already provides); no questions about the FRC or Mongolian product rules.

---

## 6. Knowledge transfer, continuity and IP

Because this becomes forever-yours regulated code, the contract must require, from day one and not at the end:

- **Documentation-as-you-go** of every ported context: the golden vectors, the design decisions, the deviations from Fineract, and the reconciliation results.
- **Pairing / shadowing** by at least one client-side engineer per context, so domain knowledge does not leave with the vendor.
- **Full IP assignment** of all produced code, tests, vectors and tooling to you; source in your repositories from commit one.
- **Named-person retention** and notice obligations for the Architect and Domain SME.
- **Exit runbook** kept current: at any milestone you can take the code in-house or to another vendor and keep running, because Fineract remains the live fallback until the last cutover.

---

## 7. What you must supply (not outsourceable)

The software house cannot own these; staff them on your side:

- **Product Owner** with authority over Mongolian NBFI product definitions and priorities.
- **Regulatory liaison** owning the FRC relationship, audit coordination, and the parallel-run acceptance.
- **Domain access** — your people who know how the institution actually operates, available for the SME and analysts.

Underfunding your own side is the most common way these engagements drift, because the vendor ends up guessing at intent that only you can supply.

---

*Companion documents in this project: `softhouse-engagement-plan.md`; and the platform proposals (`gerege-nbfi-proposal`, two-system variant, options comparison, Fineract-as-module ideation). Grounding: measured `fineract` size ~544k main LOC / 5,317 files / ~321k test LOC / 424 changelog files.*
