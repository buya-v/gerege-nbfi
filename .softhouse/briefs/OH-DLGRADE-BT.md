# OH-DLGRADE-BT — grade delinquency pause periods and installment-level delinquency. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-dlgrade` (branch `feat/OHDLGRADEbt`)
Work ONLY in that directory. **Take no captures. Start no container.** **A run works ONLY in its own worktree.**
The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/loan.md` — the `loan-delinquent-days` seam and its vectors (OH-DELINQ-U), drives, port functions.
2. `.softhouse/findings/F-2026-09-11-loan-graded-coverage.md` §4.2 and §4.6 — the two targets.
3. `.softhouse/capture/tierd-feasibility/delinquency-mnt/OWNER.md` and its manifests — 49 loans from the MNT replay of
   `LoanDelinquency-Part1.feature` (50/50 passed); driver count: 141 read-backs with populated
   `delinquencyPausePeriods`, 309 with installment-level delinquency. Hash-verified by the driver (1,026 entries).
4. The provenance rule for these throwaway captures: copy it from any `LN-TD-*` vector.

## The targets (both 0.0% from the graded corpus today)
* **Pause periods** — the paused/grace arms of `DelinquentDays` (`nexus/internal/apps/loan/delinquency.go`): days inside a
  delinquency pause do not count. The existing seam cannot carry a pause period today.
* **Installment-level delinquency** — `AggregateInstallmentDelinquency` (`delinquency.go:47`): per-installment
  delinquency summed into range buckets.

## The task — two properties, commit each separately
1. Extend the `loan-delinquent-days` seam with the pause-period input the observations carry (declare it exactly the way
   the seam's existing fields are admitted — `admit.go`, `vector.go`), and promote vectors where a pause changes the
   delinquent-day count versus the same loan without it. Drive: **pause ignored** (paused days counted).
2. Add a seam for installment-level delinquency (a graded-domain capability), promote vectors from loans with
   installment-level buckets. Drives: **all installments lumped into one bucket**; **installment in the wrong range**.
Aim for 4–8 vectors in total, one per distinct shape. Measure every drive WITHOUT and WITH your vectors; coverage of the
two targets must move off 0.0% from the committed-store test (`-count=1`). **Any refusal is a finding, never relaxed.**

## Non-negotiables
- **No balance-named field written** by any seam or drive (the I-3 guard: express defects through inputs, as
  OH-CHGGRADE-BI had to). Integer minor units / integer days; no float. `capture_ref` a JSON record; `capture_sha256`.
- **Do not touch `.softhouse/guards/`** (baseline **8** pairs), `.softhouse/conformance.sh`, captures, or `.softhouse/maps/`.
  **One bounded context: `loan`.** PostgreSQL only; **Oracle Database is prohibited.** Controls: 365 → **48**.

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`, ledger findings == baseline. ~450 iterations. **Commit property 1
by iteration 150.** **`git commit -F <file>`. Never commit TASK.md.**
