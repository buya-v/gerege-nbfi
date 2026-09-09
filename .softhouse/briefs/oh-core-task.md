# OH-CORE — extract the shared conformance core. NO new contexts, NO oracle.

Repo: /Users/buv/oh-gerege-core   Branch: feat/OHCORE-shared-harness (checked out)

## Why

Four conformance harnesses exist — ledger, loanschedule, charges, provisioning — and they
are largely the SAME CODE copied four times:

    admit.go       4 harnesses   3580 lines
    vector.go      4             3328
    grade.go       4             2588
    invariants.go  4             1324
    capability.go  4             1176
    report.go      3             1162
    money.go       2              240
    nofloat.go     3               86   (already thin — it delegates to internal/floatguard)

Eleven more contexts are coming. Copying this a fifth through fifteenth time is the single
largest avoidable cost in the programme. `nofloat.go` was already extracted to
`nexus/internal/floatguard` and that extraction was verified LOSSLESS — follow that model.

## What to build

`nexus/internal/conformance` — the shared core. Move into it everything that is genuinely
context-independent:

  * vector envelope: schema/case_id/class/context/provenance/tenant_params types
  * provenance admission: kind must be `oracle-capture`; `capture_ref` must resolve to a
    committed file; `capture_sha256` must RECOMPUTE and match, else INADMISSIBLE
  * the store loader and the per-schema claim/hand-over protocol
  * capability registry default-deny
  * the report line (`vectors_loaded= parity_pass= parity_fail= refused= inadmissible=`)
  * minor-unit money parsing and the no-float token rejection
  * the `cmd/conformance` scaffolding

Each context keeps ONLY: its own vector shape, its own expectation cells, its own grader,
its own seam vocabulary.

## THE CONSTRAINT THAT DECIDES THIS TASK

**85 vectors currently grade. All 85 must still grade, with identical verdicts, after your
refactor.** Record the before and after for each:

    ledger 17    loanschedule 50    charges 10    provisioning 8

Run each context's `cmd/conformance` BEFORE you start and paste the output. Run it again at
the end and paste it. Any change in `parity_pass`, `parity_fail`, `refused` or
`inadmissible` for any context is a FAILURE of this task, not a detail to explain away.

**Refusals must not decrease.** Count `problems = append` across all harness code before and
after. The total may RISE (dedup often reveals a check one copy had and another lacked —
if so, say which). It must not FALL. If a check exists in three copies and not the fourth,
the shared version applies it to all four: report that as a BEHAVIOUR CHANGE with the
context and check named, do not hide it.

## Prove it, do not assert it

For at least one context, after the refactor:
  * corrupt a vector's expected value  -> VERDICT FAIL, parity_fail=1
  * corrupt a `capture_sha256`         -> VERDICT UNUSABLE, inadmissible=1
  * restore                            -> VERDICT PASS
Paste that transcript. A harness that cannot fail is not a harness.

## Constraints

* Do NOT touch `.softhouse/guards/`, `.softhouse/conformance.sh`, or any vector or capture
  file. This is a pure Go refactor. If a vector must change, you have done it wrong.
* NEVER delete a test or an assertion to make the refactor land.
* No oracle access is needed or permitted for this task.
* No floating point on any money path.
* COMMIT YOUR WORK.

## Done means

All four contexts grade with unchanged verdicts; `cd nexus && go build ./... && go test ./...`
clean; `bash .softhouse/conformance.sh` EXIT 2 with the probe PRINTED and NO guard failing
except the ledger guard (red BY RECORDED DECISION, DEC-2 §4.4.2 — correct); total harness
line count materially reduced; refusal count not reduced; committed.

## Report

Before/after verdict lines for all four contexts; before/after total harness line count;
before/after refusal count; any behaviour change dedup revealed, named; the corrupt/restore
transcript. An honest "I could not share X because the contexts genuinely differ" is a fine
result — forcing false commonality is worse than leaving duplication.
