# Tier C · Platform gap audit — Fineract's platform surface mapped onto Gerege Nexus

**Inventory and classification. Analyst output. No Go written, no port performed, no contract change.**

| | |
|---|---|
| Worker | `T489` |
| Branch | `softhouse/T489-tierC-platform-gap-audit` |
| Context | `tierC-platform-map-first` (`.softhouse/program.json`) |
| Reference oracle | Fineract reference implementation, pinned read-only checkout `/home/user/fineract` |
| Oracle commit | `426a23544e8426a38ae43ae404670a0a7e85b9eb` (2026-08-12 14:59:16 +0200); `git status --porcelain` **empty** at audit time (0 lines) |
| Nexus tree read | `nexus/` of this worktree at `0aed916db7cc1680b3fecd1e94159f3d33b08418` |
| Date | 2026-09-02 |

Throughout this document **"the reference oracle" means the Fineract implementation** we grade Go
output against. **"Oracle Database"** appears only as the name of the prohibited product (CLAUDE.md,
*PostgreSQL is the only database*). The two are unrelated.

---

## 0. How to read this document

The reviewer (`T492`) will re-derive every row against both trees. Four conventions to make that cheap:

- A claim with a bare `FILE:LINE` is a claim **about that line's text**, nothing more. Every such
  citation is a line this worker opened and read.
- **Every LOC figure in this document was measured by this worker**, with the recipe in §1.2. No
  figure is inherited from `program.json` or from another handoff. Where my figure disagrees with
  `program.json`, §1.2 says so.
- **"Not found" is a statement about the search.** Every GAP row names where in Nexus I looked.
- `[UNVERIFIED]` marks something I could not establish, with the reason. §9 collects them.
  §10 lists what I found outside the assigned scope. Nothing outside `docs/analysis/` and
  `.softhouse/handoff/` was written; the oracle checkout was never modified.

The classification vocabulary is CLAUDE.md's, plus one **marker** that is not a class:

| | |
|---|---|
| **NEXUS-PROVIDES** | Nexus already has it. Do not port. Requires a Nexus `FILE:LINE`. |
| **GAP** | Absent from Nexus, applicable to Gerege. Must be ported. |
| **PARTIAL** | Nexus has part of it. The row says which part, and which part is missing. |
| **NOT-APPLICABLE** | Fineract has it, Gerege will never need it. The row argues why. |
| **†** *(marker, not a class)* | **host-candidate**: the kind of plumbing a host platform normally supplies. Classified **GAP** on the evidence available, but **must be re-graded** before a port task is scheduled. See §2. |

---

## 1. Method

### 1.1 What I compared

Two trees, and only two:

1. **The reference oracle**, `/home/user/fineract`, pinned at the commit of record, read-only.
   Scope taken verbatim from the `tierC-platform-map-first` entry of `.softhouse/program.json`
   (its 20 `fineract_paths`); no path was added and none was dropped.
2. **Nexus**, the `nexus/` directory of this worktree — read as **code**, not as prose about code.
   `go list ./...`, `go.mod`, every non-test `.go` file's package declaration, and the full import
   surface (§3).

### 1.2 How I measured

Line counts are physical lines of `.java` files under a `src/main/` path, from the pinned checkout:

```
find <path> -name '*.java' -path '*/src/main/*' -exec cat {} + | wc -l
find <path> -name '*.java' -path '*/src/main/*' | wc -l
```

This counts blank lines, imports and the 18-line Apache licence header that every Fineract file
carries, so it is an **over-count of substance** and consistently so — which is what makes the
ratios in §7 usable. Test sources, `src/test/`, resources and generated code are excluded.

**The measured Tier C surface is 192,168 LOC in 2,235 files.** `program.json` records
`main_loc: 180000` for this context; the 12,168 difference is not investigated further — my number
is the one used throughout, and it is *larger*, so no row is understated by using it.

The partition in §6 is **exhaustive and non-overlapping over those 192,168 lines**: every row's
paths are disjoint from every other row's, and the rows sum to the total (the sum is shown, and a
273-line residual is carried explicitly rather than absorbed).

### 1.3 How I decided each class

- **NEXUS-PROVIDES** requires a Nexus `FILE:LINE` that I opened. No other evidence counts.
  Doctrine — CLAUDE.md, `.softhouse/patterns.md:81`, `docs/softhouse-engagement-plan.md:68` — is
  *not* evidence for this class. It is the reason the **†** marker exists.
- **GAP** requires (a) an argument that Gerege needs the behaviour and (b) a statement of where in
  Nexus I looked and did not find it. For every GAP row, "where I looked" is the same and is stated
  once, in §3.4: the whole readable Nexus tree, which is 70 files.
- **PARTIAL** requires citing the Nexus code that covers the covered part *and* naming the
  uncovered part concretely.
- **NOT-APPLICABLE** requires a per-row argument. Four argument shapes are used, and each row says
  which one it is using:
  - **(a) prohibited-engine** — support code for MySQL/MariaDB/Oracle Database (CLAUDE.md);
  - **(b) wrong-market** — implements a scheme, rail or vendor Gerege will not join;
  - **(c) JVM-artefact** — exists because Fineract is a Spring/JPA/Java application, and has no
    behaviour a vector could grade;
  - **(d) product-deferral** — a real feature, deliberately not launched with, under CLAUDE.md's
    *Answering gates*: "features deferred rather than shipped unvectored". Each (d) row records the
    cheaper replacement if the capability is later wanted, and each is reversible.

Shapes (a)–(c) are ENGINEERING/LEGAL calls with no discretion. Shape (d) is a PRODUCT call this
worker makes and records, per CLAUDE.md *Answering gates* — `chosen_by: agent`, Buyan retains veto.
§8 lists every (d) row in one place so a reversal is a one-line edit rather than a re-audit.

---

## 2. The finding that shapes every row: the Nexus platform tree is not in this repository

This audit was commissioned to "map onto Nexus first". **It cannot be completed as commissioned,
because the Gerege Nexus platform is not present in any tree this worker can read**, and this is
the single most important thing in the document.

What I looked for and where:

| Looked for | Where | Result |
|---|---|---|
| Nexus platform packages | `nexus/` — `go list ./...` | 6 packages, all under `internal/apps/{ledger,loanschedule}` (§3.1) |
| A second Go module | `find / -name go.mod` outside the pinned Fineract checkout | only `/usr/local/go*/…` (the Go toolchain) and `nexus/go.mod` |
| A submodule or vendored tree | `.gitmodules` in the worktree root | **absent** — no submodules |
| Any Go source outside `nexus/` | `find . -name '*.go' -not -path './nexus/*'` | 7 files, all one-off probes and guards under `.softhouse/` |
| A dependency on an external Nexus library | `nexus/go.mod` | **zero `require` directives.** Standard library only. |

`nexus/go.mod` is three lines: `module github.com/gerege/nexus`, blank, `go 1.23`. There is no
`pgx`, no HTTP router, no auth library, no configuration library, no scheduler — because there are
no dependencies at all.

**Consequence, stated plainly.** The claim that "Nexus already provides auth, tenancy, command bus,
jobs" appears in the program's own doctrine — `.softhouse/patterns.md:81` ("largely plumbing … that
Nexus already provides") and `docs/softhouse-engagement-plan.md:68` ("reusing Nexus's scheduler
rather than porting Fineract's job framework"). **It is not verifiable from any tree available to
this run**, and CLAUDE.md's honesty rules forbid me from converting doctrine into a
NEXUS-PROVIDES row. A false NEXUS-PROVIDES silently drops a subsystem out of the migration.

So: **this audit records zero NEXUS-PROVIDES rows.** Everything doctrine would place there is
classified **GAP** and marked **†** — host-candidate — meaning: *do not schedule a port task for
this row until someone re-grades it against the real Nexus platform tree.* §7 quantifies exactly how
much of Tier C hangs on that re-grade, and it is the largest single number in the document.

> **Recommendation R-1, and the program's cheapest next action.** Attach the Gerege Nexus platform
> repository to a session and re-grade the 7 **†** rows in §6 (50,846 LOC, 26.5% of Tier C). Until
> that happens the program cannot tell the difference between "Tier C costs 33k LOC" and "Tier C
> costs 84k LOC" — a 2.5× spread on the largest remaining unported context. Every other
> recommendation in this document is worth less than this one.

---

## 3. The Nexus inventory — what is actually there

### 3.1 Packages

`go list ./...` from `nexus/` returns exactly six:

```
github.com/gerege/nexus/internal/apps/ledger
github.com/gerege/nexus/internal/apps/ledger/conformance
github.com/gerege/nexus/internal/apps/loanschedule
github.com/gerege/nexus/internal/apps/loanschedule/conformance
github.com/gerege/nexus/internal/apps/loanschedule/conformance/cmd/conformance
github.com/gerege/nexus/internal/apps/loanschedule/contract
```

70 `.go` files, 40,242 total lines, of which **25,628 lines are non-test**. Of that non-test total,
the two `conformance` packages account for roughly 15k — i.e. **the majority of Nexus's non-test Go
code is the golden-vector conformance harness, not product code.**

### 3.2 What the two product packages contain

| Package | Non-test content |
|---|---|
| `internal/apps/loanschedule` | `emi.go` (2,294), `generator.go` (770), `rounding.go`, plus `contract/contract.go` (2,548) — the DEC-1 frozen adapter contract |
| `internal/apps/ledger` | `glaccount.go`, `slots.go`, `resolve.go`, `mapping.go`, `financialactivity.go`, `producttype.go`, `accountingrule.go`, `money.go`, `apishape.go`, `errors.go`, `doc.go` |

Both are **Tier 0 / Tier A domain work** — the schedule-generator PoC and the GL/accounting slice.
Neither is platform.

### 3.3 The one thing Nexus does provide that a Tier C row depends on

**Exact money arithmetic.** This is the only citable NEXUS evidence in the audit, and it supports
one PARTIAL row (§6, row P1):

- `nexus/internal/apps/loanschedule/rounding.go:3` — the package imports `math/big` and nothing
  else; `rounding.go:7-12` states that every quantity is either an `int64` count of minor units or
  an exact `math/big.Rat`, "no binary fraction type anywhere on this path".
- `rounding.go:20-24` implements the two distinct senses in which the reference oracle reads a
  `MathContext`: `roundSignificant` (significant decimal digits, i.e. `BigDecimal.multiply(x, mc)`)
  and `roundScale` (decimal places, i.e. `BigDecimal.setScale(n, mode)`).
- `rounding.go:30-34` records HALF_UP as the only implemented tie-break — "Fineract's RoundingMode
  ordinal 4 and Gerege's ratified tenant mode" — and states that every other mode is refused before
  the generator runs.
- `nexus/internal/apps/ledger/money.go:10-19` records that the oracle's money columns are
  `DECIMAL(19,6)` while MNT's minor unit is 2, and that
  `MinorUnitsFromDecimalText` converts **exactly or errors** — no truncation, no silent scaling.

That is the Go-side counterpart of Fineract's `MoneyHelper`
(`fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/MoneyHelper.java`,
whose `PRECISION = 19` and `(19, HALF_UP)` `MathContext` are already ratified in CLAUDE.md).

### 3.4 Where I looked, for every GAP row

For each GAP row below, "absent from Nexus" means: **absent from all 70 files of `nexus/`.** I read
every package declaration, every non-test filename, and the complete deduplicated import surface of
the tree. That surface contains no HTTP package, no `database/sql`, no `net/http`, no third-party
import of any kind — only `bytes`, `context`, `crypto/sha256`, `encoding/hex`, `encoding/json`,
`errors`, `flag`, `fmt`, `go/parser`, `go/scanner`, `go/token`, `io`, `io/fs`, `math`, `math/big`,
`os`, `path/filepath`, `regexp`, `runtime`, `sort`, `strconv`, `strings`, `sync`, `testing`, `time`,
and the four internal `github.com/gerege/nexus/...` packages. A subsystem that needs a socket, a
database connection or a clock-driven scheduler **cannot** be present in this tree.

---

## 4. The Tier C surface, measured

The 20 declared `fineract_paths` resolve to four groups. `fineract-db` contains **no Java at all**
(§5.7); every other path contributes.

| Group | Files | LOC |
|---|---|---|
| `fineract-core` | 795 | 71,833 |
| `fineract-provider/…/infrastructure` | 903 | 81,148 |
| `fineract-provider/…/{organisation, useradministration, notification, template, adhocquery, interoperation, commands}` | 422 | 25,723 |
| Standalone modules: `fineract-security`, `-validation`, `-command{,-jdbc,-async,-audit,-disruptor}`, `-document`, `-db`, `-client`, `-avro-schemas` | 115 | 13,464 |
| **Total** | **2,235** | **192,168** |

---

## 5. Findings that change how rows are classified

### 5.1 Oracle Database does not appear in Fineract at all — the prohibition costs nothing here

`DatabaseType.java:21-25` (`fineract-core/.../infrastructure/core/service/database/DatabaseType.java`)
declares exactly two constants: `MYSQL` and `POSTGRESQL`. `DatabaseTypeResolver.java:31-33` maps
four driver class names — `org.mariadb.jdbc.Driver`, `com.mysql.jdbc.Driver`,
`com.mysql.cj.jdbc.Driver` → `MYSQL`; `org.postgresql.Driver` → `POSTGRESQL` — and
`DatabaseTypeResolver.java:48-52` **throws** for anything else.

A repo-wide `grep -rnE "ojdbc|oracle\.jdbc|OracleDialect|:1521"` over `fineract-core/src/main`,
`fineract-provider/src/main`, `fineract-security`, `fineract-command*` and `fineract-document`
returns **only false positives** — every hit is the substring `oJdbc` inside a Java method name
(`toJdbcUrl`, `toJdbcValue`). A case-insensitive search for the bare word `oracle` under
`.../core/service/database/` returns nothing.

**So there is no Oracle Database support code in Tier C to exclude.** The prohibition is satisfied
by construction. What *does* exist is MySQL/MariaDB support, and that is a genuine
NOT-APPLICABLE(a) — see row N8.

### 5.2 Idempotency: Fineract has it, and its semantics diverge from ours in one load-bearing way

CLAUDE.md: *"`Idempotency-Key` is mandatory on every money-movement POST."* Fineract's
implementation of that header lives in the legacy command path and is portable:

- `fineract-core/.../commands/service/IdempotencyKeyResolver.java:35-36` — `resolve(CommandWrapper)`.
- `fineract-core/.../commands/service/CommandSourceService.java:66-73` — `saveInitial(...)` persists
  the command *in its own transaction* and throws
  `IdempotentCommandProcessUnderProcessingException` when the key is already in flight;
  `CommandSourceService.java:101-103` looks a command up by
  `(actionName, entityName, idempotencyKey)` — the **key is scoped to the action and entity**, not
  global.
- `fineract-core/.../infrastructure/core/filters/IdempotencyStoreFilter.java` (74 lines),
  `IdempotencyStoreBatchFilter.java` (63), `IdempotencyStoreHelper.java` (63) — the servlet-filter
  side that writes the stored response back.
- The newer bus carries it too: `fineract-command/.../core/CommandProperties.java:50` sets
  `idemPotencyKeyHeaderName = "Idempotency-Key"`, `.../hook/ServletHeadersCommandHook.java:50-51`
  reads the header onto the command, and `fineract-command-jdbc/.../store/JdbcCommandStore.java:81-94`
  fetches request, response and state by key.

**The divergence.** `IdempotencyKeyResolver.java:36` reads (one line, wrapped here):

```java
return Optional.ofNullable(wrapper.getIdempotencyKey())
        .orElseGet(() -> getAttribute().orElseGet(idempotencyKeyGenerator::create));
```

When the caller supplies no key, Fineract **generates one**. Under CLAUDE.md the header is
*mandatory*: a money-movement POST without it must be **refused**. The Go port must therefore
diverge deliberately at this line, and — this is the part that matters for the harness — **the
reference oracle cannot supply a golden vector for the refusal**, because the oracle never refuses.
The refusal is a Gerege-side invariant, gradeable only by a property test.

The newer `fineract-command` bus should not be mistaken for a finished idempotency implementation:
`fineract-command/src/test/java/.../CommandSampleApiTest.java:130` is annotated
`@Disabled // TODO: implement idempotency properly with backwards compatibility`.

### 5.3 Two-field names are baked into three Tier C subsystems

CLAUDE.md: *"Names are three fields — ovog (clan), patronymic, given name. Never `first_name`/`last_name`."*
Inside Tier C, three places violate this and each is a schema-level decision, not a rendering one:

| Where | Evidence |
|---|---|
| Platform user | `fineract-core/.../useradministration/domain/AppUser.java:73-78` — `@Column(name = "firstname" …)` / `@Column(name = "lastname" …)`, both `nullable = false` |
| Staff / loan officer | `fineract-core/.../organisation/staff/domain/Staff.java:41-45` — same two columns |
| Bulk import templates | `fineract-provider/.../infrastructure/bulkimport/constants/ClientPersonConstants.java:27` — `FIRST_NAME_COL = 0` |

This collides with **"adopt Fineract's PostgreSQL schema"** (CLAUDE.md, *Contract-first,
schema-first*): `m_appuser.firstname` / `m_staff.firstname` are columns of the schema being adopted.
The port cannot satisfy both rules silently. **This is a contract question, and a contract change is
a `user` task** — I raise it as gate **G-C1** (§8) rather than deciding it.

### 5.4 Time zones: Fineract's model is per-tenant, and Gerege needs per-office

`fineract-core/.../infrastructure/core/service/DateUtils.java:65-67`:

```java
public static ZoneId getDateTimeZoneOfTenant() {
    …
    return ZoneId.of(tenant.getTimezoneId());
}
```

The zone is an **IANA identifier read from tenant configuration** — so CLAUDE.md's "never hard-code
an offset" is already satisfied by the design, and `Asia/Ulaanbaatar` / `Asia/Hovd` both fit.
`DateUtils.java:69-88` derive business `LocalDate` / `LocalDateTime` / `OffsetDateTime` from it.

But the zone lives on the **tenant**, not the office:
`fineract-provider/src/main/resources/db/changelog/tenant-store/parts/0001_initial_schema.xml:77`
declares `timezone_id VARCHAR(100)` on the tenant-store table, and
`fineract-core/.../organisation/office/domain/Office.java` has **no** timezone column (a
case-insensitive grep for `zone` over that file returns nothing).

**Consequence.** A single Gerege deployment with an Ulaanbaatar head office (+08) and a Hovd branch
(+07) has **one** tenant and therefore **one** zone in Fineract's model. Either every office shares
the head-office zone, or `timezone_id` moves onto `m_office` — a schema change. This is
`GAP-real` work inside row G9 (organisation), it is not plumbing, and no host platform will supply
it. Recorded as backlog **B-2** (§10).

### 5.5 `fineract-client` is a generated Java SDK, not platform

`fineract-client/build.gradle` applies `org.openapi.generator` with `generatorName = 'Fineract'`;
the checked-in sources are hand-written adjuncts (`util/FineractClient.java`, `util/Calls.java`,
`services/DocumentsApiFixed.java`). It is a **Java library for calling Fineract over HTTP**. The Go
module does not port another language's client SDK, and the boundary the program actually cares
about is the frozen adapter contract (DEC-1 / DEC-2). NOT-APPLICABLE(c).

### 5.6 Four subsystems inside Tier C's paths belong to Tier A or Tier B, and are being counted twice

Tier A/B contexts declare their `fineract_paths` under `fineract-provider/.../portfolio/*` and
`fineract-provider/.../accounting/*`. But Fineract splits every one of those Java packages across
Gradle modules — the pattern `tierA-a2-behaviour.md` §1.2 already recorded for `glaccount`. The
`fineract-core` halves therefore fall inside Tier C's `fineract-core` path while being Tier A/B
domain code:

| Path | LOC | Actually belongs to |
|---|---|---|
| `fineract-core/.../portfolio` (savings 8,048; calendar 3,056; client 2,685; group 2,317; search 1,271; paymenttype 1,146; +16 more) | 23,652 | `tierB-savings-deposits`, `tierB-clients-groups`, `tierA-*` |
| `…/infrastructure/dataqueries` (core 1,749 + provider 8,295) | 10,044 | `tierA-provisioning-reporting` — which **already names** `fineract-provider/…/infrastructure/dataqueries` in its own `fineract_paths` |
| `fineract-core/.../batch` | 1,932 | `tierA-cob-batch` |
| `fineract-core/.../accounting` | 1,897 | `tierA-gl-accounting` |
| **Total double-counted** | **37,525** | |

`dataqueries` is an outright duplicate: it is listed by `tierA-provisioning-reporting` **and** falls
inside Tier C's `fineract-provider/.../infrastructure` path. The other three are the module-split
pattern. **Tier C should not carry any of these 37,525 lines**, and the Tier A/B contexts should
have the `fineract-core` halves added to their `fineract_paths` — otherwise they will be ported
without their own entities, exactly as `tierA-a2-behaviour.md` §1.2 warned. Recorded as **B-1**.

### 5.7 `fineract-db` contains no Java, and the real schema is 93,498 lines of Liquibase XML

`fineract-db/` holds `mifospltaform-tenants-first-time-install.sql`, `old-schema-files/` and
`multi-tenant-demo-backups/` — MySQL-dialect dumps and demo tenant backups.
`find fineract-db -name '*.java'` returns **zero files**.

The schema Gerege actually adopts lives elsewhere:
`fineract-provider/src/main/resources/db/changelog/` — **271 files, 93,498 lines of Liquibase XML**,
split `tenant/` and `tenant-store/`. It is *not* part of the 192,168 Java LOC and never was.

**This is not a port at all.** CLAUDE.md says *adopt Fineract's PostgreSQL schema* — so the
changelog is an **operational artefact that is run, not translated**. Go's job is to read the tables
Liquibase creates, via `pgx`. Any task that proposes rewriting 93k lines of changelog into Go
migrations is a rejection under the same rule that rejects unjustified plumbing ports.

---

## 6. The classification table

One row per subsystem. `LOC` is this worker's measurement (§1.2). Rows are disjoint and exhaustive
over the 192,168 lines; the sum is checked at the foot of the table.

### 6.1 Reassign — misfiled Tier A/B domain code (not Tier C's to port)

| # | Subsystem | Fineract path | LOC | Class | Evidence / justification |
|---|---|---|---|---|---|
| R1 | Shared portfolio domain | `fineract-core/…/portfolio` | 23,652 | **reassign** | 22 sub-packages, all domain (savings 8,048, calendar 3,056, client 2,685, group 2,317). Same module-split pattern as `tierA-a2-behaviour.md` §1.2. Belongs to `tierB-savings-deposits` / `tierB-clients-groups` / Tier A. |
| R2 | Data queries / datatables / reports | `…/infrastructure/dataqueries` (core + provider) | 10,044 | **reassign** | `tierA-provisioning-reporting.fineract_paths` **already lists** `fineract-provider/…/infrastructure/dataqueries`. Outright duplicate. |
| R3 | Batch API domain | `fineract-core/…/batch` | 1,932 | **reassign** | Belongs to `tierA-cob-batch` (`fineract-provider/…/batch` is already in its paths). |
| R4 | Accounting domain types | `fineract-core/…/accounting` | 1,897 | **reassign** | Belongs to `tierA-gl-accounting`; `tierA-a2-behaviour.md` §1.2 already ports from here. |
| | **Subtotal** | | **37,525** | | |

### 6.2 NOT-APPLICABLE

| # | Subsystem | Fineract path | LOC | Shape | Justification (evidence) |
|---|---|---|---|---|---|
| N1 | Bulk import / export | `…/infrastructure/bulkimport` (core + provider) | 16,484 | (d) | Apache POI spreadsheet plumbing — **410** `org.apache.poi` references across the package; 17 per-entity `*Constants.java` column maps and matching `importhandler/` + `populator/` pairs. It is a **file-format adapter over the same command API**, so no vector exists for it that is not already a command vector, and it carries the two-name defect (`ClientPersonConstants.java:27`). **Replacement if wanted:** a CSV/XLSX loader calling the ported command API — order 1–2k LOC, not 16.5k. Largest single saving in the audit. |
| N2 | SMS / email campaigns | `…/infrastructure/campaigns` | 11,027 | (d) | Campaign scheduling with report-driven recipient selection (`campaigns/{sms,email,jobs,helper}`). Marketing, not banking behaviour; depends on N10/R2. Deferred, reversible. |
| N3 | External event delivery (Kafka / JMS / Avro) | `…/infrastructure/event/external` (core + provider) | 5,922 | (d) | `ExternalEventKafkaConfiguration.java`, `KafkaExternalEventProducer.java`, `ExternalEventJMSConfiguration.java`, `JMSMultiExternalEventProducer.java` — an outbox publishing Avro payloads to a broker. Nothing downstream consumes it at Gerege today. **The in-process half is a different row (G12) and is kept.** |
| N4 | Credit bureau integration | `…/infrastructure/creditbureau` | 4,364 | (b) | Token + report storage around a specific external bureau HTTP API (`CreditBureauToken`, `CreditReport`, `CreditBureauIntegrationApiResource`). Mongolia's bureau is not the one modelled `[UNVERIFIED: which bureau — §9 U-2]`. The *capability* (pull a report before origination) belongs to `tierB-loan-origination`, not to a Tier C plumbing port. |
| N5 | Interoperation (FSP interop scheme) | `…/interoperation` (core + provider) | 4,248 | (b) | `InteropIdentifierRequestData`, `InteropQuoteRequestData`, `InteropTransactionData`, `InteropKycData` — the quote/transfer/party-lookup shape of an inter-FSP scheme. Mongolia's rails are **RTGS (Banksuljee)** above MNT 5,000,000, **ACH+** at or below, **NETC** for cards. Fineract has no code for any of them, so this row is not a substitute for that work — it is a different scheme entirely. |
| N6 | Scheduled report mailing | `…/infrastructure/reportmailingjob` | 3,831 | (d) | Emails report output on a cron. Depends on R2 and on SMTP config. FRC reporting is a Mongolia-specific requirement with no Fineract source; building this first would be building the wrong thing. |
| N7 | Outbound hooks | `…/infrastructure/hooks` (core + provider) | 3,128 | (d) | `HookProcessorProvider.java:41-45` dispatches to `twilioHookProcessor`, `webHookProcessor`, `elasticSearchHookProcessor` — two vendor bridges and one generic webhook. **Replacement if wanted:** an HTTP subscriber on the G12 event bus, order 200 LOC. |
| N8 | DB dialect abstraction + per-tenant datasource routing | `fineract-core/…/infrastructure/core/service/database` | 2,605 | (a) + (d) | **(a)** `DatabaseType.java:21-25` = `{MYSQL, POSTGRESQL}`; `DatabaseTypeResolver.java:31-33` maps mariadb/mysql drivers; `MySQLQueryService.java` (73) and the dialect branches of `DatabaseSpecificSQLGenerator.java` (369) exist only for a prohibited engine. Go speaks Postgres via `pgx`; the abstraction has nothing left to abstract. **(d)** `RoutingDataSource.java:49,108-115` resolves a datasource from `ThreadLocalContextUtil.getTenant()` — multi-tenant routing (~896 LOC with `DataSourcePerTenantServiceFactory`, `TomcatJdbcDataSourcePerTenantService`, `FineractPlatformTenant{,Connection}`) that a single-licensed-entity deployment does not use. **Residue kept elsewhere:** `JavaType.java` (369), `JdbcJavaType.java` (362), `SqlOperator.java` (220) are Postgres-relevant datatable type mapping and follow R2 into `tierA-provisioning-reporting`. |
| N9 | Entity-to-entity access mapping | `…/infrastructure/entityaccess` | 2,382 | (d) | An optional office↔product visibility matrix (`FineractEntityToEntityMapping`, `FineractEntityAccessType`), gated by global configuration and off by default. If branch-scoped product visibility is wanted it is a policy rule in `tierB-branch`, not a 2.4k-LOC subsystem. |
| N10 | SMS gateway bridge | `…/infrastructure/sms` | 1,993 | (d) | Outbound message bridge to a gateway. A Mongolian aggregator integration is a few hundred lines against a documented API; porting Fineract's bridge buys nothing. |
| N11 | Server-side document templates | `…/template` | 1,971 | (d) | Mustache-style templates rendered by the platform. Deferred; small and reversible. |
| N12 | Push notification (FCM) | `…/infrastructure/gcm` | 1,954 | (b)+(c) | A hand-rolled HTTP shim for Google Cloud Messaging: `gcm/domain/Sender.java:106` "FCM Server Key obtained through the Firebase Web Console", `NotificationConfigurationData.java:33` `fcmEndPoint`. Re-porting a decade-old protocol shim instead of using a maintained client is waste. |
| N13 | SPM surveys | `…/infrastructure/survey` | 1,944 | (d) | Social-performance / poverty-scorecard surveys — a microfinance-donor reporting feature. No FRC requirement identified `[UNVERIFIED: §9 U-3]`. (Note: `fineract-provider/…/spm` is a *different*, second survey feature and belongs to `tierA-provisioning-reporting`.) |
| N14 | Generated Java client SDK | `fineract-client` | 1,530 | (c) | §5.5. `build.gradle` applies `org.openapi.generator`. A Go module does not port a Java SDK; the contract boundary is DEC-1/DEC-2. |
| N15 | Spring Batch glue | `…/infrastructure/springbatch` (core 60 + provider 1,296) | 1,356 | (c) | Step-scope, partitioning and `JobRepository` wiring for a specific JVM framework. **The capability** (ordered, restartable, chunked execution) is not dropped — it reappears in G4. |
| N16 | Ad-hoc query | `…/adhocquery` | 1,289 | (d)+(c) | Stores user-supplied SQL and runs it on a schedule. Fineract carries `SqlInjectionPreventerServiceImpl` (in `fineract-security`) precisely because of this family of features. Re-implementing an arbitrary-SQL execution surface in a ledger system is a security regression, not a port. |
| N17 | Teller / cashier management | `…/organisation/teller` | 1,225 | (d) | Till allocation and cashier cash management. Not required for an NBFI lending launch; deferred. |
| N18 | Cache abstraction | `fineract-core/…/infrastructure/cache` | 786 | (c) | Ehcache/no-op `CacheManager` selection for a Spring application. |
| N19 | Instance mode | `…/infrastructure/instancemode` (core + provider) | 279 | (c) | Read/write/batch instance gating for a horizontally split Fineract deployment. Nexus is a single binary. |
| N20 | OpenAPI doc customisation | `…/infrastructure/openapi` | 240 | (c) | Swagger customisation for the JAX-RS layer. |
| N21 | Patched Spring Batch classes | `fineract-core/src/main/java/org/springframework/batch/…` | 134 | (c) | Two classes (`StepSynchronizationManager`, `JobSynchronizationManager`) placed in Spring's own package to patch the framework. Not Fineract behaviour. |
| N22 | Avro schema generator | `fineract-avro-schemas` | 28 | (c) | One `ByteBufferSerializable` interface plus Velocity code-generation templates. Follows N3. |
| | **Subtotal** | | **68,720** | | |

### 6.3 PARTIAL

| # | Subsystem | Fineract path | LOC | Class | What Nexus covers / what it does not |
|---|---|---|---|---|---|
| P1 | Money & currency | `…/organisation/monetary` (core 2,049 + provider 141) | 2,190 | **PARTIAL** | **Covered, with evidence:** exact decimal arithmetic at `(19, HALF_UP)` — `nexus/internal/apps/loanschedule/rounding.go:3,7-12,20-24,30-34` (int64 minor units or `math/big.Rat`; `roundSignificant` vs `roundScale`; HALF_UP only, every other mode refused) and `nexus/internal/apps/ledger/money.go:10-19` (`MinorUnitsFromDecimalText` converts exactly or errors, no silent scaling from the oracle's `DECIMAL(19,6)`). **Not covered:** the `ApplicationCurrency` registry and its API (which currencies a tenant has enabled, decimal places, `inMultiplesOf`, display symbol), the `MonetaryCurrency`/`Money` value objects the domain passes around, and `MoneyHelper`'s tenant-rounding-mode initialisation. Estimated remainder ≈ 1,800 of the 2,190 LOC. **Do not schedule this as a fresh port** — it is an extension of ported code. |
| | **Subtotal** | | **2,190** | | |

### 6.4 GAP

**†** = host-candidate: classified GAP on the evidence available (§2), but re-grade against the real
Nexus platform tree before scheduling a port task.

| # | Subsystem | Fineract path | LOC | Class | Evidence / justification |
|---|---|---|---|---|---|
| G1 | Core runtime: REST resources, JSON serialization, validation builders, exception mapping, filters, config | `fineract-core/…/infrastructure/core` **minus** `service/database` | 16,078 | **GAP †** | 209 files. `core/api` (2,020), `core/serialization` (2,267), `core/data` (2,404), `core/exceptionmapper` (1,728), `core/exception` (1,188), `core/service` (2,029 flat, incl. `DateUtils`, `MathUtil`, `ExternalIdFactory`, `ThreadLocalContextUtil`), `core/config` (886), `core/filters` (556, incl. the three `Idempotency*` filters of §5.2), `core/domain` (1,267). Absent from Nexus (§3.4 — no `net/http`, no serialization layer). **The non-plumbing part that survives any Nexus re-grade:** the **API error envelope** (`ApiParameterError`, `DataValidatorBuilder`, the `exceptionmapper` package) is observable output the golden vectors grade, so its exact shape is contract, not plumbing. |
| G2 | Provider runtime: boot, Jersey wiring, diagnostics, auditing, HTTP config | `fineract-provider/…/infrastructure/core` | 5,469 | **GAP †** | `config` (1,844), `service` (1,158), `diagnostics` (898), `jersey` (877), `domain` (184), `auditing` (181), `boot` (108), `http` (91), `serialization` (66), `messaging` (62). Almost entirely JVM-container wiring; expect most of it to vanish on re-grade. |
| G3 | Command bus, maker-checker, **idempotency** | `fineract-core/…/commands` (6,589) + `fineract-provider/…/commands` (1,253) + `fineract-command{,-jdbc,-async,-audit,-disruptor}` (2,246) | 10,088 | **GAP** | §5.2. This is the **spine of every write path** and it is not generic plumbing: `CommandSource` is the audit record, maker-checker approval is a banking control (`Permission.java`, `SynchronousCommandProcessingService`, `PortfolioCommandSourceWritePlatformServiceImpl`), and the `Idempotency-Key` contract is a CLAUDE.md non-negotiable. **Two live sub-decisions:** (i) Fineract carries *two* command buses — the legacy `commands` package that all money endpoints actually use, and the newer `fineract-command*` modules whose own idempotency test is `@Disabled` (`CommandSampleApiTest.java:130`); the port should target the legacy semantics, which is what vectors can grade. (ii) `IdempotencyKeyResolver.java:36` *generates* a missing key — Gerege must **refuse** instead, a deliberate divergence with no oracle vector. |
| G4 | Job scheduling and execution | `…/infrastructure/jobs` (core 615 + provider 7,593) | 8,208 | **GAP †** | `JobRegisterServiceImpl`, `JobSchedulerServiceImpl`, `StuckJobExecutorService`, `SchedulerJobListener`, per-job tasklets (`updatenpa`, `retainedearning`, `aggregationjob`, `increasedateby1day`). `docs/softhouse-engagement-plan.md:68` says Nexus's scheduler is to be reused — **doctrine, not evidence**. **The part that survives re-grade regardless:** the *job catalogue* (which jobs exist, in what order, what each one posts) and the stuck-job / restart-after-failure semantics — those are business behaviour, and Tier A's COB context depends on them. |
| G5 | Authentication, session, 2FA, OIDC | `fineract-security` (4,373) + `fineract-core/…/infrastructure/security` (1,415) + `fineract-provider/…/infrastructure/security` (1,520) | 7,308 | **GAP †** *(authN)* / **GAP** *(authZ)* | `filter/{TenantAwareBasicAuthenticationFilter, TenantAwareAuthenticationFilter, OidcTenantAwareFilter, TwoFactorAuthenticationFilter, BusinessDateFilter}`, `service/{AccessTokenGenerationService, TwoFactorService, FineractOidcUserService, SpringSecurityPlatformSecurityContext, SqlInjectionPreventerServiceImpl}`. **Split the row when scheduling:** authentication/session/2FA/OIDC is the **†** half a host platform plausibly supplies; the **permission model** — `m_permission`'s (grouping, code, entity, action) tuples and `validateHasPermission` per command — is banking-specific authorisation bound to G3's maker-checker and will not come from any host. |
| G6 | User administration: users, roles, permissions, password policy | `fineract-core/…/useradministration` (1,555) + `fineract-provider/…/useradministration` (5,025) | 6,580 | **GAP †** *(user store)* / **GAP** *(role↔permission)* | Same split as G5. **Non-negotiable defect inside this row:** `AppUser.java:73-78` stores `firstname`/`lastname`, both `NOT NULL` — §5.3, gate **G-C1**. |
| G7 | Document management / content store | `fineract-document` (4,892) + `fineract-core/…/infrastructure/documentmanagement` (51) + `fineract-provider/…/infrastructure/s3` (184) | 5,127 | **GAP †** | `infrastructure/contentstore/{service,policy,processor,detector,config}` — pluggable filesystem-or-S3 blob storage with MIME detection and a content policy. Classic host-platform territory. The 184-line `s3/` package (`AmazonS3Config`, `LocalstackS3ClientCustomizer`) is a deployment choice, not a port. |
| G8 | Global & external-service configuration | `…/infrastructure/configuration` (core 1,073 + provider 3,090) | 4,163 | **GAP** | `c_configuration` global flags are **not** inert plumbing: they gate money behaviour (backdated transactions, penalty application, rounding-adjacent switches) and `ConfigurationDomainService` is consulted from the loan and accounting paths. The provider half also carries external-service config (S3/SMTP/SMS) that follows N6/N10/G7. This is where the **RTGS/ACH+ threshold (MNT 5,000,000) must be configured, never hard-coded** — CLAUDE.md. |
| G9 | Organisation: offices, staff, holidays, working days, provisioning criteria | `…/organisation/{office,staff,holiday,workingdays,provisioning}` (core + provider) | 10,780 | **GAP** | office 2,458 · staff 2,051 · holiday 2,089 · workingdays 1,390 · provisioning 2,792. **Not plumbing:** holiday and working-day calendars are direct inputs to loan schedule date arithmetic, so **Tier A is blocked on this row**. Two defects live here: `Staff.java:41-45` two-field names (§5.3, gate G-C1) and the missing per-office time zone (§5.4, backlog B-2). `organisation/provisioning` (2,792) overlaps `tierA-provisioning-reporting` and should be coordinated with it. |
| G10 | Code / code-value lookups | `…/infrastructure/codes` (core 1,014 + provider 1,537) | 2,551 | **GAP** | `m_code` / `m_code_value` back enumerated fields all over the client, loan and savings domains (gender, purpose, closure reason). Small, unavoidable, and a dependency of Tier B. |
| G11 | In-app notification | `…/notification` (core 91 + provider 1,985) | 2,076 | **GAP †** | Notification mappers, generators and the per-user read/unread store. Host-platform territory; low priority either way. |
| G12 | Business events (in-process) | `…/infrastructure/event/business` (core + provider) | 1,995 | **GAP** | The in-process publish/subscribe the COB, accrual and accounting paths hang listeners on — `TransactionBoundApplicationEventPublisher` semantics (fire **after** commit) are load-bearing for double-entry correctness. Distinct from N3, which is only the outbound broker delivery. |
| G13 | Account-number formats | `…/infrastructure/accountnumberformat` (core 600 + provider 1,144) | 1,744 | **GAP** | Per-entity-type account-number generation strategy. Observable in vectors (account numbers appear in captured output), so it is contract-adjacent, not cosmetic. |
| G14 | Business date | `fineract-core/…/infrastructure/businessdate` | 898 | **GAP** | `BusinessDateType`, `BusinessDate`, `BusinessDateReadPlatformService`, `BusinessDateWritePlatformServiceImpl`, and the `BusinessDateFilter` in `fineract-security`. The "business date vs actual date" distinction is what makes COB and back-dated posting deterministic and re-runnable. **Small, foundational, and Tier A depends on it** — see §7. |
| G15 | Bean/annotation validation | `fineract-validation` | 395 | **GAP** | 8 files of custom constraint annotations. Fold into G1. |
| G16 | Core utilities | `fineract-core/…/util` | 231 | **GAP** | 4 files. Fold into G1. |
| G17 | Unallocated residual | `fineract-core/…/infrastructure` (files not under a named sub-package) | 42 | **GAP** | Carried explicitly so the partition sums exactly rather than being absorbed silently. |
| | **Subtotal** | | **83,733** | | |

### 6.5 Partition check

```
reassign 37,525 + not-applicable 68,720 + partial 2,190 + gap 83,733  =  192,168   ✓
```

Equal to the measured total in §4. No row is double-counted and no line is unassigned.

---

## 7. The consequence for the program

### 7.1 What Tier C actually costs

The program currently carries Tier C as `main_loc: 180000`, as though all of it must be ported.
It must not.

| Class | LOC | % of measured Tier C |
|---|---|---|
| **Reassign** to Tier A/B (already scoped elsewhere) | 37,525 | 19.5% |
| **NOT-APPLICABLE** (never ported) | 68,720 | 35.8% |
| **PARTIAL** (extend ported code; ≈1,800 remaining) | 2,190 | 1.1% |
| **GAP** — must be ported | 83,733 | 43.6% |
| **NEXUS-PROVIDES** | **0** | 0% — and §2 explains why that zero is a statement about the evidence, not about Nexus |

**Tier C's genuine port is ~83.7k LOC of Fineract-equivalent behaviour, not 180k — a 54% reduction
before a single line of Nexus platform code has been read.** More than half of what the program is
carrying for Tier C is either someone else's context (19.5%) or work that should never happen
(35.8%).

### 7.2 The number that is still unresolved, and it is the larger one

Inside the 83,733 GAP lines, the **†** rows are contingent on §2:

| | LOC | Rows |
|---|---|---|
| **GAP-real** — port regardless of what Nexus turns out to provide | **32,887** | G3, G8, G9, G10, G12, G13, G14, G15, G16, G17 |
| **GAP-† host-candidate** — re-grade against the real Nexus tree first | **50,846** | G1, G2, G4, G5, G6, G7, G11 |

So Tier C is somewhere between **~33k and ~84k LOC**, and which end depends entirely on a fact this
run could not obtain. That 2.5× spread is the whole reason recommendation **R-1** (§2) outranks
everything else in this document. It is also the honest reading of "port only the genuine gaps":
**32,887 lines are provably genuine; 50,846 are unproven in both directions.**

Note what the split is *not*: it is not "plumbing vs domain". Rows G5 and G6 are marked **†** for
their authentication and user-store halves only — their permission/role halves are GAP-real and
survive any re-grade. When those rows are scheduled they must be split, not taken whole.

### 7.3 Program-file corrections this audit implies

1. **`tierC-platform-map-first.main_loc` 180,000 → 83,733** (or 32,887 + 50,846-pending, if the
   schema can express the split).
2. **Move four paths out of Tier C** (§5.6, B-1): `fineract-core/…/portfolio`,
   `fineract-core/…/batch`, `fineract-core/…/accounting`, and both halves of `…/dataqueries`; add
   the corresponding `fineract-core` paths to the Tier A/B contexts that own them, whose `main_loc`
   rise accordingly. `dataqueries` is currently in **two** contexts' paths at once.
3. **Record the NOT-APPLICABLE set** (68,720 LOC, 22 rows) somewhere a later planner will see it,
   so no future run proposes a bulk-import or campaigns task and is rejected for it.
4. `fineract-db` contributes **0** Java LOC (§5.7); the Liquibase changelog (93,498 XML lines) is
   run, not ported, and should be recorded as an operational dependency rather than a port target.

---

## 8. Recommended slice order for the GAP subsystems

Ordering principle: **what Tier A is blocked on, then what every write path needs, then the rest** —
and nothing **†** is scheduled before R-1 resolves it.

| Slice | Rows | LOC | Why here |
|---|---|---|---|
| **C-0** *(not a port)* | — | — | **R-1: attach the Nexus platform tree and re-grade the 7 † rows.** Everything below assumes this has happened; slices C-1…C-4 are safe to run even if it has not, because none of them is **†**. |
| **C-1** Business date + working days + holidays | G14, part of G9 (holiday 2,089 + workingdays 1,390) | 4,377 | **Tier A is blocked on it.** Loan schedule date arithmetic already needs holiday and working-day rules, and COB needs the business-date/actual-date distinction. Smallest slice with the largest downstream unblock. Vectors are cheap: date-in/date-out. |
| **C-2** Command bus, maker-checker, idempotency | G3 | 10,088 | The spine of every money-movement write. Nothing else in Tier A/B can be *cut over* without it, and its `Idempotency-Key` behaviour is a CLAUDE.md non-negotiable. Carries the one deliberate oracle divergence (§5.2), so it needs its own property test alongside vectors. |
| **C-3** Codes, account-number formats, global configuration | G10, G13, G8 | 8,458 | Referenced by nearly every Tier A/B entity; each is small and independently vectorable. G8 is where the RTGS/ACH+ threshold must live as configuration. |
| **C-4** Organisation: offices, staff, provisioning criteria | rest of G9 (office 2,458 + staff 2,051 + provisioning 2,792) | 7,301 | Office hierarchy is a foreign key from almost everything. **Gate G-C1 (three-field names) must be answered before this slice starts**, because `m_staff` is one of the two tables it touches. |
| **C-5** In-process business events | G12 | 1,995 | Needed before COB/accrual listeners can be ported faithfully; after-commit publication semantics are load-bearing for double-entry. |
| **C-6…** everything **†** | G1, G2, G4, G5, G6, G7, G11 (+ G15, G16, G17 folded into G1) | 50,846 + 668 | **Blocked on C-0.** Order within it depends on what the re-grade returns; if Nexus supplies HTTP, auth, jobs and blob storage, most of this collapses to adapters and the permission/role halves of G5+G6. |

Two ordering notes:

- **P1 (money/currency) is not a slice.** It is an extension of already-ported Nexus code and should
  be picked up by whichever Tier A slice next needs `ApplicationCurrency`.
- **Do not start with G1.** It is the largest GAP row and the most likely to evaporate on re-grade.
  Porting Fineract's JAX-RS resource layer into Go before knowing whether Nexus already serves HTTP
  is precisely the "unjustified plumbing port" CLAUDE.md calls a rejection.

### 8.1 Gates and recorded choices

**Raised as a `user` gate** (I do not decide these):

- **G-C1 — three-field names vs schema-first.** `m_appuser.firstname`/`lastname` and
  `m_staff.firstname`/`lastname` (§5.3) are columns of the Fineract PostgreSQL schema that CLAUDE.md
  says to *adopt*, and they violate CLAUDE.md's *names are three fields* rule. Satisfying both is
  impossible. The resolution — extend the adopted schema with ovog/patronymic/given-name columns, or
  amend the schema-first rule for person tables — **changes the frozen adapter contract**, which
  CLAUDE.md makes a `user` task. Blocks slice C-4. It is an ENGINEERING problem with a contract
  consequence, not a PRODUCT preference, which is why it is not decided here.

**Recorded PRODUCT choices** (`chosen_by: agent`, per CLAUDE.md *Answering gates*; Buyan retains
veto; each is reversible by moving one row):

- **Single-tenant deployment** — one deployment per licensed entity. Makes N8's routing half
  NOT-APPLICABLE. *Alternative rejected:* multi-tenant datasource routing, rejected because Gerege's
  ratified tenant parameters describe one entity (Buyan, NBFI) and multi-tenancy would put a second,
  unvectored variable into every parity run. Reversing this restores ~896 LOC to GAP.
- **Launch without** bulk import (N1), campaigns (N2), external event delivery (N3), report mailing
  (N6), hooks (N7), entity-access (N9), SMS (N10), templates (N11), surveys (N13), ad-hoc query
  (N16) and teller (N17) — the eleven rows carrying argument shape (d), **51,196 LOC**. Each records
  the cheaper replacement if the capability is wanted later. *Alternative rejected:* porting them
  now, rejected under "features deferred rather than shipped unvectored" — none is gradeable against
  the reference oracle in a way that adds parity confidence. (N8's tenant-routing half is (d) too
  but is covered by the single-tenant choice above; N12 is (b)+(c), not a deferral.)
- **Ad-hoc query (N16) is recommended as a permanent exclusion**, not a deferral: an
  arbitrary-SQL-execution endpoint in a ledger system is a security regression regardless of launch
  scope.

---

## 9. What I could not establish

- **`[UNVERIFIED]` U-1 — everything the Gerege Nexus platform actually provides.** §2. The tree is
  not present in this session; `nexus/` contains only Tier 0/Tier A domain work and the conformance
  harness. **This is why the audit has zero NEXUS-PROVIDES rows**, and why 50,846 GAP LOC carry the
  **†** marker instead of a settled class. Reason: repository contents, not a search failure — I
  state in §2 exactly where I looked.
- **`[UNVERIFIED]` U-2 — which credit bureau `infrastructure/creditbureau` models.** I read the
  package structure and the domain classes but did not read the HTTP client's request shapes closely
  enough to name the bureau, and I could not check Mongolian bureau requirements from this session.
  N4's classification rests on the weaker claim that the integration is *bureau-specific*, which the
  presence of `CreditBureauToken` / `CreditBureauConfiguration` per-organisation supports. If
  Mongolia's bureau happens to expose a compatible API, N4 becomes a PARTIAL.
- **`[UNVERIFIED]` U-3 — whether the FRC requires anything the survey (N13) or report-mailing (N6)
  subsystems provide.** No Mongolian regulatory reporting specification was available to this run.
  Both are deferrals, not deletions, and both are reversible.
- **`[UNVERIFIED]` U-4 — 12,168 LOC of measurement difference** between my 192,168 and
  `program.json`'s 180,000. I did not reconstruct how the earlier figure was taken, so I cannot say
  whether it excluded a path, a source set, or licence headers. Mine is the larger number, so using
  it cannot understate a row.
- **`[UNVERIFIED]` U-5 — whether the **†** split inside G5 and G6 is at the right line.** I asserted
  that authentication is host-supplied and authorisation is not, from reading the package structure
  and the filter/service names — not from reading `SpringSecurityPlatformSecurityContext` end to
  end. The row is GAP either way; only the ordering advice in §8 depends on the split.
- **Not attempted: per-file justification below subsystem granularity.** The task defines this as
  module/subsystem granularity and I kept to it. Rows N1, N2, G1 and G4 are each large enough that a
  later per-subsystem run may find a sub-package that deserves a different class than its parent
  row. The rows most likely to move that way are G1 (some of it is contract, most is plumbing) and
  N2 (the email/SMS *delivery* primitive is reusable even though campaigns are not).

### 9.1 The classification I am least confident in

**N9 — `entityaccess` (2,382 LOC), NOT-APPLICABLE.** It is the row where my argument rests most on
judgement and least on evidence. I established what it *is* (an office↔product visibility matrix,
`FineractEntityToEntityMapping` / `FineractEntityAccessType`, gated by global configuration) but I
did **not** verify that it is off by default, and I did not check whether `tierB-branch` depends on
it. If Gerege's branch model needs product visibility scoped per office, this row is a **GAP**, not
a NOT-APPLICABLE, and I would have dropped a real subsystem by assertion. It is the first row a
reviewer should re-derive.

Runners-up, in order: **N19 `instancemode`** (rests on "Nexus is a single binary", which is itself
U-1 doctrine) and **N16 `adhocquery`** (I extended a deferral into a recommended permanent exclusion
on a security argument that is mine, not the program's).

---

## 10. Found outside the assigned scope

Read only; nothing outside `docs/analysis/` and `.softhouse/handoff/` was written, and the pinned
oracle checkout was never modified (`git status --porcelain` empty before and after).

- **B-1 — `program.json` path assignments need four moves.** §5.6, §7.3. `dataqueries` sits in two
  contexts' `fineract_paths` simultaneously; three `fineract-core` domain packages sit in Tier C
  while their `fineract-provider` twins sit in Tier A/B. The Tier A/B contexts as currently written
  would port a context without its own entity classes — the same trap
  `tierA-a2-behaviour.md` §1.2 documented for `glaccount`.
- **B-2 — time zone is per-tenant, not per-office.** §5.4. `Office.java` has no zone column;
  `timezone_id` is on the tenant-store table. A deployment spanning Ulaanbaatar (+08) and Hovd (+07)
  needs the zone on `m_office`. Schema-affecting, Tier C row G9, and worth raising before Tier B's
  branch context is planned.
- **B-3 — the newer `fineract-command*` bus is unfinished and should not be the port target.**
  `CommandSampleApiTest.java:130` is `@Disabled // TODO: implement idempotency properly with
  backwards compatibility`. All money endpoints run through the legacy `fineract-core/…/commands`
  path, which is also the only one vectors can grade. Any future task in G3 should say so
  explicitly.
- **B-4 — the Liquibase changelog is an unrecorded program dependency.** 271 files, 93,498 XML lines
  (§5.7). It is how the adopted PostgreSQL schema comes into existence in every environment — the
  reference-oracle instance, the Go module, vector capture, shadow runs and CI. It appears in no
  context's `main_loc` because it is not Java, and it appears in no context's notes at all.
- **Observation, not a backlog item — the conformance harness is most of Nexus.** Of 25,628 non-test
  Go lines, roughly 15k are the two `conformance` packages (§3.1). That is a healthy ratio for a
  parity-graded migration, and it is worth stating because a reader glancing at "Nexus is 40k lines"
  could otherwise mistake harness for product.

---

*End of Tier C platform gap audit. 44 subsystem rows: 0 NEXUS-PROVIDES, 17 GAP (7 marked
host-candidate), 1 PARTIAL, 22 NOT-APPLICABLE, 4 reassigned to Tier A/B.*
