# Journal-entry type join — charge-related arms (OH-TIERD19-CW step 6)

353 swept legs across 9 transaction types; 0 legs unmatched to a read-back.

Charged-off rule: a NON-REVERSED chargeOff loan transaction dated on or before the transaction/leg date.  Fraud per leg = the loan fraud flag.

## Type × charged-off → legs → loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 161 | 0 | – |
| `loanTransactionType.accrual` | 72 | 0 | – |
| `loanTransactionType.disbursement` | 50 | 0 | – |
| `loanTransactionType.chargeAdjustment` | 28 | 0 | – |
| `loanTransactionType.goodwillCredit` | 20 | 0 | – |
| `loanTransactionType.chargeback` | 11 | 0 | – |
| `loanTransactionType.payoutRefund` | 7 | 0 | – |
| `loanTransactionType.creditBalanceRefund` | 2 | 0 | – |
| `loanTransactionType.repaymentAtDisbursement` | 2 | 0 | – |

## Charge-related arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.chargeAdjustment` | True | 28 | 8 | 7 | 0 | – | 28 | 7 |
| `loanTransactionType.waiveCharges` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.chargeback` | True | 11 | 3 | 4, 11 | 0 | – | 11 | 4, 11 |
| `loanTransactionType.goodwillCredit` | True | 20 | 4 | 13, 14 | 0 | – | 20 | 13, 14 |
| `loanTransactionType.payoutRefund` | True | 7 | 2 | 18 | 0 | – | 7 | 18 |
| `loanTransactionType.creditBalanceRefund` | True | 2 | 1 | 18 | 0 | – | 2 | 18 |

**FINDING:** charge-related transaction type(s) with NO legs at all: loanTransactionType.waiveCharges.

**FINDING:** 3 charge-related transaction(s) in the read-backs have NO journal-entry legs: loan 5 tx L25, loan 6 tx L31, loan 24 tx L124.

**FINDING:** no non-reversed `chargeOff` loan transaction appears in ANY read-back: no leg is on a charged-off loan, so the `...ForChargeOffLoanChargeAdjustment` arm is NOT exercised by this feature.

**FINDING:** no loan's LATEST read-back has `chargedOff=true`: the charged-off dimension is empty (every leg charged-off=no).

## Every charge-related leg — required listing

`charged-off at tx date` = a NON-REVERSED chargeOff dated on or before the leg's transaction date.  `charged-off latest` = the loan `chargedOff` flag in its LATEST read-back, so a charge-off later undone does not count.

| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged-off at tx date | charged-off latest | currency | tx date | charge-off tx |
| --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| `loanTransactionType.chargeback` | 4 | L17 | DEBIT | 2 | 112601 | Loans Receivable | 25000 | False | False | False | MNT | 2022-05-01 | - |
| `loanTransactionType.chargeback` | 4 | L17 | CREDIT | 5 | 145023 | Suspense/Clearing account | 25000 | False | False | False | MNT | 2022-05-01 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L36 | DEBIT | 7 | 112603 | Interest/Fee Receivable | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L36 | DEBIT | 9 | 404007 | Fee Income | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L36 | CREDIT | 7 | 112603 | Interest/Fee Receivable | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L36 | CREDIT | 9 | 404007 | Fee Income | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | DEBIT | 2 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | DEBIT | 7 | 112603 | Interest/Fee Receivable | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | DEBIT | 9 | 404007 | Fee Income | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | CREDIT | 2 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | CREDIT | 7 | 112603 | Interest/Fee Receivable | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | CREDIT | 9 | 404007 | Fee Income | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L40 | DEBIT | 7 | 112603 | Interest/Fee Receivable | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L40 | DEBIT | 9 | 404007 | Fee Income | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L40 | CREDIT | 7 | 112603 | Interest/Fee Receivable | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L40 | CREDIT | 9 | 404007 | Fee Income | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L41 | DEBIT | 9 | 404007 | Fee Income | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L41 | CREDIT | 2 | 112601 | Loans Receivable | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L43 | DEBIT | 9 | 404007 | Fee Income | 500 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L43 | CREDIT | 2 | 112601 | Loans Receivable | 500 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L45 | DEBIT | 2 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L45 | DEBIT | 9 | 404007 | Fee Income | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L45 | CREDIT | 2 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L45 | CREDIT | 9 | 404007 | Fee Income | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L46 | DEBIT | 9 | 404007 | Fee Income | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L46 | CREDIT | 2 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L47 | DEBIT | 9 | 404007 | Fee Income | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L47 | DEBIT | 19 | l1 | Overpayment account | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L47 | CREDIT | 9 | 404007 | Fee Income | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L47 | CREDIT | 19 | l1 | Overpayment account | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeback` | 11 | L61 | DEBIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L61 | DEBIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L61 | DEBIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L61 | CREDIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L61 | CREDIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L61 | CREDIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L63 | DEBIT | 2 | 112601 | Loans Receivable | 11000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L63 | DEBIT | 19 | l1 | Overpayment account | 19000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L63 | CREDIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | DEBIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | DEBIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | DEBIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | CREDIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | CREDIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | CREDIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | DEBIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | DEBIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | DEBIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | CREDIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | CREDIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | CREDIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L82 | DEBIT | 2 | 112601 | Loans Receivable | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L82 | DEBIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L82 | CREDIT | 2 | 112601 | Loans Receivable | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L82 | CREDIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L83 | DEBIT | 13 | 404008 | Fee Charge Off | 1000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L83 | DEBIT | 18 | 744003 | Goodwill Expense Account | 29000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L83 | CREDIT | 2 | 112601 | Loans Receivable | 29000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L83 | CREDIT | 7 | 112603 | Interest/Fee Receivable | 1000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L98 | DEBIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L98 | DEBIT | 19 | l1 | Overpayment account | 5000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L98 | CREDIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L98 | CREDIT | 19 | l1 | Overpayment account | 5000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L100 | DEBIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L100 | CREDIT | 2 | 112601 | Loans Receivable | 1000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L100 | CREDIT | 19 | l1 | Overpayment account | 4000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.creditBalanceRefund` | 18 | L102 | DEBIT | 19 | l1 | Overpayment account | 4000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.creditBalanceRefund` | 18 | L102 | CREDIT | 5 | 145023 | Suspense/Clearing account | 4000 | False | False | False | MNT | 2023-01-10 | - |

## Every charge-related transaction and its read-back amount / portions

Portions are integer minor units; `-` means the read-back did not carry that field.

| loan | tx | type | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged-off at date | charged-off latest | fraud | currency | legs |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | ---: |
| 4 | L17 | `loanTransactionType.chargeback` | 2022-05-01 | 25000 | 25000 | 0 | 0 | 0 | 0 | 0 | False | False | False | False | MNT | 2 |
| 5 | L25 | `loanTransactionType.waiveCharges` | 2022-04-05 | 1000 | 0 | 0 | 0 | 0 | 0 | 1000 | False | False | False | False | MNT | 0 |
| 6 | L31 | `loanTransactionType.waiveCharges` | 2022-04-05 | 1000 | 0 | 0 | 0 | 0 | 0 | 1000 | True | False | False | False | MNT | 0 |
| 7 | L36 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 300 | 0 | 0 | 0 | 300 | 0 | 0 | False | False | False | False | MNT | 4 |
| 7 | L38 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 300 | 100 | 0 | 0 | 200 | 0 | 0 | True | False | False | False | MNT | 6 |
| 7 | L40 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 400 | 0 | 0 | 200 | 200 | 0 | 0 | False | False | False | False | MNT | 4 |
| 7 | L41 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 400 | 400 | 0 | 0 | 0 | 0 | 0 | False | False | False | False | MNT | 2 |
| 7 | L43 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 500 | 500 | 0 | 0 | 0 | 0 | 0 | False | False | False | False | MNT | 2 |
| 7 | L45 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | True | False | False | False | MNT | 4 |
| 7 | L46 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | False | False | False | False | MNT | 2 |
| 7 | L47 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 200 | 0 | 0 | 0 | 0 | 200 | 0 | True | False | False | False | MNT | 4 |
| 11 | L61 | `loanTransactionType.chargeback` | 2023-01-10 | 30000 | 10000 | 0 | 0 | 0 | 20000 | 0 | False | False | False | False | MNT | 6 |
| 11 | L63 | `loanTransactionType.chargeback` | 2023-01-10 | 30000 | 11000 | 0 | 0 | 0 | 19000 | 0 | False | False | False | False | MNT | 3 |
| 13 | L75 | `loanTransactionType.goodwillCredit` | 2023-01-10 | 30000 | 10000 | 0 | 0 | 0 | 20000 | 0 | True | False | False | False | MNT | 6 |
| 14 | L81 | `loanTransactionType.goodwillCredit` | 2023-01-10 | 30000 | 10000 | 0 | 0 | 0 | 20000 | 0 | False | False | False | False | MNT | 6 |
| 14 | L82 | `loanTransactionType.goodwillCredit` | 2023-01-10 | 30000 | 30000 | 0 | 0 | 0 | 0 | 0 | False | False | False | False | MNT | 4 |
| 14 | L83 | `loanTransactionType.goodwillCredit` | 2023-01-10 | 30000 | 29000 | 0 | 1000 | 0 | 0 | 0 | False | False | False | False | MNT | 4 |
| 18 | L98 | `loanTransactionType.payoutRefund` | 2023-01-10 | 5000 | 0 | 0 | 0 | 0 | 5000 | 0 | False | False | False | False | MNT | 4 |
| 18 | L100 | `loanTransactionType.payoutRefund` | 2023-01-10 | 5000 | 1000 | 0 | 0 | 0 | 4000 | 0 | False | False | False | False | MNT | 3 |
| 18 | L102 | `loanTransactionType.creditBalanceRefund` | 2023-01-10 | 4000 | 0 | 0 | 0 | 0 | 4000 | 0 | False | False | False | False | MNT | 2 |
| 24 | L124 | `loanTransactionType.waiveCharges` | 2023-01-20 | 9500 | 0 | 0 | 0 | 0 | 0 | 9500 | False | False | False | False | MNT | 0 |

## Per-loan currency, charge-off and fraud state

| loan | currency | fraud | charged-off latest read-back | non-reversed chargeOff transactions |
| ---: | --- | --- | --- | --- |
| 1 | MNT | False | False | - |
| 2 | MNT | False | False | - |
| 3 | MNT | False | False | - |
| 4 | MNT | False | False | - |
| 5 | MNT | False | False | - |
| 6 | MNT | False | False | - |
| 7 | MNT | False | False | - |
| 8 | MNT | False | False | - |
| 9 | MNT | False | False | - |
| 10 | MNT | False | False | - |
| 11 | MNT | False | False | - |
| 12 | MNT | False | False | - |
| 13 | MNT | False | False | - |
| 14 | MNT | False | False | - |
| 15 | MNT | False | False | - |
| 16 | MNT | False | False | - |
| 17 | MNT | False | False | - |
| 18 | MNT | False | False | - |
| 19 | MNT | False | False | - |
| 20 | MNT | False | False | - |
| 21 | MNT | False | False | - |
| 22 | MNT | False | False | - |
| 23 | MNT | False | False | - |
| 24 | MNT | False | False | - |
| 25 | MNT | False | False | - |

