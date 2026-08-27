#!/bin/sh
# T294 capture environment. Sourced by every capture script in this directory.
# Facts from .softhouse/reference-oracle.md (tenant `gerege`, NEVER `default`).
# COPIED BYTE-FOR-BYTE from ../t287-closure-refusals/env.sh (only this header differs), and
# copied rather than sourced ON PURPOSE, keeping T287's property: this rig must be
# re-runnable on its own, and a cross-directory source is a dependency a reviewer reading
# `git show <branch>:.softhouse/capture/t294-openingbalance-refusal/env.sh` cannot see.
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='   # mifos:password, stock demo credentials
T='Fineract-Platform-TenantId: gerege'          # ratified production tenant, Asia/Ulaanbaatar, HALF_UP
CT='Content-Type: application/json'
DBC=fineract-db-1
DBUSER=root
DBNAME=fineract_gerege                          # PostgreSQL. The only database in this program.
export B A T CT DBC DBUSER DBNAME
