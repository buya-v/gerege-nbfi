# OWNER — Tier D `LoanInterestPaymentWaiver.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD14-CL)

Whole-file replay of `LoanInterestPaymentWaiver.feature` (15 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 15 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file, in the join and in the TSVs is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is three posting branches that were still UNOBSERVED or thin at the GL level:

* `createJournalEntriesForInterestPaymentWaiverOrInterestRefund` [`AccrualBasedAccountingProcessorForLoan.java:793`] — the interest-payment-waiver posting, never before observed at the GL level;
* the GOODWILL-CREDIT arm of `createJournalEntriesForRepaymentWhenLoanIsChargedOff` [`:1388`] — a goodwill credit made **after** a charge-off (the ChargeOff-Part1 goodwill credits were backdated before their charge-off, so they posted through the non-charged-off arm);
* the PAYOUT-REFUND arm of the same method (seen twice before).

This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at the transaction date, and lists every `interestPaymentWaiver` leg and every `merchantIssuedRefund` / `payoutRefund` / `goodwillCredit` leg that posted on a charged-off loan.

## Provenance

OH-TIERD14-CL ran the rig, the replay (15/15), the extraction, the sweep, the product mappings, the teardown and the type join. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`); the join was built offline over the captured JSON. Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-interest-payment-waiver-mnt.sh` | the exact replay driver (only FEATURE / LOG / container changed from the Part-3 copy) |
| `replay-interest-payment-waiver-mnt.log` | raw cucumber/Gradle replay log (168,123,968 B / 52,310 lines) |
| `loans/loan-<id>/` | per-loan read-backs of the 15 PASSED scenarios (709 bodies) |
| `manifest-interest-payment-waiver.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-interest-payment-waiver.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 15/15 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 4 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off/fraud state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `chargedoff-refund-goodwill.tsv` | flat listing of every refund/goodwill leg on a charged-off loan (required columns) |
| `accrual-legs.tsv` | flat listing of every accrual-type leg |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**15 scenarios, 15 PASSED, 0 FAILED; 468 steps (468 passed, 0 skipped, 0 failed).** Recorded, not diagnosed; no scenario failed, so there is nothing to diagnose.

| # | tag | line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C3141 | 5 | PASSED | 1 | `LP1_INTEREST_FLAT` |
| 2 | C3142 | 40 | PASSED | 2 | `LP1_INTEREST_FLAT` |
| 3 | C3143 | 77 | PASSED | 3 | `LP1_INTEREST_FLAT` |
| 4 | C3144 | 111 | PASSED | 4 | `LP1_INTEREST_FLAT` |
| 5 | C3145 | 204 | PASSED | 5 | `LP1_INTEREST_FLAT` |
| 6 | C3146 | 302 | PASSED | 6 | `LP1_INTEREST_FLAT` |
| 7 | C3147 | 399 | PASSED | 7 | `LP1_INTEREST_FLAT` |
| 8 | C3148 | 443 | PASSED | 8 | `LP1_INTEREST_FLAT` |
| 9 | C3149 | 495 | PASSED | 9 | `LP1_INTEREST_FLAT` |
| 10 | C3150 | 558 | PASSED | 10 | `LP1_INTEREST_FLAT` |
| 11 | C3151 | 626 | PASSED | 11 | `LP1_INTEREST_FLAT` |
| 12 | C4200 | 695 | PASSED | 12 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_ZERO_CHARGE_OFF` |
| 13 | C4204 | 751 | PASSED | 13 | `LP2_ADV_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OF_ACCRUAL` |
| 14 | C4205 | 953 | PASSED | 14 | `LP2_ADV_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OF_ACCRUAL` |
| 15 | C4206 | 1194 | PASSED | 15 | `LP2_ADV_CUSTOM_PMT_ALLOC_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OFF_ACCRUAL` |

## Extraction (step 2)

Source log 168,123,968 bytes / 52,310 lines; 2,003 exchanges (589 loan-attributed, 88% of source bytes skipped); 15 loans; 709 bodies kept (10467443 bytes) under `loans/`; each body sha256-pinned in the manifest.

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **15/15 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 324 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Product mappings (step 4)

`extract-product-mappings.py` pulled the accepted create requests of the **4** loan products the loans use out of this replay's Feign log; sha256 in `product-mappings/manifest.json`.

* `LP1_INTEREST_FLAT`
* `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_ZERO_CHARGE_OFF`
* `LP2_ADV_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OF_ACCRUAL`
* `LP2_ADV_CUSTOM_PMT_ALLOC_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OFF_ACCRUAL`

## Teardown (step 5)

`down.sh`: the `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume are gone; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF, FRAUD (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`). **324 legs, 10 types, 2 unmatched.**

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction dated on or before the leg's transaction date.** `fraud` per leg = the loan's fraud flag (`markAsFraud` request/read-back); no loan in this feature is fraud-flagged, so every `fraud` below is `false` and the fraud variants of the refund arms are not exercised.

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 182 | 4 | 12, 13 |
| `loanTransactionType.interestPaymentWaiver` | 35 | 6 | 11, 12, 13 |
| `loanTransactionType.disbursement` | 30 | 0 | – |
| `loanTransactionType.accrual` | 26 | 12 | 10, 11, 12, 13, 14, 15 |
| `loanTransactionType.chargeOff` | 24 | 24 | 10, 11, 12, 13, 14, 15 |
| `loanTransactionType.interestRefund` | 10 | 2 | 14 |
| `loanTransactionType.merchantIssuedRefund` | 10 | 0 | – |
| `loanTransactionType.goodwillCredit` | 3 | 3 | 15 |
| `(unmapped)` | 2 | 2 | 14 |
| `loanTransactionType.payoutRefund` | 2 | 2 | 14 |

### The three target arms

| type | present | legs | loans | legs on charged-off loan | loans on charged-off |
| --- | --- | ---: | --- | ---: | --- |
| `loanTransactionType.merchantIssuedRefund` | True | 10 | 12, 13, 14, 15 | 0 | – |
| `loanTransactionType.payoutRefund` | True | 2 | 14 | 2 | 14 |
| `loanTransactionType.goodwillCredit` | True | 3 | 15 | 3 | 15 |

### Legs on a CHARGED-OFF loan — required listing

| type | loan | tx | entry | account id | account name | amount (minor) | fraud | currency | tx date | charge-off tx |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- |
| `loanTransactionType.payoutRefund` | 14 | L95 | CREDIT | 11 | Credit Loss/Bad Debt | 6742 | False | MNT | 2022-09-16 | L93 |
| `loanTransactionType.payoutRefund` | 14 | L95 | DEBIT | 6 | Suspense/Clearing account | 6742 | False | MNT | 2022-09-16 | L93 |
| `loanTransactionType.goodwillCredit` | 15 | L113 | CREDIT | 13 | Recoveries | 6654 | False | MNT | 2022-09-16 | L112 |
| `loanTransactionType.goodwillCredit` | 15 | L113 | DEBIT | 19 | Goodwill Expense Account | 6307 | False | MNT | 2022-09-16 | L112 |
| `loanTransactionType.goodwillCredit` | 15 | L113 | DEBIT | 20 | Interest Income Charge Off | 347 | False | MNT | 2022-09-16 | L112 |

`merchantIssuedRefund` has **no legs on a charged-off loan** — a finding (see below). Its 10 legs are all dated before the loan's charge-off.

### `interestPaymentWaiver` — every leg (required listing)

| loan | tx | entry | account id | account name | amount (minor) | fraud | currency | charged_off | charge-off tx | tx date |
| ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| 1 | L2 | CREDIT | 2 | Loans Receivable | 25000 | False | MNT | False | - | 2024-02-01 |
| 1 | L2 | CREDIT | 4 | Interest/Fee Receivable | 1000 | False | MNT | False | - | 2024-02-01 |
| 1 | L2 | DEBIT | 9 | Interest Income | 26000 | False | MNT | False | - | 2024-02-01 |
| 2 | L4 | CREDIT | 2 | Loans Receivable | 1000 | False | MNT | False | - | 2024-02-01 |
| 2 | L4 | CREDIT | 4 | Interest/Fee Receivable | 3000 | False | MNT | False | - | 2024-02-01 |
| 2 | L4 | DEBIT | 9 | Interest Income | 4000 | False | MNT | False | - | 2024-02-01 |
| 3 | L6 | CREDIT | 2 | Loans Receivable | 1000 | False | MNT | False | - | 2024-02-01 |
| 3 | L6 | DEBIT | 9 | Interest Income | 1000 | False | MNT | False | - | 2024-02-01 |
| 4 | L12 | CREDIT | 4 | Interest/Fee Receivable | 1000 | False | MNT | False | - | 2024-05-01 |
| 4 | L12 | CREDIT | 17 | Overpayment account | 1000 | False | MNT | False | - | 2024-05-01 |
| 4 | L12 | DEBIT | 9 | Interest Income | 2000 | False | MNT | False | - | 2024-05-01 |
| 5 | L15 | CREDIT | 4 | Interest/Fee Receivable | 1000 | False | MNT | False | - | 2024-01-15 |
| 5 | L15 | DEBIT | 9 | Interest Income | 1000 | False | MNT | False | - | 2024-01-15 |
| 5 | L15 | DEBIT | 4 | Interest/Fee Receivable | 1000 | False | MNT | False | - | 2024-01-15 |
| 5 | L15 | CREDIT | 9 | Interest Income | 1000 | False | MNT | False | - | 2024-01-15 |
| 6 | L19 | CREDIT | 4 | Interest/Fee Receivable | 1000 | False | MNT | False | - | 2024-01-15 |
| 6 | L19 | DEBIT | 9 | Interest Income | 1000 | False | MNT | False | - | 2024-01-15 |
| 7 | L23 | CREDIT | 2 | Loans Receivable | 100000 | False | MNT | False | - | 2024-02-01 |
| 7 | L23 | CREDIT | 4 | Interest/Fee Receivable | 4000 | False | MNT | False | - | 2024-02-01 |
| 7 | L23 | CREDIT | 17 | Overpayment account | 6000 | False | MNT | False | - | 2024-02-01 |
| 7 | L23 | DEBIT | 9 | Interest Income | 110000 | False | MNT | False | - | 2024-02-01 |
| 8 | L28 | CREDIT | 17 | Overpayment account | 10000 | False | MNT | False | - | 2024-02-01 |
| 8 | L28 | DEBIT | 9 | Interest Income | 10000 | False | MNT | False | - | 2024-02-01 |
| 9 | L34 | CREDIT | 2 | Loans Receivable | 100000 | False | MNT | False | - | 2024-06-02 |
| 9 | L34 | CREDIT | 4 | Interest/Fee Receivable | 4000 | False | MNT | False | - | 2024-06-02 |
| 9 | L34 | DEBIT | 9 | Interest Income | 104000 | False | MNT | False | - | 2024-06-02 |
| 10 | L36 | CREDIT | 2 | Loans Receivable | 25000 | False | MNT | False | - | 2024-02-01 |
| 10 | L36 | CREDIT | 4 | Interest/Fee Receivable | 1000 | False | MNT | False | - | 2024-02-01 |
| 10 | L36 | DEBIT | 9 | Interest Income | 26000 | False | MNT | False | - | 2024-02-01 |
| 11 | L42 | CREDIT | 20 | Interest Income Charge Off | 26000 | False | MNT | True | L41 | 2024-02-01 |
| 11 | L42 | DEBIT | 9 | Interest Income | 26000 | False | MNT | True | L41 | 2024-02-01 |
| 12 | L49 | CREDIT | 20 | Interest Income Charge Off | 4656 | False | MNT | True | L48 | 2022-09-24 |
| 12 | L49 | DEBIT | 9 | Interest Income | 4656 | False | MNT | True | L48 | 2022-09-24 |
| 13 | L76 | CREDIT | 20 | Interest Income Charge Off | 4656 | False | MNT | True | L75 | 2022-09-16 |
| 13 | L76 | DEBIT | 9 | Interest Income | 4656 | False | MNT | True | L75 | 2022-09-16 |

### Per-loan currency, charge-off and fraud state

| loan | currency | fraud | non-reversed chargeOff transactions |
| ---: | --- | --- | --- |
| 1 | MNT | False | - |
| 2 | MNT | False | - |
| 3 | MNT | False | - |
| 4 | MNT | False | - |
| 5 | MNT | False | - |
| 6 | MNT | False | - |
| 7 | MNT | False | - |
| 8 | MNT | False | - |
| 9 | MNT | False | - |
| 10 | MNT | False | L38@2024-02-02 |
| 11 | MNT | False | L41@2024-01-15 |
| 12 | MNT | False | L48@2022-09-24 |
| 13 | MNT | False | L75@2022-09-16 |
| 14 | MNT | False | L93@2022-09-16 |
| 15 | MNT | False | L112@2022-09-16 |

Every loan in this capture is **MNT**.

## Findings / what the sweep observed and did not

* **Observed — the interest-payment-waiver branch (`createJournalEntriesForInterestPaymentWaiverOrInterestRefund` :793), for the first time at the GL level:** 35 legs on loans 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 (scenarios 1–13). The branch dispatches on the charged-off state at the transaction date:
  * *not charged off* (29 legs, loans 1–10): CREDIT `Loans Receivable` (2) / `Interest/Fee Receivable` (4) / `Overpayment account` (17), DEBIT `Interest Income` (9);
  * *charged off* (6 legs, loans 11, 12, 13): DEBIT `Interest Income` (9) / CREDIT `Interest Income Charge Off` (20).
* **Observed — the GOODWILL-CREDIT arm on a charged-off loan, previously UNOBSERVED:** 3 legs on loan 15, tx `L113` @ 2022-09-16 (charge-off `L112` @ 2022-09-16) — DEBIT `Goodwill Expense Account` (19) 6,307, DEBIT `Interest Income Charge Off` (20) 347, CREDIT `Recoveries` (13) 6,654.
* **Observed — the PAYOUT-REFUND arm on a charged-off loan:** 2 legs on loan 14, tx `L95` @ 2022-09-16 (charge-off `L93` @ 2022-09-16) — DEBIT `Suspense/Clearing account` (6) 6,742, CREDIT `Credit Loss/Bad Debt` (11) 6,742.
* **FINDING — a target type with no legs on a charged-off loan:** `merchantIssuedRefund` has 10 legs (loans 12–15) but **0 on a charged-off loan**; every one is dated 2021-10-29 / 2022-01-20, before its loan's charge-off (2022-09 / 2024-01), so all post through the non-charged-off amortisation arm (CREDIT `Loans Receivable` 2 / `Interest/Fee Receivable` 4, DEBIT `Suspense/Clearing` 6). The charged-off merchant-refund arm is **not** exercised here.
* `interestRefund` (not one of the required arms) is present: 10 legs on loans 12–15; 2 legs on a charged-off loan (loan 14, tx `L94`) — see `journalentry-type-join.md`.
* **Unmatched / not type-confirmable:** 2 legs (1 transaction) carry no entry in any `transactions` read-back; the posting shape did not match the inferred reverted-accrual pattern either, so no type is asserted. The loan-14 transaction `L98` (2 legs: DEBIT `Overpayment account` 17 459, CREDIT `Suspense/Clearing account` 6 459, both dated 2022-09-16, charged_off true) is the unmatched case.
* **No fraud-flagged loan** in this feature, so the `isMarkedFraud` / `chargeOffFraudExpense` variants are not exercised.

