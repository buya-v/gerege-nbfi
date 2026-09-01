#!/bin/sh
# .softhouse/oracle/env.sh -- shared reference-oracle connection facts.
#
# Sourced (never executed) by shell scripts that need to reach the reference
# oracle: conformance.sh and any capture rig. The values here are the SAME
# defaults the repo-root docker-compose.yml publishes, so a script that sources
# this file and a caller that runs `docker compose up` agree without either one
# hard-coding a host path.
#
# Every value is overridable, with the same `${VAR:-default}` shape the rest of
# the harness uses so an exported value can never be clobbered by this file.
#
# Oracle here means the FINERACT REFERENCE IMPLEMENTATION. Oracle Database is a
# prohibited product in this program. PostgreSQL is the only database.

ORACLE_HOST="${ORACLE_HOST:-localhost}"
ORACLE_APP_PORT="${ORACLE_APP_PORT:-8443}"
ORACLE_DB_PORT="${ORACLE_DB_PORT:-5432}"
ORACLE_DB_CONTAINER="${ORACLE_DB_CONTAINER:-gerege-oracle-db}"

ORACLE_BASE_URL="${ORACLE_BASE_URL:-https://${ORACLE_HOST}:${ORACLE_APP_PORT}/fineract-provider/api/v1}"
ORACLE_HEALTH_URL="${ORACLE_HEALTH_URL:-https://${ORACLE_HOST}:${ORACLE_APP_PORT}/fineract-provider/actuator/health}"

export ORACLE_HOST ORACLE_APP_PORT ORACLE_DB_PORT ORACLE_DB_CONTAINER \
       ORACLE_BASE_URL ORACLE_HEALTH_URL
