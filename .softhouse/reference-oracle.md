# Reference oracle (Fineract) — pinned facts

> **Terminology.** "The oracle" in this program means the **Fineract reference implementation**
> we grade Go output against (test-oracle sense). **Oracle Database is a prohibited product**
> in this program and appears nowhere in this stack — see the assertions below.

Recorded by task **T1** of run `2026-08-17-run1-harness-schedule-poc`, local fire on
Buyan's Mac, **2026-08-17T11:30Z (19:30 +08)**. Every vector capture must cite this file's
pin; a capture made against a different build is not comparable.

## Status: **UP** ✅ — *on the local fire's host only*

```
GET https://localhost:8443/fineract-provider/actuator/health
{"status":"UP","groups":["liveness","readiness"]}
```

## Reachability by fire — read this before planning vector work

The running instance is bound to **`localhost` on Buyan's Mac**. "UP" above is a fact about
that host, not about the program. Which fire you are determines whether vector work is
possible at all:

| Fire | Reaches this instance? | May capture vectors / run conformance? |
|---|---|---|
| **Local launchd** (08:00, 14:00 Asia/Ulaanbaatar) | **Yes** | **Yes** — the only fire that can |
| **Cloud routine** (20:00 Asia/Ulaanbaatar) | **No** | **No** — park with `oracle_unreachable` |
| By hand | depends where it runs | probe first, never assume |

Probe result from the **cloud sandbox, 2026-08-17 20:00 +08** — unreachable on every path:
no Docker daemon (`/var/run/docker.sock` absent), PostgreSQL not listening on `:5432`,
`actuator/health` returns nothing. The Fineract **source** checkout is present and pinned
in the cloud sandbox (at `/home/user/fineract`, not the Mac path below), so source analysis,
spec work and corpus mining all proceed there — only the **live instance** is missing.

**The rule this table exists to enforce:** an unreachable oracle makes conformance **exit 2**,
which is not a PASS and never becomes one. A vector that was not observed from this instance
is not a vector. No fire may synthesise, derive or extrapolate an expected value to fill the
gap — it parks the task and moves to work that needs no live instance.

**Read the code before you park, though: only exit 2 means this.** `conformance.sh`
also has **exit 3 — wrong interpreter**, which means the harness never started and
the oracle was **never contacted** (someone ran `sh conformance.sh` instead of
`bash conformance.sh`). Exit 3 is not evidence about this instance and must never
be parked as an outage; fix the invocation and grade again. Codes: `.softhouse/vectors/README.md`.

## Pinned build

| Fact | Value |
|---|---|
| Fineract commit | **`426a23544e8426a38ae43ae404670a0a7e85b9eb`** — matches the pinned commit of record |
| `git describe` | `1.15.0-273-g426a235` (273 commits past tag `1.15.0`) |
| Build version | `1.16.0-SNAPSHOT` |
| Branch | `develop` |
| Commit date | 2026-08-12T12:59+0000 |
| Source checkout | `/Users/buv/fineract` on the local fire's host; `/home/user/fineract` in the cloud sandbox — same commit, verified per fire (read-only for workers) |
| JVM | Zulu **21.0.11**+10-LTS (`azul/zulu-openjdk-alpine:21`) |
| JVM flags | `-Duser.home=/tmp -Dfile.encoding=UTF-8 -Duser.timezone=UTC -Djava.security.egd=file:/dev/./urandom` |

## Database — PostgreSQL only ✅

| Fact | Value |
|---|---|
| Engine | **PostgreSQL 18.3** (Debian 18.3-1.pgdg13+1, aarch64) |
| Image | `postgres:18.3` |
| Compose profile | `docker-compose-postgresql.yml` → `config/docker/compose/postgresql.yml` |
| Host port | `localhost:5432` |
| Databases | `fineract_tenants` (registry, 6 tables), `fineract_default` (281), **`fineract_gerege` (281)** |
| Schema size | 281 tables in `public` — the same in `fineract_default` and `fineract_gerege` |

### Tenants — READ THIS BEFORE YOU CAPTURE ANYTHING

**CORRECTED 2026-08-22 by the `/softhouse-program` driver (local fire `20260822-060013`), at repo
commit `c0be92b`.** The `Databases` row above previously named only `fineract_tenants` and
`fineract_default` and **omitted the string `fineract_gerege` entirely** — the tenant database the
ledger parity vectors were captured from. Re-derived live, evidence in
`.softhouse/capture/driver-20260822-060013/`.

**RE-DERIVED INDEPENDENTLY BY T245** at repo commit `9b6c596`; evidence and re-runnable instrument in
`.softhouse/reviews/t245-oracle-pin/`. The tenant table below is confirmed against
`tenants ⋈ tenant_server_connections`, and the six ledger vectors are confirmed — from the committed
capture artefacts and from the live rows, not by inference — to come from tenant `gerege`. **One
narrowing:** the pre-edit file *did* name the **tenant** `gerege`, on 7 lines including a whole section
headed *"The `gerege` tenant is the production-representative one"*; what was absent was the **database
name**, and the tenant-count figures the driver cited were true at `c0be92b` and have since moved
(P-69). Re-derive them rather than reading them:
`git grep -F -l -a fineract_gerege HEAD -- .softhouse/ | wc -l`.

| tenant id | identifier | name | timezone | database |
|---|---|---|---|---|
| 1 | `default` | Default Demo Tenant | **`Asia/Kolkata`** ⚠️ | `fineract_default` |
| 2 | `gerege` | Gerege T22 Audit Tenant (Asia/Ulaanbaatar) | **`Asia/Ulaanbaatar`** ✅ | `fineract_gerege` |

⚠️ **The two tenants are in different time zones and tenant 1 is not one of ours.** CLAUDE.md permits
exactly two zones, `Asia/Ulaanbaatar` (+08) and `Asia/Hovd` (+07), and hard-coded offsets nowhere.
`Asia/Kolkata` is **+05:30**. A capture taken against tenant `default` because this file named its
database and not the other one would be a capture at the wrong offset, and nothing downstream would
say so. **State the tenant, not just the database, in every capture attestation.** Both tenants are in
legitimate use across the corpus — `default` as the wrong-offset / `HALF_EVEN` **negative control** —
so the rule is not "never use `default`", it is **never leave which one unstated**. Neither
`.softhouse/vectors/PIN.json` nor `.softhouse/vectors/PIN-ledger.json` carries a tenant field today
[VERIFIED: T245, repo commit `9b6c596`]; making that a graded, default-deny field is proposed in
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T245.md` and is **not** implemented here.

### Driver assertions (asserted against the RUNNING container, not just config)

```
FINERACT_HIKARI_DRIVER_SOURCE_CLASS_NAME = org.postgresql.Driver      ✅
FINERACT_HIKARI_JDBC_URL                 = jdbc:postgresql://db:5432/fineract_tenants  ✅
FINERACT_DEFAULT_TENANTDB_PORT           = 5432                       ✅
```

### Prohibited-engine assertions — all clean ✅

| Check | Result |
|---|---|
| `ojdbc` / `oracle.jdbc` entries in `/app/fineract-provider.jar` | **0** |
| `mysql` / `mariadb` driver entries in the jar | **0** |
| Listener on port `1521` | none |
| Containers running | only `fineract:latest` (8443) and `postgres:18.3` (5432) |
| `ojdbc`/`oracle.jdbc`/`:1521`/`com.mysql.cj`/`mariadb`/`mysql` in the compose path | none |

Compose path audited: `docker-compose-postgresql.yml`, `config/docker/compose/postgresql.yml`,
`config/docker/compose/fineract.yml`, `config/docker/env/{fineract,fineract-common,fineract-postgresql,postgresql}.env`.
The mysql/mariadb compose files exist in the Fineract repo but are **never** used by this program.

## How this image was built

The host has **no JVM and no Homebrew**, so `./gradlew :fineract-provider:jibDockerBuild`
cannot run natively. `.softhouse/bin/build-oracle-image.sh` builds it reproducibly instead:

1. `:fineract-provider:bootJar -x test` inside `eclipse-temurin:21-jdk`, with a persistent
   `fineract-gradle-cache` volume and `GRADLE_USER_HOME=/gradle-home`.
2. The resulting boot jar is packaged onto `azul/zulu-openjdk-alpine:21` with the same
   workdir, entrypoint, JVM args and ports as Fineract's own jib config
   (`fineract-provider/build.gradle:314-344`), tagged `fineract:latest` — the tag
   `config/docker/compose/fineract.yml` expects.

**Build note (attempt 1 failed, recorded for the next fire):** Maven Central terminated TLS
handshakes mid-download under Gradle's default parallelism (`Remote host terminated the
handshake` on `spring-boot-starter-jdbc`, `spring-data-jdbc`, `opencsv`). Fixed with
`--max-workers=2`, longer HTTP timeouts, and a 3-attempt retry loop against the warm cache;
attempt 1 of the retry then succeeded in 1m55s. Do not "fix" this by disabling TLS verification.

## Bring up / tear down

```bash
cd /Users/buv/fineract
docker compose -f docker-compose-postgresql.yml up -d      # never the mysql/mariadb files
docker compose -f docker-compose-postgresql.yml down
```

Rebuild the image after moving the pin — same self-locating form as the toolchain activation line below, for
the same reason (the cloud fire has no `/Users/buv`):

```bash
"$(git rev-parse --show-toplevel)/.softhouse/bin/build-oracle-image.sh"
```

## Connection facts for vector capture

| Fact | Value |
|---|---|
| Base URL | `https://localhost:8443/fineract-provider/api/v1` (self-signed TLS — `curl -k`) |
| Auth | HTTP Basic `mifos:password` (verified: `GET /offices` → Head Office) |
| Tenant | **`gerege`** — tenant 2, `Asia/Ulaanbaatar`, `HALF_UP`. Header `Fineract-Platform-TenantId: gerege`, or query param `tenantIdentifier=gerege`; **both return HTTP 200 on `GET /offices`** [VERIFIED: T245, live, repo commit `9b6c596`]. |
| Postgres | **`psql -U root -d fineract_gerege`** inside `fineract-db-1` |
| Tenant `default` | **negative control only** — the wrong-offset / `HALF_EVEN` arm. Its database `fineract_default` holds **0 GL accounts, 0 journal entries, 0 loans** [VERIFIED: T245, live, repo commit `9b6c596`], so a capture pointed there does not merely run at `+05:30`, it finds no ledger at all. |

**CORRECTED 2026-08-22 by T245**, the independent review of the driver's own tenants correction above,
measured at repo commit `9b6c596`. The `Tenant` and `Postgres` rows previously read
`tenantIdentifier=default` and `psql -U root -d fineract_default`. That is not a record of a negative
control — it is **the capture instruction**, in the file that says every capture must cite it, in the same
file as (and ~60 lines below) a warning describing exactly that hazard. The fire that added the warning
did not remove the instruction. T245 swept all 5,129 tracked files for a copyable
instruction naming tenant `default`: **10 files carry one, and 9 of the 10 are deliberate negative
controls** (the `t22-probe` / `t22-audit` arms, `t149`'s `HALF_EVEN` arm, `t246`'s population-scope
control). **This file was the only prescriptive one.**

## ⚠️ Findings that affect vector capture (T8)

1. **The seeded default tenant's timezone is `Asia/Kolkata`, not a Mongolian zone.**
   ```
   tenants: default | Default Demo Tenant | Asia/Kolkata
   ```
   The vector matrix requires both `Asia/Ulaanbaatar` (+08) and `Asia/Hovd` (+07). T8 must
   either provision tenants with those zones or drive the generator with an explicit tz per
   case — and must record the tz actually in force on every captured vector. Never let a
   capture inherit `Asia/Kolkata` silently. Note the JVM also runs `-Duser.timezone=UTC`,
   so there are three timezones in play; the capture must pin which one the schedule used.

2. **MNT is seeded correctly** — `m_currency`: `MNT | decimal_places=2 | Mongolian Tugrik`,
   consistent with ISO 4217 numeric 496, minor unit 2.

3. **The schedule generator under port is an embeddable library, not a REST endpoint.**
   `fineract-progressive-loan-embeddable-schedule-generator` is invoked in-process
   (see its `misc/Main.java`). T8 should plan to capture vectors by driving that class on
   the pinned JVM, not only through the REST API — and must capture the raw output at full
   returned scale alongside the contract-shaped form.

4. **`JAVA_TOOL_OPTIONS` carries a JDWP debug agent and `-XX:TieredStopAtLevel=1`.** These
   affect JIT and debugging only, not `BigDecimal` arithmetic, so captured numbers remain
   valid. Noted so nobody attributes a future mismatch to them. (`java -version` run *inside*
   the container fails with `transport error 202: bind failed` for this reason — the version
   above was read from the base image.)

## Reproducibility rule

Every file under `.softhouse/vectors/` must stamp the Fineract commit
`426a23544e8426a38ae43ae404670a0a7e85b9eb` and PostgreSQL `18.3`. If this file's pin changes,
previously captured vectors are stale and must be re-captured — never re-interpreted.

---

## Fire log — reachability is a per-fire fact, never a global one

| Fire | Oracle reachable? | Evidence |
|---|---|---|
| local `20260817-*` | **yes** | server UP on PostgreSQL 18.3; driver assertions passed |
| cloud `20260817-2000` | **no** | no Docker daemon, nothing on `:5432`, `actuator/health` silent → T8 parked `oracle_unreachable`; nothing synthesised |
| local `20260818-080003` | **yes** | capture pass 1 executed (killed mid-run by the Mac sleeping; output rescued) |
| local `20260818-140004` | yes | killed by sleep before dispatching work |
| local `20260818-152328` | **yes** | capture pass 2 executed; `caffeinate` now holds sleep off |
| local `20260818-170002` | **yes** | Path B first used for capture (B-01…B-04) |
| local `20260818-173900`, `20260818-200001` | yes | **workers killed by the harness's 600 s background-task ceiling**, not by the oracle — see the root-cause note below |
| cloud `20260818-2000` | **no** | expected; spent entirely on oracle-free contract work |
| local `20260818-230002` | **yes** | **the fire that closed every open admissibility P0**: Path A attested + re-emitted (T35), Path B attested, re-pointed and re-captured (T36), and DEC-1 §8's five binding shapes captured (T37). Ceiling fix landed in `fire-program.sh`. |
| local `20260819-080001` | **yes** | `actuator/health` → `{"status":"UP"}`; `fineract-fineract-1` (fineract:latest) and `fineract-db-1` (postgres:18.3) both healthy; pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` verified clean (`status --porcelain` empty); no prohibited-engine port open. Spent on T39 (observe the `periodRatio` drift region, Path A throwaway containers) and T40 (first charge-bearing captures, Path B, sole server owner), alongside oracle-free T38 (DEC-1 v7). |

| local `20260822-080001` | **yes** | Driver re-asserted the DATABASE NON-NEGOTIABLE against the running stack rather than inheriting the wrapper's probe: `actuator/health` -> `{"status":"UP","groups":["liveness","readiness"]}`; `fineract-fineract-1` (fineract:latest) and `fineract-db-1` (postgres:18.3) both healthy (up 3-4 days); `select version()` inside the container returns **PostgreSQL 18.3 (Debian 18.3-1.pgdg13+1) aarch64**; the provider's own env carries `FINERACT_HIKARI_DRIVER_SOURCE_CLASS_NAME=org.postgresql.Driver` and `FINERACT_HIKARI_JDBC_URL=jdbc:postgresql://db:5432/fineract_tenants` -- **asserted, not assumed**. Prohibited-engine sweep: `find /` inside the provider container for `*ojdbc*` / `*mysql*jar` / `*mariadb*jar` returns **nothing** (the image ships one jar, `/app/fineract-provider.jar`), and no host listener on `:1521` / `:3306` / `:33060`. Conformance baseline re-run by the driver BEFORE dispatch: probe line **PRESENT and reading `up`**, `VERDICT: PASS (exit 0)`, **43 parity vectors / 5664 cells**, 0 invariant violations, 0 assertions NOT RUN. Vector store: 50 `.json` files, tree digest `5d03795b604294af0f2da3c0df2afbc0d6abe38c3ee47761739fdc80cd4c6120`. |

## Two distinct capture paths — do not conflate them

Vector capture in this program can reach the oracle two ways, and they are **not equivalent**.
Every captured vector must record which path produced it.

### Path A — the embeddable seam (in-process library call)

`fineract-progressive-loan-embeddable-schedule-generator` invoked in-process on the pinned image.
**Reaches no database at all** — no server, no PostgreSQL. This is what capture passes 1 and 2 used.

| Fact | Value |
|---|---|
| Image | `fineract:latest` = `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` |
| Image created | `2026-08-17T11:29:56Z` |
| JVM (read *inside* the container) | `openjdk 21.0.11 2026-04-21 LTS`, Zulu21.50+19-CA, build `21.0.11+10-LTS` |
| Classpath | `BOOT-INF/classes` + `BOOT-INF/lib/*.jar` from `/app/fineract-provider.jar` |
| Seam class | not bundled in that jar — compiled from source, and **must** be verified byte-identical to the pinned original before any run is trusted |
| Ambient `MoneyHelper` context | `PRECISION = 19` + the tenant's configured rounding mode; read from the running oracle, not from source |
| Tenant | must be supplied explicitly (`ThreadLocalContextUtil.setTenant` + `MoneyHelper.initializeTenantRoundingMode`); without one, any path touching `MoneyHelper` throws |

Reproduction commands: `.softhouse/capture/README-pass2.md`.

**Path A has a proven blind spot.** `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
(`LoanApplicationTerms.java:579-606`) reads 18 of the record's 19 components and never reads
`installmentAmountInMultiplesOf`. That input is therefore **accepted and silently dropped** on this path,
while the server path honours it. Any behaviour depending on it is **uncapturable through Path A** —
see `.softhouse/capture/PASS2-REPORT.md`, Finding 2. Multi-disbursement behaviour is likewise out of reach
(`disbursementDatas` is a fixed empty list at `LoanApplicationTerms.java:600`).

### Path B — the running server (REST + PostgreSQL)

The connection facts at the top of this file. **FIRST USED FOR CAPTURE, fire `20260818-170002`** — four raw
observed captures under `.softhouse/capture/pathb/`, recipe in that directory's `REPRODUCE.md`, findings in
`PATHB-REPORT.md`. **INDEPENDENTLY AUDITED by T22 (2026-08-18) — ACCEPTED WITH REQUIRED CHANGES**, the audit
re-checked by T27 and its oracle-independent corrections applied; `B-03`/`B-04` additionally re-derived from
the pinned source by T30 (`.softhouse/reviews/t30-probe/`). ~~Three P0 admissibility items are still open~~ — **ALL FOUR T22 P0s ARE NOW CLOSED** by task **T36**
on local fire `20260818-230002` (P0-3 attestation sidecar, P0-4 fail-the-run preconditions, P0-5 already
closed by T30, P0-6 re-point at a production-settings tenant + re-capture). See the T36 block below.
Still: audited observations, **nothing promoted to the vector store** — gate **G-1** (DEC-1 unratified)
is the remaining blocker, and promotion is not a capture task's call.

It is the **only** path that can close Path A's blind spot, and it is a materially larger rig than Tier 0
assumed: it needs tenants provisioned with the right timezones (see finding 1 above), and every capture must
stamp the tz actually in force.

**Path A's blind spot is now measured, not merely suspected.** Both inputs Path A drops are **honoured by
the server and move money**:

| Input | Path A | Path B | Observed effect |
|---|---|---|---|
| `installmentAmountInMultiplesOf` | dropped (never read by `assembleFrom`) | **honoured** | `100` → EMI `112,082.37` → `112,100.00`; 12/12 periods differ; final installment absorbs the residual (`111,866.22`) |
| `daysInYearCustomStrategy` | dropped (never copied by `Builder` copy-ctor `:304-351`) | **honoured** | `FULL_LEAP_YEAR` `144,659.21` vs `FEB_29_PERIOD_ONLY` `145,011.43` total interest; 12/12 periods differ |

Consequence for the harness: **a conformance suite built on Path A alone cannot grade either field.** It
would score a Go port identically whether it implemented them or ignored them. Contract clauses touching
these fields require Path-B vectors.

Path B also **corroborates** Path A: capture `B-01` reproduces pass-3 `P-MNT-1M2` to the minor unit
(`144,988.47` / `1,344,988.47`) through an entirely different seam into the same pinned image digest. The
Path A corpus is therefore not an artefact of the embeddable seam.

**Path B capture facts, fire `20260818-170002`:**

| Fact | Value |
|---|---|
| Endpoint | `POST /loans?command=calculateLoanSchedule` |
| Auth | Basic, stock demo `mifos:password` |
| Tenant | `default` — timezone **`Asia/Kolkata`** (stock demo, NOT a Mongolian tz) |
| PostgreSQL | 18.3 (Debian 18.3-1.pgdg13+1), aarch64 |
| Driver asserted | `org.postgresql.Driver`, `jdbc:postgresql://db:5432/fineract_tenants` |
| Image digest | `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` (identical to Path A) |
| Currency | MNT enabled, decimalPlaces 2 |

**Two Path B gaps that must close before it yields parity vectors:** (1) the tenant timezone is
`Asia/Kolkata`, so no clock-sensitive capture is valid until a Mongolian tenant exists; (2) tenant rounding
mode and precision are **not asserted per capture** the way Path A pins `(19, HALF_UP)` — until they are,
Path B captures are discrimination evidence, not production-settings parity vectors.

## Reproducibility rule, extended

A capture is only comparable to another capture from the **same path, same image digest, same commit**.
A jar built on a different JVM is not the pinned oracle. Promoting a new capture path to a trusted source
is a `user` decision, not an agent's.

---

## Attested capture facts — local fire `20260818-230002`

This fire moved the corpus from *audited* observations to **attested** observations on both paths, and
captured DEC-1 §8's five binding shapes. Every value below was **measured from the running oracle, its
container, its deployed bytecode, or its PostgreSQL rows** — none is inferred from the source tree.

### Provenance, now measured rather than assumed

| Fact | Value | How it was read |
|---|---|---|
| Fineract commit | `426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git.dirty=false` | the deployed jar's own `git.properties` (T35); `git.commit.id` via the server (T36) |
| Image | `sha256:e596339626bf…0459a` | `docker image inspect`, asserted by the runner |
| Jar sha256 | `60fb6dbd…f4c9` | inside the container (T35) |
| JVM | Zulu OpenJDK `21.0.11+10-LTS`, **zero JVM input flags** | inside the container (T35) |
| `MoneyHelper.PRECISION` | **19** | `javap` on the deployed `fineract-core` jar (T36); read in-process (T35) |
| Effective `MathContext` | **(19, HALF_UP)** — ordinal **4** | the oracle's own SLF4J init lines *and* `MoneyHelper.getMathContext()` |
| PostgreSQL | **18.3** | server row (T36) |
| Classpath | 350 entries digested individually — contains `postgresql-42.7.11.jar`, **zero** Oracle/MySQL/MariaDB | T35 |

**This is the ratified production setting**, so there is no adverse "ran at the wrong precision or mode"
finding on either path this fire.

### The `gerege` tenant is the production-representative one

`timezone_id = Asia/Ulaanbaatar`, `c_configuration.rounding-mode = 4` (HALF_UP), empty
`schema_connection_parameters`. Finding 1 above (the seeded `default` tenant is `Asia/Kolkata`) still
stands and is now *enforced* rather than merely warned about: T36's `preconditions.sh` (15 assertions)
**exits non-zero and names the breach**, and is **proven failable** — run against stock `default` it exits 1
with five breaches (Kolkata, mode 6, HALF_EVEN in force, MySQL-era connection params, and a behavioural
half-cent canary returning `20925.04` instead of `20925.05`). Those five are exactly the defects that made
the earlier corpus inadmissible. A DB row is not proof of the arithmetic in force; the canary is.

`MoneyHelper.updateTenantRoundingMode` has **no production caller**, so a cached tenant rounding mode
cannot drift without a container restart (T35, T27 RC-6).

### Re-capture result — the committed Path B corpus is stable

T36 re-captured `B-01`…`B-04` **twice** on the `gerege` tenant (byte-verbatim requests against the existing
products, then again against four products it re-created). **All four responses byte-identical to the
committed corpus, all eight times**; a number-by-number diff over every JSON leaf in exact integer minor
units gives **0 numbers moved, 0 scale-only, 0 structural**. T30's from-source re-derivation of `B-03`/`B-04`
re-checked at both rounding modes: **consistent, no contradiction.**

Path A likewise: unmodified `Capture3.java` reproduced the committed capture **byte for byte** on this fire,
and the re-emitted pass 3b gave **1560 / 1560 published values identical, 0 changed, 0 dropped** — the only
additions being `balance` on `DISBURSEMENT` rows, which pass 3 never emitted at all. Switching emissions to
`toPlainString()` changed nothing, not even rendering. Run-stable digest `02e94174…aa38ec` over three runs.

### New behavioural facts observed this fire

- **The EMI re-adjust loop can be made to fire, and now has been.** At `n = 12` the entry condition needs
  `|residual| > 0.06`, because the right-hand side is `Money(6.00)` — `Money.copy(double)` **replaces** the
  amount (`Money.java:219-221` → `:215-217`), it does not scale it. Six captures refute the no-loop model by
  one minor unit on all of periods 1–11 (principal `1,200,001₮` → observed EMI **112,082.46**, no-loop model
  `112,082.47`); two more enter the loop and back out at `hasLessEmiDifference`, pinning that guard too.
- **`totalOutstandingAmount` carries no information on this path** — `"0"` at **scale 0** while every other
  money string is scale 2. Not rounding: `final BigDecimal totalOutstanding = BigDecimal.ZERO`
  (`ProgressiveLoanScheduleGenerator.java:157`), passed straight through.
- **The corpus has zero discriminating power over charges** — every fee and penalty in it is `0.00`.

### Path C in all but name — the DEC-1 binding captures

`.softhouse/capture/dec1-binding/` holds eleven captures taken through the Path A seam that exist to
**separate readings**, not to sample behaviour. Both controls passed (a shipped test literal reproduced
digit-for-digit at `(12, HALF_UP)`; committed observation `Q0a` reproduced through a *different* harness),
the run is byte-identical on re-execution, and the seam-class `diff` was empty.

The widest single observation in the program to date: a port hard-coding the rate-factor day-count ratio to
1 charges period-1 interest **21,600.00** where the oracle returned **11,845.16** — an **observed** gap of
**MNT 10,195.09** in total interest on a MNT 1.2 M loan.

**Stored in raw observed form only.** Gate G-1 is open, so contract-shaped storage and promotion to the
parity vector store both remain forbidden.

---

## Root cause of the "lost local fire" pattern — fixed 2026-08-18

Four local fires (`20260817-191707`, `20260818-080003`, `-170002`, `-200001`) stranded worker output. The
diagnosis carried in `RESUME.md` — *"`fire-program.sh` dispatches and exits without awaiting its workers"* —
was **wrong**. Every one of those logs carries the harness line:

```
Background tasks still running after 600s; terminating.
Set CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 to wait indefinitely.
```

`claude -p` waits only 600 s for background tasks after the driver's final response and then **kills them**.
The driver awaited its workers correctly; the harness killed them underneath it. An opus worker re-deriving
money math or building a capture container routinely needs 20–25 minutes, so the ceiling is removed, not
raised: `fire-program.sh` now exports `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` before invoking the driver.

**This has nothing to do with the reference oracle**, and it is recorded here only because it repeatedly
destroyed oracle work that no other fire can redo.

---

## Which `MathContext` governs — the T42 attestation rule (fire `20260819-080001`)

Task T42 settled, **by observation against the live pinned oracle**, a question the program's earlier
attestations answered partly wrong. The values in every committed capture are **unaffected**; some of
the *justifications* were not evidence about money. Full derivation, negative runs and digests:
`.softhouse/handoff/T42-mathcontext-inforce.md`.

**1. Name the two contexts separately.** Never write "the `MathContext` in force" without saying which.
- **THREADED** = the `MathContext` object actually passed to the arithmetic (`generate(mc, …)`,
  `scheduleModel.mc()`, `Money.of(…, mc)`).
- **AMBIENT** = `MoneyHelper.getMathContext()` for the current tenant.

**2. On the THREADED context, echo the object, not the intent** — `mc.getPrecision()`,
`mc.getRoundingMode()`, `mc.toString()`, read off the reference handed to the callee. This is the
reading that is evidence about arithmetic.

**3. On the AMBIENT context, state what it witnesses and what it does not.** It witnesses that the
tenant was configured as ratified. It is evidence about the arithmetic **only where the caller sourced
the threaded context from it** — and then the wiring must be cited.

**4. State the WIRING explicitly, per capture path:**

| path | wiring | is the ambient reading evidence about the money? |
|---|---|---|
| **Path B** — running server | `LoanScheduleAssembler.java:753` and `LoanScheduleGeneratorServiceImpl.java:44` do `mc = MoneyHelper.getMathContext()` and pass it to `generate(mc, …)` — **the same object**. **(Corrected by T46: `:777` and `:797` were listed here originally and do NOT call `generate`; five wiring sites are now cited and verified in the charges set.)** Read off the **deployed bytecode** in `fineract-fineract-1`, digest `d5ef39897399157de96503dd242f0f999acde87bf59a191c812ab2f3547711ea`. | **Yes** — it *is* the threaded context. Cite the wiring; never leave it implicit. |
| **Path A** — embeddable seam | the harness constructs its own `mc`. The two are **independent variables**. | **No** — it witnesses the tenant configuration only, which is still worth attesting for exactly that. Plus the one leak in rule 5. |

Measured side by side in one payload: moving the tenant ordinal 4 → 1 moves **0 cells** under the Path A
wiring and **23 cells** under the Path B wiring.

**5. The one Path A ambient leak.** The ambient context still reaches money at exactly one site on the
graded call graph — `Money.<init>` [`Money.java:50`] → `roundToMultiplesOf(BigDecimal, Integer)`
[`Money.java:154`] → `MoneyHelper.getRoundingMode()` [`MoneyHelper.java:79`] — **ignoring the `mc` it was
handed**. Reached only when the currency has **0 decimal places** *and* a positive `inMultiplesOf`.
**MNT has 2, so no ratified MNT capture reaches it.** A capture that changes the currency's decimal
places must re-attest the ambient context as load-bearing, and **a Go port must reproduce this site if
it ever supports a 0-dp currency with an `inMultiplesOf`.**

**6. A configuration echo is not a discriminator — carry a behavioural canary**, a value that differs by
rounding mode, for whichever context the attestation claims governs. On Path B, T36's half-cent tie
(`1,162,502.50 × 0.018 = 20,925.045` → `20925.05` under `HALF_UP`, `20925.04` under `HALF_EVEN`) is the
right one and already exists. On Path A the canary must move the **threaded** mode; the cheapest is
`76723.70 → 76723.65` on the plain 6 × 21.6 % MNT 1,200,000 shape.

**7. The PRECISION half of `(19, HALF_UP)` can never disagree with the source** — `MoneyHelper.PRECISION
= 19` is a compile-time constant [`MoneyHelper.java:35`] and only the mode is tenant-configurable.
Echoing it is a **provenance** claim, not a discrimination — but it is now discriminable behaviourally
(next section).

**8. `(19, tenant mode)` is the LOAN-PATH rule, not a Fineract-wide one.** See N-3 below.

### The decisive experiment: ABSENCE beats DIFFERENCE

T39 tested the ambient context by *changing* it and watching for movement. T42 replaced that with an
**absence** test: register a tenant in `ThreadLocalContextUtil` but never pass it to
`initializeTenantRoundingMode`, so **any ambient read throws**. Schedules still generated — on **11 of
13** probe shapes the ambient context is **provably never read at all**, which is a stronger statement
than "changing it moved nothing". A canary proves the probe is not vacuous, and a negative leg inverts
the guard and confirms it fires. **Prefer an absence probe to a difference probe when you can build one.**

### Precision 19 is now OBSERVABLE, not merely transcribed

T39's N-4 ("threaded precision 19 vs 12 is indistinguishable") is **superseded**. A separating shape
exists and it is an ordinary loan:

| shape | total interest at threaded precision 19 | at precision 12 | gap | cells differing |
|---|---|---|---|---|
| MNT 50,000,000 / 360 months / 21.6 % | **274,527,298.56** | 274,527,296.51 | MNT 2.05 | 861 |
| MNT 25,000,000 / 360 months / 7.7 % | — | — | — | 610 |

Buyan's ratified precision-19 parameter is therefore **observably load-bearing**. Three caveats, stated
because they change how the result may be used: separation is **not monotone in principal** (25M
separates, 30–70M do not, 80M does), so **there is no safe threshold**; 19-vs-8 separates almost
everywhere and was never the hard case; and T39's N-4 was not wrong — its 16 shapes simply never reached
the 360-period regime.

### Amendments to earlier attestations — values unaffected, justification corrected

No committed capture is **mis-valued** — T42 demonstrated this in three legs rather than asserting it, and
T44 re-checked it. **Qualified by T46:** "not mis-valued" is not the same as "correctly justified", and it is
scoped to the arithmetic these captures actually exercise — it says nothing about the **ambient** rounding
locus found on the charge path (next section). The three legs were (the
threaded context was independently echoed in T35/T37/T39; the sole Path A ambient site is unreachable at
2 dp; and no committed payload uses a 0-dp currency).

- **T37 §5 is the wrong one** — its "two independent witnesses" to the effective `MathContext` are
  **both ambient**, i.e. one witness counted twice.
- **T35** — "effective" should read "**ambient**".
- **T39 — added by audit T44 (F39-2), which T42's original list missed.** T39's attestation offers "two
  independent witnesses" that are **both ambient**, and are in fact **one cache write logged and then read
  back** [`MoneyHelper.java:59-64`, `:91-94`] — T37's defect exactly. **Corrected by T46**, which re-emitted
  the threaded `MathContext` read **off the object** with **2072 / 2072 published values identical** and no
  new case in that pass.
- **T36 is substantially sound**: its half-cent canary is real behavioural evidence, and on Path B the
  ambient **is** the arithmetic. It needs only the wiring citation added.

### Two findings that reach beyond Tier 0

- **`(19, tenant mode)` is a LOAN-PATH rule.** **Inventory corrected by audit T44 (findings M-1, M-2) —
  the figures first recorded here were wrong, and an inventory is the one part of this a porter actually
  uses.** What holds, re-counted independently by both of T44's audit legs: **81** `MathContext.DECIMAL64`
  uses (49 `fineract-core` + 31 `fineract-provider` + 1 `fineract-savings`), **0 in any loan module** and
  **0 outside a savings/deposit path**. What was wrong: the total for explicit `new MathContext(…)` sites
  is **9**, not the 13 recorded here (4 × precision **15** and 5 × precision **10**; the original figure
  double-counted the 15s by listing the union as though all nine were 10s). And the universal claim
  *"everything outside the loan modules is in savings/deposits"* is **false** — two
  `new MathContext(8, MoneyHelper.getRoundingMode())` sites were omitted entirely:
  `SavingsAccountCharge.java:562` (`fineract-savings`) and **`ShareAccountCharge.java:240`, which is in
  `portfolio/shareaccounts/` — share accounts, a separate Tier B context with its own precision.**
  A porter reading the original wording would carry `(19, HALF_UP)` into share accounts and be wrong
  there too, which is exactly the error this finding exists to prevent. **This matters for Tier B and is
  not a Tier 0 problem.**
- **One loan-path site hard-codes `RoundingMode.DOWN` over the tenant mode** —
  `AdvancedPaymentScheduleTransactionProcessor.java:2845`, in repayment allocation, **invisible to every
  capture the program currently holds**. `TO_BE_CAPTURED`.

### Later corrections — the ambient context reaches further than the loan schedule (T46)

- **N46-1 (P1, open).** The **charge** rounding mode is **AMBIENT, not threaded**. Re-derived to its locus:
  `ProgressiveLoanScheduleGenerator.java:445-446` → the two-arg `Money.of` → `Money.java:114-116` →
  `Money.java:52` `setScale(2, getMc().getRoundingMode())`. This is a **second** ambient leak on the graded
  call graph, distinct from the 0-dp `inMultiplesOf` one, and unlike that one **it is reachable at MNT's 2
  decimal places**. Two exact half-cent ties were *observed* on it (`4.725 → 4.73`, `2.025 → 2.03`, both
  `HALF_UP`), which also **refutes** the charges set's original claim that no half-cent tie was possible.
  **No capture the program holds can detect the mode here** — separating it needs a tenant write, so it is
  `TO_BE_CAPTURED`.
- **T46-N1.** Six loan-path `MathUtil.percentageOf(…, 19)` sites also take the **ambient** mode.
- **M-4 (T44).** `LoanScheduleGeneratorServiceImpl:56, :63` **also drops** `installmentAmountInMultiplesOf`,
  so that field is honoured or lost **by caller** — a capture seam's blind spot is a property of the caller,
  not of the field.

**What this means for rule 4 of the attestation rule above:** the Path A row said the ambient reading is *not*
evidence about money "plus the one leak in rule 5". That is now **two** leaks, and the second one bites at
MNT's scale. State both, or state the rule as *"attest the threaded context, and enumerate the ambient leaks
you have actually searched for"* — the enumeration has now been wrong twice (T43 P1-T43-2, and this), which is
itself the argument for not resting a conclusion on an exhaustiveness claim.

---

## Environment gap found by local fire `20260819-140003` — **no Go toolchain on this host**

**`go` is not on `PATH` and no Go installation exists on the machine** [VERIFIED by the driver this fire:
`which go` → not found; no `/usr/local/go`, no Homebrew `go` cellar, no `go` binary under any `*/bin/go`].
Task T52 reported the same from inside its worktree, independently.

### What this does and does not block

**Does not block anything this fire did.** Every task run so far is analysis, capture, review or ADR text.
The Fineract reference oracle, PostgreSQL, Docker and the pinned checkout are all healthy and untouched by
this gap.

**Becomes the critical path the moment G-1 closes.** `CLAUDE.md` § Verification defines a PASS as
`go build ./...`, `go test ./...`, the conformance run and property invariants. Without a toolchain:

- **T7** (build the conformance harness) can be designed but not executed against Go.
- **T10** (port the schedule generator) cannot be compiled, so no `coder` task can honestly report green.
- **T11**, **T13** (`/softhouse-uat`) cannot run at all — and a UAT that cannot run must **never** be
  recorded as a pass.

### The consequence for `contract.go`, stated precisely

`nexus/internal/apps/loanschedule/contract/contract.go` holds **96 non-comment lines** of real Go — package
clause, three imports, types, enum constants and error values — and **it has never been compiled**, on this
host or (as far as the repo records) any other. Nine review rounds have graded its *comments*; nothing has
ever graded whether it *builds*.

A static sanity check by the driver this fire found all three imports (`context`, `errors`, `fmt`) used at
least once — Go rejects unused imports — and no duplicate top-level `type`/`func` declarations. **That is a
heuristic, not a compile, and it is recorded as one.** `[UNVERIFIED: that the package compiles]`.

This matters for ratification only in one narrow way, and it should not be overstated: DEC-1 freezes the
contract's *shape and semantics*, which nine rounds have graded from source and vectors. It does not freeze
a build result. But **the first fire with a toolchain must run `go build ./...` before any Go is written
against this file**, because a syntax or type error in a ratified artefact is discovered at the worst
possible moment.

### What is needed, and whose call it is

One toolchain install (`brew install go`, or the official tarball into `/usr/local/go`). `nexus/go.mod`
already declares `module github.com/gerege/nexus`, `go 1.23`.

This is **not** a RESERVED item under `CLAUDE.md` § Answering gates — it spends no money, exposes no
endpoint and binds Gerege to nobody. It is ordinary developer setup and the driver would normally just do
it. **It was deliberately NOT done unattended**, because installing software on Buyan's machine is a
durable change to the host rather than to this repo, and no fire had been asked to make one. It is
surfaced here and in `RESUME.md` instead. **A fire that is told "you may install a Go toolchain" should
just do it and record the version here.**

---

## Environment gap CLOSED by local fire `20260819-170001` — **repo-local Go toolchain, host untouched**

The gap above is **closed**, and closed in a way that does not make the durable change to Buyan's machine
that the previous fire (correctly) declined to make unattended.

### What was installed, and where

| Fact | Value |
|---|---|
| Version | **`go1.26.6 darwin/arm64`** (`go version` output, verbatim) |
| Source | `https://go.dev/dl/go1.26.6.darwin-arm64.tar.gz` — the official archive, from `https://go.dev/dl/?mode=json` |
| Size | 64,772,321 bytes |
| **SHA-256 asserted before extraction** | `2dc95ce4675829f2df0e86b28bcef3283635902062a5f0580ca659bf570f3204` — **published value and computed value MATCHED**; the driver would not have extracted an archive that did not match |
| `GOROOT` | **derived, never written down**: `$GEREGE_TOOLCHAIN/go`, where `GEREGE_TOOLCHAIN` = `<main checkout>/.softhouse/toolchain`. On the local fire's host that *resolved to* `/Users/buv/gerege-nbfi/.softhouse/toolchain/go`; that is an observation of one host, **not a value to paste**. |
| `GOPATH` / `GOCACHE` / `GOMODCACHE` | `$GEREGE_TOOLCHAIN/{gopath,gocache,gomodcache}` — same derivation |
| Committed to git? | **No** — `.softhouse/toolchain/` is in `.gitignore` |
| **Activation** | the single line in the block immediately below — copy it verbatim; it is the whole instruction |

<!-- T256-ACTIVATION-LINE:BEGIN
     THIS BLOCK IS EXECUTED, NOT JUST READ.
     .softhouse/capture/t256-toolchain-population/instruments/30-portability-red-drive.sh
     EXTRACTS the line between these two markers and RUNS it, on this host and inside a
     scratch checkout that has no toolchain. So this is not a sentence a future fire has to
     remember to obey — replace it with a host-pinned path and the drive goes red off-host,
     in a transcript, with the offending line quoted back. Keep it to one line. -->

```bash
. "$(git rev-parse --show-toplevel)/.softhouse/bin/go-env.sh"
```

<!-- T256-ACTIVATION-LINE:END -->

#### The activation line is host-free on purpose — do not "simplify" it back to a path

This row used to read `. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh`. That was a defect of the
**instruction**, not of the toolchain, and it is the kind that reproduces: this program is driven by **two**
fires — a launchd fire on Buyan's Mac, and a **cloud fire that never runs on that host** — so every worker who
followed the old line wrote a script the cloud fire structurally could not execute. **At commit `f02d849`,
60 archived instruments in this repo carried that paste** — a figure pinned to the commit that produced it,
because a count restated without one rots. (Measured, not remembered: re-run
`.softhouse/capture/t256-toolchain-population/instruments/10-population-census.sh`, which re-derives every
figure from the tree it is run against and prints the selector beside each one. If this sentence and that
output disagree, the output is right.)

The replacement is **self-locating**: `git rev-parse --show-toplevel` answers correctly from any working
directory, in the main checkout and in every isolated worker worktree, on any host, and names no user and no
machine. It asks the reader to remember **nothing** — there is no variable to set first and no path to know.

**It composes with `go-env.sh` rather than duplicating it.** `go-env.sh` is the seam that finds the toolchain;
it resolves the *shared* install through `git rev-parse --git-common-dir`, so a worktree gets the main
checkout's one toolchain and one module cache. Never re-implement that here — `export GOROOT=…` in a script of
your own is exactly the paste this section exists to stop.

**What it does when the toolchain is absent — verified, not assumed.** `go-env.sh` never exports a `GOROOT`
that does not exist, drops a stale inherited one, and prints an unmissable stderr banner naming the paths it
searched. If a `go` exists on `PATH` it announces the substitution and sets `GEREGE_GO_SOURCE=fallback-path`;
if none does it sets `GEREGE_GO_SOURCE=absent` and says so, leaving the caller's own fail-closed refusal to
fire accurately. Guards may build with a fallback toolchain; **vector capture and any parity claim may not.**
Drive these paths yourself with
`.softhouse/capture/t256-toolchain-population/instruments/30-portability-red-drive.sh` — transcript beside it
in `evidence/`. A guard nobody has watched fail enforces nothing.

### Why repo-local rather than `brew install go` or `/usr/local/go`

The previous fire's reasoning was right and is preserved, not overridden: this is **not** a RESERVED item
(no money, no live endpoint, no third-party binding), so under `CLAUDE.md` § *Answering gates* the driver's
default is *choose and act*. What made it awkward was only that a host install is a **durable change to
Buyan's machine**.

A repo-local `GOROOT` removes exactly that objection:

- **Nothing outside this repo is modified.** No `/usr/local`, no Homebrew (there is no Homebrew on this
  host — `command -v brew` → not found), no shell profile, no `PATH` change for any interactive shell.
- **One command fully reverses it:** `rm -rf .softhouse/toolchain`.
- **It is not committed**, so it cannot bloat the repo or reach the cloud fire, which does not need it.
- **Worktrees share it.** `go-env.sh` pins `GOROOT` to an ABSOLUTE path in the main checkout, so every
  isolated worker worktree uses one toolchain and one module cache instead of downloading its own.

**A future fire on a fresh clone will find no toolchain and must re-run the download.** That is the price of
not touching the host, and it is cheap: one verified 65 MB fetch. If Buyan would rather have `go` on the
host PATH, that is a one-line change and this section explains what it would replace.

### `contract.go` COMPILES — the ten-round shape grading is not invalidated

The ratified artefact was compiled for the first time in the program, immediately, before any Go was
written against it:

```
$ . .softhouse/bin/go-env.sh && cd nexus
$ go build ./...    → exit 0     (no output)
$ go vet  ./...     → exit 0     (no output)
$ go test ./...     → exit 0     ("no test files" — there are none yet)
```

So `[UNVERIFIED: that the package compiles]` is **retired and replaced by `[VERIFIED: exit 0]`**. The
heuristic the previous fire recorded (three imports used, no duplicate top-level declarations) was right,
and the worst-case discovery it warned about — a type error frozen into a ratified artefact — **did not
happen.** `go vet` clean additionally means no printf-verb, shadow or struct-tag defects in the contract.

### ONE new finding: `gofmt` wants to rewrite the FROZEN contract — do not let it happen silently

`gofmt -l` flags `internal/apps/loanschedule/contract/contract.go`. The diff was captured and **deliberately
NOT applied.**

- **Extent:** 3 hunks, 25 diff lines. Every one inserts a bare `//` line **between numbered list items inside
  doc comments** — Go 1.19+ doc-comment list normalisation.
- **Semantically inert:** no type, field, enum member, error value, identifier or specified predicate moves.
  The change is confined to comment whitespace structure. (Note the mechanical check "identical after
  stripping all whitespace" reports **NO** — because gofmt inserts new `//` tokens, which are non-whitespace
  bytes. The tokens it inserts are empty comment markers, so the *prose* is unchanged; do not misread that
  check as evidence of a substantive edit.)
- **Why it is a finding rather than a nit:** the doc comments in this file **are the specification**
  (`contract.go` package comment, §*Amendment gate*), and post-ratification "re-documenting any identifier in
  this package" needs a gate. So an editor-on-save `gofmt -w`, or a `coder` who runs `gofmt ./...` from the
  repo root, would **silently mutate a frozen, ratified artefact** — and the diff would look like harmless
  formatting noise in review.

**Standing instruction until the gate is answered:** no task may run `gofmt -w`, `go fmt`, or an
IDE format-on-save over `internal/apps/loanschedule/contract/contract.go`. Format only the files you
created. `gofmt -l` reporting this one path is the EXPECTED state, not a defect to fix, and a UAT must not
fail on it. Raised as gate **G-3** in `.softhouse/gates.md` (ENGINEERING, driver-decidable, deliberately not
self-answered because the artefact is frozen).

---

## Driver findings, local fire `20260819-170001` — re-derived from the pinned source, not taken on report

Both items below were established by the driver reading `/Users/buv/fineract` at commit `426a23544`
directly, while Wave 1 workers ran. Line numbers are from that commit.

### D-1 (correction) — T50-N2's citation is `:83`, not `:81`

The hard-wired call is at **`ProgressiveLoanScheduleGenerator.java:83`**:

```java
83:        return LoanSchedulePlan.from(generate(mc, loanApplicationTerms, null, null));
```

`[VERIFIED: grep -n on the pinned file]`. T50-N2, `RESUME.md`, `gates.md` and T7's task note all cite `:81`,
which is **off by two** — `:81` is inside the preceding `setLoanTransactionProcessingService` method. The
**substance of T50-N2 is confirmed exactly as recorded**; only the line cite is wrong. Recorded because
citation accuracy has been a recurring review finding in this program (T49/T52/T53 audited 155/171/47
citations precisely to catch this class), and a reviewer who checks `:81` will find an unrelated method and
may wrongly conclude the finding was fabricated.

### D-2 (NEW — extends T50-N2, does not duplicate it) — the Path A seam is ALSO structurally blind to HOLIDAYS and NON-WORKING DAYS

T50-N2 recorded the first `null` (`loanCharges`). **There are two nulls.** The second is `holidayDetailDTO`,
and it has the same structural consequence, which nothing in the record so far states:

| Step | Evidence |
|---|---|
| Path A passes `holidayDetailDTO = null` | `ProgressiveLoanScheduleGenerator.java:83` (above) |
| it flows into date generation | `:106-107` — `scheduledDateGenerator.generateRepaymentPeriods(mc, periodStartDate, loanApplicationTerms, holidayDetailDTO)` |
| which calls the adjuster | `DefaultScheduledDateGenerator.java:66` — `adjustRepaymentDate(nextRepaymentDate, loanApplicationTerms, holidayDetailDTO).getChangedScheduleDate()` |
| whose whole body is null-guarded | `:221-249` — `recursivelyCheckNonWorkingDaysAndHolidaysAndWorkingDaysExemptionToGenerateNextRepaymentPeriodDate` opens with `if (holidayDetailDTO != null) {` at **`:224`** and returns `adjustedDateDetailsDTO` **unchanged** otherwise |

So on Path A, holiday and non-working-day adjustment is a **guaranteed silent no-op** — not an error. That
null-guard is precisely why Path A captures run at all instead of throwing NPE, so the seam's usability and
its blindness have the same cause.

**Consequence, and it is the same shape as T50-N2:** **working-day / holiday conformance can ONLY ever be
graded on Path B**, exactly like charge conformance. A vector store that records path provenance only in
order to reason about *charges* is under-specified; the blind spot is at least two-dimensional. A harness
that grades a holiday-bearing case against a Path A capture is broken by construction and must refuse.

### D-2a (the sharper half — a port-defect risk of the same class as T50-N1)

Even on **Path B**, this generator adjusts for holidays **only on the FINAL period.** The
`adjustRepaymentDate` call at `DefaultScheduledDateGenerator.java:66` sits inside

```java
61:            if (repaymentPeriodNumber == numberOfRepayments) { // last period
```

so intermediate due dates are **never** holiday-adjusted on the progressive path. `[VERIFIED: :58-73, the
loop body]`.

This is dangerous in the specific way T50-N1 is dangerous. "Adjust every repayment date that falls on a
holiday" is the obvious, reasonable, and **wrong** thing for a Go port to do; it is what a developer would
write from the method name alone. And a port that did it would **pass the entire existing corpus silently**,
because every capture taken so far went through Path A where the whole mechanism is inert. The defect would
first appear in production, on a real loan whose intermediate instalment lands on a Mongolian public holiday.

Filed for the loan-schedule context as a mandatory Path-B discrimination target: two captures differing only
in whether an **intermediate** period falls on a holiday must differ in **zero** cells, while a final period
on a holiday must move the date. Both halves need observing — the zero is as much the finding as the
difference, per the `chargeCalculationType` 5 precedent where linearity, not absence, hid the effect.
`[UNVERIFIED: that a Path B capture reproduces this — nobody has observed it yet.]`

## The declared wire type for money, and the oracle's own `double` sites — task T186

Established by task T186 (`.softhouse/reviews/T186-wire-money-form-ruling.md`) from the pinned
checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb`. Read this before writing any capture harness or
arguing about float-shaped tokens in a capture.

### The loans request path is `BigDecimal` from token text — no `double`

The oracle's REST API declares `principal` as a **major-unit decimal**, so a FAITHFUL capture
**cannot** send minor units. The declared type is `BigDecimal`, and the JSON-number branch parses the
**original token text**:

- The resource method takes a **raw `String`** body, so Jackson never sees the numbers
  [VERIFIED: `LoansApiResource.java:570-572`; `JerseyJacksonObjectArgumentHandler.java:62-63`].
- `if (primitive.isNumber()) { value = primitive.getAsBigDecimal(); }`
  [VERIFIED: `JsonParserHelper.java:151-152`].
- Consumers: `LoanScheduleAssembler.java:267` (`principal`), `:252` (`interestRatePerPeriod`),
  `LoanApplicationValidator.java:637-638`; entity `LoanProductRelatedDetail.java:61-62`, `:64-65`
  (both `BigDecimal`, `scale = 6, precision = 19`); DDL `DECIMAL(19, 6)`
  [VERIFIED: `db/changelog/tenant/parts/0001_initial_schema.xml:2040`, `:3117`].
- Gson is a bare `new Gson()` with **no** `BigDecimal`/`Double`/`Number` adapter registered anywhere
  [VERIFIED: `FromJsonHelper.java:57-60`; `GoogleGsonSerializerHelper.java:105-115`], pinned at
  `gson:2.14.0` [VERIFIED: `buildSrc/src/main/groovy/org.apache.fineract.dependencies.gradle:55`].
  `[UNVERIFIED: Gson's own `getAsBigDecimal()` internals — no Gson jar or source is present on this
  host, so the final link of the loans chain rests on upstream library behaviour, not on repo source.]`

### ⚠️ INVERSION — quoting a money value moves it ONTO a `double` path

The intuitive "fix" is wrong. A **quoted** value takes the `else` branch
[`JsonParserHelper.java:154-157`] into `convertFrom`, which ends:

```java
if (parsedNumber instanceof BigDecimal) { number = (BigDecimal) parsedNumber; }
else { number = BigDecimal.valueOf(parsedNumber.doubleValue()); }   // line 737
```
[VERIFIED: `JsonParserHelper.java:732-738`]

It also makes `locale` **mandatory** — a null locale throws
`validation.msg.missing.locale.parameter` [VERIFIED: `JsonParserHelper.java:704-715`].
**Send unquoted JSON numbers.** `[UNVERIFIED: whether line 737 is reachable — that depends on Spring's
`NumberStyleFormatter` calling `setParseBigDecimal(true)`, and no `spring-context` source is present
on this host.]`

### Porter's hazard list — three genuine `double` sites in the oracle

Recorded in the style of DEC-1 §4.1.2's `Money.java` list. **None of these is a licence to introduce a
float in Go** (DEC-1:829). Reproduce the oracle's observed **output**; never import its arithmetic
**type**.

1. **`POST /charges` `amount` is a Java `Double` on the wire** — and unlike `PostLoansRequest` this
   DTO is genuinely deserialized, because the resource method declares the DTO type rather than
   `String`, so Jackson handles it and `USE_BIG_DECIMAL_FOR_FLOATS` is not enabled.
   [VERIFIED: `ChargeRequest.java:41` (`private Double amount;`); `ChargesApiResource.java:139-142`;
   `JerseyJacksonConverterConfig.java:48-54`]. Note the same class declares `minCap`/`maxCap` as
   `BigDecimal` [`ChargeRequest.java:52-53`] and the column is `BigDecimal` [`Charge.java:76-77`] —
   the `Double` is an inconsistency in one DTO, not a design.
   **Consequence:** a charge `amount` survives the oracle exactly iff its token text is already the
   shortest round-trip repr of its double — which is precisely the property
   `.softhouse/capture/lib/check_wire_float_roundtrip.py` enforces.
2. **The interest-rate getter launders `BigDecimal` through `Double.parseDouble` on every read** —
   field and column are `DECIMAL(19,6)`, but
   `BigDecimal.valueOf(Double.parseDouble(this.nominalInterestRatePerPeriod.stripTrailingZeros().toString()))`
   [VERIFIED: `LoanProductRelatedDetail.java:344-346`].
3. **The EMI kernel is `double`** — `FinanicalFunctions.pmt(double, double, double, double, boolean)`
   [VERIFIED: `FinanicalFunctions.java:44-55`], reached via `LoanApplicationTerms.java:1604-1622`.

### The OpenAPI spec disagrees with the server on loan products

`LoanProductsApiResourceSwagger.java` declares `public Double principal;` / `Double interestRatePerPeriod;`
(`:93`, `:112`), so the **generated OpenAPI advertises `number/double`** even though the server parses
`BigDecimal`. `LoansApiResourceSwagger.PostLoansRequest` correctly says `BigDecimal` (`:1343`, `:1357`).
Both are documentation-only classes, never instantiated on the request path — but a Go client generated
from the published spec would inherit a `float64`, which is a Zone B rejection.

## ⚠️ ORACLE STATE MOVED BY T287 — a `GLClosure` was created and DELETED (local fire `20260823-080004`)

**Read this before you assume `acc_gl_closure` has never been used, and before you hard-code a closure
id.** Recorded here rather than only in the capture directory because the next fire will meet the
residue in the *tenant*, not in `.softhouse/capture/t287-closure-refusals/`.

### What T287 did

To capture the `ACCOUNTING_CLOSED` refusal — which `capabilities-ledger.json` had been printing as
"NOBODY HAS TAKEN THEM" on every conformance run — a closure had to exist. T287 created one, took two
refusal captures, and **deleted it in the same fire**.

| | |
|---|---|
| Tenant | **`gerege`** (tenant 2, `Asia/Ulaanbaatar`), database `fineract_gerege` |
| Closure id | **1** |
| Office | **1 (Head Office)** — the only office on this tenant |
| Closing date | **`2026-01-31`** — chosen strictly *before* the earliest existing journal entry (`2026-02-01`) so that even a failed delete could poison nothing that exists |
| Created by | T287, `POST /glclosures`, user `mifos` — `out/A2-00-create-closure.json` → `{"officeId":1,"resourceId":1}` |
| Deleted by | T287, `DELETE /glclosures/1` — `out/A2-03-delete-closure.json` → `{"officeId":1,"resourceId":1}` |
| **Surviving closure** | **NONE.** `acc_gl_closure` is back to **0 rows**; `GET /glclosures` → `[]` |
| **What it now forbids** | **NOTHING.** The closure no longer exists, so no date is refused on its account |

The removal is a **HARD DELETE**, not a flag: `GLClosure` carries an `is_deleted` column but has **no
`@SQLDelete` annotation**, and `deleteGLClosure` calls `glClosureRepository.delete(glClosure)`
[VERIFIED: `GLClosure.java:39-62`, `GLClosureWritePlatformServiceJpaRepositoryImpl.java:135`, pinned
commit `426a23544`]. Confirmed by observation at both layers — 0 rows in PostgreSQL and `[]` from the API.

### The residue that did NOT restore — this is the part that matters

> **⚠️ The `60 / 64` and `351 → 352` figures in the next two tables are a record of WHAT T287
> MEASURED, not of what the ledger holds today.** They are correct as history and are deliberately
> left unedited — see *"§ The standing oracle MOVED"* at the end of this file, and never transcribe
> a count out of a dated table. **Derive it:**
> `bash .softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh`

Identity is not value, and identity does not restore (the T276 lesson, one section of which lives in
`.softhouse/capture/tierA-a2/ORACLE-STATE-MOVED-BY-T276.md`).

| counter | before T287 | after T287 | restored? |
|---|---|---|---|
| `acc_gl_closure` rows | 0 | 0 | yes |
| **`acc_gl_closure_id_seq`** | `last_value 1, is_called f` (never used) | `last_value 1, **is_called t**` | **NO — permanent** |
| **`m_portfolio_command_source`** | 347 rows / max id 347 | **351 rows / max id 351** | **NO — permanent, append-only** |
| `acc_gl_journal_entry` | 60 rows / max id 64 / seq 64 | 60 rows / max id 64 / seq 64 | yes — **never moved** |
| `m_office` | 1 row / max id 1 | 1 row / max id 1 | yes — never moved |
| `m_loan` | 7 rows | 7 rows | yes — never moved |

**THE NEXT `GLClosure` CREATED ON THIS TENANT WILL GET `id = 2`, NOT `id = 1`.** The sequence had never
been used before T287 and is now marked called. Any capture that hard-codes closure id 1, or asserts on
`resourceId` returned by a closure create, will be off by one. Same class of drift as T276's
`acc_product_mapping` row-id move.

**The ledger itself was never touched.** All four journal-entry posts in T287 were *refused*, so
`acc_gl_journal_entry` stayed at 60 rows / max id 64 / sequence 64 across before, during and after.

### A related fact worth knowing before you interpret any capture on this tenant

**A REFUSED COMMAND STILL WRITES AN `m_portfolio_command_source` AUDIT ROW**, with
`status = 5` (`ERROR`) and a NULL `resource_id` [VERIFIED: `CommandProcessingResultType.java:31-37` —
`0 INVALID, 1 PROCESSED, 2 AWAITING_APPROVAL, 3 REJECTED, 4 UNDER_PROCESSING, 5 ERROR`]. Across the
whole `gerege` audit table **refusals are the majority of this tenant's command history** — as expected
for a corpus built largely out of refusal probes. That is the claim; it is qualitative on purpose.

> **⚠️ CORRECTED BY T371 — a live cardinal stood here in the PRESENT TENSE and had gone stale.**
> The sentence read *"the split **is** `156 PROCESSED / 194 ERROR`"*. That was T287's measurement,
> restated as a statement about today, and by 2026-08-28 it was wrong in both terms. It is not replaced
> with today's pair, because **that pair would be wrong by the next probe** — the same trap this file
> has now fallen into four times. **Derive it:**
> `.softhouse/capture/t371-t367-conditions/sql/q2-status-split.sql`, or the baseline instrument.
> Found by T367 as F3, and it is F2 seen from the other side: no selector in `casualty-sweep.sh`
> matched a figure of this shape, so the sweep reported no casualty partly because it could not see
> this one. Selectors **S12–S16** were added to that instrument by T371 and now match this line.
> T287's own dated observation (`t287-closure-refusals/ARM2-OBSERVATION.md:136`) keeps the original
> figure and is **correct as history** — a witness is not edited to agree with today (T248/T258/T340).

Consequence: **"a refused write writes nothing" is true of the LEDGER and false of the DATABASE.** A
write-check that watches only `acc_gl_journal_entry` will report a refusal as side-effect-free while it
is in fact consuming command ids and idempotency keys.

**And the key is not merely consumed — it is BURNED. [T367, carried forward by T371.]**
`SynchronousCommandProcessingService.executeCommandAttempt` calls `commandSourceService.saveInitial`
(`:140`) **before** `executeCommandInTransaction` (`:151`), and `CommandSourceService`'s own class
comment says so: *"The initial command source is persisted separately for idempotency."* A later request
reusing that key hits `exceptionWhenTheRequestAlreadyProcessed` (`:133`), which for a `status = ERROR`
row throws `IdempotentCommandProcessFailedException` unless the caller is an explicit retry
[VERIFIED: T371, `SynchronousCommandProcessingService.java:133,140,151,241-260`, pinned `426a23544`].
**So a REFUSAL probe against the standing oracle is as irreversible as an accepted one.** Any text
anywhere in this program that treats a 4xx as a safe no-op against this tenant is wrong: it is a no-op
for the *ledger* and a permanent, unrepeatable consumption of a command id and an idempotency key. Fire
one only under the POLICY at the end of this file, and register it in `PROBES.tsv` exactly like a write.

### Blast radius of a closure, for whoever creates the next one

- The lookup is **per office with no hierarchy walk** — `WHERE closure.office.id = :officeId`
  [VERIFIED: `GLClosureRepository.getLatestGLClosureByBranch`]. On `gerege` that scoping buys nothing:
  `m_office` has exactly **one** row, so office 1 *is* the tenant.
- A closure does **not** only refuse manual journal entries. The identical
  `!DateUtils.isBefore(closingDate, transactionDate)` test lives in
  `AccountingProcessorHelper.checkForBranchClosures` and is called from ~14 automatic accounting sites
  (cash/accrual loan, savings, shares, client transactions, working-capital, and the reversal path at
  `JournalEntryWritePlatformServiceJpaRepositoryImpl:392`). A closure would also refuse a **back-dated
  disbursement or repayment on any accounting-enabled product**.
- **The boundary is INCLUSIVE**: an entry dated *on* the closing date is refused, despite the message
  saying "prior to". Observed, not merely read — see `ARM2-OBSERVATION.md` §2(ii).
- **Do not reach for "use a dedicated office" as the safe route on this tenant.** Offices cannot be
  deleted — `OfficesApiResource` exposes GET/POST/PUT and **no `@DELETE`** — so creating one trades a
  reversible mutation for an irreversible one.

---

## Fire `20260827-230001` — THE ORACLE WAS DOWN AND THIS FIRE BROUGHT IT UP (PostgreSQL profile only)

The fire opened with the reference oracle **UNREACHABLE** and Docker running. Per the fire contract
that is T1's job, not a park reason. Bring-up succeeded; **nothing was parked for oracle reasons.**

### What was actually running before

| container | image | state |
|---|---|---|
| `fineract-db-1` | `postgres:18.3` | **up 5 h, healthy**, `0.0.0.0:5432->5432/tcp` |
| `fineract-fineract-1` | — | **not running.** The app container was simply absent; the database was never down |

So "the oracle is unreachable" meant *the Fineract app process was not up*, not that the stack was
broken. Distinguishing those two is the difference between a 90-second fix and a parked fire.

### Bring-up, and the assertions made BEFORE starting it

```
docker compose -f /Users/buv/fineract/docker-compose-postgresql.yml up -d fineract
```

`docker-compose-postgresql.yml` extends `config/docker/compose/postgresql.yml` (service `postgresql`)
and `config/docker/compose/fineract.yml`. **The mariadb and mysql compose files were never invoked.**

Asserted by reading `config/docker/env/fineract-postgresql.env`, not assumed:

| assertion | observed |
|---|---|
| `FINERACT_HIKARI_DRIVER_SOURCE_CLASS_NAME` | `org.postgresql.Driver` ✅ |
| `FINERACT_HIKARI_JDBC_URL` | `jdbc:postgresql://db:5432/fineract_tenants` ✅ |
| `FINERACT_DEFAULT_TENANTDB_PORT` | `5432` ✅ |
| prohibited-engine grep (`ojdbc`, `oracle.jdbc`, `:1521`, `com.mysql.cj`, `mariadb`) over all three env files and all three compose files on this path | **0 hits** ✅ |

### Connection facts recorded this fire

| fact | value |
|---|---|
| Health endpoint | `https://localhost:8443/fineract-provider/actuator/health` → `{"status":"UP","groups":["liveness","readiness"]}` |
| **Time to healthy from `up -d`** | **80 seconds** (polled at 10 s; first 200 at the 8th poll) |
| API base | `https://localhost:8443/fineract-provider/api/v1` |
| Auth used for the probe | basic `mifos:password`, header `Fineract-Platform-TenantId: gerege` |
| Tenant probe | `GET /offices` → `[{"id":1,"name":"Head Office",…,"openingDate":[2009,1,1],"hierarchy":"."}]` |
| **PostgreSQL server version** | **`PostgreSQL 18.3 (Debian 18.3-1.pgdg13+1) on aarch64-unknown-linux-gnu`**, gcc 14.2.0, 64-bit |
| **Pinned Fineract commit** | **`426a23544`** ("Merge pull request #5946"), verified in `/Users/buv/fineract` |
| Tenant database name | **`fineract_gerege`** — *not* `gerege`. `psql -d gerege` fails with `database "gerege" does not exist`; the API tenant id `gerege` maps to database `fineract_gerege`. Databases present: `fineract_default`, `fineract_gerege`, `fineract_tenants`, `postgres`, `root` |
| `tenants` table shape | `schema_name` **does not exist** as a column in this build's `fineract_tenants.tenants` — a query written against that column name errors. Read the actual columns before scripting against it |

### Tenant state at bring-up, against the T287 baseline recorded above

> **⚠️ SUPERSEDED AS A STATEMENT ABOUT TODAY.** This table was true when it was taken and is a
> valid record of that fire. **The ledger has since moved and can never move back** — see
> *"§ The standing oracle MOVED"* at the end of this file. Derive, do not read:
> `bash .softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh`

| counter | T287 left it at | observed this fire | moved? |
|---|---|---|---|
| `acc_gl_journal_entry` | 60 | **60** | no — the ledger is untouched across the restart |
| `acc_gl_closure` | 0 | **0** | no |
| `m_office` | 1 | **1** | no |
| `m_loan` | 7 | **7** | no |
| `m_portfolio_command_source` | 351 | **352** | **+1** |

**The ledger did not move across a container restart** — 60 rows before and after, which is the fact
that matters for every vector already captured on this tenant.

`m_portfolio_command_source` is **+1 (351 → 352)**, and this fire did **not** identify which command
wrote it. This fire issued only `GET /offices`, and a GET does not write an audit row, so the extra row
predates this fire's probes. `[UNVERIFIED]` which fire or command produced it. It is consistent with
the append-only, never-restoring behaviour T287 recorded — command ids are consumed and never returned
— and it is a reminder that **`m_portfolio_command_source` is not a reliable fixture** for any vector
that pins an absolute id.

---

## The standing oracle MOVED — fire `20260828-140005`, and it can never move back

**Recorded by T363.** Every figure in this section was **re-derived by T363 against the live
PostgreSQL**, not inherited from the tasks that fired the probes. This section exists because the
record previously lived only inside the probing tasks' own capture directories, where the next task
to count something against the live database has no reason to look.

### The one-line answer

**Do not read a count out of this file. Derive it.**

```bash
bash .softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh
```

Exit **0** = every row above the floor is attributed to a recorded probe. Exit **1** = somebody wrote
to the shared oracle and did not record it, and the orphaned rows are named. Exit **2** = the database
was unreachable, which is **not** a statement about the ledger. Exit **3** = you ran it with `sh`.
If that output and any prose in this repository disagree, **the output is right.**

### What moved, stated as IDENTITIES rather than as counts

A count is true for an instant; an identity on an append-only table is true forever. So:

| what | identity | task |
|---|---|---|
| `acc_gl_journal_entry` rows **65–73** — 4 transactions, 9 legs | `a29bca0816a7`, `a29bca9bf813`, `a29bcaa6a41b`, `a29bcb5d6fcf` | **T352** |
| `acc_gl_journal_entry` rows **74–75** — 1 transaction, 2 legs | `a29bd5eaeb1b` | **T359** |
| `m_portfolio_command_source` rows **353–359** | idempotency keys `t352-a01-residue-3dp`, `t352-a03-balance-scale`, `t352-a04-overscale`, `t352-a07-usd`, `T359-P01-residue-post`, `T359-P02-residue-post`, `T359-P03-residue-post` | T352, T359 |

The last row before any of it: `acc_gl_journal_entry.id = 64`, `m_portfolio_command_source.id = 352`.
Those two numbers are the **floor**, they are pinned in
`.softhouse/capture/t363-oracle-baseline/PROBES.tsv`, and they are the only cardinals in this section
that cannot rot.

**`a29bcb5d6fcf` is the first non-MNT journal entry ever posted in this tenant** — gl 16 DEBIT /
gl 21 CREDIT `12.340000` **USD**, accepted HTTP 200. Any claim of the form *"every row in this ledger
is MNT"* was true before it and is false after it [VERIFIED: T363, live, `SELECT DISTINCT
currency_code` returns two rows].

### Three corrections to the record the probing tasks left

1. **gl 21 moved `8 → 12 → 13`, not `7 → 12 → 13`.** T352's table inherited its "before" from T242
   rather than measuring it. Re-derived independently by T363 by excluding the five registered
   transactions from the live table (legitimate only because the ledger is append-only):
   `gl 16: 16→21`, `gl 17: 4→5`, `gl 21: 8→13`.
2. **`m_portfolio_command_source` moved too — `352 → 359` — and neither task's record names it.**
   Both records name the ledger and the transaction count only. The third counter matters because
   two committed rigs pin it (below).
3. **T359's two HTTP 400s did not "move nothing".** They moved no *journal entry*, and they wrote
   **permanent** `m_portfolio_command_source` rows 357 and 358 at `status = 5` (ERROR)
   [VERIFIED: live rows; `CommandProcessingResultType.java:31-37` at `426a23544`]. *"A refused write
   writes nothing"* is true of the **ledger** and false of the **database** — the same fact this file
   already records under T287, restated because it was forgotten one section later.

**`gl 18` and `gl 22` have never carried a single journal entry and neither probe touched them.**
That is the pair `capabilities-ledger.json`'s `ledger.accrual.entry` argument actually rests on, so it
is derived on every run of the instrument rather than asserted here.

---

## POLICY — firing a probe at the SHARED reference oracle

**A probe against the standing instance on `:8443` is IRREVERSIBLE.** A journal entry has no delete
path; a closure delete leaves its sequence consumed; a *refused* command still burns a command id and
an idempotency key. Nothing you post to `gerege` can be taken back by any later task, including you.

This policy is **ENGINEERING**, decided under `CLAUDE.md` § *Answering gates* by T363 and recorded
rather than raised. Buyan may reverse it.

### 1. Prefer, in this order

1. **Read-only.** A `SELECT`, a `GET`, or re-reading a committed capture. Most questions asked of this
   oracle are answerable this way and the last three fires prove it.
2. **An absence probe over a difference probe** where one can be built — the T42 rule, already in this
   file, and it usually needs no write at all.
3. **A throwaway instance** on another port with no named volume, the shape `t305` and `t327` built.
   An accepted write that cannot be un-accepted belongs there, not here.
4. **The standing oracle, last.** Only when the question is about *this tenant's* accumulated state, or
   when a throwaway would not reproduce the behaviour.

### 2. If you fire one anyway, these are the conditions

- **Proportionality, argued in the handoff.** State what the probe settles that a read could not, and
  why the number of writes you made is the smallest number that settles it. T359's *"Two rows, three
  claims. I judge that proportionate and I would not have fired a second"* is the standard.
- **A distinct `Idempotency-Key` per probe, naming the task** — e.g. `t352-a07-usd`,
  `T359-P03-residue-post`. This is not hygiene. It is the **only** attribution link between a command
  row and the task that fired it, and the baseline instrument reads it. A shared or anonymous key
  makes your write unattributable forever.

  **Do not read the presence of a key as attribution. [T371, correcting T363; found by T367.]**
  `m_portfolio_command_source.idempotency_key` is a **`NOT NULL`** column [VERIFIED: T371, live,
  `information_schema.columns`], so *"every row in the table has one"* is the schema restated and is
  evidence of nothing. **Fineract MINTS a key when the caller sends no header** —
  `IdempotencyKeyResolver.resolve` is `Optional.ofNullable(wrapper.getIdempotencyKey()).orElseGet(() ->
  getAttribute().orElseGet(idempotencyKeyGenerator::create))` and `IdempotencyKeyGenerator.create()`
  returns `UUID.randomUUID().toString()` [VERIFIED: T371, `fineract-core/…/commands/service/
  IdempotencyKeyResolver.java:36` and `IdempotencyKeyGenerator.java:25-29`, pinned `426a23544`].
  A minted UUID names nothing and its row is **unattributable forever**. Attribution therefore comes
  from **this convention being obeyed**, never from the column being populated — which is exactly why
  it is written here as an obligation rather than reported as a property. Derive the split rather than
  reading one: `.softhouse/capture/t371-t367-conditions/sql/q3-key-naming.sql`.
- **Touch no account a promoted vector grades**, if the question can be asked on another account. Three
  ledger parity vectors read `gl 16`; T352 posted to it anyway, which is why gl 16's count has now been
  restated three times in eight days.
- **Never a product retype, a mapping edit, a GL-account edit, a closure, or a business-date change.**
  Those are not appends; they change how *existing* rows render. A2-26 flipped GL account 2
  ASSET → INCOME underneath five live mappings and the corpus is still carrying the correction.
- **No deposit or savings behaviour.** The tenant is an NBFI (ББСБ) — Law on Non-Banking Financial
  Activities Art. 12.1.3 / 12.1.4.

### 3. What you MUST record, and where — this is the part that was missing

| record | where | why there |
|---|---|---|
| **The attribution rows** — one `txn` line per transaction, one `cmd` line per idempotency key | **`.softhouse/capture/t363-oracle-baseline/PROBES.tsv`**, in the same commit as your handoff | **This is the enforceable one.** If you omit it, the next run of `oracle-state-baseline.sh` exits **1** and prints your orphaned rows. The record cannot silently go missing, because its absence is what goes red. |
| The full narrative — what each probe asked, what it observed, what it does *not* affect | `ORACLE-STATE-MOVED-BY-<TASK>.md` in your own capture directory | The shape T276, T352 and T359 used. They are good documents; keep writing them. |
| A one-line pointer to that document | your handoff's `## Changes Made` | so a reviewer reading only the handoff learns the oracle moved |

**Do not add a count to this file.** Three separate places in this program have carried a hand-typed
ledger count and all three went stale within days (`capabilities-ledger.json` twice, this file three
times, the driver's standing-baseline observation once). Add the attribution row and let the instrument
derive the count.

### 4. What NOT to do about a stale count someone else wrote

- **Do not retype a count inside an archived capture, transcript or `out/` file.** Those are snapshots
  of a state the oracle has left; that is what they are *for*. Editing one to agree with today forges a
  witness.
- **Correct a count where it is NAMED, never where it is RESTATED** (T248 / T258 / T340). If the same
  figure appears in a doctrine file and in four transcripts, exactly one of them is the defect.
- **Do not "re-baseline" a rig by retyping its pin.** See the finding on `t305` / `t327` in
  `.softhouse/capture/t363-oracle-baseline/CASUALTIES.md` — the pin is not the bug, comparing against a
  baseline of *unknown age* is.

### 5. THE BOUND ON THE INSTRUMENT — what `oracle-state-baseline.sh` cannot see

**Recorded by T371 from T367's attack, because a guarantee whose limits are unwritten will be read as
unlimited.** The instrument is **fail-closed for the APPEND PATH IT WATCHES** — two tables, floored on
`max(id)`, attributed against `PROBES.tsv`. It is **not** a fail-closed guarantee about the database.
T367 found three ways to move this tenant and leave a green run, and all three are open today:

1. **A consumed sequence is invisible.** The floor is `max(id)`; the instrument never reads a sequence.
   Live, `acc_gl_closure_id_seq` is `last_value 1, is_called t` while `acc_gl_closure` reads `0 rows /
   max id null`. The instrument prints that as pristine — **yet this file already records that consumed
   sequence as permanent, non-restoring movement** and warns that the next closure gets id 2. The one
   class of irreversible movement the canonical record documents is a class the instrument cannot see.
   (It is caught *indirectly*: creating or deleting a closure lands a command-source row above the
   floor. Indirectly is not the same as directly.)
2. **Direct SQL to any of the other 279 tables.** The instrument attributes on **2** tables; this tenant
   has **281** base tables. Its real coverage argument is *"every API-driven write lands an
   `m_portfolio_command_source` row above the floor, so the command floor catches a write anywhere."*
   That argument is sound and was, until now, **nowhere written down**. A statement issued outside the
   command bus — `psql`, a migration, a fixture load — satisfies none of it.
3. **An `UPDATE` of a row BELOW the floor.** The floor detects appends, not mutations. Flipping
   `reversed` on an existing journal-entry row moves the ledger's meaning and moves no id. **8 rows
   already carry `reversed = t`**, and the instrument never reads that column.

A fourth, weaker case: a **rolled-back** transaction leaves nothing to attribute at all.

**How to read this.** None of the three is a defect *in* the instrument — it grades attribution of
appends and it does that correctly. They are the **shape of the probe that would defeat it**, and they
are written here so that "the baseline ran green" is quoted with its scope attached. Do not fire any of
them at this tenant; if you must, none of the recording obligations in § 3 is waived by the instrument's
blindness — they are made *more* important by it.

## Oracle incidents — local fire `20260829-080002`, iteration 6 (2026-08-29)

Two unexplained terminations of `fineract-fineract-1` in one fire, **both `Exited (143)` — SIGTERM**, not a crash
and not an OOM kill (137). Neither was caused by any task; both were observed by workers mid-run.

| # | Observed by | Symptom | Recovery |
|---|---|---|---|
| 1 | `T462` | first bar on its committed tree returned `exit 2 / UNUSABLE`; **all guards green, only reachability failed**; the pre-commit run had read `up` | worker restarted both containers, re-ran to PASS |
| 2 | `T479` | oracle down mid-review and did not return; **the Docker daemon itself was gone** (`unix:///Users/buv/.docker/run/docker.sock` absent), Postgres 5432 closed | driver relaunched Docker Desktop (daemon up in 10 s, 29.6.2), `docker start fineract-db-1 fineract-fineract-1`, healthy after 90 s |

**Both were correctly diagnosed as outages rather than corpus faults**, because the probe line was *printed* and
read `down` — the presence-before-value discipline is what distinguishes this from a HARD-guard failure, which
also exits 2 but prints **no** probe line at all.

**T479 did not claim a PASS for its own final bar**, reporting `probe presence 1 / value down / VERDICT: UNUSABLE /
exit 2` with 0 guard refusals, and said so explicitly. That is the correct handling and is recorded here as the
worked example: **exit 2 is never a pass, and an outage is never reported as a green bar.**

**Unresolved:** what sends the SIGTERM. Not investigated this fire — it is a host-level question (Docker Desktop
lifecycle, resource pressure, or a desktop session event), not a migration question. Filed as a standing note so
the next fire that sees `Exited (143)` recognises it as recurring rather than novel. Parity is unaffected: the
bar was re-run green after each recovery, 46 vectors / 7884 cells against the pinned oracle.

Connection facts unchanged: `https://localhost:8443/fineract-provider/actuator/health`, PostgreSQL `localhost:5432`,
pinned Fineract checkout `/Users/buv/fineract @ 426a23544`. **PostgreSQL only** — no MySQL/MariaDB/Oracle Database
image was started at any point.
