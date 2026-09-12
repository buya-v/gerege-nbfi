# Journal-entry type join — capitalized-income p2 arms (OH-TIERD29-DO step 6)

1769 swept legs across 12 transaction types; 0 legs unmatched to a read-back.

Charged-off rule: a leg's transaction is on a charged-off loan only if the loan's LATEST read-back has `chargedOff=true` and lists a NON-REVERSED `chargeOff` transaction with an EARLIER transaction DATE than the leg's transaction, or the SAME date and a LOWER transaction id (date order, not id order).  Charged-off latest = the loan `chargedOff` flag in its LATEST read-back.

## Type x charged-off -> legs -> loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.capitalizedIncomeAmortization` | 682 | 2 | 27 |
| `loanTransactionType.accrual` | 670 | 0 | - |
| `loanTransactionType.repayment` | 150 | 2 | 27 |
| `loanTransactionType.capitalizedIncome` | 102 | 0 | - |
| `loanTransactionType.disbursement` | 80 | 0 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 45 | 0 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 14 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 10 | 0 | - |
| `loanTransactionType.payoutRefund` | 6 | 0 | - |
| `loanTransactionType.accrualAdjustment` | 4 | 0 | - |
| `loanTransactionType.chargeOff` | 4 | 0 | - |
| `loanTransactionType.downPayment` | 2 | 0 | - |

## Target arms (required)

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.capitalizedIncome` | True | 102 | 48 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 | 0 | - | 102 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 |
| `loanTransactionType.capitalizedIncomeAdjustment` | True | 45 | 20 | 2, 6, 8, 10, 11, 12, 14, 17, 20, 22, 25, 26, 27, 31, 32 | 0 | - | 45 | 2, 6, 8, 10, 11, 12, 14, 17, 20, 22, 25, 26, 27, 31, 32 |
| `loanTransactionType.capitalizedIncomeAmortization` | True | 682 | 336 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 | 2 | 27 | 680 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | True | 14 | 7 | 1, 2, 14, 17, 25, 26 | 0 | - | 14 | 1, 2, 14, 17, 25, 26 |
| `loanTransactionType.chargeOff` | True | 4 | 1 | 27 | 0 | - | 4 | 27 |

## Distinct leg shapes per required arm

### `loanTransactionType.capitalizedIncome`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:24 DEBIT:9` | 9, 24 | 45 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 | loan 1 tx L4 |
| `CREDIT:9 CREDIT:24 DEBIT:9 DEBIT:24` | 9, 24 | 3 | 1, 14, 24 | loan 1 tx L2 |

### `loanTransactionType.capitalizedIncomeAdjustment`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:9 DEBIT:24` | 9, 24 | 15 | 6, 8, 10, 11, 12, 20, 22, 25, 26, 27, 31, 32 | loan 6 tx L523 |
| `CREDIT:1 CREDIT:9 DEBIT:24` | 1, 9, 24 | 3 | 11, 17, 25 | loan 11 tx L573 |
| `CREDIT:17 DEBIT:24` | 17, 24 | 1 | 2 | loan 2 tx L198 |
| `CREDIT:9 CREDIT:24 DEBIT:9 DEBIT:24` | 9, 24 | 1 | 14 | loan 14 tx L600 |

### `loanTransactionType.capitalizedIncomeAmortization`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:5 DEBIT:24` | 5, 24 | 326 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 32, 33, 34 | loan 1 tx L7 |
| `CREDIT:11 DEBIT:24` | 11, 24 | 3 | 29, 31 | loan 29 tx L792 |
| `CREDIT:5 CREDIT:24 DEBIT:5 DEBIT:24` | 5, 24 | 3 | 24, 25, 32 | loan 24 tx L678 |
| `CREDIT:5 CREDIT:11 DEBIT:24` | 5, 11, 24 | 2 | 30 | loan 30 tx L801 |
| `CREDIT:14 DEBIT:24` | 14, 24 | 1 | 27 | loan 27 tx L782 |
| `CREDIT:5 CREDIT:24 DEBIT:11 DEBIT:24` | 5, 11, 24 | 1 | 31 | loan 31 tx L812 |

### `loanTransactionType.capitalizedIncomeAmortizationAdjustment`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:24 DEBIT:5` | 5, 24 | 7 | 1, 2, 14, 17, 25, 26 | loan 1 tx L10 |

### `loanTransactionType.chargeOff`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:9 DEBIT:14 DEBIT:20` | 1, 9, 14, 20 | 1 | 27 | loan 27 tx L781 |

