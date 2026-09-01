# Tier C — Analyst Gap Audit (map first, port only real gaps)

**Phase:** 6 (development_plan.md §9)
**Context:** `tierC-platform-map-first` (`.softhouse/program.json`)
**Deliverable:** this audit — no code ported.
**Method:** read the Go Nexus codebase (`nexus/`) as-is and the pinned Fineract
source, then for each of the 13 named subsystems state what Nexus already
provides and what is a genuine gap. Only gaps that pass this audit become coder
tasks.

## 1. Evidence and method

| Fact | Value |
|---|---|
| Nexus Go module | `/Users/buv/gerege-nbfi/nexus` — 210 `.go` files, `go 1.25.0`, sole direct dependency `github.com/jackc/pgx/v5 v5.10.0` (`go.mod`) |
| Nexus build | `go build ./...` exits 0 |
| Fineract oracle source | `/Users/buv/fineract`, pinned `426a23544e8426a38ae43ae404670a0a7e85b9eb` (`1.15.0-273-g426a235`, branch `develop`) |
| Tier C `fineract_paths` | `fineract-core`, `fineract-security`, `fineract-validation`, `fineract-command` (+ `-jdbc`, `-async`, `-audit`, `-disruptor`), `fineract-provider/.../infrastructure`, `.../organisation`, `.../useradministration`, `.../notification`, `.../template`, `.../adhocquery`, `.../interoperation`, `.../commands`, `fineract-document`, `fineract-db`, `fineract-client`, `fineract-avro-schemas` |
| Plan LOC claim | `~72k core + ~81k provider/infrastructure + ~10k organisation [VERIFIED: measured]` |

LOC figures below are measured from the pinned source (non-test `.java`, excluding
`build`/`target`/`Test.java`). They are order-of-magnitude context, not a port budget.

### 1.1 What the Tier C policy actually says

`.softhouse/patterns.md` (and `program.json` tierC notes) state the rule the audit
must apply:

> Tier C is map-first. `fineract-core` and `fineract-provider/infrastructure` are
> largely plumbing (auth, tenancy, command bus, jobs) that Nexus already provides.
> Port only a demonstrated gap, and the handoff must say what Nexus lacks. An
> unjustified plumbing port is a rejection.

**One correction to that premise is itself a finding of this audit.** The phrase
"that Nexus already provides" is only partly true today. Nexus provides the
*persistence platform* and the *domain apps* (ledger, loan, savings, …) plus a
*Close-of-Business orchestration model*. It does **not** yet provide auth, tenancy,
a command bus, a scheduler, hooks, an event bus, an audit trail, or any of the
notification / import / campaign / query / credit-bureau / survey / reporting-mail
subsystems. Those are genuine gaps — but the correct remedy for most of them is a
**minimal idiomatic Go primitive**, not a port of Fineract's Spring plumbing. That
distinction is the whole point of this document.

---

## 2. What Nexus actually provides today (ground truth)

This is the full platform surface, so each subsystem section can be read against it.

**`nexus/internal/platform/postgres`** — the only permitted persistence layer:

- `config.go` — `Config`, `ConfigFromEnv` (no hard-coded host/credential), `DSN()`,
  `NewPool` (pgx pool + ping). Single database, single schema.
- `query.go` — `Querier`/`Executor`/`DB` seams, `QueryRows`, `RowScanner`. Repos
  depend on these seams, never on a raw driver.
- `insert.go` — `InsertReturningInt64`.
- `migrate.go` — `RunMigrations`, a deliberately "dumb" version-ordered migration
  runner (no checksum, no lock, no out-of-order).
- `money.go` — `MinorUnit` integer money codec (`ParseMinorUnit`, `Format`,
  `ScanMinorUnit`) that refuses any float path.

**`nexus/internal/apps/*`** — domain contexts (business, not platform): `ledger`,
`loan`, `loanproduct`, `loanschedule`, `origination`, `savings`, `branch`, `charges`,
`provisioning`, `investor`, `workingcapital`, `shares`, `collateral`, `parties`, `cob`.

**`nexus/internal/apps/cob`** — Close-of-Business orchestration only: `Step[T]`,
`StepConfig`, `Config`, `Category`, `LockOwner`, `Run`, `Order`, and the Loan COB
job/step constants. Pure sequential pipeline; **no scheduler, no trigger, no job
registry** (see §4.4).

**`nexus/internal/apps/loan/event.go`** — `LoanEvent` enum *vocabulary* (the 31
lifecycle event names). It is a state-machine input, **not** an event bus.

**Not present anywhere in Nexus** (verified by grep + file listing): `func main`,
`net/http`/`http.Server`, any web framework, any scheduler, any event bus, any
`role`/`permission`/`appuser`/`staff`/`office` administration, any
`tenant` routing, any `datatable`/`adhoc`/`webhook`/`hook`/`sms`/`email`/`survey`/
`creditbureau`/`bulk` subsystem. The only `Password`/`User` in the codebase are the
PostgreSQL *connection* credentials (`platform/postgres/config.go`).

---

## 3. Executive summary (verdict table)

| # | Subsystem | Fineract LOC (meas.) | Nexus already provides | Genuine gap | Verdict |
|---|---|---|---|---|---|
| 1 | auth | ~12.3k (security 4.4k + user-admin 5.0k + core/provider security 2.9k) | nothing | identity + permission enforcement | **GAP — build idiomatic** |
| 2 | tenancy | ~3.7k (tenant/db/migration) | single-DB only | none for a single-tenant NBFI | **NOT A GAP (decision)** |
| 3 | command bus | ~7.6k (command 1.0k + core commands 6.6k) | per-app command/result shapes | uniform idempotency + audit envelope | **PARTIAL — minimal** |
| 4 | jobs | ~11.4k (jobs 8.2k + cob 3.2k) | cob orchestration | scheduler/trigger/job registry | **PARTIAL — small scheduler** |
| 5 | hooks | ~3.1k | nothing | outbound webhook (if needed) | **GAP — conditional** |
| 6 | events | ~7.9k | loan event vocabulary | publish/record + audit trail | **PARTIAL — minimal outbox** |
| 7 | bulk import | ~16.5k | nothing | offline import (feature) | **FEATURE — defer/decision** |
| 8 | campaigns | ~11.0k | nothing | campaign engine (feature) | **FEATURE — defer/decision** |
| 9 | data queries | ~11.3k | read seams only | datatables + ad-hoc query | **FEATURE — partial** |
| 10 | credit bureau | ~4.4k | nothing | Mongolia credit-bureau integration | **GAP — integration (likely required)** |
| 11 | SMS/GCM | ~6.0k | nothing | SMS notify; GCM likely not | **GAP — integration (SMS real)** |
| 12 | surveys | ~4.7k | nothing | survey/scorecard (feature) | **FEATURE — defer/decision** |
| 13 | reporting mail | ~4.1k | nothing | report export + SMTP mailer | **GAP — lightweight** |

Net: **0 of 13 are fully provided.** 5 are real gaps to build (auth, command bus,
jobs, credit bureau, reporting mail; plus conditional hooks and SMS), 3 are partial,
and 5 are product features that are **not** Tier C plumbing and should be deferred to
a separate product decision rather than auto-ported.

---

## 4. Per-subsystem findings

### 4.1 auth

- **Fineract:** `fineract-security` (Spring Security filter chain, basic auth,
  OAuth2/OIDC, JWT, two-factor, tenant-aware auth filters) + `useradministration`
  (`AppUser`, `Role`, `Permission`, `@Permission` annotations, password hashing) +
  `core`/`provider` security.
- **Nexus provides:** nothing. No security package, no identity/principal type, no
  role/permission model, no token/JWT/OIDC, no password handling, no permission
  check on any mutation. The domain apps are pure functions with no caller identity.
- **Genuine gap:** yes. Before any cutover of money behaviour there must be an
  identity concept (who is acting) and a permission gate (is the actor allowed to
  disburse/write-off/post). The journal-entry persistence already carries
  `createdby_id`/`lastmodifiedby_id` columns (`ledger/journalentry_postgres.go`) with
  no subsystem to populate them from.
- **Remedy / verdict:** **GAP — build idiomatic, do not port Spring Security.**
  A Go-native principal + permission-check interface is the deliverable. OIDC/JWT/
  two-factor are edge/transport concerns that belong at whatever HTTP boundary
  Nexus eventually exposes, not inside the domain library.

### 4.2 tenancy

- **Fineract:** schema-per-tenant (`fineract_tenants` registry + one DB schema per
  tenant), `TenantContext`/`ThreadLocalContextUtil`, `DataSourcePerTenantService`,
  per-tenant datasource routing, tenant-aware migration runner, per-tenant OIDC.
- **Nexus provides:** single-database `Config`/`NewPool` (`postgres/config.go`). No
  tenant registry, no per-tenant routing, no tenant context. The word "tenant"
  appears only in vector metadata describing the oracle (`ledger/conformance/
  oraclederived.go`), not as a subsystem.
- **Genuine gap:** **none for a single-tenant NBFI.** The deployment target is one
  tenant database (`fineract_gerege`). Porting `DataSourcePerTenantService` +
  schema routing would be an **unjustified plumbing port and a rejection**.
- **Remedy / verdict:** **NOT A GAP (decision).** Record a single-tenant assumption
  in `program.json` and, at most, thread a request-scoped org/tenant identifier
  through call sites if vector parity ever needs it. Do not build multi-tenant
  routing now.

### 4.3 command bus

- **Fineract:** `fineract-command` (`Command`, `CommandStore`, `CommandHandler`,
  `CommandDispatcher`, `CommandHookManager`) + `core/commands`
  (`CommandSource`, `CommandWrapper`, `CommandContext`, `CommandProcessingService`,
  JSON command serialization, `@CommandType` handlers) + `-jdbc`/`-async`/`-audit`/
  `-disruptor` variants.
- **Nexus provides:** per-app *command/result value shapes* — e.g.
  `ledger/journalentry.go` defines `PostingCommand`, `Poster`, `PostingResult`, and
  the development plan §7.1 already names `Idempotency-Key` as a posting invariant.
  But there is **no** shared command envelope, no dispatch mechanism, no command
  source/audit table, no idempotency enforcement layer.
- **Genuine gap:** a *uniform* mutation envelope carrying (a) an idempotency key and
  (b) an append-only command source record (who/when/what) that every money mutation
  routes through. This is a small, shared primitive — not Fineract's full Spring
  command framework.
- **Correction from oracle evidence:** `program.json` findings T390/T409 show the
  oracle's own scheduler **bypasses** the command bus (writes journal entries and
  running balances via raw `jdbcTemplate`, no `m_portfolio_command_source` row). So
  Fineract's command bus is **not** a complete mutation funnel; Nexus must not
  reproduce it as an assumed invariant. The audit-trail gap is real, but the
  "everything through the command bus" framing is falsified by the oracle.
- **Remedy / verdict:** **PARTIAL — build a minimal `platform/command` envelope**
  (idempotency key + source record), reuse the existing per-app command shapes. Do
  not port `fineract-command*`/`core/commands` wholesale.

### 4.4 jobs

- **Fineract:** `core`/`provider` `infrastructure/jobs` (`JobDetail`, `JobName`,
  `ScheduledJobRunnerService`, 41 jobs with `is_active`) + `fineract-cob` (Spring
  Batch partitioned COB) + `infrastructure/springbatch`.
- **Nexus provides:** the COB *orchestration* model (`cob/runner.go` `Run`/`Order`,
  `cob/loancob.go` step names and default order). `cob/doc.go` states it "reuses
  Nexus's existing scheduler" — **but no scheduler exists in Nexus** (no `func main`,
  no trigger, no registry, no status). That comment is aspirational, not factual.
- **Genuine gap:** a scheduler/trigger that fires the ported COB pipeline (and any
  future jobs), plus a job registry with on/off flag and run status. The plan
  (Phase 5/7.2, `tierA-cob-batch`) already rules: "reuse Nexus scheduler, don't port
  Fineract's job framework." That Nexus scheduler must be **built** — small and
  idiomatic — or delegated to an external trigger (cron/systemd).
- **Remedy / verdict:** **PARTIAL — build a minimal scheduler**, do not port Spring
  Batch/Quartz. The orchestration core is already done; the trigger is the gap.

### 4.5 hooks

- **Fineract:** `infrastructure/hooks` (`Hook`, `HookConfiguration`, `WebHookService`
  — outbound HTTP POST to a configured URL on named events) + hook registration API.
- **Nexus provides:** nothing. No webhook/hook abstraction.
- **Genuine gap:** only if the NBFI needs outbound callbacks (e.g. to a payment
  partner or integrator). The model is thin (~3k LOC, mostly CRUD/config).
- **Remedy / verdict:** **GAP — conditional.** Build a minimal outbound-webhook
  primitive only when a concrete integration demands it. Auto-porting it now would
  be unjustified plumbing.

### 4.6 events

- **Fineract:** `infrastructure/event` (business-event recording, `Audit`, Spring
  application event publishing/listeners) across core + provider.
- **Nexus provides:** the loan event *vocabulary* (`loan/event.go`, 31 `LoanEvent`
  names) used as state-machine inputs. No publish/subscribe, no event persistence,
  no audit trail, no outbox.
- **Genuine gap:** a cross-cutting publish/record seam so that a mutation can emit an
  event for audit and (later) for hooks/SMS triggers. Note the derive-don't-store
  ruling means Nexus should **not** replicate Fineract's audit-table machinery
  blindly; a minimal append-only outbox/audit append is the correct shape.
- **Remedy / verdict:** **PARTIAL — minimal outbox/audit append**, reusing the
  existing event vocabulary. Do not port the Spring listener/audit framework.

### 4.7 bulk import

- **Fineract:** `infrastructure/bulkimport` (~16.5k LOC, mostly workbook parsing +
  per-entity population) — template-based xlsx/csv import for clients, loans,
  repayments, etc.
- **Nexus provides:** nothing.
- **Genuine gap:** offline import is a **product feature**, not platform plumbing.
  Whether the NBFI needs it is a Buyan/product decision, not an engineering port.
- **Remedy / verdict:** **FEATURE — defer/decision.** If needed, build a minimal
  CSV/JSON import against the existing domain apps; do not port the 16k LOC workbook
  machinery.

### 4.8 campaigns

- **Fineract:** `infrastructure/campaigns` (~11.0k LOC) — SMS/email campaign engine,
  campaign messages, `BusinessRule`, scheduled triggers.
- **Nexus provides:** nothing.
- **Genuine gap:** a **product feature**. Not core to the compliance spine.
- **Remedy / verdict:** **FEATURE — defer/decision.** Do not port.

### 4.9 data queries

- **Fineract:** `infrastructure/dataqueries` (Datatables: entity-scoped custom
  fields via `m_datatable`, `EntityDatatableChecks`) + `adhocquery` (run reports /
  ad-hoc SQL).
- **Nexus provides:** the read seams (`postgres.QueryRows`, `Querier`), which are a
  foundation but **not** a user-definable datatable or ad-hoc query subsystem.
- **Genuine gap:** datatables (custom fields on entities) and ad-hoc query are real
  if the NBFI needs extensible client/loan fields or operator-run SQL. The seam
  exists; the feature does not.
- **Remedy / verdict:** **FEATURE — partial.** Datatables is a genuine extension
  feature; ad-hoc query is operational tooling. Defer to a product decision.

### 4.10 credit bureau

- **Fineract:** `infrastructure/creditbureau` (~4.4k LOC) —
  `CreditBureauConfiguration`, `CreditBureauLoanProductMapping`,
  `CreditBureauMasterData`, external credit-report integration at origination.
- **Nexus provides:** nothing.
- **Genuine gap:** yes, and Mongolia-specific — credit-bureau (CRC / credit
  information bureau) lookup is a realistic NBFI requirement at loan origination.
  This is an **integration feature**, not plumbing, and will need a concrete
  provider/contract to build against.
- **Remedy / verdict:** **GAP — integration (likely required).** Needs a product/
  provider decision before any coder task; do not port the abstract Fineract model
  without a live bureau contract.

### 4.11 SMS / GCM

- **Fineract:** `infrastructure/sms` (~2.0k) + `infrastructure/gcm` (~2.0k) +
  `notification` (core 0.1k + provider 2.0k) — SMS provider abstraction, GCM/FCM
  push, notification events/templates.
- **Nexus provides:** nothing.
- **Genuine gap:** SMS client notification is a realistic NBFI need; GCM/FCM push
  likely is not. SMS requires a provider (Twilio/MessageMedia/Mongolian gateway).
- **Remedy / verdict:** **GAP — integration (SMS real, GCM probably not).** Build a
  minimal SMS-send seam + template; defer GCM.

### 4.12 surveys

- **Fineract:** `infrastructure/survey` (~1.9k) + `spm` (~2.8k, Social Performance
  Management) — `Survey`/`Question`/`Scorecard`/`Response`.
- **Nexus provides:** nothing.
- **Genuine gap:** a **product feature** with no obvious NBFI-core dependency.
- **Remedy / verdict:** **FEATURE — defer/decision.** Do not port.

### 4.13 reporting mail

- **Fineract:** `fineract-report` (~0.3k — the report engine is external Pentaho) +
  `infrastructure/reportmailingjob` (~3.8k) — scheduled email of reports via SMTP,
  report run/export.
- **Nexus provides:** nothing.
- **Genuine gap:** report generation/export (CSV/PDF) and scheduled SMTP delivery is
  a real operational need (e.g. FRC/regulatory feeds). The heavy Pentaho engine is
  out of scope; the port-able part is the mail/export job.
- **Remedy / verdict:** **GAP — lightweight.** Build a CSV/PDF export + SMTP mailer;
  do not port Pentaho.

---

## 5. Qualified gaps (the only items that may become coder tasks)

Per the policy "only audited gaps get coder tasks," the following are the
audit-approved work items, in priority order:

1. **auth — idiomatic identity + permission enforcement** (build, not port).
2. **command bus — minimal `platform/command` envelope** (idempotency key + source
   record), reusing per-app command shapes.
3. **jobs — minimal scheduler/trigger + job registry** to fire the ported COB
   pipeline (build, not Spring Batch).
4. **events — minimal append-only outbox/audit seam** reusing the loan event
   vocabulary.
5. **credit bureau — integration** (requires a product/provider decision first).
6. **reporting mail — CSV/PDF export + SMTP mailer** (lightweight, no Pentaho).
7. **hooks — outbound webhook** (conditional on a concrete integration).
8. **SMS — send seam + template** (conditional; GCM deferred).

## 6. Explicitly NOT gaps (would be unjustified plumbing ports = rejections)

- **tenancy schema-per-tenant routing** — single-tenant NBFI; build none.
- **Fineract's Spring Batch / Quartz job framework** — replace with a minimal
  scheduler (the COB orchestration is already ported).
- **Fineract's Spring Security filter chain / OAuth2 / two-factor / JWT** — replace
  with an idiomatic identity + permission check at the future HTTP boundary.
- **Fineract's full command framework** (`fineract-command*`, `core/commands`) — the
  oracle itself bypasses it (T390/T409); reproduce only the idempotency + audit
  envelope.
- **bulk import workbook machinery (16.5k LOC), campaigns (11k), surveys/spm (4.7k),
  datatables/adhoc (unless custom fields are requested), GCM/FCM** — product
  features, deferred to a Buyan decision rather than auto-ported.

## 7. Open decisions to record before any coder task

1. Single-tenant assumption: confirm `fineract_gerege`-only and record it.
2. Credit bureau: name the live provider/contract (CRC or equivalent).
3. SMS: name the gateway provider.
4. Whether datatables (custom fields) is a genuine product requirement.
