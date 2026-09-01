# Tier D test corpus → golden vectors

This directory holds the **source-derived golden-vector corpus** produced by
Phase 7. Each vector is mined from the legacy Apache Fineract test corpus
(`/Users/buv/fineract`, pinned at commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`)
and records the oracle behaviour asserted by a specific integration test or
end-to-end (Gherkin) scenario. They are the grading targets for the new Go
"Nexus" architecture.

## What is here

- `index.json` — inventory of every vector in this corpus.
- `TD-<CTX>-<NN>.json` — one golden vector per file.

22 vectors across 10 Nexus contexts:

| context | vectors |
|---|---|
| `charges` | TD-CHG-001 … TD-CHG-007 |
| `loan` | TD-LOAN-001 … TD-LOAN-004 |
| `loanproduct` | TD-LP-001 |
| `workingcapital` | TD-WC-001 |
| `savings` | TD-SAV-001 … TD-SAV-003 |
| `provisioning` | TD-PRV-001 |
| `origination` | TD-ORIG-001 |
| `cob` | TD-COB-001 |
| `parties` | TD-PTY-001 |
| `shares` | TD-SHR-001 … TD-SHR-002 |

## Schema

`schema` is `gerege.tierd.vector/v1`. Each vector carries:

- `case_id`, `context`, `class` (always `source-derived`), `title`.
- `source` — `kind` (`integration-test` | `e2e-scenario`), `path`, `test`
  (test method or scenario name), `testrail_id`, `fineract_commit`.
- `nexus_target` — Go package in `nexus/internal/apps/...` that this grades.
- `scenario` — prose description of the exact behaviour exercised.
- `inputs` — the deterministic inputs, with money in integer minor units.
- `expect` — the golden assertions, with money in integer minor units.
- `refusal` — present only for cases whose oracle result is a refusal
  (`http_status`, API `code`, and/or `message_contains`).
- `grade` — prose predicate an implementer/generator uses to grade the Go
  behaviour.

## Money convention

Every monetary value is an **integer minor unit**, stored as a JSON string
(`"10000"`, `"1643"`), never a float. The field name ends in `_minor` and the
minor-unit scale is declared once in `inputs.currency.minor_unit_digits`.
For example `principal_minor: "100000"` with `minor_unit_digits: 2` is
`1000.00`. Percentages and rate inputs are carried as decimal strings
(`"2.5067"`, `"2.5"`) so no rounding is introduced by the JSON encoding.

## Relationship to the parity vector store

This corpus is **not** the parity vector store. The parity store lives in
`.softhouse/vectors/<context>/` and is the only place the conformance harness
(`.softhouse/conformance.sh`) scans; its vectors have `class: parity`,
`contract-refusal`, or `selftest`, are produced from oracle captures, and are
guarded by `guard_no_float_in_vectors`.

Tier D vectors have `class: source-derived`. They are graded independently by
the application-level Go test suites (or a future Tier D grader), not by the
loanschedule parity harness. Promoting one of these into a parity vector
requires a separate, mandate-carrying task (a real oracle capture run + the
promotion script), which is intentionally out of scope here.

## Provenance & fidelity

Values in `expect` are transcribed from the assertions/literals in the cited
test (for example, the charge-rounding numbers are derived from the exact
`applyRoundingRules`/`calculateExpectedPercentageCharge` arithmetic the test
itself asserts; the working-capital schedule cells are read directly from the
`WorkingCapitalLoanRepayment.feature` table). The `source.path` + `source.test`
pair lets every vector be traced back to its originating test.

## Scope note (residual corpus)

This is a representative slice, not an exhaustive dump. The full Fineract test
corpus is far larger (533 integration-test Java files and 267 e2e stepdef Java
files observed at the pinned commit). Additional vectors can be mined with the
same convention and appended to `index.json`.
