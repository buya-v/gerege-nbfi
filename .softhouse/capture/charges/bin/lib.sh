#!/bin/sh
# T40 — shared capture harness for the charges corpus.
#
# Path B: the RUNNING pinned Fineract reference oracle + PostgreSQL, tenant `gerege`
# (Asia/Ulaanbaatar, MathContext(19, HALF_UP)).  Additive only: this harness never
# restarts, re-tenants, drops or truncates anything.  PostgreSQL is the only engine.
#
# Money never passes through a float in this harness: request payloads are authored as
# text and posted with `-d @file`; responses are written to disk as raw bytes and only
# ever read back as text/Decimal.
set -u

W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513
CH=$W/.softhouse/capture/charges
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

# post <request-file> <output-file>   -> prints "HTTP <code>"; non-200 aborts the caller
post() {
  _req=$1; _out=$2; _path=${3:-loans?command=calculateLoanSchedule}
  _code=$(curl -sk -X POST "$B/$_path" -H "$A" -H "$T" -H "$CT" \
            -d @"$_req" -o "$_out" -w '%{http_code}')
  echo "  POST $_path  <- $(basename "$_req")  HTTP $_code  -> $(basename "$_out")"
  if [ "$_code" != "200" ]; then
    echo "CAPTURE FAILED: HTTP $_code — '$_out' is an ERROR BODY, not a capture." >&2
    cat "$_out" >&2; echo >&2
    return 1
  fi
  return 0
}

sha() { shasum -a 256 "$1" | awk '{print $1}'; }
