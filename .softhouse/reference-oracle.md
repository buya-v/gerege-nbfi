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
| Databases | `fineract_tenants`, `fineract_default` |
| Schema size | 281 tables in `fineract_default.public` |

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

Rebuild the image after moving the pin: `/Users/buv/gerege-nbfi/.softhouse/bin/build-oracle-image.sh`

## Connection facts for vector capture

| Fact | Value |
|---|---|
| Base URL | `https://localhost:8443/fineract-provider/api/v1` (self-signed TLS — `curl -k`) |
| Auth | HTTP Basic `mifos:password` (verified: `GET /offices` → Head Office) |
| Tenant header/param | `tenantIdentifier=default` |
| Postgres | `psql -U root -d fineract_default` inside `fineract-db-1` |

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
