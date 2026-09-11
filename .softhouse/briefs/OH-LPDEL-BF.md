# OH-LPDEL-BF — delete loanproduct's unwired progressive-recomputation kernel. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-lpdel` (branch `feat/OHLPDELbf`)
Work ONLY in that directory. **A run works ONLY in its own worktree.** The driver pushes; never exercise the
push gate.

## The decision — made by Buyan on 2026-09-11. Not re-decidable here.
OH-LPCOV-AL found (`.softhouse/findings/F-2026-09-11-loanproduct-graded-coverage.md` §5.1) that
`nexus/internal/apps/loanproduct/` carries a progressive-recomputation kernel — the port of Fineract's
progressive EMI / rate-factor arithmetic — that **no application imports** and **no vector reaches**: a
duplicate of the schedule arithmetic `loanschedule` owns and grades under DEC-1. Buyan chose: **delete it.**
Dead duplicate money code is a divergence risk the next reader would have to rule out.

## The task
Delete the kernel and ONLY the kernel:
* candidates: `calculator.go`, `dates.go`, `interestperiod.go`, `interestrate.go`, `money.go`,
  `repaymentperiod.go`, `schedulemodel.go`, and their `_test.go` files (`calculator_test.go`,
  `interestperiod_test.go`, …).
* **Keep** `relateddetail.go`, `frequency.go`, `method.go`, `doc.go`, their tests, and the whole
  `conformance/` package. If a KEPT file needs a symbol from a deleted file (e.g. a type in `money.go`), keep
  THAT symbol — move it into the file that uses it, unchanged — and say so. Do not rewrite anything.
* Confirm first, with `go list -deps` / grep over the whole module, that nothing outside the package imports
  a kernel symbol. **If something does, STOP and report it** — that would contradict the finding.
* Update `doc.go` (and the `loanproduct` row of the finding, §5.1) to say the kernel was removed on Buyan's
  decision, why, and that the arithmetic lives in `loanschedule`.

## Proof that nothing graded depended on it
Before and after, record and compare: `go build ./...`; `go test ./...`; loanproduct's 17 vectors pass
(`capcount.sh <wt> loanproduct loanproduct-go` → 0); all 4 loanproduct drives kill as before
(`kills.sh loanproduct <impl> <wt>` for each); the bar. The committed-store test must still pass.

## Non-negotiables
- **Do not touch `.softhouse/guards/`, `.softhouse/conformance.sh`, `nexus/internal/apps/loanschedule/`, or
  `.softhouse/maps/`.** **One bounded context: `loanproduct`.** No float anywhere.

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~150 iterations. **`git commit -F <file>`. Never
commit TASK.md.**
