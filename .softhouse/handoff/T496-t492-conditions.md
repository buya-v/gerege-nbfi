# T496 — apply T492's conditions to the Tier C platform gap audit

| | |
|---|---|
| Task | `T496` — apply the four MAJOR conditions from `T492`'s review of `T489` |
| Branch | `softhouse/T496-t492-conditions`, branched from `origin/softhouse/T489-tierC-platform-gap-audit` @ `0f1028cf` |
| Edited | `docs/analysis/tierC-platform-gap-audit.md`, **in place** (rev 1 → rev 2). The audit was not redone. |
| Reference oracle | Fineract reference implementation, pinned read-only checkout `/home/user/fineract` |
| Oracle pin, verified by me | `git -C /home/user/fineract rev-parse HEAD` → **`426a23544e8426a38ae43ae404670a0a7e85b9eb`**; `git status --short` → **empty** before and after. The checkout was never modified. |
| Nexus | Not read, not touched. No Go written, no vector created, no DEC-n or contract amended. |
| `program.json` / `gates.md` | **Not edited** — outside my permissions. Conflicts are recorded below and in the document for the driver. |
| Date | 2026-09-02 |

Throughout, **"the reference oracle" means the Fineract implementation** we grade Go against.
**"Oracle Database"** appears only as the name of the prohibited product. Unrelated.

## Method, and the reason for it

The brief was explicit that this program has twice had a reviewer's proposed patch **refuted** by
the worker asked to apply it (T451 refuted T449; T455 refuted T448). So **every one of T492's four
MAJORs was re-derived from the pinned checkout by me, from first commands, before any edit was
written.** T492's proposed corrected subtotals (`38,750 / 67,495 / 2,190 / 83,733`) were **not
copied** — I recomputed them from the row figures and from my own measurement of the moved package.
They happen to be right, which is a reproduction and not a reading.

**Runtime caveat, stated once.** There is no running Fineract and no PostgreSQL in this session.
Every "off by default", "throws", "returns empty" claim below is a claim about source and seed data
I opened at the pin.

**"Not found" is a statement about the search.** Every negative below names where I looked.

---

## The four MAJORs

### F-1 — N17 `organisation/teller` is a false NOT-APPLICABLE → **APPLIED**, and it is worse than T492 reported

**Re-derived, not accepted.** Commands run against the pin:

```
find fineract-branch -name '*.java' -path '*/src/main/*' | wc -l          → 50
find fineract-branch -name '*.java' -path '*/src/main/*' -exec cat {} + | wc -l → 3937
find fineract-provider/src/main/java/org/apache/fineract/organisation/teller -name '*.java' → 3 files
  …/teller/service/TellerManagementReadPlatformServiceImpl.java   704
  …/teller/service/TellerWritePlatformServiceJpaImpl.java         450
  …/teller/starter/OrganisationTellerConfiguration.java            71
                                                          total  1225
```

Both halves are the **same Java package**, `org.apache.fineract.organisation.teller`, split across
two Gradle modules — the module-split pattern T489 documents in its own §5.6 and applies correctly
to four other packages.

**The evidence is stronger than "same package name", and this is my own addition.** The three files
in `fineract-branch/…/teller/service/` are **interfaces** (`TellerManagementReadPlatformService.java`,
`TellerWritePlatformService.java`, `TellerTransactionWritePlatformService.java`), and the Tier C
files are their **implementations**, opened and read:

- `TellerWritePlatformServiceJpaImpl.java:64` — `public class TellerWritePlatformServiceJpaImpl implements TellerWritePlatformService {`
- `TellerManagementReadPlatformServiceImpl.java:60` — `public class TellerManagementReadPlatformServiceImpl implements TellerManagementReadPlatformService {`
- `OrganisationTellerConfiguration.java:49-60` — the Spring `@Bean` wiring, with
  `@ConditionalOnMissingBean(TellerManagementReadPlatformService.class)` at `:50` and
  `@ConditionalOnMissingBean(TellerWritePlatformService.class)` at `:60`.

So `tierB-branch` — which `program.json` carries as `fineract_paths: ["fineract-branch"]`,
`main_loc: 3937`, **`status: pending`** — would be ported as three service interfaces with **no
implementations behind them**. T489 did not merely misclassify 1,225 lines; it marked "never port"
the entire behavioural half of a context the program intends to build.

**Applied as:** row N17 struck from §6.2 (row number retained struck-through so the 44-row count and
any external citation of "N17" still resolve) and re-entered as **R5** in §6.1; new §5.6.1 carrying
the full re-derivation; §5.6 retitled *Five subsystems…* with teller added to its table; subtotals,
§7.1, §7.3, §8.1, §9.1's neighbourhood, B-1 and the footer all corrected.

**Direction of the split noted explicitly in the document**, because it is the opposite of the other
four: for `portfolio` / `batch` / `accounting` / `dataqueries` the `fineract-core` half sits in Tier
C and the provider half in Tier A/B; for teller the **provider** half sits in Tier C and the
`fineract-branch` half is Tier B. Same pattern, inverted.

### F-2 — `RoutingDataSource.java:49,108-115` does not support its claim → **APPLIED**, with a better replacement than proposed

Opened all the regions myself in
`fineract-core/src/main/java/org/apache/fineract/infrastructure/core/service/database/RoutingDataSource.java`:

- **`:49`** is `public class RoutingDataSource extends AbstractDataSource {` — the class
  declaration. It resolves nothing. **T492 is right.**
- **`:107-116`** is `private String tenant()`. Line `:108` *does* call
  `ThreadLocalContextUtil.getTenant()` — so the citation is not fabricated — but the method builds a
  **display string for logging** (`:113` `return tenant.getTenantIdentifier() + "/connection:" + …`)
  and is called only from `logConnectionCheckout` (`:90-96`) and `logConnectionCheckoutFailure`
  (`:98-105`), both of which return immediately unless
  `fineract.datasource.connection-checkout-diagnostics.enabled` is set (`:91`, `:99`). It resolves
  no datasource. **T492 is right that the cited lines do not support the sentence.**

**Where I went further than T492.** T492 proposed replacing the citation with
`RoutingDataSource.java:61-62,73-75` + `DataSourcePerTenantServiceFactory.java:70-96`. That is
correct but stops one link short of the line that makes T489's *sentence* true. The full chain,
every line opened:

1. `RoutingDataSource.java:60-71` `getConnection()` → calls `determineTargetDataSource()` at `:62`;
2. `RoutingDataSource.java:73-75` — `return this.dataSourceServiceFactory.determineDataSourceService().retrieveDataSource();`
3. `TomcatJdbcDataSourcePerTenantService.java:65-77` `retrieveDataSource()` — **`:69` is the line that
   actually reads the thread-local tenant**: `final FineractPlatformTenant tenant = ThreadLocalContextUtil.getTenant();`,
   then `:75-76` `TENANT_TO_DATA_SOURCE_MAP.computeIfAbsent(tenantConnectionKey, (key) -> dataSourcePerTenantServiceFactory.createNewDataSourceFor(tenant, tenantConnection))`;
4. `DataSourcePerTenantServiceFactory.java:58` `createNewDataSourceFor(FineractPlatformTenant, FineractPlatformTenantConnection)`,
   body `:70-96` — reads `tenantConnection`, branches on `fineractProperties.getMode().isReadOnlyMode()`
   at `:72`, builds the JDBC URL at `:81` and a HikariCP pool named `schemaName + "_pool"` at `:87`.

The document now carries the whole chain, with `TomcatJdbcDataSourcePerTenantService.java:69`
identified as the line that supports the original sentence. **Classification unaffected** — N8's
routing half stays NOT-APPLICABLE(d) under the recorded single-tenant PRODUCT choice.

### F-3 — N8's prose reaches into G1 and would delete the timezone source → **APPLIED**, both halves verified

**The arithmetic half — T492 says it is clean, and I confirm it.** Measured at the pin:

```
fineract-core/…/infrastructure/core/service/database   22 files   2,605 LOC   (= N8 exactly)
fineract-core/…/infrastructure/core/domain             17 files   1,267 LOC   (= G1's core/domain line exactly)
find …/core/service/database -name 'FineractPlatformTenant*'  → 0 files
```

`FineractPlatformTenant.java` and `FineractPlatformTenantConnection.java` are both under
`fineract-core/src/main/java/org/apache/fineract/infrastructure/core/**domain**/`. So the partition
never counted them in N8 — **the LOC and the sums were always right; only the prose was wrong**,
exactly as T492 said.

**The consequence half — verified, and it is the reason this is MAJOR.**
`DateUtils.java:65-67`, opened:

```java
public static ZoneId getDateTimeZoneOfTenant() {
    final FineractPlatformTenant tenant = ThreadLocalContextUtil.getTenant();
    return ZoneId.of(tenant.getTimezoneId());
}
```

`grep -rn "getTimezoneId" --include=*.java` over the module set returns exactly **two** main-source
call sites: `DateUtils.java:67` and `JobRegisterServiceImpl.java:365` — and both read it off the
same `FineractPlatformTenant` object. **`FineractPlatformTenant.getTimezoneId()` is the sole source
of the tenant time zone**, i.e. the only implementation in this tree of CLAUDE.md's *two time zones
(`Asia/Ulaanbaatar` +08, `Asia/Hovd` +07), no DST, never hard-code an offset*. A planner following
N8's rev-1 prose and dropping the classes it named would delete it.

Reach, re-derived tree-wide over `src/main`: **30** files call `ThreadLocalContextUtil.getTenant()`,
**32** reference `FineractPlatformTenant`. Both reproduce T492 exactly.

**Applied as:** the two class names struck from N8's prose, N8 now says only the routing machinery
under `core/service/database` is NOT-APPLICABLE, and **G1's evidence line names the tenant context
object explicitly as a part that survives any Nexus re-grade**, with the `DateUtils` citation.

### F-4 — N9 `entityaccess` stands, but the row was incomplete → **APPLIED, with one count corrected**

**The class stands, and I verified the two checks T489 conceded it had skipped.**

**(a) Off by default — CONFIRMED.** `fineract-provider/src/main/resources/db/changelog/tenant/parts/0002_initial_data.xml`,
opened: `:185-195` is the `<insert tableName="c_configuration">` for id 20
`office-specific-products-enabled` with `<column name="value" valueNumeric="0"/>` and
**`<column name="enabled" valueBoolean="false"/>`** at `:191`; `:196-206` is id 21
`restrict-products-to-user-office`, same shape, `enabled` false at `:202`.
*(T492 cited `:186-194` and `:195-204`; those land inside the elements but not on their boundaries.
I cite the `<insert>` blocks I actually read.)*

Enforcement, opened in
`fineract-provider/…/infrastructure/entityaccess/service/FineractEntityAccessUtil.java`:
`:79-100` is the save path, gated at `:81` on `property.isEnabled()` for
`OFFICE_SPECIFIC_PRODUCTS_ENABLED` and again at `:88` for `RESTRICT_PRODUCTS_TO_USER_OFFICE` — no
mapping is written when disabled; `:104-125` is
`getSQLWhereClauseForProductIDsForUserOffice_ifGlobalConfigEnabled`, which initialises
`String inClause = ""` at `:105`, gates at `:110`, and **returns the empty string** at `:124` when
disabled.

**(b) `tierB-branch` does not depend on it — CONFIRMED.** `grep -rn "entityaccess" fineract-branch/`
→ **0 hits**, over the whole module, not just `src/main`.

**So NOT-APPLICABLE(d) survives on evidence, and T489's own nominated worry resolves in its favour.**
The document now records the check rather than the concession: §9.1 was rewritten from *"the
classification I am least confident in"* + an open admission, to *"the row rev 1 was least confident
in — now checked, and it holds"*, carrying the citations. (This also discharges T492's MINOR **F-5**,
which was the same internal contradiction, so F-5 is applied as a side effect.)

**The omission — and here my count differs from the reviewer's.** T492 reports **11 files / 22
imports**. My own sweep finds **10 files / 21 imports**:

```
grep -rn "entityaccess" --include=*.java .   |grep '/src/main/'  |grep -v '/infrastructure/entityaccess/'
  → 21 lines across 10 files, whole pinned tree, all modules
```

The 10, with owning context:
`portfolio/loanaccount/serialization/LoanApplicationValidator.java` (6 imports — **Tier A**);
`portfolio/loanproduct/service/LoanProduct{Read,Write}PlatformService*.java` and
`loanproduct/starter/LoanProductConfiguration.java` (**Tier A**);
`portfolio/charge/service/Charge{Read,Write}PlatformService*.java` and
`charge/starter/ChargeConfiguration.java` (**Tier A**);
`portfolio/savings/service/SavingsProduct{Read,Write}PlatformService*.java` and
`savings/starter/SavingsConfiguration.java` (**Tier B**). **None is in `fineract-branch`.**

I could not reproduce an eleventh file from any search I ran (the sweep above was whole-tree,
`--include=*.java`, filtered only to `/src/main/` and away from the subsystem's own package). The
document states **my** number and says so, and flags the discrepancy in the row. It does not change
the finding: the omission is real and it lands on Tier A.

Sharpest call site, opened and read —
`LoanApplicationValidator.java:1853-1866`, `private void officeSpecificLoanProductValidation(final Long productId, final Long officeId)`:
gated at `:1856` on `restrictToUserOfficeProperty.isEnabled()` for
`GlobalConfigurationConstants.OFFICE_SPECIFIC_PRODUCTS_ENABLED`, and when enabled it looks up a
`FineractEntityToEntityMapping` and **throws `NotOfficeSpecificProductException(productId, officeId)`
at `:1862`** if none is found. A validator on the loan-application path.

**Applied as:** N9 rewritten to carry (i) the off-by-default seeds, (ii) the `fineract-branch`
non-dependence, (iii) the 10 call sites with their owning tiers and the **port-time obligation** —
because both flags seed `enabled = false`, each ported call site resolves to the disabled path (no
mapping saved, empty `IN` clause, `officeSpecificLoanProductValidation` a no-op) and **must carry a
comment saying so** rather than silently dropping the check or porting a dangling call.

---

## Re-derived subtotals, and whether the partition still reconciles

F-1 moves **1,225 LOC between two classes**. It adds no line and removes none, so the partition is
still exhaustive and non-overlapping over the same 192,168 lines.

| Class | rev 1 | rev 2 | Δ |
|---|---|---|---|
| reassign | 37,525 (4 rows) | **38,750** (5 rows) | +1,225 |
| NOT-APPLICABLE | 68,720 (22 rows) | **67,495** (21 rows) | −1,225 |
| PARTIAL | 2,190 (1 row) | 2,190 | — |
| GAP | 83,733 (17 rows) | 83,733 | — |
| **Total** | **192,168** (44 rows) | **192,168** (44 rows) | **0** |

```
38,750 + 67,495 + 2,190 + 83,733 = 192,168   ✓   (recomputed, not copied)
```

Dependent figures re-derived rather than inherited:

- **Deferred-`(d)` subtotal**, by summing the ten remaining (d) rows myself:
  `16,484 + 11,027 + 5,922 + 3,831 + 3,128 + 2,382 + 1,993 + 1,971 + 1,944 + 1,289 = 49,971`,
  and `49,971 + 1,225 = 51,196` reproduces rev 1's figure — so the arithmetic checks in both
  directions. **Ten** rows, not eleven.
- **§7.1 percentages:** 20.2% / 35.1% / 1.1% / 43.6%, summing to 100.0%.
- **`tierB-branch.main_loc`:** `3,937 + 1,225 = 5,162`.
- **Unchanged, and this is the important part:** GAP 83,733, GAP-real 32,887, GAP-**†** 50,846
  (`32,887 + 50,846 = 83,733` ✓). **The correction does not move the number Tier C is planned
  against.**

## T492's framing of the headline number — carried into the document

Added where a planner reads it, not buried:

- A boxed block at the head of **§7.1**: carry Tier C as a **range, ~33k–84k LOC**, never as 83,733
  alone; **C-1…C-5 are plannable now**; the seven **†** rows (50,846 LOC) are **not plannable in
  either direction** until R-1 attaches the real Nexus platform tree — scheduling them now risks the
  unjustified plumbing port CLAUDE.md calls a rejection, and skipping them risks a hole.
- A second boxed block at the head of **§8** (the slice table), where a planner picks a slice.
- The footer now states the range and the row counts.
- **One rev-1 slip corrected along the way:** §8's C-0 row said slices "C-1…C-4" were safe without
  R-1. C-5 (G12, in-process business events) is not **†** either, so the safe set is **C-1…C-5** —
  which is also where T492 drew the line independently.

## One MINOR applied, eight not

**Applied**, because it is a statement about the partition itself and I was asked to keep the
partition reconciling: **F-7** — §1.2 said "a 273-line residual". Re-measured: `fineract-core/…/util`
(the G16 path; note it is `org/apache/fineract/util`, not `infrastructure/core/util`) is 4 files /
**231** lines, and the only `.java` file directly under `fineract-core/…/infrastructure` is
`DataIntegrityErrorHandler.java` at **42** lines = row **G17**. `231 + 42 = 273`. The residual
carried as its own row is **42**, and §1.2 now says so.

**F-5** is applied as a side effect of F-4 (the §9.1 concession is replaced by the completed check).

**Not applied, still open** — recorded in the document's §0.1 so they are not lost: **F-6** (the
"Oracle Database does not appear at all" heading over-claims by one word — `ErrorHandler.java:74`
carries a `// Oracle: deadlock` comment — and T489's grep was narrower than its heading; T492 re-ran
it tree-wide and the substantive conclusion holds), **F-8** (N16 "runs it on a schedule" —
no executor found in the pinned tree), **F-9** (`ClientPersonConstants` is first/**middle**/last, a
Western three-field model, not a "two-name defect"), **F-10** (`HookProcessorProvider` dispatches
four processors, not three), **F-11** (N19 `instancemode` justified from U-1 doctrine when an
evidence-based reason exists), **F-12** (§3.1's "roughly 15k" harness lines is 16,715 of 25,628 =
65%), **F-13** (N4's credit-bureau capability transfer must reach `program.json`). None changes a
class or a LOC figure. I did not independently re-derive these eight and make no claim about them
beyond reporting them as open.

## Nothing refuted

All four MAJORs held on independent re-derivation. Two were **strengthened** by evidence T492 did
not cite (F-1's `implements` relationship; F-2's `TomcatJdbcDataSourcePerTenantService.java:69`), and
one had a **count corrected downward** (F-4: 10 files / 21 imports, not 11 / 22). T492's proposed
subtotals were recomputed independently and are correct.

## For the driver — `program.json` conflicts I may not fix

Recorded in the audit's §0.1, §5.6, §5.6.1, §7.3 and B-1, and repeated here:

1. **`tierB-branch` is mis-scoped and this is the urgent one.** `fineract_paths: ["fineract-branch"]`
   / `main_loc: 3937` gives the context three service interfaces with no implementations. Add
   `fineract-provider/src/main/java/org/apache/fineract/organisation/teller` and raise `main_loc` to
   **5,162**. The context is `status: pending`, so this can be fixed before it is planned.
2. **`dataqueries` overlaps two contexts** by prefix containment — Tier C names
   `fineract-provider/…/infrastructure`, which contains `tierA-provisioning-reporting`'s
   `…/infrastructure/dataqueries`. Per the driver's own sweep this is the program's **only** such
   overlap. One of the two runs must otherwise violate CLAUDE.md's per-run scope guard.
3. **`tierC-platform-map-first.main_loc: 180000`** is not the measured figure (192,168 measured;
   83,733 GAP; ~33k–84k as the honest planning range).
4. The four other path moves of **B-1** (`fineract-core/…/portfolio`, `…/batch`, `…/accounting`,
   both halves of `…/dataqueries`).

**Explicitly not raised as a contradiction:** `tierC-platform-map-first.go_target`
(`nexus/internal/platform`) not existing on disk. T492 listed it as a contradiction; **it is not
one.** All fourteen unported contexts have a non-existent `go_target`, because the port is what
creates the directory. That is the expected state of an unported context, and the audit does not say
otherwise.

## Gate candidates

No new gate is raised by this revision. Two existing ones are unaffected and stand as T489 wrote
them and T492 endorsed:

- **G-C1 — three-field names vs schema-first** (`m_appuser.firstname`/`lastname`,
  `m_staff.firstname`/`lastname` are columns of the schema CLAUDE.md says to *adopt*). A contract
  change, therefore a `user` task. Blocks slice C-4.
- **R-1 — attach the Gerege Nexus platform tree** and re-grade the seven **†** rows. Not a gate in
  the `user`-decision sense; it is a repository-access action, and it is the program's cheapest next
  move. Until it happens, no **†** row is plannable in either direction.

One thing worth the driver's attention that is *not* a gate: F-3 establishes that
`FineractPlatformTenant.getTimezoneId()` is the **sole** implementation of CLAUDE.md's two-time-zone
non-negotiable in this tree, and T489's backlog **B-2** already records that the zone is
per-**tenant** while Gerege needs it per-**office** (`m_office` has no zone column). Those two facts
together mean the two-time-zone rule is currently satisfied by exactly one scalar per deployment.
**B-2 should be resolved before `tierB-branch` is planned**, since branches are the thing that spans
+08 and +07.

## Constraints observed

No Go written. `nexus/` not touched. No vector created. No DEC-n or frozen contract amended.
`.softhouse/program.json` and `.softhouse/gates.md` not edited. The pinned oracle checkout was read
only and is unmodified (`git status --short` empty before and after). Only
`docs/analysis/tierC-platform-gap-audit.md` and this handoff were written.
