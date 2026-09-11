# OWNER — Tier D `LoanChargesInstallmentFee.feature` EUR control (`charges-eur-control`)

This directory owns the **EUR control** read-backs for the Tier D `LoanChargesInstallmentFee`
capture. It answers one question, OH-CHGCTL-BV: **do the 13 MNT failures of the whole-file
replay happen because of the MNT re-seed, or does the pinned build disagree with its own
`.feature` in EUR too?**

Capture only: no vector, no drive, no `.go`. The run works only in its own worktree
(`/Users/buv/oh-gerege-chgctl`, branch `feat/OHCHGCTLbv`) against the disposable copy
`/Users/buv/fineract-tierd`; `/Users/buv/fineract` is never written.

## Answer

**Same failures in EUR.** All three replayed scenarios fail in EUR on exactly the steps, periods
and cells that they fail on in MNT. The five currency constants were reverted to `EUR` in the
disposable copy (and only those — the Feign/build plumbing untouched), the throwaway oracle was
rebuilt at the pinned image, the Feign capture was on, and the values are byte-for-byte the MNT
values. Therefore the pinned build disagrees with its own upstream `.feature` expectations, and
the oracle's MNT output is gradeable: the MNT re-seed does **not** change charge allocation.

## The three scenarios replayed

Chosen from `../charges-installment-fee-mnt/scenario-results.json`: scenario 26 (the
100-minor-unit period-2 principal split) and two of the twelve one-minor-unit final-period fee
failures — scenario 4 (`C3786`, percent-interest) and scenario 7 (`C3788`, all-charges). Selected
by anchored Cucumber `name` regex so that the like-named scenarios 17 and 27 do not match.

| # | TestRailId | feature line | failing step line | product | principal (major) | resource | result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | C3786 | 257 | 265 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_INTEREST_CHARGES` | 100 | 1 | FAILED |
| 7 | C3788 | 509 | 517 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_ALL_CHARGES` | 100 | 2 | FAILED |
| 26 | C3890 | 2026 | 2039 | `LP2_DOWNPAYMENT` | 100 | 3 | FAILED |

Resource ids are 1/2/3 because only three scenarios ran (in the whole-file MNT replay they were
4/7/26). The step definition is the same in every case:
`LoanStepDef.loanRepaymentSchedulePeriodsCheck` (`LoanStepDef.java:2312`), message
`Wrong value in Repayment schedule of resource N tab line L`.

## Result — 3 scenarios (0 passed, 3 failed); 90 steps (38 passed, 49 skipped, 3 failed)

The failing line is `[Nr, Days, Date, Paid date, Balance of loan, Principal due, Interest, Fees,
Penalties, Due, Paid, In advance, Late, Outstanding]`; money is integer minor units (EUR, 2 ISO
4217 minor digits).

| # | period (tab line) | cell | expected | actual (EUR) | actual (MNT, whole-file) | delta |
| --- | --- | --- | --- | --- | --- | --- |
| 4 | 6 (7) | Fees | 0.00 | 0.01 | 0.01 | +1 |
| 4 | 6 (7) | Due / Outstanding | 17.04 | 17.05 | 17.05 | +1 |
| 7 | 6 (7) | Fees | 10.34 | 10.35 | 10.35 | +1 |
| 7 | 6 (7) | Due / Outstanding | 27.38 | 27.39 | 27.39 | +1 |
| 26 | 2 (3) | Balance of loan | 63.00 | 62.00 | 62.00 | −100 |
| 26 | 2 (3) | Principal due | 12.00 | 13.00 | 13.00 | +100 |
| 26 | 2 (3) | Due / Outstanding | 22.00 | 23.00 | 23.00 | +100 |

Raw actual/expected arrays (also machine-readable in `scenario-results.json`):

```
# 4  actual   [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 0.01, 0.0, 17.05, 0.0, 0.0, 0.0, 17.05]
# 4  expected [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 0.00, 0.0, 17.04, 0.0, 0.0, 0.0, 17.04]
# 7  actual   [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.35, 0.0, 27.39, 0.0, 0.0, 0.0, 27.39]
# 7  expected [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.34, 0.0, 27.38, 0.0, 0.0, 0.0, 27.38]
# 26 actual   [2, 31, 01 February 2024, null, 62.0, 13.0, 0.0, 10.0, 0.0, 23.0, 0.0, 0.0, 0.0, 23.0]
# 26 expected [2, 31, 01 February 2024, null, 63.0, 12.0, 0.0, 10.0, 0.0, 22.0, 0.0, 0.0, 0.0, 22.0]
```

The MNT column is the `actual` array recorded for these scenarios in
`../charges-installment-fee-mnt/replay-result-table.md`; it is identical to the EUR `actual` in
every cell. EUR and MNT both carry 2 minor digits, and the EUR control shows the arithmetic is
currency-independent: the re-seed is not the cause.

## Method and rig

The method is the tested one from `../uc10-eur-control/` (OH-UC10CTL-BQ), reused unchanged:
revert the five currency constants of `../uc6-mnt/currency-seed-mnt.diff` to `EUR` in the
disposable copy only, run `preflight.sh`, bring the throwaway up, replay with the Feign capture
on, `down.sh`, then restore MNT.

* copy: `/Users/buv/fineract-tierd` (disposable); image `fineract:latest`
  `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, proven identical to the
  standing reference oracle by `preflight.sh` (`rc=0`, PREFLIGHT OK).
* tenant `tierd`; DBs `fineract_tenants`, `fineract_tierd`; PostgreSQL only.
* `docker compose -p tierd-oracle -f docker-compose.tierd.yml up -d --wait --wait-timeout 600`,
  health `https://localhost:8444/fineract-provider/actuator/health` = 200.
* replay `2026-09-11T13:15:25Z → 13:17:06Z`, `rc=1` (the three scenario failures);
  `run-charges-eur.sh`, Feign capture at
  `fineract-e2e-tests-runner/build/capture/feign-installmentfee-eur.log`
  (`120067584 B` / `25314` lines, sha256 `afae99b6…d0dda43`).
* capture is currency-clean EUR: `"code":"EUR"` × 15442, `"currencyCode":"EUR"` × 214,
  `"code":"MNT"` / `"currencyCode":"MNT"` × 0.

## Restore and isolation

* MNT restored by applying `mnt-currency-restore.diff` (the 5-currency EUR→MNT patch); the
  resulting diff of the six files named by `../uc6-mnt/currency-seed-mnt.diff` is
  **byte-identical** to that file (`post-restore-seed-diff.txt`, sha256 match), and the five
  constants read `MNT` again.
* `down.sh` exit 0: all `tierd-*` containers, the `tierd-oracle` network and volume are gone;
  every standing counter `== baseline`, standing health 200 (`teardown-isolation.txt`). The
  baseline hash is unchanged: `3e94854b…e637541`.
* Standing tenants `gerege` and `default` untouched; `/Users/buv/fineract` never written.
* `bash .softhouse/conformance.sh` **exit 2**, only exit-2 line
  `§4.4.2-RECORDED-DECISION-EXIT`; no `HARD guard failed`, no vector mismatch
  (`conformance.txt`).

## Meaning (the decision branch)

This is the **same-failures-in-EUR** branch of OH-CHGCTL-BV: the pinned build disagrees with its
own tests, so the oracle's MNT output is gradeable. The MNT capture's 15 PASSED scenarios remain
valid, and the 13 failures are pin-vs-feature disagreements — recorded as such, not as Tier D
defects. See `.softhouse/findings/F-2026-09-11-tierd-charges-mnt-eur-control.md`.

## Artifact index

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `scenario-results.json` | machine-readable per-scenario result, resource, actual/expected, deltas |
| `replay-charges-eur.log` | raw Gradle/cucumber replay console log (ANSI) |
| `replay-charges-eur.plain.log` | same log with ANSI stripped |
| `run-charges-eur.sh` | the exact replay driver (scenario name filter) |
| `preflight.txt` | TierD preflight + isolation guard + standing baseline |
| `up.txt` | `docker compose … up` output |
| `teardown-isolation.txt` | `down.sh` baseline-vs-teardown comparison |
| `conformance.txt` | `bash .softhouse/conformance.sh` output (exit 2, recorded-decision marker) |
| `feign-charges-eur.sha256` | Feign capture path, size, line count, sha256, currency-token census |
| `mnt-currency-restore.diff` | 5-currency EUR→MNT patch applied to restore the copy |
| `post-restore-seed-diff.txt` | post-restore diff of the six seed files, == `currency-seed-mnt.diff` |
