# T489 — Tier C platform gap audit: Fineract's platform surface mapped onto Nexus

Task `T489` (`analyst`), context `tierC-platform-map-first`, dispatch `cloud-20260902-2000`.
Branch `softhouse/T489-tierC-platform-gap-audit`. Paired reviewer: **T492**.

Deliverable: **`docs/analysis/tierC-platform-gap-audit.md`**. No Go written, no port performed,
no contract changed, no file under `nexus/` touched. The pinned oracle checkout
`/home/user/fineract` (`426a23544e8426a38ae43ae404670a0a7e85b9eb`) was read only and
`git status --porcelain` was empty before and after.

---

## Headline

**Tier C's genuine port is ~83.7k LOC, not the 180k the program is carrying — and the larger half
of that 83.7k is unresolved because the Gerege Nexus platform tree is not in this repository.**

```
measured Tier C surface        192,168 LOC / 2,235 files   (program.json says 180,000)
  reassign to Tier A/B          37,525  19.5%   already someone else's context
  NOT-APPLICABLE                68,720  35.8%   never ported
  PARTIAL                        2,190   1.1%   extend already-ported Nexus code (~1,800 left)
  GAP                           83,733  43.6%   must be ported
  NEXUS-PROVIDES                     0     0%   see below — this zero is about the EVIDENCE
```

Inside the GAP:

```
  GAP-real       32,887   port regardless of what Nexus turns out to provide
  GAP-† pending  50,846   host-candidate; re-grade before scheduling any port task
```

**So Tier C is somewhere between ~33k and ~84k LOC and this run could not close the gap.**

---

## 1. The finding that shapes the whole audit

`nexus/` contains **no platform code**. `go list ./...` returns six packages, all under
`internal/apps/{ledger,loanschedule}` — the Tier 0 schedule PoC, the Tier A GL slice, and the
conformance harness. `nexus/go.mod` has **zero `require` directives**: no `pgx`, no HTTP router, no
auth library, no scheduler. The complete deduplicated import surface of all 70 files is standard
library plus four internal packages — no `net/http`, no `database/sql`, nothing third-party.

I also checked: no `.gitmodules`, no second `go.mod` anywhere on disk outside the Go toolchain and
the pinned Fineract checkout, and the only Go outside `nexus/` is 7 one-off probes under
`.softhouse/`.

The doctrine that "Nexus already provides auth, tenancy, command bus, jobs"
(`.softhouse/patterns.md:81`, `docs/softhouse-engagement-plan.md:68`) is **not verifiable from any
tree available to this run**. Under the honesty rules I could not convert doctrine into a
NEXUS-PROVIDES row, because a false NEXUS-PROVIDES silently drops a subsystem out of the migration.

**So the audit records zero NEXUS-PROVIDES rows**, and everything doctrine would place there is
GAP with a **†** marker meaning *re-grade before scheduling a port task*.

> **R-1 is the program's cheapest next action:** attach the Gerege Nexus platform repository and
> re-grade the 7 **†** rows (50,846 LOC, 26.5% of Tier C). Until then the program cannot tell
> "Tier C costs 33k" from "Tier C costs 84k" — a 2.5× spread on the largest unported context.

---

## 2. Class counts

44 subsystem rows: **0 NEXUS-PROVIDES · 17 GAP (7 marked †) · 1 PARTIAL · 22 NOT-APPLICABLE ·
4 reassigned to Tier A/B.** The partition is exhaustive and non-overlapping and sums exactly to the
measured 192,168 (a 42-line residual is carried as its own row rather than absorbed).

The one PARTIAL is **money & currency** (`organisation/monetary`, 2,190 LOC) — the only row with
citable Nexus evidence: `nexus/internal/apps/loanschedule/rounding.go:3,7-12,20-24,30-34` and
`nexus/internal/apps/ledger/money.go:10-19` cover exact `(19, HALF_UP)` arithmetic; the
`ApplicationCurrency` registry, `MonetaryCurrency`/`Money` value objects and `MoneyHelper`'s
tenant-mode initialisation are not covered.

The largest NOT-APPLICABLE is **bulkimport, 16,484 LOC** — 410 `org.apache.poi` references, 17
per-entity column maps, a spreadsheet adapter over the same command API with no gradeable behaviour
of its own. Replacement if wanted: 1–2k LOC, not 16.5k.

---

## 3. Things a later run must not miss

1. **Four paths are misfiled into Tier C** (37,525 LOC): `fineract-core/…/portfolio` (23,652),
   `…/infrastructure/dataqueries` (10,044 — **already listed by `tierA-provisioning-reporting`**),
   `fineract-core/…/batch` (1,932), `fineract-core/…/accounting` (1,897). Same module-split trap
   `tierA-a2-behaviour.md` §1.2 documented: the Tier A/B contexts as written would port their
   contexts **without their own entity classes**. Backlog **B-1**.
2. **Idempotency diverges from CLAUDE.md at one line.**
   `fineract-core/…/commands/service/IdempotencyKeyResolver.java:36` *generates* a key when the
   caller supplies none; Gerege must **refuse**. The reference oracle therefore cannot supply a
   vector for the refusal — it needs a property test. The rest of the semantics is portable and
   located: `CommandSourceService.java:66-73,101-103` (key scoped to *action + entity*) and the
   three `Idempotency*` servlet filters.
3. **Do not target the newer `fineract-command*` bus.** Its own idempotency test is
   `CommandSampleApiTest.java:130` → `@Disabled // TODO: implement idempotency properly`. All money
   endpoints run the legacy path, which is also the only one vectors can grade. Backlog **B-3**.
4. **Three-field names collide with schema-first, and I did not decide it.**
   `AppUser.java:73-78` and `Staff.java:41-45` store `firstname`/`lastname` `NOT NULL` — columns of
   the schema CLAUDE.md says to *adopt*. Resolving it changes the frozen adapter contract, so it is
   raised as **`user` gate G-C1**, and it **blocks slice C-4**.
5. **Time zone is per-tenant, not per-office.** `DateUtils.java:65-67` reads an IANA zone from
   tenant config (so "never hard-code an offset" is already satisfied), but `timezone_id` lives on
   the tenant-store table (`0001_initial_schema.xml:77`) and `Office.java` has no zone column. A
   deployment spanning Ulaanbaatar (+08) and Hovd (+07) needs it on `m_office`. Backlog **B-2**.
6. **Oracle Database does not appear in Fineract at all.** `DatabaseType.java:21-25` is exactly
   `{MYSQL, POSTGRESQL}`; every `ojdbc`/`oracle.jdbc` grep hit is the substring `oJdbc` inside
   `toJdbcUrl`/`toJdbcValue`. The prohibition costs nothing here. What *does* exist is MySQL/MariaDB
   support (`DatabaseTypeResolver.java:31-33`), and that is the NOT-APPLICABLE.
7. **`fineract-db` contributes 0 Java LOC.** The adopted schema is 271 files / 93,498 lines of
   Liquibase XML under `fineract-provider/src/main/resources/db/changelog` — **run, not ported**.
   It is in no context's `main_loc` and no context's notes. Backlog **B-4**.

---

## 4. Recommended slice order (GAP only; nothing † before R-1)

| Slice | Rows | LOC | Why |
|---|---|---|---|
| **C-0** | — | — | R-1: attach Nexus, re-grade the 7 † rows |
| **C-1** | business date + holidays + working days | 4,377 | **Tier A is blocked on it**; cheapest vectors |
| **C-2** | command bus + maker-checker + idempotency | 10,088 | spine of every money write; the one deliberate oracle divergence |
| **C-3** | codes + account-number formats + configuration | 8,458 | referenced everywhere; G8 is where the RTGS/ACH+ MNT 5,000,000 threshold must live as config |
| **C-4** | offices + staff + provisioning criteria | 7,301 | **needs gate G-C1 answered first** (`m_staff`) |
| **C-5** | in-process business events | 1,995 | after-commit publication is load-bearing for double-entry |
| **C-6…** | everything † | 51,514 | blocked on C-0 |

**Do not start with G1** (core runtime/REST, 16,078 — the largest GAP row). It is the most likely to
evaporate on re-grade, and porting a JAX-RS layer into Go before knowing whether Nexus serves HTTP
is exactly the unjustified plumbing port CLAUDE.md calls a rejection.

---

## 5. `program.json` changes this implies (not made by me — I did not edit the file)

- `tierC-platform-map-first.main_loc`: **180,000 → 83,733** (ideally split 32,887 + 50,846-pending).
- Move the four §5.6 paths out of Tier C and add the `fineract-core` twins to the Tier A/B contexts
  that own them; `…/infrastructure/dataqueries` is currently in **two** contexts at once.
- Record the 22-row NOT-APPLICABLE set somewhere a later planner sees it, so no future run proposes
  a bulk-import or campaigns task and is rejected for it.

---

## 6. Honest boundary — what I did not do

- **Zero NEXUS-PROVIDES rows is a limitation, not a result.** §2 of the document states exactly
  where I looked. If the Nexus platform tree exists elsewhere, up to 50,846 LOC of my GAP total is
  wrong in the safe direction (over-scoped, not under-scoped).
- **Subsystem granularity only**, per the brief. Rows N1, N2, G1 and G4 are each large enough that a
  per-subsystem run may reclassify a sub-package.
- **Five `[UNVERIFIED]` items** in §9: U-1 (what Nexus provides), U-2 (which credit bureau
  `creditbureau` models), U-3 (whether FRC needs anything from N6/N13), U-4 (the 12,168 LOC
  measurement difference vs `program.json`), U-5 (whether the † split inside G5/G6 is at the right
  line).
- **Least-confident classification, stated in §9.1: `N9 entityaccess` (2,382 LOC, NOT-APPLICABLE).**
  I established what it is (an office↔product visibility matrix) but did **not** verify it is off by
  default and did **not** check whether `tierB-branch` depends on it. If Gerege's branch model needs
  per-office product visibility, that row is a GAP and I dropped a real subsystem by assertion.
  **T492 should re-derive N9 first.** Runners-up: N19 `instancemode` (rests on U-1 doctrine) and N16
  `adhocquery` (I extended a deferral into a recommended permanent exclusion on a security argument
  that is mine, not the program's).

---

## 7. Recorded PRODUCT choices (`chosen_by: agent`, Buyan retains veto)

- **Single-tenant deployment** — one deployment per licensed entity. Makes N8's routing half N/A.
  Reversing restores ~896 LOC to GAP.
- **Launch without** the eleven shape-(d) rows (51,196 LOC): bulk import, campaigns, external event
  delivery, report mailing, hooks, entity-access, SMS, templates, surveys, ad-hoc query, teller.
  Each row records the cheaper replacement if the capability is later wanted.
- **Ad-hoc query (N16) recommended as a permanent exclusion**, not a deferral — an arbitrary-SQL
  execution endpoint in a ledger system is a security regression regardless of launch scope.

Raised as a `user` gate, not decided: **G-C1** (three-field names vs adopt-Fineract's-schema).
