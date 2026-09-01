# Reference oracle — reproducible stack

This directory holds everything the repo-root `docker-compose.yml` needs to
reproduce the **Fineract reference implementation on PostgreSQL**, decoupled from
the host that recorded `.softhouse/reference-oracle.md`.

> **Terminology.** "The oracle" means the Fineract reference implementation we
> grade Go output against (test-oracle sense). Oracle Database is a prohibited
> product in this program and appears in no service here. PostgreSQL is the only
> database.

## Layout

```
.softhouse/oracle/
├── README.md                    this file
├── env.sh                       shell connection facts (sourced, not executed)
├── env/                         container env files, vendored from the pinned checkout
│   ├── postgresql.env
│   ├── fineract.env
│   ├── fineract-common.env
│   └── fineract-postgresql.env
└── config/                      read-only files bind-mounted into the containers
    ├── 01-init.sh               tenant-registry + default-tenant bootstrap
    ├── logback-override.xml
    └── aws-credentials
```

The `env/` and `config/` files are byte-copies of the pinned Fineract checkout's
`config/docker/` tree (Apache 2.0). They are vendored here so `docker compose up`
does not depend on `/Users/buv/fineract` existing on this host.

## Bring up / tear down

From the repository root:

```sh
# one-time image build on a fresh host (pins JDK 21; see .softhouse/bin/build-oracle-image.sh)
bash .softhouse/bin/build-oracle-image.sh

docker compose up -d        # PostgreSQL + Fineract; healthy oracle on :8443
docker compose down         # stop, keep database and log volumes
docker compose down -v      # stop and destroy database and log volumes
```

Health probe (self-signed TLS, hence `-k`):

```sh
curl -sk https://localhost:8443/fineract-provider/actuator/health
# {"status":"UP","groups":["liveness","readiness"]}
```

## Connection facts

`env.sh` is the single source of truth for the shell side, and it carries the
same defaults and the same override names as the compose file:

| variable | default | meaning |
| -------- | ------- | ------- |
| `ORACLE_HOST` | `localhost` | host that publishes the Fineract API |
| `ORACLE_APP_PORT` | `8443` | host port mapped to Fineract's 8443 |
| `ORACLE_DB_PORT` | `5432` | host port mapped to PostgreSQL's 5432 |
| `ORACLE_DB_CONTAINER` | `gerege-oracle-db` | container name for `docker exec` psql access |
| `ORACLE_BASE_URL` | derived from host/port | `.../fineract-provider/api/v1` |
| `ORACLE_HEALTH_URL` | derived from host/port | `.../fineract-provider/actuator/health` |

`.softhouse/conformance.sh` sources `env.sh`; the harness-level override
`CONFORMANCE_ORACLE_HEALTH_URL` still wins when set.

## Known gap (Phase 1.B)

`docker compose up` on a clean host reproduces the **default** Fineract tenant
(`fineract_default`) and the tenant registry (`fineract_tenants`). It does **not**
yet provision the production `gerege` tenant / `fineract_gerege` database that the
ledger captures were made against. Provisioning that tenant from a pinned snapshot
is a separate step; until it lands, this stack can grade the committed vector
store and serve loan-schedule parity, but it cannot re-observe ledger A2 captures.
