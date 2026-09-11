# OH-TIERD8-BW — Tier D at scale: replay LoanChargeOff-Part1.feature in MNT and capture it. CAPTURE ONLY.

Worktree: `/Users/buv/oh-gerege-tierd8` (branch `feat/OHTIERD8BW`)
Work ONLY in that directory (plus the disposable copy `/Users/buv/fineract-tierd`). **A run works ONLY in its own
worktree.** The driver pushes; never exercise the push gate. OVERNIGHT QUEUE run: nobody is watching — commit after each step, and tear down even if a step fails.

## Read first — do not search
1. `.softhouse/findings/F-2026-09-11-tierd-repsched-mnt-uc10.md` and `F-2026-09-11-tierd-mnt-uc6-promotion.md` — the MNT re-seed that worked (11/11 passed),
   and the exact commands used. **Reuse them.**
2. `.softhouse/capture/tierd-feasibility/throwaway/` — the rig; `preflight.sh` now writes the standing baseline
   fail-closed. `.softhouse/capture/tierd-feasibility/bin/` — the control-tested extractor.

## YOUR ENTIRE DELIVERABLE IS A COMMITTED CAPTURE — no vector, no drive, no `.go`.

## The task
1. The disposable copy is already re-seeded to MNT and built (verify with `git -C /Users/buv/fineract-tierd diff
   --stat`; do not rebuild unless a build is actually stale).
2. `preflight.sh`, bring up the throwaway, replay **`LoanChargeOff-Part1.feature`** (charge-off: the charged-off write-off branch no capture has observed — createJournalEntriesForWriteOffsWhenLoanIsChargedOff) with the Feign capture on. Any business-date move stays inside the throwaway tenant `tierd`. If the whole file is too slow, replay a named subset and say which.
3. Record per scenario: PASSED / FAILED (a failure in MNT is a finding: which step, which value).
4. Run `bin/extract.py` over the new log; commit the per-loan read-backs for the PASSED scenarios under
   `.softhouse/capture/tierd-feasibility/chargeoff-mnt/` with a manifest and an OWNER.md: the feature file,
   each scenario, its loans, and which read-back files belong to it.
5. `down.sh`; commit `teardown-isolation.txt`. Every standing counter must equal the baseline.

## Non-negotiables
- Standing tenants `gerege` and `default` untouched — proven by the rig, not asserted. Never write into
  `/Users/buv/fineract`. Tear down every `tierd-*` container. Never `find` over `/Users/buv`.
- Money in integer minor units in anything you write. **Do not touch `nexus/`, `.softhouse/vectors/`,
  `.softhouse/guards/`, `.softhouse/conformance.sh`, or `.softhouse/maps/`.** PostgreSQL only; **Oracle Database is
  prohibited.**

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~300 iterations. **Commit the replay result table by
iteration 100**, the extraction after. **`git commit -F <file>`. Never commit TASK.md.**

**Failed scenarios:** record them (which step, actual vs expected) and commit ONLY the passing scenarios' loans, exactly as
OH-TIERD7-BU did. Do NOT decide the cause; the driver dispatches an EUR control in the morning.
