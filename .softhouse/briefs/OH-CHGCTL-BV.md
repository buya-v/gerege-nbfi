# OH-CHGCTL-BV — the control: do the LoanChargesInstallmentFee failures happen in EUR too? CAPTURE ONLY.

Worktree: `/Users/buv/oh-gerege-chgctl` (branch `feat/OHCHGCTLbv`)
Work ONLY in that directory (plus the disposable copy `/Users/buv/fineract-tierd`). **A run works ONLY in its own
worktree.** The driver pushes; never exercise the push gate. The overnight queue is running a `loan` Go run beside
you; you touch no Go and no vector.

## Read first
1. `.softhouse/capture/tierd-feasibility/charges-installment-fee-mnt/OWNER.md`, `replay-result-table.md`,
   `scenario-results.json` — in MNT, 13 of 28 scenarios failed: twelve by ONE minor unit in the final period's fee
   allocation, scenario 26 (cumulative loan) by ONE CURRENCY UNIT (100 minor) in period 2's principal split.
2. `.softhouse/capture/tierd-feasibility/uc10-eur-control/` — the UC10 control: the exact method to revert the five
   currency constants to EUR, replay, and restore MNT. **Reuse it.**
3. `.softhouse/capture/tierd-feasibility/uc6-mnt/currency-seed-mnt.diff`.

## The question — ONE
**Are these failures caused by the MNT re-seed, or does the pinned build disagree with its own test in EUR too?**
1. Revert the five currency constants to `EUR` in the disposable copy only (as the UC10 control did).
2. `preflight.sh`, throwaway up, replay **three** failing scenarios of `LoanChargesInstallmentFee.feature` alone —
   **scenario 26** (the 100-minor-unit split) and **two** of the one-minor-unit fee failures (pick them from
   `scenario-results.json` and say which) — with the Feign capture on; `down.sh`.
3. For each: PASSED or FAILED in EUR, and if failed, actual vs expected cells.
4. Restore MNT and confirm the copy matches `currency-seed-mnt.diff`.
5. Write the result into the charges capture's OWNER.md and a finding:
   * **same failures in EUR** → the pinned build disagrees with its own tests; the oracle's MNT output is gradeable;
   * **pass in EUR** → the MNT currency seed changes charge allocation (e.g. in-multiples-of / rounding of the seeded
     currency) — find WHICH currency property differs (read the seeded currency rows of both runs) and say it; no charge
     scenario from the MNT capture may be promoted until the seed is fixed and the scenarios re-replayed.
   * **mixed** → say exactly which.
Commit under `.softhouse/capture/tierd-feasibility/charges-eur-control/`.

## Non-negotiables
Standing tenants untouched (proven by the rig's fail-closed baseline and teardown). Never write into
`/Users/buv/fineract`. Tear down every `tierd-*` container. Never `find` over `/Users/buv`. **Do not touch `nexus/`,
`.softhouse/vectors/`, `.softhouse/guards/`, `.softhouse/conformance.sh`, or `.softhouse/maps/`.**

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~200 iterations. **`git commit -F <file>`. Never commit TASK.md.**
