#!/bin/sh
# T305 capture environment. Sourced by every script in this directory.
#
# COPIED from ../t294-openingbalance-refusal/env.sh (only this header and the extra
# database names differ), and copied rather than sourced ON PURPOSE, keeping T287's and
# T294's property: this rig must be re-runnable on its own, and a cross-directory source
# is a dependency a reviewer reading
# `git show <branch>:.softhouse/capture/t305-openingbalance-accepting-side/env.sh`
# cannot see.
#
# ***** THIS RIG FIRES NOTHING AT THE REFERENCE ORACLE THAT WRITES. *****
# Every observation under out/ is a read-only SELECT. There is no req/ directory in this
# rig and there is no POST script, ON PURPOSE: the whole deliverable of T305 is the
# finding that the accepting-side observation CANNOT be taken reversibly, so a rig that
# carried a ready-to-fire body would be exactly the loaded weapon P-92 names --
# "a probe whose safety comes from an EXTERNAL PRECONDITION rather than from its own
# content is a loaded weapon, and the danger is highest immediately after the capture
# SUCCEEDS". An accepting probe's danger is worse than that: it is highest WHEN IT
# SUCCEEDS, permanently, because a posted journal entry cannot be deleted.
#
# ONE DELIBERATE DIFFERENCE FROM THE T287/T294 ORIGINALS: the connection variables use
# `${VAR:-default}` rather than a bare assignment. T294's env.sh clobbers an inherited
# value, and red-drive-gate.sh ARM 2 MEASURED that this made the fail-closed branch of
# guard-accepting-capture.sh UNREACHABLE FROM A TEST -- the guard was asserted to exit 2 on
# an unreachable database and could not be shown to. That is P-22's shape ("a control that
# cannot fail is worse than none") applied to the guard's own error path, and the red-drive
# caught it rather than the author noticing. The override cannot manufacture a PASS: every
# value it can take either reaches the real database or reaches none, and reaching none is
# exit 2 by construction.
B=${B:-https://localhost:8443/fineract-provider/api/v1}
A=${A:-'Authorization: Basic bWlmb3M6cGFzc3dvcmQ='}   # mifos:password, stock demo credentials
T=${T:-'Fineract-Platform-TenantId: gerege'}          # ratified production tenant, Asia/Ulaanbaatar, HALF_UP
CT=${CT:-'Content-Type: application/json'}
DBC=${DBC:-fineract-db-1}
DBUSER=${DBUSER:-root}
DBNAME=${DBNAME:-fineract_gerege}               # PostgreSQL. The only database in this program.
DBNAME_DEFAULT=${DBNAME_DEFAULT:-fineract_default}  # tenant `default`, Asia/Kolkata -- NOT ours
DBNAME_STORE=${DBNAME_STORE:-fineract_tenants}      # the SHARED tenant registry
export B A T CT DBC DBUSER DBNAME DBNAME_DEFAULT DBNAME_STORE
