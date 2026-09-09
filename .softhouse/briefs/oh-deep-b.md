# OH-DEEP-B — deepen loan and workingcapital from captures already on disk

Repo: /Users/buv/oh-gerege-deepb   Branch: feat/OHDEEPb (checked out)
OFFLINE. No oracle. Every observation you need is already captured and committed.

## RULE ONE

**Write each vector the moment you derive it, and commit every third.** Four runs in this
programme burned 400-633 events and produced NOTHING because they composed at the end.
Whatever is not on disk did not happen.

## What exists

    loan            27 captures, 3 vectors, 2,351 LOC — 24 unpromoted
    workingcapital  12 captures, 1 vector, 1,253 LOC — 11 unpromoted

loan already pins period-1 interest (1000.505 -> HALF_UP 1000.51), a repayment allocation
across penalty/fee/interest/principal, and a disbursement net. 24 captures remain: schedules,
transaction read-backs, waivers.
workingcapital pins one loan-list read. m_wc_loan_balance — the stored balance table whose
thirteen columns never say 'balance' — is unreached. If it is not observable through the API,
say so; that is a real finding, not a gap to paper over.

Each context already has a working harness and is registered with the shared store census.
You are adding vectors, not building infrastructure.

Read `.softhouse/capture/<ctx>/MANIFEST.json` first — its `roundingSurface` field records
what discriminates in that context and why the capture exists.

## THE BAR: a vector must be able to FAIL for a reason that matters

Do NOT promote one vector per capture to raise a count. A capture of an empty list, or a
read-back that restates an input, pins nothing. Ask of each candidate: **what wrong port
behaviour would this catch?** If the answer is "none", skip it and say so in your report.

Prefer, in order:
  1. cells where a WRONG ROUNDING or WRONG ARITHMETIC would show — the money
  2. cells where a WRONG ORDER or ALLOCATION would show — which bucket got paid, what
     sequence steps ran in
  3. cells where a WRONG ENUM ORDINAL would show — Fineract persists enums as integers and
     ACTIVE is 300, not 2
  4. structural reads, only where they pin an id or status a port could get wrong

Five seams have already proved this tenant rounds HALF_UP (charges 20925.05, provisioning
74234.32, loan 1000.51, savings 0.01, shares 0.01). If a capture contains another such tie,
pin it and state both outcomes.

## Vector rules — unchanged, and enforced by the harness

`provenance.kind = "oracle-capture"`, `provenance.capture_ref`, a REAL `shasum -a 256` in
`provenance.capture_sha256`, and `tenant_params`. Money as INTEGER MINOR UNITS in a string.
TRANSCRIBE from the committed capture; never compute. If the oracle did not show it, it does
not go in a vector. Each vector's note names the capture and the field each number came from.

The harness REFUSES a vector whose cited hash does not recompute. Do not weaken that.

## Constraints

* Touch only your contexts' vector dirs and, if a new seam needs grading, their own harness.
* Do NOT edit another context's harness, `.softhouse/guards/`, or `.softhouse/conformance.sh`.
* NEVER remove an assertion, a refusal or a test.
* No floating point on any money path.
* Run `gofmt -w` on any Go you write, before committing.

## Done means

Per context: `go run ./internal/apps/<ctx>/conformance/cmd/conformance --root <repo>` prints
VERDICT: PASS with parity_pass == vector count; `cd nexus && go build ./... && go test ./...`
clean. PROVE at least one new vector can fail: corrupt its expected value -> VERDICT FAIL;
restore -> PASS. Paste that.

## Report

Per context: vectors before and after, what each new one pins, and — importantly — **which
captures you deliberately did NOT promote and why**. A short list of vectors that each catch
a real defect beats a long list that catches nothing.
