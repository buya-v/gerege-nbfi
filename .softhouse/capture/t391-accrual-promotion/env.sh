#!/bin/sh
# T391 capture environment. A COPY, not a `.` of another directory's env.sh --
# T287's rule, kept: a cross-directory source is a dependency a reviewer reading
# `git show <branch>:...` cannot see.
#
# Facts from .softhouse/reference-oracle.md; tenant per the Path B recipe (NEVER `default`).
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='   # mifos:password, stock demo credentials
T='Fineract-Platform-TenantId: gerege'          # ratified production tenant, Asia/Ulaanbaatar, HALF_UP
CT='Content-Type: application/json'
export B A T CT
