# T329 — the oracle reports two different dates for the same instant, and the wire carries no marker

**FU-T327-1.** T327 observed, on one instance, seconds apart:

| endpoint | field | wire value | shape |
|---|---|---|---|
| `GET /glclosures` | `createdDate` | `"2026-08-27"` | **string** |
| `GET /journalentries?transactionId=…` | `createdDate` | `[2026,8,28]` | **int array** |

Same instant. Same instance. Same field NAME. **Two different dates and two different wire shapes.**
T327 marked the cause `[UNVERIFIED]`. This document supplies the cause, from the pinned source.

**Source of record: `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`** — verified with
`git rev-parse HEAD` at the time of writing; working tree reports the same commit as `.softhouse`'s
recorded pin and as `oracle.fineract_commit` in every ledger vector.

**No oracle contact was made by this task.** Every claim below is source-derived or read from
T327's committed bytes under `.softhouse/capture/t327-closure-accepting-side/`.

---

## 0. The headline, in one paragraph

The two fields are **not the same quantity and never were**. They share a name and nothing else.

- `/glclosures` `createdDate` is an **audit row-insertion timestamp**, truncated to a date, stamped
  from `ZoneId.systemDefault()` — the **JVM/container** zone.
- `/journalentries` `createdDate` is **an alias for `submittedOnDate`**, which is the **business
  date**, seeded from the **tenant** zone.

So this is **two defects stacked**, and they must be fixed separately:

1. **A SHAPE fork** — two serialisation stacks (Gson vs Jackson), decided per DTO **class**.
2. **A SEMANTIC collision** — one field name, `createdDate`, carrying an audit timestamp on one
   endpoint and a business date on the other. **This is the dangerous one.** The zone difference is
   a *symptom* of it, not the disease.

A port that "fixes the timezone" fixes nothing, because the two fields would still disagree even if
both clocks were in the same zone — they measure different things.

---

## 1. The SHAPE fork — why one is a string and the other an int array

### 1.1 Two serialisation stacks, chosen by how the resource method returns

**`/journalentries` — the GSON stack.**
`JournalEntriesApiResource` holds a `DefaultToApiJsonSerializer<Object>` and returns a **String**:

- `[VERIFIED: fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/api/JournalEntriesApiResource.java:93]`
  `private final DefaultToApiJsonSerializer<Object> apiJsonSerializerService;`
- `[VERIFIED: …/JournalEntriesApiResource.java:166]`
  `return this.apiJsonSerializerService.serialize(settings, glJournalEntries, RESPONSE_DATA_PARAMETERS);`
  (and `:189`, `:219`, `:243`, `:259`, `:274`, `:303` — every other method on the resource does the same)

The Gson instance registers a `LocalDate` adapter that emits a **three-element int array**:

- `[VERIFIED: fineract-core/src/main/java/org/apache/fineract/infrastructure/core/serialization/GoogleGsonSerializerHelper.java:105-115]`
  `registerTypeAdapters(GsonBuilder)`, with `:107` `builder.registerTypeAdapter(LocalDate.class, new LocalDateAdapter());`
- The adapter it registers is `org.apache.fineract.infrastructure.core.api.LocalDateAdapter`
  `[VERIFIED: GoogleGsonSerializerHelper.java:37]` (the import), whose `serialize` builds a `JsonArray`
  of `YEAR_OF_ERA`, `getMonthValue()`, `getDayOfMonth()`
  `[VERIFIED: fineract-core/src/main/java/org/apache/fineract/infrastructure/core/api/LocalDateAdapter.java:38-47]`.

**Its own class comment is the smoking gun**
`[VERIFIED: core/api/LocalDateAdapter.java:30-33]`:

> "Serializer for Java Local Time `{@link LocalDate}` that returns the date **in array format to
> match previous Jackson functionality**."

The Gson adapter exists to imitate an **old** Jackson configuration. The **current** Jackson
configuration no longer behaves that way — which is precisely how the two endpoints drifted apart.

**`/glclosures` — the JACKSON stack.**
`GLClosuresApiResource.retrieveAllClosures` returns the **POJO list directly**; it never touches the
serializer field:

- `[VERIFIED: fineract-accounting/src/main/java/org/apache/fineract/accounting/closure/api/GLClosuresApiResource.java:91-95]`
  `public List<GLClosureData> retrieveAllClosures(…) { … return glClosureReadPlatformService.retrieveAllGLClosures(officeId); }`
- likewise `retreiveClosure` `[VERIFIED: GLClosuresApiResource.java:109-120]` returns `GLClosureData`.
- The class *does* hold a `DefaultToApiJsonSerializer<GLClosureData>`
  `[VERIFIED: GLClosuresApiResource.java:78]`, but the two GET methods do not use it — it is used only
  to serialise the **request** body on POST/PUT `[VERIFIED: GLClosuresApiResource.java:132, :147]`.

Jersey/Jackson therefore writes the response, using the ObjectMapper bean at
`[VERIFIED: fineract-provider/src/main/java/org/apache/fineract/infrastructure/core/jersey/JerseyJacksonConverterConfig.java:40-57]`.

### 1.2 On the Jackson side, the shape is a per-CLASS opt-in

The mapper registers `JacksonLocalDateArrayModule`
`[VERIFIED: JerseyJacksonConverterConfig.java:55]`, which installs a `BeanSerializerModifier`
`[VERIFIED: fineract-provider/…/core/jersey/serializer/legacy/JacksonLocalDateArrayModule.java:26-28]`.

That modifier branches on a **class-level annotation**
`[VERIFIED: fineract-provider/…/core/jersey/serializer/JacksonLocalDateBeanSerializerModifier.java:39-48]`:

```java
if (beanDesc.getBeanClass().isAnnotationPresent(JsonLocalDateArrayFormat.class)) {
    assignLocalDateSerializer(beanProperties, localDateArraySerializer);   // -> [y, m, d]
} else {
    assignLocalDateSerializer(beanProperties, localDateSerializer);        // -> "yyyy-MM-dd"
}
```

- **array branch** → `JacksonLocalDateArraySerializer`, writes `writeStartArray / year / monthValue /
  dayOfMonth / writeEndArray`
  `[VERIFIED: …/serializer/legacy/JacksonLocalDateArraySerializer.java:30-41]`
- **string branch** → `LocalDateJsonConverter`, writes `generator.writeString(ISO_LOCAL_DATE.format(value))`
  `[VERIFIED: fineract-provider/…/core/jersey/converter/LocalDateJsonConverter.java:31, :44-48]`

The annotation is `@Target(ElementType.TYPE)`
`[VERIFIED: fineract-core/…/core/jersey/serializer/legacy/JsonLocalDateArrayFormat.java:26-28]`.

**Consequence, and it matters for the port:** on the Jackson stack the shape is decided **per DTO
class, never per field**. Every `LocalDate` on one DTO shares one shape. You cannot read the shape
off a field name; you must know which class — and which stack — produced it.

**`GLClosureData` is NOT annotated.** Its declaration carries only Lombok's `@Data`
`[VERIFIED: fineract-accounting/…/closure/data/GLClosureData.java:34-35]`; there is no
`@JsonLocalDateArrayFormat` anywhere in the file. Hence the **string** branch, hence
`"2026-08-27"`, and hence also `closingDate: "2026-08-26"` and `lastUpdatedDate: "2026-08-27"` in
the same response — **all three of its `LocalDate` fields are strings**
`[VERIFIED: GLClosureData.java:43, :45, :46]`, and T327's captured bytes show exactly that
`[VERIFIED: .softhouse/capture/t327-closure-accepting-side/throwaway/out/B1-glclosures-list.json]`.

### 1.3 The complete opt-in list — 9 classes, program-wide

Every class in the pinned checkout carrying `@JsonLocalDateArrayFormat`
(`grep -rln "JsonLocalDateArrayFormat" --include="*.java" .`, excluding the three
`core/jersey/serializer/` machinery files that merely define or reference it):

| # | class | module |
|---|---|---|
| 1 | `infrastructure/businessdate/data/api/BusinessDateResponse.java` | fineract-core |
| 2 | `infrastructure/businessdate/data/api/BusinessDateUpdateResponse.java` | fineract-core |
| 3 | `portfolio/savings/data/SavingsAccountApplicationTimelineData.java` | fineract-core |
| 4 | `portfolio/savings/data/SavingsAccountChargeData.java` | fineract-core |
| 5 | `portfolio/savings/data/SavingsAccountData.java` | fineract-core |
| 6 | `portfolio/savings/data/SavingsAccountSummaryData.java` | fineract-core |
| 7 | `portfolio/savings/data/SavingsAccountTransactionData.java` | fineract-core |
| 8 | `portfolio/shareaccounts/data/ShareAccountApplicationTimelineData.java` | fineract-provider |
| 9 | `portfolio/shareaccounts/data/ShareAccountTransactionData.java` | fineract-provider |

**No accounting DTO is on this list.** So on the Jackson stack, everything in the GL/accounting
slice serialises `LocalDate` as an **ISO string**; anything still on the Gson stack serialises it as
an **int array**. The slice is split by stack, not by annotation.

**Note the trap in row 1:** `BusinessDateResponse` — the endpoint a port would naturally call to
*learn the business date* — is **array**-shaped, while `/glclosures` is string-shaped. A port that
hard-codes one parser for "dates from the oracle" breaks on one or the other.

### 1.4 A third shape, inside our own store

The vector store encodes dates in a **third** shape again: `loanschedule` vectors carry
`"schedule_start_date": {"year":2024,"month":1,"day":1}` — a JSON **object**
`[VERIFIED: .softhouse/vectors/loanschedule/P-00-baseline-6x7pct.json and all 40 sibling
loanschedule vectors]` — while `ledger` vectors carry ISO strings
`[VERIFIED: .softhouse/vectors/ledger/LDG-REFUSE-04-preclosure-entry-on-closing-date.json,
request.transaction_date "2026-01-31"]`. Recorded so nobody "unifies" the wire shape and assumes
the store already matches it. **Three shapes are in play: array, string, object.**

---

## 2. The ZONE / SEMANTIC fork — which clock stamps each field

This is the half that actually threatens correctness, and it is **not** a timezone bug.

### 2.1 `/journalentries` `createdDate` is not a creation timestamp at all

`JournalEntryData.createdDate` is assigned **the value of `submittedOnDate`**, in the constructor:

- `[VERIFIED: fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/data/JournalEntryData.java:211]`
  `this.createdDate = submittedOnDate;`
- `[VERIFIED: …/JournalEntryData.java:212]` `this.submittedOnDate = submittedOnDate;`

The two fields are declared separately `[VERIFIED: JournalEntryData.java:63, :82]` and then filled
from **one** source. That is why T327's capture shows them equal —
`"createdDate": [2026,8,28]` and `"submittedOnDate": [2026,8,28]`
`[VERIFIED: .softhouse/capture/t327-closure-accepting-side/throwaway/out/B1-ACCEPT-06-readback-rest.json]`.

**There is no `created_date` column in the journal-entry SQL at all.** The row mapper selects
`journalEntry.submitted_on_date as submittedOnDate`
`[VERIFIED: fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/JournalEntryReadPlatformServiceImpl.java:100]`,
reads it at `[VERIFIED: …/JournalEntryReadPlatformServiceImpl.java:160]`
`final LocalDate submittedOnDate = JdbcSupport.getLocalDate(rs, "submittedOnDate");`
and passes it into the constructor at `[VERIFIED: …:232]`.

`grep -n "createdDate\|created_date\|created_on_utc" JournalEntryReadPlatformServiceImpl.java`
returns **no hit for any created-date column** — a statement about that grep over that file, which I
ran; the field is synthesised in the DTO, not selected from the database.

**And `submitted_on_date` is the BUSINESS DATE**, written from the tenant-zone clock:

- `[VERIFIED: fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/domain/JournalEntry.java:106-107]`
  `@Column(name = "submitted_on_date", nullable = false) private LocalDate submittedOnDate;`
- `[VERIFIED: …/JournalEntry.java:136]` `this.submittedOnDate = DateUtils.getBusinessLocalDate();`
- `[VERIFIED: fineract-core/…/core/service/DateUtils.java:238-240]`
  `getBusinessLocalDate() { return ThreadLocalContextUtil.getBusinessDate(); }`
- With `enable-business-date` off (the state on both the standing oracle and T327's throwaway),
  that is seeded from the **tenant** zone:
  `[VERIFIED: fineract-core/src/main/java/org/apache/fineract/infrastructure/businessdate/service/BusinessDateReadPlatformServiceImpl.java:74-75]`
  `LocalDate tenantDate = DateUtils.getLocalDateOfTenant(); businessDateMap.put(BusinessDateType.BUSINESS_DATE, tenantDate);`
- `[VERIFIED: DateUtils.java:70-72]` `getLocalDateOfTenant() { return LocalDate.now(getDateTimeZoneOfTenant()); }`
- `[VERIFIED: DateUtils.java:65-68]` `getDateTimeZoneOfTenant()` = `ZoneId.of(tenant.getTimezoneId())`
  — read from the tenant row, **never a literal offset**.

I re-derived `BusinessDateReadPlatformServiceImpl:74` independently rather than inheriting T327's
citation; it holds.

### 2.2 `/glclosures` `createdDate` IS an audit timestamp, in the JVM zone

- The mapper selects the audit column: `glClosure.created_date as createdDate`
  `[VERIFIED: fineract-accounting/src/main/java/org/apache/fineract/accounting/closure/service/GLClosureReadPlatformServiceImpl.java:46]`,
  read at `[VERIFIED: …:61]` `JdbcSupport.getLocalDate(rs, "createdDate")` — **a `LocalDateTime`
  column truncated to a date by the read.**
- `GLClosure extends AbstractAuditableCustom`
  `[VERIFIED: fineract-accounting/…/closure/domain/GLClosure.java:44]`
- which declares `@Column(name = "created_date") private LocalDateTime createdDate;`
  `[VERIFIED: fineract-core/src/main/java/org/apache/fineract/infrastructure/core/domain/AbstractAuditableCustom.java:46-47]`
- Spring Data auditing picks the clock **by superclass**:
  `[VERIFIED: fineract-provider/src/main/java/org/apache/fineract/infrastructure/core/auditing/CustomAuditingHandler.java:63-69]`

  ```java
  private DateTimeProvider fetchDateTimeProvider(Object bean) {
      if (bean instanceof AbstractAuditableWithUTCDateTimeCustom) { return CustomDateTimeProvider.UTC; }
      else { return CustomDateTimeProvider.INSTANCE; }
  }
  ```

  applied on create at `[VERIFIED: CustomAuditingHandler.java:77-82]` (`markCreated`) and on update
  at `[VERIFIED: …:90-95]` (`markModified`).
- `GLClosure` extends the **non-UTC** base, so it takes `INSTANCE`, which is
  `[VERIFIED: fineract-provider/…/core/auditing/CustomDateTimeProvider.java:42-44]`
  `DateUtils.getLocalDateTimeOfSystem()`
- `[VERIFIED: DateUtils.java:101-104]` `LocalDateTime.now(ZoneId.systemDefault())`

**Precision that matters: it is `ZoneId.systemDefault()`, i.e. the JVM/container zone — NOT "UTC" by
design.** On T327's instance the container had no `TZ` set, so the JVM default was UTC and the field
read `2026-08-27` at `2026-08-27T17:33:40Z`
`[VERIFIED: .softhouse/capture/t327-closure-accepting-side/throwaway/out/B1-SETUP-03-create-glclosure.captured-at-utc`
= `2026-08-27T17:33:40Z`, alongside `B1-glclosures-list.json` `createdDate: "2026-08-27"`].
Calling this field "UTC" is therefore **true of the observation and false of the rule**: change the
container's `TZ` and this field moves, while `/journalentries`' `createdDate` does not.

### 2.3 The disagreement, assembled

Tenant zone on the capture instance was `Asia/Ulaanbaatar`
`[VERIFIED: .softhouse/capture/t327-closure-accepting-side/throwaway/out/F3-target-registry.txt`
= `registry=t327|Asia/Ulaanbaatar|fineract_t327`; seeded by
`FINERACT_DEFAULT_TENANTDB_TIMEZONE: Asia/Ulaanbaatar` at
`throwaway/docker-compose.t327.yml:91`].

At the capture instant `2026-08-27T17:33:40Z`:

| | field | clock | source | value |
|---|---|---|---|---|
| `/glclosures` | `createdDate` | `ZoneId.systemDefault()` (container = UTC) | audit insert timestamp | `2026-08-27` |
| `/journalentries` | `createdDate` | tenant zone `Asia/Ulaanbaatar` (+08) | business date, via `submittedOnDate` | `2026-08-28` |

`17:33Z + 08:00 = 01:33 on the 28th`. **The two disagree for the 8 hours from 16:00Z to 24:00Z every
day** — one third of every day, and silent the other two thirds. T327 landed at 17:33Z, 93 minutes
into that window. **That is the only reason this was ever seen.**

The window width is `tenantOffset − jvmOffset`; it is 8h only because the container ran UTC and the
tenant is +08. For `Asia/Hovd` (+07) it would be 7h. **It is not a constant and must never be
written as one.**

### 2.4 What is NOT established

- `[UNVERIFIED]` **that the standing reference oracle on `:8443` / tenant `gerege` behaves
  identically.** T327's capture was taken on a throwaway with `TZ` unset. I made no oracle contact.
  A container with `TZ=Asia/Ulaanbaatar` would collapse the window to zero and hide the fork
  entirely — which is a *reason to pin the vector, not a reason to relax*.
- ~~`[UNVERIFIED]` the DDL type of `acc_gl_closure.created_date`.~~ **RESOLVED during this task —
  see `blast-radius.md` §C-2.** It is `datetime` `[VERIFIED: db/changelog/tenant/parts/0001_initial_schema.xml:93]`
  → PostgreSQL **`timestamp without time zone`**, and the widening to `datetime(6)` is gated
  `context="mysql"` `[VERIFIED: …/0117_set_datetime_precision.xml:25]` so it never runs for us.
  Because the column carries no zone, Postgres performs **no** conversion on read: the JVM zone is
  the whole story, with no second database-side effect layered on top.
- `[UNVERIFIED]` **whether any Fineract code path writes `acc_gl_closure.created_date` outside JPA
  auditing** (e.g. a Liquibase seed or a raw SQL insert), which would bypass `CustomAuditingHandler`
  entirely.

---

## 3. Blast radius

See **`blast-radius.md`** in this directory: a 16-row per-field table (endpoint x field x stack x
shape x kind x clock), the list of slice endpoints that return no date at all, and two sharp
caveats (the array/string switch does not reach inside `Map` values; the `datetime(6)` migration is
MySQL-gated and inert on PostgreSQL).

---

## 4. What a PORT must do

**Rule P-1 — never infer a date's meaning from its field name.** `createdDate` is an audit timestamp
on `/glclosures` and a business date on `/journalentries`. Any port type that maps both to one Go
field is wrong at the type level, not just the value level. Give them different names:
`closure_audit_created_local_date` vs `journal_entry_submitted_business_date`.

**Rule P-2 — model the three quantities separately, because they are three.**

| quantity | Go type | source of truth | zone dependence |
|---|---|---|---|
| **calendar date** (`transactionDate`, `closingDate`, `submittedOnDate`) | a zone-free civil date | caller / DB `date` column | **none** — do not attach a zone |
| **business date** | a zone-free civil date, but **derived** | tenant business-date service; when disabled, `LocalDate.now(tenantZone)` | **origin is tenant-zone**; the value, once obtained, is zone-free |
| **audit instant** (`created_date`, `lastmodified_date`) | an instant (`time.Time` with location), formatted only at the edge | DB timestamp | **fully zone-dependent** |

**Rule P-3 — the business date is an INPUT, never a clock read.** A port must never call
`time.Now()` to obtain it. `admit.go` and `vector.go` already enforce this and the reasoning there is
correct `[VERIFIED: nexus/internal/apps/ledger/conformance/vector.go:449-467]`; this document is
evidence for keeping it, not for relaxing it.

**Rule P-4 — the tenant zone comes from the tenant row.** `ZoneId.of(tenant.getTimezoneId())`
`[VERIFIED: DateUtils.java:65-68]`. The Go port reads the same column. **No `+08`, no `+07`, no
`Asia/Ulaanbaatar` literal in any code path** — per CLAUDE.md. Both zones are configuration.

**Rule P-5 — the audit zone is a THIRD zone and it is the deployment's, not the tenant's.**
`ZoneId.systemDefault()` `[VERIFIED: DateUtils.java:101-104]`. A port must represent it explicitly
and must not silently equate it to either the tenant zone or UTC. Note Fineract itself has a
UTC-anchored audit base — `AbstractAuditableWithUTCDateTimeCustom` →
`CustomDateTimeProvider.UTC` → `OffsetDateTime.now(ZoneOffset.UTC)`
`[VERIFIED: CustomDateTimeProvider.java:45-47; DateUtils.java:110-112]` — which `GLClosure` does
**not** use. Two audit clocks coexist in the oracle; the port must reproduce the *choice*, per entity.

**Rule P-6 — the deserialiser must accept all three shapes and must not guess.** Decide the shape
from the *endpoint + DTO*, matching §1's table, and **fail loudly on an unexpected shape** rather
than falling back. A tolerant "accept array or string" parser silently masks the very drift that
produced this finding.

**DO NOT hard-code `+08`.** It is the rule this finding threatens, not the fix for it.

---

## 5. What a VECTOR must do

**Rule V-1 — a vector that carries a date must also carry that date's PROVENANCE.** Not just the
value: which clock produced it. Three attributes are needed and none is currently recorded on the
wire-facing side: *stack* (gson-array / jackson-string / jackson-array), *quantity* (calendar /
business / audit-instant), *zone source* (n/a / tenant / jvm).

**Rule V-2 — never grade an audit-timestamp-derived date cell without also pinning the JVM zone.**
`/glclosures.createdDate` is **not gradeable as a stable value**: it depends on the container's `TZ`,
which is deployment configuration and not part of the contract. Either pin `TZ` in the capture rig
and record it in the vector, **or grade the field's absence/shape only, never its value.**

**Rule V-3 — assert RELATIONS, not literals, wherever a wall clock is involved.** T289's date
strategy (c), already in force, is the right instrument and this finding vindicates it.

**Rule V-4 — a vector promoting T327's ACCEPTING captures must not grade `createdDate` as a date.**
This is live and imminent: T327's `B1-ACCEPT-06` / `B2-ACCEPT-01` readbacks are the next queued
promotion, and they contain `createdDate`, `submittedOnDate` and `transactionDate`. Grading
`createdDate` as a literal would bake the 8-hour window into the corpus, and the vector would pass
or fail depending on **what time of day CI runs**. Grade `transactionDate` (a true calendar date,
safe) and, if `submittedOnDate` is graded at all, grade it as a *relation* to `request.business_date`.

---

## 6. Named ambiguous cells in `.softhouse/vectors/`

I swept every vector JSON in the store for date-bearing cells
(`.softhouse/vectors/ledger/*.json`, `.softhouse/vectors/loanschedule/*.json`, plus
`capabilities*.json`, `PIN*.json`, `README.md`) by parsing each file and listing every
`request.*`/`expect.*` key containing "date". **Statement about that sweep:** it covers key *names*
containing `date`; a date hidden under a differently-named key would not be caught.

**Exactly two cells are zone-ambiguous, and they are the same field in two vectors:**

| # | file | cell | value | why ambiguous |
|---|---|---|---|---|
| 1 | `.softhouse/vectors/ledger/LDG-REFUSE-04-preclosure-entry-on-closing-date.json` | `request.business_date` | `"2026-08-23"` | derived by `LocalDate.now(tenantZone)`; **the JSON carries no zone attribution** |
| 2 | `.softhouse/vectors/ledger/LDG-REFUSE-05-future-dated-entry-one-day-after-business-date.json` | `request.business_date` | `"2026-08-23"` | same |

**These are the only two.** `request.transaction_date` and `request.latest_closing_date` are **not**
ambiguous — both are genuine civil dates (a caller-chosen wire value and a `date` column
respectively) with no instant behind them. The `loanschedule` cells
(`schedule_start_date`, `last_repayment_due_date`) are pure calendar arithmetic and are **not**
ambiguous either.

**Severity — stated honestly, because the store is better here than it first looks.** The ambiguity
is **documented in the Go struct** but **not in the JSON**:
`[VERIFIED: nexus/internal/apps/ledger/conformance/vector.go:461-466]` — *"ON THIS TENANT IT IS
DERIVED, NOT PINNED… BusinessDateReadPlatformServiceImpl seeds BUSINESS_DATE with
DateUtils.getLocalDateOfTenant() — today in the TENANT zone."* That is exactly right and predates
this task. So the correct finding is **not** "the store got it wrong"; it is:

> **the provenance lives in one place (`vector.go`) and the data lives in another (the JSON), and
> only the first tells you the zone.** Anyone reading a vector file — a reviewer, a future capture
> rig, an external auditor — sees a bare `"2026-08-23"`.

One nuance worth flagging so it is not over-read: `admit.go`'s comment on the layout constant says
*"NO ZONE AND NO OFFSET APPEARS HERE… These are calendar dates."*
`[VERIFIED: nexus/internal/apps/ledger/conformance/admit.go:24-26]`. As a statement about the
**stored strings** that is true and correct. But it sits over a loop that validates all three date
fields uniformly `[VERIFIED: admit.go:348-352]`, and a reader can easily carry "these are calendar
dates" over to `business_date`'s **origin**, which is not zone-free. **This is an incompleteness, not
a contradiction**, and `vector.go` already supplies the missing half.

**Recommended remedy — NOT APPLIED, as I am an analyst and not the owner of these files:** add a
sibling provenance cell (e.g. `request.business_date_zone_source: "tenant"`) or a short `_note` on
the two vectors, so the JSON is self-describing. `admit.go` is owned by T306 this batch and
`.softhouse/vectors/` is not mine to edit; **I have named the defect and changed nothing.**

---

## 7. What remains `[UNVERIFIED]`

1. That the **standing** oracle (`:8443`, tenant `gerege`) reproduces the fork — no oracle contact made.
2. The **DDL type** of `acc_gl_closure.created_date` (`timestamp` vs `timestamptz`) in the applied schema.
3. Whether any non-JPA path writes `acc_gl_closure.created_date`, bypassing `CustomAuditingHandler`.
4. Whether **other** modules' resources outside the accounting slice mix the two stacks the same way
   — §3's sweep is scoped to accounting plus the business-date endpoint, by design (scope guard).
5. The **runtime** shape of any endpoint listed in §3 that I derived from the source path rather than
   from captured bytes. Only `/glclosures` and `/journalentries` are confirmed **on the wire**, by
   T327's committed captures; every other row in §3 is source-derived and marked as such there.
