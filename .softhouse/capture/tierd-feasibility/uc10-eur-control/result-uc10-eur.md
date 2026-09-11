# OH-UC10CTL-BQ — UC10 replay in EUR: **FAILED**, identically to MNT

**Question (one):** is the one-unit period-2 split in UC10 caused by the MNT re-seed, or does the
pinned build disagree with its own `.feature` test in EUR too?

**Answer: it fails identically in EUR.** The currency re-seed does not cause the split. With the
five `currency-seed-mnt.diff` currency hunks reverted to `EUR` (and only those; the build/capture
plumbing untouched), UC10 replayed against the same throwaway reference oracle fails on the same
step, at the same cells, with the same integer-minor-unit delta as under MNT. The pinned build's
arithmetic on the complex-transaction / interest-recalculation path diverges from the checked-in
feature expectation independently of currency.

## 1. Rig (as run)

* Disposable copy `/Users/buv/fineract-tierd`, branch under test, five currency constants reverted
  to EUR via `recorded-currency-only.diff` (byte-identical to the five currency hunks of
  `../uc6-mnt/currency-seed-mnt.diff`; applied reversed). Logback FEIGN appender, Feign
  `build.gradle`, `gradle.properties` (the capture plumbing) left in place.
* Throwaway compose project `tierd-oracle` over image `fineract:latest`; tenant `tierd`;
  reference-oracle DB `tierd-oracle-db` (172.27.0.2). No Oracle Database; PostgreSQL only.
* Replay: `run-uc10-eur.sh` — JDK 21 container over the copy, Feign FULL capture to
  `feign-uc10-eur.log`, feature selector `LoanRepaymentSchedule.feature:824` (UC10 alone),
  UC1..UC9/UC11/UC12 not run.
* `preflight.sh` rc=0 (`preflight.txt`); `up.sh` rc=0 (`up.txt`); `down.sh` rc=0
  (`teardown-isolation.txt`, every standing counter `== baseline`, all `tierd-*` gone).

## 2. Result

**FAILED.** Cucumber: `1 scenario (1 failed)`, `67 steps (18 passed, 48 skipped, 1 failed)`.

Failing step — `Then Loan Repayment schedule has 3 periods, with the following data for periods:`
at feature line 841, step def `LoanStepDef.loanRepaymentSchedulePeriodsCheck`
(`LoanStepDef.java:2312`), scenario line 824:

```
Wrong value in Repayment schedule of resource 1 tab line 4.
Actual values in line (with the same due date) are:
  [2, 28, 01 March 2025, null, 434.77, 429.73, 11.29, 0.0, 0.0, 441.02, 0.0, 0.0, 0.0, 441.02]
But expected values in line:
  [2, 28, 01 March 2025, null, 434.76, 429.74, 11.28, 0.0, 0.0, 441.02, 0.0, 0.0, 0.0, 441.02]
```

Period 2, money in integer minor units (EUR, 2 ISO 4217 digits):

| cell | expected | actual | delta |
| --- | --- | --- | --- |
| Balance of loan | 43476 | 43477 | +1 |
| Principal due | 42974 | 42973 | −1 |
| Interest | 1128 | 1129 | +1 |
| Due | 44102 | 44102 | 0 |

This is the **same** actual/expected tuple, the same step, and the same deltas recorded for MNT in
`F-2026-09-11-tierd-repsched-mnt-uc10.md` §3. The resource id differs only because running UC10
alone makes it the first resource created in the run (`resource 1`); in the whole-file MNT replay
it was the tenth (`resource 10`). The values are what matter and they are identical.

## 3. Currency is genuinely EUR

The capture `feign-uc10-eur.log` (115,924,781 B, 23,287 lines,
sha256 `06833c9c0b35db931c566da19fe8e4ce87288a3759ad87daa6bb008e33c943dc`) contains:

* `"code":"EUR"` × 198 and `"currencyCode":"EUR"` × 214;
* `"code":"MNT"` × 0 and `"currencyCode":"MNT"` × 0.

(The raw substring `PYMNT` appears 248 times inside product names such as
`LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` — not a currency. A plain `grep MNT` over-counts on it.)

## 4. Restore

The MNT constants were re-applied after the run. `git -C /Users/buv/fineract-tierd diff` restricted
to the five currency files is byte-identical to `recorded-currency-only.diff`, and the `logback.xml`
hunk is byte-identical to the logback hunk of `currency-seed-mnt.diff` (both checked by `diff -u`,
zero output). Full state in `post-restore-mnt-git-diff.txt`. The copy is back to the MNT state;
untracked files unchanged.

## 5. Meaning

Per the task's first branch: **fails identically in EUR** → the pinned build disagrees with its own
upstream test. The 1-minor-unit period-2 principal/interest split on the complex-transaction /
interest-recalculation path is not a currency artefact; it reproduces with `EUR` exactly. The
oracle's own output (not the `.feature` table) is what this program grades, so at this pin
`LoanRepaymentSchedule.feature`'s UC10 period-2 expectation is **not a trustworthy expectation**.
UC10's output should not be treated as a conformance signal against that table until the pinned
build and the feature file are reconciled upstream.
