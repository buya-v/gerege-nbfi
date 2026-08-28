# T329 §3 — blast radius, per field

**Scope, stated as a statement about the search.** I enumerated every `*ApiResource.java` under any
`*/accounting/*` path in the pinned checkout (`find` → **7 classes**, all listed below), plus
`BusinessDateApiResource` because a port must call it to learn the business date. I then read, for
each resource method, the return statement, the DTO class, whether that class carries
`@JsonLocalDateArrayFormat`, every date-typed field on it, and the SQL/service provenance of each.

**What this sweep does NOT cover, and therefore says nothing about:** resources outside the
accounting slice (loan, savings, client, group, transfers, …). The scope guard applies — one bounded
context per run. Row shapes for savings/shares can be *inferred* from the annotation inventory in
the main README §1.3 but were **not** traced to their mappers here.

**Confidence marker used below:**
- **[WIRE]** — confirmed against T327's committed response bytes.
- **[SRC]** — derived from the pinned source only. Not observed on the wire.

---

## A. The shape/clock table

`SHAPE` = `ARRAY` (`[y,m,d]`) or `STRING` (`"yyyy-MM-dd"`).
`STACK` = `GSON` (resource returns `apiJsonSerializerService.serialize(...)`) or `JACKSON` (resource returns the POJO).
`KIND` = what the value **means**. `CLOCK` = what stamps it.

| # | endpoint | field | STACK | SHAPE | KIND | CLOCK / zone | conf |
|---|---|---|---|---|---|---|---|
| 1 | `GET /v1/glclosures` | `closingDate` | JACKSON | **STRING** | calendar date (`acc_gl_closure.closing_date`, `date`) | none — civil date | **[WIRE]** |
| 2 | `GET /v1/glclosures` | `createdDate` | JACKSON | **STRING** | **audit timestamp** (`acc_gl_closure.created_date`, `datetime`) | `ZoneId.systemDefault()` — **JVM** | **[WIRE]** |
| 3 | `GET /v1/glclosures` | `lastUpdatedDate` | JACKSON | **STRING** | **audit timestamp** (`lastmodified_date`, `datetime`) | `ZoneId.systemDefault()` — **JVM** | **[WIRE]** |
| 4 | `GET /v1/glclosures/{id}` | same three | JACKSON | **STRING** | same | same | [SRC] |
| 5 | `GET /v1/journalentries` | `transactionDate` | GSON | **ARRAY** | calendar date (`acc_gl_journal_entry.entry_date`) | none — civil date | **[WIRE]** |
| 6 | `GET /v1/journalentries` | `submittedOnDate` | GSON | **ARRAY** | **business date** (`submitted_on_date`, `DATE`) | **tenant** zone | **[WIRE]** |
| 7 | `GET /v1/journalentries` | `createdDate` | GSON | **ARRAY** | **alias of `submittedOnDate`** — no column | **tenant** zone | **[WIRE]** |
| 8 | `GET /v1/journalentries/{id}` | same three | GSON | **ARRAY** | same | same | [SRC] |
| 9 | `GET /v1/journalentries/provisioning` | same three | GSON | **ARRAY** | same | same | [SRC] |
| 10 | `GET /v1/journalentries/openingbalance` | `transactionDate` | GSON | **ARRAY** | **business date, computed at request time** — not a column | **tenant** zone | [SRC] |
| 11 | `GET /v1/provisioningentries` | `createdDate` | JACKSON | **STRING** | run date (`m_provisioning_history.created_date`, **`date`**) | none — civil date | [SRC] |
| 12 | `GET /v1/provisioningentries/{id}` | `createdDate` | JACKSON | **STRING** | same | none — civil date | [SRC] |
| 13 | `GET /v1/businessdate` | `date` | JACKSON | **ARRAY** (annotated) | **business date** (`m_business_date.date`, `DATE`) | none once stored; **tenant** when seeded | [SRC] |
| 14 | `GET /v1/businessdate/{type}` | `date` | JACKSON | **ARRAY** (annotated) | same | same | [SRC] |
| 15 | `POST /v1/businessdate` | `date` | JACKSON | **ARRAY** (annotated) | same | same | [SRC] |
| 16 | `POST /v1/businessdate` | `changes` map values | JACKSON | **see §C caveat** | same | same | [SRC] |

**Endpoints in the slice that return NO date at all** (so a port needs no date logic for them):
`GET/POST/PUT/DELETE /v1/glaccounts`, `/v1/accountingrules`, `/v1/financialactivityaccounts`,
`POST /v1/runaccruals`, `GET /v1/provisioningentries/entries`. Verified by reading each DTO's full
field block and grepping each file case-insensitively for `date` — those greps returned zero hits.
Every create/update/delete in the slice returns `CommandProcessingResult`, which has no date field.

**Citations for the table.** Rows 1–4: `GLClosuresApiResource.java:91-95, :109-120`;
`GLClosureData.java:34-35` (unannotated), `:43, :45, :46`;
`GLClosureReadPlatformServiceImpl.java:44, :46, :47, :59, :61, :62`;
`db/changelog/tenant/parts/0001_initial_schema.xml:78` (`createTable acc_gl_closure`), `:85`
(`closing_date type="date"`), `:93` (`created_date type="datetime"`), `:94`
(`lastmodified_date type="datetime"`).
Rows 5–10: `JournalEntriesApiResource.java:93, :166, :189, :259, :274`;
`JournalEntryData.java:48, :63, :82, :211-212`;
`JournalEntryReadPlatformServiceImpl.java:96, :100, :146, :160, :232, :454, :456`;
`JournalEntry.java:106-107, :136`.
Rows 11–12: `ProvisioningEntriesApiResource.java:115-117, :139-143`;
`ProvisioningEntryData.java:34` (unannotated), `:47`;
`ProvisioningEntriesReadPlatformServiceImpl.java:118, :130, :134, :195, :209, :213`;
`0001_initial_schema.xml:3452` (`created_date type="date"`).
Rows 13–16: `BusinessDateApiResource.java:57-58, :65-66, :73-80`;
`BusinessDateResponse.java:35` (annotated), `:44`;
`BusinessDateUpdateResponse.java:36` (annotated), `:45, :46`;
`BusinessDate.java:48-49`.

---

## B. The three findings a port must not miss

**B-1. `/journalentries` is the ONLY accounting resource still on the Gson stack.**
Counting Gson `serialize(...)` calls per accounting resource
(`grep -rc "apiJsonSerializerService.serialize\|toApiJsonSerializer.serialize" --include="*ApiResource.java"`):
`JournalEntriesApiResource` = **7**; every other accounting resource = **1 or 2**, and in those the
calls serialise the **inbound request body** on POST/PUT, not the response
(e.g. `GLClosuresApiResource.java:132, :147`). So the slice has migrated to
return-the-POJO/Jackson **except journal entries**, which is exactly the pair T327 compared.
**This is a migration in progress, not a design.** It will keep moving; a port that hard-codes
"journalentries is array" must pin the commit it was true at.

**B-2. Three distinct `createdDate` fields, three distinct meanings.**

| endpoint | `createdDate` really is | stable across a day? |
|---|---|---|
| `/glclosures` | JVM-zone wall-clock date of row insertion | **no** — moves with container `TZ` |
| `/journalentries` | the business date (alias of `submittedOnDate`) | yes, within a tenant day |
| `/provisioningentries` | the provisioning run date, a true `date` column | yes |

Any Go type that maps all three onto one field is wrong. **The name is not the meaning.**

**B-3. The business date has two shapes on two endpoints, and both are "correct".**
`/v1/businessdate` returns `[y,m,d]` (annotated Jackson); `/v1/journalentries`'s
`submittedOnDate` — the same quantity — returns `[y,m,d]` too (Gson), **but for an unrelated
reason**. If `JournalEntriesApiResource` is migrated to the Jackson stack and `JournalEntryData`
is not annotated, `submittedOnDate` silently becomes a **string** while `/v1/businessdate` stays an
array. That is a one-line upstream change with a wire-breaking effect and **nothing in the codebase
guards it.**

---

## C. Two sharp caveats

**C-1. The array/string switch does not reach inside collections.**
`JacksonLocalDateBeanSerializerModifier.assignLocalDateSerializer` only rewrites bean property
writers whose raw type is exactly `LocalDate.class`
`[VERIFIED: JacksonLocalDateBeanSerializerModifier.java:50-56]`. `BusinessDateUpdateResponse.changes`
is a `Map<BusinessDateType, LocalDate>` `[VERIFIED: BusinessDateUpdateResponse.java:46]`, so its
**values are not** bean properties of raw type `LocalDate` and the array serializer does not apply
to them. The class is annotated, its `date` field is an array — and its `changes` values are
serialised by Jackson's default `LocalDate` handling instead. **Two shapes inside one response
object.** `[SRC — not observed on the wire; I made no oracle contact. Worth a probe before any port
consumes `changes`.]`

**C-2. `0117_set_datetime_precision.xml` does NOT apply to us.**
It widens `acc_gl_closure.created_date` to `datetime(6)`, but its changeSet is declared
`context="mysql"` `[VERIFIED: db/changelog/tenant/parts/0117_set_datetime_precision.xml:25]`.
**CLAUDE.md: PostgreSQL is the only database.** On our Postgres deployments the column keeps the
`0001_initial_schema.xml:93` type, `datetime` → **`timestamp without time zone`**.

That last point *resolves* an item the main README listed as `[UNVERIFIED]`: because the column is
`timestamp` **without** time zone, PostgreSQL performs **no** conversion on read. The value returned
is exactly the naive `LocalDateTime.now(ZoneId.systemDefault())` that JPA auditing wrote. So the
JVM zone is the **whole** story for rows 2–3 — there is no second, database-side zone effect layered
on top. Good news: one variable, not two.

---

## D. Count discrepancy, recorded rather than smoothed over

My `grep -rln "JsonLocalDateArrayFormat" --include="*.java" .` (excluding the three
`core/jersey/serializer/` machinery files) returns **9** DTO files; see main README §1.3 for the
list. A parallel sweep of the same question reported the number as "7" in prose while listing the
same **9** paths. **9 is the count I stand behind**, because it is the one I ran and the file list is
enumerable and agrees. Recorded because a reader meeting both numbers should know which was
measured.
