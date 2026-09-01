# Gerege NBFI — Fineract → Go migration: development plan

> Generated 2026-09-01 from the repository state at commit `11512452`
> (`softhouse: release local fire lock (20260901-080005)`).
>
> Sources of truth read to produce this plan: `CLAUDE.md`, `.softhouse/RESUME.md`,
> `.softhouse/gates.md`, `.softhouse/gates-proposed-answers.md`,
> `.softhouse/program.json`, `.softhouse/tasks.json`,
> `.softhouse/state/DRIVER.STATE.json`, `.softhouse/reference-oracle.md`,
> `nexus/` (the Go module), and `docs/`.

---

## 1. What this project is (one paragraph)

Gerege NBFI is the **composition layer for a Mongolian NBFI core platform**, and the
home of the **Fineract → Go native migration** into `nexus/`. The target is the
**complete Apache Fineract codebase (~544k main Java LOC, 5,317 files)** ported to Go
behind a frozen adapter contract, worked in strangler order. "Correct" is defined
strictly as **parity with the Fineract reference oracle** on captured golden vectors,
under the production `MathContext` of **(19, HALF_UP)** and integer minor-unit money.

The migration is executed by the `softhouse` agent pipeline (plan → coder →
independent adversarial review → verify → merge → learn) under a daily scheduler. The
hard, non-negotiable guardrails are in `CLAUDE.md`: integer minor-unit money, a
double-entry append-only ledger with derived (never written) balances, mandatory
`Idempotency-Key` on every money-movement POST, Fineract-as-oracle, contract-first /
schema-first strangler migration, PostgreSQL as the **only** database (Oracle Database
is prohibited), and the Mongolian regulatory constraints (FRC, NBFI vs SCC, no deposit
insurance language, three-part names, 10-char national IDs, two no-DST time zones, no US
payment rails).

---

## 2. Current state — the facts this plan is built on

### 2.1 Migration progress

| Area | State |
|---|---|
| Contexts done | **1 of 17** — `tier0-harness-schedule-poc` (182 LOC, the progressive-loan embeddable schedule generator) |
| Context in progress | `tierA-gl-accounting`, slice `A2` (chart of accounts + product/account mapping + financial-activity accounts) |
| Pending contexts | 15 (see §6) |
| Go ported behaviour (non-test) | `loanschedule` 3,253 LOC + `ledger` 3,112 LOC |
| Conformance harness (Go) | 13,702 LOC across `loanschedule/conformance` and `ledger/conformance` (60 % of the Go tree — the grader is 1.5× the size of the port) |
| Frozen contract | DEC-1 rev 12 (schedule generator) in `nexus/internal/apps/loanschedule/contract/contract.go`; DEC-2 rev 8 (GL accounting) in `docs/adr/DEC-2-gl-accounting-adapter.md` |
| Golden vectors | 46 parity vectors / 7,884 cells (schedule) + 4 ledger parity / 2 oracle-refusal / 21 money cells (ledger) |
| Bar at HEAD | `bash .softhouse/conformance.sh` → EXIT 0, probe PRESENT `up`, PASS 46 / 7,884, frontier 11 == 11, deadOccurrences 108, 16 guards timed |

**The blunt number from G-20:** of the last ~1,204 commits over 7 days, 34.5 % were
capture artefacts and 2.8 % were `nexus/` (Go). Of 43 live tasks at the last measurement,
**none** ported new Fineract behaviour — 29 harness/process repairs, 11 reviews of those
repairs, 2 vector-store, 1 Go-harness. The pipeline is currently hardening the grader
faster than it uses it.

### 2.2 The three structural problems named for this plan

1. **Single-host oracle dependency.** The Fineract reference oracle is a Docker
   container bound to `localhost:8443` on Buyan's Mac, PostgreSQL 18.3 on
   `localhost:5432`, Docker daemon only on that host. The **only** fire that can
   capture vectors / run conformance is the local `launchd` agent (08:00 and 14:00
   Asia/Ulaanbaatar). The cloud routine (20:00) cannot reach it and parks vector work
   as `oracle_unreachable`. This is a bus-factor / availability single point of failure
   for the entire parity story.

2. **Missing pgx integration.** `program.json` declares `go_driver:
   github.com/jackc/pgx/v5`, but `nexus/go.mod` has **zero dependencies** (no `pgx`,
   no `go.sum`). The port is entirely in-memory behind repository interfaces
   (`MappingRepository`, `InMemoryFinancialActivityStore`, etc.) that are explicitly
   designed to be "swapped for a pgx-backed one" — but the pgx-backed implementation
   does not exist yet. Schema-first means the Go module must read the *same* PostgreSQL
   schema as the oracle for shadow-parity to be meaningful; today nothing in Go talks to
   PostgreSQL.

3. **Remaining tier migrations.** 15 contexts and ~543k LOC remain. The only completed
   context is the 182-LOC PoC. Tier A (money core) is ~186k LOC and every slice is
   `pending`.

### 2.3 Gate register (authoritative state)

Open gates, with their resolution path:

| Gate | Class | Blocks? | What it needs |
|---|---|---|---|
| **G-4** | ENGINEERING | No | **`user` gate** — DEC-1 wording amendment ("non-zero first segment" → "spans two calendar years of differing length") |
| **G-5** | ENGINEERING | No | **`user` gate** — DEC-1 zero-interest-rate self-contradiction amendment |
| **G-8** | ENGINEERING | No | **Agent/measurement** — rounding-floor phenomena. Not ready for a Buyan decision; must first close two named gaps (§5.3). Options (b)/(c) are hard `user` gates and must **not** be raised yet |
| **G-10** | ENGINEERING | No | **Agent decision** — driver recommends (c): take vectors only from products the oracle would still accept |
| **G-12** | ENGINEERING | No | **Agent decision** — recommend (a)+(b′); driver decides (option (c) is a hard `user` gate) |
| **G-19** | ENGINEERING | No | **Narrow `user` question** — is option (a) free, or a parallel-run hazard? (DEC-2 already ratifies (a)) |
| **G-20** | PRODUCT/ENG | No | **Agent policy** — every fire must dispatch ≥1 port/vector task before harness repair |
| **G-21** | ENGINEERING | No | **Agent** — correct/delete a falsified DEC-2 cardinal (60-of-60 now 91-of-109); extend casualty sweep to `docs/` |
| **G-22** | ENGINEERING | No | **Agent-prep + `user`** — DEC-2 amendment: new §4.4a "ORACLE-DERIVED COLUMNS" + I-5 correction (proposed rev at `docs/adr/DEC-2-PROPOSED-REVISION-T429-oracle-derived-columns.md`) |

Closed: G-1, G-2, G-3, G-6, G-7 (never allocated), G-9, G-11, G-13, G-14.

Hard `user` gates that remain for the whole program regardless of the table above:
**CUTOVER** of any context, **regulatory/parallel-run sign-off**, **deposit-taking
ACTIVATION** (porting savings is in scope; enabling it is not), and any **licence fact**.

---

## 3. Guiding principles for the plan

1. **Stop hardening the grader faster than the port.** Adopt G-20 as policy from the
   next fire: at least one port-or-vector task per fire, before any harness repair.
2. **Close the agent-decidable gates immediately.** G-10, G-12 (behaviour half), G-20,
   G-21, and the engineering half of G-19/G-22 are ENGINEERING/PRODUCT and should be
   decided, recorded in `.softhouse/gates-proposed-answers.md`, and acted on. Only the
   genuinely RESERVED items go to Buyan (G-4, G-5, the narrow G-19 question, G-22's
   amendment, and anything that is cutover/regulatory/licence).
3. **Make the oracle reproducible, not just running.** The single-host dependency is
   resolved by turning the oracle into a pinned, rebuildable, snapshot-backed artifact
   (§4), not by asking for a second always-on server.
4. **Schema-first before porting more.** pgx integration (§5) lands *before* the A1
   journal-posting engine, because A1 is the first context whose correctness only makes
   sense against a real PostgreSQL schema.
5. **One bounded context per run, strangler order, never cut over without vectors +
   shadow-parity + sign-off.** This is unchanged and is enforced by the pipeline.

---

## 4. Phase 1 — Remove the single-host oracle dependency

**Goal:** the reference oracle and its PostgreSQL database must be reproducible,
re-runnable, and shareable, so vector capture and conformance no longer depend on one
Mac being on, or one Docker daemon being alive.

### 4.1 Pin and snapshot the oracle state into the repository

- [ ] **A. Publish the oracle build recipe as code.** `build-oracle-image.sh` already
  builds `fineract:latest` from the pinned checkout. Make it the canonical, versioned
  path: add the pin (commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`) as an argument
  with a default, and verify the produced jar's `git.properties` matches the pin (the
  existing `commit_attestation` check) before tagging the image.
  - Owner: agent. Exit: `docker images fineract:latest` carries a build-attested pin.
- [ ] **B. Snapshot the PostgreSQL schema + seed as reproducible DDL/data.**
  The oracle uses `fineract_tenants`, `fineract_default`, `fineract_gerege` (281 tables
  each). Export the schema and the `gerege` tenant seed into the repo under
  `.softhouse/oracle/` (schema DDL + a minimal, FRC-clean seed — **no** production
  customer data), and add a `restore` script. This is what makes "same PostgreSQL
  schema" verifiable off-host.
  - Owner: agent. Exit: a fresh `postgres:18.3` container restores and serves the
    `gerege` tenant with the same 281-table public schema.
- [ ] **C. Add a compose profile that reproduces the whole oracle.** A single
  `docker compose` (PostgreSQL + Fineract on the postgresql profile) so a clean host
  runs `docker compose up` and gets an oracle. The non-negotiable already forbids the
  MySQL/MariaDB profiles; this makes the PostgreSQL profile the *only* one.
  - Owner: agent. Exit: `docker compose up` on a clean host yields a healthy oracle.

### 4.2 Decouple "capture" from "live container" via promoted vectors

- [ ] **D. Make the golden-vector store self-contained.** The `.softhouse/vectors/`
  store must be able to grade the Go module **without** a live oracle for the
  already-captured corpus. The live oracle remains required only for *new* captures.
  - Owner: agent. Exit: `bash .softhouse/conformance.sh` passes against the committed
    vector store with the oracle container stopped, and exits 2 (not PASS) only when a
    *fresh* capture is requested and the oracle is unreachable.
- [ ] **E. Record an oracle "moved" policy.** The pipeline already tracks
  ORACLE-STATE-MOVED. Formalise: any task that mutates the oracle must (1) list the
  blast radius and (2) promote/re-capture affected vectors before landing. This closes
  the recurring P-69 staleness class that produced G-21 and G-22.

### 4.3 Remove the host as a hard dependency for *new* captures

- [ ] **F. Containerise the Go toolchain + capture path.** The repo-local Go toolchain
  (`.softhouse/bin/go-env.sh`, `.softhouse/toolchain`) is host-installed. Put the Go
  build and the capture harness into the same reproducible image family so a capture run
  is `docker run`-able anywhere.
  - Owner: agent. Exit: `go build ./... && go test ./...` runs inside a pinned toolchain
    image, not a host `go`.
- [ ] **G. (Optional, `user` decision) Add a second oracle host.** If Buyan wants
  continuous capture when the Mac is offline, stand up a second host (or GitHub Actions
  runner) that runs the compose profile from §4.1.C. This is **RESERVED** only in the
  sense of spending money/infrastructure; otherwise it is engineering.
  - Owner: `user` (infra). Exit: cloud fire reports oracle REACHABLE.

**Exit criteria for Phase 1:** the oracle can be rebuilt and restored from the repo; the
existing vector corpus grades the port with no live oracle; and the only thing that still
requires the Mac is capturing *new* vectors (until §4.3.G is decided).

---

## 5. Phase 2 — pgx integration (schema-first storage layer)

**Goal:** give the Go module a real PostgreSQL read/write path via `pgx/v5`, matching
the adopted Fineract schema, so shadow-parity is possible and the port stops being
in-memory-only.

### 5.1 Add the dependency and establish the storage package

- [ ] **A. Add `github.com/jackc/pgx/v5`** to `nexus/go.mod` (generate `go.sum`).
  Pin the version. This is the only permitted Go→Postgres driver.
  - Owner: agent. Exit: `go mod tidy` clean, `go build ./...` green.
- [ ] **B. Create `nexus/internal/platform/postgres` (or `nexus/internal/pgx`)** with:
  - connection/pool management (`pgxpool`), DSN from config (never hard-coded offsets or
    creds in source);
  - an integer-minor-unit money codec for `bigint` columns — **no** `float4/float8/
    numeric→float` conversion in any money path;
  - a migration runner that applies the adopted Fineract DDL (from §4.1.B) into the Go
    module's own database.
  - Owner: agent. Exit: unit tests prove the money codec round-trips minor units and
    rejects non-integer/float inputs.

### 5.2 Implement pgx-backed repositories behind the existing interfaces

- [ ] **C. Replace the in-memory stores with pgx implementations** for the A2 surfaces
  already modelled in `nexus/internal/apps/ledger`:
  - `MappingRepository` (`mapping.go`) — reproduce the five named queries
    (`FindCoreProductToFinAccountMapping`, `FindByPaymentType`, `FindByCharge`,
    `FindChargeOffReasonMapping`, `FindWriteOffReasonMapping`) against
    `acc_product_mapping`;
  - `FinancialActivityRepository` (`financialactivity.go`);
  - `GLAccount` read surface (`glaccount.go`).
  - Owner: agent. Exit: the existing A2 conformance vectors pass with the pgx-backed
    repository pointed at a Postgres seeded from the oracle schema (identical results to
    the in-memory store), and the in-memory stores remain only as test doubles.

### 5.3 Model the G-12 ruling directly in the storage layer

- [ ] **D. Implement the G-12 decision** (recommended (a)+(b′), driver to decide):
  - derive every balance from append-only entries — **never** read
    `office_running_balance` / `organization_running_balance` /
    `is_running_balance_calculated`;
  - keep the three columns in the schema with their DDL defaults, **never** run an
    equivalent of `ACCOUNTING_RUNNING_BALANCE_UPDATE`;
  - add an explicit shadow-parity exclusion for those three columns, documented, so a
    row-level diff doesn't false-positive.
  - Owner: agent (decides) + `user` only if option (c) is contemplated. Exit: a
    row-level diff of Go-vs-oracle ignores exactly the declared columns and no others.

### 5.4 Close G-22's storage half and prepare its amendment

- [ ] **E. Add the `oracle-derived-columns` declaration as a first-class grader input.**
  The work exists (`.softhouse/vectors/oracle-derived-columns.json`, loaded by `Run`).
  Promote it into the pgx-backed comparator so a conforming port that does **not** produce
  the three oracle-derived balance columns is graded correct, not divergent.
  - Owner: agent. Exit: the grader asserts the 3 ORACLE_DERIVED / 7 PROVENANCE / 3
    GRADED / 18 GRADED_GAP split on every run, both directions.

**Exit criteria for Phase 2:** `go.mod` carries `pgx/v5`; the Go module reads the adopted
PostgreSQL schema through pgx-backed repositories and passes the A2 vectors; the G-12 and
G-22 storage rulings are encoded in code + grader, not just prose.

---

## 6. Phase 3 — Close the agent-decidable gates (unblock the port)

Ordered to unblock the most work first.

- [ ] **G-20 (policy) — decide now.** Adopt: "every fire dispatches ≥1 port/vector task
  before any harness repair." Record in `.softhouse/gates-proposed-answers.md`. This is
  the single highest-leverage change to invert the allocation ratio.
- [ ] **G-12 (behaviour) — decide (a)+(b′).** Record the decision and rationale
  (reject (c); import no recompute). This is ENGINEERING and already measured by `A2-29`.
- [ ] **G-10 — decide (c).** Record: take vectors only from products the oracle would
  still accept; no vector from a retyped-account product without explicit disclosure.
- [ ] **G-21 — correct/delete the DEC-2 I-5 cardinal.** Prefer deleting the
  live-oracle cardinal over refreshing it (revision 8's own lesson). Route through the
  gate because DEC-2 is ratified. `T395` extends the casualty sweep to `docs/`.
- [ ] **G-19 — decide the engineering half, ask only the narrow question.**
  Record that DEC-2 already ratifies option (a) (port refusal correct); capture
  `FU-T352-2` (can the oracle's own arithmetic *generate* residue?) to inform the
  parallel-run question; escalate only the parallel-run question to Buyan.
- [ ] **G-22 — prepare the DEC-2 amendment.** The proposed revision is already drafted
  at `docs/adr/DEC-2-PROPOSED-REVISION-T429-oracle-derived-columns.md`. Independently
  review it, land the code half (no ratified doc), and raise the doc amendment as a
  `user` gate.
- [ ] **G-8 — do NOT put options (b)/(c) to Buyan yet.** This is the one open gate that
  is deliberately *not* decided. The gate register states the precondition: close the
  two named gaps first —
  1. a verified **pre-rescue instalment `E`** (currently wrong on 3 cells);
  2. the **balance-reduction path** behind seven corpus cells.
  Until those are closed, the only statable region is the conservative superset
  `B_minor < 1.5·n` (resting on the unproven `δ ≤ 1`). Plan a dedicated measurement task
  to close both gaps, then restate the region and only then raise a decision if one is
  actually needed.

- [ ] **G-4 / G-5 — escalate to Buyan (RESERVED by procedure).** Both are wording-only
  DEC-1 amendments that an agent may not make. Package them together with the already
  recorded re-derivations so Buyan can sign them off in one pass. **They block nothing
  today** (the corrected wording already lives in the operational files).

**Exit criteria for Phase 3:** the only open ENGINEERING/PRODUCT gates are the ones that
genuinely need Buyan (G-4, G-5, G-8-if-it-ever-narrows-the-domain, G-19's narrow
question, G-22's amendment) — everything else is decided, recorded, and acted on.

---

## 7. Phase 4 — Tier A money core (the next actual porting work)

Strangler order is already fixed in `program.json`: **A2 → A1 → A3**, then the remaining
Tier A contexts. Follow `docs/agent-squad-delivery-and-scheduler.md` for checkpointing.

### 7.1 Finish `tierA-gl-accounting` (A2 → A1 → A3)

- [ ] **A2 (chart of accounts + product/account mapping + financial activity).**
  Close the remaining `pending`/`needs_retry` tasks in `tasks.json` (51 pending, 10
  needs_retry at last read), land the pgx-backed repositories from §5.2, and close the
  named gaps that G-20 listed: **accrual, account transfers (gl 17), charge-off,
  multi-currency, opening balances, `GLClosure`, slot resolution** — all currently
  "graded by nothing".
- [ ] **A1 (journal-entry posting — the double-entry engine, 11,535 LOC / 63 files).**
  Largest slice; the planner must check at plan time whether to split again (posting
  engine vs per-product accounting processors). This is the first context that *writes*
  money — it is where the G-12 derive-don't-store ruling, `Idempotency-Key`, and
  double-entry invariants become code, graded by captured vectors.
- [ ] **A3 (accruals, closure, provisioning, rules, retained earnings, trial balance,
  4,953 LOC / 69 files).** Depends on A1. Carries the `OBL-A3-1` ruling: derive the
  trial-balance closing balance, port no written-balance write path.

**Exit:** `tierA-gl-accounting` status `done` in `program.json`; ledger parity vectors
cover the six captured cases *and* the named gaps; every invariant green.

### 7.2 Remaining Tier A contexts (in dependency order)

| # | Context | LOC | go_target | Key note |
|---|---|---|---|---|
| 1 | `tierA-loan-product-schedule` | 20,461 | `nexus/internal/apps/loanproduct` | richest vector seam (7,863 test LOC) |
| 2 | `tierA-loan-lifecycle` | 106,246 | `nexus/internal/apps/loan` | **largest** — split by sub-behaviour: disbursement / repayment allocation / penalties-charges / rescheduling / write-off-delinquency |
| 3 | `tierA-charges-rates-tax` | 10,333 | `nexus/internal/apps/charges` | Mongolian VAT / e-Barimt is **additive** — spec it, don't invent parity vectors |
| 4 | `tierA-cob-batch` | 13,471 | `nexus/internal/apps/cob` | reuse Nexus scheduler, don't port Fineract's job framework |
| 5 | `tierA-provisioning-reporting` | 11,400 | `nexus/internal/apps/provisioning` | compliance-spine capital, 30 %/70 % limits reconcile to native GL |

**Exit for Tier A:** all six contexts `done` (porting sense only). **Cutover of Tier A
remains a hard `user` gate** requiring vectors + clean shadow-parity window +
FRC/parallel-run sign-off.

---

## 8. Phase 5 — Tier B business contexts (port in scope, activate selectively)

| # | Context | LOC | go_target | Key note |
|---|---|---|---|---|
| 1 | `tierB-savings-deposits` | 61,910 | `nexus/internal/apps/savings` | **ships DISABLED** behind a config flag default OFF; never render deposits as insured/protected/guaranteed; activation is a `user` licensing gate |
| 2 | `tierB-working-capital-loan` | 34,244 | `nexus/internal/apps/workingcapital` | split by sub-behaviour |
| 3 | `tierB-loan-origination` | 3,966 | `nexus/internal/apps/origination` | 1,657 test LOC as vectors |
| 4 | `tierB-investor` | 6,250 | `nexus/internal/apps/investor` | 3,748 test LOC |
| 5 | `tierB-branch` | 3,937 | `nexus/internal/apps/branch` | |
| 6 | `tierB-shares` | 9,412 | `nexus/internal/apps/shares` | member share capital feeds the compliance-spine capital figure |
| 7 | `tierB-collateral` | 5,511 | `nexus/internal/apps/collateral` | pledged-collateral holds alter **available** only — the exact defect that failed adversarial review twice on the sister project |
| 8 | `tierB-clients-groups` | 42,000 | `nexus/internal/apps/parties` | three-part names (ovog/patronymic/given), 10-char national ID, match on registration number |

---

## 9. Phase 6 — Tier C platform (map first, port only real gaps)

- [ ] **First run is an ANALYST GAP AUDIT, not a port.** For each subsystem (auth,
  tenancy, command bus, jobs, hooks, events, bulk import, campaigns, data queries, credit
  bureau, SMS/GCM, surveys, reporting mail) state what Nexus already provides vs what is
  a genuine gap. Only audited gaps get coder tasks.
- [ ] Port only demonstrated gaps; an unjustified plumbing port is a rejection.

---

## 10. Phase 7 — Tier D test corpus → vectors (opportunistic)

- [ ] Mine `integration-tests`, `fineract-e2e-tests-*`, and `**/src/test` (~321k LOC)
  into golden vectors. Runs opportunistically alongside each Tier A/B plan (the same
  run's `test_writer` mines that context's slice of the corpus). Never ported 1:1 into Go
  tests.

---

## 11. Phase 8 — Cutover, regulatory, and activation (hard `user` gates)

These are the stop-and-ask gates; the plan does not cross them.

- [ ] **Per-context CUTOVER** from Fineract to Go: vectors passing + clean shadow-parity
  window + regulatory/parallel-run sign-off.
- [ ] **FRC / external-audit acceptance** of the Tier A compliance spine (provisioning,
  reporting, capital ratios).
- [ ] **Deposit-taking ACTIVATION** decision (NBFI licence = prohibited; SCC = members
  only). The ported savings code stays disabled until Buyan settles the licensing
  position. The statutory citations are fixed in `CLAUDE.md` (NBFI Law Art. 12.1.3 /
  12.1.4; SCC Law).

---

## 12. Immediate next actions (the first week)

1. Recover any dead-dispatch WIP from the `20260901-080005` fire (see the STALE banner in
   `RESUME.md`) — reconcile `tasks.json` and set orphaned `in_progress` tasks to
   `needs_retry`.
2. Apply the G-20 policy and dispatch the first port/vector task (the Tier A named gaps
   are the ready candidates) before any further harness repair.
3. Decide and record G-12 and G-10 (agent-decidable).
4. Start Phase 1.A–1.C (oracle reproducibility) and Phase 2.A (add `pgx/v5`).
5. Package G-4 + G-5 for Buyan (they are the only two hard `user` gates currently
   blocking *nothing* but carrying ratified-doc defects).

---

## 13. Dependency and risk summary

- **Biggest schedule risk:** the grader-hardening loop (G-20). Mitigation is policy:
  invert the ratio from the next fire.
- **Biggest correctness risk:** cutting over any context without a clean shadow-parity
  window. Mitigation is the unchanged hard `user` CUTOVER gate.
- **Biggest availability risk:** the single-host oracle. Mitigation is Phase 1
  reproducibility + snapshot vectors.
- **Biggest integration risk:** porting more money behaviour before the pgx storage
  layer exists. Mitigation is sequencing Phase 2 before Tier A1.
- **Biggest regulatory risk:** any deposit-taking language or behaviour leaking into a
  live NBFI deployment. Mitigation is the config-disabled savings port and the
  "never insured/protected/guaranteed" rule.

---

## 14. What this plan deliberately does **not** do

- It does **not** authorise any CUTOVER, regulatory sign-off, or deposit-taking
  activation — those remain hard `user` gates.
- It does **not** put G-8 options (b)/(c) to Buyan — the two named gaps must be closed
  first.
- It does **not** introduce MySQL/MariaDB/Oracle or any non-PostgreSQL path — PostgreSQL
  via `pgx` only.
- It does **not** re-litigate ratified tenant parameters (NBFI licence, HALF_UP,
  precision 19) or the full-codebase scope.
