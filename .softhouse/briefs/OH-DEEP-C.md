# OH-DEEP-C — deepen `savings` and `workingcapital` from captures already on disk

Worktree: `/Users/buv/oh-gerege-deepc`  (branch `feat/OHDEEPc`, from main `8c00b69f`)
Work ONLY in that directory. Never touch `/Users/buv/gerege-nbfi` or any other worktree.

## The goal, stated as a number
`savings` has 3 parity vectors against 1,862 non-comment Go lines (1.6 per 1k).
`workingcapital` has 2 against 1,253 (1.6 per 1k). By contrast `loanschedule` has 28.2.
Raise both. Target: savings 3 -> 6+, workingcapital 2 -> 5+. Quality beats count —
a vector that pins nothing is worse than no vector, because it reads as coverage.

## What you may and may not do
- **PROMOTE from captures already in `.softhouse/capture/`.** Do not run a new oracle pass.
  savings has 8 raw captures, workingcapital has 12. Most are unpromoted.
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

## The two seams worth your attention
1. **savings — the deposit and interest-posting paths.** Captures exist for
   `savings-daily-deposit`, `savings-daily-postInterest`, `savings-account-monthly`.
   The status ordinals (200 approved / 300 active) are already pinned with a permanent
   red-drive; do not re-pin them. What is unpinned is the money: what a deposit does to
   the balance, and what `postInterest` computes. Pin the observed values.
2. **workingcapital — draw and repayment.** Captures exist for `wc-loan-submit`,
   `wc-loan-approve`, `wc-loan-disburse`, `wc-loan-detail`. The balance IS observable
   through the **detail** endpoint (not the list — that was a prior mistake, corrected).
   The balance decomposition vector already exists; extend to the disbursement seam.

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
Commit to `feat/OHDEEPc` with a message naming what each vector discriminates.
Do not merge to main, do not push. When done, write a short report covering:
- each vector added, and the wrong implementation it catches
- any ORACLE GAP you hit (a value no capture contains)
- the final `ledger-invariants-compare` line, verbatim
