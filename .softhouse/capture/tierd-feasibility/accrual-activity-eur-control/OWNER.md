# OWNER — Tier D `LoanAccrualActivity-Part2` scenario 11 EUR control (`accrual-activity-eur-control`)

This directory owns the **EUR control** read-back for the single MNT failure of the whole-file
`LoanAccrualActivity-Part2.feature` replay. It answers one question, OH-ACCCTL-CG: **does scenario
11 (`@TestRailId:C3697`, feature line 1232, "Verify accrual activity of overpaid loan in case of
reversed MIR made before MIR and CBR for progressive loan - UC6") fail identically in EUR, or did
the MNT re-seed change the arithmetic?**

Capture only: no vector, no drive, no `.go`. The run works only in its own worktree
(`/Users/buv/oh-gerege-accctl`, branch `feat/OHACCCTLCG`) against the disposable copy
`/Users/buv/fineract-tierd`; `/Users/buv/fineract` is never written.

## Answer

**Same failure in EUR.** The single scenario fails in EUR on exactly the step, period and cells it
fails on in MNT, with byte-for-byte identical actual values. The five currency constants were
reverted to `EUR` in the disposable copy (and only those — the Feign/build plumbing untouched),
the throwaway oracle was rebuilt at the pinned image, and the Feign capture was on. Therefore the
pinned build disagrees with its own upstream `.feature` at line 1274, the MNT output is gradeable,
and the MNT re-seed does **not** change the arithmetic.

## The scenario replayed

| # | TestRailId | feature line | failing step line | product | resource (EUR) | resource (MNT) | result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | C3697 | 1232 (tag at 1231) | 1274 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` | 1 | 11 | FAILED |

Resource id is 1 because only this scenario ran (in the whole-file MNT replay it was loan 11). Step
definition `LoanStepDef.loanRepaymentSchedulePeriodsCheck` (`LoanStepDef.java:2312`), message
`Wrong value in Repayment schedule of resource N tab line 2.`

## Result — 1 scenario (0 passed, 1 failed); 48 steps (27 passed, 20 skipped, 1 failed)

The failing line is `[Nr, Days, Date, Paid date, Balance of loan, Principal due, Interest, Fees,
Penalties, Due, Paid, In advance, Late, Outstanding]`; money is integer minor units (2 ISO 4217
minor digits in both EUR and MNT). Only the cells that differ from the expectation are listed;
every other cell (Days 31, Date 21 April 2025, Interest 193, Fees 0, Penalties 0, Late 0,
Outstanding 10193) matches exactly.

| step line | period (tab line) | cell | expected | actual (EUR) | actual (MNT, whole-file) | delta |
| --- | --- | --- | --- | --- | --- | --- |
| 1274 | 1 (2) | Balance of loan | 22226 | 22225 | 22225 | −1 |
| 1274 | 1 (2) | Principal due | 12020 | 12021 | 12021 | +1 |
| 1274 | 1 (2) | Due | 12213 | 12214 | 12214 | +1 |
| 1274 | 1 (2) | Paid | 2020 | 2021 | 2021 | +1 |
| 1274 | 1 (2) | In advance | 2020 | 2021 | 2021 | +1 |

Raw actual/expected arrays (also machine-readable in `scenario-results.json`):

```
EUR actual   [1, 31, 21 April 2025, null, 222.25, 120.21, 1.93, 0.0, 0.0, 122.14, 20.21, 20.21, 0.0, 101.93]
EUR expected [1, 31, 21 April 2025, null, 222.26, 120.20, 1.93, 0.0, 0.0, 122.13, 20.20, 20.20, 0.0, 101.93]
MNT actual   [1, 31, 21 April 2025, null, 222.25, 120.21, 1.93, 0.0, 0.0, 122.14, 20.21, 20.21, 0.0, 101.93]
MNT expected [1, 31, 21 April 2025, null, 222.26, 120.20, 1.93, 0.0, 0.0, 122.13, 20.20, 20.20, 0.0, 101.93]
```

The MNT column is the `actual`/`expected` array recorded for loan 11 in
`../accrual-activity-mnt/replay-result-table.md`; it is identical to the EUR values in every money
cell. The arithmetic is currency-independent: the one-minor-unit split is a pin-vs-feature
disagreement, not a re-seed artifact.

## Scenario selection (anchored regex, unique)

```
NAME='^Verify accrual activity of overpaid loan in case of reversed MIR made before MIR and CBR for progressive loan - UC6$'
```

`grep -c` of the exact `Scenario:` line in `LoanAccrualActivity-Part2.feature` is **1** (line 1232;
the `@TestRailId:C3697` tag is at line 1231). The like-named `... reversed repayment ...` scenarios
UC4 (line 771) and UC5 (line 968) do **not** match, and the run reported exactly 1 scenario (1
failed). Chosen by the precedent `run-charges-eur.sh` mechanism (`-Pcucumber.name`).

## Method and rig

The method is the tested one from `../charges-eur-control/` (OH-CHGCTL-BV), itself from
`../uc10-eur-control/` (OH-UC10CTL-BQ), reused unchanged: revert the five currency constants to
`EUR` in the disposable copy only, run `preflight.sh`, bring the throwaway up, replay the named
scenario with the Feign capture on, `down.sh`, then restore MNT.

* copy: `/Users/buv/fineract-tierd` (disposable); image `fineract:latest`
  `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, proven identical to the
  standing reference oracle by `preflight.sh` (`rc=0`, PREFLIGHT OK).
* tenant `tierd`; DBs `fineract_tenants`, `fineract_tierd`; PostgreSQL only.
* `docker compose -p tierd-oracle -f docker-compose.tierd.yml up -d --wait --wait-timeout 600`,
  health `https://localhost:8444/fineract-provider/actuator/health` = 200.
* replay `rc=1` (the scenario failure); `run-accrualactivity-eur.sh`, Feign capture at
  `fineract-e2e-tests-runner/build/capture/feign-accrualactivity-eur.log`
  (`114187919 B` / `23546` lines, sha256 `52e9c2b5…ac46ed`).
* capture is currency-clean EUR: `"code":"EUR"` × 14664, `"currencyCode":"EUR"` × 214,
  `"code":"MNT"` / `"currencyCode":"MNT"` × 0 (one stray `"currencyCode":"USD"` in a validation
  payload).

## Restore and isolation

* MNT restored by applying `mnt-currency-restore.diff` (the 5-currency EUR→MNT patch) forward;
  after restore `git status --short` is byte-identical to `pre-state.txt` (recorded before the EUR
  revert), and the five currency blocks of `git diff` are **byte-identical** to
  `mnt-currency-restore.diff` (`6024 B`, IDENTICAL). The five constants read `MNT` again. See
  `restore-verification.txt` and `post-restore-seed-diff.txt`.
* `down.sh` exit 0: all `tierd-*` containers, the `tierd-oracle` network and volume are gone; every
  standing counter `== baseline`, standing health 200 (`teardown-isolation.txt`).
* Standing tenants `gerege` and `default` untouched; `/Users/buv/fineract` never written.
* `bash .softhouse/conformance.sh` **exit 2**, only exit-2 line
  `§4.4.2-RECORDED-DECISION-EXIT`; no `HARD guard failed` (`conformance.txt`).

## Incidents

A path-limited `git diff -- <5 paths>` did not return within 60 s (index refresh over the large
untracked `.../client/models/` dir). It was interrupted with Ctrl-C (exit 1) and the restore proof
was completed from the already-saved full `git diff`. No capture command (replay, up, down,
restore) was affected.

## Meaning (the decision branch)

This is the **same-failure-in-EUR** branch of OH-ACCCTL-CG: the pinned build disagrees with its own
`.feature` at line 1274, so the oracle's MNT output is gradeable. The one MNT failure is a
pin-vs-feature disagreement — not an MNT-re-seed artifact and not a Tier D defect.

## Artifact index

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `scenario-results.json` | per-scenario result, resource, actual/expected arrays, EUR/MNT deltas |
| `replay-accrualactivity-eur.log` | raw Gradle/cucumber replay console log (ANSI) |
| `replay-accrualactivity-eur.plain.log` | same log with ANSI stripped |
| `run-accrualactivity-eur.sh` | the exact replay driver (anchored scenario name filter) |
| `preflight.txt` | TierD preflight + isolation guard + standing baseline |
| `up.txt` | `docker compose … up` output |
| `teardown-isolation.txt` | `down.sh` baseline-vs-teardown comparison |
| `conformance.txt` | `bash .softhouse/conformance.sh` output (exit 2, recorded-decision marker) |
| `feign-accrualactivity-eur.sha256` | Feign capture path, size, line count, sha256, currency census |
| `mnt-currency-restore.diff` | 5-currency EUR→MNT patch applied to restore the copy |
| `post-restore-seed-diff.txt` | full post-restore `git diff` of the copy |
| `restore-verification.txt` | proof the copy is back on its MNT seed |
| `pre-state.txt` | copy state before the EUR revert (MNT seed), plus the revert/restore commands |
| `eur-applied.txt` | copy state after the EUR revert, plus the exact commands |
