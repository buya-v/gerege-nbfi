# OH-DEEP-F — deepen `branch` and `shares`

Worktree: `/Users/buv/oh-gerege-deepf`  (branch `feat/OHDEEPf`, from main `ba633d10`)
Work ONLY in that directory. Never touch `/Users/buv/gerege-nbfi` or another worktree.

## The goal
Both contexts are at **2 vectors** against 11 and 10 captures. Take branch to **7+** and
shares to **7+**. Both currently have exactly ONE registered wrong implementation each —
a generic off-by-one — which means their vectors are barely graded. Fixing that matters
as much as the count.

## branch — where the value is
1. **The cashier summary is a three-point series.** `summary-cashier2-pre`,
   `summary-cashier2-post`, `summary-cashier2-final` are the same read at three moments,
   with `allocate-raw` and `settle-raw` between them. That is two deltas, and a delta
   discriminates where a single read cannot: it shows WHICH figure an allocation moved and
   by how much. This is the single most valuable thing in the branch captures — do it first.
2. **Teller and cashier identity.** `tellers-list`, `cashiers-teller1`, `cashiers-teller2`,
   `staff-list` pin row identity and mapping.
3. **Transactions.** `txns-cashier2-raw` carries the transaction rows behind the summary.

## branch — one thing you must NOT decide
`settle-3dp-probe-raw.json` records Fineract accepting and storing `txnAmount 40000.245`
— money finer than MNT's minor unit — which the Go port refuses. This divergence is
**documented in `branch/conformance/doc.go` and is awaiting a USER DECISION.** You may
neither pin it as parity nor declare it a departure. Leave it exactly as it is, work
around it, and note in your report that you did.

## shares — where the value is
1. **The lifecycle sequence.** `share-account-submit` / `-approve` / `-activate` is a full
   status progression. Pin the **stored status integer** at each step, never the label.
   Then **register a wrong impl that re-encodes the status as a contiguous Go enum ordinal**
   — the same defect class `loan-wrong-status-iota-ordinal` catches — and show it red.
2. **Dividends.** `share-dividend-create` and `shares-product-dividends` are the money
   seam. A dividend is a per-share amount times a share count, then rounded — so it is a
   rounding surface. If a capture shows a dividend whose HALF_UP and HALF_EVEN results
   differ, that is a sixth independent seam proving the tenant rounding mode, and worth
   more than any other vector in this brief. Look for it; if no capture discriminates,
   say so rather than forcing it.
3. **Product and account detail.** `share-product-detail`, `share-account-detail`.

## Registered wrong implementations
`branch-wrong-off-by-one` and `shares-wrong-off-by-one` are all that exist today. Both are
generic. **Register at least one specific wrong impl per context** encoding a real defect
— a dropped summary field, a status label used where the ordinal belongs, a dividend
rounded the wrong way — and prove each goes red.

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
