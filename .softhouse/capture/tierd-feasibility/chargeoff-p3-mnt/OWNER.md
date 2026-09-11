# OWNER — Tier D `LoanChargeOff-Part3.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD13-CI)

Whole-file replay of `LoanChargeOff-Part3.feature` (50 scenarios) against the throwaway reference oracle,
tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then —
while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 50
loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file, in the join and in the
TSV is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and
`loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the **charged-off repayment/refund dispatch** —
`createJournalEntriesForRepaymentWhenLoanIsChargedOff`
[`AccrualBasedAccountingProcessorForLoan.java:1388`]. Only the plain REPAYMENT arm was observed before
(OH-RCOGRADE-CF / `chargeoff-mnt`). Part 3 adds the arms that were still UNOBSERVED: `merchantIssuedRefund`
(with its `isMarkedFraud` split), `payoutRefund` and `goodwillCredit`. This capture joins every swept leg to its
transaction TYPE and to the loan's CHARGED-OFF state at the transaction date, and lists every
`merchantIssuedRefund` / `payoutRefund` / `goodwillCredit` leg that posted on a charged-off loan.

## Provenance

OH-TIERD13-CI ran the rig, the replay (50/50), the extraction, the sweep, the product mappings, the teardown and the
type join. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle).
No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN
(`teardown-isolation.txt`); the join was built offline over the captured JSON. Nothing was written into
`/Users/buv/fineract`; the driver work was done in the disposable copy `/Users/buv/fineract-tierd`.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-chargeoff-p3-mnt.sh` | the exact replay driver (only FEATURE / LOG / container changed from the Part-2 copy) |
| `replay-chargeoff-p3-mnt.log` | raw cucumber/Gradle replay log (277,226,785 B / 103,068 lines) |
| `loans/loan-<id>/` | per-loan read-backs of the 50 PASSED scenarios (1,522 bodies) |
| `manifest-chargeoff-p3.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-chargeoff-p3.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 50/50 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 16 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off/fraud state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `chargedoff-refund-goodwill.tsv` | flat listing of every refund/goodwill leg on a charged-off loan (required columns) |
| `accrual-legs.tsv` | flat listing of every accrual-type leg (by-product) |
| `build-type-join.py` | the join builder (copied from the Part-1 capture; extended here with the charged-off + fraud dimensions) |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result

**50 scenarios, 50 PASSED, 0 FAILED; 1,379 steps (1,379 passed, 0 skipped, 0 failed).** Recorded, not diagnosed; no
scenario failed, so there is nothing to diagnose.

## Extraction (step 2)

Source log 277,226,785 bytes / 103,068 lines; 3,918 exchanges (1,263 loan-attributed, 2,655 skipped = 243,686,817
bytes, 87% of source bytes); 50 loans; 1,522 bodies kept (15,777,138 bytes) under `loans/`; each body sha256-pinned
in the manifest.

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no
write. Result: **50/50 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 1,333 legs total**, each body saved verbatim
and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Product mappings (step 4)

`extract-product-mappings.py` pulled the accepted create requests of the **16** loan products the 50 loans use out of
this replay's Feign log; sha256 in `product-mappings/manifest.json`. The relevant links for the charged-off arms are
`chargeOffExpense` / `chargeOffFraudExpense` (merchant/payout principal), `incomeFromChargeOffInterest` /
`incomeFromChargeOffFees` / `incomeFromChargeOffPenalty`, `goodwillCreditAccount`,
`incomeFromGoodwillCreditInterest/Fees/Penalty`, `incomeFromRecovery`, `overpayment` and `fundSource`.

## Teardown (step 5)

`down.sh`: the `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named
volume are gone; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their
normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no
Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF, FRAUD (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through
the loan read-backs (`transactions[].id` → `transactions[].type.code`). **1,333 legs, 9 types, 20 unmatched** (5
transactions on loans 27/28 carry no read-back type and are inferred `loanTransactionType.accrual` from their
net-zero 4-leg posting shape).

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction dated on or before the leg's transaction
date.** `fraud` per leg = the loan's fraud flag (`markAsFraud` request/read-back). This date rule matches the
observed accounting dispatch exactly: the backdated refunds on loans 45/46 (dated 13 April, before the 14 April
charge-off) post through the NON-charged-off arm, while loans 48/49/50 (refunds dated 15 April, after the 14 April
charge-off) post through `createJournalEntriesForRepaymentWhenLoanIsChargedOff`.

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.chargeOff` | 339 | 331 | 1–26, 27, 28, 30–36, 38, 39, 40, 45, 46, 47, 48, 49, 50 |
| `loanTransactionType.accrual` | 642 | 166 | 1–26, 28, 30, 32, 33, 34, 38, 39, 40, 45, 46, 47, 48, 49, 50 |
| `loanTransactionType.repayment` | 153 | 12 | 39, 40 |
| `loanTransactionType.merchantIssuedRefund` | 39 | 32 | 48, 49, 50 |
| `loanTransactionType.interestRefund` | 18 | 18 | 48, 49, 50 |
| `loanTransactionType.accrualAdjustment` | 18 | 18 | 13, 14, 15, 33, 35, 36, 45, 46 |
| `loanTransactionType.disbursement` | 98 | 0 | – |
| `loanTransactionType.goodwillCredit` | 6 | 0 | – |
| `(unmapped — inferred `accrual`)` | 20 | 20 | 27, 28 |

Fraud-flagged loans (the `fraud` flag is set on the loan, never on a transaction): **37, 45, 46, 47**.

### The three target arms

| type | present | legs | loans | legs on charged-off loan | loans on charged-off |
| --- | --- | ---: | --- | ---: | --- |
| `merchantIssuedRefund` | yes | 39 | 45, 46, 48, 49, 50 | **32** | **48, 49, 50** |
| `payoutRefund` | no | 0 | – | 0 | – |
| `goodwillCredit` | yes | 6 | 42, 45, 46 | 0 | – |

Each loan's currency is **MNT** for every loan (the sweep body and the loan read-back both carry
`currency.code = MNT`).

### Every `merchantIssuedRefund` / `payoutRefund` / `goodwillCredit` leg ON A CHARGED-OFF LOAN

`payoutRefund`: none issued by any Part-3 scenario. `goodwillCredit`: the three loans that issue one (42, 45, 46)
all post it on a NON-charged-off loan, so no goodwill leg qualifies. Only `merchantIssuedRefund` qualifies, on loans
48 / 49 / 50 (all fraud flag `false`, all MNT), as follows.

| loan | tx | type | entry | GL account id | GL account name | amount (minor) | fraud | currency |
| ---: | --- | --- | --- | ---: | --- | ---: | --- | --- |
| 48 | L475 | merchantIssuedRefund | DEBIT | 7 | Suspense/Clearing account | 90000 | false | MNT |
| 48 | L475 | merchantIssuedRefund | DEBIT | 18 | Credit Loss/Bad Debt | 80000 | false | MNT |
| 48 | L475 | merchantIssuedRefund | DEBIT | 16 | Interest Income Charge Off | 1849 | false | MNT |
| 48 | L475 | merchantIssuedRefund | DEBIT | 13 | Overpayment account | 8151 | false | MNT |
| 48 | L475 | merchantIssuedRefund | CREDIT | 18 | Credit Loss/Bad Debt | 80000 | false | MNT |
| 48 | L475 | merchantIssuedRefund | CREDIT | 16 | Interest Income Charge Off | 1849 | false | MNT |
| 48 | L475 | merchantIssuedRefund | CREDIT | 13 | Overpayment account | 8151 | false | MNT |
| 48 | L475 | merchantIssuedRefund | CREDIT | 7 | Suspense/Clearing account | 90000 | false | MNT |
| 48 | L477 | merchantIssuedRefund | DEBIT | 7 | Suspense/Clearing account | 90000 | false | MNT |
| 48 | L477 | merchantIssuedRefund | CREDIT | 18 | Credit Loss/Bad Debt | 88310 | false | MNT |
| 48 | L477 | merchantIssuedRefund | CREDIT | 16 | Interest Income Charge Off | 1690 | false | MNT |
| 49 | L485 | merchantIssuedRefund | DEBIT | 7 | Suspense/Clearing account | 90000 | false | MNT |
| 49 | L485 | merchantIssuedRefund | DEBIT | 18 | Credit Loss/Bad Debt | 80000 | false | MNT |
| 49 | L485 | merchantIssuedRefund | DEBIT | 16 | Interest Income Charge Off | 732 | false | MNT |
| 49 | L485 | merchantIssuedRefund | DEBIT | 13 | Overpayment account | 9268 | false | MNT |
| 49 | L485 | merchantIssuedRefund | CREDIT | 18 | Credit Loss/Bad Debt | 80000 | false | MNT |
| 49 | L485 | merchantIssuedRefund | CREDIT | 16 | Interest Income Charge Off | 732 | false | MNT |
| 49 | L485 | merchantIssuedRefund | CREDIT | 13 | Overpayment account | 9268 | false | MNT |
| 49 | L485 | merchantIssuedRefund | CREDIT | 7 | Suspense/Clearing account | 90000 | false | MNT |
| 49 | L488 | merchantIssuedRefund | DEBIT | 7 | Suspense/Clearing account | 90000 | false | MNT |
| 49 | L488 | merchantIssuedRefund | CREDIT | 18 | Credit Loss/Bad Debt | 89243 | false | MNT |
| 49 | L488 | merchantIssuedRefund | CREDIT | 16 | Interest Income Charge Off | 757 | false | MNT |
| 50 | L495 | merchantIssuedRefund | DEBIT | 7 | Suspense/Clearing account | 90000 | false | MNT |
| 50 | L495 | merchantIssuedRefund | DEBIT | 18 | Credit Loss/Bad Debt | 80000 | false | MNT |
| 50 | L495 | merchantIssuedRefund | DEBIT | 16 | Interest Income Charge Off | 732 | false | MNT |
| 50 | L495 | merchantIssuedRefund | DEBIT | 13 | Overpayment account | 9268 | false | MNT |
| 50 | L495 | merchantIssuedRefund | CREDIT | 18 | Credit Loss/Bad Debt | 80000 | false | MNT |
| 50 | L495 | merchantIssuedRefund | CREDIT | 16 | Interest Income Charge Off | 732 | false | MNT |
| 50 | L495 | merchantIssuedRefund | CREDIT | 13 | Overpayment account | 9268 | false | MNT |
| 50 | L495 | merchantIssuedRefund | CREDIT | 7 | Suspense/Clearing account | 90000 | false | MNT |
| 50 | L498 | merchantIssuedRefund | DEBIT | 7 | Suspense/Clearing account | 90000 | false | MNT |
| 50 | L498 | merchantIssuedRefund | CREDIT | 18 | Credit Loss/Bad Debt | 90000 | false | MNT |

Loan 48 also posts `interestRefund` L476 / L478; loans 49 (L486 / L490) and 50 (L496 / L500) likewise — 18
`interestRefund` legs in all, every one on a charged-off loan (loans 48, 49, 50); those are not one of the three
requested arms but are visible in `journalentry-type-join.md`.

### Per-loan charge-off / fraud state (target loans)

| loan | currency | fraud | non-reversed chargeOff transactions | merchant refund / goodwill date |
| ---: | --- | --- | --- | --- |
| 42 | MNT | false | none | goodwill L444 @ 2024-01-23 |
| 45 | MNT | **true** | L451 @ 2025-04-14, L453 @ 2025-04-14 | merchant L455 + goodwill L457 @ 2025-04-13 |
| 46 | MNT | **true** | L460 @ 2025-04-14, L463 @ 2025-04-14 | merchant L464 + goodwill L466 @ 2025-04-13 |
| 48 | MNT | false | L474 @ 2025-04-14, L479 @ 2025-04-14 | merchant L475 @ 2025-04-15, L477 @ 2025-04-15 |
| 49 | MNT | false | L484 @ 2025-04-14, L487 @ 2025-04-14 | merchant L485 @ 2025-04-15, L488 @ 2025-04-15 |
| 50 | MNT | false | L494 @ 2025-04-14, L497 @ 2025-04-14 | merchant L495 @ 2025-04-15, L498 @ 2025-04-15 |

### Appendix — backdated refund/goodwill legs on loans 45 / 46 (created after charge-off, dated before it)

These 11 legs are NOT charged off under the transaction-date rule (they are dated 13 April; the charge-off is dated
14 April), and the GL accounts confirm the non-charged-off arm. They are listed here because the scenarios
(45, 46) are titled "backdated transactions … after charge-off": the loan was charged off when the teller keyed
them, but the oracle posts them through `createJournalEntriesForRepayment` (Loans Receivable / Interest/Fee
Receivable), not `…WhenLoanIsChargedOff`.

| loan | tx | type | entry | GL account id | GL account name | amount (minor) | fraud | currency | tx date |
| ---: | --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| 45 | L455 | merchantIssuedRefund | DEBIT | 7 | Suspense/Clearing account | 50000 | true | MNT | 2025-04-13 |
| 45 | L455 | merchantIssuedRefund | CREDIT | 6 | Loans Receivable | 977 | true | MNT | 2025-04-13 |
| 45 | L455 | merchantIssuedRefund | CREDIT | 3 | Interest/Fee Receivable | 49 | true | MNT | 2025-04-13 |
| 45 | L455 | merchantIssuedRefund | CREDIT | 13 | Overpayment account | 48974 | true | MNT | 2025-04-13 |
| 45 | L457 | goodwillCredit | DEBIT | 20 | Goodwill Expense Account | 50000 | true | MNT | 2025-04-13 |
| 45 | L457 | goodwillCredit | CREDIT | 13 | Overpayment account | 50000 | true | MNT | 2025-04-13 |
| 46 | L464 | merchantIssuedRefund | DEBIT | 7 | Suspense/Clearing account | 50000 | true | MNT | 2025-04-13 |
| 46 | L464 | merchantIssuedRefund | CREDIT | 6 | Loans Receivable | 311 | true | MNT | 2025-04-13 |
| 46 | L464 | merchantIssuedRefund | CREDIT | 13 | Overpayment account | 49689 | true | MNT | 2025-04-13 |
| 46 | L466 | goodwillCredit | DEBIT | 20 | Goodwill Expense Account | 50000 | true | MNT | 2025-04-13 |
| 46 | L466 | goodwillCredit | CREDIT | 13 | Overpayment account | 50000 | true | MNT | 2025-04-13 |

## Findings / what the sweep observed and did not

- **Observed (charged-off arm):** `merchantIssuedRefund` principal → CREDIT `Credit Loss/Bad Debt` (18,
  `chargeOffExpense`), interest → CREDIT `Interest Income Charge Off` (16, `incomeFromChargeOffInterest`),
  overpayment → CREDIT `Overpayment account` (13), DEBIT `Suspense/Clearing account` (7, `fundSource`), with the
  replayed reversal pairs. Loans 48/49/50, non-fraud.
- **Observed (by-product):** 331 charge-off-posting legs, 166 accrual / 18 accrualAdjustment legs on charged-off
  loans, 12 `repayment` legs on charged-off loans (39, 40), 39 total `merchantIssuedRefund` legs and 6
  `goodwillCredit` legs.
- **Still UNOBSERVED under this rule:** the `goodwillCredit` arm **on a charged-off loan** (all three goodwill
  transactions are on non-charged-off loans), the `payoutRefund` arm (no scenario issues one), and the
  `isMarkedFraud` variants of `merchantIssuedRefund` / `payoutRefund` (loans 45/46 are fraud-flagged but their
  refunds are backdated to 13 April, before the 14 April charge-off, so they post through the NON-charged-off arm;
  loan 47 is fraud-flagged and charged off but issues no refund). Part 3 therefore does **not** exercise
  `chargeOffFraudExpense` through these arms; scenario 1 (loan 1) exercises the fraud *charge-off* mapping via its
  `FRAUD` charge-off reason.
- **Backdating caveat:** scenarios 45/46 are titled "backdated transactions … after charge-off"; the transactions are
  dated 13 April, the charge-off 14 April. The loan was charged off when they were keyed, yet the oracle posts them
  through the non-charged-off arm — confirmed by the GL accounts (loans 45/46 credit `Loans Receivable` 6 /
  `Interest/Fee Receivable` 3, not `Credit Loss/Bad Debt` 18). The join reports the transaction-date state, per the
  stated rule.
