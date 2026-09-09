# OH-RED-G — loanschedule has 50 vectors and NOT ONE red-drive

Worktree: `/Users/buv/oh-gerege-deepg` (branch `feat/OHDEEPg`, from main `ed729cf3`)
Work ONLY in that directory.

## The finding you are acting on
```
go run ./internal/apps/loanschedule/conformance/cmd/conformance -list-implementations
  loanschedule-go
  ledger-go                                    [-ledger-impl]
  ledger-wrong-accounting-closed-echoes-...    [-ledger-impl]
  ...eleven more ledger-wrong-* ...
```
`loanschedule-go` is the ONLY loanschedule implementation registered. **Its 50 vectors —
48 distinct facts, the largest corpus in the programme — have never been shown to fail
against anything.** The ledger context, which shares this same harness binary, carries
eleven meticulously argued wrong implementations. Loanschedule carries zero.

Every claim resting on those 50 vectors is currently unfalsified, including the
**HALF_UP** result. If a HALF_EVEN generator does not kill a loanschedule vector, then
loanschedule is not one of the seams proving the rounding mode, and we need to know that.

## Your task
Register red-drives for the loanschedule seams and MEASURE each one. Start with these,
in this order — the first is the most important thing in this brief:

1. **`loanschedule-wrong-half-even`** — the schedule generator rounding with HALF_EVEN
   instead of the tenant's HALF_UP (ordinal 4), everything else identical. Measure it.
   Whatever the number, report it: if it kills several vectors the HALF_UP claim is
   confirmed executable; if it kills none, say so plainly — that is the finding.
2. **Aggregation order.** `loanschedule` is where per-loan-then-sum order was established.
   Register a generator that sums then rounds, or rounds then sums, in the wrong order.
3. **Period boundary.** A schedule's first and last periods are where off-by-one day
   counts and inclusive/exclusive boundaries live. Register the boundary read the wrong
   way — the same defect class as `ledger-wrong-closure-boundary-exclusive`.
4. **Days-in-year.** `DAYS_360` vs `DAYS_365` changes every interest cell. `loanproduct`
   already has `loanproduct-wrong-swap-days360-365`; loanschedule consumes the value and
   has no equivalent.

If a seam has no vector that can see it, say so — do not invent one. A capture may exist
that could; `.softhouse/capture/loanschedule/` is the place to look.

## What a red-drive is, and the standard it must meet
A red-drive is a registered, DELIBERATELY WRONG implementation of a seam. Its job is to
prove the vectors can fail. Register it with `RegisterWrong(name, defect, evaluator)`.

The `defect` string is not a label — it is the ARGUMENT. Study the ledger context's
`RegisterWrong` calls before you write one; they are the standard in this repo. Each says
what the wrong port does, WHY a competent porter would write it (a real misreading of the
Fineract source, cited by file and line), and WHICH vector kills it. Example of the tone:

  "gets the closure BOUNDARY exactly right and echoes the WRONG DATE back ... The two
   throw sites five lines apart disagree -- :631 DOES echo the transaction date, for
   FUTURE_DATE -- so a porter who reads one and generalises writes this. It is
   INDISTINGUISHABLE from a correct port on LDG-REFUSE-04 ... and it dies on
   LDG-REFUSE-06 alone"

**A red-drive nobody would plausibly write is worth little.** Do not register
"returns 42". Register the defect a careful porter actually produces: a misread boundary,
a generalised special case, a dropped third key component, a label used where the stored
ordinal belongs, an aggregation performed in the wrong order, a rounding mode inherited
instead of pinned.

**Every red-drive must be MEASURED, never asserted:**
```
go run ./internal/apps/<ctx>/conformance/cmd/conformance -root <worktree> -impl <name>
```
Record the exact `parity_fail=N` and name which vectors die. If a red-drive kills ZERO
vectors, that is a REAL FINDING — it means the store cannot see that defect. Say so in
your report and, if a capture on disk could see it, promote that vector too.

## Non-negotiables (a violation is a rejection, not a discussion)
- Money is **integer minor units**. No float in any money path, struct field, column, API
  field, or test fixture — including intermediates. MNT = ISO 496, minor unit 2.
- Balances are **derived, never written** (I-3). Append-only (I-4).
- Rounding is **HALF_UP** (ordinal 4), precision **19**, tz Asia/Ulaanbaatar.
- PostgreSQL only. Never write to the `default` tenant. SQL is read-only.
- **Never synthesise a value you did not observe in a capture.** Captures are at
  `.softhouse/capture/<ctx>/out/*-raw.json`. Do not run a new oracle pass.

## Do NOT pad
A previous run was told "reach 18 vectors" and reached it by cloning: 18 vectors carrying
10 distinct (request, expect) pairs, six of them grading the identical fact. Eight were
thrown away. **You are not measured on vector count.** You are measured on distinct facts
graded and defects provably caught. Before adding a vector, check no existing vector
already grades that exact (request, expect) pair.

## Two traps that have already cost this programme time
1. **`go test ./...` does not grade every context.** Some conformance packages have no
   test files; their harness is the `cmd/conformance` binary. Always run the binary.
2. **Read exported names before using them.** Do not derive an identifier from a
   directory name.

## The bar — green before you commit
```
cd nexus && go build ./... && go test ./...
gofmt -l .        # only loanschedule/contract/contract.go may appear; pre-existing
bash ../.softhouse/guards/ledger-invariants-compare.sh    # must say exactly 12 pairs
```
**Run `gofmt -w` in the SAME command as any scripted patch.**

## COMMIT EACH INCREMENT AS YOU FINISH IT
A prior agent finished good work and exited with seven files uncommitted; another was
stopped and its staged index had to be recovered from dangling blobs. Commit as you go.
Do not merge to main, do not push.

## Report
- each red-drive registered, its argument, and its MEASURED parity_fail
- any red-drive that killed zero vectors, and why
- the final `ledger-invariants-compare` line, verbatim
