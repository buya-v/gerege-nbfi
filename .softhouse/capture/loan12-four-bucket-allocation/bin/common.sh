#!/usr/bin/env bash
# loan12-four-bucket-allocation shared oracle client.
#
# ADDITIVE ONLY: every call is a GET or the one POST that creates a NEW repayment
# transaction on the EXISTING loan 12 (OHLGT-L03). No product, client, charge or
# loan is modified; nothing is addressed at existing rows.
#
# BYTE-STABLE REQUEST: the repayment body carries NO numeric JSON token at all.
# transactionAmount is a JSON STRING ("97978.65") and transactionDate is a string,
# so every token is already byte-preserved under a binary-double round trip. This
# is the P-25 defect the gl-accounting-surface rig was refused for; this body
# cannot carry it.
set -uo pipefail

BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

ROOT="/Users/buv/oh-gerege-allocg"
CAP="$ROOT/.softhouse/capture/loan12-four-bucket-allocation"
REQ="$CAP/req"
OUT="$CAP/out"

mkdir -p "$REQ" "$OUT"

api_get()  { curl -sk -m 30 "$BASE$1" -H "$AUTH" -H "$TEN"; }
api_post() { curl -sk -m 30 -X POST "$BASE$1" -H "$AUTH" -H "$TEN" -H "$CT" --data-binary @"$2"; }
