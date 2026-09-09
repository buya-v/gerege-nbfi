# OH-PROMOTE-B2 — finish loan, then savings. CONTINUE, do not restart.

Repo: /Users/buv/oh-gerege-promb   Branch: feat/OHPROMb-promote (checked out)
OFFLINE. Do NOT touch the oracle. Everything you need is committed or already in the tree.

## State you are inheriting — read this before touching anything

A previous run in THIS worktree delivered collateral (2 vectors, merged) and then ran out.
It left you real work, already on disk:

  nexus/internal/apps/loan/conformance/   1,616 lines, 11 files, BUILDS CLEANLY, UNCOMMITTED
     admit.go capability.go cmd/ conformance_test.go doc.go grade.go impl.go
     invariants.go nofloat.go report.go vector.go

That harness has ZERO vectors promoted into it. Your first job is to finish it, NOT rebuild
it. Read it, keep it, and only change what is actually wrong. Rebuilding from scratch throws
away sound work and is the wrong move.

savings has nothing yet. It comes second.

## The captures, already committed

  .softhouse/capture/loan/out/      54 raw responses + .status files
  .softhouse/capture/savings/out/   16 raw responses + .status files

Each context's MANIFEST.json carries a `roundingSurface` field recording what discriminates.
READ IT FIRST — it tells you the cell that is worth pinning and why the capture exists.

Both already have their discriminator identified. Pin these cells:

  loan     SEED-L06, principal 100050.50 at 12%/yr. Period-1 interest raw 1000.505.
           HALF_UP 1000.51, HALF_EVEN 1000.50. The oracle returned 1000.51.
           Capture: loan-L06-schedule-raw.json
  savings  1000.00 at 0.1825%/yr on a 365-day basis. Raw daily interest 0.005.
           HALF_UP 0.01, HALF_EVEN 0.00. The oracle posted 0.01.
           Capture: savings-daily-postInterest-raw.json and the account read-backs

A vector that does not pin its context's discriminating cell has missed the point of the
capture.

## Rules

Build on `nexus/internal/conformance` (the shared core). `charges`, `provisioning`,
`branch`, `shares` and `collateral` are already built on it — follow them.

Every vector: `provenance.kind = "oracle-capture"`, `provenance.capture_ref`,
`provenance.capture_sha256` = the REAL `shasum -a 256`, and `tenant_params`. Money as
INTEGER MINOR UNITS in a string. TRANSCRIBE from the capture; never compute. If the oracle
did not show it, it does not go in a vector.

## DO NOT REGISTER YOUR SCHEMA

Do NOT edit `nexus/internal/apps/loanschedule/conformance/` — census.go, vector.go or its
tests. That file is shared and the driver registers ALL new schemas in one pass.

EXPECTED, NOT YOURS TO FIX: `go test ./internal/apps/loanschedule/...` will FAIL its
store-file census because your new vectors are unaccounted for. Do not fix it by touching
loanschedule, and do not delete vectors to quiet it.

## Constraints

* No oracle. No new captures. Promotion only.
* Do NOT touch `.softhouse/guards/`, `.softhouse/conformance.sh`, or another context's harness.
* NEVER remove an assertion, a refusal or a test.
* No floating point on any money path.
* COMMIT LOAN AS SOON AS IT PASSES, before starting savings. The previous run lost its loan
  work to a run ending; do not repeat that.

## Done means

Per context: `go run ./internal/apps/<ctx>/conformance/cmd/conformance --root <repo>` prints
VERDICT: PASS with parity_pass == vector count; `cd nexus && go build ./...` clean.

PROVE each harness can FAIL: assert the HALF_EVEN answer instead of the observed one ->
VERDICT FAIL; forge a capture_sha256 -> UNUSABLE/inadmissible; restore -> PASS. Paste it.

## Report

Per context: vector count, the verdict line, the discriminating cell you pinned with both
rounding outcomes, and one `shasum -a 256` beside the `capture_sha256` a vector cites.
Name anything you could not promote and why. If you finish loan but not savings, SAY SO
plainly — a partial delivery that is honest is fine; a silent one is not.
