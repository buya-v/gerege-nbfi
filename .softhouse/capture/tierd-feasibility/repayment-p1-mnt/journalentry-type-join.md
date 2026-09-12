# Journal-entry type join — repayment-family arms (OH-TIERD21-DA step 6)

285 swept legs across 7 transaction types; 0 legs unmatched to a read-back.

Charged-off rule: a NON-REVERSED chargeOff loan transaction with a LOWER transaction id than the leg's transaction.  Charged-off latest = the loan `chargedOff` flag in its LATEST read-back.

## Type x charged-off -> legs -> loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 150 | 0 | - |
| `loanTransactionType.disbursement` | 86 | 0 | - |
| `loanTransactionType.goodwillCredit` | 29 | 12 | 45, 47 |
| `loanTransactionType.chargeOff` | 10 | 0 | - |
| `loanTransactionType.accrual` | 4 | 0 | - |
| `loanTransactionType.merchantIssuedRefund` | 4 | 0 | - |
| `loanTransactionType.payoutRefund` | 2 | 0 | - |

## Target repayment-family arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.repayment` | True | 150 | 59 | 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | 0 | - | 150 | 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 |
| `loanTransactionType.goodwillCredit` | True | 29 | 5 | 30, 44, 45, 46, 47 | 12 | 45, 47 | 17 | 30, 44, 46 |
| `loanTransactionType.merchantIssuedRefund` | True | 4 | 2 | 32, 33 | 0 | - | 4 | 32, 33 |
| `loanTransactionType.payoutRefund` | True | 2 | 1 | 31 | 0 | - | 2 | 31 |
| `loanTransactionType.recoveryRepayment` | False | 0 | 0 | - | 0 | - | 0 | - |

**FINDING:** target repayment-family type(s) with NO journal-entry legs at all: loanTransactionType.recoveryRepayment.  The arm was NOT exercised by this feature.

## Distinct leg shapes per target arm

### `loanTransactionType.repayment`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:8 DEBIT:10` | 8, 10 | 23 | 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30, 31, 32, 33 | loan 1 tx L2 |
| `CREDIT:6 CREDIT:8 DEBIT:10` | 6, 8, 10 | 16 | 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 48, 49, 50 | loan 34 tx L71 |
| `CREDIT:14 DEBIT:10` | 10, 14 | 8 | 13, 14, 15, 16, 17, 18, 19, 20 | loan 13 tx L27 |
| `CREDIT:8 CREDIT:10 DEBIT:8 DEBIT:10` | 8, 10 | 8 | 13, 14, 15, 16, 17, 18, 19, 20 | loan 13 tx L25 |
| `CREDIT:6 DEBIT:10` | 6, 10 | 4 | 44, 45, 46, 47 | loan 44 tx L91 |

### `loanTransactionType.goodwillCredit`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:13 CREDIT:17 CREDIT:18 CREDIT:20 DEBIT:13 DEBIT:17 DEBIT:18 DEBIT:20` | 13, 17, 18, 20 | 1 | 47 | loan 47 tx L105 |
| `CREDIT:13 DEBIT:17 DEBIT:18 DEBIT:20` | 13, 17, 18, 20 | 1 | 45 | loan 45 tx L97 |
| `CREDIT:14 DEBIT:20` | 14, 20 | 1 | 30 | loan 30 tx L60 |
| `CREDIT:6 CREDIT:8 CREDIT:17 CREDIT:18 CREDIT:20 DEBIT:6 DEBIT:8 DEBIT:17 DEBIT:18 DEBIT:20` | 6, 8, 17, 18, 20 | 1 | 46 | loan 46 tx L100 |
| `CREDIT:6 CREDIT:8 DEBIT:17 DEBIT:18 DEBIT:20` | 6, 8, 17, 18, 20 | 1 | 44 | loan 44 tx L92 |

### `loanTransactionType.merchantIssuedRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:14 DEBIT:10` | 10, 14 | 1 | 32 | loan 32 tx L66 |
| `CREDIT:8 DEBIT:10` | 8, 10 | 1 | 33 | loan 33 tx L68 |

### `loanTransactionType.payoutRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:14 DEBIT:10` | 10, 14 | 1 | 31 | loan 31 tx L63 |

### `loanTransactionType.recoveryRepayment`

_no legs._

