# Journal-entry type join — required MIR arms (OH-TIERD22-DB step 6)

364 swept legs across 11 transaction types; 16 legs unmatched to a read-back.

Charged-off rule: a NON-REVERSED chargeOff loan transaction with a LOWER transaction id than the leg's transaction.  Charged-off latest = the loan `chargedOff` flag in its LATEST read-back.

## Type x charged-off -> legs -> loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 105 | 3 | 2 |
| `loanTransactionType.merchantIssuedRefund` | 77 | 4 | 2, 3 |
| `loanTransactionType.interestRefund` | 62 | 2 | 3 |
| `loanTransactionType.disbursement` | 44 | 0 | - |
| `loanTransactionType.accrual` | 22 | 0 | - |
| `(unmapped)` | 16 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 14 | 0 | - |
| `loanTransactionType.accrualAdjustment` | 10 | 2 | 2 |
| `loanTransactionType.chargeOff` | 8 | 0 | - |
| `loanTransactionType.payoutRefund` | 4 | 0 | - |
| `loanTransactionType.goodwillCredit` | 2 | 0 | - |

## Target arms (required)

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.merchantIssuedRefund` | True | 77 | 24 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19 | 4 | 2, 3 | 73 | 1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19 |
| `loanTransactionType.payoutRefund` | True | 4 | 2 | 8, 17 | 0 | - | 4 | 8, 17 |
| `loanTransactionType.accrual` | True | 22 | 11 | 1, 2, 3, 9, 14, 16, 17, 18, 19 | 0 | - | 22 | 1, 2, 3, 9, 14, 16, 17, 18, 19 |
| `loanTransactionType.accrualAdjustment` | True | 10 | 5 | 2, 3, 16, 17, 18 | 2 | 2 | 8 | 3, 16, 17, 18 |
| `loanTransactionType.repayment` | True | 105 | 30 | 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 3 | 2 | 102 | 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 |
| `loanTransactionType.chargeOff` | True | 8 | 2 | 2, 3 | 0 | - | 8 | 2, 3 |

## Distinct leg shapes per required arm

### `loanTransactionType.merchantIssuedRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:7 DEBIT:10` | 7, 10 | 9 | 4, 5, 6, 8, 10, 12, 13, 19 | loan 4 tx L36 |
| `CREDIT:7 CREDIT:10 DEBIT:7 DEBIT:10` | 7, 10 | 3 | 7, 11, 15 | loan 7 tx L46 |
| `CREDIT:13 DEBIT:10` | 10, 13 | 2 | 2, 3 | loan 2 tx L24 |
| `CREDIT:16 DEBIT:10` | 10, 16 | 2 | 9, 16 | loan 9 tx L55 |
| `CREDIT:4 CREDIT:7 CREDIT:10 CREDIT:16 DEBIT:4 DEBIT:7 DEBIT:10 DEBIT:16` | 4, 7, 10, 16 | 2 | 1 | loan 1 tx L4 |
| `CREDIT:4 CREDIT:7 CREDIT:16 DEBIT:10` | 4, 7, 10, 16 | 2 | 1, 14 | loan 1 tx L14 |
| `CREDIT:4 CREDIT:7 DEBIT:10` | 4, 7, 10 | 2 | 15, 19 | loan 15 tx L86 |
| `CREDIT:4 CREDIT:7 CREDIT:10 DEBIT:4 DEBIT:7 DEBIT:10` | 4, 7, 10 | 1 | 15 | loan 15 tx L79 |
| `CREDIT:7 CREDIT:16 DEBIT:10` | 7, 10, 16 | 1 | 19 | loan 19 tx L137 |

### `loanTransactionType.payoutRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:16 DEBIT:10` | 10, 16 | 1 | 17 | loan 17 tx L105 |
| `CREDIT:7 DEBIT:10` | 7, 10 | 1 | 8 | loan 8 tx L50 |

### `loanTransactionType.accrual`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:9 DEBIT:4` | 4, 9 | 10 | 1, 2, 3, 9, 14, 16, 17, 18, 19 | loan 1 tx L6 |
| `CREDIT:5 DEBIT:4` | 4, 5 | 1 | 1 | loan 1 tx L16 |

### `loanTransactionType.accrualAdjustment`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:4 DEBIT:9` | 4, 9 | 5 | 2, 3, 16, 17, 18 | loan 2 tx L22 |

### `loanTransactionType.repayment`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:4 CREDIT:7 DEBIT:10` | 4, 7, 10 | 19 | 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 19 | loan 1 tx L2 |
| `CREDIT:4 CREDIT:7 CREDIT:10 DEBIT:4 DEBIT:7 DEBIT:10` | 4, 7, 10 | 5 | 1, 15, 16, 17, 18 | loan 1 tx L3 |
| `CREDIT:4 CREDIT:7 CREDIT:16 DEBIT:10` | 4, 7, 10, 16 | 3 | 16, 17, 18 | loan 16 tx L95 |
| `CREDIT:7 DEBIT:10` | 7, 10 | 3 | 2, 3, 15 | loan 2 tx L18 |

### `loanTransactionType.chargeOff`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:4 CREDIT:7 DEBIT:13 DEBIT:17` | 4, 7, 13, 17 | 2 | 2, 3 | loan 2 tx L21 |

