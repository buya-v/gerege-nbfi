# OH-LIFECYCLE-BN — grade the loan lifecycle state machine from observed transitions. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-lifecycle` (branch `feat/OHLIFECYCLEbn`)
Work ONLY in that directory. **Take no captures.** **A run works ONLY in its own worktree.** The driver pushes;
never exercise the push gate. **This is an OVERNIGHT QUEUE run: nobody is watching — commit early and often.**

## Read first — do not search
1. `.softhouse/maps/loan.md`.
2. `.softhouse/findings/F-2026-09-11-loan-graded-coverage.md` §4.5 — the target.
3. `nexus/internal/apps/loan/lifecycle.go` — `NextStatus :37`, `TotalOutstandingIsZero :144`,
   `NoTransition :157`, `DetermineTransition :171`.

## The observations — all committed captures from TODAY's instance
* submit → approve → disburse: `.softhouse/capture/loan/out/loan-L06-{submit,approve,disburse}-raw.json`.
* repaid in full → `closed.obligations.met` (600): `.softhouse/capture/loan-charge-partial-waive-repaid/out/
  loan-18-{after-waive,final}-detail-raw.json` (loan 18).
* written off → `closed.written.off` (601): `.softhouse/capture/loan11-writeoff-four-bucket/out/loan-11-{before,after}-detail-raw.json`
  and `.softhouse/capture/loan-writeoff-paid-instalment/out/loan-13-*-detail-raw.json`.
Verify each status code / id against the files.

## The task — ONE property
> **Given the observed status, event and outstanding facts, the next status is the one the oracle reported.**
Add a seam (e.g. `loan-status-transition`) and a graded-domain capability, declared the way the existing loan
seams are. Promote one vector per observed transition (submit, approve, disburse, repaid-in-full, write-off).
Drives: **repaid-in-full ignored** (stays active when outstanding reaches zero); **write-off closes as
obligations-met**; **approve skipped** (submitted → active). Measure each WITHOUT and WITH your vectors.
Coverage of `NextStatus` / `DetermineTransition` must move off 0.0% from the committed-store test (`-count=1`).

## Non-negotiables
- **No balance-named field written** by any drive or seam (the I-3 guard; express defects through inputs, as
  OH-CHGGRADE-BI had to). **Do not touch `.softhouse/guards/`** (baseline **8** pairs), `.softhouse/conformance.sh`,
  captures, or `.softhouse/maps/`. `capture_ref` a JSON record; `capture_sha256`. **One bounded context: `loan`.**
  PostgreSQL only; **Oracle Database is prohibited.** Controls: `loanschedule-wrong-days-in-year-365` → **48**.

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`, ledger findings == baseline. ~300 iterations. **Commit by
iteration 80, then after each vector.** **`git commit -F <file>`. Never commit TASK.md.**
