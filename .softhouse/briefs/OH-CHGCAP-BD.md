# OH-CHGCAP-BD — CAPTURE ONLY. A loan charge partly paid, a charge waived, then the loan repaid in full.

Worktree: `/Users/buv/oh-gerege-chgcap` (branch `feat/OHCHGCAPbd`)
Work ONLY in that directory. **You hold the oracle server.** A parallel run (`OH-WOGRADE2-BE`) is oracle-free.
**A run works ONLY in its own worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/loan.md`.
2. `.softhouse/findings/F-2026-09-11-loan-graded-coverage.md` §4.4 (charges) and §4.5 (lifecycle) — the targets
   and exactly what a capture needs.
3. `.softhouse/capture/loan-writeoff-paid-instalment/OWNER.md` and its `req/` — a client + product-3 loan +
   repayment the oracle ACCEPTED today. **Copy its method and bodies.**
4. `.softhouse/capture/tierA-a2/out/A2-336*`, `A2-339*`, `A2-384*` — loan-charge read-back SHAPES (an EARLIER
   oracle instance: use them for field names only, never for ids or values).

## YOUR ENTIRE DELIVERABLE IS A COMMITTED CAPTURE — no vector, no drive, no `.go` file.

## WHY
`nexus/internal/apps/loan/charge.go` — 18 money-mutation functions over a LoanCharge's `amount / amountPaid /
amountWaived / amountOutstanding` (`UpdatePaidAmountBy`, `Waive`, `UpdateWaivedAmount`, `ReconcileFullyPaid`,
…) — is reached by no vector: every cited loan read-back has `charges: null`. And `lifecycle.go`'s
money-crossing transition (`RepaidInFull`) has no observation: no captured loan is ever paid off.

## THE OBJECTIVE — one new loan, read back after each step with `associations=all` (it carries `charges`)
1. Create a client and a **product-3** loan as the reference capture did; before disbursal (or right after,
   whichever the oracle accepts) add **two charges** with a specified due date inside the first period: a
   **fee** and a **penalty**, with **different non-round amounts** (e.g. 123.45 and 67.89 — whole minor
   units). Use existing charge definitions if suitable (read `GET /charges`); create one only if none fits.
2. **Partly pay the fee**: a repayment SMALLER than the fee's amount, timed so the allocation lands on the
   fee (the allocation order is penalty → fee → interest → principal for this product — read the capture
   of loan 12's allocation first; the oracle's allocation is the observation, not your plan). Capture.
3. **Waive the penalty** (`POST /loans/{id}/charges/{chargeId}?command=waive`). Capture.
4. **Repay the loan in full** (the oracle's `GET …/transactions/template?command=repayment` gives the amount).
   Capture the final detail: the status transition to closed/obligations-met is the lifecycle observation.

Each capture: detail (`associations=all`), transactions, journal entries. `pg_dump -Fc` snapshot of
`fineract_gerege` from **`gerege-oracle-db`** (NOT `fineract-db-1`) to `/Users/buv/gerege-oracle-snapshots/`
first; never commit a `.dump`. **Commit after each step.**

`OWNER.md`: per step, each charge's amount / amountPaid / amountWaived / amountOutstanding / paid / waived, in
integer minor units, the loan status, and which `charge.go` / `lifecycle.go` function each step observes.
**If the oracle refuses a step, THE REFUSAL IS THE RESULT** — capture it, commit, continue where possible.

## Rules of evidence
- JSON records only for anything a vector will cite; SQL read-only, corroboration only.
- Request bodies byte-stable (`123.45` must stay `123.45`). Money in integer minor units; never sub-minor.
- **Tenant `gerege` only — never `default`. No SQL inserts.** "The oracle" is the Fineract reference;
  **Oracle Database is prohibited.** PostgreSQL only.
- **Do not touch `.softhouse/guards/`, `.softhouse/conformance.sh`, `nexus/`, or `.softhouse/maps/`.**

## The bar and the budget
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~450 iterations. **`git commit -F <file>`. Never commit TASK.md.**
