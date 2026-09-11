# OH-WCALLOC-AG — grade the working-capital payment-allocation order. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-wcalloc` (branch `feat/OHWCALLOCag`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**
**A run works ONLY in its own worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/workingcapital.md` — seams, vectors, drives, port functions with file:line.
2. `.softhouse/findings/F-2026-09-11-workingcapital-graded-coverage.md` §4.2 — the target.

## The target
The payment-allocation rule: the ORDER in which a repayment fills buckets. Ported as
`SplitAllocationTypes` / `JoinAllocationTypes` [`paymentallocationrule.go:32,52,76,87`] and the
classification `DueType` / `AllocationType` / `Code` [`allocationtype.go:86-108`], mirroring
`GenericEnumListConverter.java:43-57`. All at **0.0%** from the graded corpus.

## The observation — committed
`.softhouse/capture/workingcapital/out/wc-loan-detail-raw.json` (already cited by WC-02/03/04) carries the
`DEFAULT` rule as six ordered names: `DUE_PENALTY, DUE_FEE, DUE_PRINCIPAL, IN_ADVANCE_PENALTY,
IN_ADVANCE_FEE, IN_ADVANCE_PRINCIPAL`. **Verify against the file.**

## The task — ONE property
> **The observed allocation rule decodes to exactly these six types, in this order, each classified
> DUE or IN_ADVANCE and penalty / fee / principal by its name.**

Promote ONE vector (request: the rule as observed; expect: the ordered types with their due-type and
allocation-type). Drives, each discriminated here:
* **fee before penalty** (order swapped within DUE);
* **IN_ADVANCE decoded as DUE**;
* **the join/split round-trip drops or de-dups a name** — only if the observation discriminates it.

This grades a decode/classification, not arithmetic — say so plainly in the vector's note. Coverage of
the named functions must move off 0.0% from the committed-store test (`-count=1`), or say why not.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or **delete it
with the argument**. **Do not manufacture coverage.** Measure each drive against the store WITHOUT
your vector(s) and WITH them; report every count.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. **HALF_UP**, ordinal 4, precision 19.
- **Do not touch `.softhouse/guards/`** (12 pairs) or `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference; **Oracle Database is prohibited.**
- `capture_ref` must be a **JSON** capture record (the wire-float guard refuses anything else — a
  psql dump cannot be cited); `capture_sha256`, `citation`; **re-verify the hash after writing**.
  Never synthesise a value you did not observe.

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY with the line
`§4.4.2-RECORDED-DECISION-EXIT`; **"a HARD guard failed" is a failure, not the recorded decision.**
Run it EARLY and again before your last commit. ~400 iterations. **Commit by iteration 120.**
**Write commit messages to a file and use `git commit -F <file>`. Never commit TASK.md.**
**One bounded context: `workingcapital`.**
