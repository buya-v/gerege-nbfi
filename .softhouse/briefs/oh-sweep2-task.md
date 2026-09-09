# OH-SWEEP2 — investor and workingcapital. THE PATHS ARE BELOW. Start calling them.

Repo: /Users/buv/oh-gerege-sweep2   Branch: feat/OHSWEEP2-investor-wc (checked out)

## Every endpoint you need, VERIFIED 200 minutes ago. Do NOT search for them.

    BASE='https://localhost:8443/fineract-provider/api/v1'
    AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
    TEN='Fineract-Platform-TenantId: gerege'
    CT='Content-Type: application/json'

    GET $BASE/external-asset-owners/transfers?loanId=1   -> 200   VERIFIED
    GET $BASE/external-asset-owners/transfers            -> 500   (missing param, NOT 400)
    GET $BASE/working-capital-loan-products              -> 200   VERIFIED
    GET $BASE/working-capital-loans                      -> 200   VERIFIED
    GET $BASE/working-capital/near-breach                -> 200   VERIFIED
    POST $BASE/external-asset-owners/search              (405 on GET; it wants POST)

The routes are HYPHENATED. `workingcapitalloans` and `workingcapitalloanproducts` are 404 —
a previous attempt burned 478 events, issued 9 POSTs that ALL FAILED on wrong paths, and
wrote NOTHING to disk. The oracle is unchanged. Do not repeat that run.

Further paths, if you need them, from
/Users/buv/fineract/fineract-working-capital-loan/.../api/*.java @Path annotations:
  /v1/working-capital-loans/{loanId}/breach-schedule
  /v1/working-capital-loans/{loanId}/delinquency-range-schedule

## RULE ONE: WRITE TO DISK BEFORE YOU MOVE ON

After EVERY call, write the request body to `.softhouse/capture/<ctx>/req/` and the RAW
response to `.softhouse/capture/<ctx>/out/<case>-raw.json` with a `<case>.status` file
holding the HTTP code. Commit after each context. **Whatever is not on disk did not happen** —
two runs today ended with hundreds of events and nothing to show.

If a call returns non-200, SAVE IT ANYWAY as an oracle-refusal recording (the 500 above is
one) and move on. Do not loop on it.

## What exists — `.softhouse/capture/seed/MANIFEST.json`, never re-derive it

BUSINESS DATE PINNED 2026-09-01. gerege: HALF_UP (ordinal 4), MNT, 2 minor units.
  1 office  9 clients  4 GL accounts  7 loans (5 disbursed)  1 external-asset-owner transfer
  m_wc_* tables exist and the working-capital jar is deployed; m_wc_loan is currently EMPTY.

`.softhouse/capture/ohsweep/lib.sh` holds curl helpers from the last sweep — reuse them.

## Then promote

Build `nexus/internal/apps/<ctx>/conformance/` on the SHARED CORE
`nexus/internal/conformance`. Follow `loan` or `savings`, NOT loanschedule. Include a
`cmd/conformance` entrypoint.

Every vector: `provenance.kind = "oracle-capture"`, `capture_ref`, a REAL `shasum -a 256`
in `capture_sha256`, `tenant_params`. Money as INTEGER MINOR UNITS in a string. TRANSCRIBE
from the capture; never compute.

Where a seam divides or takes a percentage, CONSTRUCT an input whose raw result lands on a
half minor unit and pin it — five seams have now proved this tenant rounds HALF_UP
(20925.05, 74234.32, 1000.51, 0.01, 0.01). Where a seam only adds integer minor units, put
"no rounding surface" in the MANIFEST's `roundingSurface` field. Do NOT invent a tie.

## DO NOT REGISTER YOUR SCHEMA

Do NOT edit `nexus/internal/apps/loanschedule/conformance/`. A parallel agent is running and
that file is shared; the driver registers all schemas in one pass. Until then
`go test ./internal/apps/loanschedule/...` FAILS its store census — EXPECTED, not yours to
fix, and not a reason to delete vectors.

## Constraints

* NEVER the `default` tenant. API only for writes; SQL is READ-ONLY verification.
* Change NO configuration row. `rounding-mode` must still read 4 and `enable-business-date`
  must still be true at the end. VERIFY BOTH and say so.
* Do NOT touch `.softhouse/guards/`, `.softhouse/conformance.sh`, or another context's harness.
* NEVER remove an assertion, a refusal or a test. No floating point on any money path.

## Done means

Per context: raw captures committed; `go run ./internal/apps/<ctx>/conformance/cmd/conformance
--root <repo>` prints VERDICT: PASS with parity_pass == vector count; `go build ./...` clean.
PROVE the harness can fail: corrupt an expected value -> FAIL; forge a capture_sha256 ->
UNUSABLE; restore -> PASS.

## Report

Per context: vector count, verdict line, the discriminating input with both rounding outcomes
or an explicit "no rounding surface", and one `shasum -a 256` beside a cited
`capture_sha256`. If workingcapital has no loans to observe and you cannot create one, SAY SO
— an honest "this context has nothing to capture yet" is a real finding, exactly as
collateral's unreachable valuation arithmetic was.
