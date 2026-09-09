# OH-3 — the `provisioning` context: a conformance harness, then CAPTURED vectors

Repo: /Users/buv/oh-gerege-oh3   Branch: feat/OH3-provisioning (checked out)
Work ONLY in this worktree. Never touch /Users/buv/gerege-nbfi or any other worktree.
Run long commands under `caffeinate -is`.

## What this context is

`nexus/internal/apps/provisioning` (478 lines) is Fineract's loan-provisioning money core:
the criteria aggregate, age-band matching, the overlap invariant, and the reserve amount
computed from a product's outstanding balance and overdue age. `money.go:45`
`PercentageOf(value MinorUnits, percentage Percent)` is rounding-sensitive — it is exactly
the kind of arithmetic a parity vector exists to pin.

It has NO harness and NO vectors today. You are building the first ones.

## THE PIPELINE IS TWO STAGES. Do not collapse them.

A previous task was given a one-stage brief, burned 923 events and produced nothing. The
stages are separate and the second may not invent anything the first did not observe:

  1. CAPTURE  — drive the running Fineract oracle, write its RAW response to
                `.softhouse/capture/provisioning/out/<case>-raw.json`, unmodified. Commit it.
  2. PROMOTE  — write a vector that TRANSCRIBES values out of that committed file and CITES
                it: `provenance.capture_ref` = the path, `provenance.capture_sha256` = the
                real `shasum -a 256` of that file, `provenance.kind` = `oracle-capture`.

NEVER compute an expected value. If the oracle did not show it, it does not go in a vector.
A vector's note must say which capture and which field each number came from.

## The oracle

Up now: `gerege-oracle-app` / `gerege-oracle-db`, https://localhost:8443, tenant **gerege**
(NOT `default`). Tenant params, already established and NOT to be re-derived or guessed:

    rounding_mode HALF_UP, rounding_ordinal 4, precision 19,
    currency MNT, minor_units 2, timezone Asia/Ulaanbaatar

Every vector carries these as `tenant_params`. Read `.softhouse/PIN-charges.json` for the
exact shape and copy it to `.softhouse/PIN-provisioning.json`.

Leave the tenant EXACTLY as found. Read-only SQL for verification; never write to a schema,
never restart, never re-tenant. Record in your attestation that you did so.

## The harness — copy the RIGHT template

Model it on `nexus/internal/apps/charges/conformance` (1,983 lines across 13 files). That is
the SECOND-generation harness and it is the one to follow.

Do NOT model it on `loanschedule/conformance` (10,899 lines) or `ledger/conformance` (7,422).
Those are first-generation and seven times the size for the same job. If you find yourself
writing thousands of lines you have copied the wrong one.

Reuse, do not re-implement:
  * `nexus/internal/floatguard` — the shared no-float guard. Import it. Do not fork it.
  * charges' `admit.go` provenance refusals — a vector whose cited capture does not exist,
    or whose hash does not match, must be REFUSED. Carry that across.

The harness needs its own `cmd/conformance` entrypoint, as charges has, since grading runs
from the binary and not from `go test`.

## Hard constraints

* Do NOT edit any other context's harness — not charges, not loanschedule, not ledger.
* Do NOT edit `.softhouse/guards/ledger-invariants.baseline`, `.softhouse/guards/ledgerguard/`,
  `check-ledger-invariants.sh`, or `ledger-invariants-compare.sh`.
* Do NOT weaken, skip or shorten any guard anywhere.
* No floating point on any money path. Money is integer minor units. This is the first
  project non-negotiable and `floatguard` will catch you.
* Balances are DERIVED, never written (I-3). If your port needs a balance, compute it.
* PostgreSQL only.

## Definition of done

  1. `nexus/internal/apps/provisioning/conformance/` exists, modelled on charges.
  2. `.softhouse/capture/provisioning/out/` holds RAW oracle responses, committed.
  3. `.softhouse/vectors/provisioning/` holds vectors that each cite a committed capture with
     a hash that RECOMPUTES, and carry `tenant_params`.
  4. `go run ./internal/apps/provisioning/conformance/cmd/conformance --root <repo>` prints
     `VERDICT: PASS` with `parity_pass` equal to the vector count and `parity_fail=0`.
  5. `cd nexus && go build ./... && go test ./...` clean.
  6. `bash .softhouse/conformance.sh` — expect EXIT 2. That is CORRECT and expected: the
     ledger guard is red by recorded decision (DEC-2 §4.4.2, findings == baseline). What you
     must check is that NO OTHER guard fails and that the probe line PRINTS.
  7. **COMMIT YOUR WORK.** A previous task left everything uncommitted. `git add -A` and commit
     with a message stating what was captured, what was promoted, and what you verified.

## Report

State the vector count, paste the conformance verdict line, paste the `shasum -a 256` of one
capture beside the `capture_sha256` your vector cites for it, and name anything you could not
verify. If you conclude a case cannot be captured honestly, say so and leave it out — a
smaller true store beats a larger invented one.
