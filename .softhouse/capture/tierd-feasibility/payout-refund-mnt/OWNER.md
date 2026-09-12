# OWNER — Tier D `LoanPayoutRefund.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD24-DE)

Whole-file replay of `LoanPayoutRefund.feature` (9 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 9 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file and in the join is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the PAYOUT-REFUND posting family and the interest refunds that follow it: `payoutRefund` (with the principal, interest, fee and penalty portions the feature exercises), `interestRefund` (the interest/fee portions a payout refund generates and the manual interest refunds), plus the `merchantIssuedRefund`, `repayment`, `accrualAdjustment` and `chargeOff` legs that appear alongside them. The feature also reverses a payout refund together with its linked interest refund, and guards against a duplicate or invalid manual interest refund. This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at that transaction, and gives each required arm's DISTINCT leg shapes.

## Provenance

OH-TIERD24-DE ran the rig, the replay (9/9), the extraction, the sweep, the product mappings, the teardown and the type join over the captured JSON. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`). Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-payout-refund-mnt.sh` | the exact replay driver |
| `replay-payout-refund-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 9 PASSED scenarios |
| `manifest-payout-refund.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-payout-refund.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 9/9 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 1 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**9 scenarios, 9 PASSED, 0 FAILED; 210 steps (210 passed, 0 skipped, 0 failed).** Recorded, not diagnosed.

| # | TestRailId | feature line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C3845 | 4 | PASSED | 1 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 2 | C3846 | 44 | PASSED | 2 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 3 | C3847 | 85 | PASSED | 3 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 4 | C3857 | 126 | PASSED | 4 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 5 | C3870 | 198 | PASSED | 5 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 6 | C3871 | 262 | PASSED | 6 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 7 | C3872 | 354 | PASSED | 7 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 8 | C3878 | 396 | PASSED | 8 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 9 | C3879 | 412 | PASSED | 9 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 9 loans, 267 bodies kept under `loans/`, each body sha256-pinned in `manifest-payout-refund.json`; the FAILED scenarios' loans are not committed (`manifest-payout-refund-passed.json`). Attribution: validated.

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **9/9 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 89 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Product mappings (step 4)

The copied `extract-product-mappings.py` pulled the accepted `createLoanProduct` bodies for the 1 distinct products this feature's loans use, sha256-pinned in `product-mappings/manifest.json`.

- `create-request-LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL.json`

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`) and to the transaction's read-back portions and `paymentDetailData.paymentType`. **89 legs, 4 types, 0 unmatched.**

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction with a LOWER transaction id than the leg's transaction.** (The rule is transaction id order, not date order.) `charged-off latest` = the loan `chargedOff` flag in its LATEST read-back, so a charge-off later undone does not count.

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 33 | 0 | - |
| `loanTransactionType.payoutRefund` | 22 | 0 | - |
| `loanTransactionType.disbursement` | 18 | 0 | - |
| `loanTransactionType.interestRefund` | 16 | 0 | - |

### The six required arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.payoutRefund` | True | 22 | 8 | 1, 2, 3, 4, 5, 6, 7, 8 | 0 | - | 22 | 1, 2, 3, 4, 5, 6, 7, 8 |
| `loanTransactionType.interestRefund` | True | 16 | 6 | 2, 3, 4, 5, 6, 7 | 0 | - | 16 | 2, 3, 4, 5, 6, 7 |
| `loanTransactionType.merchantIssuedRefund` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.repayment` | True | 33 | 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 0 | - | 33 | 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| `loanTransactionType.accrualAdjustment` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.chargeOff` | False | 0 | 0 | - | 0 | - | 0 | - |

**FINDING:** target type(s) with NO journal-entry legs at all: loanTransactionType.merchantIssuedRefund, loanTransactionType.accrualAdjustment, loanTransactionType.chargeOff.  The arm was NOT exercised by this feature.

**FINDING:** no non-reversed `chargeOff` loan transaction appears in ANY read-back: no leg is on a charged-off loan.

**FINDING:** no loan's LATEST read-back has `chargedOff=true`: the charged-off dimension is empty (every leg charged-off=no).

### Distinct leg shapes per required arm (account ids + sides, example, count)

#### `loanTransactionType.payoutRefund`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:3 DEBIT:9` | 3, 9 | CREDIT 3, DEBIT 9 | 5 | 1, 2, 3, 5, 7 | 1 | L3 | P 5000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 7 |
| `CREDIT:3 CREDIT:9 DEBIT:3 DEBIT:9` | 3, 9 | CREDIT 3, CREDIT 9, DEBIT 3, DEBIT 9 | 3 | 4, 6, 8 | 4 | L13 | P 5000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 7 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:3 DEBIT:9`: loan 1, tx L3, P 5000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 7 — 5 transaction(s) across loan(s) 1, 2, 3, 5, 7.
- shape `CREDIT:3 CREDIT:9 DEBIT:3 DEBIT:9`: loan 4, tx L13, P 5000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 7 — 3 transaction(s) across loan(s) 4, 6, 8.

#### `loanTransactionType.interestRefund`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:4 DEBIT:7` | 4, 7 | CREDIT 4, DEBIT 7 | 4 | 2, 3, 5, 7 | 2 | L7 | P 0 / I 19 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:4 CREDIT:7 DEBIT:4 DEBIT:7` | 4, 7 | CREDIT 4, CREDIT 7, DEBIT 4, DEBIT 7 | 2 | 4, 6 | 4 | L14 | P 0 / I 12 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:4 DEBIT:7`: loan 2, tx L7, P 0 / I 19 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 4 transaction(s) across loan(s) 2, 3, 5, 7.
- shape `CREDIT:4 CREDIT:7 DEBIT:4 DEBIT:7`: loan 4, tx L14, P 0 / I 12 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 2 transaction(s) across loan(s) 4, 6.

#### `loanTransactionType.merchantIssuedRefund`

_No legs for this type — see the finding above._

#### `loanTransactionType.repayment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:3 CREDIT:4 DEBIT:9` | 3, 4, 9 | CREDIT 3, CREDIT 4, DEBIT 9 | 9 | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 1 | L2 | P 33648 / I 242 / F 0 / Pen 0 / OP 0 / UI 0 | 7 |
| `CREDIT:3 CREDIT:4 CREDIT:9 DEBIT:3 DEBIT:4 DEBIT:9` | 3, 4, 9 | CREDIT 3, CREDIT 4, CREDIT 9, DEBIT 3, DEBIT 4, DEBIT 9 | 1 | 4 | 4 | L15 | P 9642 / I 358 / F 0 / Pen 0 / OP 0 / UI 0 | 7 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:3 CREDIT:4 DEBIT:9`: loan 1, tx L2, P 33648 / I 242 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 7 — 9 transaction(s) across loan(s) 1, 2, 3, 4, 5, 6, 7, 8, 9.
- shape `CREDIT:3 CREDIT:4 CREDIT:9 DEBIT:3 DEBIT:4 DEBIT:9`: loan 4, tx L15, P 9642 / I 358 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 7 — 1 transaction(s) across loan(s) 4.

#### `loanTransactionType.accrualAdjustment`

_No legs for this type — see the finding above._

#### `loanTransactionType.chargeOff`

_No legs for this type — see the finding above._

### Per-loan currency and charge-off state

| loan | currency | charged-off latest read-back | non-reversed chargeOff transactions |
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

### Findings

- target type(s) with NO journal-entry legs at all: loanTransactionType.merchantIssuedRefund, loanTransactionType.accrualAdjustment, loanTransactionType.chargeOff.  The arm was NOT exercised by this feature.
- no non-reversed `chargeOff` loan transaction appears in ANY read-back: no leg is on a charged-off loan.
- no loan's LATEST read-back has `chargedOff=true`: the charged-off dimension is empty (every leg charged-off=no).

Other observations from the join:

- `loanTransactionType.payoutRefund`: 22 legs on 8 transaction(s) / 8 loan(s); 0 legs on charged-off loan(s) (-); 22 on not-charged-off loan(s) (1, 2, 3, 4, 5, 6, 7, 8).
- `loanTransactionType.interestRefund`: 16 legs on 6 transaction(s) / 6 loan(s); 0 legs on charged-off loan(s) (-); 16 on not-charged-off loan(s) (2, 3, 4, 5, 6, 7).
- `loanTransactionType.merchantIssuedRefund`: NO legs at all — the arm was NOT exercised by this feature.
- `loanTransactionType.repayment`: 33 legs on 10 transaction(s) / 9 loan(s); 0 legs on charged-off loan(s) (-); 33 on not-charged-off loan(s) (1, 2, 3, 4, 5, 6, 7, 8, 9).
- `loanTransactionType.accrualAdjustment`: NO legs at all — the arm was NOT exercised by this feature.
- `loanTransactionType.chargeOff`: NO legs at all — the arm was NOT exercised by this feature.

The payment type on each arm comes from `paymentDetailData.paymentType.id` in the read-back (channel-mapped fund source); it is listed per shape above.

