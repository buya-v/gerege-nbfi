# Journal-entry type join — OH-TIERD27-DL step 6 (`Loan-Part3`)

349 swept legs across 11 transaction types; 6 legs unmatched to a read-back.

Charged-off rule: a leg is on a charged-off loan only if the loan's LATEST read-back (highest manifest source_line) has chargedOff=true and lists a NON-REVERSED chargeOff transaction with an EARLIER transaction DATE than the leg, or the SAME date and a LOWER id (DATE order, not id order -- OH-TIERD26-DJ).

Resolved target codes (the exact code seen in this capture): `loanTransactionType.refund` -> `loanTransactionType.refund`, `loanTransactionType.repayment` -> `loanTransactionType.repayment`, `loanTransactionType.merchantIssuedRefund` -> `loanTransactionType.merchantIssuedRefund`, `loanTransactionType.payoutRefund` -> `loanTransactionType.payoutRefund`, `loanTransactionType.creditBalanceRefund` -> `loanTransactionType.creditBalanceRefund`, `loanTransactionType.interestRefund` -> `loanTransactionType.interestRefund`.

## Type x charged-off -> legs -> loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 120 | 0 | - |
| `loanTransactionType.disbursement` | 119 | 0 | - |
| `loanTransactionType.goodwillCredit` | 26 | 0 | - |
| `loanTransactionType.merchantIssuedRefund` | 22 | 0 | - |
| `loanTransactionType.payoutRefund` | 15 | 0 | - |
| `loanTransactionType.downPayment` | 14 | 0 | - |
| `loanTransactionType.interestRefund` | 12 | 0 | - |
| `(unmapped)` | 6 | 0 | - |
| `loanTransactionType.accrual` | 6 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 6 | 0 | - |
| `loanTransactionType.refund` | 3 | 0 | - |

## Target arms (required)

| target | exact code | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs not charged-off | loans not charged-off |
| --- | --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.refund` | `loanTransactionType.refund` | True | 3 | 1 | 19 | 0 | - | 3 | 19 |
| `loanTransactionType.repayment` | `loanTransactionType.repayment` | True | 120 | 48 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 24, 25, 37, 42, 43, 46, 49 | 0 | - | 120 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 24, 25, 37, 42, 43, 46, 49 |
| `loanTransactionType.merchantIssuedRefund` | `loanTransactionType.merchantIssuedRefund` | True | 22 | 8 | 11, 12, 13, 14, 37, 38, 40 | 0 | - | 22 | 11, 12, 13, 14, 37, 38, 40 |
| `loanTransactionType.payoutRefund` | `loanTransactionType.payoutRefund` | True | 15 | 5 | 21, 22, 23, 39, 41 | 0 | - | 15 | 21, 22, 23, 39, 41 |
| `loanTransactionType.creditBalanceRefund` | `loanTransactionType.creditBalanceRefund` | True | 6 | 2 | 37 | 0 | - | 6 | 37 |
| `loanTransactionType.interestRefund` | `loanTransactionType.interestRefund` | True | 12 | 4 | 38, 39, 40, 41 | 0 | - | 12 | 38, 39, 40, 41 |

**FINDING:** no non-reversed `chargeOff` loan transaction appears in ANY read-back: no leg is on a charged-off loan.

**FINDING:** no loan's LATEST read-back has `chargedOff=true`: the charged-off dimension is empty (every leg charged-off=no).

## Distinct leg shapes per required arm

Each shape lists the GL account ids and sides, the count of transactions of that shape, and ONE example (loan, tx id, portions in integer minor units, paymentType id).

### `loanTransactionType.refund` (exact code `loanTransactionType.refund`)

| shape (SIDE:account) | account ids | transactions | loans | example loan | example tx | example portions (minor units) | paymentType id |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:9 DEBIT:7 DEBIT:10` | 7, 9, 10 | 1 | 19 | 19 | L71 | principal_minor=13000, interest_minor=0, fee_minor=2000, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | None |

### `loanTransactionType.repayment` (exact code `loanTransactionType.repayment`)

| shape (SIDE:account) | account ids | transactions | loans | example loan | example tx | example portions (minor units) | paymentType id |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:7 DEBIT:9` | 7, 9 | 35 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 24, 25, 49 | 1 | L2 | principal_minor=25000, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | 10 |
| `CREDIT:2 CREDIT:7 DEBIT:9` | 2, 7, 9 | 7 | 19, 42, 43, 46, 49 | 19 | L70 | principal_minor=25500, interest_minor=0, fee_minor=6000, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | 10 |
| `CREDIT:7 CREDIT:9 CREDIT:18 DEBIT:7 DEBIT:9 DEBIT:18` | 7, 9, 18 | 3 | 24, 25 | 24 | L91 | principal_minor=65000, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=10000, unrecognized_income_minor=0 | 10 |
| `CREDIT:7 CREDIT:9 DEBIT:7 DEBIT:9` | 7, 9 | 2 | 24, 37 | 24 | L90 | principal_minor=10000, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | 10 |
| `CREDIT:7 CREDIT:18 DEBIT:9` | 7, 9, 18 | 1 | 20 | 20 | L74 | principal_minor=37500, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=12500, unrecognized_income_minor=0 | 10 |

### `loanTransactionType.merchantIssuedRefund` (exact code `loanTransactionType.merchantIssuedRefund`)

| shape (SIDE:account) | account ids | transactions | loans | example loan | example tx | example portions (minor units) | paymentType id |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:2 DEBIT:9` | 2, 9 | 4 | 11, 12, 13, 14 | 11 | L44 | principal_minor=0, interest_minor=0, fee_minor=0, penalty_minor=3000, overpayment_minor=0, unrecognized_income_minor=0 | 10 |
| `CREDIT:7 DEBIT:9` | 7, 9 | 2 | 37, 40 | 37 | L115 | principal_minor=40000, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | 10 |
| `CREDIT:7 CREDIT:9 CREDIT:18 DEBIT:7 DEBIT:9 DEBIT:18` | 7, 9, 18 | 1 | 37 | 37 | L112 | principal_minor=30000, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=10000, unrecognized_income_minor=0 | 10 |
| `CREDIT:7 CREDIT:9 DEBIT:7 DEBIT:9` | 7, 9 | 1 | 38 | 38 | L117 | principal_minor=10000, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | 10 |

### `loanTransactionType.payoutRefund` (exact code `loanTransactionType.payoutRefund`)

| shape (SIDE:account) | account ids | transactions | loans | example loan | example tx | example portions (minor units) | paymentType id |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:7 CREDIT:18 DEBIT:9` | 7, 9, 18 | 3 | 21, 22, 23 | 21 | L78 | principal_minor=37500, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=12500, unrecognized_income_minor=0 | 10 |
| `CREDIT:7 CREDIT:9 DEBIT:7 DEBIT:9` | 7, 9 | 1 | 39 | 39 | L120 | principal_minor=10000, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | 10 |
| `CREDIT:7 DEBIT:9` | 7, 9 | 1 | 41 | 41 | L126 | principal_minor=10000, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | 10 |

### `loanTransactionType.creditBalanceRefund` (exact code `loanTransactionType.creditBalanceRefund`)

| shape (SIDE:account) | account ids | transactions | loans | example loan | example tx | example portions (minor units) | paymentType id |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:9 CREDIT:18 DEBIT:9 DEBIT:18` | 9, 18 | 1 | 37 | 37 | L113 | principal_minor=0, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=9121, unrecognized_income_minor=0 | 10 |
| `CREDIT:9 DEBIT:7` | 7, 9 | 1 | 37 | 37 | L114 | principal_minor=9121, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | 10 |

### `loanTransactionType.interestRefund` (exact code `loanTransactionType.interestRefund`)

| shape (SIDE:account) | account ids | transactions | loans | example loan | example tx | example portions (minor units) | paymentType id |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:5 CREDIT:7 DEBIT:5 DEBIT:7` | 5, 7 | 2 | 38, 39 | 38 | L118 | principal_minor=57, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | None |
| `CREDIT:7 DEBIT:5` | 5, 7 | 2 | 40, 41 | 40 | L123 | principal_minor=57, interest_minor=0, fee_minor=0, penalty_minor=0, overpayment_minor=0, unrecognized_income_minor=0 | None |

