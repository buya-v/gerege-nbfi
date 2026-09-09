# OH-PROMOTE-B — promote committed captures into graded vectors: loan, savings and collateral

Repo: /Users/buv/oh-gerege-promb   Branch: feat/OHPROMb-promote (checked out)
OFFLINE TASK. Do NOT touch the oracle. Everything you need is already committed.

## What exists

`.softhouse/capture/<context>/` holds RAW oracle responses captured in one pass, each with
a `.status` file, plus `req/` bodies, `bin/` scripts and a `MANIFEST.json`. The MANIFEST's
`roundingSurface` field records, per context, whether a rounding surface exists and what
the discriminating input was. READ IT FIRST — it tells you what is worth pinning.

Tenant params (already established, do NOT re-derive): HALF_UP, ordinal 4, precision 19,
MNT, 2 minor units, Asia/Ulaanbaatar. Business date pinned 2026-09-01.

## Your contexts: loan, savings and collateral

For EACH, build `nexus/internal/apps/<context>/conformance/` and promote its captures.

## The harness — build on the SHARED CORE, do not copy a harness

`nexus/internal/conformance` (717 lines) already provides: the vector envelope, provenance
admission, the store loader and claim protocol, capability default-deny, minor-unit money,
no-float rejection, the report line, and the pin. `charges` and `provisioning` are built on
it — read those two as the pattern.

Your context supplies ONLY its own vector shape, expectation cells, grader and seam
vocabulary. If you find yourself writing hundreds of lines that already exist in the core,
stop and use the core.

Include a `cmd/conformance` entrypoint: grading runs from the binary, not from `go test`.

## Promotion rules — TRANSCRIBE, never compute

Every vector: `provenance.kind = "oracle-capture"`, `provenance.capture_ref` pointing at the
committed raw file, `provenance.capture_sha256` = its REAL `shasum -a 256`, and
`tenant_params`. Money as INTEGER MINOR UNITS in a string.

If the oracle did not show a value, it does not go in a vector. Each vector's note must name
the capture and the field each number came from. A vector whose cited hash does not
recompute must be INADMISSIBLE — the core already enforces this; do not weaken it.

Where the MANIFEST records a discriminating input, PIN THAT CELL. It is the reason the
capture exists. Where it records "no rounding surface", do not invent one.

## DO NOT REGISTER YOUR SCHEMA

Do NOT edit `nexus/internal/apps/loanschedule/conformance/` — not census.go, not vector.go,
not its tests. Another task is promoting other contexts in parallel and that file is shared;
the driver registers ALL new schemas in ONE pass after merge.

CONSEQUENCE, EXPECTED, NOT YOURS TO FIX: until that registration lands,
`go test ./internal/apps/loanschedule/...` will FAIL its store-file census because your new
vectors are unaccounted for. That failure is expected. Do not "fix" it by touching
loanschedule and do not delete your vectors to make it go away.

## Constraints

* No oracle access. No new captures. Promotion only.
* Do NOT touch `.softhouse/guards/`, `.softhouse/conformance.sh`, or another context's harness.
* NEVER remove an assertion, a refusal or a test anywhere.
* No floating point on any money path.
* COMMIT YOUR WORK as you finish each context.

## Done means

For each of your contexts:
`go run ./internal/apps/<ctx>/conformance/cmd/conformance --root <repo>` prints VERDICT: PASS
with parity_pass == vector count; `cd nexus && go build ./...` clean;
`go test ./internal/apps/<ctx>/...` clean (loanschedule's failure is expected and excluded).

PROVE the harness can FAIL, per context: corrupt an expected value -> VERDICT FAIL; corrupt a
capture_sha256 -> VERDICT UNUSABLE/inadmissible; restore -> PASS. Paste that transcript.

## Report

Per context: vector count, the verdict line, which discriminating cell you pinned (or why the
seam has none), and one `shasum -a 256` beside the `capture_sha256` a vector cites. Name
anything you could not promote and why. A smaller true store beats a larger invented one.
