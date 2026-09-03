# T492 — INDEPENDENT adversarial review of T489 (Tier C platform gap audit)

| | |
|---|---|
| Reviewer | `T492` |
| Branch | `softhouse/T492-review-t489` |
| Under review | `softhouse/T489-tierC-platform-gap-audit` @ `0f1028cfe45300831cab7d424c55427ec53c235b` |
| Artefacts reviewed | `docs/analysis/tierC-platform-gap-audit.md` (644 lines), `.softhouse/handoff/T489-tierC-platform-gap-audit.md` |
| Reference oracle | Fineract reference implementation, `/home/user/fineract` |
| Oracle pin, verified by me | `git rev-parse HEAD` → **`426a23544e8426a38ae43ae404670a0a7e85b9eb`**, `git log -1` → `Wed Aug 12 14:59:16 2026 +0200  Merge pull request #5946`, `git status --porcelain` → **empty (0 lines)**. Checkout not modified by this review. |
| Nexus tree read | `nexus/` of `/home/user/wt/T492` (worktree of `origin/main` @ `68399446`) |
| Date | 2026-09-02 |

Throughout, **"the reference oracle" is the Fineract implementation** we grade Go against.
**"Oracle Database"** appears only as the name of the prohibited product. The two are unrelated and
this review never blurs them.

---

## 0. Method and its honest boundary

**Order followed, as mandated.** §§1–4 below were derived from the two trees *before* T489's
document was opened. T489's output was read only after my own measurement of the Tier C surface,
the Nexus inventory, the `program.json` path analysis and all five non-negotiable claims was
complete and written down.

**Caveat on independence I must state.** The review brief itself disclosed several of T489's
figures (192,168 / 2,235 / 44 rows / 50,846 / 37,525 / 2,382). I could not un-see them. My
derivations below were nonetheless run from the trees and are reproducible from the commands
quoted; where a number agrees, the agreement is a *reproduction*, not a *reading*.

**What I actually re-derived, and what I did not.**

| | |
|---|---|
| Row **LOC** independently re-measured | **44 of 44.** I decomposed every parent directory in the 20 `fineract_paths` and checked the children sum to the parent, so every row's figure and the partition's exhaustiveness are re-derived, not accepted. |
| Row **classification argument** re-derived in depth | **12 of 44** — N8, N9, N14, N16, N17, N19, N21, G12/N3 (the event split), G17, P1/G9/N17 (the organisation split), plus R1–R4 as a group. |
| Row classification **accepted on the row's stated evidence** without independent challenge | the remaining ~32, chiefly N1–N7, N10–N13, N15, N18, N20, N22 and G1–G11, G13–G16. A later per-subsystem run may still move one of these. |
| Non-negotiable claims re-derived | **5 of 5** (§4). |
| Citations spot-checked | **33** (§5). |

Runtime claims are claims about code I read. There is no running Fineract and no PostgreSQL here.
`[UNVERIFIED]` marks anything I could not establish, with the reason.

**"Not found" is a statement about the search.** Every negative below names where I looked.

---

## 1. My independent measurement of the Tier C surface

Recipe (physical lines of `.java` under a `src/main/java/` path, pinned checkout, `build/` absent):

```
find <path> -name '*.java' -path '*/src/main/java/*' | wc -l
find <path> -name '*.java' -path '*/src/main/java/*' -print0 | xargs -0 cat | wc -l
```

Whole-tree control: **5,331 files / 544,996 lines** of main Java (CLAUDE.md states ~544k / 5,317 —
the 14-file gap is a pre-existing program-inventory figure, not T489's, and I did not chase it).

Per declared `fineract_path`, measured by me:

| Path | Files | LOC |
|---|---|---|
| `fineract-core` | 795 | 71,833 |
| `fineract-security` | 65 | 4,373 |
| `fineract-validation` | 8 | 395 |
| `fineract-command` | 25 | 980 |
| `fineract-command-jdbc` | 9 | 592 |
| `fineract-command-async` | 3 | 152 |
| `fineract-command-audit` | 6 | 262 |
| `fineract-command-disruptor` | 4 | 260 |
| `fineract-provider/…/infrastructure` | 903 | 81,148 |
| `fineract-provider/…/organisation` | 117 | 10,025 |
| `fineract-provider/…/useradministration` | 64 | 5,025 |
| `fineract-provider/…/notification` | 32 | 1,985 |
| `fineract-provider/…/template` | 36 | 1,971 |
| `fineract-provider/…/adhocquery` | 17 | 1,289 |
| `fineract-provider/…/interoperation` | 44 | 4,175 |
| `fineract-provider/…/commands` | 11 | 1,253 |
| `fineract-document` | 85 | 4,892 |
| `fineract-db` | **0** | **0** |
| `fineract-client` | 10 | 1,530 |
| `fineract-avro-schemas` | 1 | 28 |
| **Total** | **2,235** | **192,168** |

**I independently reproduce T489's 192,168 / 2,235 exactly.** `program.json` records
`main_loc: 180000`; the difference is **+12,168 (6.8%)** and `program.json` is the understated one.
Like T489 I did not reconstruct how the 180,000 was taken `[UNVERIFIED — no record of the earlier
measurement recipe exists in the repo]`.

### 1.1 The partition is exhaustive and non-overlapping — verified, not assumed

I checked this the only way that proves it: measure each **parent** directory, decompose it into the
children T489's rows use, and confirm the children sum to the parent with nothing left over.

| Parent | Measured | Children in T489's rows | Sum | Residual |
|---|---|---|---|---|
| `fineract-provider/…/infrastructure` | 81,148 | 21 sub-packages (N1–N3, N4, N6, N7, N9, N10, N12, N13, N15, N18–N20, G1-adjacent, G2, G4, G7, G8, G10, G11, G12, G13) | **81,148** | 0 — and `find … -maxdepth 1 -name '*.java'` returns **0 files**, so nothing hides at that level |
| `fineract-core/…/infrastructure` | 31,509 | 15 sub-packages | 31,467 | **42** = `DataIntegrityErrorHandler.java` (exactly 42 lines, verified) = row **G17** |
| `fineract-core` top level | 71,833 | 10 packages + `org/springframework/batch` | **71,833** | 0 (the 134-line Spring patch is row N21) |
| `…/organisation` (core 4,170 + provider 10,025 = 14,195) | 14,195 | G9 10,780 + P1 2,190 + N17 1,225 | **14,195** | 0 |
| `…/infrastructure/event` (core 3,998 + provider 3,919 = 7,917) | 7,917 | N3 external 5,922 + G12 business 1,995 | **7,917** | 0 — only two subdirs exist |
| `…/infrastructure/core/service/database` | **2,605** | N8 | 2,605 | 0 (so G1 = 18,683 − 2,605 = **16,078**, reproduced) |

Class subtotals, recomputed by me from the row figures:

```
reassign 37,525 + not-applicable 68,720 + partial 2,190 + gap 83,733 = 192,168   ✓
```

**Verdict on attack #3: the partition claim holds. Every one of the 44 row LOC figures reproduces
against my own directory measurements, the rows are disjoint, and they sum exactly.** No hole, no
overlap. This is independently derived agreement.

---

## 2. Attack #2 — the load-bearing structural claim, re-derived

**T489's claim:** the Nexus platform tree is not in this repository; `go list ./...` returns six
packages, all Tier 0 / Tier A plus the harness; `nexus/go.mod` carries zero `require` directives;
therefore zero NEXUS-PROVIDES rows and 50,846 LOC parked as `GAP-†`.

**My derivation, run before reading the above.**

`cat nexus/go.mod` returns, in full:

```
module github.com/gerege/nexus

go 1.23
```

Three lines. **Zero `require` directives.** No `pgx`, no HTTP router, no auth, no config, no
scheduler — no dependency of any kind.

`go list ./...` from `nexus/` returns exactly six:

```
github.com/gerege/nexus/internal/apps/ledger
github.com/gerege/nexus/internal/apps/ledger/conformance
github.com/gerege/nexus/internal/apps/loanschedule
github.com/gerege/nexus/internal/apps/loanschedule/conformance
github.com/gerege/nexus/internal/apps/loanschedule/conformance/cmd/conformance
github.com/gerege/nexus/internal/apps/loanschedule/contract
```

**Where I looked for a Nexus platform tree, and what I found:**

| Looked for | Where | Result |
|---|---|---|
| Any file under `nexus/` | `find nexus -type f` | **72 files** — 70 `.go`, plus `go.mod` and one `testdata/*.txt` |
| Directory structure | `find nexus -type d` | 10 dirs, all under `internal/apps/{ledger,loanschedule}` |
| A platform package | `nexus/internal/platform` — the `go_target` `program.json` declares for this context | **does not exist** |
| A git submodule | `git config --file .gitmodules --list` | `fatal: unable to read config file '.gitmodules': No such file or directory` |
| A reference to an external Nexus platform repo | `grep -rn "gerege/nexus\|nexus-platform\|Nexus repo" --include=*.md --include=*.json .` | only the module path `github.com/gerege/nexus` in DEC-1, `reference-oracle.md:594`, and prior review/handoff `go test` transcripts. **No second repository is named anywhere.** |

Nexus metrics, measured by me: **70 `.go` files, 40,242 total lines, 25,628 non-test**, of which the
two `conformance` packages are **16,715 non-test lines (65%)**.

**FINDING: I independently confirm T489's structural claim in full, and I record it as my own.**
The Nexus platform tree is not present in this repository, in any submodule, or under any path this
session can read. `program.json`'s own `go_target` for this context (`nexus/internal/platform`)
points at a directory that does not exist. Doctrine asserts otherwise — I verified both citations:

- `.softhouse/patterns.md:81` — *"`fineract-core` and `fineract-provider/infrastructure` are largely
  plumbing (auth, tenancy, command bus, jobs) that Nexus already provides."* ✓ exact.
- `docs/softhouse-engagement-plan.md:68` — *"reusing Nexus's scheduler rather than porting
  Fineract's job framework."* ✓ exact.

Neither is evidence. **T489 was right to refuse to convert doctrine into a NEXUS-PROVIDES row**, and
right that a false NEXUS-PROVIDES is the expensive direction. Its recommendation **R-1** (attach the
Nexus platform tree and re-grade the 7 **†** rows) is, in my independent judgement too, the
program's cheapest next action, and the 33k–84k spread on Tier C is real.

This is **not** a MAJOR against T489. It is the audit's best work.

---

## 3. Attack #4 — the 37,525 LOC misfiled into Tier C, re-derived

Measured by me from the pinned tree:

| Path | Files | LOC |
|---|---|---|
| `fineract-core/…/portfolio` | 206 | 23,652 |
| `fineract-core/…/batch` | 18 | 1,932 |
| `fineract-core/…/accounting` | 21 | 1,897 |
| `fineract-core/…/infrastructure/dataqueries` | 27 | 1,749 |
| `fineract-provider/…/infrastructure/dataqueries` | 68 | 8,295 |
| **Total** | | **37,525** |

**Reproduced exactly.**

**The duplicate is real, and I confirm it from `program.json` directly.**
`tierA-provisioning-reporting.fineract_paths` contains
`"fineract-provider/src/main/java/org/apache/fineract/infrastructure/dataqueries"`, while
`tierC-platform-map-first.fineract_paths` contains
`"fineract-provider/src/main/java/org/apache/fineract/infrastructure"` — the **parent** of that
path. 8,295 LOC therefore sits in two contexts' scopes simultaneously. Under CLAUDE.md's per-run
scope guard, whichever context runs second will be reading files assigned to another context.

The other three are the module-split pattern: the `fineract-provider` halves are already in Tier A/B
paths (`…/portfolio/*`, `…/accounting/*`, `…/batch`) while the `fineract-core` halves fall inside
Tier C's blanket `fineract-core` path. **I agree with the reassignment and with the warning that the
Tier A/B contexts must gain the `fineract-core` paths, or they will be ported without their own
entity classes.**

---

## 4. Attack #5 — the five non-negotiable claims, each re-derived

### 4.1 Two-field names — **CONFIRMED, citations exact, collision real**

`grep -n "firstname\|lastname"`, lines opened:

- `fineract-core/src/main/java/org/apache/fineract/useradministration/domain/AppUser.java`
  **:73** `@Column(name = "firstname", nullable = false, length = 100)` · **:74** `private String firstname;`
  **:77** `@Column(name = "lastname", nullable = false, length = 100)` · **:78** `private String lastname;`
  → **`AppUser.java:73-78` is exactly right, and both columns are `nullable = false`.**
- `fineract-core/src/main/java/org/apache/fineract/organisation/staff/domain/Staff.java`
  **:41-42** `firstname` · **:44-45** `lastname` → **`Staff.java:41-45` is exactly right.**

The collision is real and it is genuinely two-sided: `m_appuser.firstname` and `m_staff.firstname`
are columns of the very PostgreSQL schema CLAUDE.md says to *adopt*, and CLAUDE.md separately
forbids `first_name`/`last_name` in favour of ovog / patronymic / given name. Both rules cannot be
satisfied silently. **Raising this as `user` gate G-C1 rather than deciding it is correct** —
CLAUDE.md's *Answering gates* makes agents decide PRODUCT and ENGINEERING questions, but this one
changes the frozen adapter contract, and a contract change is explicitly a `user` task.

### 4.2 Timezone is per-tenant, not per-office — **CONFIRMED, and it is a first-order finding**

- `fineract-provider/src/main/resources/db/changelog/tenant-store/parts/0001_initial_schema.xml:77`
  — `<column name="timezone_id" type="VARCHAR(100)">` with `<constraints nullable="false"/>`, on
  `createTable tableName="tenants"` (changeSet id 2). ✓ exact. *(Note: four files in the tree are
  named `0001_initial_schema.xml`; T489's §5.4 gives the full disambiguating path — good.)*
- `fineract-core/…/infrastructure/core/service/DateUtils.java:65-67` —
  `getDateTimeZoneOfTenant()` → `ZoneId.of(tenant.getTimezoneId())`. ✓ exact. The zone is an IANA
  identifier from config, so *"never hard-code an offset"* is satisfied by design.
- `fineract-core/…/organisation/office/domain/Office.java` — `grep -ic "zone"` returns **0**.
- `grep -rn "timezone" fineract-provider/src/main/resources/db/changelog/tenant/` returns
  **nothing**: there is no timezone column anywhere in the tenant schema, and `m_office`
  (`0001_initial_schema.xml:2863-2878`, opened and read) has columns
  `id, parent_id, hierarchy, external_id, name, opening_date` — **no timezone.**

**Independently confirmed and I extend it.** Both Mongolian zones are already seeded in Fineract's
`timezones` lookup — `tenant-store/parts/0002_initial_data.xml:1502` `Asia/Ulaanbaatar`, **:1508**
`Asia/Hovd` (comment: *"Bayan-Olgiy, Govi-Altai, Hovd, Uvs, Zavkhan"*), **:1514**
`Asia/Choibalsan`. But that table is a *lookup*; `tenants.timezone_id` is a **single scalar per
tenant**. So a Gerege deployment with a Ulaanbaatar head office (+08) and a Hovd branch (+07) gets
**one** zone. Either every office runs on the head-office zone, or `timezone_id` moves onto
`m_office` — a schema change to the adopted schema. T489's backlog **B-2** is correct and, for a
two-timezone country with a CLAUDE.md non-negotiable naming both zones, it deserves to be raised
before `tierB-branch` is planned, exactly as T489 says.

### 4.3 `IdempotencyKeyResolver.java:36` generates a missing key — **CONFIRMED, citation exact**

`fineract-core/src/main/java/org/apache/fineract/commands/service/IdempotencyKeyResolver.java`,
line 36 read in full:

```java
return Optional.ofNullable(wrapper.getIdempotencyKey()).orElseGet(() -> getAttribute().orElseGet(idempotencyKeyGenerator::create));
```

Absent both a wrapper key and the request attribute, Fineract **fabricates** a key. CLAUDE.md makes
`Idempotency-Key` **mandatory** on every money-movement POST — i.e. a missing key must be
**refused**. T489's consequence is right and is the important part: **the reference oracle can never
produce a golden vector for the refusal, because it never refuses.** That divergence is gradeable
only by a Gerege-side property test, and slice C-2 must carry one.

### 4.4 Oracle Database does not appear — **CONFIRMED, and I searched harder in both directions**

`DatabaseType.java`, lines opened: **:21** `public enum DatabaseType {` · **:23** `MYSQL, //` ·
**:24** `POSTGRESQL, //` · **:25** `;` → **`DatabaseType.java:21-25` is exactly right.**
`DatabaseTypeResolver.java:31-33` is the `DRIVER_MAPPING` of `org.mariadb.jdbc.Driver`,
`com.mysql.jdbc.Driver`, `com.mysql.cj.jdbc.Driver` → `MYSQL` and `org.postgresql.Driver` →
`POSTGRESQL`; **:48-52** is `determineDatabaseType`, which **throws
`IllegalArgumentException("The driver's class is not supported " + driverClassName)`** for anything
else. ✓ both exact.

**T489's grep covered only the Tier C paths. I ran it over the entire pinned tree** — every module,
including tests, resources, gradle files, docs and SQL dumps:

| Search (whole tree) | Hits | Assessment |
|---|---|---|
| `grep -rni "ojdbc"` | 44 | **all false positives.** Every hit is the substring `oJdbc` inside a camelCase identifier: `toJdbcUrl`, `toJdbcValue`, `toJdbcValueImpl`, `validateToJdbcColumn(s\|Name\|Names)`, `mapApiTypeToJdbcType`, and one test method `…SoJdbcDoesNotShare…`. Not one is the `ojdbc` driver artefact. |
| `grep -rni "oracle\.jdbc"` | **0** | |
| `grep -rni "OracleDialect\|Oracle12cDialect\|OracleDatabase"` | **0** | |
| `grep -rn "1521"` | 6 | **all coincidental digit substrings** — `1811521678` in two sample-data SQL dumps, and the amount `1521.83`/`1521.84` in `LoanMigration.feature`. No `:1521` port. |
| `grep -rniw "oracle"` (whole word) | **4** | a Java download URL and a MySQL-overview URL in `fineract-doc/…/technology.adoc:3,11`; a JDK regex doc URL in `ESAPI.properties:454`; and `fineract-core/…/exception/ErrorHandler.java:74` — `DEADLOCK("60"), // Oracle: deadlock` |
| driver declarations in `*.gradle` | — | only `com.mysql:mysql-connector-j`, `org.mariadb.jdbc:mariadb-java-client`, `org.postgresql:postgresql`. **No Oracle artefact.** |

**T489's correction of the program's repeated belief is right, and it survives a harder search than
T489 ran.** There is no Oracle Database driver, dialect, port or dependency anywhere in the pinned
Fineract tree; the prohibition costs Tier C nothing. See F-6 for the one word of over-claim.

### 4.5 `fineract-db` has 0 Java LOC; the schema is 93,498 Liquibase lines — **CONFIRMED exactly**

- `find fineract-db -name '*.java'` → **0 files**. `fineract-db/` holds
  `mifospltaform-tenants-first-time-install.sql`, `old-schema-files/` and
  `multi-tenant-demo-backups/` — MySQL-dialect dumps and demo backups.
- `find fineract-provider/src/main/resources/db -name '*.xml' | wc -l` → **271**;
  `… -print0 | xargs -0 cat | wc -l` → **93,498**. ✓ both exact.
  *(Tree-wide, across all modules: 420 changelog files / 103,858 lines — the other 149 files are
  per-module changelogs belonging to Tier A/B contexts.)*

**I agree with the conclusion and think it is the audit's second-most-useful finding.** CLAUDE.md
says *adopt Fineract's PostgreSQL schema* — so the changelog is an operational artefact that is
**run, not translated**, and any task proposing to rewrite it into Go migrations is a rejection.
T489's backlog **B-4** (the changelog is an unrecorded program dependency, in no context's
`main_loc` and no context's notes) is correct and should be actioned.

---

## 5. Citation spot-check — stated sample, stated rate

I opened **33** distinct `FILE:LINE` citations at the pin and read what is there.

| # | Citation | Verdict |
|---|---|---|
| 1 | oracle pin `426a2354…`, `status --porcelain` empty | ✓ |
| 2 | `DatabaseType.java:21-25` | ✓ exact |
| 3 | `DatabaseTypeResolver.java:31-33` | ✓ exact |
| 4 | `DatabaseTypeResolver.java:48-52` | ✓ exact |
| 5 | `AppUser.java:73-78` | ✓ exact |
| 6 | `Staff.java:41-45` | ✓ exact |
| 7 | `ClientPersonConstants.java:27` `FIRST_NAME_COL = 0` | ✓ line exact (label imprecise — F-9) |
| 8 | `IdempotencyKeyResolver.java:35-36` / `:36` | ✓ exact |
| 9 | `CommandSourceService.java:66-73` `saveInitial` + `IdempotentCommandProcessUnderProcessingException` | ✓ exact |
| 10 | `CommandSourceService.java:101-103` `findByActionNameAndEntityNameAndIdempotencyKey` | ✓ exact |
| 11 | `IdempotencyStoreFilter.java` 74 / `…BatchFilter` 63 / `…Helper` 63 lines | ✓ all three exact |
| 12 | `CommandProperties.java:50` `idemPotencyKeyHeaderName = "Idempotency-Key"` | ✓ exact |
| 13 | `ServletHeadersCommandHook.java:50-51` | ✓ exact |
| 14 | `JdbcCommandStore.java:81-94` (request/response/state by key) | ✓ exact |
| 15 | `CommandSampleApiTest.java:130` `@Disabled // TODO: implement idempotency properly…` | ✓ exact |
| 16 | `tenant-store/…/0001_initial_schema.xml:77` `timezone_id` | ✓ exact |
| 17 | `DateUtils.java:65-67` | ✓ exact |
| 18 | `Office.java` no zone column | ✓ (`grep -ic zone` = 0) |
| 19 | `m_office` has no timezone (`…/tenant/parts/0001_initial_schema.xml:2863-2878`) | ✓ |
| 20 | `HookProcessorProvider.java:41-45` twilio/web/elasticSearch | ✓ lines exact (count understated — F-10) |
| 21 | `gcm/domain/Sender.java:106` "FCM Server Key obtained through the Firebase Web Console" | ✓ exact |
| 22 | `NotificationConfigurationData.java:33` `fcmEndPoint` | ✓ exact |
| 23 | **`RoutingDataSource.java:49,108-115`** "resolves a datasource from `ThreadLocalContextUtil.getTenant()`" | ✗ **DOES NOT SUPPORT — F-2** |
| 24 | `fineract-client/build.gradle` `org.openapi.generator` / `generatorName = 'Fineract'` | ✓ (lines 19, 28) |
| 25 | `SqlInjectionPreventerServiceImpl` is in `fineract-security` | ✓ |
| 26 | `fineract-db` 0 `.java` | ✓ |
| 27 | changelog 271 files / 93,498 lines | ✓ exact |
| 28 | `nexus/…/loanschedule/rounding.go:3` (`import "math/big"`) | ✓ exact |
| 29 | `rounding.go:7-12` "no binary fraction type anywhere on this path" | ✓ |
| 30 | `rounding.go:20-24` `roundSignificant` vs `roundScale` | ✓ |
| 31 | `rounding.go:30-34` HALF_UP only, ordinal 4, all other modes refused | ✓ exact |
| 32 | `nexus/…/ledger/money.go:10-19` `DECIMAL(19,6)` / converts exactly or errors | ✓ (±1 line) |
| 33 | `.softhouse/patterns.md:81` and `docs/softhouse-engagement-plan.md:68` | ✓ both exact quotes |

**Rate: 32 of 33 confirmed (97.0%). 1 of 33 (3.0%) does not support its claim.** One further claim
(N16's "runs it on a schedule") is partially unsupported and is graded separately as F-8, because it
is a prose claim rather than a `FILE:LINE`. This is a high accuracy rate; T489's stated discipline
("every such citation is a line this worker opened and read") largely holds.

---

## 6. Findings

### F-1 — **MAJOR.** N17 `organisation/teller` is a FALSE NOT-APPLICABLE: it is `tierB-branch`'s own service layer

**T489's claim.** Row N17, *"Teller / cashier management, `…/organisation/teller`, 1,225 LOC,
NOT-APPLICABLE(d) — till allocation and cashier cash management. Not required for an NBFI lending
launch; deferred."* §8.1 lists teller among the eleven deferred (d) rows the program will
*"launch without."*

**My independent derivation.** `tierB-branch` in `program.json` has exactly one
`fineract_paths` entry: **`"fineract-branch"`**. I measured and enumerated both halves:

| Module | Contents | Files | LOC |
|---|---|---|---|
| `fineract-branch/…/organisation/teller/` | `api/` (4), `data/` (8), `domain/` (+`model/request/`) (19), `exception/` (8), `handler/`, `util/` | 50 | 3,937 |
| `fineract-provider/…/organisation/teller/` | **`service/TellerManagementReadPlatformServiceImpl.java`, `service/TellerWritePlatformServiceJpaImpl.java`, `starter/OrganisationTellerConfiguration.java`** | 3 | **1,225** |

They are **the same Java package `org.apache.fineract.organisation.teller` split across two Gradle
modules** — and the provider half is the *service implementation* half, i.e. the behaviour.

**This is exactly the module-split pattern T489 itself documents in §5.6 and applies correctly to
four other cases (`portfolio`, `batch`, `accounting`, `dataqueries`). It missed this fifth one, and
missed it in the expensive direction:** instead of reassigning it, the audit deletes it.

**Two consequences, both bad.**
1. **1,225 LOC of an active Tier B context is classified "never port."** `tierB-branch` is
   `status: pending` in `program.json` — the program intends to port it. The audit and the program
   now contradict each other about whether teller ships.
2. **`tierB-branch` as currently scoped would be ported without its service layer** — precisely the
   trap T489 quotes `tierA-a2-behaviour.md` §1.2 for (*"ported without their own entities"*), only
   inverted: here the *entities* are in scope and the *services* are not.

**What should change.** Reclassify N17 as **R5 — reassign to `tierB-branch`**, and add
`"fineract-provider/src/main/java/org/apache/fineract/organisation/teller"` to
`tierB-branch.fineract_paths` (raising its `main_loc` from 3,937 to 5,162). Corrected subtotals,
which still sum to 192,168:

```
reassign 38,750  +  not-applicable 67,495  +  partial 2,190  +  gap 83,733  =  192,168   ✓
```

and §8.1's deferred-(d) subtotal drops from 51,196 to **49,971**.

---

### F-2 — **MAJOR (citation).** `RoutingDataSource.java:49,108-115` does not support the claim it is cited for

**T489's claim (row N8).** *"`RoutingDataSource.java:49,108-115` resolves a datasource from
`ThreadLocalContextUtil.getTenant()`."*

**My derivation — I opened all three regions.**
- **`:49`** is `public class RoutingDataSource extends AbstractDataSource {` — the **class
  declaration**. It resolves nothing.
- **`:108-115`** is the body of `private String tenant()`, which builds a **display string for
  logging** (`return tenant.getTenantIdentifier() + "/connection:" + …`). It is called only from
  `logConnectionCheckout` / `logConnectionCheckoutFailure`. It resolves no datasource.
- The **actual** resolution is `determineTargetDataSource()` at **`RoutingDataSource.java:73-75`**:
  `return this.dataSourceServiceFactory.determineDataSourceService().retrieveDataSource();`
  called from `getConnection()` at `:61-62` and `:78-79`. The per-tenant pool is built in
  `DataSourcePerTenantServiceFactory.java` (I read `:70-96`: it reads
  `tenantConnection`, branches on `fineractProperties.getMode().isReadOnlyMode()`, and builds a
  `HikariConfig` with `toJdbcUrl(...)` and pool name `schemaName + "_pool"`).

**Assessment.** The **classification is unaffected** — multi-tenant datasource routing genuinely
exists and N8(d) is a defensible PRODUCT call. But the citation is decorative rather than
load-bearing, and the review brief grades a citation that does not support its claim as MAJOR.

**What should change.** Replace the citation with
`RoutingDataSource.java:61-62,73-75` **and** `DataSourcePerTenantServiceFactory.java:70-96`.

---

### F-3 — **MAJOR.** N8's prose classifies `FineractPlatformTenant{,Connection}` as NOT-APPLICABLE, but they live in G1 — and one of them carries the tenant timezone

**T489's claim (row N8).** *"…multi-tenant routing (~896 LOC with `DataSourcePerTenantServiceFactory`,
`TomcatJdbcDataSourcePerTenantService`, `FineractPlatformTenant{,Connection}`) that a
single-licensed-entity deployment does not use."*

**My derivation.** Both named classes are in `fineract-core/…/infrastructure/core/**domain**/`:
`FineractPlatformTenant.java` and `FineractPlatformTenantConnection.java` (the latter is where
`toJdbcUrl` is defined, at `:117`). N8's LOC figure (2,605) is exactly
`…/infrastructure/core/service/database`, so **the partition arithmetic does not include these two
files in N8** — they fall in **G1**, whose evidence line explicitly counts `core/domain` (1,267).
The row's prose therefore reaches outside its own path boundary.

**Why that is MAJOR rather than cosmetic.** `FineractPlatformTenant.getTimezoneId()` is the **sole
source** read by `DateUtils.getDateTimeZoneOfTenant()` (`DateUtils.java:65-67`, §4.2) — the code
path that satisfies CLAUDE.md's *two time zones, no DST, never hard-code an offset*. I count **30
files** in main source calling `ThreadLocalContextUtil.getTenant()` and **32** referencing
`FineractPlatformTenant`. A planner reading N8's row alone, and dropping the classes it names, would
delete the tenant context object and with it the only non-hard-coded timezone source. This is the
"false NOT-APPLICABLE silently deletes a subsystem" failure mode, reached through prose rather than
arithmetic.

**What should change.** Strike `FineractPlatformTenant{,Connection}` from N8's prose and add one
sentence: *the tenant **context object** (`FineractPlatformTenant`, `ThreadLocalContextUtil`) is
retained under G1 and carries the tenant timezone; only the **routing** machinery under
`core/service/database` is NOT-APPLICABLE.*

---

### F-4 — **MAJOR.** N9 `entityaccess`: the class is right (I verified what T489 did not), but the row omits its **Tier A** call sites

This is the row the brief asked me to attack first, and T489 nominated as its least-confident call.

**T489's claim (row N9).** *"An optional office↔product visibility matrix …, gated by global
configuration and off by default. If branch-scoped product visibility is wanted it is a policy rule
in `tierB-branch`, not a 2.4k-LOC subsystem."* §9.1 concedes it *"did **not** verify that it is off
by default, and did not check whether `tierB-branch` depends on it."*

**My derivation — I did both checks.**

**(a) It is off by default. CONFIRMED.**
`fineract-provider/src/main/resources/db/changelog/tenant/parts/0002_initial_data.xml`:
- **:186-194** seeds `c_configuration` id 20, `office-specific-products-enabled`, `value = 0`,
  **`enabled = false`**;
- **:195-204** seeds id 21, `restrict-products-to-user-office`, `value = 0`,
  **`enabled = false`**.

The enforcement point, `FineractEntityAccessUtil.java:79-100` and `:104-125`, gates *every* behaviour
behind `property.isEnabled()` on `OFFICE_SPECIFIC_PRODUCTS_ENABLED`. Off by default is therefore a
fact, not an assertion. Sample-data dumps agree (`load_sample_data.sql:369-370`, `barebones_db.sql:292-293`).

**(b) `tierB-branch` does NOT depend on it. CONFIRMED.**
`grep -rn "entityaccess" fineract-branch/` → **0 hits**. `fineract-branch` is teller/cashier
management (50 files, §F-1), with no product-visibility concern.

**So the NOT-APPLICABLE class survives, and I say so as my own finding.** T489's nominated worry is
resolved in its favour.

**But the row is materially incomplete, and the omission lands on Tier A.** I enumerated every main-source
importer of `org.apache.fineract.infrastructure.entityaccess` outside its own package — **22 import
statements across 11 files**, and **not one of them is in `fineract-branch`**:

| Caller | Context that owns it |
|---|---|
| `portfolio/loanaccount/serialization/LoanApplicationValidator.java` (6 imports) | **Tier A** — loan lifecycle |
| `portfolio/loanproduct/service/LoanProduct{Write,Read}PlatformService*.java`, `loanproduct/starter/LoanProductConfiguration.java` | **Tier A** — loan product |
| `portfolio/charge/service/Charge{Read,Write}PlatformService*.java`, `charge/starter/ChargeConfiguration.java` | **Tier A** — charges |
| `portfolio/savings/service/SavingsProduct{Read,Write}PlatformService*.java`, `savings/starter/SavingsConfiguration.java` | **Tier B** — savings |

The sharpest one, opened and read —
`LoanApplicationValidator.java:1853-1866`, `private void officeSpecificLoanProductValidation(...)`:
when the flag is on it looks up `FineractEntityToEntityMapping` and **throws
`NotOfficeSpecificProductException(productId, officeId)`** if the product is not mapped to the
applicant's office. That is a **validation on the loan-application path** — Tier A's territory.

**Why MAJOR.** The audit is the artefact Tier A will plan from. As written, a Tier A porter reaching
`LoanApplicationValidator` finds a call into a subsystem this audit deleted, with nothing telling
them what to do. They will either port a dangling dependency or silently drop a validator, and
neither choice is recorded anywhere.

**What should change.** Keep N9 NOT-APPLICABLE, add the verification I supplied (the two
`0002_initial_data.xml` seeds), and add the **port-time obligation**: *entityaccess is called from 11
Tier A/B files; because both global flags are seeded `enabled = false`, the ported call sites resolve
to the disabled path — empty `IN` clause, no mapping saved, `officeSpecificLoanProductValidation` a
no-op — and each ported call site must say so in a comment rather than omit the check silently.*
Then record it in `program.json` so it reaches the Tier A planner, not only this document.

---

### F-5 — MINOR. Row N9 states as fact what §9.1 admits was unverified

Row N9 asserts *"off by default"* flatly; §9.1 says *"I did **not** verify that it is off by
default."* An internal contradiction in a document whose stated discipline is that every claim is a
line the author read. The fact is true (F-4a), so nothing downstream is wrong — but the row
overstated its evidence, which is the habit the **†** marker exists to prevent. **Change:** cite the
`0002_initial_data.xml:186-204` seeds in the row and delete the concession from §9.1.

### F-6 — MINOR. *"Oracle Database does not appear in Fineract at all"* over-claims by one word

`fineract-core/…/infrastructure/core/exception/ErrorHandler.java:74` reads
`DEADLOCK("60"), // Oracle: deadlock` — a vestigial comment on an SQLState code. Also, T489's grep
covered only the Tier C paths while the §5.1 heading claims the whole codebase; **I ran it tree-wide
and the substantive conclusion holds** (§4.4). **Change:** narrow the heading to *"no Oracle Database
**dependency, driver, dialect or support code** appears in Fineract"* and note the one comment, so
the next agent who greps `oracle` and gets a hit does not think the audit was wrong.

### F-7 — MINOR. §1.2 says "a 273-line residual"; row G17 says 42

The partition sums exactly with **G17 = 42** (`DataIntegrityErrorHandler.java`, which I measured at
exactly 42 lines). 273 = G16 (`core/util`, 231) + G17 (42) — the two rows §8 folds into G1. The
arithmetic is right; the sentence is not. **Change:** say "42-line residual (G17)".

### F-8 — MINOR. N16 `adhocquery`: "runs it on a schedule" is not supported by the pinned tree

**Confirmed:** `AdHoc.java:46-47` is `@Column(name = "query", length = 2000) private String query;`
— user-supplied query text is genuinely stored, and `:58-62` carry
`report_run_frequency_code` / `report_run_every`. **Not confirmed:** any executor.
`grep -rn "AdHoc" fineract-provider/src/main fineract-core/src/main` outside `adhocquery/` returns
only `portfolio/search`'s unrelated `AdHocQuerySearchRequest` / `AdHocSearchQueryData` classes;
`grep -rn "AdHoc" …/infrastructure/jobs/` returns **nothing**. In the pinned tree the schedule
columns are stored but nothing reads them to execute the query. **This strengthens the
NOT-APPLICABLE class** while weakening the security argument T489 used to escalate it from a
deferral to a *"recommended permanent exclusion."* **Change:** keep NOT-APPLICABLE, restate the
argument as *stores an unexecuted arbitrary-SQL surface*, and drop the escalation to permanent
exclusion or mark it explicitly as the author's own recommendation `[chosen_by: agent]`.

### F-9 — MINOR. `ClientPersonConstants.java:27` is not a "two-name defect"

Lines 27-29 read `FIRST_NAME_COL = 0`, `LAST_NAME_COL = 1`, **`MIDDLE_NAME_COL = 2`** — a
three-field *Western* name model. Still incompatible with ovog / patronymic / given name, so the
collision is real, but calling it the "two-name defect" mislabels it and could send a later reader
looking for two columns. **Change:** *"a Western first/middle/last name model, not ovog/patronymic/given."*

### F-10 — MINOR. N7 undercounts the hook processors

`HookProcessorProvider.java:41-47` dispatches to **four** beans — `twilioHookProcessor`,
`webHookProcessor`, `elasticSearchHookProcessor` and **`messageGatewayHookProcessor`** — not
*"two vendor bridges and one generic webhook."* Class unaffected.

### F-11 — MINOR. N19 `instancemode` is correctly classified but justified from doctrine, not evidence

**LOC confirmed:** `fineract-core/…/infrastructure/instancemode` = 2 files / **155**;
`fineract-provider/…/infrastructure/instancemode` = 2 files / **124**; total **279** ✓.
T489's stated reason is *"Nexus is a single binary"* — which is U-1 doctrine, the very thing §2
forbids relying on. **A stronger, evidence-based reason is available and I derived it:** I read
`FineractInstanceModeApiFilter.java:42-73` — it is an HTTP filter that rejects requests with
`405 METHOD_NOT_ALLOWED` based on `fineractProperties.getMode().isReadEnabled()` /
`isWriteEnabled()` / `isBatchManagerEnabled()`. It is **Fineract's own deployment topology**, has no
domain behaviour and produces no gradeable output, so it is NOT-APPLICABLE(c) **regardless of what
Nexus turns out to be**. **Change:** swap the justification. *Operational note worth adding:*
`DataSourcePerTenantServiceFactory.java:72-80` uses `getMode().isReadOnlyMode()` to swap to
read-only schema servers — directly useful for running the reference oracle read-only during the
shadow-parity window CLAUDE.md requires. That is an *operating* the oracle concern, not a port.

### F-12 — MINOR. §3.1's "roughly 15k" conformance lines is 16,715

Of **25,628** non-test Go lines, the two `conformance` packages are **16,715 (65%)**. T489's
qualitative point ("the majority of Nexus's non-test Go code is the harness") is right and, at 65%,
slightly stronger than stated. All other §3.1 figures (**70** `.go` files, **40,242** total,
**25,628** non-test) reproduce exactly.

### F-13 — MINOR (condition, not error). N4 `creditbureau`'s capability transfer must reach `program.json`

The row's class is **NOT-APPLICABLE**, but its text says the *capability* (pull a bureau report
before origination) belongs to `tierB-loan-origination`. §7.3 rec 3 asks that the NOT-APPLICABLE set
be recorded "so no future run proposes a bulk-import or campaigns task." If only the **class**
propagates and not the **transfer note**, credit-bureau integration silently leaves the program —
and Mongolian NBFI lending has credit-information obligations `[UNVERIFIED: no Mongolian
credit-information specification was available to this session; I could not check the obligation and
did not try to]`. Same shape applies to N15 → G4 and N3 → G12, which T489 *does* handle explicitly in
the row text. **Change:** carry the capability-transfer notes into `program.json`, not just this doc.

---

## 7. Claims I could not falsify, versus claims I confirmed

The brief is right that these are different, so I separate them.

**Confirmed by independent derivation** (I re-ran the measurement or opened the code myself):
the oracle pin; 192,168 / 2,235; the exhaustive non-overlapping partition and all 44 row LOCs; the
zero-NEXUS-PROVIDES structural claim and every line of its evidence; the 37,525 misfiled LOC and the
`dataqueries` duplicate; all five non-negotiable claims (§4); `fineract-db` = 0 Java; 271 files /
93,498 changelog lines; G17 = `DataIntegrityErrorHandler.java` at 42 lines; N9 off-by-default and
`tierB-branch`'s non-dependence on it; the F-1 teller split; 32 of 33 citations.

**Could not falsify, but did not independently confirm** (I accepted the row's reasoning without
re-deriving it): the classification arguments for N1–N7, N10–N13, N15, N18, N20, N22 and G1–G11,
G13–G16 — about 32 rows. Their **LOC** are confirmed; their **class** rests on T489's stated
argument, which I read and found internally coherent but did not test against the code.

**`[UNVERIFIED]` in my own review:**
- **V-1** — everything the Gerege Nexus platform actually provides. Same as T489's U-1, same reason,
  and I looked in the five places listed in §2. This is a repository-contents fact, not a search
  failure.
- **V-2** — whether `program.json`'s `main_loc: 180000` excluded a path, a source set or licence
  headers. I did not reconstruct the earlier recipe either.
- **V-3** — Mongolian regulatory obligations bearing on N4 (credit bureau), N6 (report mailing) and
  N13 (surveys). No FRC specification was available to this session.
- **V-4** — whether the **†** split inside G5/G6 (authN host-supplied, authZ not) is at the right
  line. I did not read `SpringSecurityPlatformSecurityContext` end to end. T489 flags the same as
  U-5; I inherit the uncertainty rather than resolve it.
- **V-5** — runtime behaviour of anything. There is no running Fineract and no PostgreSQL here.
  Every "off by default", "throws", "rejects" claim above is a claim about code and seed data I read.

---

## 8. Contradictions with CLAUDE.md found during this review

Per the rules binding me, a contradiction is a finding, not something I fix.

1. **`tierC-platform-map-first.go_target` is `nexus/internal/platform`, which does not exist.**
   `find nexus -type d` returns no `internal/platform`. The context is configured to write into a
   directory that has never been created. Non-blocking, but it should be corrected alongside the
   `main_loc` change.
2. **`dataqueries` violates CLAUDE.md's per-run scope guard by construction** (§3): 8,295 LOC is
   inside two contexts' `fineract_paths` at once, so one of the two runs *must* touch files assigned
   elsewhere. This should be fixed in `program.json` before either context is planned.
3. **F-1's teller split puts the audit and `program.json` in direct conflict** over whether
   `tierB-branch` ships. One of them must move; §F-1 says which.

I did not write Go, did not touch `nexus/`, did not create a vector, did not amend a DEC-n or the
frozen contract, and did not modify the pinned oracle checkout (`git status --porcelain` empty,
re-checked after all reads).

---

## 9. Verdict

# ACCEPT WITH CONDITIONS

T489 is a strong piece of work. Its central structural finding — that the Nexus platform tree is not
in this repository, so no honest NEXUS-PROVIDES row can be written and 50,846 LOC must be parked
pending a re-grade — **I derived independently and reach the same conclusion.** Its measurement is
exact: I reproduced the 192,168 / 2,235 total, verified the partition is genuinely exhaustive and
non-overlapping by decomposing every parent directory, and every one of the 44 row LOC figures
reproduces. Its five non-negotiable claims all hold at the cited lines, including the correction of a
belief this program has repeated about Oracle Database. Its citation discipline measures at 97%.

It is not accepted as-is because of **4 MAJOR findings**, all of which are edits to the document
rather than a re-audit.

**Conditions — all four must be applied before the audit is used to plan:**

1. **F-1 — reclassify N17 `organisation/teller` from NOT-APPLICABLE to reassign (R5 →
   `tierB-branch`)**, and add
   `fineract-provider/src/main/java/org/apache/fineract/organisation/teller` to
   `tierB-branch.fineract_paths`. Restate the subtotals as
   `38,750 / 67,495 / 2,190 / 83,733 = 192,168` and the deferred-(d) subtotal as 49,971.
   *This is the one finding that would otherwise delete a subsystem the program intends to build.*
2. **F-4 — add entityaccess's 11 Tier A/B call sites and the resulting port-time obligation to N9**,
   with the off-by-default verification I supplied (`0002_initial_data.xml:186-204`), and record it
   where the Tier A planner will see it. The NOT-APPLICABLE class stands.
3. **F-3 — strike `FineractPlatformTenant{,Connection}` from N8's prose** and state that the tenant
   context object is retained under G1 and carries the tenant timezone.
4. **F-2 — replace the `RoutingDataSource.java:49,108-115` citation** with
   `RoutingDataSource.java:61-62,73-75` and `DataSourcePerTenantServiceFactory.java:70-96`.

**Recommended (MINOR, not blocking):** F-5 through F-13, each a one- or two-line edit.

**Endorsed without change:** recommendation **R-1** (attach the Nexus platform tree and re-grade the
7 **†** rows) — I independently agree it outranks everything else in the document; gate **G-C1**
(three-field names vs schema-first) is correctly routed to `user`; backlog **B-1** (the four — now
five — path moves), **B-2** (per-office timezone), **B-3** (the legacy command bus is the port
target, not `fineract-command*`) and **B-4** (the Liquibase changelog is an unrecorded program
dependency).

### Is the audit safe to plan Tier C from?

**Yes, with the four conditions applied — and with one boundary stated plainly.**

- **Safe now:** the *shape* of Tier C. The measured surface, the partition, the reassignments, the
  NOT-APPLICABLE set and the slice order C-1 → C-5 are sound and independently reproduced. Slices
  C-1 (business date + working days + holidays), C-2 (command bus / maker-checker / idempotency),
  C-3 (codes, account-number formats, global configuration), C-4 (organisation) and C-5 (in-process
  business events) are **not** marked **†** and can be planned against this document. C-4 remains
  correctly blocked on gate G-C1.
- **Not safe, and the audit says so itself:** anything **†**. 50,846 LOC across G1, G2, G4, G5, G6,
  G7, G11 is unresolved in **both** directions, and no plan should schedule a port task for those
  rows until R-1 resolves them. Planning them now risks precisely the unjustified plumbing port
  CLAUDE.md calls a rejection.
- **Not established at all:** that Tier C costs 83,733 LOC rather than ~33,000. That number is a
  ceiling with an unmeasured floor, and the program should carry it as a range, not a figure.

The audit's willingness to report "I cannot complete this as commissioned, and here is exactly why"
rather than manufacture NEXUS-PROVIDES rows from doctrine is the reason it is safe to plan from at
all. That judgement was correct and I would have made the same one.

---

*T492 · 4 MAJOR · 9 MINOR · 33 citations sampled, 32 confirmed (97.0%) · 44 of 44 row LOCs
re-measured, ~12 of 44 classifications re-derived in depth · verdict ACCEPT WITH CONDITIONS.*
