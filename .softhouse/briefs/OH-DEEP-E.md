# OH-DEEP-E — finish the `loan` promotion backlog

Worktree: `/Users/buv/oh-gerege-deepe`  (branch `feat/OHDEEPe`, from main `ba633d10`)
Work ONLY in that directory. Never touch `/Users/buv/gerege-nbfi` or another worktree.

## The goal
`loan` has **9 vectors against 27 captures** — the largest unpromoted backlog left.
The previous run took it 6 → 9 and stopped short of its target. Take it to **18+**.

## Where the value is
The three existing summary-total vectors pin `totalOutstanding` from the detail read-back.
Almost everything else in those 27 captures is unpinned. In rough order of worth:

1. **The repayment allocation order.** A repayment splits across penalty, fee, interest and
   principal in a defined order. The `-transactions` / `-transactions-after` capture pairs
   show the split as a **delta**. The existing `LN-L01-...-after-waiver` pair is the model:
   it proved the waiver moved interest and nothing else. Do that for repayments.
2. **Per-period schedule arithmetic.** `loan-N-schedule` captures carry per-period
   principal, interest and outstanding. Only the aggregate is pinned. Pin the periods —
   and note that `loanschedule` already proves per-loan-then-sum aggregation ORDER, so a
   period vector that ties to the same total corroborates it from a second direction.
3. **Lifecycle status transitions.** `loan-L06-{submit,approve,disburse}` is a full
   sequence. Loan status ordinals are non-sequential (`ACTIVE=300`). Pin the STORED
   INTEGER at each step, never the label — `loan-wrong-status-iota-ordinal` exists
   precisely to catch a port that re-encodes 300 as the Go enum's 3.

## Registered wrong implementations you must keep red
`loan-wrong-half-even-schedule-interest`, `loan-wrong-status-iota-ordinal`,
`loan-wrong-summary-interest-not-outstanding`. If you pin a repayment allocation, the
existing three probably cannot see it — **register a wrong impl that allocates in the
wrong order** and show it goes red.

## What you may and may not do
- **PROMOTE from captures already on disk.** Do not run a new oracle pass.
  Captures live at `.softhouse/capture/<context>/out/*-raw.json` — note the `out/`.
- **Never synthesise a value you did not observe in a capture.** If a field you want to
  pin is absent from every capture, say so in the report and move on — that is an ORACLE
  GAP, and inventing the number is the one unrecoverable failure here.
- **SQL is READ-ONLY**, for verification only. Writes go through the API.
- **Never write to the `default` tenant.** `enable-business-date` is the only
  configuration row you may change.

## Non-negotiables (a violation is a rejection, not a discussion)
- Money is **integer minor units**. No float in any money path, struct field, column,
  API field, or test fixture — including intermediates. MNT = ISO 496, minor unit 2.
- Balances are **derived, never written** (I-3). Append-only (I-4).
- Rounding is **HALF_UP** (RoundingMode ordinal 4), precision **19**, tz Asia/Ulaanbaatar.
- PostgreSQL only.

## A vector must DISCRIMINATE — and you must PROVE it does
State in each vector's `_note` what wrong implementation it catches. Then prove it:
```
go run ./internal/apps/<ctx>/conformance/cmd/conformance -root <worktree> -list-implementations
go run ./internal/apps/<ctx>/conformance/cmd/conformance -root <worktree> -impl <wrong-name>
```
The correct impl must be **PASS**, and each registered wrong impl must be **FAIL** with a
non-zero `parity_fail`. Record those counts in your commit message.

**If a seam you pin has no wrong implementation that can see it, REGISTER ONE.** A vector
whose only red-drive is a generic off-by-one is barely graded. Add a wrong impl that
encodes the specific defect — a dropped field, a transposed order, a label used where the
stored ordinal belongs — and show it goes red.

## Two traps that have already cost this programme time
1. **`go test ./...` does not grade every context.** Some `conformance` packages have NO
   test files; their harness is the `cmd/conformance` binary. A green `go test` proves
   nothing about them. **Always run the binary with `-root` and read the VERDICT line.**
2. **Read exported names before using them.** Do not derive an identifier from a directory
   name — a prior run invented `FileDeclaresCobSchema` when the export was
   `FileDeclaresCOBSchema`, and it did not compile.

## Schema registration — FOUR sites where the package has a conformance_test.go
  1. `vector.go` — `SchemaContexts()`
  2. `vector.go` — the `FileDeclares*` and `Claimed*` slices
  3. `coverage_refusal_test.go` — the `Declares` list
  4. `store_integrity_test.go` — `FilePaths`
Miss one and the harness misreports its own coverage.

## The bar — green before you commit
```
cd nexus && go build ./... && go test ./...
gofmt -l .                                    # only loanschedule/contract/contract.go may appear; it is pre-existing
bash ../.softhouse/guards/ledger-invariants-compare.sh
```
The guard must report **exactly 12 (class, file) pairs, none added, none silenced**. If
your change adds a pair, fix the code, or add the baseline row **with an argument for why
it stands and a REMOVAL CONDITION** — never silently.

**gofmt immediately.** If you patch a file with a script, run `gofmt -w` in the SAME
command. Two prior runs left files unformatted and the bar refused them.

## COMMIT BEFORE YOU EXIT
A prior agent finished good work and exited with seven files uncommitted. **Commit each
increment as you finish it**, do not batch to the end. Do not merge to main, do not push.

## Report when done
- each vector added, and the wrong implementation it catches
- the red-drive FAIL counts, verbatim
- any ORACLE GAP you hit (a value no capture contains)
- the final `ledger-invariants-compare` line, verbatim
