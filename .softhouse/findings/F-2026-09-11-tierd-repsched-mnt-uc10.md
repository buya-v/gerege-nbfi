# F-2026-09-11 — Tier D `LoanRepaymentSchedule.feature` replayed in MNT: 11/12 pass, UC10 splits by 1 minor unit

**Status: CAPTURE COMMITTED.** `OH-TIERD5-BP`, worktree `/Users/buv/oh-gerege-tierd5`,
branch `feat/OHTIERD5bp`. Whole-file replay of the 12 progressive-schedule scenarios against the
throwaway reference oracle on the disposable MNT-reseeded copy, with the Feign capture on. This
is capture only: no vector, no drive, no `.go`.

## 1. Capture

`.softhouse/capture/tierd-feasibility/repayment-schedule-mnt/`:

* `replay-result-table.md` — the result table and the UC10 failure.
* `replay-repsched-mnt.log` — raw cucumber/Gradle replay log (1,619 lines).
* `run-repsched-mnt.sh` — the exact driver; its copy at `throwaway/` was used unchanged.
* `scenario-results.json` — per-scenario PASSED/FAILED.
* `OWNER.md` — feature file, each scenario, its loan, and each read-back file.
* `manifest-repsched.json` (all 12 loans, `committed` flag) and `manifest-repsched-passed.json`
  (committed files only) — source line, bytes, sha256 per body.
* `summary-repsched.json` — extractor totals.
* `loans/loan-<id>/` — the per-loan exchanges for the 11 PASSED scenarios (402 files).
* `teardown-isolation.txt` — baseline-vs-teardown counter comparison.

Extraction command (the control-tested extractor): `bin/extract.py feign-repsched-mnt.log --out <dir>`
over the 159,152,907 B / 43,468-line Feign log: 1,652 exchanges, 364 loan-keyed, 12 loans, 424
files, 11,078,728 kept body bytes. Every committed body carrying a currency object resolves to
`code = "MNT"` (2 minor digits); the literal token `EUR` appears nowhere. The throwaway ran image
`fineract:latest` = `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`,
proven identical by `preflight.sh` to the standing reference oracle. Capture window
2026-09-11T10:34:02Z → 10:35:03Z.

## 2. Result — 12 scenarios (11 passed, 1 failed); 408 steps (359 passed, 48 skipped, 1 failed)

| UC | feature line | result | loan | read-backs |
| --- | --- | --- | --- | --- |
| UC1..UC9 | 5/76/147/218/272/326/380/528/676 | PASSED | 1..9 | committed |
| **UC10** | 824 | **FAILED** | 10 | not committed (aborted) |
| UC11, UC12 | 1070/1315 | PASSED | 11, 12 | committed |

One loan per scenario; loan `N` is UC`N`, proven by each read-back's `loanProductName` matching
the scenario's product (P139/P135/P137 rotate exactly) and by the UC10 failure naming
`resource 10`.

## 3. The failure (a finding)

**UC10** — complex transactions, interest recalculation enabled, partial-period interest enabled
— fails on the step at feature line 841:

> `Then Loan Repayment schedule has 3 periods, with the following data for periods:`

Step def `LoanStepDef.loanRepaymentSchedulePeriodsCheck` (`LoanStepDef.java:2312`):

```
Wrong value in Repayment schedule of resource 10 tab line 4.
Actual:   [2, 28, 01 March 2025, null, 434.77, 429.73, 11.29, 0.0, 0.0, 441.02, ...]
Expected: [2, 28, 01 March 2025, null, 434.76, 429.74, 11.28, 0.0, 0.0, 441.02, ...]
```

Period 2, money in **integer minor units** (MNT, 2 digits):

| cell | expected | actual | delta |
| --- | --- | --- | --- |
| Balance of loan | 43476 | 43477 | +1 |
| Principal due | 42974 | 42973 | −1 |
| Interest | 1128 | 1129 | +1 |
| Due | 44102 | 44102 | 0 |

MNT and EUR both carry 2 ISO 4217 minor digits (496 / 978), so this 1-minor-unit
principal/interest boundary split is **not** attributable to the currency re-seed. It is the
oracle's rounding of the period-2 split on the complex-transaction path diverging from the
checked-in `.feature` expectation. No other scenario failed and no other step failed.

## 4. Isolation and the bar

* `preflight.sh` wrote `throwaway/out/STANDING-baseline.txt` (12 counters over `fineract-db-1`
  and `gerege-oracle-db`); after the replay `down.sh` reported **every counter `== baseline`**,
  standing health 200, exit 0 (`teardown-isolation.txt`). All `tierd-*` containers, the
  `tierd-oracle` network and its volume are gone. Standing tenants `gerege` and `default`
  untouched; `/Users/buv/fineract` never written. PostgreSQL only; no Oracle Database.
* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit-2 line is
  `conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded run
  completed and the bar is refused by that recorded decision`; no `HARD guard failed`.
* `nexus/`, `.softhouse/vectors/`, `.softhouse/guards/`, `.softhouse/conformance.sh`,
  `.softhouse/maps/` untouched (branch diff restricted to those paths is empty); no `.go`
  touched; `.softhouse/vectors/loan/` still 32.

## 5. What this establishes

The MNT re-seed makes the schedule seam replayable at scale: 11 of 12 progressive-schedule
scenarios reproduce their `.feature` expected values under MNT and yield MNT read-backs suitable
for future promotion. The single UC10 divergence is a 1-minor-unit period-2 split on the
complex-transaction/recalculation path and is recorded here, with the exact step and values, as
the one MNT replay finding.

## 6. Follow-up control — **OH-UC10CTL-BQ**: UC10 in EUR fails identically (2026-09-11)

The MNT replay left one open question in §3: whether the 1-minor-unit period-2 split was a
currency artefact. A control replay of **UC10 alone** (feature line 824) was run on the same
disposable copy with the five currency constants of `uc6-mnt/currency-seed-mnt.diff` reverted to
`EUR` (and only those; the Feign/build plumbing untouched), against the same throwaway reference
oracle, tenant `tierd`. Evidence:
`.softhouse/capture/tierd-feasibility/uc10-eur-control/` (`replay-uc10-eur.log`,
`result-uc10-eur.md`, `teardown-isolation.txt`, `post-restore-mnt-git-diff.txt`,
`feign-uc10-eur.sha256`).

**Result: FAILED, identically.** Same step (`LoanRepaymentSchedule.feature:841`,
`LoanStepDef.loanRepaymentSchedulePeriodsCheck`), same period-2 cells, same delta:

| cell | expected | actual (EUR) | actual (MNT, §3) | delta |
| --- | --- | --- | --- | --- |
| Balance of loan | 43476 | 43477 | 43477 | +1 |
| Principal due | 42974 | 42973 | 42973 | −1 |
| Interest | 1128 | 1129 | 1129 | +1 |
| Due | 44102 | 44102 | 44102 | 0 |

The Feign capture is currency-clean EUR (`"code":"EUR"` × 198, `"currencyCode":"EUR"` × 214,
`MNT` currency objects × 0). Only the resource id differs (`resource 1` here vs `resource 10` in
the whole-file replay), a consequence of UC10 running alone. The five currency files were then
restored and verified byte-identical to the recorded MNT diff, and `logback.xml` to the recorded
plumbing hunk.

**Meaning.** The split is **not** caused by the MNT re-seed. The pinned build disagrees with its
own upstream `.feature` expectation on the complex-transaction / interest-recalculation path in
`EUR` as well. At this pin the program's oracle output — not the feature table — is the graded
expectation, so `LoanRepaymentSchedule.feature`'s UC10 period-2 value is **not a trustworthy
expectation** until the build and the feature file are reconciled upstream. This removes the last
currency-attributable doubt from §3 and leaves the divergence as a pin-vs-test disagreement, not a
Tier D defect.

