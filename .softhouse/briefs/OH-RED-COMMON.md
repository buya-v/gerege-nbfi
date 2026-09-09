
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
