# OH-PROV — capture provisioning's RESERVE ARITHMETIC and promote it to vectors

Repo: /Users/buv/oh-gerege-prov   Branch: feat/OHPROV-provisioning-entries (checked out)

## The API. Verified working. Do not go hunting for it.

    BASE='https://localhost:8443/fineract-provider/api/v1'
    AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
    TEN='Fineract-Platform-TenantId: gerege'
    CT='Content-Type: application/json'

Your first tool call is an API call, not a file read. Read a file only when a call fails.

## What already exists — read `.softhouse/capture/seed/MANIFEST.json`, do not re-derive

The oracle is seeded and the business date is PINNED to **2026-09-01**:

    4 GL accounts   1 provisioning criteria   7 clients   3 loans, ALL DISBURSED
    loan 1  62 days overdue  DOUBTFUL      50%
    loan 2  31 days overdue  SUB-STANDARD  25%
    loan 3   0 days overdue  STANDARD       1%
    criteria bands: 0-29 = 1%, 30-59 = 25%, 60-89 = 50%, 90+ = 100%

The rig that built it is `.softhouse/capture/seed/bin/run.sh` and it is IDEMPOTENT —
re-run it freely, it creates nothing twice.

## STEP 1 — fix the two gaps in the corpus FIRST

The seeded loans cannot prove what matters. Every principal is 100,000 MNT, so 1%, 25%
and 50% are all EXACT to the minor unit. A vector built on them pins band selection and
nothing about rounding.

The discrimination that proved this tenant is HALF_UP was `20925.05` vs HALF_EVEN's
`20925.04`. A round number proves nothing. So, following the seed rig's own conventions
and adding scripts beside it:

  (a) Add at least one loan with a ROUNDING-SENSITIVE principal — one where the band
      percentage lands on a fractional minor unit, so HALF_UP and HALF_EVEN would give
      DIFFERENT answers. Compute the candidate principal yourself and SAY IN YOUR REPORT
      what the two modes would each produce. If the two modes agree on your chosen
      number, it is the wrong number.
  (b) Add a loan in the LOSS band (90+ days overdue relative to 2026-09-01), which is
      currently unpopulated.

Date every new loan RELATIVE TO THE PINNED BUSINESS DATE, never to `date`/`now()`.

## STEP 2 — generate and capture the provisioning entries

    POST /provisioningentries   {"date":"01 September 2026","dateFormat":"dd MMMM yyyy",
                                 "locale":"en","createjournalentries":false}
    GET  /provisioningentries/{id}
    GET  /provisioningentries/{id}/entries

Save the request bodies under `.softhouse/capture/provisioning/req/` and the RAW,
UNMODIFIED responses under `.softhouse/capture/provisioning/out/<case>-raw.json`.
Commit the captures.

## STEP 3 — promote, transcribing only

For each observed entry write a vector under `.softhouse/vectors/provisioning/` that
TRANSCRIBES the reserved amount out of the committed capture and CITES it:

    provenance.kind           = "oracle-capture"
    provenance.capture_ref    = the path to the raw file
    provenance.capture_sha256 = the REAL `shasum -a 256` of that file
    tenant_params             = copy the shape from .softhouse/PIN-provisioning.json

NEVER compute an expected value. If the oracle did not show it, it does not go in a
vector. Each vector's note must name the capture and the field each number came from.

The existing harness is `nexus/internal/apps/provisioning/conformance` (1,544 lines). It
already refuses a vector whose cited hash does not recompute — verified. Extend it to
grade reserve-amount cells if it cannot already. Do NOT weaken any existing check.

## Constraints

* NEVER the `default` tenant. API only — no schema DDL, no INSERT/UPDATE/DELETE.
  SQL is READ-ONLY verification.
* Change NO configuration row. `rounding-mode` must still read 4 at the end — verify it.
* Do NOT edit `.softhouse/guards/`, `.softhouse/conformance.sh`, or another context's
  harness EXCEPT for the registration another schema legitimately requires.
* Never REMOVE an assertion, a refusal or a test anywhere. Adding is fine.
* Money is integer minor units. No floating point.
* COMMIT YOUR WORK.

## Done means

`go run ./internal/apps/provisioning/conformance/cmd/conformance --root <repo>` prints
VERDICT: PASS with parity_pass equal to the vector count; `cd nexus && go build ./... &&
go test ./...` clean; `bash .softhouse/conformance.sh` EXIT 2 with the probe PRINTED and
NO guard failing except the ledger guard; work committed.

## Report

The vector count; the conformance verdict line; for the rounding-sensitive loan, the
principal, the percentage, and what HALF_UP vs HALF_EVEN each give; one `shasum -a 256`
pasted beside the `capture_sha256` the vector cites for it; and anything you could not
verify. An honest gap beats a silent one.
