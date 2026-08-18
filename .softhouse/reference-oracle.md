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
`PATHB-REPORT.md`. Raw observed only; **not audited**, nothing promoted to the vector store.

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
