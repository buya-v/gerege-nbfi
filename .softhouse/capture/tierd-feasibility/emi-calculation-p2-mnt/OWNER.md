# OWNER — Tier D `EMICalculation-Part2.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD25-DG)

Whole-file replay of `EMICalculation-Part2.feature` (50 scenarios) against the throwaway reference oracle, tenant `tierd` (currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every loan the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file and in the join is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

`EMICalculation-Part2.feature` complements the few-loan merchant-refund and payout-refund captures (`merchant-refund-mnt`, OH-TIERD22-DB) by exercising the refund posts at breadth: interest refunds (with interest and fee portions) and payout refunds across more products. This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at that transaction, and gives each required arm's DISTINCT leg shapes.

## Provenance

OH-TIERD25-DG ran the rig, the replay (49/50), the extraction, the sweep, the product mappings, the teardown and the type join over the captured JSON. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`, 12/12 standing counters == baseline). Nothing was written into `/Users/buv/fineract`; the replay ran in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

Charged-off classification (exactly the rule this capture uses): **a leg's transaction is on a charged-off loan only if that loan's LATEST read-back (highest index) lists a `chargeOff` transaction with a LOWER id and the loan's `chargedOff` is true.** Charge-offs that were undone vanish from the latest read-back; `manuallyReversed` on earlier read-backs is not reliable and is not used.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, client/loan mapping, steps |
| `run-emi-calculation-p2-mnt.sh` | the exact replay driver |
| `replay-emi-calculation-p2-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 51 PASSED loans |
| `manifest-emi-calculation-p2.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-emi-calculation-p2.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 52/52 clean |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 7 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**50 scenarios, 49 PASSED, 1 FAILED; 1293 steps (1279 passed, 13 skipped, 1 failed); 52 loans over 50 clients.** Recorded, not diagnosed; a failure would be dispatched to an EUR control, not fixed here. Two of the 50 scenarios each create a second loan for the same client, so the replay creates 52 loans over 50 clients.

Per-scenario detail (TestRailId, feature line, result, client, loan ids, product) is in `replay-result-table.md`. Scenario attribution validated: yes.

## The journal-entry sweep (step 3 — the new step)

52 loans swept, 52 clean (52 HTTP 200, `curl` rc 0, valid JSON), 0 not clean. Each body is saved verbatim as `journalentries-sweep/loan-<id>.json`; the manifest records the sha256 and the exact URL `https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1`. GET only; no write. This is the THROWAWAY (port 8444, tenant `tierd`), never 8443 and never tenant `gerege`/`default`.

Total swept legs: 1035 across 8 transaction types; 0 legs unmatched to a loan read-back.

## Product mappings (step 4)

7 products used by the committed loans; each is the accepted create request from THIS replay's Feign log, sha256 in `product-mappings/manifest.json`.

## Teardown (step 5)

`down.sh` removed every `tierd-*` container, network and volume. The 12 standing reference-oracle counters (6 each on `fineract-db-1` and `gerege-oracle-db`) were read after teardown and all 12 equal the baseline this capture opened with (`teardown-isolation.txt`).

## The type join (step 6)

Every swept leg -> its transaction TYPE through the loan read-backs, and for each leg whether the loan was CHARGED OFF at that transaction. Charged-off rule: a NON-REVERSED chargeOff loan transaction with a LOWER transaction id than the leg's transaction, listed in the loan's LATEST read-back, with the loan's `chargedOff` true.

### Type x charged-off -> legs -> loans (every type swept)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.accrual` | 570 | 0 | - |
| `loanTransactionType.repayment` | 196 | 0 | - |
| `loanTransactionType.disbursement` | 126 | 0 | - |
| `loanTransactionType.interestRefund` | 54 | 0 | - |
| `loanTransactionType.merchantIssuedRefund` | 41 | 0 | - |
| `loanTransactionType.payoutRefund` | 40 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 6 | 0 | - |
| `loanTransactionType.accrualAdjustment` | 2 | 0 | - |

### Required arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.payoutRefund` | True | 40 | 13 | 26, 28, 30, 32, 34, 35, 36, 37, 38, 39, 40, 41 | 0 | - | 40 | 26, 28, 30, 32, 34, 35, 36, 37, 38, 39, 40, 41 |
| `loanTransactionType.interestRefund` | True | 54 | 26 | 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 52 | 0 | - | 54 | 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 52 |
| `loanTransactionType.merchantIssuedRefund` | True | 41 | 13 | 25, 27, 31, 33, 35, 36, 37, 38, 39, 40, 41, 52 | 0 | - | 41 | 25, 27, 31, 33, 35, 36, 37, 38, 39, 40, 41, 52 |
| `loanTransactionType.repayment` | True | 196 | 70 | 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52 | 0 | - | 196 | 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52 |
| `loanTransactionType.accrualAdjustment` | True | 2 | 1 | 52 | 0 | - | 2 | 52 |
| `loanTransactionType.chargeOff` | False | 0 | 0 | - | 0 | - | 0 | - |

### Distinct leg shapes per required arm

#### `loanTransactionType.payoutRefund`

| shape (side:account) | account ids | transactions | loans | example (loan, tx id, portions, paymentType id) |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:5 DEBIT:8` | 1, 5, 8 | 10 | 28, 30, 32, 35, 36, 37, 38, 39, 41 | loan 28, tx L226, P 99493 / I 507 / F 0 / Pen 0 / OP 0 / UI 0, paymentType 11 |
| `CREDIT:1 CREDIT:5 CREDIT:15 DEBIT:8` | 1, 5, 8, 15 | 2 | 26, 40 | loan 26, tx L215, P 75325 / I 163 / F 0 / Pen 0 / OP 24512 / UI 0, paymentType 11 |
| `CREDIT:15 DEBIT:8` | 8, 15 | 1 | 34 | loan 34, tx L270, P 0 / I 0 / F 0 / Pen 0 / OP 50000 / UI 0, paymentType 11 |

#### `loanTransactionType.interestRefund`

| shape (side:account) | account ids | transactions | loans | example (loan, tx id, portions, paymentType id) |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 DEBIT:2` | 1, 2 | 21 | 25, 27, 28, 30, 31, 32, 33, 35, 36, 37, 38, 39, 40, 41 | loan 25, tx L210, P 568 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType - |
| `CREDIT:15 DEBIT:2` | 2, 15 | 4 | 26, 34, 40, 52 | loan 26, tx L216, P 0 / I 0 / F 0 / Pen 0 / OP 1002 / UI 0, paymentType - |
| `CREDIT:2 CREDIT:5 DEBIT:2 DEBIT:5` | 2, 5 | 1 | 52 | loan 52, tx L469, P 0 / I 570 / F 0 / Pen 0 / OP 0 / UI 0, paymentType - |

#### `loanTransactionType.merchantIssuedRefund`

| shape (side:account) | account ids | transactions | loans | example (loan, tx id, portions, paymentType id) |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:5 DEBIT:8` | 1, 5, 8 | 11 | 25, 27, 31, 33, 35, 36, 37, 38, 39, 40, 41 | loan 25, tx L211, P 99432 / I 568 / F 0 / Pen 0 / OP 0 / UI 0, paymentType 11 |
| `CREDIT:1 CREDIT:5 CREDIT:15 DEBIT:8` | 1, 5, 8, 15 | 1 | 52 | loan 52, tx L472, P 91437 / I 542 / F 0 / Pen 0 / OP 8021 / UI 0, paymentType 11 |
| `CREDIT:1 CREDIT:8 DEBIT:1 DEBIT:8` | 1, 8 | 1 | 52 | loan 52, tx L468, P 100000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType 11 |

#### `loanTransactionType.repayment`

| shape (side:account) | account ids | transactions | loans | example (loan, tx id, portions, paymentType id) |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:5 DEBIT:8` | 1, 5, 8 | 56 | 1, 2, 3, 4, 5, 10, 11, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 26, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 46, 48, 49, 51 | loan 1, tx L2, P 1643 / I 58 / F 0 / Pen 0 / OP 0 / UI 0, paymentType 11 |
| `CREDIT:1 DEBIT:8` | 1, 8 | 13 | 2, 3, 4, 5, 12, 30, 43, 44, 45, 46, 47, 50, 52 | loan 2, tx L6, P 1000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType 11 |
| `CREDIT:5 DEBIT:8` | 5, 8 | 1 | 16 | loan 16, tx L57, P 0 / I 20 / F 0 / Pen 0 / OP 0 / UI 0, paymentType 11 |

#### `loanTransactionType.accrualAdjustment`

| shape (side:account) | account ids | transactions | loans | example (loan, tx id, portions, paymentType id) |
| --- | --- | ---: | --- | --- |
| `CREDIT:5 DEBIT:2` | 2, 5 | 1 | 52 | loan 52, tx L474, P 0 / I 28 / F 0 / Pen 0 / OP 0 / UI 0, paymentType - |

#### `loanTransactionType.chargeOff`

_No legs: this arm was NOT exercised by this feature (a finding, see below)._

### Per-loan currency and charge-off state

| loan | currency | chargedOff (latest read-back) | chargeOff tx ids (non-reversed, lower id) |
| ---: | --- | --- | --- |
| 1 | MNT | - | - |
| 2 | MNT | - | - |
| 3 | MNT | - | - |
| 4 | MNT | - | - |
| 5 | MNT | - | - |
| 6 | MNT | - | - |
| 7 | MNT | - | - |
| 8 | MNT | - | - |
| 9 | MNT | - | - |
| 10 | MNT | - | - |
| 11 | MNT | - | - |
| 12 | MNT | - | - |
| 13 | MNT | - | - |
| 14 | MNT | - | - |
| 15 | MNT | - | - |
| 16 | MNT | - | - |
| 17 | MNT | - | - |
| 18 | MNT | - | - |
| 19 | MNT | - | - |
| 20 | MNT | - | - |
| 21 | MNT | - | - |
| 22 | MNT | - | - |
| 23 | MNT | - | - |
| 24 | MNT | - | - |
| 25 | MNT | - | - |
| 26 | MNT | - | - |
| 27 | MNT | - | - |
| 28 | MNT | - | - |
| 29 | MNT | - | - |
| 30 | MNT | - | - |
| 31 | MNT | - | - |
| 32 | MNT | - | - |
| 33 | MNT | - | - |
| 34 | MNT | - | - |
| 35 | MNT | - | - |
| 36 | MNT | - | - |
| 37 | MNT | - | - |
| 38 | MNT | - | - |
| 39 | MNT | - | - |
| 40 | MNT | - | - |
| 41 | MNT | - | - |
| 42 | MNT | - | - |
| 43 | MNT | - | - |
| 44 | MNT | - | - |
| 45 | MNT | - | - |
| 46 | MNT | - | - |
| 47 | MNT | - | - |
| 48 | MNT | - | - |
| 49 | MNT | - | - |
| 50 | MNT | - | - |
| 51 | MNT | - | - |
| 52 | MNT | - | - |

## Findings

- target type(s) with NO journal-entry legs at all: loanTransactionType.chargeOff.  The arm was NOT exercised by this feature.
- no non-reversed `chargeOff` loan transaction appears in any loan's LATEST read-back: no leg is on a charged-off loan.
- no loan's LATEST read-back has `chargedOff=true`: the charged-off dimension is empty (every leg charged-off=no).

A required type with no legs is itself a result: `loanTransactionType.chargeOff` had no swept leg, so the feature did not exercise that arm.
