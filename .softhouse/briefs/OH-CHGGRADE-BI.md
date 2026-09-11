# OH-CHGGRADE-BI — grade the loan-charge lifecycle from loan 18. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-chggrade` (branch `feat/OHCHGGRADEbi`)
Work ONLY in that directory. **Take no captures.** **A run works ONLY in its own worktree.** The driver
pushes; never exercise the push gate. **Model credit is limited — be direct; do not explore.**

## Read first — do not search
1. `.softhouse/maps/loan.md` — seams, vectors, drives (file:line), port functions.
2. `.softhouse/capture/loan-charge-partial-waive-repaid/OWNER.md` — every figure, per step.
3. `nexus/internal/apps/loan/charge.go` — the port (`UpdatePaidAmountBy :191`, `Waive :169`,
   `UpdateWaivedAmount :243`, `ReconcileFullyPaid :133`, `CalculateOutstanding :61`, the predicates).

## The observation (driver-traced from the raw read-backs)
Loan 18, product 3 — fee 123.45 (12345), penalty 67.89 (6789):
    created        fee paid 0     waived 0     outstanding 12345 | penalty outstanding 6789
    repay 100.00   fee paid 10000 outstanding 2345, paid=false   | penalty untouched
    waive penalty  penalty waived 6789, outstanding 0, waived=true, paid=false
    repay in full  fee paid 12345, outstanding 0, paid=true      | loan closed.obligations.met

## The task — ONE property
> **A charge's outstanding is amount − paid − waived; a payment moves paid up to the amount and flips
> `paid` only when nothing is left; a waiver moves the whole outstanding into waived.**

Add a seam (e.g. `loan-charge-lifecycle`) and a capability in the graded domain, declared exactly the way the
existing loan seams are (`.softhouse/capabilities-loan.json`, `conformance/vector.go`, `admit.go`).
Request: the charge's amount and penalty flag + an ordered list of operations (`pay <minor>`, `waive`) taken
from the observed transactions; Expect: after each operation, the charge's paid / waived / outstanding and
the paid / waived flags — as observed. Promote vectors for the fee (created → partial → full) and the penalty
(created → waived), each citing its JSON read-backs by path and sha256.

Drives, each discriminated here:
* **partial payment marks paid** (flag flips before outstanding reaches 0) — the partial step moves;
* **waiver leaves outstanding** (waived recorded, outstanding not reduced);
* **waiver counts as paid** (sets `paid` instead of `waived`);
* **outstanding ignores waived** (amount − paid only).
Measure each WITHOUT and WITH your vectors; report every count. Coverage of `UpdatePaidAmountBy`, `Waive`,
`UpdateWaivedAmount` must move off 0.0% from the committed-store test (`-count=1`).

## Non-negotiables
- Integer minor units; no float. `capture_ref` a JSON record; `capture_sha256`; re-verify.
- **Do not touch `.softhouse/guards/`** (baseline **8** pairs), `.softhouse/conformance.sh` (census 17), captures,
  or `.softhouse/maps/`. **One bounded context: `loan`.** PostgreSQL only; **Oracle Database is prohibited.**
- Controls: `loanschedule-wrong-days-in-year-365` → **48**, `parties-wrong-iota-ordinals` → 12.

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~300 iterations. **Commit by iteration 80.**
**`git commit -F <file>`. Never commit TASK.md.**
