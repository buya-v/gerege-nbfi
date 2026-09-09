# OH-WC — workingcapital: SEED it, then capture and promote

Repo: /Users/buv/oh-gerege-wc   Branch: feat/OHwc (checked out)

## The API. VERIFIED 200 minutes ago. Do NOT search for it, do NOT unzip jars.

    BASE='https://localhost:8443/fineract-provider/api/v1'
    AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
    TEN='Fineract-Platform-TenantId: gerege'
    CT='Content-Type: application/json'

    GET  $BASE/working-capital-loan-products   -> 200 (currently [])
    GET  $BASE/working-capital-loans           -> 200 (currently empty)
    GET  $BASE/working-capital/near-breach     -> 200 (currently [])
    POST $BASE/working-capital-loan-products   requires: name, shortName, currencyCode,
         digitsAfterDecimal, inMultiplesOf, amortizationType  (probe it for the rest)

THE ROUTES ARE HYPHENATED. 'workingcapitalloans' is 404. A previous run burned 478 events
on the wrong spelling. The tenant currently holds NO working-capital product and NO
working-capital loan — every list is empty, which is why this context has a built harness
(861 lines, already on main) and zero vectors. YOUR FIRST JOB IS TO SEED ONE, then capture.

Your FIRST tool call is an API call. Read a file only when a call fails.

## RULE ONE: WRITE TO DISK BEFORE YOU MOVE ON

After EVERY call, save the request to `.softhouse/capture/workingcapital/req/` and the RAW response to
`.softhouse/capture/workingcapital/out/<case>-raw.json` with a `<case>.status` holding the HTTP code.
Commit as soon as a context's captures are on disk, BEFORE promoting.

**Whatever is not on disk did not happen.** Three runs today ended with 400+ events and
nothing to show; each was stopped and re-dispatched.

CAPTURES CITED BY A VECTOR MUST BE PARSEABLE JSON. The wire-float guard reads every record
a vector cites and REFUSES one it cannot parse. If you record an excerpt of Fineract source,
wrap it in a JSON object (source_commit, source_file, source_lines, verbatim as a line
array) — never a bare .txt. That exact mistake was repaired earlier today.

## What exists — `.softhouse/capture/seed/MANIFEST.json`, never re-derive it

BUSINESS DATE PINNED 2026-09-01. gerege: HALF_UP (ordinal 4), MNT, 2 minor units.
  1 office  9 clients  4 GL accounts  7 loans (5 disbursed)  2 loan products
`.softhouse/capture/seed/bin/run.sh` is idempotent. `.softhouse/capture/ohsweep/lib.sh`
holds curl helpers — reuse them.

## Then promote

Build `nexus/internal/apps/workingcapital/conformance/` on the SHARED CORE
`nexus/internal/conformance`. Follow `loan`, `savings` or `parties` — NOT loanschedule.
Include a `cmd/conformance` entrypoint.

Every vector: `provenance.kind = "oracle-capture"`, `capture_ref`, a REAL `shasum -a 256`
in `capture_sha256`, `tenant_params`. Money as INTEGER MINOR UNITS in a string. TRANSCRIBE
from the capture; never compute.

## DISCRIMINATE WHERE THE DOMAIN ALLOWS

Five seams have proved this tenant rounds HALF_UP by CONSTRUCTING an input whose raw result
lands on a half minor unit: charges 20925.05, provisioning 74234.32, loan 1000.51,
savings 0.01, shares 0.01. Do the same wherever a percentage, rate or apportionment occurs.
State the input and what HALF_UP and HALF_EVEN each give. If they agree, it is the wrong input.

Where a seam only adds integer minor units or carries no money, put an explicit
"no rounding surface" in the MANIFEST's `roundingSurface` field. An honest "none" is a
correct result — collateral's and branch's both are. Do NOT invent a tie.

## DO NOT REGISTER YOUR SCHEMA

Do NOT edit `nexus/internal/apps/loanschedule/conformance/`. A parallel agent is running and
that file is shared; the driver registers all schemas in one pass. Until then
`go test ./internal/apps/loanschedule/...` FAILS its store census — EXPECTED, not yours to
fix, and never a reason to delete vectors.

## Constraints

* NEVER the `default` tenant. API only for writes; SQL is READ-ONLY verification.
* Change NO configuration row. `rounding-mode` must still read 4 and `enable-business-date`
  must still be true at the end. VERIFY BOTH and say so.
* Do NOT touch `.softhouse/guards/`, `.softhouse/conformance.sh`, or another context's harness.
* NEVER remove an assertion, a refusal or a test. No floating point on any money path.
* Run `gofmt -w` on every Go file you write, before committing.

## Done means

Captures committed; `go run ./internal/apps/workingcapital/conformance/cmd/conformance --root <repo>`
prints VERDICT: PASS with parity_pass == vector count; `go build ./...` clean.
PROVE the harness can fail: corrupt an expected value -> FAIL; forge a capture_sha256 ->
UNUSABLE; restore -> PASS. Paste that transcript.

## Report

Vector count, the verdict line, the discriminating input with both rounding outcomes or an
explicit "no rounding surface", and one `shasum -a 256` beside a cited `capture_sha256`.
Name what you could not do and why. An honest gap beats a silent one.
