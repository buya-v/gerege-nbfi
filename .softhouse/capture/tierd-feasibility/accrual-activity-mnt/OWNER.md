# OWNER — Tier D `LoanAccrualActivity-Part2.feature` MNT capture (OH-TIERD11-CC / CC2, finished by the driver)

Replay of the whole `LoanAccrualActivity-Part2.feature` (35 scenarios) against the throwaway reference oracle,
tenant `tierd` (image `sha256:e596339626bf…`, Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency re-seeded to MNT),
with the Feign capture on. Capture only: no vector, no drive, no `.go`. Money in this file and the join is integer
minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies keep the decimal major units the oracle emitted.

## Provenance of this directory
OH-TIERD11-CC ran the rig, the replay (34/35) and the extraction, then stalled waiting on a background job; the driver
killed it by pid and ran `throwaway/down.sh` itself (`teardown-isolation.txt`, 12/12 == baseline). OH-TIERD11-CC2
committed the read-backs and journal entries, then wedged on the product-mapping step; killed by pid. The driver ran
`extract-product-mappings.py` (0.1 s — the extractor was not the hang), wrote the type join and this file.

## What is here

| path | what |
| --- | --- |
| `replay-result-table.md` | per-scenario PASSED/FAILED, failing step and values |
| `scenario-results.json` | the same, machine-readable |
| `run-accrualactivity-mnt.sh` | the exact replay driver |
| `replay-accrualactivity-mnt.log` | cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 34 PASSED scenarios (1,530 files; loan 11 excluded) |
| `manifest-accrual-activity.json` | all 1,565 extracted bodies with sha256 and `committed` flag |
| `manifest-accrual-activity-passed.json` | the 1,530 committed bodies |
| `summary-accrual-activity.json` | extractor totals |
| `journalentries/loan-<id>/` | the runner's `GET /journalentries` responses (8, loans 34 and 35) |
| `journalentries-manifest.json` | their sha256 |
| `product-mappings/` | accepted create requests of the 14 products the loans use, from THIS replay's log, sha256 in its manifest.json |
| `journalentry-type-join.json` | every leg joined to its transaction type (driver) |
| `extract-journalentries.py, extract-product-mappings.py, organize.py, build-results.py` | the extractors (logic unchanged from chargeback-mnt/writeoff-mnt) |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof |

## The type join — journal-entry legs → transaction TYPE (through the loan read-backs)

18 unique legs, 0 unmatched.

| transaction type | legs | loans |
| --- | ---: | --- |
| `disbursement` | 4 | 34, 35 |
| `interestRefund` | 4 | 34, 35 |
| `merchantIssuedRefund` | 4 | 34, 35 |
| `repayment` | 6 | 34, 35 |

**Finding: no accrual posting was observed at the GL level.** The point of this capture was
`createJournalEntriesForAccruals` [AccrualBasedAccountingProcessorForLoan.java:2015] (types `accrual`,
`accrualAdjustment`, `accrualActivity`). The runner fetched `/journalentries` only for the scenarios with a
journal-entry table (loans 34 and 35), and none of those legs belongs to an accrual-type transaction. The accrual
TRANSACTIONS themselves are observed in the loan read-backs, with their portions:

| transaction type (loan read-backs) | transactions | loans |
| --- | ---: | ---: |
| `accrual` | 406 | 34 |
| `accrualActivity` | 95 | 26 |
| `repayment` | 59 | 34 |
| `merchantIssuedRefund` | 37 | 17 |
| `disbursement` | 35 | 34 |
| `creditBalanceRefund` | 27 | 15 |
| `interestRefund` | 26 | 12 |
| `downPayment` | 9 | 9 |
| `accrualAdjustment` | 8 | 8 |
| `payoutRefund` | 5 | 3 |
| `goodwillCredit` | 3 | 3 |
| `interestPaymentWaiver` | 1 | 1 |
| `chargeOff` | 1 | 1 |

So the accrual AMOUNTS (per transaction, per portion) are capturable from `loans/`; their GL legs are not here.
Observing them needs a replay that reads `/journalentries` for accrual transactions (a capture-side step, not a
feature change).

## Failures — 1 scenario (recorded, not diagnosed)

### 11 — C3697 — `FAILED` — loan 11 — Verify accrual activity of overpaid loan in case of reversed MIR made before MIR and CBR for progressive loan - UC6

- failing step (feature line 1274): `Then Loan Repayment schedule has 12 periods, with the following data for periods:`
  - resource/loan id in the assertion: 11

```
Wrong value in Repayment schedule of resource 11 tab line 2.
Actual values in line (with the same due date) are:
[1, 31, 21 April 2025, null, 222.25, 120.21, 1.93, 0.0, 0.0, 122.14, 20.21, 20.21, 0.0, 101.93] -
But expected values in line:
[1, 31, 21 April 2025, null, 222.26, 120.2, 1.93, 0.0, 0.0, 122.13, 20.2, 20.2, 0.0, 101.93]]
```

Its loan (11) is NOT committed under `loans/`. The cause is not decided here; the driver dispatches an EUR control
(an earlier UC6 1-minor-unit difference was shown by EUR control to be the pinned build, not the MNT seed).

## Isolation
`preflight.txt` (same image as the standing oracle, baseline written fail-closed) and `teardown-isolation.txt`
(12/12 standing counters on both standing DBs == baseline; every `tierd-*` container removed).
