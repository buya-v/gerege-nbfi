#!/bin/sh
# Tier D FEASIBILITY -- THROWAWAY-instance environment.
#
# THIS POINTS AT THE THROWAWAY, NEVER AT THE STANDING REFERENCE ORACLE, and the difference is
# visible in every value: port 8444 (standing: 8443), tenant `tierd` (standing: `gerege`),
# container tierd-oracle-db (standing: fineract-db-1 and gerege-oracle-db), database
# fineract_tierd (standing: fineract_gerege). Two files, two targets, no shared defaults.
#
# `${VAR:-default}` throughout, never a bare assignment (T305 ../env.sh records why: a
# clobbering assignment made a guard's own fail-closed branch untestable, P-22).
B=${B:-https://localhost:8444/fineract-provider/api/v1}
A=${A:-'Authorization: Basic bWlmb3M6cGFzc3dvcmQ='}   # mifos:password, stock demo credentials
T=${T:-'Fineract-Platform-TenantId: tierd'}
CT=${CT:-'Content-Type: application/json'}
DBC=${DBC:-tierd-oracle-db}
DBUSER=${DBUSER:-root}
DBNAME=${DBNAME:-fineract_tierd}
# Root API (no /api/v1 on the tail) for actuator/health probes.
ROOT=${ROOT:-https://localhost:8444/fineract-provider}
export B A T CT DBC DBUSER DBNAME ROOT
