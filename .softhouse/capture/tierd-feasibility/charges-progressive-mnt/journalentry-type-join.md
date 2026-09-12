# Journal-entry type join — charge-related arms (OH-TIERD20-CX step 6)

536 swept legs across 8 transaction types; 0 legs unmatched to a read-back.

Charged-off rule: a NON-REVERSED chargeOff loan transaction dated on or before the transaction/leg date.  Fraud per leg = the loan fraud flag.

## Type × charged-off → legs → loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 263 | 2 | 40 |
| `loanTransactionType.accrual` | 96 | 2 | 40 |
| `loanTransactionType.disbursement` | 82 | 0 | – |
| `loanTransactionType.downPayment` | 36 | 0 | – |
| `loanTransactionType.merchantIssuedRefund` | 30 | 0 | – |
| `loanTransactionType.interestRefund` | 16 | 0 | – |
| `loanTransactionType.chargeAdjustment` | 8 | 2 | 40 |
| `loanTransactionType.chargeOff` | 5 | 5 | 40 |

## Charge-related arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.chargeAdjustment` | True | 8 | 4 | 30, 36, 40, 41 | 2 | 40 | 6 | 30, 36, 41 |
| `loanTransactionType.chargeOff` | True | 5 | 1 | 40 | 5 | 40 | 0 | – |
| `loanTransactionType.chargeback` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.creditBalanceRefund` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.goodwillCredit` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.interestRefund` | True | 16 | 5 | 26, 27 | 0 | – | 16 | 26, 27 |
| `loanTransactionType.merchantIssuedRefund` | True | 30 | 5 | 26, 27 | 0 | – | 30 | 26, 27 |
| `loanTransactionType.payoutRefund` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.waiveCharges` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.writeoff` | False | 0 | 0 | – | 0 | – | 0 | – |

**FINDING:** charge-related transaction type(s) with NO legs at all: loanTransactionType.chargeback, loanTransactionType.creditBalanceRefund, loanTransactionType.goodwillCredit, loanTransactionType.payoutRefund, loanTransactionType.waiveCharges, loanTransactionType.writeoff.

**FINDING:** 5 charge-related transaction(s) in the read-backs have NO journal-entry legs: loan 23 tx L132, loan 24 tx L138, loan 25 tx L141, loan 39 tx L226, loan 39 tx L227.

## Every charge-related leg — required listing

`charged-off at tx date` = a NON-REVERSED chargeOff dated on or before the leg's transaction date.  `charged-off latest` = the loan `chargedOff` flag in its LATEST read-back, so a charge-off later undone does not count.

| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged-off at tx date | charged-off latest | currency | tx date | charge-off tx |
| --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| `loanTransactionType.interestRefund` | 26 | L148 | DEBIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 26 | L148 | DEBIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 26 | L148 | CREDIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 26 | L148 | CREDIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | DEBIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | DEBIT | 8 | 112601 | Loans Receivable | 17820 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | DEBIT | 9 | 112603 | Interest/Fee Receivable | 12 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | DEBIT | 19 | l1 | Overpayment account | 1048 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | CREDIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | CREDIT | 8 | 112601 | Loans Receivable | 17820 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 12 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | CREDIT | 19 | l1 | Overpayment account | 1048 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 26 | L156 | DEBIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 26 | L156 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L157 | DEBIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L157 | CREDIT | 8 | 112601 | Loans Receivable | 17820 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L157 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 1060 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L173 | DEBIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L173 | DEBIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L173 | CREDIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L173 | CREDIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | DEBIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | DEBIT | 8 | 112601 | Loans Receivable | 17820 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | DEBIT | 9 | 112603 | Interest/Fee Receivable | 12 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | DEBIT | 19 | l1 | Overpayment account | 1048 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | CREDIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | CREDIT | 8 | 112601 | Loans Receivable | 17820 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 12 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | CREDIT | 19 | l1 | Overpayment account | 1048 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L177 | DEBIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L177 | DEBIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L177 | CREDIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L177 | CREDIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | DEBIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | DEBIT | 8 | 112601 | Loans Receivable | 18620 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | DEBIT | 9 | 112603 | Interest/Fee Receivable | 202 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | DEBIT | 19 | l1 | Overpayment account | 58 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | CREDIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | CREDIT | 8 | 112601 | Loans Receivable | 18620 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 202 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | CREDIT | 19 | l1 | Overpayment account | 58 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L179 | DEBIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L179 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L180 | DEBIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L180 | CREDIT | 8 | 112601 | Loans Receivable | 18620 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L180 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 260 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.chargeAdjustment` | 30 | L190 | DEBIT | 3 | 404007 | Fee Income | 100 | False | False | False | MNT | 2024-09-27 | - |
| `loanTransactionType.chargeAdjustment` | 30 | L190 | CREDIT | 8 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2024-09-27 | - |
| `loanTransactionType.chargeAdjustment` | 36 | L213 | DEBIT | 3 | 404007 | Fee Income | 2000 | False | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.chargeAdjustment` | 36 | L213 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 2000 | False | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.chargeOff` | 40 | L231 | DEBIT | 11 | 744007 | Credit Loss/Bad Debt | 10000 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeOff` | 40 | L231 | DEBIT | 12 | 404008 | Fee Charge Off | 500 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeOff` | 40 | L231 | DEBIT | 17 | 404001 | Interest Income Charge Off | 214 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeOff` | 40 | L231 | CREDIT | 8 | 112601 | Loans Receivable | 10000 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeOff` | 40 | L231 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 714 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeAdjustment` | 40 | L232 | DEBIT | 3 | 404007 | Fee Income | 500 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeAdjustment` | 40 | L232 | CREDIT | 12 | 404008 | Fee Charge Off | 500 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeAdjustment` | 41 | L239 | DEBIT | 3 | 404007 | Fee Income | 1000 | False | False | False | MNT | 2025-03-25 | - |
| `loanTransactionType.chargeAdjustment` | 41 | L239 | CREDIT | 8 | 112601 | Loans Receivable | 1000 | False | False | False | MNT | 2025-03-25 | - |

## Every charge-related transaction and its read-back amount / portions

Portions are integer minor units; `-` means the read-back did not carry that field.

| loan | tx | type | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged-off at date | charged-off latest | fraud | currency | legs |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | ---: |
| 23 | L132 | `loanTransactionType.waiveCharges` | 2023-04-05 | 1000 | 0 | 0 | 0 | 0 | 0 | 1000 | False | False | False | False | MNT | 0 |
| 24 | L138 | `loanTransactionType.waiveCharges` | 2023-04-05 | 1000 | 0 | 0 | 0 | 0 | 0 | 1000 | False | False | False | False | MNT | 0 |
| 25 | L141 | `loanTransactionType.waiveCharges` | 2023-02-22 | 10000 | 0 | 0 | 0 | 0 | 0 | 10000 | False | False | False | False | MNT | 0 |
| 26 | L148 | `loanTransactionType.interestRefund` | 2025-08-13 | 787 | 0 | 0 | 0 | 0 | 787 | 0 | False | False | False | False | MNT | 4 |
| 26 | L149 | `loanTransactionType.merchantIssuedRefund` | 2025-08-13 | 18880 | 17820 | 12 | 0 | 0 | 1048 | 0 | False | False | False | False | MNT | 8 |
| 26 | L156 | `loanTransactionType.interestRefund` | 2025-08-13 | 787 | 0 | 12 | 0 | 775 | 0 | 0 | False | False | False | False | MNT | 2 |
| 26 | L157 | `loanTransactionType.merchantIssuedRefund` | 2025-08-13 | 18880 | 17820 | 0 | 0 | 1060 | 0 | 0 | False | False | False | False | MNT | 3 |
| 27 | L173 | `loanTransactionType.interestRefund` | 2025-08-13 | 787 | 0 | 0 | 0 | 0 | 787 | 0 | False | False | False | False | MNT | 4 |
| 27 | L174 | `loanTransactionType.merchantIssuedRefund` | 2025-08-13 | 18880 | 17820 | 12 | 0 | 0 | 1048 | 0 | False | False | False | False | MNT | 8 |
| 27 | L177 | `loanTransactionType.interestRefund` | 2025-08-13 | 787 | 0 | 0 | 0 | 0 | 787 | 0 | False | False | False | False | MNT | 4 |
| 27 | L178 | `loanTransactionType.merchantIssuedRefund` | 2025-08-13 | 18880 | 18620 | 202 | 0 | 0 | 58 | 0 | False | False | False | False | MNT | 8 |
| 27 | L179 | `loanTransactionType.interestRefund` | 2025-08-13 | 787 | 0 | 12 | 0 | 775 | 0 | 0 | False | False | False | False | MNT | 2 |
| 27 | L180 | `loanTransactionType.merchantIssuedRefund` | 2025-08-13 | 18880 | 18620 | 190 | 0 | 70 | 0 | 0 | False | False | False | False | MNT | 3 |
| 30 | L190 | `loanTransactionType.chargeAdjustment` | 2024-09-27 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | False | False | False | False | MNT | 2 |
| 36 | L213 | `loanTransactionType.chargeAdjustment` | 2024-02-01 | 2000 | 0 | 0 | 0 | 2000 | 0 | 0 | False | False | False | False | MNT | 2 |
| 39 | L226 | `loanTransactionType.chargeOff` | 2024-03-01 | 10714 | 10000 | 214 | 500 | 0 | 0 | 0 | False | True | True | False | MNT | 0 |
| 39 | L227 | `loanTransactionType.chargeAdjustment` | 2024-03-01 | 500 | 500 | 0 | 0 | 0 | 0 | 0 | False | True | True | False | MNT | 0 |
| 40 | L231 | `loanTransactionType.chargeOff` | 2024-03-01 | 10714 | 10000 | 214 | 500 | 0 | 0 | 0 | False | True | True | False | MNT | 5 |
| 40 | L232 | `loanTransactionType.chargeAdjustment` | 2024-03-01 | 500 | 500 | 0 | 0 | 0 | 0 | 0 | False | True | True | False | MNT | 2 |
| 41 | L239 | `loanTransactionType.chargeAdjustment` | 2025-03-25 | 1000 | 1000 | 0 | 0 | 0 | 0 | 0 | False | False | False | False | MNT | 2 |

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
| 26 | MNT | False | False | - |
| 27 | MNT | False | False | - |
| 28 | MNT | False | False | - |
| 29 | MNT | False | False | - |
| 30 | MNT | False | False | - |
| 31 | MNT | False | False | - |
| 32 | MNT | False | False | - |
| 33 | MNT | False | False | - |
| 34 | MNT | False | False | - |
| 35 | MNT | False | False | - |
| 36 | MNT | False | False | - |
| 37 | MNT | False | False | - |
| 38 | MNT | False | False | - |
| 39 | MNT | False | True | L226@2024-03-01 |
| 40 | MNT | False | True | L231@2024-03-01 |
| 41 | MNT | False | False | - |
| 42 | MNT | False | False | - |

