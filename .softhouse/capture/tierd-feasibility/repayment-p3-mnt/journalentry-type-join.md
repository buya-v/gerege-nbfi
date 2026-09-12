# Journal-entry type join — required LoanRepayment-Part3 arms (OH-TIERD28-DM step 6)

559 swept legs across 13 transaction types; 0 legs unmatched to a read-back.

Charged-off rule: a NON-REVERSED chargeOff loan transaction with an EARLIER transaction DATE than the leg's transaction, or the SAME DATE and a LOWER id, while the loan's LATEST read-back has chargedOff=true (OH-TIERD28-DM; DATE order, not id order).  Charged-off latest = the loan `chargedOff` flag in its LATEST read-back.

## Type x charged-off -> legs -> loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 217 | 0 | - |
| `loanTransactionType.disbursement` | 106 | 0 | - |
| `loanTransactionType.accrual` | 78 | 0 | - |
| `loanTransactionType.merchantIssuedRefund` | 57 | 0 | - |
| `loanTransactionType.interestRefund` | 31 | 0 | - |
| `loanTransactionType.payoutRefund` | 22 | 0 | - |
| `loanTransactionType.downPayment` | 14 | 0 | - |
| `loanTransactionType.chargeOff` | 12 | 4 | 35 |
| `loanTransactionType.goodwillCredit` | 12 | 0 | - |
| `loanTransactionType.interestPaymentWaiver` | 4 | 0 | - |
| `loanTransactionType.accrualAdjustment` | 2 | 2 | 35 |
| `loanTransactionType.chargeAdjustment` | 2 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 2 | 0 | - |

## Target arms (required)

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.refund` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.repayment` | True | 217 | 69 | 1, 10, 12, 13, 20, 21, 23, 24, 28, 29, 30, 31, 32, 33, 34, 35, 36, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 50 | 0 | - | 217 | 1, 10, 12, 13, 20, 21, 23, 24, 28, 29, 30, 31, 32, 33, 34, 35, 36, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 50 |
| `loanTransactionType.merchantIssuedRefund` | True | 57 | 20 | 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 26, 27, 31, 36, 37, 44 | 0 | - | 57 | 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 26, 27, 31, 36, 37, 44 |
| `loanTransactionType.payoutRefund` | True | 22 | 5 | 17, 20, 22 | 0 | - | 22 | 17, 20, 22 |
| `loanTransactionType.creditBalanceRefund` | True | 2 | 1 | 31 | 0 | - | 2 | 31 |
| `loanTransactionType.interestRefund` | True | 31 | 9 | 20, 31, 37, 44 | 0 | - | 31 | 20, 31, 37, 44 |

**FINDING:** target type(s) with NO journal-entry legs at all: loanTransactionType.refund.  The arm was NOT exercised by this feature.

## Distinct leg shapes per required arm

### `loanTransactionType.refund`

_no legs._

### `loanTransactionType.repayment`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:10 DEBIT:5` | 1, 5, 10 | 37 | 12, 29, 30, 31, 33, 34, 35, 36, 38, 39, 40, 41, 43, 44, 45, 46, 47 | loan 12 tx L29 |
| `CREDIT:10 DEBIT:5` | 5, 10 | 14 | 1, 10, 13, 20, 21, 23, 32, 33, 43, 44, 48, 50 | loan 1 tx L3 |
| `CREDIT:5 CREDIT:10 DEBIT:5 DEBIT:10` | 5, 10 | 7 | 12, 31, 34, 40, 41 | loan 12 tx L27 |
| `CREDIT:1 CREDIT:5 CREDIT:10 DEBIT:1 DEBIT:5 DEBIT:10` | 1, 5, 10 | 5 | 24, 28, 31, 42 | loan 24 tx L79 |
| `CREDIT:1 DEBIT:5` | 1, 5 | 3 | 12, 40, 45 | loan 12 tx L33 |
| `CREDIT:1 CREDIT:5 CREDIT:17 DEBIT:1 DEBIT:5 DEBIT:17` | 1, 5, 17 | 1 | 12 | loan 12 tx L31 |
| `CREDIT:10 CREDIT:18 DEBIT:10 DEBIT:18` | 10, 18 | 1 | 12 | loan 12 tx L26 |
| `CREDIT:5 CREDIT:17 DEBIT:5 DEBIT:17` | 5, 17 | 1 | 12 | loan 12 tx L30 |

### `loanTransactionType.merchantIssuedRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:10 DEBIT:5` | 5, 10 | 11 | 12, 13, 14, 15, 16, 17, 19, 22, 37, 44 | loan 12 tx L25 |
| `CREDIT:1 CREDIT:10 DEBIT:5` | 1, 5, 10 | 4 | 18, 26, 27, 36 | loan 18 tx L52 |
| `CREDIT:5 CREDIT:10 DEBIT:5 DEBIT:10` | 5, 10 | 2 | 18, 20 | loan 18 tx L51 |
| `CREDIT:1 CREDIT:5 CREDIT:10 DEBIT:1 DEBIT:5 DEBIT:10` | 1, 5, 10 | 1 | 20 | loan 20 tx L63 |
| `CREDIT:10 CREDIT:17 DEBIT:5` | 5, 10, 17 | 1 | 31 | loan 31 tx L112 |
| `CREDIT:5 CREDIT:10 CREDIT:17 DEBIT:5 DEBIT:10 DEBIT:17` | 5, 10, 17 | 1 | 31 | loan 31 tx L106 |

### `loanTransactionType.payoutRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:5 CREDIT:10 DEBIT:1 DEBIT:5 DEBIT:10` | 1, 5, 10 | 3 | 20 | loan 20 tx L61 |
| `CREDIT:10 DEBIT:5` | 5, 10 | 2 | 17, 22 | loan 17 tx L49 |

### `loanTransactionType.creditBalanceRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:5 DEBIT:17` | 5, 17 | 1 | 31 | loan 31 tx L110 |

### `loanTransactionType.interestRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:4 CREDIT:10 DEBIT:4 DEBIT:10` | 4, 10 | 5 | 20 | loan 20 tx L58 |
| `CREDIT:1 CREDIT:10 DEBIT:4` | 1, 4, 10 | 1 | 44 | loan 44 tx L196 |
| `CREDIT:10 DEBIT:4` | 4, 10 | 1 | 37 | loan 37 tx L150 |
| `CREDIT:17 DEBIT:4` | 4, 17 | 1 | 31 | loan 31 tx L111 |
| `CREDIT:4 CREDIT:17 DEBIT:4 DEBIT:17` | 4, 17 | 1 | 31 | loan 31 tx L107 |

