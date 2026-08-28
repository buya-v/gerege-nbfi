#!/bin/sh
# T327 THROWAWAY-instance capture environment.
#
# THIS POINTS AT THE THROWAWAY, NEVER AT THE STANDING REFERENCE ORACLE, and the difference is
# visible in every value: port 8444 (standing: 8443), tenant `t327` (standing: `gerege`),
# container t327-oracle-db (standing: fineract-db-1), database fineract_t327 (standing:
# fineract_gerege). ../env.sh -- the READ-ONLY rig one directory up -- points at the standing
# oracle and is not sourced from here; two files, two targets, no shared defaults to confuse.
#
# `${VAR:-default}` throughout, never a bare assignment, for the reason ../env.sh records:
# a clobbering assignment made a guard's own fail-closed branch untestable (P-22).
B=${B:-https://localhost:8444/fineract-provider/api/v1}
A=${A:-'Authorization: Basic bWlmb3M6cGFzc3dvcmQ='}   # mifos:password, stock demo credentials
T=${T:-'Fineract-Platform-TenantId: t327'}
CT=${CT:-'Content-Type: application/json'}
DBC=${DBC:-t327-oracle-db}
DBUSER=${DBUSER:-root}
DBNAME=${DBNAME:-fineract_t327}
export B A T CT DBC DBUSER DBNAME
