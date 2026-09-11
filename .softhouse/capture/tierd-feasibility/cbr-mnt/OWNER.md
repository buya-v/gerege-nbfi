# OWNER — Tier D `LoanCBR.feature` MNT capture (OH-TIERD16-CO, finished by the driver)

Replay of the whole `LoanCBR.feature` (40 `Scenario` blocks; one Scenario Outline expands, so **41 scenarios ran**)
against the throwaway reference oracle, tenant `tierd` (image `sha256:e596339626bf…`, Asia/Ulaanbaatar, rounding 4,
currency re-seeded to MNT), Feign capture on, plus the journal-entry SWEEP of every loan (GET only, port 8444, tenant
`tierd`) before teardown. Capture only: no vector, no drive, no `.go`. Money here and in the join is integer minor units.

## Provenance of this directory
The run committed steps 1-3 (result table 41/41 PASSED; extraction; sweep). At step 4 it wedged on a `grep` that read
`$FEIGN` before assigning it (so grep waited on stdin) — killed by pid. The driver then ran `throwaway/down.sh`
(`teardown-isolation.txt`, 12/12 == this run's baseline), restored the run's edit of `extract-product-mappings.py` (logic
unchanged from chargeback-p2-mnt), ran it (3 products), and wrote the join and this file.

| path | what |
| --- | --- |
| `replay-result-table.md, scenario-results.json` | per-scenario result (41/41 PASSED) |
| `run-cbr-mnt.sh, replay-cbr-mnt.log` | the replay driver and its log |
| `loans/loan-<id>/` | read-backs of all 41 loans; `manifest-cbr.json` / `manifest-cbr-passed.json` with sha256 |
| `journalentries-sweep/loan-<id>.json` | the sweep, one body per loan; `journalentries-sweep-manifest.json` with sha256 and URL |
| `product-mappings/` | accepted create requests of the 3 products used; sha256 in its manifest.json |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off state (driver) |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof |

## The type × charged-off join — 992 legs, 4 unmatched (no read-back transaction; not typed)

| transaction type | charged off | legs | loans |
| --- | --- | ---: | --- |
| `accrual` | no | 114 | 19, 25, 35, 36, 39 |
| `chargeAdjustment` | no | 6 | 39 |
| `chargeOff` | yes | 20 | 27, 28, 29, 30, 32, 39 |
| `chargeback` | no | 4 | 9, 17 |
| `creditBalanceRefund` | no | 205 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 31, 33, 34, 35, 36, 37, 38, 39, 40, 41 |
| `creditBalanceRefund` | yes | 31 | 27, 28, 29, 30, 32 |
| `disbursement` | no | 78 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41 |
| `disbursement` | yes | 6 | 27, 28, 30 |
| `downPayment` | no | 26 | 20, 21, 22, 23, 24, 25, 26, 29, 32, 33, 34 |
| `downPayment` | yes | 6 | 27, 28, 30 |
| `goodwillCredit` | no | 10 | 35, 36, 37 |
| `interestRefund` | no | 28 | 35, 36 |
| `merchantIssuedRefund` | no | 54 | 19, 25, 31, 34, 35, 36, 39 |
| `merchantIssuedRefund` | yes | 8 | 32 |
| `payoutRefund` | no | 47 | 6, 7, 8, 10, 14, 15, 16, 18, 22, 34 |
| `payoutRefund` | yes | 9 | 29 |
| `repayment` | no | 312 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 31, 32, 33, 35, 36, 37, 38, 39, 40, 41 |
| `repayment` | yes | 24 | 27, 28, 30, 39 |

## Newly observed: the CREDIT-BALANCE-REFUND posting
`createJournalEntriesForCreditBalanceRefund` / `createJournalEntriesForLoanCreditBalanceRefund`
[AccrualBasedAccountingProcessorForLoan.java:2113-2170] — 236 legs on 41 loans. Shapes (each posting; many
transactions also carry a later reversal/replay pair under the same id — take the first posting):
* overpayment only — DEBIT Overpayment account (16), CREDIT Suspense/Clearing (4) (e.g. loan 1 L5, 200.00);
* principal only — DEBIT Loans Receivable (5), CREDIT 4 (e.g. loan 3 L16);
* principal + overpayment — DEBIT 5 and DEBIT 16, one CREDIT 4 of the amount (e.g. loan 1 L6: 100 + 100 → 200;
  loan 19 L112: 10 + 190; loan 31 L202: 36.99 + 87.84);
* ON A CHARGED-OFF LOAN the principal debit is CHARGE_OFF_EXPENSE — Credit Loss/Bad Debt (15) (loans 28 L175, 30 L190,
  29 L183, 32 L211) — or the FRAUD expense, Credit Loss/Bad Debt-Fraud (11), on loan 27 L169.
Also: sub-minor-looking but exact amounts are observed (loans 35/36 L276/L329: 0.01; loan 37 L336: 0.50).

Also observed on charged-off loans: payout refunds (loan 29 L180/L182: C15 + C16, D4) and merchant-issued refunds
(loan 32 L208/L210) — the arms already graded (OH-MIRGRADE-CK, OH-MIRFRAUD-CN). Goodwill appears only on loans NOT
charged off (35, 36, 37).

## Currency — all MNT
Every loan resolves to MNT (41 loans; no USD product in this feature).

## Isolation
`preflight.txt` (same image as the standing oracle; baseline written fail-closed) and `teardown-isolation.txt`
(12/12 standing counters on both standing DBs == this run's baseline; every `tierd-*` container removed).
