# Journal-entry type join — required arms (OH-TIERD25-DG step 6)

1035 swept legs across 8 transaction types; 0 legs unmatched to a read-back.

Charged-off rule: a NON-REVERSED chargeOff loan transaction with a LOWER transaction id than the leg's transaction, listed in the loan's LATEST read-back, with the loan's `chargedOff` true.  Charged-off latest = the loan `chargedOff` flag in its LATEST read-back.

## Type x charged-off -> legs -> loans (every type)

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

## Target arms (required)

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.payoutRefund` | True | 40 | 13 | 26, 28, 30, 32, 34, 35, 36, 37, 38, 39, 40, 41 | 0 | - | 40 | 26, 28, 30, 32, 34, 35, 36, 37, 38, 39, 40, 41 |
| `loanTransactionType.interestRefund` | True | 54 | 26 | 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 52 | 0 | - | 54 | 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 52 |
| `loanTransactionType.merchantIssuedRefund` | True | 41 | 13 | 25, 27, 31, 33, 35, 36, 37, 38, 39, 40, 41, 52 | 0 | - | 41 | 25, 27, 31, 33, 35, 36, 37, 38, 39, 40, 41, 52 |
| `loanTransactionType.repayment` | True | 196 | 70 | 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52 | 0 | - | 196 | 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52 |
| `loanTransactionType.accrualAdjustment` | True | 2 | 1 | 52 | 0 | - | 2 | 52 |
| `loanTransactionType.chargeOff` | False | 0 | 0 | - | 0 | - | 0 | - |

**FINDING:** target type(s) with NO journal-entry legs at all: loanTransactionType.chargeOff.  The arm was NOT exercised by this feature.

**FINDING:** no non-reversed `chargeOff` loan transaction appears in any loan's LATEST read-back: no leg is on a charged-off loan.

**FINDING:** no loan's LATEST read-back has `chargedOff=true`: the charged-off dimension is empty (every leg charged-off=no).

## Distinct leg shapes per required arm

### `loanTransactionType.payoutRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:5 DEBIT:8` | 1, 5, 8 | 10 | 28, 30, 32, 35, 36, 37, 38, 39, 41 | loan 28 tx L226 |
| `CREDIT:1 CREDIT:5 CREDIT:15 DEBIT:8` | 1, 5, 8, 15 | 2 | 26, 40 | loan 26 tx L215 |
| `CREDIT:15 DEBIT:8` | 8, 15 | 1 | 34 | loan 34 tx L270 |

### `loanTransactionType.interestRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 DEBIT:2` | 1, 2 | 21 | 25, 27, 28, 30, 31, 32, 33, 35, 36, 37, 38, 39, 40, 41 | loan 25 tx L210 |
| `CREDIT:15 DEBIT:2` | 2, 15 | 4 | 26, 34, 40, 52 | loan 26 tx L216 |
| `CREDIT:2 CREDIT:5 DEBIT:2 DEBIT:5` | 2, 5 | 1 | 52 | loan 52 tx L469 |

### `loanTransactionType.merchantIssuedRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:5 DEBIT:8` | 1, 5, 8 | 11 | 25, 27, 31, 33, 35, 36, 37, 38, 39, 40, 41 | loan 25 tx L211 |
| `CREDIT:1 CREDIT:5 CREDIT:15 DEBIT:8` | 1, 5, 8, 15 | 1 | 52 | loan 52 tx L472 |
| `CREDIT:1 CREDIT:8 DEBIT:1 DEBIT:8` | 1, 8 | 1 | 52 | loan 52 tx L468 |

### `loanTransactionType.repayment`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:5 DEBIT:8` | 1, 5, 8 | 56 | 1, 2, 3, 4, 5, 10, 11, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 26, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 46, 48, 49, 51 | loan 1 tx L2 |
| `CREDIT:1 DEBIT:8` | 1, 8 | 13 | 2, 3, 4, 5, 12, 30, 43, 44, 45, 46, 47, 50, 52 | loan 2 tx L6 |
| `CREDIT:5 DEBIT:8` | 5, 8 | 1 | 16 | loan 16 tx L57 |

### `loanTransactionType.accrualAdjustment`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:5 DEBIT:2` | 2, 5 | 1 | 52 | loan 52 tx L474 |

### `loanTransactionType.chargeOff`

_no legs._

