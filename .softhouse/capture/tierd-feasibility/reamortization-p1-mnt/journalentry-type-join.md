# Journal-entry type join — re-amortization arms (OH-TIERD30-DR step 6)

539 swept legs across 8 transaction types; 0 legs unmatched to a read-back.

Charged-off rule: a NON-REVERSED chargeOff loan transaction, listed in the loan's LATEST read-back, with an EARLIER transaction DATE than the leg's transaction, or the SAME date and a LOWER id.  Charged-off latest = the loan `chargedOff` flag in its LATEST read-back.

## Type x charged-off -> legs -> loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 257 | 10 | 46, 47, 48, 49, 50 |
| `loanTransactionType.disbursement` | 108 | 0 | - |
| `loanTransactionType.accrual` | 82 | 0 | - |
| `loanTransactionType.downPayment` | 51 | 0 | - |
| `loanTransactionType.chargeOff` | 20 | 0 | - |
| `loanTransactionType.merchantIssuedRefund` | 9 | 0 | - |
| `loanTransactionType.chargeback` | 6 | 0 | - |
| `loanTransactionType.interestRefund` | 6 | 0 | - |

## Target arms (required)

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.reAmortize` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.repayment` | True | 257 | 91 | 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | 10 | 46, 47, 48, 49, 50 | 247 | 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 |
| `loanTransactionType.accrual` | True | 82 | 36 | 8, 9, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | 0 | - | 82 | 8, 9, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 |
| `loanTransactionType.chargeOff` | True | 20 | 5 | 46, 47, 48, 49, 50 | 0 | - | 20 | 46, 47, 48, 49, 50 |

**FINDING:** target type(s) with NO journal-entry legs at all: loanTransactionType.reAmortize.  The re-amortization command succeeds and rewrites the schedule, but the reAmortize transaction itself posts no journal entry.

**FINDING:** 49 target transaction(s) in the read-backs have NO journal-entry legs: loan 4 tx L12, loan 6 tx L19, loan 7 tx L23, loan 7 tx L25, loan 8 tx L29, loan 9 tx L34, loan 10 tx L40, loan 11 tx L44, loan 12 tx L49, loan 12 tx L50, loan 13 tx L54, loan 13 tx L55, loan 14 tx L60, loan 14 tx L63, loan 15 tx L69, loan 15 tx L70, loan 16 tx L76, loan 17 tx L82, loan 18 tx L89, loan 19 tx L97, loan 20 tx L105, loan 21 tx L110, loan 22 tx L118, loan 23 tx L123, loan 24 tx L130, loan 25 tx L137, loan 26 tx L145, loan 27 tx L150, loan 28 tx L158, loan 29 tx L163, loan 30 tx L172, loan 31 tx L181, loan 31 tx L183, loan 32 tx L190, loan 32 tx L191, loan 33 tx L199, loan 33 tx L201, loan 34 tx L209, loan 34 tx L210, loan 36 tx L218, loan 37 tx L224, loan 38 tx L231, loan 39 tx L236, loan 40 tx L241, loan 41 tx L248, loan 42 tx L254, loan 43 tx L259, loan 44 tx L271, loan 45 tx L278.

## Distinct leg shapes per required arm

### `loanTransactionType.reAmortize`

_no legs._

### `loanTransactionType.repayment`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:8 CREDIT:10 DEBIT:2` | 2, 8, 10 | 67 | 8, 9, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | loan 8 tx L30 |
| `CREDIT:8 DEBIT:2` | 2, 8 | 16 | 4, 6, 7, 10, 11, 12, 13, 14, 15, 16, 31, 32, 43 | loan 4 tx L13 |
| `CREDIT:14 DEBIT:2` | 2, 14 | 5 | 46, 47, 48, 49, 50 | loan 46 tx L288 |
| `CREDIT:2 CREDIT:8 DEBIT:2 DEBIT:8` | 2, 8 | 2 | 12, 15 | loan 12 tx L48 |
| `CREDIT:2 CREDIT:8 CREDIT:10 DEBIT:2 DEBIT:8 DEBIT:10` | 2, 8, 10 | 1 | 40 | loan 40 tx L242 |

### `loanTransactionType.accrual`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:9 DEBIT:10` | 9, 10 | 28 | 17, 20, 21, 22, 23, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 43, 44, 45, 46, 47, 48, 49, 50 | loan 17 tx L84 |
| `CREDIT:5 CREDIT:9 DEBIT:10 DEBIT:10` | 5, 9, 10 | 5 | 18, 19, 24, 25, 42 | loan 18 tx L91 |
| `CREDIT:5 DEBIT:10` | 5, 10 | 3 | 8, 9, 15 | loan 8 tx L31 |

### `loanTransactionType.chargeOff`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:8 CREDIT:10 DEBIT:11 DEBIT:19` | 8, 10, 11, 19 | 5 | 46, 47, 48, 49, 50 | loan 46 tx L287 |

## Repayment schedules before/after each re-amortization

### loan 1 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 2 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 3 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 4 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 5 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 6 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 7 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 8 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 9 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 10 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 11 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 12 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 13 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 14 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 15 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 16 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 17 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 18 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 19 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 20 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 21 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 22 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 23 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 24 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 25 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 26 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 27 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 28 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 29 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 30 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 31 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 32 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 33 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 34 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 35 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 36 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 37 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 38 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 39 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 40 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 41 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 42 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 43 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 44 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 45 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 46 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 47 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 48 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 49 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

### loan 50 — UNKNOWN

reAmortize calls (source line): -; reAmortize transactions: -

_no read-back carries a `periods` array._

