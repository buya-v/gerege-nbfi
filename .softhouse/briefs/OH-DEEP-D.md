# OH-DEEP-D — deepen `loan` from the 27 captures already on disk

Worktree: `/Users/buv/oh-gerege-deepd`  (branch `feat/OHDEEPd`, from main `8c00b69f`)
Work ONLY in that directory. Never touch `/Users/buv/gerege-nbfi` or any other worktree.

## The goal, stated as a number
`loan` has 6 parity vectors against 2,351 non-comment Go lines (2.6 per 1k), and
**27 raw captures on disk** — the largest unpromoted backlog in the programme. By
contrast `loanschedule` has 28.2 per 1k. Target: loan 6 -> 14+. Quality beats count —
a vector that pins nothing is worse than no vector, because it reads as coverage.

## What you may and may not do
- **PROMOTE from captures already in `.softhouse/capture/loan/`.** Do not run a new
  oracle pass. There are 27 raw captures: `loan-{1..N}-detail`, `-schedule`,
  `-transactions`, and several `-after` pairs. Most are unpromoted.
- **Never synthesise a value you did not observe in a capture.** If a field you want to
  pin is absent from every capture, say so in the report and move on — that is an ORACLE
  GAP, and inventing the number is the one unrecoverable failure here.
- **SQL is READ-ONLY**, for verification only. Writes go through the API.
- **Never write to the `default` tenant.**
- `enable-business-date` is the ONLY configuration row you may change.

## Non-negotiables (a violation is a rejection, not a discussion)
- Money is **integer minor units**. No float in any money path, struct field, column,
  API field, or test fixture — including intermediates. MNT = ISO 496, minor unit 2.
- Balances are **derived, never written** (I-3). Append-only (I-4).
- Rounding is **HALF_UP** (RoundingMode ordinal 4), precision **19**, tz Asia/Ulaanbaatar.
- PostgreSQL only.

## The seams worth your attention
The `-after` capture pairs are the valuable ones: a `-detail`/`-transactions` pair taken
before and after a transaction is a **delta**, and a delta discriminates far more than a
single read. Prefer them.

1. **The repayment allocation order.** A repayment splits across penalty, fee, interest
   and principal in a defined order. A `-transactions`/`-transactions-after` pair shows
   the split. Pin it — a transposed allocation order is a real defect class this catches.
2. **Schedule period arithmetic.** `loan-N-schedule` captures carry per-period principal,
   interest and outstanding. `LN-L03-summary-total-outstanding` (9773365) already pins the
   per-loan-then-sum aggregation ORDER; extend to the per-period figures.
3. **Status ordinals.** Loan status values are non-sequential (`ACTIVE=300`). Where a
   capture shows one, pin the stored integer, not the label.

## A vector must DISCRIMINATE
For each vector, state in its own file what wrong implementation it would catch.
"It matches" is not a reason to add it. If a vector would pass against both HALF_UP and
HALF_EVEN, or against both a correct and a transposed field order, it discriminates
nothing — either construct it so it fails against the wrong answer, or drop it.

## Schema registration — FOUR sites, all of them
Adding a schema context to a conformance package means editing all four or the harness
lies about its own coverage:
  1. `vector.go` — `SchemaContexts()`
  2. `vector.go` — the `FileDeclares*` and `Claimed*` slices
  3. `coverage_refusal_test.go` — the `Declares` list
  4. `store_integrity_test.go` — `FilePaths`
**Read the actual exported names first.** Do not derive an identifier from a directory
name — a prior run invented `FileDeclaresCobSchema` when the export was
`FileDeclaresCOBSchema`, and it did not compile.

## The bar
Run from the worktree root, and it must be green before you commit:
```
cd nexus && go build ./... && go test ./...
gofmt -l . | tee /dev/stderr | wc -l    # must be 0
bash ../.softhouse/guards/ledger-invariants-compare.sh
```
`ledger-invariants-compare.sh` must report **exactly 12 (class, file) pairs, none added,
none silenced**. If your change adds a pair, either fix the code or add the baseline row
**with an argument for why it stands and a REMOVAL CONDITION** — never silently.

**gofmt immediately.** If you patch a file with a script, run `gofmt -w` in the SAME
command. Two prior runs left files unformatted and the bar refused them.

## Commit and report
Commit to `feat/OHDEEPd` with a message naming what each vector discriminates.
Do not merge to main, do not push. When done, write a short report covering:
- each vector added, and the wrong implementation it catches
- any ORACLE GAP you hit (a value no capture contains)
- the final `ledger-invariants-compare` line, verbatim
