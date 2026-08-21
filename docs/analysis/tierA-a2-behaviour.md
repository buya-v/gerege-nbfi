# Tier A · Slice A2 — chart of accounts, product-to-account mapping, financial activity accounts

**Fineract behaviour extraction. Analyst output. No Go, no contract change.**

| | |
|---|---|
| Worker | `A2-1` |
| Branch | `softhouse/A2-1-behaviour` |
| Oracle | Fineract reference implementation, pinned checkout `/Users/buv/fineract` |
| Commit | `426a23544e8426a38ae43ae404670a0a7e85b9eb` (2026-08-12 14:59:16 +0200), `git status --porcelain` empty at extraction time |
| Date | 2026-08-21 |

All `FILE:LINE` citations are relative to the pinned checkout root and were opened and read by
this worker. Where a claim rests on a construct this worker could not evaluate here (a Liquibase
type mapping, a runtime reachability question) it is tagged **`[UNVERIFIED]`** with the reason.

---

## 0. How to read this document

The reviewer for this slice will re-derive. Three conventions to make that cheap:

- A claim with a bare `FILE:LINE` is a claim **about that line's text**, nothing more.
- A claim that two things *disagree* always cites **both** sides.
- Section §11 lists everything this worker could not establish. Section §12 lists everything of
  value found **outside** the four assigned scope paths — none of it was changed, only read.

---

## 1. Scope, and where the slice's own dependencies actually live

### 1.1 The four assigned paths (58 files, 6,636 LOC — count confirmed by `wc -l`)

| Path | Files | LOC |
|---|---|---|
| `fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount` | 25 | 2,165 |
| `fineract-accounting/src/main/java/org/apache/fineract/accounting/producttoaccountmapping` | 12 | 2,643 |
| `fineract-accounting/src/main/java/org/apache/fineract/accounting/financialactivityaccount` | 20 | 1,333 |
| `fineract-provider/src/main/java/org/apache/fineract/accounting/productaccountmapping` | 1 | 495 |

### 1.2 The critical finding about scope: the slice's own core types are NOT in the slice

**The `glaccount` package under `fineract-accounting` does not contain `GLAccount`.** The entity,
both enums, the repository, the data DTO and the accounting placeholder constants all live in
**`fineract-core`**, under the *same Java package names*:

| Type the slice needs | Actual file |
|---|---|
| `GLAccount` (entity) | `fineract-core/src/main/java/org/apache/fineract/accounting/glaccount/domain/GLAccount.java` |
| `GLAccountType` | `fineract-core/src/main/java/org/apache/fineract/accounting/glaccount/domain/GLAccountType.java` |
| `GLAccountUsage` | `fineract-core/src/main/java/org/apache/fineract/accounting/glaccount/domain/GLAccountUsage.java` |
| `GLAccountRepository` / `…Wrapper` | `fineract-core/src/main/java/org/apache/fineract/accounting/glaccount/domain/` |
| `GLAccountData` | `fineract-core/src/main/java/org/apache/fineract/accounting/glaccount/data/GLAccountData.java` |
| `GLAccountJsonInputParams` | `fineract-core/src/main/java/org/apache/fineract/accounting/glaccount/api/GLAccountJsonInputParams.java` |
| `AccountingConstants` (all placeholder enums + `FinancialActivity`) | `fineract-core/src/main/java/org/apache/fineract/accounting/common/AccountingConstants.java` |
| `PortfolioProductType` | `fineract-core/src/main/java/org/apache/fineract/portfolio/PortfolioProductType.java` |

Only `glaccount/domain/TrialBalance*.java` actually lives in `fineract-accounting/.../glaccount/domain/`.

The single file in the fourth path (`fineract-provider/.../productaccountmapping/service/`) has a
sibling class **in a different Gradle module under the identical Java package**:
`LoanProductToGLAccountMappingHelper` is at
`fineract-loan/src/main/java/org/apache/fineract/accounting/productaccountmapping/service/LoanProductToGLAccountMappingHelper.java`
and is referenced with no import from
`fineract-provider/src/main/java/org/apache/fineract/accounting/productaccountmapping/service/ProductToGLAccountMappingWritePlatformServiceImpl.java:55`.
That is a **split package across two modules** — a Java-module-system hazard and a porting fact.

> **Consequence for the port.** A Go package boundary drawn on the Fineract *directory* boundary
> would leave A2 with no account entity and no enums. The boundary must be drawn on the *Java
> package* (`org.apache.fineract.accounting.glaccount`, `…producttoaccountmapping`,
> `…financialactivityaccount`, `…productaccountmapping`), which spans `fineract-core`,
> `fineract-accounting`, `fineract-loan` and `fineract-provider`. §12 backlog B-1.

### 1.3 The resolution code path is not in the slice either

The question "given a product + transaction type + optional charge/payment type, which GL account?"
is answered by
`fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccountingProcessorHelper.java`
— the `journalentry` package, i.e. **slice A1's** territory. A2 owns the *storage and the finder
queries*; A1 owns the *selection*. This document traces the selection anyway (it is priority 3 of
the brief), citing A1's file explicitly each time so the reviewer can see the boundary.

---

## 2. The GL account tree

### 2.1 Entity and table

`fineract-core/.../glaccount/domain/GLAccount.java:42-84`

```
@Table(name = "acc_gl_account", uniqueConstraints = { @UniqueConstraint(columnNames = { "gl_code" }, name = "acc_gl_code") })
```

| Java field | Column | JPA declaration | Liquibase DDL |
|---|---|---|---|
| `parent` (`@ManyToOne` LAZY) | `parent_id` | `GLAccount.java:50-52` | `BIGINT`, nullable, `DEFAULT NULL` — `0001_initial_schema.xml:56` |
| `hierarchy` | `hierarchy` | `nullable=true, length=50` — `:54-55` | `VARCHAR(50)`, **nullable, no index** — `0001_initial_schema.xml:57` |
| `children` (`@OneToMany` LAZY on `parent_id`) | — | `:57-59` | (derived from `parent_id`) |
| `name` | `name` | **`nullable=false, length=45`** — `:61-62` | **`VARCHAR(200)` NOT NULL** — `0001_initial_schema.xml:53` |
| `glCode` | `gl_code` | **`nullable=false, length=100`** — `:64-65` | **`VARCHAR(45)` NOT NULL UNIQUE (inline)** — `0001_initial_schema.xml:58-60` |
| `disabled` | `disabled` | `nullable=false` — `:67-68` | `boolean` NOT NULL DEFAULT `false` — `:61-63` |
| `manualEntriesAllowed` | `manual_journal_entries_allowed` | `nullable=false`, **Java initialiser `= true`** — `:70-71` | `boolean` NOT NULL DEFAULT `true` — `:64-66` |
| `type` (Integer) | `classification_enum` | `nullable=false` — `:73-74` | `SMALLINT` NOT NULL — `:70-72` |
| `usage` (Integer) | `account_usage` | `nullable=false` — `:76-77` | `TINYINT` NOT NULL **DEFAULT 2** — `:67-69` |
| `description` | `description` | `nullable=true, length=500` — `:79-80` | `VARCHAR(500)` nullable — `:74` |
| `tagId` (`@ManyToOne` `CodeValue`) | `tag_id` | `:82-84` | `INT` nullable — `:73` |

**Three length disagreements, all real:**

| Field | JPA `length` | Liquibase | API validator |
|---|---|---|---|
| `name` | **45** (`GLAccount.java:61`) | **200** (`0001_initial_schema.xml:53`) | **200** (`GLAccountCommand.java:43`) |
| `gl_code` | **100** (`GLAccount.java:64`) | **45** (`0001_initial_schema.xml:58`) | **45** (`GLAccountCommand.java:45-46`) |
| `description` | 500 | 500 | 500 — all three agree |

The DDL is authoritative on a Liquibase-managed Fineract (Hibernate does not generate schema here;
see §5.2). So the **effective** limits are name ≤ 200 and glCode ≤ 45, and the JPA `length`
attributes are dead metadata that disagrees with the database in both directions. A port that
copies the entity annotations would truncate names at 45 and accept 100-char GL codes the database
rejects.

Also note the DDL default `account_usage = 2` (= `HEADER`, §3.2) — but every write path supplies
`usage` explicitly from the command (`GLAccount.fromJson`, `GLAccount.java:92`), so the default is
only reachable by direct SQL insert. `[UNVERIFIED: no runtime probe was run]`

### 2.2 The hierarchy string — how it is built and where it goes stale

`fineract-core/.../glaccount/domain/GLAccount.java:186-197`

```java
public void generateHierarchy() {
    if (this.parent != null) {
        this.hierarchy = this.parent.hierarchyOf(getId());
    } else {
        this.hierarchy = ".";
    }
}
private String hierarchyOf(final Long id) {
    return this.hierarchy + id.toString() + ".";
}
```

`hierarchyOf` is invoked **on the parent**, so it reads the *parent's* `hierarchy` field. Therefore:

- root account → `"."`
- child of root id 5 → `"." + "5" + "."` = `".5."` — wait: the *child's* hierarchy is
  `parent.hierarchy + childId + "."`, i.e. for a child with id 7 of a root with id 5:
  `parent.hierarchy` is `"."`, so the child's hierarchy is `".7."`.
  **The parent's own id does not appear in the child's hierarchy string at the first level**; it
  appears only from the grandchild down, because the grandchild inherits `".7."` and appends its
  own id. This is worth stating precisely because it is counter-intuitive: the string is
  *"the concatenation of the ids of my ancestors strictly below the root, plus my own id"*.
  A grandchild id 9 gets `".7." + "9" + "."` = `".7.9."`.

**Creation sequence** — `fineract-accounting/.../glaccount/service/GLAccountWritePlatformServiceJpaRepositoryImpl.java:96-100`:

```java
this.glAccountRepository.saveAndFlush(glAccount);   // :96  — assigns the id
glAccount.generateHierarchy();                       // :98  — needs getId()
this.glAccountRepository.saveAndFlush(glAccount);    // :100 — persists the hierarchy
```

Two flushes are required because the hierarchy embeds the account's own generated id.

**Re-parenting on update** — `GLAccountWritePlatformServiceJpaRepositoryImpl.java:134-138`:

```java
if (changesOnly.containsKey(GLAccountJsonInputParams.PARENT_ID.getValue())) {
    final GLAccount parentAccount = validateParentGLAccount(parentId);
    glAccount.setParent(parentAccount);
    glAccount.generateHierarchy();
}
```

**Only the moved account's own hierarchy is regenerated. Its descendants are not touched.** There
is no cascade, no recursive walk and no `UPDATE … WHERE hierarchy LIKE …` anywhere in the slice
(grep of the four scope paths for `hierarchy` returns the entity, this call, and the SQL decoration
in §2.3 only). So after re-parenting a header account that has children, every descendant's
`hierarchy` column is stale, and the indentation computed in §2.3 is wrong for them until they are
individually re-saved. **This is a defect in the oracle that a faithful port must decide whether to
reproduce** (see §10 D-6).

`hierarchy` is nullable in the DDL and has **no index** (`0001_initial_schema.xml:57`; the only two
indexes on the table are on `tag_id` and `parent_id` — `0001_initial_schema.xml:5486-5488`,
`:5551-5553`). A subtree query by hierarchy prefix would be a sequential scan.

### 2.3 The one consumer of `hierarchy`

`fineract-accounting/.../glaccount/service/GLAccountReadPlatformServiceImpl.java:49`

```java
private static final String NAME_DECORATED_BASE_ON_HIERARCHY =
  "concat(substring('........................................', 1, ((LENGTH(hierarchy) - LENGTH(REPLACE(hierarchy, '.', '')) - 1) * 4)), name)";
```

Depth = (count of `.` in `hierarchy`) − 1; the display name is prefixed with `4 × depth` dot
characters. Exposed as `nameDecorated` (`GLAccountReadPlatformServiceImpl.java:72, :98, :108`).
This is the *only* place the hierarchy string is read in the whole slice. It is presentation only —
**no money decision anywhere depends on `hierarchy`.**

### 2.4 Header vs detail — what makes an account usable

`fineract-core/.../glaccount/domain/GLAccount.java:182-184, :199-201`

```java
public boolean isHeaderAccount()  { return GLAccountUsage.HEADER.getValue().equals(this.usage); }
public boolean isDetailAccount()  { return GLAccountUsage.DETAIL.getValue().equals(this.usage); }
```

Both compare the **`getValue()`** of the enum against the stored `Integer`, never `ordinal()`.

Where usage actually gates behaviour:

| Rule | Site |
|---|---|
| A **detail** account may not be a parent | `GLAccountWritePlatformServiceJpaRepositoryImpl.java:229-231` → `GLAccountInvalidParentException` |
| A **header** account with children may not be deleted | `…:196-198` → `GLAccountInvalidDeleteException(HAS_CHILDREN)` |
| Changing usage **to header** is refused if journal entries exist | `…:153-158` → `GLAccountInvalidUpdateException(TRANSANCTIONS_LOGGED)` |
| Product-mapping selection lists offer only **enabled detail** accounts | `GLAccountReadPlatformServiceImpl.java:214-222` (`retrieveAllEnabledDetailGLAccounts`, `usage=DETAIL`, `disabled=false`) |

**There is no check anywhere in this slice that a journal entry may only be posted to a DETAIL
account, nor that a product mapping may only point at a DETAIL account.** `getAccountByIdAndType`
(`ProductToGLAccountMappingHelper.java:727-736`) validates the account **type** only; usage is not
consulted. The "only detail accounts" rule is enforced by the *dropdown*, not by the *domain*.
A port that adds the check would refuse inputs the oracle accepts. `[UNVERIFIED: whether any code
outside the four scope paths enforces detail-only posting — not swept]`

### 2.5 `manualEntriesAllowed` and `disabled`

- `manualEntriesAllowed` — declared `nullable=false` with Java initialiser `true`
  (`GLAccount.java:70-71`), DDL default `true` (`0001_initial_schema.xml:64-66`), **mandatory on
  create** (`GLAccountCommand.java:60-61`, `.notBlank()`), and settable on update
  (`GLAccount.java:174-175`). **Nothing in the four scope paths reads it.** Its only consumer is a
  read filter (`GLAccountReadPlatformServiceImpl.java:172-179`). The enforcement that a *manual*
  journal entry may not target such an account is not in this slice.
  `[UNVERIFIED: where the flag is enforced — journalentry, i.e. A1, is the likely site but was not
  swept]`
- `disabled` — settable on create and update. The **only** rule attached to it in this slice is
  that you cannot disable an account that any product maps to (§2.6, `validateForAttachedProduct`).
  A disabled account is **not** excluded from mapping resolution at posting time — `AccountingProcessorHelper`
  never reads `disabled` (§4).

### 2.6 Every refusal on create / update / delete

All in `fineract-accounting/.../glaccount/service/GLAccountWritePlatformServiceJpaRepositoryImpl.java`
unless stated. These are the contract-refusal vectors for A2.

#### CREATE (`createGLAccount`, `:73-111`)

| # | Condition | Exception / error code | Site |
|---|---|---|---|
| C1 | `name` blank or > 200 chars | `PlatformApiDataValidationException`, `validation.msg.validation.errors.exist` | `GLAccountCommand.java:43` |
| C2 | `glCode` blank or > 45 chars | same | `GLAccountCommand.java:45-46` |
| C3 | `parentId` present and ≤ 0 | same | `GLAccountCommand.java:48-49` |
| C4 | `type` null, or outside `[GLAccountType.getMinValue(), getMaxValue()]` = **[1,5]** | same | `GLAccountCommand.java:51-52` |
| C5 | `usage` outside `[GLAccountUsage.getMinValue(), getMaxValue()]` = **[1,2]**. Note: `.notNull()` is **not** applied, so a *missing* `usage` passes the validator | same | `GLAccountCommand.java:54-55` |
| C6 | `description` present and > 500 | same | `GLAccountCommand.java:57-58` |
| C7 | `manualEntriesAllowed` blank/absent | same | `GLAccountCommand.java:60-61` |
| C8 | `tagId` present and ≤ 0 | same | `GLAccountCommand.java:63-64` |
| C9 | any JSON key not in `GLAccountJsonInputParams` (`id, name, parentId, glCode, disabled, manualEntriesAllowed, type, usage, description, tagId`) | `checkForUnsupportedParameters` | `GLAccountCommandFromApiJsonDeserializer.java:52-53`; enum at `GLAccountJsonInputParams.java:29-38` |
| C10 | blank JSON body | `InvalidJsonException` | `GLAccountCommandFromApiJsonDeserializer.java:47-49` |
| C11 | `parentId` names a non-existent account | `GLAccountNotFoundException` | `:226-227` |
| C12 | `parentId` names a **DETAIL** account | `GLAccountInvalidParentException`, `error.msg.glaccount.parent.invalid` | `:229-231`; exception at `exception/GLAccountInvalidParentException.java:28-31` |
| C13 | `tagId` present but not a code value of the code name matching the account type | `CodeValueNotFoundException` (via `findOneByCodeNameAndIdWithNotFoundDetection`) | `:252-271`; code names at `AccountingConstants.java:578-582` |
| C14 | duplicate `gl_code` (DB unique constraint) | `GLAccountDuplicateException`, `error.msg.glaccount.glcode.duplicate` | `:242-245`, triggered by the DB error text containing `acc_gl_code` |

**C14 is fragile in a way the port must know.** The handler matches on the *substring* `acc_gl_code`
in the driver's message (`:242`). The JPA `@UniqueConstraint` names it `acc_gl_code`
(`GLAccount.java:43`) but **Hibernate does not create the schema here** — the Liquibase DDL declares
the uniqueness inline with `unique="true"` and **no name** (`0001_initial_schema.xml:58-60`), so
PostgreSQL auto-names the index (conventionally `acc_gl_account_gl_code_key`). If PostgreSQL's
message does not contain the literal `acc_gl_code`, the branch falls through to the generic
`error.msg.glAccount.unknown.data.integrity.issue` at `:248`.
`[UNVERIFIED: which of the two error codes a duplicate glCode actually returns on PostgreSQL — no
live probe was run this fire. This is a high-value capture: it decides a contract refusal code.]`

#### UPDATE (`updateGLAccount`, `:115-175`)

| # | Condition | Exception / error code | Site |
|---|---|---|---|
| U1 | validator rules, all `ignoreIfNull` variants of C1–C6, C8 | `PlatformApiDataValidationException` | `GLAccountCommand.java:77-94` |
| U2 | **none** of `name, glCode, parentId, type, description, disabled` supplied | `anyOfNotNull` failure | `GLAccountCommand.java:96` |
| U3 | `disabled=true` supplied **and** ≥1 row in `acc_product_mapping` references this account | `GLAccountDisableException`, `error.msg.glaccount.attached.to.product` | `:119-122` → `:177-187` |
| U4 | `glAccountId == parentId` | `InvalidParentGLAccountHeadException`, `error.msg.glaccount.id.and.parentid.must.not.same` | `:124-126` |
| U5 | account not found | `GLAccountNotFoundException` | `:128-129` |
| U6 | new `parentId` not found | `GLAccountNotFoundException` | `:135` → `:226-227` |
| U7 | new parent is a DETAIL account | `GLAccountInvalidParentException` | `:135` → `:229-231` |
| U8 | usage changed **and** the account is now a HEADER **and** journal entries exist against it | `GLAccountInvalidUpdateException(TRANSANCTIONS_LOGGED)`, `error.msg.glaccount.glcode.invalid.update.transactions.logged` | `:153-158` |
| U9 | duplicate `gl_code` | as C14 | `:170-173` → `:242-245` |

Order matters and is observable: **U3 and U4 run before the account is even loaded** (`:119-126`
precede `:128`). So `PUT /glaccounts/999999` with `disabled=true` on a non-existent account reports
the *product-mapping* or *same-parent* error, not `GLAccountNotFoundException`. A port that loads
first would return a different error for the same request.

`validateForAttachedProduct` (`:177-187`) has a quirk worth transcribing exactly:

```java
Integer count = this.jdbcTemplate.queryForObject(sql, Integer.class, glAccountId);
if (count == null || count > 0) { throw new GLAccountDisableException(); }
```

`count == null` also throws. `SELECT count(*)` cannot return NULL, so the disjunct is unreachable in
practice, but a port that maps a NULL scan result to "no mappings" would diverge if it ever were.

**U8 has a scope the comment does not describe.** The comment at `:150-152` says *"a detail account
cannot be changed to a header account if transactions are already logged against it"*, but the guard
is `changesOnly.containsKey(USAGE) && glAccount.isHeaderAccount()`. `glAccount.update(command)`
(`GLAccount.java:134-136`) has **already mutated** `this.usage` to the new value by the time
`isHeaderAccount()` is called, so the guard fires whenever the **new** usage is HEADER — including a
header→header no-op that `isChangeInIntegerSansLocaleParameterNamed` would not have recorded (it
would not be in `changesOnly`), and *not* firing on header→detail. Net effect: it blocks
`→ HEADER` when entries exist, which is what was intended; the wording "detail account" is the part
that is wrong, not the logic. Stated here so the porter does not "fix" it in the wrong direction.

#### DELETE (`deleteGLAccount`, `:191-217`)

| # | Condition | Exception / error code | Site |
|---|---|---|---|
| D1 | account not found | `GLAccountNotFoundException` | `:192-193` |
| D2 | account is HEADER **and** `getChildren()` non-empty | `GLAccountInvalidDeleteException(HAS_CHILDREN)`, `error.msg.glaccount.glcode.invalid.delete.has.children` | `:196-198` |
| D3 | any journal entry references it | `…(TRANSACTIONS_LOGGED)`, `error.msg.glaccount.glcode.invalid.delete.transactions.logged` | `:201-205` |
| D4 | any `acc_product_mapping` row references it | `…(PRODUCT_MAPPING)`, `error.msg.glaccount.glcode.invalid.delete.product.mapping` | `:207-211` |

Error codes/messages: `exception/GLAccountInvalidDeleteException.java:35-55`.

**D2 checks `isHeaderAccount()` first.** A **DETAIL** account with children is therefore deletable —
and children are only creatable under a header (C12/U7 refuse a detail parent), so the only route to
that state is: create children under a header, then flip the header to DETAIL. That flip is refused
only if the *new* usage is HEADER (U8), so header→detail is unguarded. The resulting delete leaves
orphan rows whose `parent_id` FK (`FK_ACC_0000000001`, RESTRICT — `0001_initial_schema.xml:7465-7468`)
would actually block the delete at the database. So the *outcome* is a data-integrity error rather
than a domain error. `[UNVERIFIED: not probed against a live database]`

There is **no** refusal for deleting a **disabled** account, and none for an account referenced by
`acc_gl_financial_activity_account` — the FK `FK_office_mapping_acc_gl_account`
(`0001_initial_schema.xml:8486-8489`, RESTRICT) would block it at the database with a generic error
rather than a domain error. §10 D-7.

---

## 3. Enums and their persisted integer values

### 3.1 The rule: the persisted value is `getValue()`, never `ordinal()`

Every enum in this slice carries an explicit `Integer value` supplied in the constructor, and every
persistence site writes that value. **No `ordinal()` call exists anywhere in the four scope paths or
in `AccountingConstants.java`** (grep). For `GLAccountType` and `GLAccountUsage` declaration order
happens to coincide with `getValue()−1`, so `ordinal()` would accidentally work if shifted; for
`FinancialActivity` and `CashAccountsForLoan` it emphatically would not.

### 3.2 `GLAccountType` → `acc_gl_account.classification_enum`

`fineract-core/.../glaccount/domain/GLAccountType.java:25-29`

| Constant | Persisted value | i18n code |
|---|---|---|
| `ASSET` | **1** | `accountType.asset` |
| `LIABILITY` | **2** | `accountType.liability` |
| `EQUITY` | **3** | `accountType.equity` |
| `INCOME` | **4** | `accountType.income` |
| `EXPENSE` | **5** | `accountType.expense` |

`fromInt` maps 1..5 and returns **`null`** for anything else (`GLAccountType.java:88-107`).
`getMinValue()/getMaxValue()` are computed in a static block over `values()` (`:50-64`) and yield
**1 and 5**; they are what `inMinMaxRange` uses at `GLAccountCommand.java:52`.
The column is `SMALLINT NOT NULL` (`0001_initial_schema.xml:70-72`).

### 3.3 `GLAccountUsage` → `acc_gl_account.account_usage`

`fineract-core/.../glaccount/domain/GLAccountUsage.java:27-28`

| Constant | Persisted value |
|---|---|
| `DETAIL` | **1** |
| `HEADER` | **2** |

`fromInt` is a `HashMap` lookup returning `null` on miss (`:67-70`). Range [1,2]
(`:50-65` → `GLAccountCommand.java:55`). Column type `TINYINT` in the changelog with default `2`
(`0001_initial_schema.xml:67-69`) — **PostgreSQL has no `TINYINT`**; Liquibase's Postgres dialect
maps it, but the mapping is in the Liquibase library, not in this repository.
`[UNVERIFIED: the literal PostgreSQL type of `account_usage` — almost certainly `smallint`, but not
readable from the pinned source. Confirm from a live `\d acc_gl_account` before pinning the Go type.]`

### 3.4 `PortfolioProductType` → `acc_product_mapping.product_type` — **`fromInt` disagrees with `getValue()`**

`fineract-core/src/main/java/org/apache/fineract/portfolio/PortfolioProductType.java`

Declared values, `:26-31`:

| Constant | `getValue()` |
|---|---|
| `LOAN` | 1 |
| `SAVING` | 2 |
| `CLIENT` | **5** |
| `PROVISIONING` | **3** |
| `SHARES` | **4** |
| `WORKING_CAPITAL_LOAN` | 6 |

`fromInt`, `:51-59`:

```java
case 1 -> LOAN;  case 2 -> SAVING;  case 3 -> CLIENT;
case 4 -> PROVISIONING;  case 5 -> SHARES;  case 6 -> WORKING_CAPITAL_LOAN;
```

**`fromInt` follows declaration order, not `getValue()`.** Therefore for
`v ∈ {3, 4, 5}`, `PortfolioProductType.fromInt(v).getValue() != v`:

| stored `product_type` | written by | `fromInt` returns | its `getValue()` |
|---|---|---|---|
| 3 | `PROVISIONING` | `CLIENT` | 5 |
| 4 | `SHARES` | `PROVISIONING` | 3 |
| 5 | `CLIENT` | `SHARES` | 4 |

`1, 2, 6` round-trip correctly.

**Every write in this slice uses `getValue()`** — e.g. `ProductToGLAccountMappingHelper.java:80, :140,
:605, :637, :665-666, :698-699`, and every finder is called with `…getValue()`
(`AccountingProcessorHelper.java:1193, :1202, :1220, :1231, :1244, :1260, :1307, :1312, :1324, :1332`).
So **storage and retrieval are self-consistent** and posting is unaffected. The defect only bites a
caller that reads a stored `product_type` back through `fromInt`. Three such callers exist in the
tree (grep `PortfolioProductType.fromInt`):
`fineract-core/.../accounting/common/AccountingEnumerations.java:84`,
`fineract-accounting/.../journalentry/JournalEntryMapper.java:79`, and the declaration itself.
`[UNVERIFIED: whether either caller is ever passed a shares/provisioning/client id — not traced]`

> **Porting instruction.** Encode the persisted `product_type` from the **`getValue()` table above**
> and write an explicit inverse of *that* table. Do **not** transcribe Fineract's `fromInt`. If you
> transcribe it, you inherit an off-by-permutation bug on shares. §10 D-1.

### 3.5 The accounting placeholder enums → `acc_product_mapping.financial_account_type`

The stored integer is **only meaningful together with `product_type` and the product's accounting
rule (cash vs accrual)**. `AccountingConstants.java`:

**`CashAccountsForLoan` (`:37-62`)** — 1 FUND_SOURCE, 2 LOAN_PORTFOLIO, 3 INTEREST_ON_LOANS,
4 INCOME_FROM_FEES, 5 INCOME_FROM_PENALTIES, 6 LOSSES_WRITTEN_OFF, 10 TRANSFERS_SUSPENSE,
11 OVERPAYMENT, 12 INCOME_FROM_RECOVERY, 13 GOODWILL_CREDIT, 14 INCOME_FROM_CHARGE_OFF_INTEREST,
15 INCOME_FROM_CHARGE_OFF_FEES, 16 CHARGE_OFF_EXPENSE, 17 CHARGE_OFF_FRAUD_EXPENSE,
18 INCOME_FROM_CHARGE_OFF_PENALTY, 19 INCOME_FROM_GOODWILL_CREDIT_INTEREST,
20 INCOME_FROM_GOODWILL_CREDIT_FEES, 21 INCOME_FROM_GOODWILL_CREDIT_PENALTY,
**22 CLASSIFICATION_INCOME**, 23 DEFERRED_INCOME_LIABILITY, **24 INCOME_FROM_DISCOUNT_FEE**,
**25 FEES_RECEIVABLE**, **26 PENALTIES_RECEIVABLE**. *(no 7, 8, 9)*

**`AccrualAccountsForLoan` (`:95-122`)** — 1..6 identical, then **7 INTEREST_RECEIVABLE,
8 FEES_RECEIVABLE, 9 PENALTIES_RECEIVABLE**, 10..21 identical to cash, then
**22 INCOME_FROM_CAPITALIZATION**, 23 DEFERRED_INCOME_LIABILITY, **24 BUY_DOWN_EXPENSE**,
**25 INCOME_FROM_BUY_DOWN**. *(no 26)*

**The two enums collide at 22, 24 and 25 with different meanings, and cash uses 25/26 for
receivables that accrual puts at 8/9.**

| value | `CashAccountsForLoan` | `AccrualAccountsForLoan` |
|---|---|---|
| 7 | *(absent)* | `INTEREST_RECEIVABLE` |
| 8 | *(absent)* | `FEES_RECEIVABLE` |
| 9 | *(absent)* | `PENALTIES_RECEIVABLE` |
| **22** | `CLASSIFICATION_INCOME` | `INCOME_FROM_CAPITALIZATION` |
| **24** | `INCOME_FROM_DISCOUNT_FEE` | `BUY_DOWN_EXPENSE` |
| **25** | `FEES_RECEIVABLE` | `INCOME_FROM_BUY_DOWN` |
| **26** | `PENALTIES_RECEIVABLE` | *(absent)* |

So `(product_type=1, financial_account_type=24)` is **not decidable from the row alone**; you must
read the loan product's `accounting_type` to know whether it means "income from discount fee" or
"buy-down expense". A Go schema that models `financial_account_type` as a single enum type is
already wrong. §10 D-2.

Corroborating writes: cash create uses `CashAccountsForLoan.*`
(`ProductToGLAccountMappingWritePlatformServiceImpl.java:80-137`), accrual create uses
`AccrualAccountsForLoan.*` (`:154-235`) — with one deliberate exception, `FUND_SOURCE`, which the
accrual branch writes using `CashAccountsForLoan.FUND_SOURCE.getValue()` (`:154`); both are 1, so it
is harmless, and `AccountingProcessorHelper.java:1196-1198` documents the intent
(*"fund source placeholder ID would be same for both cash and accrual accounts"*).

**`CashAccountsForSavings` (`:267-278`)** — 1 SAVINGS_REFERENCE, 2 SAVINGS_CONTROL,
3 INTEREST_ON_SAVINGS, 4 INCOME_FROM_FEES, 5 INCOME_FROM_PENALTIES, 10 TRANSFERS_SUSPENSE,
11 OVERDRAFT_PORTFOLIO_CONTROL, 12 INCOME_FROM_INTEREST, 13 LOSSES_WRITTEN_OFF, 14 ESCHEAT_LIABILITY.

**`AccrualAccountsForSavings` (`:311-326`)** — the same ten, plus 15 FEES_RECEIVABLE,
16 PENALTIES_RECEIVABLE, 17 INTEREST_PAYABLE, 18 INTEREST_RECEIVABLE. **No collision** for savings.

**`CashAccountsForShares` (`:517-522`)** — 1 SHARES_REFERENCE, 2 SHARES_SUSPENSE,
3 INCOME_FROM_FEES, 4 SHARES_EQUITY.

Note the cross-product collisions on value 1: `FUND_SOURCE` (loan), `SAVINGS_REFERENCE` (savings),
`SHARES_REFERENCE` (shares). The `product_type` column is what disambiguates, which is why every
finder query keys on `(productId, productType, financialAccountType)`.

### 3.6 `FinancialActivity` → `acc_gl_financial_activity_account.financial_activity_type`

`AccountingConstants.java:437-445`

| Constant | Persisted value | code | Required `GLAccountType` |
|---|---|---|---|
| `ASSET_TRANSFER` | **100** | `assetTransfer` | ASSET (1) |
| `CASH_AT_MAINVAULT` | **101** | `cashAtMainVault` | ASSET (1) |
| `CASH_AT_TELLER` | **102** | `cashAtTeller` | ASSET (1) |
| `ASSET_FUND_SOURCE` | **103** | `fundSource` | ASSET (1) |
| `LIABILITY_TRANSFER` | **200** | `liabilityTransfer` | LIABILITY (2) |
| `PAYABLE_DIVIDENDS` | **201** | `payableDividends` | LIABILITY (2) |
| `OPENING_BALANCES_TRANSFER_CONTRA` | **300** | `openingBalancesTransferContra` | EQUITY (3) |

Declaration order in the file is `ASSET_TRANSFER, LIABILITY_TRANSFER, CASH_AT_MAINVAULT,
CASH_AT_TELLER, OPENING_BALANCES_TRANSFER_CONTRA, ASSET_FUND_SOURCE, PAYABLE_DIVIDENDS` — i.e.
**not** value order; `ordinal()` would be wrong here in a way that changes which account is used.
`fromInt` is a `HashMap` on `value` (`:488-498`), so it is correct.

**The 100/200/300 numbering is load-bearing, and it is a convention, not an enforcement.** §4.1
shows that the resolver decides "is this a product placeholder or an organisation-wide financial
activity?" purely by asking whether `FinancialActivity.fromInt(id)` is non-null
(`AccountingProcessorHelper.java:1340-1342`). That works only because the product placeholder values
(1..26) are disjoint from {100,101,102,103,200,201,300}. **Nothing in the source enforces the
disjointness.** Adding a 27th loan placeholder is safe; adding a 100th is a silent takeover of
`ASSET_TRANSFER`. §10 D-3 — a port should assert the disjointness at construction.

---

## 4. THE MAPPING RESOLUTION ORDER — which single GL account is selected

This is the highest-value output. The code lives in
`fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccountingProcessorHelper.java`
(A1's file). Traced in full below.

### 4.1 The algorithm, for a *product* account (no charge involved)

`getLinkedGLAccountForLoanProduct`, `AccountingProcessorHelper.java:1185-1216`:

```
resolve(productId, accountMappingTypeId, paymentTypeId):

  STEP 0 — ORGANISATION OVERRIDE
    if FinancialActivity.fromInt(accountMappingTypeId) != null:            [:1187, :1340-1342]
        faa = financialActivityAccountRepository
                .findByFinancialActivityTypeWithNotFoundDetection(accountMappingTypeId)   [:1188-1189]
        return faa.getGlAccount()                                           [:1190]
        # MISS: FinancialActivityAccountNotFoundException
        #       (FinancialActivityAccountRepositoryWrapper.java:45-51)
        # NOTE: productId and paymentTypeId are IGNORED on this branch.

  STEP 1 — CORE (product-wide) MAPPING
    m = findCoreProductToFinAccountMapping(productId, productType, accountMappingTypeId)   [:1192-1193]
        # SQL predicate, ProductToGLAccountMappingRepository.java:38-40 :
        #   productId = ? AND productType = ? AND financialAccountType = ?
        #   AND paymentType IS NULL AND charge IS NULL
        #   AND chargeOffReason IS NULL AND writeOffReason IS NULL
        #   AND capitalizedIncomeClassification IS NULL AND buydownFeeClassification IS NULL

  STEP 2 — PAYMENT-CHANNEL OVERRIDE (narrow, gated on the placeholder id)
    if accountMappingTypeId == CashAccountsForLoan.FUND_SOURCE.getValue()   # == 1   [:1199]
        p = findByProductIdAndProductTypeAndFinancialAccountTypeAndPaymentTypeId(
                 productId, productType, accountMappingTypeId, paymentTypeId)        [:1200-1202]
        if p != null: m = p                                                          [:1203-1205]

  STEP 3 — MISS
    if m == null: throw ProductToGLAccountMappingNotFoundException(...)      [:1208-1211]
    return m.getGlAccount()                                                 [:1213]
```

**In one sentence:** *financial activity wins outright if the placeholder id is a financial-activity
id; otherwise the product-wide row is fetched and then, only for the fund-source/reference
placeholder, a payment-type-specific row replaces it if one exists; a missing product-wide row is
an error for loans and a NullPointerException everywhere else.*

### 4.2 The same algorithm across the four product families

| Family | Method | STEP 0 present? | STEP 2 gate | On STEP 3 miss |
|---|---|---|---|---|
| **Loan** | `getLinkedGLAccountForLoanProduct` `:1185-1216` | **yes** `:1187` | `accountMappingTypeId == CashAccountsForLoan.FUND_SOURCE` (1) `:1199` — **no null-check on `paymentTypeId`** | `ProductToGLAccountMappingNotFoundException` `:1208-1211` |
| **Working-capital loan** | `getLinkedGLAccountForWorkingCapitalLoanProduct` `:1010-1029` | **no** | `…== FUND_SOURCE (1) && paymentTypeId != null` `:1015` | `ProductToGLAccountMappingNotFoundException` `:1024-1027` |
| **Savings** | `getLinkedGLAccountForSavingsProduct` `:1271-1296` | **yes** `:1274` | `…== CashAccountsForSavings.SAVINGS_REFERENCE` (1) `:1285` | **no check — `accountMapping.getGlAccount()` on null → NPE** `:1293` |
| **Shares** | `getLinkedGLAccountForShareProduct` `:1298-1320` | **yes** `:1301` | `…== CashAccountsForShares.SHARES_REFERENCE` (1) `:1309` | **no check → NPE** `:1317` |

Two divergences that matter for a port and for refusal vectors:

- **Only the loan and working-capital-loan paths raise a typed miss.** Savings and shares
  dereference `accountMapping` unconditionally. A missing mapping there surfaces as HTTP 500 /
  `NullPointerException`, not a `error.msg.productToAccountMapping.not.found`.
- **The working-capital-loan path has no STEP 0** — it never consults financial activity accounts,
  and it additionally requires `paymentTypeId != null` before attempting the payment-channel lookup
  (which the loan path does not; `findBy…PaymentTypeId(…, null)` is issued with a null argument and
  simply matches nothing).

### 4.3 CHARGE resolution — a different and *inconsistent* algorithm per family

| Family | Method | Order |
|---|---|---|
| **Loan** | `getLinkedGLAccountForLoanCharges` `:1218-1238` | core mapping `:1219-1220`; then **if `chargeId != null`** a charge-specific row for **any** `accountMappingTypeId` replaces it `:1229-1236`; **no null check before `getGlAccount()`** `:1237` |
| **Savings** | `getLinkedGLAccountForSavingsCharges` `:1240-1269` | core mapping `:1243-1244`; then **if** `accountMappingTypeId ∈ {CashAccountsForSavings.INCOME_FROM_FEES (4), CashAccountsForLoan.INCOME_FROM_PENALTIES (5)}` `:1253-1254`: **first** `charge.getAccount()` — the GL account carried by the `m_charge` row itself — and if non-null **return it immediately, outranking every mapping** `:1255-1258`; otherwise a charge-specific mapping row `:1259-1265`. **no null check** `:1268` |
| **Shares** | `getLinkedGLAccountForShareCharges` `:1322-1338` | core mapping `:1323-1324`; then a charge-specific row **unconditionally**, no `chargeId != null` guard `:1331-1336`; **no null check** `:1337` |

**The savings path has a precedence level the other two do not have**: the charge entity's own GL
account (`m_charge.income_or_liability_account_id`, read via
`chargeRepositoryWrapper.findOneWithNotFoundDetection(chargeId).getAccount()` at `:1255`) beats the
product mapping. Neither the loan nor the shares path consults it. So the same conceptual question —
"which income account does this fee credit?" — is answered by **three different precedence chains**
depending on the product family. Any port that unifies them changes behaviour.

Note also `:1253-1254` mixes enum families in one condition: `CashAccountsForSavings.INCOME_FROM_FEES`
(4) OR `CashAccountsForLoan.INCOME_FROM_PENALTIES` (5). Since `CashAccountsForSavings.INCOME_FROM_PENALTIES`
is also 5, the condition is numerically `id ∈ {4,5}` and is correct by coincidence of the values; the
in-source comment at `:1251` (*"Vishwas TODO: remove this condition as it should always be true"*)
shows the author did not intend it to be selective.

### 4.4 The reason / classification finders — a *fifth* lookup shape

For charge-off, write-off and the two classification dimensions the lookup does **not** go through
the core mapping at all. `AccountingProcessorHelper.java:194-208`:

```java
return accountMappingRepository.findChargeOffReasonMapping(loanProductId, productType.getValue(), chargeOffReasonId);   // :194
return accountMappingRepository.findWriteOffReasonMapping(loanProductId, productType.getValue(), writeOffReasonId);     // :199
return accountMappingRepository.findBuydownFeeClassificationMapping(loanProductId, productType.getValue(), classificationId);      // :205
return accountMappingRepository.findCapitalizedIncomeClassificationMapping(loanProductId, productType.getValue(), classificationId); // :207
```

Queries at `ProductToGLAccountMappingRepository.java:76-78, :109-111, :101-103, :105-107`. Each keys
on `(productId, productType, <the reason/classification code value id>)` and — critically —
**does not filter on `financialAccountType` at all**. These return the `ProductToGLAccountMapping`
itself (not a `GLAccount`), and return `null` on miss with no exception; the null-handling is the
caller's, outside this slice. `[UNVERIFIED: what the callers of these four do with null — not traced]`

### 4.5 What is **never** consulted during resolution

Established by reading the four methods end to end. Resolution ignores:

- **`GLAccount.disabled`** — a disabled account still receives postings if a mapping points at it.
  (The only protection is U3, which refuses *disabling* a mapped account in the first place.)
- **`GLAccount.usage`** — a HEADER account can be a posting target if mapped (§2.4).
- **`GLAccount.manualEntriesAllowed`** — not read on this path.
- **`GLAccount.hierarchy` / `parent`** — there is **no roll-up, no fallback to a parent account, and
  no inheritance of any kind**. The tree is presentation and referential structure only.
- **the office** — `acc_gl_financial_activity_account` has no office column
  (`0001_initial_schema.xml:98-110`), despite its FK being named `FK_office_mapping_acc_gl_account`.
  Financial activity mappings are **tenant-global**.
- **`fund`** — the brief asks about a fund dimension; **`acc_product_mapping` has no fund column**
  (full column list in §5.1) and no finder mentions a fund. **There is no fund dimension in
  product-to-account mapping in this Fineract revision.** The only "fund source" concept is the
  `FUND_SOURCE`/`ASSET_FUND_SOURCE` *placeholder*, which is an account role, not a fund entity.

### 4.6 The exception message on a loan miss can itself throw

`AccountingProcessorHelper.java:1208-1211`:

```java
throw new ProductToGLAccountMappingNotFoundException(PortfolioProductType.LOAN, loanProductId,
        AccrualAccountsForLoan.fromInt(accountMappingTypeId).toString());
```

The message is always rendered through **`AccrualAccountsForLoan`**, even for a cash-based product.
`AccrualAccountsForLoan.fromInt` returns `null` for **26** (`CashAccountsForLoan.PENALTIES_RECEIVABLE`
exists at 26; accrual has no 26 — §3.5), so `.toString()` on the result is an NPE and the caller sees
a NullPointerException instead of the intended not-found error. Same shape at `:1026`, which uses
`CashAccountsForLoan.fromInt` and would NPE for accrual-only ids 7, 8, 9.
`[UNVERIFIED: reachability — requires a cash product with a missing mapping for placeholder 26. Not probed.]`
This is a good candidate for a refusal vector precisely because it is the *error* path.

### 4.7 Summary answer, for the A1 porter

> **Resolution is a two-key lookup with one conditional override and one pre-emptive branch.**
> First, if the placeholder id is one of the seven `FinancialActivity` values (100, 101, 102, 103,
> 200, 201, 300) the account comes from `acc_gl_financial_activity_account` keyed on
> `financial_activity_type` alone — tenant-global, product-independent, and a miss is
> `FinancialActivityAccountNotFoundException`. Otherwise the base row is the *core* row in
> `acc_product_mapping` matching `(product_id, product_type, financial_account_type)` with **all
> six** discriminator columns (`payment_type`, `charge_id`, `charge_off_reason_id`,
> `write_off_reason_id`, `capitalized_income_classification_id`, `buydown_fee_classification_id`)
> NULL. That base row is then replaced — only when the placeholder is the family's fund-source /
> reference placeholder, whose value is 1 in all three families — by the row additionally matching
> `payment_type`, if such a row exists; a non-existent payment-specific row silently leaves the base
> row in place. Charges are a separate entry point with a *different* precedence per family: loans
> override the base row with a `charge_id`-matching row for any placeholder; shares do the same
> unconditionally; savings first return the GL account hung off the `m_charge` row itself and only
> then look for a `charge_id`-matching row, and only for placeholders 4 and 5. Charge-off reasons,
> write-off reasons and the two capitalized-income / buy-down classifications do not use the base row
> at all — they are direct `(product_id, product_type, <code_value_id>)` lookups that ignore
> `financial_account_type` and return NULL on miss. On a miss of the base row, loans and
> working-capital loans raise `ProductToGLAccountMappingNotFoundException`
> (`error.msg.productToAccountMapping.not.found`) while savings, shares and all three charge paths
> dereference null and raise a NullPointerException. Nothing in resolution reads `disabled`,
> `usage`, `manual_journal_entries_allowed`, the account tree, the office, or any fund — there is no
> fallback to a parent account and no fund dimension in this schema at all.

---

## 5. The mapping table, its constraints, and how rows are written

### 5.1 `acc_product_mapping`

Entity `fineract-accounting/.../producttoaccountmapping/domain/ProductToGLAccountMapping.java:42-81`.

| Column | Java | DDL type / nullability | DDL site |
|---|---|---|---|
| `id` | inherited | `BIGINT` autoIncrement, PK | `0001_initial_schema.xml:179-181` |
| `gl_account_id` | `@ManyToOne(optional=true) GLAccount` `:46-48` | `BIGINT` nullable | `:182` |
| `product_id` | `Long` `:50-51` | `BIGINT` nullable | `:183` |
| `product_type` | `int` `:61-62` | `SMALLINT` nullable | `:184` |
| `financial_account_type` | `int` `:64-65` | `SMALLINT` nullable | `:187` |
| `payment_type` | `@ManyToOne PaymentType` `:53-55` | `INT` nullable | `:185` |
| `charge_id` | `@ManyToOne Charge` `:57-59` | `BIGINT` nullable | `:186` |
| `charge_off_reason_id` | `@ManyToOne CodeValue` `:67-69` | `INT` nullable | `0153_add_charge_off_reason_id_to_acc_product_mapping.xml:28` |
| `write_off_reason_id` | `@ManyToOne CodeValue` `:71-73` | `BIGINT` nullable, **no FK** | `0199_write_off_reason_mapping_loan.xml:28` |
| `capitalized_income_classification_id` | `@ManyToOne CodeValue` `:75-77` | `INT` nullable | `0198_add_classification_id_to_acc_product_mapping.xml:28` |
| `buydown_fee_classification_id` | `@ManyToOne CodeValue` `:79-81` | `INT` nullable | `0198_…xml:41` |

Note the width inconsistency: three of the four `m_code_value` references are `INT` while
`write_off_reason_id` is `BIGINT`, and `m_code_value.id` is `BIGINT`.

Indexes: `charge_id`, `payment_type` (`0001_initial_schema.xml:5693-5695, :5698-5700`), `product_id`
(`0160_add_acc_product_mapping_product_id_index.xml:28-30`). **No index on `gl_account_id`**, even
though a FK was added to it late (`0175_add_fk_acc_product_mapping.xml:26-29`) and `validateForAttachedProduct`
(§2.6 U3) scans on exactly that column.

### 5.2 The `financial_action` unique constraint **does not exist in the database** — REFUTED

`ProductToGLAccountMapping.java:42-43` declares:

```java
@Table(name = "acc_product_mapping", uniqueConstraints = { @UniqueConstraint(columnNames = { "product_id", "product_type",
        "financial_account_type", "payment_type" }, name = "financial_action") })
```

`grep -rn "financial_action" fineract-provider/src/main/resources/db/` returns **zero hits** (run by
this worker). There is no `addUniqueConstraint`, no inline `unique="true"`, and no raw `ALTER TABLE`
against `acc_product_mapping` anywhere in the changelog. Fineract's schema is Liquibase-owned, not
`hbm2ddl`-generated, so **this uniqueness is unenforced on a real PostgreSQL instance**.

Two consequences:

1. **Duplicate mapping rows are physically possible**, and the finders return a single result
   (`ProductToGLAccountMappingRepository.java:30-40` return `ProductToGLAccountMapping`, not a list),
   so a duplicate would raise a non-unique-result error at query time rather than at insert time.
2. Even if the constraint existed, `payment_type` is nullable, and PostgreSQL's NULL semantics mean
   two rows with `payment_type IS NULL` would not collide — so it could never have deduplicated the
   *core* rows, which are exactly the rows where uniqueness matters most.

§10 D-4. A port that adds this unique index changes behaviour under a data set the oracle accepts;
a port that omits it inherits the ambiguity. **This is a design decision the A2 porter must record,
not inherit silently.**

### 5.3 Write paths and their validations

`fineract-accounting/.../producttoaccountmapping/service/ProductToGLAccountMappingHelper.java`

| Operation | Site | Type check applied to the GL account |
|---|---|---|
| create a core mapping | `saveProductToAccountMapping` `:73-83` | `getAccountByIdAndType(paramName, expectedAccountType, accountId)` `:77` → must equal the single expected `GLAccountType`, else `ProductToGLAccountMappingInvalidException` (`:727-736`) |
| update a core mapping, failing if absent | `mergeProductToAccountMappingChanges` `:85-125` | same; **absent** → `ProductToGLAccountMappingNotFoundException` `:114`, **unless** the param is on the 14-entry optional allow-list `:95-109`, in which case the mapping is created instead `:112` |
| update-or-create | `createOrmergeProductToAccountMappingChanges` `:127-149` | same; absent → create `:136-141` |
| payment-channel row | `savePaymentChannelToFundSourceMapping` `:599-608` | **`getAccountById` — no type check at all** `:603`. Payment type must exist (`PaymentTypeNotFoundException` `:601-602`). `financial_account_type` is hard-wired to `CashAccountsForLoan.FUND_SOURCE.getValue()` = **1** for *every* product family `:605` |
| charge row | `saveChargeToFundSourceMapping` `:614-640` | penalty → must be `INCOME` `:627-628`; fee → must be `INCOME` **or** `LIABILITY` `:631-633` (`getAllowedAccountTypesForFeeMapping` `:711-716`). `financial_account_type` set to `INCOME_FROM_PENALTIES` (5) or `INCOME_FROM_FEES` (4) `:629, :634`. Charge must exist `:616`. **The charge's own fee/penalty flag is not checked against `isPenalty`** — see the in-source TODO at `:618-619` |
| charge-off / write-off reason row | `saveReasonToExpenseMapping` `:652-676` | **no type check**; silently does nothing if the GL account or the code value is absent `:663`; idempotent — skips if a matching reason row already exists `:658-661` |
| classification row | `saveClassificationToIncomeMapping` `:678-709` | **no type check**; same silent-skip semantics `:696`. `financial_account_type` hard-wired to `CashAccountsForLoan.CLASSIFICATION_INCOME.getValue()` = **22** for *both* the capitalized-income and buy-down classifications `:699` — the two are distinguished only by which nullable code-value column is populated `:701-705` |
| delete one core mapping | `deleteProductToGLAccountMapping(id, type, accountTypeId)` `:757-764` | deletes only if the row exists **and** its `glAccount` is non-null `:761` |
| delete all for a product | `deleteProductToGLAccountMapping(id, type)` `:766-772` | unconditional bulk delete |

**Three of the seven write paths do no GL-account-type validation at all**, and two of those fail
*silently* (no exception, no row, HTTP 200) when the referenced account or code value does not exist.
Those silent no-ops are excellent negative vectors: the API reports success and the mapping is absent,
which then surfaces as an NPE or a not-found at posting time, far from the cause. §10 D-5.

The bulk-update methods (`updateChargeToIncomeAccountMappings` `:297-378`,
`updatePaymentChannelToFundSourceMappings` `:386-451`, `updateReasonToGLAccountMappings` `:466-524`,
`updateClassificationToGLAccountMappings` `:526-593`) all share one semantic worth pinning:
**an empty input array deletes every existing mapping of that kind** (`:336-337`, `:416-417`,
`:492-493`, `:557-558`), whereas an **absent** array is a no-op (the whole body is inside
`if (…Array != null)`). Absent ≠ empty is a contract-visible distinction.

### 5.4 Product-family entry points

`fineract-provider/.../productaccountmapping/service/ProductToGLAccountMappingWritePlatformServiceImpl.java`

- `createLoanProductToGLAccountMapping` `:61-248` — switch on `AccountingRuleType`; `NONE` writes
  nothing `:75-76`; `CASH_BASED` `:77-148`; `ACCRUAL_UPFRONT` falls through to `ACCRUAL_PERIODIC`
  `:149-246`. The `BUY_DOWN_EXPENSE` mapping is written only when `merchantBuyDownFee` is true
  `:224-228` (default true, `:65`, overridden by `LoanProductConstants.MERCHANT_BUY_DOWN_FEE_PARAM_NAME`
  `:66-72`).
- `createSavingProductToGLAccountMapping` `:311-349` — `ACCRUAL_UPFRONT` is **not** handled (falls to
  `default: break` `:345-346`), so an upfront-accrual savings product gets **no mappings at all**.
- `createShareProductToGLAccountMapping` `:353-393` — only `CASH_BASED` is handled.
- On an accounting-rule change, all three update methods **delete every mapping and recreate**
  (`:410-415`, `:449-454`, `:481-485`), rather than migrating. Any payment-channel or charge mapping
  is destroyed and only recreated from what is in the same request.

**A defect in the share create path.** `:386-387`:

```java
this.savingsProductToGLAccountMappingHelper.savePaymentChannelToFundSourceMappings(command, element, shareProductId, null);
this.savingsProductToGLAccountMappingHelper.saveChargesToIncomeAccountMappings(command, element, shareProductId, null);
```

It uses the **savings** helper, whose methods hard-wire `PortfolioProductType.SAVING`
(`SavingsProductToGLAccountMappingHelper.java:113, :124-125`). So a share product's payment-channel
and charge mappings are stored with `product_type = 2` (SAVING) and `product_id =` the *share*
product id. Resolution then looks for them with `PortfolioProductType.SHARES.getValue()` = 4
(`AccountingProcessorHelper.java:1312, :1332`) and never finds them. The **update** path uses the
correct helper (`ProductToGLAccountMappingWritePlatformServiceImpl.java:490-491` →
`ShareProductToGLAccountMappingHelper.java:106, :116-117`, both `PortfolioProductType.SHARES`), so
create and update write to **two different product_type values for the same logical mapping**.
Additionally, the mis-filed rows collide in the savings namespace with a savings product that happens
to share the id.
`[UNVERIFIED: not observed at runtime; established from the three cited files only. Worth a capture —
it would be visible as a share charge mapping that survives a create but vanishes from the read model.]`
§10 D-8.

---

## 6. Financial activity accounts

### 6.1 Table and entity

`fineract-accounting/.../financialactivityaccount/domain/FinancialActivityAccount.java:34-46`

| Column | Java | DDL |
|---|---|---|
| `id` | inherited | `BIGINT` autoIncrement PK — `0001_initial_schema.xml:100-102` |
| `gl_account_id` | `@ManyToOne(EAGER) GLAccount` `:41-43` | `BIGINT` **NOT NULL, DEFAULT 0** — `:103-105` |
| `financial_activity_type` | `Integer`, `nullable=false` `:45-46` | `SMALLINT` **NOT NULL, UNIQUE (inline, unnamed)** — `:106-108` |

The unique constraint is **single-column on `financial_activity_type`** — so there is exactly one GL
account per financial activity, tenant-wide, with no office dimension. FK
`FK_office_mapping_acc_gl_account` on `gl_account_id` → `acc_gl_account(id)` RESTRICT
(`0001_initial_schema.xml:8486-8489`); index of the same name (`:6332-6334`). The `office` in that
name is legacy: there is no office column.

`gl_account_id` being `NOT NULL DEFAULT 0` is a latent trap — `0` is not a valid account id, so any
insert relying on the default violates the FK.

### 6.2 Lookup

`FinancialActivityAccountRepository.java:29-30`:

```java
@Query("select faa from FinancialActivityAccount faa where faa.financialActivityType = :financialActivityType")
FinancialActivityAccount findByFinancialActivityType(@Param("financialActivityType") int financialAccountType);
```

Wrapped at `FinancialActivityAccountRepositoryWrapper.java:45-51`, throwing
`FinancialActivityAccountNotFoundException(financialActivityType)` —
`error.msg.financialActivityAccount.not.found` — when null
(`exception/FinancialActivityAccountNotFoundException.java:40-43`).

The query returns a **single** entity, so if the DB uniqueness were ever absent a second row would
raise a non-unique-result error. Uniqueness is enforced **only** by the DDL constraint; the write
service does **no** pre-check for duplicates and instead catches the integrity violation
(`FinancialActivityAccountWritePlatformServiceImpl.java:142-153`) and re-maps it to
`DuplicateFinancialActivityAccountFoundException` (`error.msg.financialActivityAccount.exists`) **by
substring-matching `financial_activity_type` in the driver's message** (`:144`). The DDL constraint
is unnamed, so PostgreSQL auto-names the index; whether its message contains that literal substring
is `[UNVERIFIED — same capture as C14 in §2.6]`.

### 6.3 Validations

`financialactivityaccount/serialization/FinancialActivityAccountDataValidator.java`

**CREATE** (`:53-72`):

| # | Condition | Result |
|---|---|---|
| F1 | blank JSON | `InvalidJsonException` `:104-106` |
| F2 | any key other than `financialActivityId`, `glAccountId` | unsupported-parameter error `:108-109`; the two keys at `api/FinancialActivityAccountsJsonInputParams.java:29-30` |
| F3 | `financialActivityId` null, or not one of **{100, 200, 101, 102, 300, 103, 201}** | validation error `:62-66` |
| F4 | `glAccountId` null or ≤ 0 | validation error `:69` |
| F5 | GL account not found | `GLAccountNotFoundException` (`…WritePlatformServiceImpl.java:62`) |
| F6 | GL account's `classification_enum` ≠ the activity's `getMappedGLAccountType().getValue()` | `FinancialActivityAccountInvalidException`, `error.msg.financialActivityAccount.invalid` — `…WritePlatformServiceImpl.java:84-90`; exception at `exception/FinancialActivityAccountInvalidException.java:32-40` |
| F7 | a row already exists for that activity type | `DuplicateFinancialActivityAccountFoundException` `…WritePlatformServiceImpl.java:144-147` |

**UPDATE** (`:78-101`) — **and here is a genuine asymmetry:**

```java
// create, :62-66 — SEVEN values
.isOneOfTheseValues(ASSET_TRANSFER, LIABILITY_TRANSFER, CASH_AT_MAINVAULT, CASH_AT_TELLER,
                    OPENING_BALANCES_TRANSFER_CONTRA, ASSET_FUND_SOURCE, PAYABLE_DIVIDENDS)

// update, :89-92 — FIVE values
.isOneOfTheseValues(ASSET_TRANSFER, LIABILITY_TRANSFER,
                    OPENING_BALANCES_TRANSFER_CONTRA, ASSET_FUND_SOURCE, PAYABLE_DIVIDENDS)
```

**`CASH_AT_MAINVAULT` (101) and `CASH_AT_TELLER` (102) are creatable but not settable on update.**
An existing mapping for either can have its GL account changed (that goes through the `glAccountId`
branch `:95-98`), but its `financialActivityId` can never be *set to* 101 or 102. Both halves of the
list were read; this is not a transcription slip. It is a clean refusal vector: `PUT` with
`financialActivityId: 101` → validation error; `POST` with the same value → success.

Type validation on update runs only when something changed (`…WritePlatformServiceImpl.java:112-115`),
and it validates the **post-mutation** state, so changing either the account or the activity type
re-checks the pairing.

**DELETE** (`…WritePlatformServiceImpl.java:131-140`) has **no validation whatsoever** — no check for
in-use, no check for pending transfers. Deleting the `ASSET_TRANSFER` mapping is accepted, and the
next inter-office transfer fails at posting time with
`FinancialActivityAccountNotFoundException`. Contrast D4 in §2.6, where deleting a GL account *is*
guarded against product mappings. §10 D-7.

---

## 7. Debit / credit sign convention

**This slice does not fix a debit/credit sign convention, and A1 must not take one from it.**

Neither `acc_gl_account`, nor `acc_product_mapping`, nor `acc_gl_financial_activity_account` carries
a sign, a normal-balance flag, or a debit/credit indicator. `GLAccountType` (§3.2) records
ASSET/LIABILITY/EQUITY/INCOME/EXPENSE and **nothing in the four scope paths derives a normal balance
from it**. Grep of the scope paths for `debit`/`credit` finds hits only in the trial-balance job
described below and in Swagger example strings.

The **one** place this slice *consumes* a sign convention is the trial-balance tasklet, and it
consumes one fixed elsewhere. `fineract-accounting/.../glaccount/domain/JournalEntryRepository`?
— no; the query lives in
`fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/domain/JournalEntryRepository.java:52-66`:

```java
SELECT je.office.id, je.glAccount.id,
       SUM(CASE WHEN je.type = 1 THEN -1 * je.amount ELSE je.amount END),   // :55-58
       je.transactionDate, je.createdDate, SUM(je.amount)                    // :59-61
```

and `JournalEntryType` (`fineract-accounting/.../journalentry/domain/JournalEntryType.java:23-24`) is
`CREDIT(1)`, `DEBIT(2)`. So:

> **For the trial balance only: `je.amount` is stored unsigned with a separate type discriminator,
> and the signed movement is `+amount` for a DEBIT (type 2) and `−amount` for a CREDIT (type 1).**
> `UpdateTrialBalanceDetailsTasklet.java:119-127` then accumulates `closingBalance += amount` over
> rows ordered by `created_date, entry_date` (`TrialBalanceRepository.java:31-32`).
> Cited from A1's files; **A2 does not define this and A1 must re-derive it from
> `JournalEntry`/`JournalEntryType` directly, not from this document.**

---

## 8. `BigDecimal` inventory and persisted scale

Exhaustive grep of the four scope paths for `BigDecimal|double |float |Double|Float`.
**Every hit is in the trial-balance code; there are ZERO `BigDecimal` fields and zero floating-point
types in `producttoaccountmapping`, `financialactivityaccount` or `productaccountmapping`.**

| Site | Field / use | Persisted as |
|---|---|---|
| `glaccount/domain/TrialBalance.java:49-50` | `@Column(name="amount", nullable=false) BigDecimal amount` — **no `precision`/`scale` on the annotation** | `m_trial_balance.amount` = **`DECIMAL(19, 6)` NOT NULL** — `0001_initial_schema.xml:4669-4671` |
| `glaccount/domain/TrialBalance.java:58-59` | `@Column(name="closing_balance", nullable=false) BigDecimal closingBalance` — no precision/scale | `m_trial_balance.closing_balance` = **`DECIMAL(19, 6)` NOT NULL** — `0001_initial_schema.xml:4676-4678` |
| `glaccount/domain/TrialBalanceRepository.java:45` | `List<BigDecimal> findLastClosingBalance(…)` | (projection of the above) |
| `glaccount/jobs/…/UpdateTrialBalanceDetailsTasklet.java:78, :81` | casts JPQL result columns to `BigDecimal` | as above |
| `…Tasklet.java:108, :114-117, :119-127` | running accumulation, seeded `BigDecimal.ZERO` `:116`, `closingBalance.add(row.getAmount())` `:124` | as above |

**No `java.lang.Double`, `java.lang.Float`, `double` or `float` occurs anywhere in the four scope
paths.** `TrialBalance.equals/hashCode` (`:67-81`) use `Objects.equals` on the `BigDecimal`s — which
is `BigDecimal.equals`, i.e. **scale-sensitive**: `1.00` and `1.000000` are unequal. A Go port using
integer minor units removes that hazard entirely, but any comparison against a captured Fineract
value must normalise scale first.

Two facts for the porter:

1. **`DECIMAL(19, 6)` is this schema's house style for amounts** — the same on
   `acc_gl_journal_entry.amount`, `office_running_balance`, `organization_running_balance`
   (`0001_initial_schema.xml:145, :168, :171`). Under the ratified MNT minor unit of 2, six stored
   decimals means Fineract can hold sub-minor-unit residue in a balance column. Any parity vector
   comparing a Go integer-minor-unit balance to a Fineract `DECIMAL(19,6)` must state the truncation
   rule it applies. That rule is **not** specified anywhere in this slice.
2. **`m_trial_balance.closing_balance` is a WRITTEN, STORED balance**, computed by a batch job and
   `UPDATE`d in place (`UpdateTrialBalanceDetailsTasklet.java:126` sets it on a managed entity inside
   a transactional tasklet). This is in direct tension with the project non-negotiable *"balances are
   derived, never written"*. It is a **reporting cache**, not the ledger — the ledger itself is
   `acc_gl_journal_entry`, which A1 owns. The A2 porter must not carry `m_trial_balance` across as a
   balance store; it should be a derived view or be dropped. §10 D-9, and it is a design decision,
   not a transcription.

---

## 9. Additional refusal / error surface worth vectoring

Beyond §2.6, §5.3 and §6.3:

| Behaviour | Site | Why it matters |
|---|---|---|
| `GLAccountInvalidUsageException` is **dead code** — constructed nowhere in the tree | `exception/GLAccountInvalidUsageException.java:26-30`; grep for the class name across all non-`build/` `*.java` returns only its own file and one import-free hit in the read service's *sibling* class | Do not port it as a live refusal |
| The two exceptions' **error codes are swapped relative to their class names** | `GLAccountInvalidUsageException.java:29` emits `error.msg.glaccount.classification.invalid`; `GLAccountInvalidClassificationException.java:29` emits `error.msg.glaccount.usage.invalid` | A port that "fixes" the naming changes the wire contract |
| An invalid `usage` query param throws `GLAccountInvalidClassificationException(accountClassification)` — passing the **classification**, which may be `null` | `GLAccountReadPlatformServiceImpl.java:120-122` | The error message reports the wrong (possibly null) value |
| `GET /glaccounts?searchParam=…` builds **syntactically invalid SQL** | `GLAccountReadPlatformServiceImpl.java:154`: `sql += " ( name like %?% or gl_code like %?% )"` — `%?%` is not valid SQL and the placeholders would not bind | Any non-blank `searchParam` should fail. `[UNVERIFIED: not executed against a live database this fire — high-value cheap capture]` |
| `rs.wasNull()` is evaluated **after** reading a different column | `GLAccountReadPlatformServiceImpl.java:98-99`: `nameDecorated` is read at `:98`, then `codeId` nulling is decided by `rs.wasNull()` at `:99` | `tagId` may be reported as `0` instead of null, or vice versa. `[UNVERIFIED: not probed]` |
| `retrieveAllGLAccounts` interpolates `manualTransactionsAllowed` and `disabled` **directly into the SQL string** rather than binding | `:177`, `:185` | Both are `Boolean`, so not injectable, but the emitted literal is Java's `true`/`false` — PostgreSQL-compatible; noted for the porter |

---

## 10. Design decisions this slice forces on the port

Not defects in the port — decisions the A2 porter must **record**, because inheriting silently is how
a wrong one survives.

| # | Decision | Recommendation |
|---|---|---|
| D-1 | `PortfolioProductType.fromInt` permutes 3/4/5 vs `getValue()` (§3.4) | Encode `getValue()` and its true inverse. Add a compile-time or init-time assertion that the map is a bijection. Do not transcribe `fromInt`. |
| D-2 | `financial_account_type` means different things under cash vs accrual for loan values 7, 8, 9, 22, 24, 25, 26 (§3.5) | Model it as `(accountingRule, placeholderId)` in Go, never a bare int enum. Vectors must cover a cash and an accrual product at value 22, 24 and 25. |
| D-3 | The `FinancialActivity`-vs-placeholder disjointness (§3.6) is a convention, unenforced | Assert disjointness at construction; a collision would silently reroute a posting. |
| D-4 | The `financial_action` unique constraint exists in JPA only, never in the DDL (§5.2) | Decide explicitly whether the Go schema enforces it. If yes, note that it is a **behaviour change vs the oracle** and that shadow-parity may diverge on data the oracle accepts. |
| D-5 | Three write paths do no type check; two fail silently on a missing account or code value (§5.3) | Reproduce the oracle for parity; log a warning. Do **not** convert a silent no-op into an error without a recorded decision — it changes HTTP status codes. |
| D-6 | Re-parenting does not cascade `hierarchy` to descendants (§2.2) | `hierarchy` drives only display indentation, so a correct cascade is safe and strictly better. Record it as an intentional divergence and vector `nameDecorated`. |
| D-7 | Deleting a financial activity account has no in-use guard (§6.3); deleting a GL account has no financial-activity guard (§2.6 D4) | Same call as D-5: reproduce for parity, or guard and record the divergence. |
| D-8 | Share product create writes advanced mappings under `product_type = SAVING`; update writes them under `SHARES` (§5.4) | Reproducing this faithfully means reproducing a data-corrupting bug. Shares are Tier B; park it with a written decision rather than porting the inconsistency. |
| D-9 | `m_trial_balance.closing_balance` is a written, stored balance at `DECIMAL(19,6)` (§8) | Do not port as a balance store. Derive it, or drop the table and compute the trial balance from the ledger. Recording this is required by the project non-negotiable on derived balances. |
| D-10 | No default chart of accounts ships with Fineract | See §12 backlog B-5 — a Mongolian FRC-aligned COA is a product decision, not a port. |

---

## 11. `[UNVERIFIED]` — what this worker could not establish

Each of these is a *gap*, not a guess. None was papered over.

1. **The PostgreSQL type of `acc_gl_account.account_usage`.** Declared `TINYINT`
   (`0001_initial_schema.xml:67`), which PostgreSQL does not have. The mapping lives in the Liquibase
   library, not in this repository. Resolve from a live `\d acc_gl_account`.
2. **The literal names of the auto-generated PostgreSQL constraints** for the `acc_gl_account.gl_code`
   and `acc_gl_financial_activity_account.financial_activity_type` unique indexes and for the three
   primary keys — the changelog supplies no names.
3. **Which error code a duplicate `glCode` actually produces** (§2.6 C14) and **whether a duplicate
   financial-activity row produces `DuplicateFinancialActivityAccountFoundException`** (§6.2). Both
   depend on the driver's message containing a literal substring that the *unnamed* index may not
   supply. These decide two contract refusal codes and are the highest-value cheap captures from this
   slice.
4. **Whether `GET /glaccounts?searchParam=x` errors** (§9). The SQL text at
   `GLAccountReadPlatformServiceImpl.java:154` is invalid as written, but this was not executed.
5. **The reachability of the two `fromInt(...).toString()` NPEs** in the not-found exception messages
   (§4.6, `AccountingProcessorHelper.java:1210` and `:1026`). Requires a product with a missing
   mapping at a placeholder absent from the *other* enum.
6. **The share-product `product_type` mis-filing (§5.4 / D-8) was not observed at runtime.** It is
   derived from three cited files and is a strong claim on that evidence, but it is not an
   observation.
7. **Where `manual_journal_entries_allowed` is enforced** (§2.5). Nothing in the four scope paths
   reads it; the `journalentry` package was not swept for it.
8. **Whether any code outside the four scope paths forbids posting to a HEADER account** (§2.4).
   Nothing inside them does.
9. **What the callers of the four reason/classification finders do with a `null` return** (§4.4) —
   those callers are outside the slice and were not traced.
10. **Whether `PortfolioProductType.fromInt` is ever reached with a stored 3/4/5** via
    `AccountingEnumerations.java:84` or `JournalEntryMapper.java:79` (§3.4). The permutation is
    verified; the blast radius is not.
11. **The runtime effect of the DDL default `account_usage = 2`** (§2.1) — every code path supplies
    `usage` explicitly, so the default should be unreachable except by direct SQL.
12. **`rs.wasNull()` mis-ordering** (§9) — the ordering is verified in source; the resulting
    `tagId` value was not observed.

---

## 12. Backlog — findings outside the four assigned scope paths

Read only; nothing outside the scope paths was modified.

| # | Finding | Where |
|---|---|---|
| B-1 | The slice's core types live in `fineract-core`, and `LoanProductToGLAccountMappingHelper` lives in `fineract-loan` under a **split package** shared with `fineract-provider`. The Go package boundary must be drawn on the Java package, not the Gradle module. | §1.2 |
| B-2 | The whole mapping-*resolution* code path is in `AccountingProcessorHelper.java` (`journalentry`, slice A1). A1 and A2 must agree on who owns it; this document is A2's transcription of A1's code and should be re-derived by A1 rather than trusted. | §4 |
| B-3 | `AccountingProcessorHelper.java` duplicates the resolution logic **four times** (loan / working-capital / savings / shares) with three different miss behaviours and three different charge-precedence chains. `InvestorAccountingHelper.java:92, :123` (module `fineract-investor`) is a **fifth** partial copy. A single parameterised resolver is the obvious port shape, but unifying it changes behaviour — decide deliberately. | §4.2, §4.3 |
| B-4 | `m_trial_balance` (`DECIMAL(19,6)`, written balances) and the `acc_gl_journal_entry` money columns (also `DECIMAL(19,6)`) belong to A1's ledger port, not A2's. The `19,6` house style vs MNT minor-unit 2 needs one program-level decision, not one per slice. | §8 |
| B-5 | **Fineract ships no default chart of accounts.** `0002_initial_data.xml` and `0003_postgresql_specific_initial_data.xml` insert **zero** rows into `acc_gl_account`; the only mentions are report-parameter SQL strings (`0002_initial_data.xml:12276`, `0003_postgresql_specific_initial_data.xml:277`). A fresh tenant starts with an empty COA. A Mongolian NBFI/FRC-aligned chart is therefore a **product decision to be made**, with no upstream seed to reconcile against. | subagent sweep, re-verified by this worker's own grep |
| B-6 | `acc_product_mapping` has **no index on `gl_account_id`** despite the FK added in `0175_add_fk_acc_product_mapping.xml:26-29` and despite `validateForAttachedProduct` scanning exactly that column on every GL-account disable. Cheap index in the Go schema. | §5.1, §2.6 U3 |
| B-7 | `acc_gl_account.hierarchy` has no index (`0001_initial_schema.xml:57`), so any subtree query is a sequential scan. If the Go port ever queries by hierarchy prefix, index it. | §2.2 |
| B-8 | `write_off_reason_id` was added to `acc_product_mapping` with **no foreign key** (`0199_write_off_reason_mapping_loan.xml:28`), unlike the three sibling code-value columns. Width also differs (`BIGINT` vs `INT`). | §5.1 |
| B-9 | `Charge.getAccount()` (`m_charge`'s own GL account) is a precedence level that exists for savings charges only (`AccountingProcessorHelper.java:1255-1258`). The `charge` context is Tier A too; the two slices must not each assume they own it. | §4.3 |

---

## 13. Complete citation index

Every file this document cites, so the reviewer can re-open them in one pass. All paths relative to
`/Users/buv/fineract` at commit `426a23544`.

**In scope (the four assigned paths):**

- `fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/service/GLAccountWritePlatformServiceJpaRepositoryImpl.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/service/GLAccountReadPlatformServiceImpl.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/command/GLAccountCommand.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/serialization/GLAccountCommandFromApiJsonDeserializer.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/exception/{GLAccountInvalidDeleteException,GLAccountInvalidUpdateException,GLAccountInvalidParentException,GLAccountDuplicateException,GLAccountDisableException,GLAccountInvalidUsageException,GLAccountInvalidClassificationException,InvalidParentGLAccountHeadException}.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/domain/{TrialBalance,TrialBalanceRepository}.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/jobs/updatetrialbalancedetails/UpdateTrialBalanceDetailsTasklet.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/api/GLAccountsApiResource.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/producttoaccountmapping/domain/{ProductToGLAccountMapping,ProductToGLAccountMappingRepository}.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/producttoaccountmapping/service/{ProductToGLAccountMappingHelper,SavingsProductToGLAccountMappingHelper,ShareProductToGLAccountMappingHelper,ProductToGLAccountMappingReadPlatformServiceImpl}.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/producttoaccountmapping/serialization/ProductToGLAccountMappingFromApiJsonDeserializer.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/producttoaccountmapping/exception/{ProductToGLAccountMappingNotFoundException,ProductToGLAccountMappingInvalidException}.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/financialactivityaccount/domain/{FinancialActivityAccount,FinancialActivityAccountRepository,FinancialActivityAccountRepositoryWrapper}.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/financialactivityaccount/serialization/FinancialActivityAccountDataValidator.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/financialactivityaccount/service/FinancialActivityAccountWritePlatformServiceImpl.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/financialactivityaccount/api/FinancialActivityAccountsJsonInputParams.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/financialactivityaccount/exception/{FinancialActivityAccountInvalidException,FinancialActivityAccountNotFoundException,DuplicateFinancialActivityAccountFoundException}.java`
- `fineract-provider/src/main/java/org/apache/fineract/accounting/productaccountmapping/service/ProductToGLAccountMappingWritePlatformServiceImpl.java`

**Read outside scope, cited, never modified:**

- `fineract-core/src/main/java/org/apache/fineract/accounting/glaccount/domain/{GLAccount,GLAccountType,GLAccountUsage}.java`
- `fineract-core/src/main/java/org/apache/fineract/accounting/glaccount/data/GLAccountData.java`
- `fineract-core/src/main/java/org/apache/fineract/accounting/glaccount/api/GLAccountJsonInputParams.java`
- `fineract-core/src/main/java/org/apache/fineract/accounting/common/AccountingConstants.java`
- `fineract-core/src/main/java/org/apache/fineract/accounting/common/AccountingEnumerations.java` (line 84 only)
- `fineract-core/src/main/java/org/apache/fineract/portfolio/PortfolioProductType.java`
- `fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccountingProcessorHelper.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/domain/{JournalEntryRepository,JournalEntryType}.java`
- `fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/JournalEntryMapper.java` (line 79 only)
- `fineract-loan/src/main/java/org/apache/fineract/accounting/productaccountmapping/service/LoanProductToGLAccountMappingHelper.java` (existence/location only)
- `fineract-investor/src/main/java/org/apache/fineract/investor/accounting/journalentry/service/InvestorAccountingHelper.java` (lines 92, 123 only)
- `fineract-provider/src/main/resources/db/changelog/tenant/parts/0001_initial_schema.xml`
- `fineract-provider/src/main/resources/db/changelog/tenant/parts/{0153_add_charge_off_reason_id_to_acc_product_mapping,0160_add_acc_product_mapping_product_id_index,0175_add_fk_acc_product_mapping,0198_add_classification_id_to_acc_product_mapping,0199_write_off_reason_mapping_loan}.xml`
- `fineract-provider/src/main/resources/db/changelog/tenant/parts/{0002_initial_data,0003_postgresql_specific_initial_data}.xml` (seed-row sweep only)
