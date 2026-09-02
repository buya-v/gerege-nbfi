# Tier A · Slice A1 — journal-entry posting, the double-entry engine

**Fineract behaviour extraction. Analyst output. No Go, no contract change, no vector.**

| | |
|---|---|
| Worker | `T487` |
| Branch | `softhouse/T487-a1-journalentry-behaviour` |
| Oracle | Fineract reference implementation (the *test oracle*, never Oracle Database), pinned checkout `/home/user/fineract` |
| Commit | `426a23544e8426a38ae43ae404670a0a7e85b9eb` — verified with `git -C /home/user/fineract log -1 --format=%H` **before any line number below was read**; `git status --porcelain` empty at extraction time |
| Date | 2026-09-02 |
| Running instance | **None.** No Fineract process, no PostgreSQL. Every statement below is a statement about *source text this worker opened*. |

All `FILE:LINE` citations are relative to the pinned checkout root and were opened and read by this
worker. Where a claim rests on something this worker could not evaluate from source alone it is
tagged **`[UNVERIFIED]`** with the reason.

---

## 0. How to read this document

The reviewer for this slice (`T490`) will re-derive. Four conventions to make that cheap:

- A claim with a bare `FILE:LINE` is a claim **about that line's text**, nothing more.
- A claim that two things *disagree* always cites **both** sides.
- **"Not found" is a statement about the search.** Every negative claim below names the command or
  the file set it rests on.
- §11 lists everything this worker could not establish. §12 lists everything of value found
  **outside** the three assigned scope paths — read only, nothing modified.

**One thing this document deliberately does not contain: an expected numeric output.** There is no
running oracle in this session. Every arithmetic statement is about the *operations the code
performs*, never about a value it was observed to produce.

---

## 1. Scope, and where the slice's types actually live

### 1.1 The three assigned paths — 63 files, 11,374 LOC, counted by this worker

Measured with `find … -name '*.java' | xargs wc -l` at the pin:

| Path | Files | LOC |
|---|---|---|
| `fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry` | 39 | 9,650 |
| `fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry` | 22 | 1,623 |
| `fineract-core/src/main/java/org/apache/fineract/accounting/journalentry` | 2 | 101 |
| **Total** | **63** | **11,374** |

`find … -type f ! -name '*.java'` over the same three roots returns nothing: the slice is Java only.

### 1.2 A2's finding reproduces here — the slice is split across three Gradle modules under ONE Java package

A2 recorded that its core types live in `fineract-core` under the same Java package name. The same
shape holds for A1, and it is worse: the package `org.apache.fineract.accounting.journalentry` is
**split across three Gradle modules**, and the split runs through the middle of the engine.

| Type A1 needs | Actual module and file |
|---|---|
| `JournalEntry` (the **entity**) | `fineract-accounting/.../journalentry/domain/JournalEntry.java` |
| `JournalEntryRepository` | `fineract-accounting/.../journalentry/domain/JournalEntryRepository.java` |
| `JournalEntryType` (the **debit/credit enum**) | **`fineract-core`**/.../journalentry/domain/JournalEntryType.java |
| `AdvancedMappingtDTO` | **`fineract-core`**/.../journalentry/data/AdvancedMappingtDTO.java |
| `JournalEntryCommand`, `SingleDebitOrCreditEntryCommand` | `fineract-accounting/.../journalentry/command/` |
| `JournalEntryCommandFromApiJsonDeserializer` | `fineract-accounting/.../journalentry/serialization/` |
| `JournalEntryInvalidException` + its reason enum | `fineract-accounting/.../journalentry/exception/` |
| `JournalEntryData` (the read DTO) | `fineract-accounting/.../journalentry/data/JournalEntryData.java` |
| `JournalEntryMapper` (MapStruct) | `fineract-accounting/.../journalentry/JournalEntryMapper.java` |
| **`AccountingProcessorHelper`** (the posting engine) | `fineract-provider/.../journalentry/service/AccountingProcessorHelper.java` |
| **`JournalEntryWritePlatformServiceJpaRepositoryImpl`** (the command implementation) | `fineract-provider/.../journalentry/service/` |
| The six `*AccountingProcessorFor*` classes | `fineract-provider/.../journalentry/service/` |
| `JournalEntryRunningBalanceUpdateServiceImpl` | `fineract-provider/.../journalentry/service/` |

The entity is in `fineract-accounting`; the enum that gives it its debit/credit sense is in
`fineract-core`; every service that writes it is in `fineract-provider`. All three are the same Java
package `org.apache.fineract.accounting.journalentry.*`.

> **Consequence for the port.** A Go package boundary drawn on the Gradle-module boundary cuts the
> engine in three. The boundary must be drawn on the **Java package**, exactly as A2 concluded for
> its own slice (`docs/analysis/tierA-a2-behaviour.md` §1.2). §12 backlog **B-1**.

### 1.3 Types A1 unavoidably depends on that belong to A2 or to Tier C

Read and cited below, but **owned by another slice**, and this document does not redefine them:

| Type | Owner | File |
|---|---|---|
| `GLAccount`, `GLAccountType` | A2 | `fineract-core/.../glaccount/domain/` |
| `ProductToGLAccountMapping`, `FinancialActivityAccount` | A2 | `fineract-accounting/.../` |
| `GLClosure`, `GLClosureRepository` | A1-adjacent (`accounting/closure`, **not** in the three paths) | `fineract-accounting/.../closure/domain/` |
| `MoneyHelper` | Tier C / organisation | `fineract-core/.../organisation/monetary/domain/MoneyHelper.java` |
| `DateUtils`, `ThreadLocalContextUtil` | Tier C | `fineract-core/.../infrastructure/core/service/` |
| `AbstractAuditableWithUTCDateTimeCustom` | Tier C | `fineract-core/.../infrastructure/core/domain/` |

**A2 owns *which* GL account a posting hits; A1 owns *what gets written when it does*.** A2 §1.3
already says the resolution code lives in A1's `AccountingProcessorHelper`. This document confirms
that from A1's side and does **not** re-derive A2's resolution order — see §12 B-2.

---

## 2. The journal entry: entity, table, and exactly how the money is stored

### 2.1 The entity

`fineract-accounting/.../journalentry/domain/JournalEntry.java:38-41`

```
@Entity
@Getter
@Table(name = "acc_gl_journal_entry")
public class JournalEntry extends AbstractAuditableWithUTCDateTimeCustom<Long> {
```

There is **one row per leg**. There is no "journal entry header" table and no "transaction" table:
a multi-leg transaction is a set of rows sharing the `transaction_id` **string**. That single fact
shapes everything in §4.

| Java field | Java type | Column | JPA declaration | Liquibase DDL (`0001_initial_schema.xml`, unless noted) |
|---|---|---|---|---|
| *(inherited)* `id` | `Long` | `id` | `AbstractPersistableCustom` | `BIGINT` autoincrement PK — `:113-115` |
| `office` | `Office` `@ManyToOne` | `office_id` | `nullable=false` — `:43-45` | `BIGINT NOT NULL` — `:119-121` |
| `paymentDetail` | `PaymentDetail` `@ManyToOne` | `payment_details_id` | `:47-49` | `BIGINT`, `DEFAULT NULL` — `:172` |
| `glAccount` | `GLAccount` `@ManyToOne` | `account_id` | `nullable=false` — `:51-53` | `BIGINT NOT NULL` — `:116-118` |
| `currencyCode` | `String` | `currency_code` | `length=3, nullable=false` — `:55-56` | `VARCHAR(3) NOT NULL` — `:123-125` |
| `reversalJournalEntry` | `JournalEntry` `@ManyToOne(LAZY)`, **`@Setter`** | `reversal_id` | `:58-61` | `BIGINT`, `DEFAULT NULL`, self-FK — `:122`, FK at `:7617-7620` |
| `transactionId` | `String` | `transaction_id` | `nullable=false, length=50` — `:63-64` | `VARCHAR(50) NOT NULL` — `:126-128` |
| `loanTransactionId` | `Long` | `loan_transaction_id` | `:66-67` | `BIGINT`, `DEFAULT NULL` — `:129` |
| `savingsTransactionId` | `Long` | `savings_transaction_id` | `:69-70` | `BIGINT`, `DEFAULT NULL` — `:130` |
| `clientTransactionId` | `Long` | `client_transaction_id` | `:72-73` | `BIGINT`, `DEFAULT NULL` — `:131` |
| `shareTransactionId` | `Long` | `share_transaction_id` | `:75-76` | `BIGINT`, `DEFAULT NULL` — `:173` |
| `reversed` | `boolean`, **`@Setter`** | `reversed` | `nullable=false`, Java initialiser `= false` — `:78-80` | `boolean NOT NULL DEFAULT false` — `:132-134` |
| `manualEntry` | `boolean` | `manual_entry` | `nullable=false`, initialiser `= false` — `:82-83` | `boolean NOT NULL DEFAULT false` — `:136-138` |
| `transactionDate` | `LocalDate` | **`entry_date`** | **no `nullable`** — `:85-86` | **`date NOT NULL`** — `:139-141` |
| `type` | `Integer` | `type_enum` | `nullable=false` — `:88-89` | `SMALLINT NOT NULL` — `:142-144` |
| **`amount`** | **`BigDecimal`** | **`amount`** | **`scale=6, precision=19, nullable=false`** — `:91-92` | **`DECIMAL(19, 6) NOT NULL`** — `:145-147` |
| `description` | `String` | `description` | `length=500` — `:94-95` | `VARCHAR(500)` nullable — `:148` |
| `entityType` | `Integer` | `entity_type_enum` | **`length=50`** on an integer — `:97-98` | `SMALLINT`, `DEFAULT NULL` — `:149` |
| `entityId` | `Long` | `entity_id` | `:100-101` | `BIGINT`, `DEFAULT NULL` — `:150` |
| `referenceNumber` | `String` | `ref_num` | **no `length`** (JPA default 255) — `:103-104` | **`VARCHAR(100)`** nullable — `:135` |
| `submittedOnDate` | `LocalDate` | `submitted_on_date` | `nullable=false` — `:106-107` | `DATE NOT NULL`, added later — `0025_add_audit_entries_to_journal_entry.xml:72-76` |
| *(inherited)* `createdBy` | `Long` | `created_by` | `updatable=false, nullable=false` — `AbstractAuditableWithUTCDateTimeCustom.java:55-57` | renamed from `createdby_id` — `0025:44` |
| *(inherited)* `createdDate` | `OffsetDateTime` | **`created_on_utc`** | `updatable=false, nullable=false` — `…Custom.java:59-61` | `TIMESTAMP WITH TIME ZONE` (postgresql changeset) — `0025:32-36`, NOT NULL at `0025:64-70` |
| *(inherited)* `lastModifiedBy` | `Long` | `last_modified_by` | `nullable=false` — `…Custom.java:63-65` | renamed from `lastmodifiedby_id` — `0025:45` |
| *(inherited)* `lastModifiedDate` | `OffsetDateTime` | **`last_modified_on_utc`** | `nullable=false` — `…Custom.java:67-69` | as above |

Column names for the four audit fields are constants:
`AuditableFieldsConstants.java:28-31` — `created_by`, `created_on_utc`, `last_modified_by`,
`last_modified_on_utc`.

### 2.2 Five columns the entity does not map at all

| Column | DDL | Mapped on `JournalEntry`? | Who writes it |
|---|---|---|---|
| `is_running_balance_calculated` | `boolean NOT NULL DEFAULT false` — `:163-165` | **No** | raw batch `UPDATE`, §2.5 |
| `office_running_balance` | `DECIMAL(19,6) NOT NULL DEFAULT 0.000000` — `:166-168` | **No** | raw batch `UPDATE`, §2.5 |
| `organization_running_balance` | `DECIMAL(19,6) NOT NULL DEFAULT 0.000000` — `:169-171` | **No** | raw batch `UPDATE`, §2.5 |
| `created_date`, `lastmodified_date` | `datetime`, made nullable by `0025:40-41` | **No** — the entity uses the `*_on_utc` pair | nothing in the tree, on the evidence of the sweep in §11 item 5 |
| **`transaction_date`** | `date`, `DEFAULT NULL` — `:174`, **indexed** `transaction_date_index` — `:7164-7166` | **No** | nothing. Remarked **`"Unfinished. Not maintained."`** — `0025:78-84` |

**The `transaction_date` trap.** The Java field named `transactionDate` maps to the column named
**`entry_date`** (`JournalEntry.java:85-86`). A separate, unmapped, indexed column literally named
`transaction_date` also exists and is documented as abandoned. A port that adopts the schema and
matches Go field names to column names by string similarity will write the wrong column.

`grep -rn "transaction_date" ` over the three scope paths returns hits only in
`JournalEntryReadPlatformServiceImpl` and `JournalEntryRunningBalanceUpdateServiceImpl`, and every
one of those is against **`entry_date`** or a SQL alias `as transactionDate` — e.g.
`JournalEntryReadPlatformServiceImpl.java:96` (`journalEntry.entry_date as transactionDate`),
`:296`, `:303`, `:308`, `:369`. No code in the three scope paths reads or writes the physical
`transaction_date` column.

### 2.3 The monetary column: `BigDecimal` at `DECIMAL(19,6)` — how it is stored, and with what scale

**Storage.** `acc_gl_journal_entry.amount` is `DECIMAL(19, 6) NOT NULL`
(`0001_initial_schema.xml:145-147`), mapped as `BigDecimal` with `scale = 6, precision = 19`
(`JournalEntry.java:91-92`). The same `19,6` shape is used for the two running-balance columns
(`:166`, `:169`).

**Scale on the way in — there is none.** Tracing every constructor call in §3, the value handed to
`JournalEntry.createNew` is the caller's `BigDecimal` **unmodified**:
`JournalEntry.java:113-137` assigns `this.amount = amount` at `:125` with no `setScale`, no
rounding, no currency lookup. The JPA `scale = 6` attribute is DDL-generation metadata, not a
runtime coercion. So the scale actually stored is whatever the database does when a `numeric` of
some other scale is inserted into a `numeric(19,6)` column — PostgreSQL rounds to the declared
scale on insert. **`[UNVERIFIED: no database was available to observe an insert. This is a
statement about PostgreSQL's documented `numeric` behaviour, not an observation of this
instance.]`**

**Six stored decimals against MNT's minor unit of 2.** `CLAUDE.md` fixes MNT at ISO 4217 numeric
496, minor unit 2. The column can hold four digits of sub-minor-unit residue. Nothing in the three
scope paths rounds an amount to the currency's decimal places before persisting it — the sweep
that establishes this is in §6.2. This is the same `19,6`-vs-minor-unit-2 question A2 raised for
`m_trial_balance` (`docs/analysis/tierA-a2-behaviour.md` §8, backlog B-4); it is **the same
program-level decision**, and it lands on A1's table, which is the ledger itself.

**No floating-point type is used to carry the amount anywhere on the persistence path.** See §6.3
for the two places floating-point *does* appear in the slice, neither of which is a stored value.

### 2.4 Constraints, indexes, and what is NOT constrained

| Object | Where |
|---|---|
| PK on `id` | `0001:113-115` |
| FK `account_id` → `acc_gl_account` | `0001:7611-7615`, index `FK_acc_gl_journal_entry_acc_gl_account` `:5643` |
| FK `reversal_id` → `acc_gl_journal_entry` (self) | `0001:7617-7620`, index `:5648` |
| FK `created_by` / `last_modified_by` → `m_appuser` | `0025:47-56` |
| FKs to `m_office`, `m_payment_detail`, `m_loan_transaction`, `m_savings_account_transaction`, `m_share_account_transaction`, `m_client_transaction` | indexes at `0001:5653-5692` |
| Index on `transaction_date` (the abandoned column) | `0001:7164-7166` |
| Index on `transaction_id` | `0177_acc_journal_entry_index.xml:25-33` (postgresql, `CREATE INDEX CONCURRENTLY`) |

**There is no unique constraint of any kind on this table beyond the primary key**, and in
particular **no database-level constraint that ties the legs of a transaction together or requires
them to balance**. Where this worker looked: the `createTable` block `0001:112-175` in full; every
`acc_gl_journal_entry` hit in `grep -ln "acc_gl_journal_entry" *.xml` over
`fineract-provider/src/main/resources/db/changelog/tenant/parts/` (24 files), of which the
structural ones are `0001`, `0025`, `0032`, `0117`, `0177`, `0241` and the rest are report SQL. No
`addUniqueConstraint`, no `sql` check constraint against this table appears in any of them.

**Consequence:** double-entry is an *application* invariant in Fineract, not a *schema* one. §4.

### 2.5 The two written balance columns — G-12 and G-22, re-derived from source here

`CLAUDE.md`: *"The ledger is double-entry and append-only. **Balances are derived, never
written.**"* The reference oracle writes a balance onto the posted row. This worker re-derived that
independently of `.softhouse/gates.md`, and the two agree.

**What writes them.** `JournalEntryRunningBalanceUpdateServiceImpl.java` issues exactly two
`UPDATE` statements against the table:

- `:163-164` —
  `UPDATE acc_gl_journal_entry SET is_running_balance_calculated=?, organization_running_balance=?, office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?`,
  batched 1,000 at a time at `:180-181`;
- `:211` —
  `UPDATE acc_gl_journal_entry SET office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?`,
  the **office-scoped** path, which writes `office_running_balance` alone and sets **neither** the
  flag **nor** the organisation column.

`grep -rn "UPDATE acc_gl_journal_entry"` over the three scope paths returns exactly these two.

**The seed makes it state, not a projection.** `updateOrganizationRunningBalance` (`:106-189`)
primes `runningBalanceMap` at `:110-132` by **selecting the previously stored
`organization_running_balance`** of the last row before `entityDate`, and `officesRunningBalance` at
`:134-155` likewise from the stored `office_running_balance`. `calculateRunningBalance`
(`:220-250`) then adds or subtracts from that seed. **A recompute therefore inherits whatever the
last stored value was**; it does not re-derive from the legs. `updateRunningBalance(officeId, …)`
(`:191-218`) does the same for one office.

**How far back a recompute reaches** is decided by `MIN(entry_date) WHERE is_running_balance_calculated=false`
(`:72-73` organisation-wide, `:93-94` per office). Rows older than that are never revisited.

**The sign rule** is read from the **GL account's classification joined at recompute time**
(`:255-258`, `:261-266` select `glAccount.classification_enum`), not from anything stored on the
entry: `ASSET`/`EXPENSE` increase on DEBIT, `EQUITY`/`INCOME`/`LIABILITY` increase on CREDIT
(`:228-242`).

**The domain model does not know these columns exist.** `JournalEntry.java` declares no field for
either balance or the flag (§2.2), and `JournalEntryMapper.java:64-66` marks
`officeRunningBalance`, `organizationRunningBalance` and `runningBalanceComputed`
`@Mapping(… ignore = true)`. On the ordinary posting path they take the DDL defaults
(`0001:163-171`).

**They reach the contract boundary.** `JournalEntryReadPlatformServiceImpl.java:105` adds
`journalEntry.is_running_balance_calculated as runningBalanceComputed` (plus the two balance
columns) to the projection when the association parameter is set, and `:179-181` reads all three
with `rs.getBigDecimal` / `rs.getBoolean`. The parameter is
`?runningBalance=true` on `GET /v1/journalentries` and `GET /v1/journalentries/{id}`
(`JournalEntriesApiResource.java:130`, `:179`).

**How this reconciles with the open gates.** `.softhouse/gates.md`:

- **G-12** ("Fineract STORES a running balance on the entry") — raised, then **MEASURED** by
  `A2-29` against a live oracle: the stored value is a **second source of truth**, not a cache; it
  was made to disagree with the derived sum, the disagreement survived four recomputes and was
  served at the boundary with `runningBalanceComputed: true`. **This worker's source reading
  supplies the mechanism for that measurement and contradicts none of it**: the seed at
  `:110-116`/`:134-141`, the reach limit at `:72-73`/`:93-94`, and the recompute-time
  classification join at `:225-242` are exactly the three properties that let a stored value drift
  and stay drifted. The gate is **OPEN**; option (a)/(b′) is recommended there and this document
  takes no decision on it.
- **G-22** ("the oracle WRITES a balance onto a posted row") — raised by `T429`, which cites
  `JournalEntryRunningBalanceUpdateServiceImpl.java:163-165` and `:211`. **Re-derived here
  independently: both statements exist, at those lines, and they are the only two `UPDATE`s against
  the table in the scope paths.** G-22 asks to ratify a normative `§4.4a` in DEC-2 naming three
  ORACLE_DERIVED columns. That is a `user`/driver gate and this document does not pre-empt it.

**No contradiction with a ratified DEC was found here.** DEC-2 §4.4 row `I-3` explicitly states
*"GATE G-12 IS OPEN ON THIS EXACT INVARIANT AND DEC-2 DOES NOT RESOLVE IT"*
(`docs/adr/DEC-2-gl-accounting-adapter.md` §4.4, `I-3` row). This document's finding is consistent
with that sentence. **What this document adds** is that the office-scoped `UPDATE` at `:211` writes
one of the two columns and not the other, and sets neither flag — so the two columns can describe
different ledgers even in a single-office tenant. `A2-29` measured exactly that; the source is why.

---

## 3. The posting path, end to end

### 3.1 Path A — the MANUAL journal entry (`POST /v1/journalentries`)

```
POST /v1/journalentries                       JournalEntriesApiResource.java:192-220
  │  (no ?command=, or ?command= anything but updateRunningBalance/defineOpeningBalance)
  ├─ CommandWrapperBuilder().createJournalEntry()                                 :216
  ├─ commandsSourceWritePlatformService.logCommandSource(...)                     :217
  │       └─ command bus → @CommandType(entity="JOURNALENTRY", action="CREATE")
  │          CreateJournalEntryCommandHandler.java:31-42  (@Transactional)
  └─ JournalEntryWritePlatformServiceJpaRepositoryImpl.createJournalEntry(JsonCommand)
                                                                                 :144-248
       1. fromApiJsonDeserializer.commandFromApiJson(json)                        :148
            JournalEntryCommandFromApiJsonDeserializer.java:56-113
            – checkForUnsupportedParameters against JournalEntryJsonInputParams   :64
            – credits[]/debits[] parsed by populateCreditsOrDebitsArray           :113-133
       2. journalEntryCommand.validateForCreate()                                 :149
            JournalEntryCommand.java:59-112   (field-level validation only)
       3. office lookup (findOneWithNotFoundDetection)                            :153
       4. validateBusinessRulesForJournalEntries(command)                         :157
            :626-652  – future date / accounting closure / at least one debit AND
                        one credit / checkDebitAndCreditAmounts
       5. paymentDetailWritePlatformService.createAndPersistPaymentDetail         :161
       6. transactionId = generateTransactionId(officeId)                         :166
       7. optional external-asset-owner resolution                                :169-183
       8. branch on accountingRule != null                                        :185-237
            – rule present  : per-side validation, then saveAllDebitOrCreditEntries
            – rule absent   : saveAllDebitOrCreditEntries(DEBIT)  then (CREDIT)   :231-235
       9. CommandProcessingResultBuilder …withTransactionId(transactionId)        :239-243
```

`saveAllDebitOrCreditEntries` (`:654-681`) is where a row is born, once per array element:

1. `organisationCurrencyRepository.findOneWithNotFoundDetection(currencyCode)` — `:661`, **once per
   call**, i.e. twice per request (debits then credits);
2. `glAccountRepository.findById(...)` or `GLAccountNotFoundException` — `:664-665`;
3. `validateGLAccountForTransaction(glAccount)` — `:667`; refuses a **disabled** account and an
   account with `manualEntriesAllowed == false` (`:328-339`);
4. per-leg `comments` override the entry-level `comments` when non-blank — `:669-672`;
5. `JournalEntry.createNew(office, paymentDetail, glAccount, currencyCode, transactionId,
   manualEntry=true, transactionDate, type, singleDebitOrCreditEntryCommand.getAmount(), comments,
   entityType=null, entityId=null, referenceNumber, null, null, null, null)` — `:674-676`;
6. `helper.persistJournalEntry(glJournalEntry)` — `:677`;
7. `accountingService.createMappingToOwner(externalAssetOwner, glJournalEntry)` — `:679`.

`persistJournalEntry` (`AccountingProcessorHelper.java:1414-1420`) is a `saveAndFlush` plus, **only
when the row is new and `loanTransactionId != null`**, a `LoanJournalEntryCreatedBusinessEvent`.

**`manualEntry = true` on every leg of this path** (`:658`, and `:764` for opening balances). It is
`false` on every leg of the automatic paths (§3.2). That flag is load-bearing for reversal (§5.1).

**`transactionId` generation** — `:687-692`:

```java
final AppUser user = this.context.authenticatedUser();
final Long time = System.currentTimeMillis();
final String uniqueVal = String.valueOf(time) + user.getId() + officeId;
return Long.toHexString(Long.parseLong(uniqueVal));
```

The source's own comment at `:683-686` says *"TODO: Need a better implementation with guaranteed
uniqueness"*. Two facts a porter needs:

- it is **decimal string concatenation** of a 13-digit epoch-millis, the user id and the office id,
  then parsed as a `long` and hex-formatted. 13 digits + the two ids must stay within `Long`'s 19
  digits, so a sufficiently large `userId`/`officeId` pair makes `Long.parseLong` throw
  `NumberFormatException`. `[UNVERIFIED: not executed; this is arithmetic on the literal expression
  at `:690`.]`
- two requests in the same millisecond from the same user and office produce the **same**
  transaction id. There is no unique index on `transaction_id` (§2.4).

**The top-level `amount` parameter is accepted, validated, and never used.**
`JournalEntryJsonInputParams.AMOUNT` is parsed (`…Deserializer.java:84-85`) and validated
`zeroOrPositiveAmount` (`JournalEntryCommand.java:105`), but
`grep -n "journalEntryCommand.getAmount\|command.getAmount()"` over
`JournalEntryWritePlatformServiceJpaRepositoryImpl.java` returns **nothing** — every `getAmount()`
hit in that file is on a `SingleDebitOrCreditEntryCommand` or on a `JournalEntry`. The reason enum
carries a constant for the check that would have used it — `DEBIT_CREDIT_SUM_MISMATCH_WITH_AMOUNT`
— and that constant is **dead**: `grep -rn "DEBIT_CREDIT_SUM_MISMATCH_WITH_AMOUNT" --include='*.java' .`
over the whole checkout (excluding `/build/`) returns exactly two lines, both inside
`JournalEntryInvalidException.java` (`:35` the declaration, `:49` its `errorMessage()` branch), and
**it has no `errorCode()` branch at all** (`errorCode()` is `:65-84` and covers eight of the nine
constants; the ninth falls through to `return name();` at `:83`), so if it
were ever thrown its error code would be the raw enum name.

`USE_ACCOUNTING_RULE("useAccountingRule")` is the same shape: declared at
`JournalEntryJsonInputParams.java:37`, accepted by the unsupported-parameter check, and read
nowhere — `grep -rn "USE_ACCOUNTING_RULE" --include='*.java' .` over the checkout returns that one
line.

### 3.2 Path B — the AUTOMATIC posting (portfolio → ledger)

Nothing on this path goes through the command bus, the deserializer, or
`validateBusinessRulesForJournalEntries`.

```
Loan / savings / shares / client transaction committed
  └─ JournalEntryWritePlatformServiceJpaRepositoryImpl
       .createJournalEntriesForLoan(AccountingBridgeDataDTO)              :538-551
       .createJournalEntriesForSavings(Map)                               :553-567
       .createJournalEntriesForShares(Map)                                :569-584
       .createJournalEntriesForClientTransactions(Map)                    :818-822
         │  (each is @Transactional and each first tests whether accounting
         │   is enabled at all — cash / upfront-accrual / periodic-accrual)
         ├─ helper.populate…DtoFromDTO / …FromMap        AccountingProcessorHelper.java:106-378
         ├─ …ProcessorFor…Factory.determineProcessor(dto)
         └─ processor.createJournalEntriesFor…(dto)
               CashBasedAccountingProcessorForLoan.java            (1,014 LOC)
               AccrualBasedAccountingProcessorForLoan.java         (2,242 LOC)
               AccrualWithDeferredRevenueAmortization…ForWorkingCapitalLoan.java (529)
               CashBasedAccountingProcessorForSavings.java   / AccrualBased…ForSavings.java
               CashBasedAccountingProcessorForShares.java
               CashBasedAccountingProcessorForClientTransactions.java
                 └─ helper.create{Debit,Credit}JournalEntryFor…(…)
                      AccountingProcessorHelper.java:912-1055, :1154-1184
                      └─ JournalEntry.createNew(… manualEntry = false …)
                         └─ persistJournalEntry(...)                            :1414-1420
```

The leaf creators are pairwise-identical per product family. Reading
`AccountingProcessorHelper.java:912-1055`:

| Leaf | Lines | `entity_type_enum` | `transaction_id` prefix | Which `*_transaction_id` column |
|---|---|---|---|---|
| `createDebitJournalEntryForLoan` / `…Credit…` | `:975-988`, `:940-953` | `PortfolioProductType.LOAN` | `"L"` | `loan_transaction_id` |
| `createDebitJournalEntryForSavings` / `…Credit…` | `:1031-1045`, `:923-938` | `SAVING` | `"S"` | `savings_transaction_id` |
| `createDebitJournalEntryForShares` / `…Credit…` | `:1154-1168`, `:1170-1184` | `SHARES` | `"SH"` | `share_transaction_id` |
| `createDebitJournalEntryForClientPayments` / `…Credit…` | `:1047-1055`, `:912-921` | `CLIENT` | `"C"` | `client_transaction_id` |
| `createProvisioningDebitJournalEntry` / `…Credit…` | `:955-963`, `:965-973` | `PROVISIONING` | `"P"` | none |
| `create{Debit,Credit}JournalEntryForWorkingCapitalLoan` | `:1000-1008`, `:990-998` | `WORKING_CAPITAL_LOAN` | `"WC"` | none |

The prefixes are constants at `AccountingProcessorHelper.java:89-94`. Four of the six leaves apply
the prefix **only if `StringUtils.isNumeric(transactionId)`** (e.g. `:979-983`); if the id is not
numeric the prefix is skipped and the corresponding `*_transaction_id` column stays null. The
provisioning and working-capital leaves always prefix (`:958`, `:993`).

**Where the pair comes from.** The generic pair-maker is
`createJournalEntriesForLoan(office, currencyCode, accountTypeToDebitId, accountTypeToCreditId, …)`
at `:570-577`: resolve the debit account, resolve the credit account, create one debit leg, create
one credit leg, same `amount`, same `transactionId`, same `transactionDate`. The savings twin is at
`:587-595`. **That is the only place in the slice where "a debit and a credit of equal amount" is
produced as a unit**; everywhere else the processors accumulate a `totalDebitAmount` and post one
balancing leg for it (§4.2).

### 3.3 Path C — opening balances (`POST /v1/journalentries?command=defineOpeningBalance`)

`JournalEntryWritePlatformServiceJpaRepositoryImpl.defineOpeningBalance` — `:701-757`:

1. resolve the contra account from **financial activity 300**, hard-coded as an integer literal at
   `:709`: `findByFinancialActivityTypeWithNotFoundDetection(300)`;
2. `validateJournalEntriesArePostedBefore(contraId)` — `:717`, `:810-816`: if **any** transaction id
   exists that does not touch the contra account, throw
   `error.msg.journalentry.defining.openingbalance.not.allowed`;
3. **reverse every existing non-reversed contra transaction** — `:729-735`, via the ordinary
   `revertJournalEntry` (§5.1) with the comment `"defining opening balance"`;
4. post debits then credits through `saveAllDebitOrCreditOpeningBalanceEntries` — `:742-746`.

`saveAllDebitOrCreditOpeningBalanceEntries` (`:759-798`) additionally:

- refuses a contra account whose `GLAccountType` is not EQUITY — `:767-771`;
- runs `validateGLAccountForTransaction` on **both** the contra account (`:772`) and each target
  account (`:783`);
- writes **two** rows per array element: the target leg (`:789-791`) and a **contra leg of the
  opposite type** (`:793-796`), `getContraType` at `:800-808`.

So an opening-balance request with N debits and M credits writes `2(N+M)` rows, all
`manualEntry = true`, all under one `transactionId`.

**A latent NPE.** `:710-715` reads `financialActivityAccountId.getGlAccount().getId()` and *then*
tests `if (contraId == null)`. If the financial-activity row exists with a null GL account, the
dereference at `:710` throws before the guard at `:711` can produce the intended
`GeneralPlatformDomainRuleException`. `[UNVERIFIED: not executed; whether a null `gl_account_id` is
possible on that table is A2's question.]`

### 3.4 Path D — the running-balance recompute (`POST /v1/journalentries?command=updateRunningBalance`)

`JournalEntriesApiResource.java:206-210` → `UpdateRunningBalanceCommandHandler` →
`JournalEntryRunningBalanceUpdateServiceImpl.updateOfficeRunningBalance(JsonCommand)` (`:82-104`).
This path **writes no journal entry**; it rewrites the three unmapped columns of rows that already
exist (§2.5). It is the only command in this slice that mutates a posted row without adding one.

---

## 4. Double-entry invariants as Fineract actually enforces them

Not as accounting theory says. Each row below names the **enforcement site**, or says there is
none and where this worker looked.

### 4.1 The enforcement inventory

| # | Invariant | Enforced? | Site | What happens on violation |
|---|---|---|---|---|
| E-1 | A manual entry has **at least one debit and at least one credit** | **Yes** | `…JpaRepositoryImpl.java:643-649` | `JournalEntryInvalidException(NO_DEBITS_OR_CREDITS)` → `error.msg.glJournalEntry.invalid.no.debits.or.credits` |
| E-2 | For a manual entry, **Σ debit amounts == Σ credit amounts** | **Yes**, once, at the boundary | `checkDebitAndCreditAmounts`, `:306-326`; called from `validateBusinessRulesForJournalEntries:651` and again inside the accounting-rule branches at `:197` and `:217` | `JournalEntryInvalidException(DEBIT_CREDIT_SUM_MISMATCH)` → `error.msg.glJournalEntry.invalid.mismatch.debits.credits` |
| E-3 | Each leg has both an account and an amount | **Yes** | `:312-314`, `:317-320` | `DEBIT_CREDIT_ACCOUNT_OR_AMOUNT_EMPTY` |
| E-4 | Each leg's amount is non-negative | **Yes**, but only `zeroOrPositiveAmount` | `JournalEntryCommand.java:108-111` | `PlatformApiDataValidationException` |
| E-5 | Target account is not disabled, and allows manual entries | **Yes** | `validateGLAccountForTransaction`, `:328-339` | `GL_ACCOUNT_DISABLED` / `GL_ACCOUNT_MANUAL_ENTRIES_NOT_PERMITTED` |
| E-6 | Entry date is not in the future | **Yes** | `:630-632`, via `DateUtils.isDateInTheFuture` | `FUTURE_DATE` |
| E-7 | Entry date is after the branch's latest GL closure | **Yes** on the manual path (`:634-640`) and on the reversal path (`:392-400`); on the automatic path only where a processor calls `helper.checkForBranchClosures` (`AccountingProcessorHelper.java:556-564`) | `ACCOUNTING_CLOSED` |
| E-8 | **Σ debits == Σ credits for an AUTOMATIC posting** | **NO. There is no such check.** | see §4.2 | — |
| E-9 | Σ debits == Σ credits **as a stored/database constraint** | **NO.** §2.4 | — | — |
| E-10 | The charge-split total equals the transaction total | **Yes**, three sites | `AccountingProcessorHelper.java:433-446` (credits and debits, separately) and `:1450-1455` | `PlatformDataIntegrityException`, message begins `"Meltdown in advanced accounting…"` |
| E-11 | Savings- and share-charge splits equal the transaction total | **Yes**, four sites | savings `AccountingProcessorHelper.java:825`, `:860`; shares `:1118`, `:1150` | `PlatformDataIntegrityException("Recent Portfolio changes w.r.t Charges for Savings/shares have Broken the accounting code")` |
| E-12 | `Idempotency-Key` on a money-movement POST | **NO — it is optional in the oracle.** §4.4 | — | — |

`grep -rn "Meltdown\|DEBIT_CREDIT_SUM_MISMATCH\|does not equal"` over the three scope paths returns
exactly the sites listed in E-2, E-10 and E-11 (plus the enum declarations). That grep is the basis
for the "no other balance check exists in this slice" claim.

### 4.2 Why E-8 is a "no", stated precisely

On the automatic path the processors do not *check* balance; they *construct* it. The canonical
shape, read from `createJournalEntriesForLoanRepayments`,
`CashBasedAccountingProcessorForLoan.java:727-848`:

```java
BigDecimal totalDebitAmount = new BigDecimal(0);                              // :743
if (principalAmount != null && principalAmount.compareTo(BigDecimal.ZERO) > 0) {   // :746
    totalDebitAmount = totalDebitAmount.add(principalAmount);                 // :747
    helper.createCreditJournalEntryForLoan(… LOAN_PORTFOLIO … principalAmount);// :748-749
}
… the same accumulate-and-post-one-component block for interest, fees, penalties, overpayment
/*** create a single debit entry for the entire amount **/                     // :822  (source's own comment)
… helper.createDebitJournalEntryForLoan(… FUND_SOURCE … totalDebitAmount);     // :839-840
```

**The polarity is per method, the shape is universal.** Here the components are CREDITs and the
single balancing leg is a DEBIT; in `createJournalEntriesForChargeOffLoanChargeAdjustment`
(`:217-314`) the same `totalDebitAmount` accumulator drives credits from an `accountMap` at
`:298-301` and one debit for the total at `:303-313`. The source's own comment
*"create a single debit entry for the entire amount"* appears twice, at `:698` and `:822`. The same
accumulate-then-post-the-total structure recurs at `:234`, `:332`, `:545`, `:743`, `:959` in this
file (every `BigDecimal totalDebitAmount = new BigDecimal(0)` in it) and throughout
`AccrualBasedAccountingProcessorForLoan.java` (e.g. `:2195-2233`).

**Balance holds because the balancing leg is literally the running sum of the legs just posted**,
not because anything compares them afterwards.

**Two consequences the porter must not lose:**

1. **A bug anywhere between the accumulation and the post produces an unbalanced transaction and
   nothing objects.** No exception, no log line, no constraint. The only after-the-fact detector in
   the entire slice is the charge-split "Meltdown"/"Recent Portfolio changes" family (E-10, E-11),
   which compares a *charge* total to a *transaction* total — not debits to credits.
2. **Guard conditions decide whether a leg exists at all.** `MathUtil.isGreaterThanZero(BigDecimal)`
   (`MathUtil.java:196-198`: `value != null && value.compareTo(BigDecimal.ZERO) > 0`) is
   null-safe and **scale-insensitive**, so `0.00` and `0.000000` both suppress a leg. The cash
   processor uses the longhand `amount != null && amount.compareTo(BigDecimal.ZERO) > 0`
   (`CashBasedAccountingProcessorForLoan.java:239`, `:746`, …) and the accrual processor uses
   `MathUtil.isGreaterThanZero` (`AccrualBasedAccountingProcessorForLoan.java:181`, `:208`, …).
   **The two are equivalent in behaviour** — re-derived here by reading both — but a port that
   transcribes one and not the other will diverge if either is later "simplified".

`GLAccountBalanceHolder` (`data/GLAccountBalanceHolder.java:29-52`) is the accumulator type used by
some processors: two `Map<Long, BigDecimal>`, `debitBalances` and `creditBalances`, with
`addToCredit`/`addToDebit` merging by account id. **It never compares the two maps.** It is an
aggregation helper, not an invariant.

### 4.3 What the append-only invariant actually meets in this code

`CLAUDE.md`: *"The ledger is … append-only."* On the posted row, the oracle has:

- **two ORM-mutable fields** — `reversalJournalEntry` (`@Setter` at `JournalEntry.java:58`) and
  `reversed` (`@Setter` at `:78`). `grep -n "@Setter"` over `JournalEntry.java` returns exactly
  those two. Both are set only by a reversal (§5), and both go through `persistJournalEntry`;
- **three fields mutable only by raw batch `UPDATE` from outside the model** — the two running
  balances and the flag (§2.5), plus `last_modified_by` / `last_modified_on_utc`, which those same
  statements rewrite.

So the oracle's ledger is **append-plus-flag**, not append-only, and separately it is
**rewritten nightly** in three columns the domain model does not know about. Both halves are
already on the gate register (G-12, G-22); this section records that A1's own reading reaches the
same conclusion by a different route.

### 4.4 `Idempotency-Key` — mandatory for us, optional in the oracle

`CLAUDE.md`: *"`Idempotency-Key` is mandatory on every money-movement POST."*

In Fineract the header name is configurable and defaults to exactly that string:
`fineract.idempotency-key-header-name=${FINERACT_IDEMPOTENCY_KEY_HEADER_NAME:Idempotency-Key}`
(`fineract-provider/src/main/resources/application.properties:179`, and again for the command bus
at `:857`). `IdempotencyStoreFilter.java:71-73` reads it off the request.

**But it is optional.** `IdempotencyKeyResolver.java:36`:

```java
return Optional.ofNullable(wrapper.getIdempotencyKey())
        .orElseGet(() -> getAttribute().orElseGet(idempotencyKeyGenerator::create));
```

and `IdempotencyKeyGenerator.java:27-29` returns `UUID.randomUUID().toString()`. A `POST
/v1/journalentries` with no header is accepted and given a fresh key, which is the same as having
none.

**Therefore the port's behaviour here is a deliberate divergence, not a parity target.** A missing
`Idempotency-Key` must be a refusal in the Go module and will be a **success** in the oracle. No
vector can be captured for that refusal; it is a structural rule, in the same class as DEC-2's
`I-3`/`I-4`. §10 D-6.

---

## 5. Reversals and corrections

`CLAUDE.md`: *"Corrections are reversing entries."* Fineract agrees on the *adds-a-pair* half and
disagrees on the *never-mutates* half. There are **four** reversal shapes in this slice and they
are not consistent with each other.

### 5.1 Shape 1 — the user-facing reversal (`POST /v1/journalentries/{transactionId}?command=reverse`)

`JournalEntriesApiResource.java:222-244` → `ReverseJournalEntryCommandHandler` →
`JournalEntryWritePlatformServiceJpaRepositoryImpl.revertJournalEntry(JsonCommand)` — `:341-356`,
then the worker method `revertJournalEntry(List<JournalEntry>, String)` — `:380-429`.

**Selection.** `findUnReversedManualJournalEntriesByTransactionId` —
`JournalEntryRepository.java:30-31`:

```
where journalEntry.transactionId = :transactionId
  and journalEntry.reversed = false
  and journalEntry.manualEntry = true
```

**Two hard consequences.** Because the query filters `manualEntry = true`, **an automatically
generated posting (§3.2, `manualEntry = false`) can never be reversed through this endpoint** — the
result set is empty. And because `:349-351` throws `JournalEntriesNotFoundException` when
`journalEntries.size() <= 1`, **a single-leg transaction can never be reversed either**, and an
empty result produces a *not found*, not a *not permitted*.

**What it writes**, per original leg (`:402-427`):

| | |
|---|---|
| a **new** row | `JournalEntry.createNew(…)` at `:409-413` (original was DEBIT → new is CREDIT) or `:415-419` (the mirror) |
| its `transactionId` | a **new** id from `generateTransactionId(officeId)` — `:382` |
| its `manualEntry` | **`true`** — `:383`, even when reversing… well, only manual entries can get here |
| its `transactionDate` | **the ORIGINAL leg's `transactionDate`** — `:411`, `:417`. Not today. |
| its `amount` | the original amount, unchanged and unrounded — `:411`, `:417` |
| its `entityType`, `entityId` | **`null`, `null`** — hard-coded at `:411`, `:417`, discarding the original's |
| its `description` | `reversalComment`, or, when blank, the generated `"Reversal entry for Journal Entry with Entry Id  :{id} and transaction Id {txnId}"` — `:404-407` (note the two spaces before the colon; a port that "fixes" it changes the wire) |
| **and it MUTATES the original** | `journalEntry.setReversed(true)` — `:423`; `journalEntry.setReversalJournalEntry(reversalJournalEntry)` — `:424`; `helper.persistJournalEntry(journalEntry)` — `:426` |

**The original row is updated in place.** That is a JPA merge of an existing row, so it also
rewrites `last_modified_by` / `last_modified_on_utc` through Spring auditing. The reversal is
therefore *append a mirror leg **and** flag the original*, not *append only*.

**Ordering.** The reversal leg is persisted at `:422` **before** the original is flagged at
`:426` — both inside the one `@Transactional` (`:341`).

**Closure check.** `:391-400` refuses if the branch's latest closure is not strictly before the
**original** transaction date, with `ACCOUNTING_CLOSED`. Note it checks
`journalEntries.get(0).getTransactionDate()` only — the first leg's date, on the assumption that
all legs of a transaction share one.

**Comment validation** is length-only: `validateCommentForReversal` — `:525-536`,
`notExceedingLengthOf(500)`.

### 5.2 Shape 2 — the reversed-loan-transaction posting

`createJournalEntryForReversedLoanTransaction` — `:358-378`. Called from outside the slice.

- selects with `findJournalEntries(transactionId, PortfolioProductType.LOAN)`
  (`JournalEntryRepository.java:42-43`), which filters `reversed = false` **and** `entityType`, and
  orders `transactionDate asc, createdDate asc, id asc`;
- writes mirror legs under **the SAME `transactionId`** — `:363`, `:371`;
- with `manualEntry = Boolean.FALSE` — `:371`;
- on the **new** `transactionDate` passed in — `:371`, not the original's;
- **preserving** `entityType`/`entityId` — `:373`, unlike shape 1;
- and it does **NOT** set `reversed` or `reversal_id` on the originals.

So after this runs, the ledger holds `2n` rows under one transaction id, none flagged, and
`findUnReversedManualJournalEntriesByTransactionId` would still not find them (they are
`manualEntry = false`).

### 5.3 Shape 3 — provisioning reversal

`revertProvisioningJournalEntries` — `:431-463`. Mirrors legs, `manualEntry = FALSE`, **reuses the
ORIGINAL `transactionId`** (`:441`, `:448`), on a passed-in `reversalTransactionDate`, preserves
`entityType`/`entityId`, **and** flags the originals `reversed = true` with `reversal_id` (`:456-459`).
It returns `journalEntries.get(0).getTransactionId()` — the original id (`:434`) — as the "reversal
transaction id".

`:434` dereferences `journalEntries.get(0)` with no emptiness guard, unlike shape 1's `size() <= 1`
test. `[UNVERIFIED: not executed.]`

### 5.4 Shape 4 — share-account reversal

`revertShareAccountJournalEntries` — `:586-624`. Generates a **new** transaction id (`:596`),
`manualEntry = Boolean.FALSE` (`:603`, `:610`), preserves `entityType`/`entityId`, flags the
originals (`:618-619`). `continue`s silently on an empty result (`:592-594`).

### 5.5 The four shapes side by side

| | New txn id? | `manualEntry` | Date used | `entityType`/`entityId` | Flags original? |
|---|---|---|---|---|---|
| 1 · manual reverse (`:380-429`) | **yes** | `true` | **original's** | **discarded (null)** | **yes** |
| 2 · reversed loan txn (`:358-378`) | **no — same id** | `false` | **new, passed in** | preserved | **no** |
| 3 · provisioning (`:431-463`) | **no — same id** | `false` | new, passed in | preserved | yes |
| 4 · shares (`:586-624`) | yes | `false` | new, passed in | preserved | yes |

**Nothing in the slice reconciles these.** A port that implements "reversal" once, uniformly, will
diverge from the oracle on three of the four. A port that implements four is transcribing an
inconsistency. §10 D-4.

---

## 6. Rounding and money arithmetic

### 6.1 `MoneyHelper` — re-verified against source, and `CLAUDE.md` is correct

`CLAUDE.md` records `MoneyHelper.PRECISION = 19` as a compile-time constant and the production
`MathContext` as `(19, HALF_UP)`. **Re-read here at the pin and confirmed, at these lines:**

| Claim | Source |
|---|---|
| `public static final int PRECISION = 19;` | `fineract-core/.../organisation/monetary/domain/MoneyHelper.java:35` |
| `getMathContext()` returns `new MathContext(PRECISION, getRoundingMode())` | `MoneyHelper.java:91-93` — `mathContextCache.computeIfAbsent(tenantId, k -> new MathContext(PRECISION, getRoundingMode()))` |
| Only the **mode** is tenant-configurable | `initializeTenantRoundingMode(String, int)` — `:54`; `getRoundingMode()` throws `IllegalStateException` if the tenant was never initialised — `:74-81` |

**It has not moved.** `HALF_UP` is `RoundingMode` ordinal 4 in the JDK, which is a JDK fact and not
a Fineract one. The ratified tenant parameter `(19, HALF_UP)` therefore stands unchanged, and any
parity claim must run at that setting.

### 6.2 Every rounding / scaling / conversion site **inside the three scope paths**

The sweep:
`grep -rn "setScale\|\.divide(\|\.multiply(\|MathContext\|RoundingMode" --include='*.java'` over the
three scope paths. **Complete output, six lines, all of them:**

| Site | What it does |
|---|---|
| `…JpaRepositoryImpl.java:22` | `import java.math.MathContext` |
| `…JpaRepositoryImpl.java:964` | `final MathContext mc = MoneyHelper.getMathContext();` |
| **`…JpaRepositoryImpl.java:981`** | **`taxDetail.getAmount().multiply(paidAmount, mc).divide(chargeAmount, mc)`** |
| `AccrualBasedAccountingProcessorForLoan.java:2208`, `:2222` | `…getAmount().multiply(new BigDecimal(-1))` — sign flip, exact |
| `CashBasedAccountingProcessorForLoan.java:980`, `:994` | the same sign flip |

**There is exactly ONE rounding site on the whole posting path**, and it is `:981`: the pro-rating
of a charge's tax component to the amount actually paid,
`taxAmount × paidAmount ÷ chargeAmount` at `MathContext(19, HALF_UP)`. It is guarded by
`chargeAmount != null && chargeAmount.compareTo(BigDecimal.ZERO) > 0 && !lc.getTaxDetails().isEmpty()`
(`:977`), and its result goes straight into a `ChargeTaxDetailDTO` (`:982`) and from there to a
journal entry amount.

**`setScale` appears nowhere in the three scope paths.** Nothing rounds an amount to the currency's
minor unit before persisting. **The amount stored is the amount the caller handed in.**

That has a sharp consequence for the port: **at `(19, HALF_UP)` a division at precision 19 can
produce far more than two decimals**, and `numeric(19,6)` will keep six of them. A Go port working
in integer minor units cannot reproduce `:981` exactly without deciding, explicitly, where the
rounding to minor units happens. Nothing in this slice makes that decision. §10 D-1.

### 6.3 Floating point in the slice — the complete inventory

`grep -rn "double \|float \|Double\|Float" --include='*.java'` over the three scope paths returns
**exactly one line**:

| Site | What it is |
|---|---|
| `fineract-provider/.../journalentry/api/JournalEntriesApiResourceSwagger.java:159` | `public Double amount;` — an **OpenAPI documentation model**, not a runtime money path |

That is the whole float inventory *by type declaration*. But the sweep in §6.2 turns up a second
form the type grep misses, and it is the more interesting one:

**Four sites convert a `BigDecimal` to a 32-bit binary `float` to decide a sign, on the posting
path.**

```java
chargePaymentDTO.getAmount().floatValue() < 0
        ? chargePaymentDTO.getAmount().multiply(new BigDecimal(-1))
        : chargePaymentDTO.getAmount()
```

- `AccrualBasedAccountingProcessorForLoan.java:2208` (fee payments) and `:2222` (penalty payments);
- `CashBasedAccountingProcessorForLoan.java:980` (fees) and `:994` (penalties).

The *value* that flows onward is a `BigDecimal` — the `multiply(new BigDecimal(-1))` is exact — so
this is not a precision loss in the amount. It is a **binary float in a money decision**, and
`CLAUDE.md` forbids float "in any monetary code path … including intermediate calculation". The
failure mode is narrow and worth stating precisely rather than dramatising: `BigDecimal.floatValue()`
of a negative magnitude smaller than the smallest positive `float` subnormal returns `-0.0f`, and
`-0.0f < 0` is **false**, so such a value would not be negated. Under MNT minor units that magnitude
is unreachable. **The point is not that it will bite; it is that the port must not copy it** — the
Go equivalent is a sign test on an `int64`. §10 D-2.

### 6.4 Arithmetic that is exact, and where it happens

Everything else in the slice is `BigDecimal.add` / `compareTo` / `merge(…, BigDecimal::add)`, which
are exact:

- `checkDebitAndCreditAmounts` — `…JpaRepositoryImpl.java:309-325`, seeded `BigDecimal.ZERO`,
  compared with `compareTo(...) != 0` — i.e. **scale-insensitive**, so `1200000` and `1200000.000000`
  are equal here. A Go port comparing minor-unit `int64`s reproduces this; a port comparing decimal
  strings would not;
- the charge aggregation maps — `AccountingProcessorHelper.java:408`, `:411`,
  `creditDetailsMap.merge(account, amount, BigDecimal::add)`, and again at `:1433`;
- the provisioning aggregation — `…JpaRepositoryImpl.java:489-505`;
- the chargeback portion sums — `…JpaRepositoryImpl.java:1000-1008`,
  `.reduce(BigDecimal.ZERO, BigDecimal::add)`;
- `calculateRunningBalance` — `JournalEntryRunningBalanceUpdateServiceImpl.java:243-247`,
  `add`/`subtract`.

**Note the `equals` hazard A2 flagged for its own slice applies here too.** `BigDecimal.equals` is
scale-sensitive; every comparison this worker found in the slice uses `compareTo`, which is not.
`grep -n "\.equals(" ` over `JournalEntry.java` returns only `JournalEntryType.DEBIT.getValue().equals(this.type)`
at `:150` and its credit twin at `:154` — `Integer.equals`, not `BigDecimal.equals`. **No
scale-sensitive money comparison was found in the three scope paths.**

---

## 7. Currency handling

### 7.1 What a posting carries

A journal entry carries **a three-character currency code and nothing else**:
`currency_code VARCHAR(3) NOT NULL` (`0001:123-125`), `@Column(length = 3, nullable = false)`
(`JournalEntry.java:55-56`). **No decimal places, no multiples-of, no ISO numeric code, no
currency id.** MNT's minor unit of 2 and its ISO numeric 496 are nowhere on the row.

### 7.2 Where the code is validated

Once per side, on the manual path: `organisationCurrencyRepository.findOneWithNotFoundDetection(currencyCode)`
— `…JpaRepositoryImpl.java:661` (and `:777` for opening balances). That checks the code exists in
the organisation's currency list; it does **not** return decimal places to the posting path, and
the return value is discarded.

On the automatic path the code comes from the source object —
`transactionDTO.setCurrencyCode(currency.getCode())`
(`…JpaRepositoryImpl.java:935`, from `loanTransaction.getLoan().getCurrency()`) — and is **not
re-validated** before the row is written. Where this worker looked: every
`JournalEntry.createNew` call site in `AccountingProcessorHelper.java:912-1184`; none of them calls
a currency repository.

### 7.3 Two different currency shapes come back out, and one of them is wrong for MNT

| Read path | How currency is built | `decimalPlaces` |
|---|---|---|
| **JDBC** — `JournalEntryReadPlatformServiceImpl.java:101-102`, `:121`, `:169-176` | joins `m_currency curr on curr.code = journalEntry.currency_code` and reads `curr.decimal_places as currencyDigits`, `curr.currency_multiplesof as inMultiplesOf`, then `new CurrencyData(code, name, currencyDigits, inMultiplesOf, symbol, nameCode)` | **from the database** |
| **MapStruct** — `JournalEntryMapper.java:104-106` | `default CurrencyData mapCurrency(String currencyCode) { return new CurrencyData(currencyCode); }` | **hard 0** — `CurrencyData.java:49-57` sets `this.decimalPlaces = 0` |

So the same journal entry, read through the two paths, reports different currency metadata. The
MapStruct path reports **zero decimal places for MNT**, whose minor unit is 2. Its consumers are
outside the slice: `grep -rn "JournalEntryMapper" --include='*.java' .` over the checkout (excluding
`/build/`) returns `fineract-investor/.../ExternalAssetOwnersTransferMapper.java:22,33` and
`ExternalAssetOwnersReadServiceImpl.java:24,57` and nothing else. §12 B-5.

**For the port:** currency decimal places are **not** a property of a journal entry in this schema;
they are a join away, and the join is done inconsistently. A Go port carrying `int64` minor units
must decide where the currency's scale comes from and pin it, because the oracle has two answers.
§10 D-3.

**Multi-currency is ungraded.** DEC-2 §8.1 records that of the six `LDG-*` vectors, multi-currency
is one of the named not-graded rows. This document changes nothing about that; it only adds that
the divergence above exists in the read path.

---

## 8. Dates and time zones

`CLAUDE.md`: two zones, `Asia/Ulaanbaatar` (+08) and `Asia/Hovd` (+07), no DST, and **never
hard-code an offset**.

### 8.1 Every date on a journal entry, and where it comes from

| Column | Java | Source | Zone-sensitive? |
|---|---|---|---|
| `entry_date` | `transactionDate` | **the request** (`JournalEntryJsonInputParams.TRANSACTION_DATE`, `…JpaRepositoryImpl.java:164-165`) on the manual path; **the source transaction's date** on the automatic path (`…JpaRepositoryImpl.java:934`, `transactionDTO.setDate(loanTransaction.getTransactionDate())`) | No — it is a `LocalDate` carried through unchanged |
| `submitted_on_date` | `submittedOnDate` | **`DateUtils.getBusinessLocalDate()`**, hard-wired in the entity constructor — `JournalEntry.java:136` | **Yes** — see §8.2 |
| `created_on_utc` / `last_modified_on_utc` | inherited `OffsetDateTime` | Spring Data auditing on `AbstractAuditableWithUTCDateTimeCustom`; the class comment at `…Custom.java:41-42` says the values are *"converted from tenant TZ to UTC before storing … and converted from System TZ to tenant TZ after fetching"* | **Yes** |
| `last_modified_on_utc` (recompute) | — | `DateUtils.getAuditOffsetDateTime()` — `JournalEntryRunningBalanceUpdateServiceImpl.java:178`, `:215` | Yes |

### 8.2 The business date, and why no offset is hard-coded

`DateUtils.getBusinessLocalDate()` (`DateUtils.java:238-240`) returns
`ThreadLocalContextUtil.getBusinessDate()` (`ThreadLocalContextUtil.java:94-97`), which reads the
per-request business-date map. That map is built by
`BusinessDateReadPlatformServiceImpl.getBusinessDates()` (`:71-84`):

```java
LocalDate tenantDate = DateUtils.getLocalDateOfTenant();          // :74
businessDateMap.put(BusinessDateType.BUSINESS_DATE, tenantDate);  // :75
businessDateMap.put(BusinessDateType.COB_DATE, tenantDate);       // :76
if (configurationDomainService.isBusinessDateEnabled()) { … override from m_business_date … }
```

and `DateUtils.getLocalDateOfTenant()` (`:69-71`) is `LocalDate.now(getDateTimeZoneOfTenant())`,
where `getDateTimeZoneOfTenant()` (`:65-68`) is
`ZoneId.of(ThreadLocalContextUtil.getTenant().getTimezoneId())` —
`FineractPlatformTenant.java:38` holds `timezoneId` as tenant configuration.

**So the zone is configuration, never a literal.** `grep -rn "+08\|Asia/"` was not needed: the
chain above shows the only zone input is `tenant.getTimezoneId()`. For a Mongolian deployment that
value must be `Asia/Ulaanbaatar` or `Asia/Hovd`; a wrong value silently shifts
`submitted_on_date` and every audit timestamp. **`[UNVERIFIED: the value actually configured on any
instance — that is a deployment fact, and no instance was reachable.]`**

### 8.3 The one place a posting could land on the wrong day under +08

`FUTURE_DATE` (E-6) is `DateUtils.isDateInTheFuture(localDate)` → `isAfterBusinessDate(localDate)`
→ compares against `getBusinessLocalDate()` (`DateUtils.java:262-264`, `:258-260`). So the
"is this in the future?" question is answered against the **tenant's** today, not the server's.
That is correct behaviour and the port must reproduce it: a server running UTC and a tenant at +08
disagree about "today" for eight hours of every day, and an entry dated *today in Ulaanbaatar*
would be refused as a future date by a UTC comparison.

The same reasoning applies to `submitted_on_date` (`JournalEntry.java:136`): between 16:00 UTC and
24:00 UTC, +08 is already on the next calendar day.

**`entry_date` itself is safe** — it is a `LocalDate` supplied by the caller or copied from a
transaction, and no conversion is applied to it anywhere on the posting path (traced through every
`createNew` call site listed in §3.2).

### 8.4 The closure comparison is strict, in both directions

`checkForBranchClosures` (`AccountingProcessorHelper.java:556-564`) and the manual path
(`…JpaRepositoryImpl.java:636`) both refuse when
`!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate)` — i.e. an entry **on** the
closing date is refused, not only one before it. The reversal path uses the identical predicate at
`:394`. A port that writes `closingDate <= transactionDate` inverted, or that uses `<` where this
uses `!(<)`, changes a refusal.

---

## 9. The refusal surface worth vectoring

Every refusal reachable from `POST /v1/journalentries` and its two sibling commands, with its wire
error code, from `JournalEntryInvalidException.java:42-84` and the call sites already cited:

| Error code | Reason constant | Thrown at |
|---|---|---|
| `error.msg.glJournalEntry.invalid.future.date` | `FUTURE_DATE` | `…JpaRepositoryImpl.java:631` |
| `error.msg.glJournalEntry.invalid.accounting.closed` | `ACCOUNTING_CLOSED` | `:637`, `:397`, `AccountingProcessorHelper.java:560` |
| `error.msg.glJournalEntry.invalid.no.debits.or.credits` | `NO_DEBITS_OR_CREDITS` | `:648`, `:192`, `:212` |
| `error.msg.glJournalEntry.invalid.mismatch.debits.credits` | `DEBIT_CREDIT_SUM_MISMATCH` | `:324` |
| `error.msg.glJournalEntry.invalid.empty.account.or.amount` | `DEBIT_CREDIT_ACCOUNT_OR_AMOUNT_EMPTY` | `:313`, `:319` |
| `error.msg.glJournalEntry.invalid.account.disabled` | `GL_ACCOUNT_DISABLED` | `:333` |
| `error.msg.glJournalEntry.invalid.account.manual.adjustments.not.permitted` | `GL_ACCOUNT_MANUAL_ENTRIES_NOT_PERMITTED` | `:336` |
| `error.msg.glJournalEntry.invalid.debit.or.credit.accounts` | `INVALID_DEBIT_OR_CREDIT_ACCOUNTS` | `:257`, `:261` |
| **`DEBIT_CREDIT_SUM_MISMATCH_WITH_AMOUNT`** (the raw enum name — **no `errorCode()` branch**) | dead constant | never |
| `error.msg.glJournalEntry.invalid.credits` / `.invalid.debits` | `JournalEntryRuntimeException` | `:286`, `:301` |
| `error.msg.glJournalEntry.asset.externalization.not.enabled` | `JournalEntryRuntimeException` | `:175` |
| `error.msg.financial.activity.mapping.opening.balance.contra.account.cannot.be.null` | `GeneralPlatformDomainRuleException` | `:712` |
| `error.msg.configuration.opening.balance.contra.account.value.is.invalid.account.type` | `GeneralPlatformDomainRuleException` | `:768` |
| `error.msg.journalentry.defining.openingbalance.not.allowed` | `GeneralPlatformDomainRuleException` | `:813` |
| `error.msg.glJournalEntry.unknown.data.integrity.issue` | `PlatformDataIntegrityException` via `ErrorHandler.getMappable` | `:694-699` |
| `"Meltdown in advanced accounting…"` ×3 | `PlatformDataIntegrityException` — **no `error.msg.` code**, a bare English string | `AccountingProcessorHelper.java:434`, `:442`, `:1451` |
| `"Recent Portfolio changes w.r.t Charges for Savings have Broken the accounting code"` ×2 | `PlatformDataIntegrityException` — likewise | `AccountingProcessorHelper.java:825`, `:860` |
| `"Recent Portfolio changes w.r.t Charges for shares have Broken the accounting code"` ×2 | `PlatformDataIntegrityException` — likewise | `AccountingProcessorHelper.java:1118`, `:1150` |
| `error.msg.chargeRefundChargeType.can.only.be.P.or.F` | `PlatformDataIntegrityException` | `AccountingProcessorHelper.java:1401-1402` |
| not-found on the reversal | `JournalEntriesNotFoundException` | `:350` — **also** the response for "this transaction is automatic" and for "this transaction has one leg" (§5.1) |

**Seven throw sites, carrying three distinct messages, have no `error.msg.*` code at all** — only an
English sentence. `grep -n "throw new PlatformDataIntegrityException"` over
`AccountingProcessorHelper.java` returns eight lines: `:434`, `:442` (Meltdown), `:825`, `:860`
(Savings), `:1118`, `:1150` (shares), `:1401` (the one that *does* carry a code), `:1451`
(Meltdown). A port that invents codes for the seven changes the wire contract; a port that
reproduces them ships English strings. §10 D-5.

---

## 10. What the Go port must reproduce, and the decisions this slice forces

Decisions to be **recorded**, not inherited silently.

| # | Decision | Recommendation |
|---|---|---|
| D-1 | The single rounding site — the tax pro-rate at `…JpaRepositoryImpl.java:981`, `multiply(mc).divide(mc)` at `(19, HALF_UP)` — has no `setScale` after it and lands in a `numeric(19,6)` column (§6.2) | The port must state, in one place, where a computed money value is rounded to MNT minor units and with which mode. Do **not** leave it implicit. Any parity vector touching a taxed charge must record both the oracle's six-decimal text and the port's minor-unit integer, per DEC-2 §4.3's `principal_minor`/`principal_major_text` pairing. |
| D-2 | Four `BigDecimal.floatValue() < 0` sign tests on the posting path (§6.3) | Port as an `int64` sign test. Record it as a **deliberate divergence in mechanism with identical behaviour over the reachable domain**, and say why (float subnormals are unreachable at minor-unit granularity). Do not copy the float. |
| D-3 | Currency decimal places are not on the row, and the two read paths disagree — DB join vs a hard `0` (§7.3) | Carry currency scale from one authority in the port. Assert at construction that a posting's currency scale matches the tenant's configured scale for that code. |
| D-4 | Four mutually inconsistent reversal shapes (§5.5) | Do not unify them silently — that changes `transaction_id`, `manual_entry`, the date and the `entity_*` columns on three of the four. Pick one shape for the port's own API, and treat the other three as **oracle behaviours to be matched only where a vector exists**. Record the choice. |
| D-5 | Seven throw sites across three distinct messages carry a bare English string and no `error.msg.*` code; one enum constant (`DEBIT_CREDIT_SUM_MISMATCH_WITH_AMOUNT`) is dead and has no code branch at all (§9) | Do not port the dead constant. For the uncoded refusals, decide explicitly whether the port emits a code (a wire divergence, recorded) or the same string. |
| D-6 | `Idempotency-Key` is **mandatory** for us and **optional** in the oracle (§4.4) | A structural rule in the same class as DEC-2's `I-3`/`I-4`: enforced by a source guard, never by a vector, because the oracle produces no refusal to capture. |
| D-7 | The two written balance columns and the flag (§2.5) | **Do not decide here.** G-12 and G-22 are open; this document supplies the mechanism and takes no option. What A1 *can* say from source: a conforming Go port that derives balances will differ from the oracle on exactly `office_running_balance`, `organization_running_balance` and `is_running_balance_calculated`, and on `last_modified_*` as a side effect of the nightly rewrite. |
| D-8 | The `transaction_date` column is present, indexed, unmapped and remarked *"Unfinished. Not maintained."*, while the Java field named `transactionDate` maps to `entry_date` (§2.2) | Drop `transaction_date` from the Go schema, or carry it as an explicitly-null legacy column. Never name a Go field after it. |
| D-9 | `generateTransactionId` is millis+userId+officeId parsed as a `long` (§3.1), with no unique index (§2.4) | The port needs a real, collision-free transaction identifier. That is a **divergence in generated values**, so no vector can pin the id itself; vectors must grade the *grouping*, not the string. |
| D-10 | Balance holds by construction on the automatic path; nothing checks it (§4.2) | The port should assert Σdebits == Σcredits per `transaction_id` before commit. That is **stricter than the oracle** and cannot fail a parity comparison on well-formed oracle data — but it changes behaviour on malformed data, so record it. |
| D-11 | An automatic posting cannot be reversed through the reverse endpoint (`manualEntry = true` filter, `JournalEntryRepository.java:30-31`), and a one-leg transaction returns *not found* rather than *not permitted* (§5.1) | Reproduce for parity, including the misleading not-found. Do not "improve" the status code without recording it. |

### What a capture plan must ask the oracle, that source cannot answer

These are the open questions the next capture plan needs; each is a *cheap* probe against a live
instance and none can be settled by reading:

1. **What scale does a posted `amount` actually come back at**, for an amount supplied with fewer
   than six decimals? (§2.3 — the insert-time coercion.)
2. **Can the oracle produce sub-minor-unit residue in `acc_gl_journal_entry.amount` at all?** The
   tax pro-rate at `:981` is the one arithmetic path that could. DEC-2 §4.3 already carries this as
   an `[UNVERIFIED]`; A1 now names the exact line that would produce it. A charge with a tax
   component, part-paid, is the probe.
3. **What HTTP status and body does the reverse endpoint return for (a) an automatic transaction id,
   (b) a one-leg transaction?** (§5.1 — both are predicted to be `JournalEntriesNotFoundException`.)
4. **What does a `POST /v1/journalentries` with no `Idempotency-Key` return?** (§4.4 — predicted:
   success. It is the *absence* of a refusal that has to be recorded.)
5. **Does `generateTransactionId` ever collide, or throw `NumberFormatException`?** (§3.1.)
6. **What is `submitted_on_date` for a posting made between 16:00 and 24:00 UTC on a tenant at +08?**
   (§8.3 — the single highest-value date probe for a Mongolian deployment.)
7. **Does the office-scoped recompute leave the two balance columns describing different ledgers?**
   `A2-29` measured yes on a one-office tenant; the source reason is `:211` writing one column.
   Re-confirmation is cheap and it is the sharpest evidence for G-12.

---

## 11. `[UNVERIFIED]` — what this worker could NOT establish

Each is a gap, not a guess.

1. **Anything about runtime behaviour.** There is no running Fineract and no PostgreSQL in this
   session. Every claim above is about source text. Where a sentence could be read as an
   observation, it is not one.
2. **The scale PostgreSQL actually stores** when a `BigDecimal` of scale ≠ 6 is inserted into
   `numeric(19,6)` (§2.3). Standard `numeric` semantics say it rounds to the declared scale; that
   is documented database behaviour, not something observed on this instance.
3. **Whether `Long.parseLong(uniqueVal)` in `generateTransactionId` can overflow in practice**
   (§3.1). The arithmetic is read off `:690`; no user/office id ranges were sampled.
4. **Whether the opening-balance NPE at `:710` is reachable** — it depends on whether
   `acc_gl_financial_activity_account` can hold a row with a null `gl_account_id`, which is A2's
   table (§3.3).
5. **Whether anything still writes `created_date` / `lastmodified_date`** (the pre-`0025` audit
   columns). `grep -rn "created_date\|lastmodified_date"` over the three scope paths returns
   nothing; `0025:40-41` drops their NOT NULL and `0025:72-76` back-fills `submitted_on_date` from
   `created_date`. The whole checkout was **not** swept for other writers.
6. **The literal names PostgreSQL assigns** to the primary key and to any auto-generated index on
   this table — the changelog names the FK constraints (`0001:7611-7630`, `0025:47-56`) but not the
   PK.
7. **Whether the automatic paths ever produce an unbalanced transaction.** §4.2 establishes that
   *nothing would catch it*; it does not establish that it happens. That distinction matters and is
   not blurred here.
8. **Whether `?runningBalance=true` on `GET /v1/journalentries` is reachable on PostgreSQL.**
   `A2-29` recorded that the *`/glaccounts`* list variant emits MySQL-only `group by … desc` and
   fails on PostgreSQL. This worker did **not** re-read the `/journalentries` SQL for the same
   defect, and did not execute either.
9. **The consumers of `JournalEntryMapper`'s zero-decimal `CurrencyData`** (§7.3) — the two
   `fineract-investor` files were located by grep but their handling of `decimalPlaces` was not
   traced; that module is Tier B.
10. **What `AdvancedMappingtDTO` (the second `fineract-core` file in scope, 31 LOC) contributes**
    beyond being constructed at `…JpaRepositoryImpl.java:890`, `:914`, `:916`. Its consumers are in
    the loan-classification path, which is a different slice.
11. **Which of the six processor classes are reachable for an NBFI deployment.** Savings and shares
    processors are ported-but-disabled territory under the deposit-taking activation gate; this
    document describes them because they write to the same table, and takes no position on
    activation.
12. **Whether `JournalEntriesApiResourceSwagger.java:159`'s `Double amount` reaches any runtime
    path.** It is an OpenAPI model class; it was read, not traced.
13. **Everything `A2-29` measured against a live oracle** is cited here as *`A2-29` measured it*,
    never re-asserted as this worker's own observation. What this worker independently established
    is the **source mechanism** (§2.5), which is a different kind of evidence.

---

## 12. Found outside the three assigned scope paths

Read only. Nothing outside the scope paths was modified.

| # | Finding | Where |
|---|---|---|
| B-1 | The package `org.apache.fineract.accounting.journalentry` is **split across three Gradle modules** — entity in `fineract-accounting`, its debit/credit enum in `fineract-core`, every writer in `fineract-provider`. Same shape as A2 B-1, one module worse. The Go boundary must follow the Java package. | §1.2 |
| B-2 | **A2 and A1 both transcribe `AccountingProcessorHelper`'s mapping resolution.** A2 §1.3/§4 documents it as "A1's territory"; this document documents the *posting* and deliberately does **not** re-derive the resolution order. Neither slice should be treated as the authority on the other's half. | §1.3 |
| B-3 | `GLClosure` / `GLClosureRepository` (`fineract-accounting/.../closure/`) gate every write path in this slice (E-7) and are in **neither** A1's nor A2's assigned paths. Whoever ports A1 needs closure semantics, and no slice currently owns them. | §4.1 E-7 |
| B-4 | `CurrencyData(String code)` sets `decimalPlaces = 0` (`fineract-core/.../monetary/data/CurrencyData.java:49-57`). Any caller that builds a `CurrencyData` from a bare code silently claims zero minor units. `JournalEntryMapper.java:104-106` is one such caller. | §7.3 |
| B-5 | `fineract-investor`'s `ExternalAssetOwnersTransferMapper.java:33` uses `JournalEntryMapper` as a MapStruct `uses =` component, so the zero-decimal currency propagates into the investor read model. Tier B, but it is A1's mapper doing it. | §7.3 |
| B-6 | **`Idempotency-Key` is optional in the oracle** — `IdempotencyKeyResolver.java:36` generates a UUID when the header is absent. This is a platform (Tier C) fact with a direct consequence for every Tier A money-movement endpoint, not just this one. | §4.4 |
| B-7 | `MoneyHelper.getRoundingMode()` **throws `IllegalStateException` if the tenant was never initialised** (`MoneyHelper.java:74-81`). The ratified requirement to "pin `HALF_UP` explicitly in tenant config, never inherit a default" is therefore enforced by the oracle itself — there is no default to inherit. Worth recording as *support* for the ratified parameter, not a new decision. | §6.1 |
| B-8 | `JournalEntryRepository.findTrialBalanceLinesForDate` (`:52-66`) projects `SUM(CASE WHEN je.type = 1 THEN -1 * je.amount ELSE je.amount END)` **and** an unsigned `SUM(je.amount)` in the same row. A2 §8 identified the unsigned one as what gets stored in `m_trial_balance.closing_balance`. **This query lives in A1's repository and feeds A2's table** — the two slices must agree who owns it. | §12, cross-ref A2 §8 |
| B-9 | `acc_gl_journal_entry` has **no index on `account_id` + `entry_date`**, the exact pair the running-balance recompute scans (`JournalEntryRunningBalanceUpdateServiceImpl.java:255-258`, `:261-266`). There is an FK index on `account_id` alone (`0001:5643`) and one on `transaction_id` (`0177:31`). Cheap composite index in the Go schema. | §2.4 |
| B-10 | The nightly recompute calls `platformSecurityContext.authenticatedUser().getId()` **inside the per-row loop** (`:178`) and again per row at `:214`. Not a correctness issue; a porting note. | §2.5 |

---

## 13. Complete citation index

Every file this document cites, so the reviewer can re-open them in one pass. All paths relative to
`/home/user/fineract` at commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

**In scope — `fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/`:**

- `service/JournalEntryWritePlatformServiceJpaRepositoryImpl.java` (read in full, 1,053 lines)
- `service/AccountingProcessorHelper.java` (1,457 lines; `:89-94`, `:380-446`, `:500-620`, `:912-1060`, `:1148-1184`, `:1330-1457` read)
- `service/JournalEntryRunningBalanceUpdateServiceImpl.java` (`:60-284` read)
- `service/JournalEntryReadPlatformServiceImpl.java` (`:82-235`, `:279-370` read)
- `service/CashBasedAccountingProcessorForLoan.java` (`:52-56` method map, `:226-315`, `:727-848`, `:965-1005` read)
- `service/AccrualBasedAccountingProcessorForLoan.java` (`:181-300`, `:2195-2235` read)
- `data/GLAccountBalanceHolder.java`
- `api/JournalEntriesApiResource.java` (`:75-245` read)
- `api/JournalEntriesApiResourceSwagger.java` (`:159` only)
- `handler/CreateJournalEntryCommandHandler.java`

**In scope — `fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/`:**

- `domain/JournalEntry.java` (read in full)
- `domain/JournalEntryRepository.java` (read in full)
- `command/JournalEntryCommand.java`, `command/SingleDebitOrCreditEntryCommand.java`
- `serialization/JournalEntryCommandFromApiJsonDeserializer.java`
- `exception/JournalEntryInvalidException.java` (read in full)
- `api/JournalEntryJsonInputParams.java`
- `data/JournalEntryDataValidator.java`
- `service/JournalAmountHolder.java`
- `JournalEntryMapper.java` (read in full)

**In scope — `fineract-core/src/main/java/org/apache/fineract/accounting/journalentry/`:**

- `domain/JournalEntryType.java` (read in full)
- `data/AdvancedMappingtDTO.java` (existence and construction sites only — §11 item 10)

**Read outside scope, cited, never modified:**

- `fineract-core/.../organisation/monetary/domain/MoneyHelper.java` (`:25-100`)
- `fineract-core/.../organisation/monetary/data/CurrencyData.java` (`:32-75`)
- `fineract-core/.../infrastructure/core/service/DateUtils.java` (`:55-95`, `:236-270`)
- `fineract-core/.../infrastructure/core/service/ThreadLocalContextUtil.java` (`:82-117`)
- `fineract-core/.../infrastructure/core/service/MathUtil.java` (`:59-65`, `:196-202`, `:364-366`)
- `fineract-core/.../infrastructure/core/domain/AbstractAuditableWithUTCDateTimeCustom.java`
- `fineract-core/.../infrastructure/core/domain/AuditableFieldsConstants.java` (`:28-31`)
- `fineract-core/.../infrastructure/core/domain/FineractPlatformTenant.java` (`:38` only)
- `fineract-core/.../infrastructure/businessdate/service/BusinessDateReadPlatformServiceImpl.java` (`:60-84`)
- `fineract-core/.../infrastructure/core/filters/IdempotencyStoreFilter.java` (`:55-73`)
- `fineract-core/.../commands/service/IdempotencyKeyResolver.java` (`:29-36`)
- `fineract-core/.../commands/service/IdempotencyKeyGenerator.java`
- `fineract-provider/src/main/resources/application.properties` (`:179`, `:857` only)
- `fineract-provider/src/main/resources/db/changelog/tenant/parts/0001_initial_schema.xml`
  (`:112-175` the `createTable`; `:5643-5692` FK indexes; `:7164-7166`; `:7611-7630`)
- `fineract-provider/src/main/resources/db/changelog/tenant/parts/0025_add_audit_entries_to_journal_entry.xml` (read in full)
- `fineract-provider/src/main/resources/db/changelog/tenant/parts/0117_set_datetime_precision.xml` (`:25-37`)
- `fineract-provider/src/main/resources/db/changelog/tenant/parts/0177_acc_journal_entry_index.xml` (read in full)
- `fineract-investor/.../service/ExternalAssetOwnersTransferMapper.java` (`:22`, `:33` only)
- `fineract-investor/.../service/ExternalAssetOwnersReadServiceImpl.java` (`:24`, `:57` only)

**Project documents consulted (in `/home/user/wt/T487`):**

- `CLAUDE.md` — every non-negotiable applied above
- `docs/analysis/tierA-a2-behaviour.md` — house style; §1.2, §1.3, §4, §8 cross-referenced
- `docs/adr/DEC-2-gl-accounting-adapter.md` — §4.3 (money representation), §4.4 (`I-1`…`I-7`),
  §4.4.1, §8.1
- `.softhouse/gates.md` — `G-12` (raising block and the `A2-29` MEASURED block), `G-22`
