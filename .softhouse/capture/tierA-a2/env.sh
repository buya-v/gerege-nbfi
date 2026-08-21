#!/bin/sh
# A2 capture environment. Sourced by every capture script in this directory.
# Facts from .softhouse/reference-oracle.md; tenant per the Path B recipe (NEVER `default`).
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='   # mifos:password, stock demo credentials
T='Fineract-Platform-TenantId: gerege'          # ratified production tenant, Asia/Ulaanbaatar, HALF_UP
CT='Content-Type: application/json'
export B A T CT
