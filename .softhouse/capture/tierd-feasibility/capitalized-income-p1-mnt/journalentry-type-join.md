# Journal-entry type join — capitalized-income arms (OH-TIERD18-CS step 6)

3036 swept legs across 12 transaction types; 14 legs unmatched to a read-back.

Charged-off rule: a NON-REVERSED chargeOff loan transaction dated on or before the transaction/leg date.  Fraud per leg = the loan fraud flag.

## Type × charged-off → legs → loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.capitalizedIncomeAmortization` | 1392 | 16 | 24, 25, 26, 30 |
| `loanTransactionType.accrual` | 1000 | 8 | 24, 25, 26, 30 |
| `loanTransactionType.repayment` | 212 | 8 | 24, 25, 26, 30 |
| `loanTransactionType.disbursement` | 162 | 0 | – |
| `loanTransactionType.capitalizedIncome` | 144 | 0 | – |
| `loanTransactionType.capitalizedIncomeAdjustment` | 57 | 0 | – |
| `loanTransactionType.chargeOff` | 24 | 16 | 24, 25, 26, 30 |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 16 | 0 | – |
| `(unmapped)` | 14 | 0 | – |
| `loanTransactionType.accrualAdjustment` | 6 | 0 | – |
| `loanTransactionType.downPayment` | 6 | 0 | – |
| `loanTransactionType.writeOff` | 3 | 0 | – |

## Capitalized-income arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.capitalizedIncome` | True | 144 | 61 | 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | 0 | – | 144 | 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 |
| `loanTransactionType.capitalizedIncomeAdjustment` | True | 57 | 17 | 14, 18, 31, 32, 33, 34, 37, 38, 39, 41, 42, 43, 44, 45 | 0 | – | 57 | 14, 18, 31, 32, 33, 34, 37, 38, 39, 41, 42, 43, 44, 45 |
| `loanTransactionType.capitalizedIncomeAmortization` | True | 1392 | 695 | 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 50 | 16 | 24, 25, 26, 30 | 1376 | 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 50 |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | True | 16 | 8 | 33, 34, 38, 42, 44, 46, 47, 48 | 0 | – | 16 | 33, 34, 38, 42, 44, 46, 47, 48 |

## Every capitalized-income leg — required listing

| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged_off | currency | tx date | charge-off tx |
| --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- |
| `loanTransactionType.capitalizedIncome` | 1 | L3 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 1 | L3 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 1 | L5 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 1 | L5 | CREDIT | 6 | 404000 | Interest Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 2 | L7 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 2 | L7 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 2 | L10 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 2 | L10 | CREDIT | 6 | 404000 | Interest Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 3 | L13 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncome` | 3 | L13 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 3 | L16 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 3 | L16 | CREDIT | 6 | 404000 | Interest Income | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncome` | 6 | L26 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 6 | L26 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 6 | L26 | CREDIT | 10 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 6 | L26 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 6 | L28 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncome` | 6 | L28 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 6 | L30 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 6 | L30 | CREDIT | 6 | 404000 | Interest Income | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncome` | 7 | L33 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 7 | L33 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 7 | L33 | CREDIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 7 | L33 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 7 | L36 | DEBIT | 10 | 112601 | Loans Receivable | 30000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 7 | L36 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 7 | L39 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 7 | L39 | CREDIT | 6 | 404000 | Interest Income | 30000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 8 | L41 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 8 | L41 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 8 | L44 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 8 | L44 | CREDIT | 6 | 404000 | Interest Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 9 | L46 | DEBIT | 10 | 112601 | Loans Receivable | 15000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 9 | L46 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 15000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 9 | L48 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncome` | 9 | L48 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncome` | 9 | L50 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 9 | L50 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 9 | L53 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 9 | L53 | CREDIT | 6 | 404000 | Interest Income | 30000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 10 | L55 | DEBIT | 10 | 112601 | Loans Receivable | 15000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 10 | L55 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 15000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 10 | L55 | CREDIT | 10 | 112601 | Loans Receivable | 15000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 10 | L55 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 15000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 10 | L58 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 10 | L58 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 10 | L61 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 10 | L61 | CREDIT | 6 | 404000 | Interest Income | 20000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 11 | L63 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 11 | L63 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 11 | L63 | CREDIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 11 | L63 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 11 | L66 | DEBIT | 10 | 112601 | Loans Receivable | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 11 | L66 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 11 | L69 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 11 | L69 | CREDIT | 6 | 404000 | Interest Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 12 | L71 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 12 | L71 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 12 | L76 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 12 | L76 | CREDIT | 6 | 404000 | Interest Income | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncome` | 13 | L78 | DEBIT | 10 | 112601 | Loans Receivable | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 13 | L78 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 13 | L78 | CREDIT | 10 | 112601 | Loans Receivable | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 13 | L78 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 13 | L80 | DEBIT | 10 | 112601 | Loans Receivable | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 13 | L80 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 13 | L83 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 13 | L83 | CREDIT | 6 | 404000 | Interest Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 14 | L85 | DEBIT | 10 | 112601 | Loans Receivable | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 14 | L85 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 14 | L86 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 14 | L86 | CREDIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 14 | L89 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 14 | L89 | CREDIT | 6 | 404000 | Interest Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 15 | L91 | DEBIT | 10 | 112601 | Loans Receivable | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 15 | L91 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 15 | L91 | CREDIT | 10 | 112601 | Loans Receivable | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 15 | L91 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 15 | L93 | DEBIT | 10 | 112601 | Loans Receivable | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 15 | L93 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 15 | L96 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 15 | L96 | CREDIT | 6 | 404000 | Interest Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 16 | L98 | DEBIT | 10 | 112601 | Loans Receivable | 60000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 16 | L98 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 60000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 16 | L100 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncome` | 16 | L100 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 16 | L103 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 80000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 16 | L103 | CREDIT | 6 | 404000 | Interest Income | 80000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncome` | 17 | L105 | DEBIT | 10 | 112601 | Loans Receivable | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 17 | L105 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 17 | L105 | CREDIT | 10 | 112601 | Loans Receivable | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 17 | L105 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 17 | L107 | DEBIT | 10 | 112601 | Loans Receivable | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 17 | L107 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 17 | L110 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 17 | L110 | CREDIT | 6 | 404000 | Interest Income | 50000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncome` | 18 | L112 | DEBIT | 10 | 112601 | Loans Receivable | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 18 | L112 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 40000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 18 | L113 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 18 | L113 | CREDIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 18 | L116 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 18 | L116 | CREDIT | 6 | 404000 | Interest Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 19 | L118 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 19 | L118 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 19 | L121 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 19 | L121 | CREDIT | 6 | 404000 | Interest Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 20 | L123 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 20 | L123 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 20 | L126 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 20 | L126 | CREDIT | 6 | 404000 | Interest Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 21 | L129 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 21 | L129 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 21 | L131 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 21 | L131 | CREDIT | 13 | e4 | Written off | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 22 | L133 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 22 | L133 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L134 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L134 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L135 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L135 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L136 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L136 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L137 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L137 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L138 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L138 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L139 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L139 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L140 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L140 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L141 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L141 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L142 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L142 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L143 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L143 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L144 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L144 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L145 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L145 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L146 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L146 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L147 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L147 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L148 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L148 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L149 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L149 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L150 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L150 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L151 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L151 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L152 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L152 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L153 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L153 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L154 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L154 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L155 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L155 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L156 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L156 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L157 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L157 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L158 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L158 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L159 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L159 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L160 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L160 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L161 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L161 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L162 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L162 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L163 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L163 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L164 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L164 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L165 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L165 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L166 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L166 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L167 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L167 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L168 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L168 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L169 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L169 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L170 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L170 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L171 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L171 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L172 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L172 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L173 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L173 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L174 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L174 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L175 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L175 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L176 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L176 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L177 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L177 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L178 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L178 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L179 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L179 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L180 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L180 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L181 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L181 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L182 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L182 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L183 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L183 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L184 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L184 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L185 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L185 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L186 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L186 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L187 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L187 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L188 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L188 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L189 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L189 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L190 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L190 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L191 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L191 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L192 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L192 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L193 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L193 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L194 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L194 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L195 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L195 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L196 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L196 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L197 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-03-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L197 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-03-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L198 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L198 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L199 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L199 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L200 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L200 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L201 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L201 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L202 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L202 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L203 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L203 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L204 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L204 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L205 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L205 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L206 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L206 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L207 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L207 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L208 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L208 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L209 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L209 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L210 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L210 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L211 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L211 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L212 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L212 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L213 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L213 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L214 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L214 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L215 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-03-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L215 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-03-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L216 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L216 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L217 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L217 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L218 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L218 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L219 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L219 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L220 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L220 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L221 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L221 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L222 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L222 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L223 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L223 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L224 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 22 | L224 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.capitalizedIncome` | 23 | L227 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 23 | L227 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L228 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L228 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L229 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L229 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L230 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L230 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L231 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L231 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L232 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L232 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L233 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L233 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L234 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L234 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L235 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L235 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L236 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L236 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L237 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L237 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L238 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L238 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L239 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L239 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L240 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L240 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L241 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L241 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L242 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L242 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L243 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L243 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L244 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L244 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L245 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L245 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L246 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L246 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L247 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L247 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L248 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L248 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L249 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L249 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L250 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L250 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L251 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L251 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L252 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L252 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L253 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L253 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L254 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L254 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L255 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L255 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L256 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L256 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L257 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L257 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L258 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L258 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L259 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L259 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L260 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L260 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L261 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L261 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L262 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L262 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L263 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L263 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L264 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L264 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L265 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L265 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L266 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L266 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L267 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L267 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L268 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L268 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L269 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L269 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L270 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L270 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L271 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L271 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L272 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L272 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L273 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L273 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L274 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L274 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L275 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L275 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L276 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L276 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L277 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L277 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L278 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L278 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L279 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L279 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L280 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L280 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L281 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L281 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L282 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L282 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L283 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L283 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L284 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L284 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L285 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L285 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L286 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L286 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L287 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L287 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L288 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L288 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L289 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L289 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L290 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L290 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L291 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-03-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L291 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-03-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L292 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L292 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L293 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L293 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L294 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L294 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L295 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L295 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L296 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L296 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L297 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L297 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L298 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L298 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L299 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L299 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L300 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L300 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L301 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L301 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L302 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L302 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L303 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L303 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L304 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L304 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L305 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L305 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L306 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L306 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L307 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L307 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L308 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L308 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L309 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-03-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L309 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-03-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L310 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L310 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L311 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L311 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L312 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L312 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L313 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L313 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L314 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L314 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L315 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L315 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L316 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L316 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L317 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L317 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L318 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 23 | L318 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.capitalizedIncome` | 24 | L321 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | True | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 24 | L321 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | True | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 24 | L322 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 8333 | True | True | MNT | 2024-01-26 | L324 |
| `loanTransactionType.capitalizedIncomeAmortization` | 24 | L322 | CREDIT | 6 | 404000 | Interest Income | 8333 | True | True | MNT | 2024-01-26 | L324 |
| `loanTransactionType.capitalizedIncomeAmortization` | 24 | L325 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1667 | True | True | MNT | 2024-01-26 | L324 |
| `loanTransactionType.capitalizedIncomeAmortization` | 24 | L325 | CREDIT | 14 | 744007 | Credit Loss/Bad Debt | 1667 | True | True | MNT | 2024-01-26 | L324 |
| `loanTransactionType.capitalizedIncome` | 25 | L328 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | True | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 25 | L328 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | True | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 25 | L329 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 8333 | True | True | MNT | 2024-01-26 | L331 |
| `loanTransactionType.capitalizedIncomeAmortization` | 25 | L329 | CREDIT | 6 | 404000 | Interest Income | 8333 | True | True | MNT | 2024-01-26 | L331 |
| `loanTransactionType.capitalizedIncomeAmortization` | 25 | L332 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1667 | True | True | MNT | 2024-01-26 | L331 |
| `loanTransactionType.capitalizedIncomeAmortization` | 25 | L332 | CREDIT | 12 | 744037 | Credit Loss/Bad Debt-Fraud | 1667 | True | True | MNT | 2024-01-26 | L331 |
| `loanTransactionType.capitalizedIncome` | 26 | L335 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | True | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 26 | L335 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | True | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 26 | L336 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 8333 | True | True | MNT | 2024-01-26 | L338 |
| `loanTransactionType.capitalizedIncomeAmortization` | 26 | L336 | CREDIT | 6 | 404000 | Interest Income | 8333 | True | True | MNT | 2024-01-26 | L338 |
| `loanTransactionType.capitalizedIncomeAmortization` | 26 | L339 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1667 | True | True | MNT | 2024-01-26 | L338 |
| `loanTransactionType.capitalizedIncomeAmortization` | 26 | L339 | CREDIT | 14 | 744007 | Credit Loss/Bad Debt | 1667 | True | True | MNT | 2024-01-26 | L338 |
| `loanTransactionType.capitalizedIncome` | 27 | L342 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | True | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 27 | L342 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | True | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 27 | L343 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 8333 | True | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 27 | L343 | CREDIT | 6 | 404000 | Interest Income | 8333 | True | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 27 | L346 | DEBIT | 14 | 744007 | Credit Loss/Bad Debt | 1667 | True | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 27 | L346 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1667 | True | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 27 | L346 | CREDIT | 14 | 744007 | Credit Loss/Bad Debt | 1667 | True | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 27 | L346 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 1667 | True | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 27 | L348 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1667 | True | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 27 | L348 | CREDIT | 6 | 404000 | Interest Income | 1667 | True | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncome` | 28 | L350 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 28 | L350 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L351 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L351 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L353 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L353 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L355 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L355 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L357 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L357 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L359 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L359 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L361 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L361 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L363 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L363 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L365 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L365 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L367 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L367 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L369 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L369 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L371 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L371 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L373 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L373 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L375 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L375 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L377 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L377 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L379 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L379 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L381 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L381 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L383 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L383 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L385 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L385 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L387 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L387 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L389 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L389 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L391 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L391 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L393 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L393 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L395 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L395 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L397 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L397 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L399 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L399 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L401 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L401 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L403 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L403 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L405 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L405 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L407 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L407 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L409 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L409 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L411 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L411 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L414 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L414 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L416 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L416 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L418 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L418 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L420 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L420 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L422 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L422 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L424 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L424 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L426 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L426 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L428 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L428 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L430 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L430 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L432 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L432 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L434 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L434 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L436 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L436 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L438 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L438 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L440 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L440 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L442 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L442 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L444 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L444 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L446 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L446 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L448 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L448 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L450 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L450 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L452 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L452 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L454 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L454 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L456 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L456 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L458 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L458 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L460 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L460 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L462 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L462 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L464 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L464 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L466 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L466 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L468 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L468 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L470 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L470 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L473 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L473 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L475 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L475 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L477 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L477 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L479 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-03-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L479 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-03-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L481 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L481 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L483 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L483 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L485 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L485 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L487 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L487 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L489 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L489 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L491 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L491 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L492 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L492 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L494 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L494 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L496 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L496 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L498 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L498 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L500 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L500 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L502 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L502 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L504 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L504 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L506 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L506 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L508 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L508 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L510 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L510 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L512 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L512 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L514 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-03-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L514 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-03-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L516 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L516 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L518 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L518 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L520 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L520 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L522 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L522 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L524 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L524 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L526 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L526 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L528 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L528 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L529 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L529 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L531 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 28 | L531 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.capitalizedIncome` | 29 | L535 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 29 | L535 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L536 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L536 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L538 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L538 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L540 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L540 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L542 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L542 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L544 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L544 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L546 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L546 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L548 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L548 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L550 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L550 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L552 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L552 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L554 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L554 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L556 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L556 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L558 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L558 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L560 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L560 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L562 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L562 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L564 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L564 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L566 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L566 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L568 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L568 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L570 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L570 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L572 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L572 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L574 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L574 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L576 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L576 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L578 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L578 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L580 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L580 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L582 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L582 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L584 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L584 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L586 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L586 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L588 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L588 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L590 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L590 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L592 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L592 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L594 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L594 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L596 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L596 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L599 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L599 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L601 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L601 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L603 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L603 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L605 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L605 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L607 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L607 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L609 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L609 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L611 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L611 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L613 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L613 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L615 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L615 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L617 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L617 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L619 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L619 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L621 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L621 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L623 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L623 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L625 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L625 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L627 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L627 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L629 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L629 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L631 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L631 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L633 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L633 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L635 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L635 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L637 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L637 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L639 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L639 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L641 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L641 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L643 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L643 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L645 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L645 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L647 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L647 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L649 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L649 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L651 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L651 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L653 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L653 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L655 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L655 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L658 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1703 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 29 | L658 | CREDIT | 6 | 404000 | Interest Income | 1703 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncome` | 30 | L660 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 30 | L660 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L661 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L661 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L663 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L663 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L665 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L665 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L667 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L667 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L669 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L669 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L671 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L671 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L673 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L673 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L675 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L675 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L677 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L677 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L679 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L679 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L681 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L681 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L683 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L683 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L685 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L685 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L687 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L687 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L689 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L689 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L691 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L691 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L693 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L693 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L695 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L695 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L697 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L697 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L699 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L699 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L701 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L701 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L703 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L703 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L705 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L705 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L707 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L707 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L709 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L709 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L711 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L711 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L713 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L713 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L715 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L715 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L717 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L717 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L719 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L719 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L721 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L721 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L724 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L724 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L726 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L726 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L728 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L728 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L730 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L730 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L732 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L732 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L734 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L734 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L736 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L736 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L738 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L738 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L740 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L740 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L742 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L742 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L744 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L744 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L746 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L746 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L748 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L748 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L750 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L750 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L752 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L752 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L754 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L754 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L756 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L756 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L758 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L758 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L760 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L760 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L762 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L762 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L764 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L764 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L766 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L766 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L768 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L768 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L770 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L770 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L772 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L772 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L774 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L774 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L776 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L776 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L778 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L778 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L780 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L780 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L781 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | True | MNT | 2024-03-01 | L783 |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L781 | CREDIT | 6 | 404000 | Interest Income | 55 | False | True | MNT | 2024-03-01 | L783 |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L784 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1648 | False | True | MNT | 2024-03-01 | L783 |
| `loanTransactionType.capitalizedIncomeAmortization` | 30 | L784 | CREDIT | 14 | 744007 | Credit Loss/Bad Debt | 1648 | False | True | MNT | 2024-03-01 | L783 |
| `loanTransactionType.capitalizedIncome` | 31 | L787 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 31 | L787 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 31 | L790 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1758 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 31 | L790 | CREDIT | 6 | 404000 | Interest Income | 1758 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 31 | L792 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 31 | L792 | CREDIT | 10 | 112601 | Loans Receivable | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 31 | L795 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 2242 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 31 | L795 | CREDIT | 6 | 404000 | Interest Income | 2242 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.capitalizedIncome` | 32 | L797 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 32 | L797 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 32 | L800 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1758 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 32 | L800 | CREDIT | 6 | 404000 | Interest Income | 1758 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 32 | L802 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 32 | L802 | CREDIT | 10 | 112601 | Loans Receivable | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 32 | L803 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 500 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 32 | L803 | CREDIT | 10 | 112601 | Loans Receivable | 500 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 32 | L806 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1742 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 32 | L806 | CREDIT | 6 | 404000 | Interest Income | 1742 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.capitalizedIncome` | 33 | L808 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 33 | L808 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L809 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L809 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L811 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L811 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L813 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L813 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L815 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L815 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L817 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L817 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L819 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L819 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L821 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L821 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L823 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L823 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L825 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L825 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L827 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L827 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L829 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L829 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L831 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L831 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L833 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L833 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L835 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L835 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L837 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L837 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L839 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L839 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L841 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L841 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L843 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L843 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L845 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L845 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L847 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L847 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L849 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L849 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L851 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L851 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L853 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L853 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L855 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L855 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L857 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L857 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L859 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L859 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L861 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L861 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L863 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L863 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L865 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L865 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L867 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L867 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L869 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L869 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L871 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L871 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L873 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L873 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L875 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L875 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L877 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L877 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L879 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L879 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L881 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L881 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L883 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L883 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L885 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L885 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L887 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L887 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L889 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L889 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L891 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L891 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L893 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L893 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L895 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L895 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L897 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L897 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L899 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L899 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L901 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L901 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L903 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L903 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L905 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L905 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L907 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L907 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L909 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L909 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L911 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L911 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L913 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L913 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L915 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L915 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L917 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L917 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L919 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L919 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L921 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L921 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L923 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L923 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L925 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L925 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L927 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 33 | L927 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 33 | L928 | DEBIT | 1 | 112603 | Interest/Fee Receivable | 29 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 33 | L928 | DEBIT | 10 | 112601 | Loans Receivable | 4971 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 33 | L928 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 33 | L928 | CREDIT | 1 | 112603 | Interest/Fee Receivable | 29 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 33 | L928 | CREDIT | 10 | 112601 | Loans Receivable | 4971 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 33 | L928 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 33 | L929 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 33 | L929 | CREDIT | 1 | 112603 | Interest/Fee Receivable | 87 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 33 | L929 | CREDIT | 10 | 112601 | Loans Receivable | 4913 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 33 | L933 | DEBIT | 6 | 404000 | Interest Income | 3297 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 33 | L933 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 3297 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncome` | 34 | L935 | DEBIT | 10 | 112601 | Loans Receivable | 5100 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 34 | L935 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5100 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L936 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L936 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L938 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L938 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L940 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L940 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L942 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L942 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L944 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L944 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L946 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L946 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L948 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L948 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L950 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L950 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L952 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L952 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L954 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L954 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L956 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L956 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L958 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 57 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L958 | CREDIT | 6 | 404000 | Interest Income | 57 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L960 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L960 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L962 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L962 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L964 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L964 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L966 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L966 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L968 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L968 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L970 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L970 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L972 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L972 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L974 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L974 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L976 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L976 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L978 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L978 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L980 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L980 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L982 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L982 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L984 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L984 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L986 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L986 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L988 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L988 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L990 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L990 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L992 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L992 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L994 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L994 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L996 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L996 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L998 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L998 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1000 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1000 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1002 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1002 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1004 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 57 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1004 | CREDIT | 6 | 404000 | Interest Income | 57 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1006 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1006 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1008 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1008 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1010 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1010 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1012 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1012 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1014 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1014 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1016 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1016 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1018 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1018 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1020 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1020 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1022 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1022 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1024 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1024 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1026 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1026 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1028 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1028 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1030 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1030 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1032 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1032 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1034 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1034 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1036 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1036 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1038 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1038 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1040 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1040 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1042 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1042 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1044 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1044 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1046 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1046 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1048 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 57 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1048 | CREDIT | 6 | 404000 | Interest Income | 57 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1050 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1050 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1052 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1052 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1054 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 34 | L1054 | CREDIT | 6 | 404000 | Interest Income | 56 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 34 | L1055 | DEBIT | 1 | 112603 | Interest/Fee Receivable | 88 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 34 | L1055 | DEBIT | 10 | 112601 | Loans Receivable | 5012 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 34 | L1055 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5100 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 34 | L1055 | CREDIT | 1 | 112603 | Interest/Fee Receivable | 88 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 34 | L1055 | CREDIT | 10 | 112601 | Loans Receivable | 5012 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 34 | L1055 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5100 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 34 | L1056 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5100 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 34 | L1056 | CREDIT | 1 | 112603 | Interest/Fee Receivable | 96 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 34 | L1056 | CREDIT | 10 | 112601 | Loans Receivable | 5004 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 34 | L1059 | DEBIT | 6 | 404000 | Interest Income | 3363 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 34 | L1059 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 3363 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncome` | 35 | L1061 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 35 | L1061 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 35 | L1064 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 35 | L1064 | CREDIT | 6 | 404000 | Interest Income | 5000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncome` | 36 | L1066 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 36 | L1066 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 36 | L1069 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 36 | L1069 | CREDIT | 6 | 404000 | Interest Income | 5000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncome` | 37 | L1071 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 37 | L1071 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 37 | L1072 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 3000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 37 | L1072 | CREDIT | 10 | 112601 | Loans Receivable | 3000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 37 | L1075 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 2000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 37 | L1075 | CREDIT | 6 | 404000 | Interest Income | 2000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncome` | 38 | L1077 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 38 | L1077 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 38 | L1080 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1758 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 38 | L1080 | CREDIT | 6 | 404000 | Interest Income | 1758 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 38 | L1082 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 38 | L1082 | CREDIT | 1 | 112603 | Interest/Fee Receivable | 1 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 38 | L1082 | CREDIT | 10 | 112601 | Loans Receivable | 4999 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 38 | L1084 | DEBIT | 6 | 404000 | Interest Income | 1758 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 38 | L1084 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 1758 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncome` | 39 | L1086 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 39 | L1086 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 39 | L1087 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 3000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 39 | L1087 | CREDIT | 10 | 112601 | Loans Receivable | 3000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 39 | L1090 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 2000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 39 | L1090 | CREDIT | 6 | 404000 | Interest Income | 2000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncome` | 40 | L1092 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 40 | L1092 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 40 | L1093 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 40 | L1093 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 40 | L1096 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 4945 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 40 | L1096 | CREDIT | 6 | 404000 | Interest Income | 4945 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 41 | L1098 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 41 | L1098 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 41 | L1099 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 4000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 41 | L1099 | CREDIT | 10 | 112601 | Loans Receivable | 4000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 41 | L1100 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 11 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 41 | L1100 | CREDIT | 6 | 404000 | Interest Income | 11 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 41 | L1103 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 989 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 41 | L1103 | CREDIT | 6 | 404000 | Interest Income | 989 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncome` | 42 | L1105 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 42 | L1105 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1106 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1106 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1108 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1108 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1110 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1110 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1112 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1112 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1114 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1114 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1116 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1116 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1118 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1118 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1120 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1120 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1122 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1122 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1124 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1124 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1126 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1126 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1128 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1128 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1130 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1130 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1132 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1132 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1134 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1134 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1136 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1136 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1138 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1138 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1140 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1140 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1142 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1142 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1144 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1144 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1146 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1146 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1148 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1148 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1150 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1150 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1152 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1152 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1154 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1154 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1156 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1156 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1158 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1158 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1160 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1160 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1162 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1162 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1164 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1164 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1166 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1166 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1168 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1168 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1170 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1170 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1172 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1172 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1174 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1174 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1176 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1176 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1178 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1178 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1180 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1180 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1182 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1182 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1184 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1184 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1186 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1186 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1188 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1188 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1190 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1190 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1192 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1192 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1194 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1194 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1196 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1196 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1198 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1198 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1200 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1200 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1202 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1202 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1204 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1204 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1206 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1206 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1208 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1208 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1210 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1210 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1212 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1212 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1214 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1214 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1216 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1216 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1218 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1218 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1220 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1220 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1222 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1222 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1224 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1224 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 42 | L1225 | DEBIT | 10 | 112601 | Loans Receivable | 4000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 42 | L1225 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 4000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 42 | L1225 | CREDIT | 10 | 112601 | Loans Receivable | 4000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 42 | L1225 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 4000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 42 | L1227 | DEBIT | 6 | 404000 | Interest Income | 2297 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 42 | L1227 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 2297 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1229 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 2407 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1229 | CREDIT | 6 | 404000 | Interest Income | 2407 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1232 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 1593 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 42 | L1232 | CREDIT | 6 | 404000 | Interest Income | 1593 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.capitalizedIncome` | 43 | L1234 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 43 | L1234 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1235 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1235 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1237 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1237 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1239 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1239 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1241 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1241 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1243 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1243 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1245 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1245 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1247 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1247 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1249 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1249 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1251 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1251 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 43 | L1252 | DEBIT | 10 | 112601 | Loans Receivable | 4000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 43 | L1252 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 4000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 43 | L1252 | CREDIT | 10 | 112601 | Loans Receivable | 4000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 43 | L1252 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 4000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1254 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 6 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1254 | CREDIT | 6 | 404000 | Interest Income | 6 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1256 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 103 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1256 | CREDIT | 6 | 404000 | Interest Income | 103 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1259 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 4396 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 43 | L1259 | CREDIT | 6 | 404000 | Interest Income | 4396 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncome` | 44 | L1261 | DEBIT | 10 | 112601 | Loans Receivable | 6000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 44 | L1261 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 6000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1262 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 66 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1262 | CREDIT | 6 | 404000 | Interest Income | 66 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1264 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 66 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1264 | CREDIT | 6 | 404000 | Interest Income | 66 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1266 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 66 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1266 | CREDIT | 6 | 404000 | Interest Income | 66 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1268 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 66 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1268 | CREDIT | 6 | 404000 | Interest Income | 66 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1270 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 66 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1270 | CREDIT | 6 | 404000 | Interest Income | 66 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1272 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 66 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1272 | CREDIT | 6 | 404000 | Interest Income | 66 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1274 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 66 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1274 | CREDIT | 6 | 404000 | Interest Income | 66 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1276 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 65 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1276 | CREDIT | 6 | 404000 | Interest Income | 65 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1278 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 66 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1278 | CREDIT | 6 | 404000 | Interest Income | 66 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 44 | L1279 | DEBIT | 1 | 112603 | Interest/Fee Receivable | 25 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 44 | L1279 | DEBIT | 10 | 112601 | Loans Receivable | 5475 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 44 | L1279 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5500 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 44 | L1279 | CREDIT | 1 | 112603 | Interest/Fee Receivable | 25 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 44 | L1279 | CREDIT | 10 | 112601 | Loans Receivable | 5475 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 44 | L1279 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5500 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 44 | L1281 | DEBIT | 6 | 404000 | Interest Income | 93 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 44 | L1281 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 93 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1283 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 225 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1283 | CREDIT | 6 | 404000 | Interest Income | 225 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1286 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5275 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 44 | L1286 | CREDIT | 6 | 404000 | Interest Income | 5275 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncome` | 45 | L1288 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 45 | L1288 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 45 | L1289 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 110 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 45 | L1289 | CREDIT | 6 | 404000 | Interest Income | 110 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 45 | L1291 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 110 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 45 | L1291 | CREDIT | 6 | 404000 | Interest Income | 110 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 45 | L1292 | DEBIT | 1 | 112603 | Interest/Fee Receivable | 8 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 45 | L1292 | DEBIT | 10 | 112601 | Loans Receivable | 9992 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 45 | L1292 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 45 | L1292 | CREDIT | 1 | 112603 | Interest/Fee Receivable | 8 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 45 | L1292 | CREDIT | 10 | 112601 | Loans Receivable | 9992 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 45 | L1292 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 45 | L1294 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 110 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 45 | L1294 | CREDIT | 6 | 404000 | Interest Income | 110 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 45 | L1296 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 110 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 45 | L1296 | CREDIT | 6 | 404000 | Interest Income | 110 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 45 | L1299 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 9560 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 45 | L1299 | CREDIT | 6 | 404000 | Interest Income | 9560 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 46 | L1301 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 46 | L1301 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 46 | L1301 | CREDIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncome` | 46 | L1301 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1302 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1302 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1304 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1304 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1306 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1306 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1308 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1308 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1310 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1310 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1312 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1312 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1314 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1314 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1316 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1316 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1318 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1318 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1320 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1320 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1322 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1322 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1324 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1324 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1326 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1326 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1328 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1328 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1330 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1330 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1332 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1332 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1334 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1334 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1336 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1336 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1338 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1338 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1340 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1340 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1342 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1342 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1344 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1344 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1346 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1346 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1348 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1348 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1350 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1350 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1352 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1352 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1354 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1354 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1356 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1356 | CREDIT | 6 | 404000 | Interest Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1358 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1358 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1360 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1360 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1362 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1362 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1365 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1365 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1367 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1367 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1369 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1369 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1371 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1371 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1373 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1373 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1375 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1375 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1377 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1377 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1379 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1379 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1381 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1381 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1383 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1383 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1385 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1385 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1387 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1387 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1389 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1389 | CREDIT | 6 | 404000 | Interest Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 46 | L1392 | DEBIT | 6 | 404000 | Interest Income | 2418 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 46 | L1392 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 2418 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.capitalizedIncome` | 46 | L1394 | DEBIT | 10 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncome` | 46 | L1394 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1397 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 46 | L1397 | CREDIT | 6 | 404000 | Interest Income | 5000 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.capitalizedIncome` | 47 | L1399 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 47 | L1399 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 47 | L1399 | CREDIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 47 | L1399 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 47 | L1402 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 47 | L1402 | CREDIT | 6 | 404000 | Interest Income | 20000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 47 | L1404 | DEBIT | 6 | 404000 | Interest Income | 20000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 47 | L1404 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 48 | L1407 | DEBIT | 10 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 48 | L1407 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 48 | L1408 | DEBIT | 10 | 112601 | Loans Receivable | 15000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncome` | 48 | L1408 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 15000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncome` | 48 | L1408 | CREDIT | 10 | 112601 | Loans Receivable | 15000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncome` | 48 | L1408 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 15000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncome` | 48 | L1409 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncome` | 48 | L1409 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 48 | L1412 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 45000 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 48 | L1412 | CREDIT | 6 | 404000 | Interest Income | 45000 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 48 | L1415 | DEBIT | 6 | 404000 | Interest Income | 15000 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 48 | L1415 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 15000 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.capitalizedIncome` | 49 | L1418 | DEBIT | 10 | 112601 | Loans Receivable | 50000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 49 | L1418 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 50000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 49 | L1418 | CREDIT | 10 | 112601 | Loans Receivable | 50000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 49 | L1418 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 50000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.capitalizedIncome` | 50 | L1424 | DEBIT | 10 | 112601 | Loans Receivable | 20000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncome` | 50 | L1424 | CREDIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 50 | L1427 | DEBIT | 23 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.capitalizedIncomeAmortization` | 50 | L1427 | CREDIT | 6 | 404000 | Interest Income | 20000 | False | False | MNT | 2024-01-10 | - |

## Every capitalized-income transaction and its read-back amount / portions

Portions are integer minor units; `-` means the read-back did not carry that field.

| loan | tx | type | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged_off | fraud | currency | legs |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| 1 | L3 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 1 | L5 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 10000 | 0 | 10000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L7 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L10 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 10000 | 0 | 10000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 3 | L13 | `loanTransactionType.capitalizedIncome` | 2024-01-03 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 3 | L16 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L26 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 6 | L28 | `loanTransactionType.capitalizedIncome` | 2024-01-03 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L30 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L33 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 7 | L36 | `loanTransactionType.capitalizedIncome` | 2024-01-04 | 30000 | 30000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L39 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 8 | L41 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 8 | L44 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 9 | L46 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 15000 | 15000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 9 | L48 | `loanTransactionType.capitalizedIncome` | 2024-01-03 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 9 | L50 | `loanTransactionType.capitalizedIncome` | 2024-01-04 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 9 | L53 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 10 | L55 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 15000 | 15000 | 0 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 10 | L58 | `loanTransactionType.capitalizedIncome` | 2024-01-04 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 10 | L61 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 11 | L63 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 11 | L66 | `loanTransactionType.capitalizedIncome` | 2024-01-04 | 50000 | 50000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 11 | L69 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 50000 | 0 | 50000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 12 | L71 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 12 | L76 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 13 | L78 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 40000 | 40000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 13 | L80 | `loanTransactionType.capitalizedIncome` | 2024-01-04 | 50000 | 50000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 13 | L83 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 50000 | 0 | 50000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 14 | L85 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 40000 | 40000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 14 | L86 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-01-02 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 14 | L89 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 15 | L91 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 40000 | 40000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 15 | L93 | `loanTransactionType.capitalizedIncome` | 2024-01-04 | 50000 | 50000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 15 | L96 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 50000 | 0 | 50000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L98 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 60000 | 60000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L100 | `loanTransactionType.capitalizedIncome` | 2024-01-03 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L103 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 80000 | 0 | 80000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L105 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 40000 | 40000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 17 | L107 | `loanTransactionType.capitalizedIncome` | 2024-01-04 | 50000 | 50000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L110 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 50000 | 0 | 50000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 18 | L112 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 40000 | 40000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 18 | L113 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-01-02 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 18 | L116 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L118 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L121 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 10000 | 0 | 10000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 20 | L123 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 20 | L126 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 10000 | 0 | 10000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 21 | L129 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 21 | L131 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 10000 | 0 | 10000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L133 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L134 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L135 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L136 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L137 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L138 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L139 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L140 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L141 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L142 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L143 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L144 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L145 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L146 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L147 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L148 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L149 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L150 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L151 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L152 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L153 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L154 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L155 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L156 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L157 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L158 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L159 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L160 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L161 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L162 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L163 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L164 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L165 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L166 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L167 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L168 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L169 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L170 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L171 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L172 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L173 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L174 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L175 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L176 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L177 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L178 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L179 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L180 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L181 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L182 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L183 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L184 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L185 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L186 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L187 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L188 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L189 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L190 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L191 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L192 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L193 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L194 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L195 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L196 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L197 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-04 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L198 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L199 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L200 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L201 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L202 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L203 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L204 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L205 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L206 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L207 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L208 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L209 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L210 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L211 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L212 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L213 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L214 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L215 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-22 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L216 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L217 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L218 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L219 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L220 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L221 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L222 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L223 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L224 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L227 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L228 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L229 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L230 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L231 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L232 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L233 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L234 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L235 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L236 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L237 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 54 | 0 | 0 | 54 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L238 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L239 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L240 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-13 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L241 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-14 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L242 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-15 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L243 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-16 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L244 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-17 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L245 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-18 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L246 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-19 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L247 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-20 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L248 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-21 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L249 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-22 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L250 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-23 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L251 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-24 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L252 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-25 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L253 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L254 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-27 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L255 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-28 | 54 | 0 | 0 | 54 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L256 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-29 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L257 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-30 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L258 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-31 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L259 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L260 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-02 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L261 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-03 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L262 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-04 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L263 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-05 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L264 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-06 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L265 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-07 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L266 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-08 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L267 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-09 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L268 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-10 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L269 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-11 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L270 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-12 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L271 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-13 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L272 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-14 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L273 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-15 | 54 | 0 | 0 | 54 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L274 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-16 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L275 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-17 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L276 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-18 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L277 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-19 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L278 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-20 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L279 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-21 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L280 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-22 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L281 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-23 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L282 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-24 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L283 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-25 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L284 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-26 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L285 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-27 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L286 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-28 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L287 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-29 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L288 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-01 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L289 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-02 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L290 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-03 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L291 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-04 | 54 | 0 | 0 | 54 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L292 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-05 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L293 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-06 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L294 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-07 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L295 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-08 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L296 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-09 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L297 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-10 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L298 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-11 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L299 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-12 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L300 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-13 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L301 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-14 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L302 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-15 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L303 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-16 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L304 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-17 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L305 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-18 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L306 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-19 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L307 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-20 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L308 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-21 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L309 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-22 | 54 | 0 | 0 | 54 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L310 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-23 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L311 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-24 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L312 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-25 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L313 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-26 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L314 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-27 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L315 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-28 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L316 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-29 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L317 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-30 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L318 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-31 | 55 | 0 | 0 | 55 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 24 | L321 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 24 | L322 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 8333 | 0 | 8333 | 0 | 0 | 0 | 0 | False | True | True | MNT | 2 |
| 24 | L325 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 1667 | 0 | 1667 | 0 | 0 | 0 | 0 | False | True | True | MNT | 2 |
| 25 | L328 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 25 | L329 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 8333 | 0 | 8333 | 0 | 0 | 0 | 0 | False | True | True | MNT | 2 |
| 25 | L332 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 1667 | 0 | 1667 | 0 | 0 | 0 | 0 | False | True | True | MNT | 2 |
| 26 | L335 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 26 | L336 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 8333 | 0 | 8333 | 0 | 0 | 0 | 0 | False | True | True | MNT | 2 |
| 26 | L339 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 1667 | 0 | 1667 | 0 | 0 | 0 | 0 | False | True | True | MNT | 2 |
| 27 | L342 | `loanTransactionType.capitalizedIncome` | 2024-01-02 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 27 | L343 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 8333 | 0 | 8333 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 27 | L346 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 1667 | 0 | 1667 | 0 | 0 | 0 | 0 | False | False | True | MNT | 4 |
| 27 | L348 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 1667 | 0 | 1667 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 28 | L350 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L351 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L353 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L355 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L357 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L359 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L361 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L363 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L365 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L367 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L369 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L371 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L373 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L375 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L377 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L379 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L381 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L383 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L385 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L387 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L389 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L391 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L393 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L395 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L397 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L399 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L401 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L403 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L405 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L407 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L409 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L411 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L414 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L416 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L418 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L420 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L422 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L424 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L426 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L428 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L430 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L432 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L434 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L436 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L438 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L440 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L442 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L444 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L446 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L448 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L450 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L452 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L454 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L456 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L458 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L460 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L462 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L464 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L466 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L468 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L470 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L473 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L475 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L477 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L479 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-04 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L481 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L483 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L485 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L487 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L489 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L491 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L492 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L494 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L496 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L498 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L500 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L502 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L504 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L506 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L508 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L510 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L512 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L514 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-22 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L516 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L518 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L520 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L522 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L524 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L526 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L528 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L529 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L531 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L535 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L536 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L538 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L540 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L542 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L544 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L546 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L548 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L550 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L552 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L554 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L556 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L558 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L560 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L562 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L564 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L566 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L568 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L570 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L572 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L574 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L576 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L578 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L580 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L582 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L584 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L586 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L588 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L590 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L592 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L594 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L596 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L599 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L601 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L603 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L605 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L607 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L609 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L611 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L613 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L615 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L617 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L619 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L621 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L623 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L625 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L627 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L629 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L631 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L633 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L635 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L637 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L639 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L641 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L643 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L645 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L647 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L649 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L651 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L653 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L655 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L658 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-01 | 1703 | 0 | 1703 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L660 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L661 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L663 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L665 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L667 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L669 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L671 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L673 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L675 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L677 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L679 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L681 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L683 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L685 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L687 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L689 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L691 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L693 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L695 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L697 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L699 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L701 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L703 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L705 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L707 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L709 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L711 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L713 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L715 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L717 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L719 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L721 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L724 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L726 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L728 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L730 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L732 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L734 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L736 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L738 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L740 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L742 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L744 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L746 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L748 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L750 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L752 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L754 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L756 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L758 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L760 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L762 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L764 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L766 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L768 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L770 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L772 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L774 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L776 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L778 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L780 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L781 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 30 | L784 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-01 | 1648 | 0 | 1648 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 31 | L787 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L790 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 1758 | 0 | 1758 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L792 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-03-01 | 1000 | 1000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L795 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-04-01 | 2242 | 0 | 2242 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 32 | L797 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 32 | L800 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 1758 | 0 | 1758 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 32 | L802 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-03-01 | 1000 | 1000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 32 | L803 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-03-15 | 500 | 500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 32 | L806 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-04-01 | 1742 | 0 | 1742 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L808 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L809 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L811 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L813 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L815 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L817 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L819 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L821 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L823 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L825 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L827 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L829 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L831 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L833 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L835 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L837 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L839 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L841 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L843 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L845 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L847 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L849 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L851 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L853 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L855 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L857 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L859 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L861 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L863 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L865 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L867 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L869 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L871 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L873 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L875 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L877 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L879 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L881 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L883 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L885 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L887 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L889 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L891 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L893 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L895 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L897 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L899 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L901 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L903 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L905 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L907 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L909 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L911 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L913 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L915 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L917 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L919 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L921 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L923 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L925 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L927 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L928 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-03-01 | 5000 | 4971 | 29 | 0 | 0 | 0 | 0 | False | False | False | MNT | 6 |
| 33 | L929 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-03-01 | 5000 | 4913 | 87 | 0 | 0 | 0 | 0 | False | False | False | MNT | 3 |
| 33 | L933 | `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 2024-03-01 | 3297 | 0 | 3297 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L935 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5100 | 5100 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L936 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L938 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L940 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L942 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L944 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L946 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L948 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L950 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L952 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L954 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L956 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L958 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 57 | 0 | 57 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L960 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-13 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L962 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-14 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L964 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-15 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L966 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-16 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L968 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-17 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L970 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-18 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L972 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-19 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L974 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-20 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L976 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-21 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L978 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-22 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L980 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-23 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L982 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-24 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L984 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-25 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L986 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L988 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-27 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L990 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-28 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L992 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-29 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L994 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-30 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L996 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-31 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L998 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1000 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-02 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1002 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-03 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1004 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-04 | 57 | 0 | 57 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1006 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-05 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1008 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-06 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1010 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-07 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1012 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-08 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1014 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-09 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1016 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-10 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1018 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-11 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1020 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-12 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1022 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-13 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1024 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-14 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1026 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-15 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1028 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-16 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1030 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-17 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1032 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-18 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1034 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-19 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1036 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-20 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1038 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-21 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1040 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-22 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1042 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-23 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1044 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-24 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1046 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-25 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1048 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-26 | 57 | 0 | 57 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1050 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-27 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1052 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-28 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1054 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-29 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L1055 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-03-01 | 5100 | 5012 | 88 | 0 | 0 | 0 | 0 | False | False | False | MNT | 6 |
| 34 | L1056 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-03-01 | 5100 | 5004 | 88 | 8 | 0 | 0 | 0 | False | False | False | MNT | 3 |
| 34 | L1059 | `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 2024-03-01 | 3363 | 0 | 3363 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 35 | L1061 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 35 | L1064 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L1066 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L1069 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1071 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1072 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-02-01 | 3000 | 3000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1075 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-01 | 2000 | 0 | 2000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1077 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1080 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 1758 | 0 | 1758 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1082 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-03-02 | 5000 | 4999 | 1 | 0 | 0 | 0 | 0 | False | False | False | MNT | 3 |
| 38 | L1084 | `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 2024-03-02 | 1758 | 0 | 1758 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1086 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1087 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-02-01 | 3000 | 3000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1090 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 2000 | 0 | 2000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1092 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1093 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1096 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 4945 | 0 | 4945 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1098 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1099 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-01-01 | 4000 | 4000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1100 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 11 | 0 | 11 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1103 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 989 | 0 | 989 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1105 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1106 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1108 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1110 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1112 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1114 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1116 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1118 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1120 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1122 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1124 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1126 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1128 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1130 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1132 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1134 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1136 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1138 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1140 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1142 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1144 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1146 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1148 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1150 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1152 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1154 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1156 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1158 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1160 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1162 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1164 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1166 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1168 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1170 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1172 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1174 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1176 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1178 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1180 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1182 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1184 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1186 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1188 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1190 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1192 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1194 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1196 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1198 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1200 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1202 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1204 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1206 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1208 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1210 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1212 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1214 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1216 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1218 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1220 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1222 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1224 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1225 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-03-01 | 4000 | 4000 | 0 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 42 | L1227 | `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 2024-03-01 | 2297 | 0 | 2297 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1229 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-02 | 2407 | 0 | 2407 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1232 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-03-03 | 1593 | 0 | 1593 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1234 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1235 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1237 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1239 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1241 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1243 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1245 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1247 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1249 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1251 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1252 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-01-10 | 4000 | 4000 | 0 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 43 | L1254 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 6 | 0 | 6 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1256 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 103 | 0 | 103 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L1259 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 4396 | 0 | 4396 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1261 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 6000 | 6000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1262 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 66 | 0 | 66 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1264 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 66 | 0 | 66 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1266 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 66 | 0 | 66 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1268 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 66 | 0 | 66 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1270 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 66 | 0 | 66 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1272 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 66 | 0 | 66 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1274 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 66 | 0 | 66 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1276 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 65 | 0 | 65 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1278 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 66 | 0 | 66 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1279 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-01-10 | 5500 | 5475 | 25 | 0 | 0 | 0 | 0 | True | False | False | MNT | 6 |
| 44 | L1281 | `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 2024-01-10 | 93 | 0 | 93 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1283 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 225 | 0 | 225 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L1286 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 5275 | 0 | 5275 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L1288 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L1289 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 110 | 0 | 110 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L1291 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 110 | 0 | 110 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L1292 | `loanTransactionType.capitalizedIncomeAdjustment` | 2024-01-03 | 10000 | 9992 | 8 | 0 | 0 | 0 | 0 | True | False | False | MNT | 6 |
| 45 | L1294 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 110 | 0 | 110 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L1296 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 110 | 0 | 110 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L1299 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 9560 | 0 | 9560 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1301 | `loanTransactionType.capitalizedIncome` | 2024-01-01 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 46 | L1302 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1304 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1306 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1308 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1310 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1312 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1314 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1316 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1318 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1320 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1322 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1324 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1326 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1328 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1330 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1332 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1334 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1336 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1338 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1340 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1342 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1344 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1346 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1348 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1350 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1352 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1354 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1356 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1358 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1360 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1362 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1365 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1367 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1369 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1371 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1373 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1375 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1377 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1379 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1381 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1383 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1385 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1387 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1389 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1392 | `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 2024-02-14 | 2418 | 0 | 2418 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1394 | `loanTransactionType.capitalizedIncome` | 2024-02-16 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L1397 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-02-16 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 47 | L1399 | `loanTransactionType.capitalizedIncome` | 2024-01-05 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 47 | L1402 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-05 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 47 | L1404 | `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 2024-01-05 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 48 | L1407 | `loanTransactionType.capitalizedIncome` | 2024-01-05 | 10000 | 10000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 48 | L1408 | `loanTransactionType.capitalizedIncome` | 2024-01-10 | 15000 | 15000 | 0 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 48 | L1409 | `loanTransactionType.capitalizedIncome` | 2024-01-15 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 48 | L1412 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-15 | 45000 | 0 | 45000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 48 | L1415 | `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 2024-01-15 | 15000 | 0 | 15000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 49 | L1418 | `loanTransactionType.capitalizedIncome` | 2024-01-05 | 50000 | 50000 | 0 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 50 | L1424 | `loanTransactionType.capitalizedIncome` | 2024-01-10 | 20000 | 20000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 50 | L1427 | `loanTransactionType.capitalizedIncomeAmortization` | 2024-01-10 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |

## Per-loan currency, charge-off and fraud state

| loan | currency | fraud | non-reversed chargeOff transactions |
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
| 10 | MNT | False | - |
| 11 | MNT | False | - |
| 12 | MNT | False | - |
| 13 | MNT | False | - |
| 14 | MNT | False | - |
| 15 | MNT | False | - |
| 16 | MNT | False | - |
| 17 | MNT | False | - |
| 18 | MNT | False | - |
| 19 | MNT | False | - |
| 20 | MNT | False | - |
| 21 | MNT | False | - |
| 22 | MNT | False | - |
| 23 | MNT | False | - |
| 24 | MNT | True | L324@2024-01-26 |
| 25 | MNT | True | L331@2024-01-26 |
| 26 | MNT | True | L338@2024-01-26 |
| 27 | MNT | True | - |
| 28 | MNT | False | - |
| 29 | MNT | False | - |
| 30 | MNT | False | L783@2024-03-01 |
| 31 | MNT | False | - |
| 32 | MNT | False | - |
| 33 | MNT | False | - |
| 34 | MNT | False | - |
| 35 | MNT | False | - |
| 36 | MNT | False | - |
| 37 | MNT | False | - |
| 38 | MNT | False | - |
| 39 | MNT | False | - |
| 40 | MNT | False | - |
| 41 | MNT | False | - |
| 42 | MNT | False | - |
| 43 | MNT | False | - |
| 44 | MNT | False | - |
| 45 | MNT | False | - |
| 46 | MNT | False | - |
| 47 | MNT | False | - |
| 48 | MNT | False | - |
| 49 | MNT | False | - |
| 50 | MNT | False | - |

