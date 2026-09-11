# F-2026-09-11 — Tier D `LoanChargesInstallmentFee` failures reproduce in EUR: the MNT re-seed is not the cause

**Status: CAPTURE COMMITTED.** `OH-CHGCTL-BV`, worktree `/Users/buv/oh-gerege-chgctl`, branch
`feat/OHCHGCTLbv`. Control replay of three failing `LoanChargesInstallmentFee.feature` scenarios
against the throwaway reference oracle on the disposable EUR copy, Feign capture on. Capture only:
no vector, no drive, no `.go`.

## 1. Question

The MNT whole-file replay (`../capture/tierd-feasibility/charges-installment-fee-mnt/`) left 13 of
28 scenarios FAILED: twelve by ONE minor unit in the final period's fee allocation, and scenario 26
(cumulative loan) by ONE CURRENCY UNIT (100 minor) in period 2's principal split. Both EUR and MNT
carry 2 ISO 4217 minor digits. The question was whether the MNT re-seed caused the failures, or
whether the pinned build disagrees with its own `.feature` in EUR too.

## 2. Method

The tested UC10 control (`../capture/tierd-feasibility/uc10-eur-control/`, `F-2026-09-11-tierd-repsched-mnt-uc10.md`)
was reused unchanged: revert the five currency constants of
`../capture/tierd-feasibility/uc6-mnt/currency-seed-mnt.diff` to `EUR` in the disposable copy
`/Users/buv/fineract-tierd` only (Feign/build plumbing untouched), `preflight.sh`, throwaway up,
replay, `down.sh`, restore MNT and prove it. Image
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, tenant `tierd`.
Three scenarios replayed alone, selected by anchored Cucumber `name` regex: **26** (`C3890`,
100-minor-unit period-2 split) and two of the twelve one-minor-unit fee failures — **4** (`C3786`,
percent-interest) and **7** (`C3788`, all-charges). Replay window `2026-09-11T13:15:25Z →
13:17:06Z`.

## 3. Result — 3 scenarios (0 passed, 3 failed); 90 steps (38 passed, 49 skipped, 3 failed)

Every one of the three **FAILS in EUR**, on the same step, the same period and the same cells as
the MNT whole-file replay.

| # | TestRailId | feature line | failing step | resource | period (tab line) | cell | expected | actual (EUR) | actual (MNT) | delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | C3786 | 257 | 265 | 1 | 6 (7) | Fees | 0.00 | 0.01 | 0.01 | +1 |
| 4 | C3786 | 257 | 265 | 1 | 6 (7) | Due / Outstanding | 17.04 | 17.05 | 17.05 | +1 |
| 7 | C3788 | 509 | 517 | 2 | 6 (7) | Fees | 10.34 | 10.35 | 10.35 | +1 |
| 7 | C3788 | 509 | 517 | 2 | 6 (7) | Due / Outstanding | 27.38 | 27.39 | 27.39 | +1 |
| 26 | C3890 | 2026 | 2039 | 3 | 2 (3) | Balance of loan | 63.00 | 62.00 | 62.00 | −100 |
| 26 | C3890 | 2026 | 2039 | 3 | 2 (3) | Principal due | 12.00 | 13.00 | 13.00 | +100 |
| 26 | C3890 | 2026 | 2039 | 3 | 2 (3) | Due / Outstanding | 22.00 | 23.00 | 23.00 | +100 |

Money in integer minor units (EUR, 2 digits). The step def is identical throughout:
`LoanStepDef.loanRepaymentSchedulePeriodsCheck` (`LoanStepDef.java:2312`), message
`Wrong value in Repayment schedule of resource N tab line L`. Only the resource id differs
(1/2/3 here vs 4/7/26 in the whole-file replay), because the three scenarios ran alone.

The Feign capture is currency-clean EUR: `"code":"EUR"` × 15442, `"currencyCode":"EUR"` × 214,
MNT currency objects × 0 (sha256 `afae99b6…d0dda43`, 120067584 B / 25314 lines).

## 4. Restore and isolation

The five currency constants were restored to MNT; the diff of the six files named by
`currency-seed-mnt.diff` is byte-identical to that recorded diff. `down.sh` exit 0: every
`tierd-*` container, network and volume gone; every standing counter `== baseline`, standing
health 200, baseline hash `3e94854b…e637541` unchanged. Standing tenants untouched;
`/Users/buv/fineract` never written. Evidence:
`.softhouse/capture/tierd-feasibility/charges-eur-control/`.

Bar: `bash .softhouse/conformance.sh` → **exit 2**, and the only exit-2 line is
`conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded run
completed and the bar is refused by that recorded decision`; no `HARD guard failed`, no vector
mismatch (`.softhouse/capture/tierd-feasibility/charges-eur-control/conformance.txt`). `nexus/`,
`.softhouse/vectors/`, `.softhouse/guards/`, `.softhouse/conformance.sh`, `.softhouse/maps/`
untouched; no `.go` touched.

## 5. Meaning

**Same failures in EUR, therefore:** the pinned build **disagrees with its own tests**; the MNT
re-seed does not change charge allocation. The oracle's MNT output is gradeable — the 15 PASSED
scenarios of the MNT capture stand, and the 13 failures are pin-vs-feature disagreements to be
reconciled upstream, not Tier D defects. The one-minor-unit final-period fee remainder and the
scenario-26 period-2 100-minor-unit principal shift are the same pin-vs-feature family as the
UC10 period-2 split in `F-2026-09-11-tierd-repsched-mnt-uc10.md`: a rounding/boundary choice the
build makes differently from the checked-in expectation, in either currency.
