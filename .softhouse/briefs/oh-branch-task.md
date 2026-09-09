# OH-BRANCH — seed, capture and pin the teller/cashier cash movements

Repo: /Users/buv/oh-gerege-branch   Branch: feat/OHBRANCH-teller-cashier (checked out)

## The API. Verified working right now. Do not go hunting for it.

    BASE='https://localhost:8443/fineract-provider/api/v1'
    AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
    TEN='Fineract-Platform-TenantId: gerege'
    CT='Content-Type: application/json'

Your FIRST tool call is an API call, not a file read. Read a file only when a call fails.
A previous task in this program spent 579 events reading and issued zero POSTs. Do not.

## What exists already — read `.softhouse/capture/seed/MANIFEST.json`, never re-derive it

The oracle is seeded and the BUSINESS DATE IS PINNED to **2026-09-01**. Tenant `gerege`:
HALF_UP (ordinal 4), precision 19, MNT, 2 minor units, Asia/Ulaanbaatar.

    1 office   9 clients   4 GL accounts   1 provisioning criteria   5 loans (disbursed)
    tellers 0   cashiers 0   staff 0   <- YOUR domain is empty; you seed it

The idempotent rig is `.softhouse/capture/seed/bin/run.sh`. Follow its conventions and add
your steps beside it as new numbered scripts. Re-run it freely; it creates nothing twice.

## STEP 1 — seed the teller/cashier chain (API only)

    POST /staff                                   (staff=0; a cashier IS a staff member)
    POST /tellers                                 (name/office/status/valid-from)
    POST /tellers/{tellerId}/cashiers             (assign staff, from/to dates)
    POST /tellers/{tellerId}/cashiers/{id}?command=allocate   (cash IN to the till)
    POST /tellers/{tellerId}/cashiers/{id}?command=settle     (cash OUT of the till)

Date everything RELATIVE TO 2026-09-01, never to `date`/`now()`. Prefix names `SEED-`.
Make it idempotent: check-then-create.

## STEP 2 — THE AMOUNTS MUST DISCRIMINATE. This is the point of the task.

A previous context was seeded entirely with 100,000 MNT and every result came out exact,
so the vectors proved band selection and NOTHING about arithmetic. Do not repeat that.

Choose allocate/settle amounts so that at least one derived figure — a running till
balance, or a sum over several transactions — lands on a HALF minor unit, where HALF_UP
and HALF_EVEN would DIFFER. In your report state the amounts, the derived figure, and
what each rounding mode would produce. **If the two modes agree on your numbers, they are
the wrong numbers.**

If the teller/cashier seam turns out to do no rounding at all — plain integer minor-unit
addition with no percentage or division anywhere — then SAY SO EXPLICITLY in your report
rather than inventing a tie that the domain does not have. An honest "this seam has no
rounding surface" is a correct and useful result. Do not fabricate one.

## STEP 3 — capture, raw and committed

Request bodies to `.softhouse/capture/branch/req/`, RAW UNMODIFIED responses to
`.softhouse/capture/branch/out/<case>-raw.json`. Capture the READ-BACKS too:
GET /tellers, GET /tellers/{id}/cashiers, GET /tellers/{id}/cashiers/{id}/transactions,
and the cashier summary/template if one exists. Commit the captures.

## STEP 4 — build the harness and promote

`nexus/internal/apps/branch` has NO conformance harness. Build one modelled on
`nexus/internal/apps/provisioning/conformance` (~1,600 lines, the current best template).
Do NOT model it on loanschedule (10,899) or ledger (7,422) — wrong generation, 7x the size.

Reuse, do not fork: `nexus/internal/floatguard` for the no-float guard, and provisioning's
provenance refusals (a vector whose cited capture hash does not recompute is INADMISSIBLE).
Include a `cmd/conformance` entrypoint — grading runs from the binary, not from `go test`.

Every vector: `provenance.kind = "oracle-capture"`, `provenance.capture_ref`, a REAL
`shasum -a 256` in `provenance.capture_sha256`, and `tenant_params`. Money as INTEGER
MINOR UNITS, as a string. TRANSCRIBE only — never compute an expected value. If the
oracle did not show it, it does not go in a vector.

Register the new schema with the shared store census the way charges/provisioning are
registered in `nexus/internal/apps/loanschedule/conformance` — that registration is
REQUIRED, not a scope violation, or loanschedule's census will refuse the store.

## Constraints

* NEVER the `default` tenant. API only for writes — no schema DDL, no INSERT/UPDATE/DELETE.
  SQL is READ-ONLY verification.
* Change NO configuration row. `rounding-mode` must still read 4 at the end. VERIFY it.
* Do NOT edit `.softhouse/guards/` or `.softhouse/conformance.sh`.
* NEVER remove an assertion, a refusal, or a test anywhere. Adding is fine.
* No floating point on any money path.
* COMMIT YOUR WORK.

## Done means

`go run ./internal/apps/branch/conformance/cmd/conformance --root <repo>` prints
VERDICT: PASS with parity_pass == vector count; `cd nexus && go build ./... && go test ./...`
clean; `bash .softhouse/conformance.sh` EXIT 2 with the probe PRINTED and NO guard failing
except the ledger guard (that one is red BY RECORDED DECISION, DEC-2 §4.4.2 — correct and
expected); work committed.

## Report

Vector count; the verdict line; the discriminating amounts and what HALF_UP vs HALF_EVEN
each give (or an explicit statement that this seam has no rounding surface); one
`shasum -a 256` pasted beside the `capture_sha256` a vector cites for it; and anything you
could not verify. An honest gap beats a silent one.
