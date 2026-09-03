# T492 — INDEPENDENT review of T489 (Tier C platform gap audit)

| | |
|---|---|
| Task | `T492` — independent adversarial reviewer of `T489` |
| Branch | `softhouse/T492-review-t489` |
| Reviewed | `softhouse/T489-tierC-platform-gap-audit` @ `0f1028cfe45300831cab7d424c55427ec53c235b` |
| Deliverable | `.softhouse/reviews/t492-review-t489/REVIEW.md` |
| Oracle pin, verified | `426a23544e8426a38ae43ae404670a0a7e85b9eb` · `status --porcelain` empty before and after · checkout not modified |
| Verdict | **ACCEPT WITH CONDITIONS** (4 conditions) |
| Counts | **4 MAJOR · 9 MINOR** · 33 citations sampled, **32 confirmed (97.0%)** · **44 of 44** row LOCs re-measured, ~12 of 44 classifications re-derived in depth |
| Safe to plan Tier C from? | **Yes for the non-`†` slices C-1…C-5, once the four conditions are applied. No for the 7 `†` rows (50,846 LOC) until R-1 resolves them.** |

## What I did

Derived my own answers from the two trees **before** opening T489's document, per the mandated
order: measured the whole Tier C surface from the 20 `fineract_paths`, inventoried `nexus/`,
analysed `program.json`'s path assignments, and re-derived all five non-negotiable claims. Then read
T489 and compared.

## Independently reproduced (agreement, derived not read)

- **Tier C surface = 192,168 main-Java LOC / 2,235 files.** `program.json` says `main_loc: 180000`
  — understated by **12,168 (6.8%)**.
- **The partition is genuinely exhaustive and non-overlapping.** Verified by decomposing every
  parent directory and checking the children sum to the parent: `provider/infrastructure` 81,148 (0
  residual, 0 files at maxdepth 1); `core/infrastructure` 31,509 (residual **42** =
  `DataIntegrityErrorHandler.java`, exactly 42 lines = row G17); `fineract-core` 71,833 (0);
  `organisation` 14,195 = G9 10,780 + P1 2,190 + N17 1,225 (0); `event` 7,917 = N3 5,922 + G12 1,995
  (0). All 44 row LOCs reproduce. Subtotals sum to 192,168.
- **The zero-NEXUS-PROVIDES structural claim.** `nexus/go.mod` is three lines with **zero `require`
  directives**; `go list ./...` returns **6 packages**, all Tier 0 / Tier A + harness; **no
  `.gitmodules`**; no second Go module; no reference to an external Nexus repo anywhere in the tree;
  `program.json`'s own `go_target` `nexus/internal/platform` **does not exist**. 70 `.go` files,
  40,242 lines, 25,628 non-test, 16,715 of those the conformance harness. T489 was right to refuse
  to convert doctrine (`patterns.md:81`, `engagement-plan:68`, both verified verbatim) into a
  NEXUS-PROVIDES row. **R-1 endorsed as the program's cheapest next action.**
- **37,525 LOC misfiled into Tier C**, reproduced to the line (23,652 + 1,932 + 1,897 + 1,749 +
  8,295). The **`dataqueries` duplicate is real**: `tierA-provisioning-reporting` names
  `…/infrastructure/dataqueries` while Tier C names its **parent** `…/infrastructure`.
- **All five non-negotiable claims hold at the cited lines:** `AppUser.java:73-78` /
  `Staff.java:41-45` two-field names (both `nullable = false`); timezone per-tenant
  (`tenant-store/…/0001_initial_schema.xml:77`; `m_office` at `tenant/…:2863-2878` has **no** zone
  column; both Mongolian zones are seeded at `0002_initial_data.xml:1502,1508` but
  `tenants.timezone_id` is one scalar); `IdempotencyKeyResolver.java:36` **generates** a missing key
  where CLAUDE.md requires refusal; `fineract-db` = **0** Java LOC with 271 files / **93,498** lines
  of Liquibase XML run-not-ported.
- **Oracle Database is absent — verified harder than T489 verified it.** T489 grepped only the Tier
  C paths; I grepped the **whole** pinned tree: `oracle.jdbc` 0, `OracleDialect` 0, `:1521` 0 real,
  `ojdbc` 44 hits **all** the substring `oJdbc` in camelCase (`toJdbcUrl`, `validateToJdbcColumn`,
  `mapApiTypeToJdbcType`), whole-word `oracle` only **4** (two URLs, one ESAPI doc link, one
  comment). `DatabaseType.java:21-25` = `{MYSQL, POSTGRESQL}`; gradle declares only
  mysql/mariadb/postgresql drivers. **The program's repeated belief is corrected and the correction
  survives.**

## MAJOR findings (all four are conditions)

- **F-1 — N17 `organisation/teller` is a FALSE NOT-APPLICABLE.** `org.apache.fineract.organisation.teller`
  is split across two Gradle modules: `fineract-branch/` (50 files, 3,937 LOC — api/data/domain,
  the whole `tierB-branch` context) and `fineract-provider/…/organisation/teller/` (3 files, **1,225
  LOC — the service implementations**: `TellerManagementReadPlatformServiceImpl`,
  `TellerWritePlatformServiceJpaImpl`, `OrganisationTellerConfiguration`). This is **exactly** the
  module-split pattern T489 documents in §5.6 and applies correctly to four other cases; it missed
  the fifth and deleted it instead of reassigning it. Two consequences: 1,225 LOC of an active
  (`status: pending`) Tier B context is marked "never port", and `tierB-branch` as scoped
  (`fineract-branch` only) would be ported **without its service layer**. → reclassify as **R5,
  reassign to `tierB-branch`**; add the provider path to `tierB-branch.fineract_paths`
  (`main_loc` 3,937 → 5,162). Corrected subtotals **38,750 / 67,495 / 2,190 / 83,733 = 192,168**;
  deferred-(d) 51,196 → **49,971**.
- **F-2 — `RoutingDataSource.java:49,108-115` does not support its claim.** `:49` is the class
  declaration; `:108-115` is `private String tenant()`, a **logging** helper. Real resolution is
  `:73-75` `determineTargetDataSource()` (called from `:61-62`, `:78-79`) plus
  `DataSourcePerTenantServiceFactory.java:70-96`. Classification unaffected; citation must be
  replaced.
- **F-3 — N8's prose classifies `FineractPlatformTenant{,Connection}` NOT-APPLICABLE, but both are
  in `core/domain/`, which the same partition assigns to G1.** The arithmetic is clean (N8 = 2,605 =
  `core/service/database` exactly), but a planner following the prose would delete the tenant context
  object — and `FineractPlatformTenant.getTimezoneId()` is the **sole source** read by
  `DateUtils.getDateTimeZoneOfTenant()` (`:65-67`), the code path satisfying CLAUDE.md's
  two-timezone rule. 30 main-source files call `ThreadLocalContextUtil.getTenant()`; 32 reference
  `FineractPlatformTenant`.
- **F-4 — N9 `entityaccess`: class correct, row materially incomplete.** I performed **both** checks
  T489 conceded it skipped. **(a) Off by default: CONFIRMED** —
  `tenant/parts/0002_initial_data.xml:186-194` and `:195-204` seed
  `office-specific-products-enabled` and `restrict-products-to-user-office` with
  **`enabled = false`, `value = 0`**; `FineractEntityAccessUtil.java:79-100,104-125` gates every
  behaviour behind `property.isEnabled()`. **(b) `tierB-branch` does NOT depend on it: CONFIRMED** —
  `grep entityaccess fineract-branch/` = 0 hits. **So NOT-APPLICABLE stands.** But the row omits that
  entityaccess is imported by **11 Tier A/B files** (22 imports): `LoanApplicationValidator`,
  `LoanProduct{Read,Write}PlatformService*`, `Charge{Read,Write}PlatformService*`,
  `SavingsProduct{Read,Write}PlatformService*` and three `starter/` configs. Sharpest:
  `LoanApplicationValidator.java:1853-1866` throws `NotOfficeSpecificProductException` on the
  **loan-application path**. Dropping entityaccess without recording this leaves Tier A porters with
  a dangling call or a silently-dropped validator.

## MINOR findings (9)

F-5 row N9 asserts as fact what §9.1 admits was unverified · F-6 "*Oracle Database does not appear
at all*" over-claims (`ErrorHandler.java:74` = `// Oracle: deadlock`) and the grep was narrower than
the heading · F-7 §1.2 says "273-line residual", G17 says 42 (273 = G16 231 + G17 42) · F-8 N16
"runs it on a schedule" unsupported — `AdHoc.java:46` stores the query and `:58-62` the frequency,
but **no executor exists** in the pinned tree, which strengthens the class and weakens the
permanent-exclusion argument · F-9 `ClientPersonConstants.java:27-29` is first/**middle**/last, not a
"two-name defect" · F-10 `HookProcessorProvider.java:41-47` dispatches **four** processors, not
three · F-11 N19 `instancemode` (279 LOC ✓) is justified from U-1 doctrine when a stronger
evidence-based reason exists (`FineractInstanceModeApiFilter.java:42-73` is Fineract deployment
topology, NOT-APPLICABLE(c) regardless of Nexus) · F-12 §3.1's "roughly 15k" harness lines is 16,715
of 25,628 (65%) · F-13 N4's credit-bureau capability transfer to `tierB-loan-origination` must reach
`program.json`, not only the document.

## Contradictions surfaced (findings, not fixed by me)

1. `tierC-platform-map-first.go_target` = `nexus/internal/platform` — **does not exist**.
2. `dataqueries` sits in two contexts' `fineract_paths`, so one run **must** violate CLAUDE.md's
   per-run scope guard. Fix in `program.json` before either context is planned.
3. F-1 puts the audit and `program.json` in direct conflict over whether `tierB-branch` ships.

## Honest boundary

I re-measured **44 of 44** row LOCs and proved the partition. I re-derived the **classification
argument** in depth for ~**12** rows (N8, N9, N14, N16, N17, N19, N21, the N3/G12 event split, G17,
the organisation split, R1–R4). The other ~32 rows' classes I accepted on T489's stated reasoning
without independent challenge — their LOC are confirmed, their class is not. `[UNVERIFIED]` in my
own review: V-1 what Nexus actually provides (repository contents, not a search failure — five
search locations listed); V-2 how `program.json`'s 180,000 was taken; V-3 Mongolian regulatory
obligations bearing on N4/N6/N13; V-4 the `†` split inside G5/G6; V-5 all runtime behaviour — there
is no running Fineract and no PostgreSQL here, so every "off by default"/"throws" claim above is a
claim about code and seed data I read.

## Constraints observed

No Go written · `nexus/` untouched · no vector created · no DEC-n or frozen contract amended · no
`program.json` edit (all changes are recommendations) · pinned oracle checkout unmodified.

## Next

`softhouse-program` should apply the four conditions to T489's document, action B-1 (now **five**
path moves, including the teller one) and the `dataqueries` de-duplication in `program.json`, raise
gate **G-C1** (three-field names vs schema-first) to `user`, and treat **R-1** — attach the Gerege
Nexus platform tree — as the next scheduled work, because until it lands Tier C is a range
(~33k–84k LOC), not a number.
