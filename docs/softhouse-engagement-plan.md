# Software House — Engagement & Delivery Plan

**Full-native migration of Apache Fineract into a Go module of Gerege Nexus**

Project: gerege-nbfi · Prepared for: Buyan · Date: 13 August 2026
Companion: *Software House — Skills & Team Requirements*. Grounding: measured `fineract` ≈ 544k main Java LOC / 5,317 files / ~321k test LOC / 424 changelog files.

---

## 1. Objective and scope

Deliver a native-Go reimplementation of Fineract's core-banking domain, running as a module inside the Gerege Nexus single binary, replacing the Fineract JVM — **without ever risking the institution's ledger on a big-bang cutover.**

Two scope tiers, delivered in order so value and safety come early:

- **Tier A — NBFI Minimum Portable Core** (GL/accounting, loan product + schedule + lifecycle, charges/rates/tax, COB, provisioning/reporting). This is what the institution actually needs to operate. Production-live target: **~18–24 months.**
- **Tier B — remainder toward "whole Fineract"** (any of savings-as-control-accounts, investor, working-capital, branch, etc. that prove in-scope later). Completes the full migration: **~3–4 years total.**

The plan below reaches Tier A first and treats Tier B as optional continuations, each justified on its own merits rather than assumed.

---

## 2. Delivery philosophy (non-negotiable)

Three rules protect the money and make the estimate achievable:

1. **Strangler-fig, one bounded context at a time.** Fineract stays live as **oracle and fallback** throughout. Each context is reimplemented, shadow-tested to parity, then cut over — and can be rolled back.
2. **Contract-first.** A frozen adapter interface sits in front of the ledger. Callers never know whether Fineract-JVM or the Go module answers; the implementation is switched per context by config. This is what makes each cutover reversible.
3. **Fineract-as-executable-specification.** Correctness is *proven* against golden vectors captured from the live Fineract and against property invariants — never asserted. No context cuts over until its vectors pass and a shadow-parity window is clean.

A vendor unwilling to work this way should not be engaged for this project.

---

## 3. Contract & commercial model

- **Do not** sign a fixed-price, fixed-date contract for the whole port. There is no safe big-bang cutover for a lender's ledger, and a fixed bid forces the vendor to either pad hugely or cut the testing that keeps you solvent.
- **Do** structure as: a **paid PoC trial** → then **milestone-based T&M** with acceptance gates per bounded context. Payment is released on gate acceptance (parity proven), not on code delivered.
- **Stage gates are real stop points.** After any context you may pause, change vendor, or take the work in-house, because Fineract still runs. Bake that right into the contract.

---

## 4. Phase plan

Durations assume the ~8–9 FTE squad from the skills document, ramping as shown in §6. Calendar ranges are planning-grade with wide error bars; the money-math tail and regulatory acceptance are the usual overrun sources.

### Phase 0 — Vendor selection & paid PoC · ~4–6 weeks
Shortlist software houses against the selection criteria. Run a **paid 3–4 week PoC** with each finalist (or the lead candidate): port the **182-line embeddable schedule generator** to Go and match Fineract's golden vectors, standing up a first slice of the conformance harness.
**Gate G0:** vectors pass; the vendor demonstrated correctness discipline and Fineract-reading ability. *This is the cheapest, highest-signal filter in the whole engagement.*

### Phase 1 — Foundations & specification · ~8–12 weeks
Freeze the adapter contract. Build the **golden-vector harness** and shadow/differential rig. Adopt and prune Fineract's PostgreSQL schema; set up shared-DB dual-run. Stand up CI quality gates, observability, and the Fineract-as-oracle environment. Capture the first vector sets for GL and lending.
**Gate G1:** harness operational; any Go context can now be graded automatically against live Fineract.

### Phase 2 — General Ledger / accounting context · ~10–14 weeks
Reimplement the double-entry GL and chart-of-accounts behavior (the most reused, most stable domain; guarded by balance-always-holds property tests). Shadow against Fineract; reconcile trial balances.
**Gate G2:** GL parity proven over a clean shadow window; cut over behind the contract. The compliance spine's capital math now runs on native GL.

### Phase 3 — Loan product + schedule + lifecycle · ~16–24 weeks
The hard money math: products, interest methods, schedule generation (kernel from the Phase-0 PoC), disbursement, repayment, penalties, rescheduling, write-off. Largest and riskiest context; the correctness tail lives here.
**Gate G3:** loan vectors pass across the product-config matrix; shadow parity clean; cut over.

### Phase 4 — Charges, rates, tax · ~6–10 weeks
Pricing, fees, interest rates, and VAT/e-Barimt tie-in.
**Gate G4:** parity proven; cut over.

### Phase 5 — Close-of-business (COB) batch · ~6–10 weeks
Daily accrual/aging/posting, idempotency, restart-after-failure — reusing Nexus's scheduler rather than porting Fineract's job framework.
**Gate G5:** end-of-day runs match Fineract day-over-day on the shared dataset; cut over.

### Phase 6 — Provisioning, reporting & Tier-A completion · ~8–12 weeks
Provisioning thresholds and the data feeds for FRC reporting via the compliance spine. Close out Tier A.
**Gate G6 — Tier A functionally complete:** the NBFI Minimum Portable Core runs natively; Fineract retained only as fallback/oracle.

### Phase 7 — Regulatory acceptance, parallel run & cutover · ~12–24 weeks (calendar you don't fully control)
Formal **parallel run** of native vs Fineract on production-like data; external audit of the reimplemented ledger; FRC comfort. Decommission Fineract for Tier-A scope only after sign-off. Hypercare.
**Gate G7:** audited parity + regulatory acceptance; Tier A **production-live**. *Target ≈ 18–24 months from G0.*

### Phase 8 — Tier B remainder (optional, justified per module) · +12–24 months
Only the additional Fineract modules that prove genuinely in scope, each as its own strangler mini-project with its own gate. Completes the **full** migration; total program **~3–4 years** if pursued to the whole.

---

## 5. Timeline at a glance

| Phase | Focus | Duration | Cumulative (approx.) |
|---|---|---|---|
| 0 | Vendor + paid PoC | 4–6 wk | ~1 mo |
| 1 | Foundations & harness | 8–12 wk | ~4 mo |
| 2 | GL / accounting | 10–14 wk | ~7 mo |
| 3 | Loan + schedule + lifecycle | 16–24 wk | ~12 mo |
| 4 | Charges / rates / tax | 6–10 wk | ~14 mo |
| 5 | COB batch | 6–10 wk | ~16 mo |
| 6 | Provisioning / reporting (Tier A done) | 8–12 wk | ~18 mo |
| 7 | Regulatory acceptance + parallel run | 12–24 wk | **~18–24 mo — Tier A live** |
| 8 | Tier B remainder (optional) | +12–24 mo | **~3–4 yr — full migration** |

Phases 2–6 overlap partially (a context can enter shadow while the next begins), which is already reflected in the compressed cumulative figures. They do **not** fully parallelize, because everything touches the GL.

---

## 6. Staffing ramp

| Phase | Squad size (vendor FTE) | Notes |
|---|:--:|---|
| 0 | 2–3 | Architect + 1–2 engineers + SDET for the PoC |
| 1 | 5–6 | Add SDETs, data, DevOps to build the harness |
| 2–3 | 8–9 (peak) | Full squad through the hardest contexts |
| 4–6 | 7–8 | Slight taper |
| 7 | 4–5 + client regulatory | Acceptance & hypercare; engineers wind down |
| 8 | 4–6 | Per-module continuations as needed |

Ramp in gradually; a full squad on day one burns money before the harness exists to make them productive.

---

## 7. Definition of Done (per context — the acceptance gate)

A context is accepted only when **all** hold:

- Golden vectors pass across the full product-configuration matrix, to the defined rounding tolerances.
- Property invariants hold (double-entry balances; principal amortizes to exactly zero; splits sum to the whole; no impossible negatives).
- A **clean shadow-parity window** on live/production-like traffic (e.g. N consecutive days with zero unreconciled differences).
- Reconciliation report signed off by the client Product Owner / regulatory liaison.
- Documentation, vectors and tooling committed to your repositories; rollback tested.

"Feature demoed" is **not** done. "Matches the incumbent, provably, and can be rolled back" is done.

---

## 8. Governance

- **Cadence:** weekly delivery sync; per-phase steering review at each gate.
- **Reporting:** burn-up against gates (not story points), parity dashboards from the harness, risk-register review.
- **RACI headline:** vendor is Responsible for build/test; client Product Owner is Accountable for scope/priority and Approves gates; regulatory liaison is Accountable for acceptance and FRC/audit.
- **Change control:** scope changes re-baseline the affected phase only, not the whole program — a benefit of the incremental structure.

---

## 9. Risk register (top items)

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Silently-wrong money math | Severe (financial + regulatory) | Med | Golden-vector harness as a hard gate; property tests; Fineract as oracle; parallel run before cutover |
| Vendor lacks true domain/test depth | High | Med | Paid PoC filter (G0); named key people; disqualify weak test culture |
| Key-person loss (Architect/SME) | High | Med | Named-person retention; deputies; pairing/KT from day one |
| Correctness tail overruns Phase 3/7 | Med (schedule/cost) | High | Buffer Phases 3 & 7; T&M not fixed-price; stop-point gates |
| Regulatory acceptance slips | Med | Med | Engage FRC/auditor early; client-owned regulatory liaison; realistic parallel-run window |
| Scope creep toward "whole Fineract" | Med (cost) | Med | Tier A vs Tier B split; each Tier-B module justified separately |
| Big-bang pressure to "just switch" | Severe | Low–Med | Contractual strangler + reversible per-context cutover; Fineract retained until last |
| Losing upstream Fineract patches | Med (long-term) | High (by design) | Accept consciously; own maintenance; keep contexts small and well-tested |

---

## 10. How to start (next 30 days)

1. Approve Tier-A-first scope and the strangler/T&M model.
2. Finalize the client-side Product Owner and regulatory liaison.
3. Issue the RFP built on the skills document's selection criteria.
4. Commission the **paid PoC** with the lead candidate(s) — the schedule-generator port + first harness slice. Let its result, not the sales deck, decide the award.

The PoC is the whole strategy in miniature: for the price of a few engineer-weeks you learn whether *this vendor* can hit financial parity before you commit years or money.

---

*This plan implements Option 4 (full native migration) from `gerege-nbfi-fineract-as-module-ideation.md`, executed by the strangler method so the "full" outcome is reached safely and incrementally rather than as a single bet.*
