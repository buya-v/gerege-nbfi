# Journal-entry leg -> loan transaction TYPE join (sweep)

Every swept `/journalentries` leg carries only `transactionId` =
`L<loanTransactionId>`; the transaction **type** comes only from the loan
read-backs (`transactions[].id -> transactions[].type.code`).  Amounts are
integer minor units; the raw sweep bodies keep decimal major units.

Legs joined: 324; unmatched by read-back: 2.

**2 unmatched legs (1 transactions, loans 14)** carry no type in the read-backs;
their posting shape infers `unknown` (see the section at the end).

| type | value | loans | transactions | legs |
| --- | --- | --- | --- | --- |
| `loanTransactionType.accrual` | Accrual | 4, 7, 8, 9, 10, 11, 12, 13, 14, 15 | L13, L24, L27, L30, L31, L32, L33, L37, L40, L47, L74, L92, L111 | 26 |
| `loanTransactionType.chargeOff` | Charge-off | 10, 11, 12, 13, 14, 15 | L38, L41, L48, L75, L93, L112 | 24 |
| `loanTransactionType.disbursement` | Disbursement | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 | L1, L3, L5, L7, L14, L18, L22, L25, L29, L35, L39, L43, L62, L80, L99 | 30 |
| `loanTransactionType.goodwillCredit` | Goodwill Credit | 15 | L113 | 3 |
| `loanTransactionType.interestPaymentWaiver` | Interest Payment Waiver | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | L2, L4, L6, L12, L15, L19, L23, L28, L34, L36, L42, L49, L76 | 35 |
| `loanTransactionType.interestRefund` | Interest Refund | 12, 13, 14, 15 | L45, L63, L82, L94, L101 | 10 |
| `loanTransactionType.merchantIssuedRefund` | Merchant Issued Refund | 12, 13, 14, 15 | L44, L64, L81, L100 | 10 |
| `loanTransactionType.payoutRefund` | Payout Refund | 14 | L95 | 2 |
| `loanTransactionType.repayment` | Repayment | 4, 5, 6, 8, 12, 13, 14, 15 | L8, L9, L10, L11, L16, L17, L20, L21, L26, L46, L50, L65, L66, L67, L68, L69, L70, L71, L72, L73, L77, L83, L84, L85, L86, L87, L88, L89, L90, L91, L102, L103, L104, L105, L106, L107, L108, L109, L110 | 182 |
| `None` |  | 14 | L98 | 2 |

## `loanTransactionType.accrual` — Accrual

loans: 4, 7, 8, 9, 10, 11, 12, 13, 14, 15; transactions: L13, L24, L27, L30, L31, L32, L33, L37, L40, L47, L74, L92, L111; legs: 26

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | L13 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 4000 | MNT | False | False | False |
| 4 | L13 | CREDIT | 9 | 404000 | Interest Income | 4000 | MNT | False | False | False |
| 7 | L24 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 4000 | MNT | False | False | False |
| 7 | L24 | CREDIT | 9 | 404000 | Interest Income | 4000 | MNT | False | False | False |
| 8 | L27 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 4000 | MNT | False | False | False |
| 8 | L27 | CREDIT | 9 | 404000 | Interest Income | 4000 | MNT | False | False | False |
| 9 | L30 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 9 | L30 | CREDIT | 9 | 404000 | Interest Income | 1000 | MNT | False | False | False |
| 9 | L31 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 9 | L31 | CREDIT | 9 | 404000 | Interest Income | 1000 | MNT | False | False | False |
| 9 | L32 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 9 | L32 | CREDIT | 9 | 404000 | Interest Income | 1000 | MNT | False | False | False |
| 9 | L33 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 9 | L33 | CREDIT | 9 | 404000 | Interest Income | 1000 | MNT | False | False | False |
| 10 | L37 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 1034 | MNT | False | True | False |
| 10 | L37 | CREDIT | 9 | 404000 | Interest Income | 1034 | MNT | False | True | False |
| 11 | L40 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 452 | MNT | False | True | False |
| 11 | L40 | CREDIT | 9 | 404000 | Interest Income | 452 | MNT | False | True | False |
| 12 | L47 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 5699 | MNT | False | True | False |
| 12 | L47 | CREDIT | 9 | 404000 | Interest Income | 5699 | MNT | False | True | False |
| 13 | L74 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 452 | MNT | False | True | False |
| 13 | L74 | CREDIT | 9 | 404000 | Interest Income | 452 | MNT | False | True | False |
| 14 | L92 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 459 | MNT | False | True | False |
| 14 | L92 | CREDIT | 9 | 404000 | Interest Income | 459 | MNT | False | True | False |
| 15 | L111 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 458 | MNT | False | True | False |
| 15 | L111 | CREDIT | 9 | 404000 | Interest Income | 458 | MNT | False | True | False |

## `loanTransactionType.chargeOff` — Charge-off

loans: 10, 11, 12, 13, 14, 15; transactions: L38, L41, L48, L75, L93, L112; legs: 24

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | L38 | CREDIT | 2 | 112601 | Loans Receivable | 75000 | MNT | False | True | False |
| 10 | L38 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | True | False |
| 10 | L38 | DEBIT | 11 | 744007 | Credit Loss/Bad Debt | 75000 | MNT | False | True | False |
| 10 | L38 | DEBIT | 20 | 404001 | Interest Income Charge Off | 3000 | MNT | False | True | False |
| 11 | L41 | CREDIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | True | False |
| 11 | L41 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 4000 | MNT | False | True | False |
| 11 | L41 | DEBIT | 11 | 744007 | Credit Loss/Bad Debt | 100000 | MNT | False | True | False |
| 11 | L41 | DEBIT | 20 | 404001 | Interest Income Charge Off | 4000 | MNT | False | True | False |
| 12 | L48 | CREDIT | 2 | 112601 | Loans Receivable | 51300 | MNT | False | True | False |
| 12 | L48 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 2517 | MNT | False | True | False |
| 12 | L48 | DEBIT | 11 | 744007 | Credit Loss/Bad Debt | 51300 | MNT | False | True | False |
| 12 | L48 | DEBIT | 20 | 404001 | Interest Income Charge Off | 2517 | MNT | False | True | False |
| 13 | L75 | CREDIT | 2 | 112601 | Loans Receivable | 6220 | MNT | False | True | False |
| 13 | L75 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 428 | MNT | False | True | False |
| 13 | L75 | DEBIT | 11 | 744007 | Credit Loss/Bad Debt | 6220 | MNT | False | True | False |
| 13 | L75 | DEBIT | 20 | 404001 | Interest Income Charge Off | 428 | MNT | False | True | False |
| 14 | L93 | CREDIT | 2 | 112601 | Loans Receivable | 6307 | MNT | False | True | False |
| 14 | L93 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 435 | MNT | False | True | False |
| 14 | L93 | DEBIT | 11 | 744007 | Credit Loss/Bad Debt | 6307 | MNT | False | True | False |
| 14 | L93 | DEBIT | 20 | 404001 | Interest Income Charge Off | 435 | MNT | False | True | False |
| 15 | L112 | CREDIT | 2 | 112601 | Loans Receivable | 6307 | MNT | False | True | False |
| 15 | L112 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 347 | MNT | False | True | False |
| 15 | L112 | DEBIT | 11 | 744007 | Credit Loss/Bad Debt | 6307 | MNT | False | True | False |
| 15 | L112 | DEBIT | 20 | 404001 | Interest Income Charge Off | 347 | MNT | False | True | False |

## `loanTransactionType.disbursement` — Disbursement

loans: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15; transactions: L1, L3, L5, L7, L14, L18, L22, L25, L29, L35, L39, L43, L62, L80, L99; legs: 30

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | L1 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 1 | L1 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 2 | L3 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 2 | L3 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 3 | L5 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 3 | L5 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 4 | L7 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 4 | L7 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 5 | L14 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 5 | L14 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 6 | L18 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 6 | L18 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 7 | L22 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 7 | L22 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 8 | L25 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 8 | L25 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 9 | L29 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 9 | L29 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 10 | L35 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 10 | L35 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 11 | L39 | DEBIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 11 | L39 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 12 | L43 | DEBIT | 2 | 112601 | Loans Receivable | 67803 | MNT | False | False | False |
| 12 | L43 | CREDIT | 6 | 145023 | Suspense/Clearing account | 67803 | MNT | False | False | False |
| 13 | L62 | DEBIT | 2 | 112601 | Loans Receivable | 43198 | MNT | False | False | False |
| 13 | L62 | CREDIT | 6 | 145023 | Suspense/Clearing account | 43198 | MNT | False | False | False |
| 14 | L80 | DEBIT | 2 | 112601 | Loans Receivable | 43198 | MNT | False | False | False |
| 14 | L80 | CREDIT | 6 | 145023 | Suspense/Clearing account | 43198 | MNT | False | False | False |
| 15 | L99 | DEBIT | 2 | 112601 | Loans Receivable | 43198 | MNT | False | False | False |
| 15 | L99 | CREDIT | 6 | 145023 | Suspense/Clearing account | 43198 | MNT | False | False | False |

## `loanTransactionType.goodwillCredit` — Goodwill Credit

loans: 15; transactions: L113; legs: 3

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15 | L113 | CREDIT | 13 | 744008 | Recoveries | 6654 | MNT | False | True | False |
| 15 | L113 | DEBIT | 19 | 744003 | Goodwill Expense Account | 6307 | MNT | False | True | False |
| 15 | L113 | DEBIT | 20 | 404001 | Interest Income Charge Off | 347 | MNT | False | True | False |

## `loanTransactionType.interestPaymentWaiver` — Interest Payment Waiver

loans: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13; transactions: L2, L4, L6, L12, L15, L19, L23, L28, L34, L36, L42, L49, L76; legs: 35

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | L2 | CREDIT | 2 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 1 | L2 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 1 | L2 | DEBIT | 9 | 404000 | Interest Income | 26000 | MNT | False | False | False |
| 2 | L4 | CREDIT | 2 | 112601 | Loans Receivable | 1000 | MNT | False | False | False |
| 2 | L4 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 2 | L4 | DEBIT | 9 | 404000 | Interest Income | 4000 | MNT | False | False | False |
| 3 | L6 | CREDIT | 2 | 112601 | Loans Receivable | 1000 | MNT | False | False | False |
| 3 | L6 | DEBIT | 9 | 404000 | Interest Income | 1000 | MNT | False | False | False |
| 4 | L12 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 4 | L12 | CREDIT | 17 | l1 | Overpayment account | 1000 | MNT | False | False | False |
| 4 | L12 | DEBIT | 9 | 404000 | Interest Income | 2000 | MNT | False | False | False |
| 5 | L15 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 5 | L15 | DEBIT | 9 | 404000 | Interest Income | 1000 | MNT | False | False | False |
| 5 | L15 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 5 | L15 | CREDIT | 9 | 404000 | Interest Income | 1000 | MNT | False | False | False |
| 6 | L19 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 6 | L19 | DEBIT | 9 | 404000 | Interest Income | 1000 | MNT | False | False | False |
| 7 | L23 | CREDIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 7 | L23 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 4000 | MNT | False | False | False |
| 7 | L23 | CREDIT | 17 | l1 | Overpayment account | 6000 | MNT | False | False | False |
| 7 | L23 | DEBIT | 9 | 404000 | Interest Income | 110000 | MNT | False | False | False |
| 8 | L28 | CREDIT | 17 | l1 | Overpayment account | 10000 | MNT | False | False | False |
| 8 | L28 | DEBIT | 9 | 404000 | Interest Income | 10000 | MNT | False | False | False |
| 9 | L34 | CREDIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 9 | L34 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 4000 | MNT | False | False | False |
| 9 | L34 | DEBIT | 9 | 404000 | Interest Income | 104000 | MNT | False | False | False |
| 10 | L36 | CREDIT | 2 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 10 | L36 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 10 | L36 | DEBIT | 9 | 404000 | Interest Income | 26000 | MNT | False | False | False |
| 11 | L42 | CREDIT | 20 | 404001 | Interest Income Charge Off | 26000 | MNT | False | True | False |
| 11 | L42 | DEBIT | 9 | 404000 | Interest Income | 26000 | MNT | False | True | False |
| 12 | L49 | CREDIT | 20 | 404001 | Interest Income Charge Off | 4656 | MNT | False | True | False |
| 12 | L49 | DEBIT | 9 | 404000 | Interest Income | 4656 | MNT | False | True | False |
| 13 | L76 | CREDIT | 20 | 404001 | Interest Income Charge Off | 4656 | MNT | False | True | False |
| 13 | L76 | DEBIT | 9 | 404000 | Interest Income | 4656 | MNT | False | True | False |

## `loanTransactionType.interestRefund` — Interest Refund

loans: 12, 13, 14, 15; transactions: L45, L63, L82, L94, L101; legs: 10

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | L45 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 12 | L45 | DEBIT | 9 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 13 | L63 | CREDIT | 2 | 112601 | Loans Receivable | 20 | MNT | False | False | False |
| 13 | L63 | DEBIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 14 | L82 | CREDIT | 2 | 112601 | Loans Receivable | 20 | MNT | False | False | False |
| 14 | L82 | DEBIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 14 | L94 | CREDIT | 17 | l1 | Overpayment account | 459 | MNT | False | True | False |
| 14 | L94 | DEBIT | 9 | 404000 | Interest Income | 459 | MNT | False | True | False |
| 15 | L101 | CREDIT | 2 | 112601 | Loans Receivable | 20 | MNT | False | False | False |
| 15 | L101 | DEBIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |

## `loanTransactionType.merchantIssuedRefund` — Merchant Issued Refund

loans: 12, 13, 14, 15; transactions: L44, L64, L81, L100; legs: 10

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | L44 | CREDIT | 2 | 112601 | Loans Receivable | 1000 | MNT | False | False | False |
| 12 | L44 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 13 | L64 | CREDIT | 2 | 112601 | Loans Receivable | 34975 | MNT | False | False | False |
| 13 | L64 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 24 | MNT | False | False | False |
| 13 | L64 | DEBIT | 6 | 145023 | Suspense/Clearing account | 34999 | MNT | False | False | False |
| 14 | L81 | CREDIT | 2 | 112601 | Loans Receivable | 34975 | MNT | False | False | False |
| 14 | L81 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 24 | MNT | False | False | False |
| 14 | L81 | DEBIT | 6 | 145023 | Suspense/Clearing account | 34999 | MNT | False | False | False |
| 15 | L100 | CREDIT | 2 | 112601 | Loans Receivable | 34999 | MNT | False | False | False |
| 15 | L100 | DEBIT | 6 | 145023 | Suspense/Clearing account | 34999 | MNT | False | False | False |

## `loanTransactionType.payoutRefund` — Payout Refund

loans: 14; transactions: L95; legs: 2

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | L95 | CREDIT | 11 | 744007 | Credit Loss/Bad Debt | 6742 | MNT | False | True | False |
| 14 | L95 | DEBIT | 6 | 145023 | Suspense/Clearing account | 6742 | MNT | False | True | False |

## `loanTransactionType.repayment` — Repayment

loans: 4, 5, 6, 8, 12, 13, 14, 15; transactions: L8, L9, L10, L11, L16, L17, L20, L21, L26, L46, L50, L65, L66, L67, L68, L69, L70, L71, L72, L73, L77, L83, L84, L85, L86, L87, L88, L89, L90, L91, L102, L103, L104, L105, L106, L107, L108, L109, L110; legs: 182

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | L8 | CREDIT | 2 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 4 | L8 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 4 | L8 | DEBIT | 6 | 145023 | Suspense/Clearing account | 26000 | MNT | False | False | False |
| 4 | L9 | CREDIT | 2 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 4 | L9 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 4 | L9 | DEBIT | 6 | 145023 | Suspense/Clearing account | 26000 | MNT | False | False | False |
| 4 | L10 | CREDIT | 2 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 4 | L10 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 4 | L10 | DEBIT | 6 | 145023 | Suspense/Clearing account | 26000 | MNT | False | False | False |
| 4 | L11 | CREDIT | 2 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 4 | L11 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 5 | L16 | CREDIT | 2 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 5 | L16 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 5 | L16 | DEBIT | 2 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 5 | L16 | CREDIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 5 | L17 | CREDIT | 2 | 112601 | Loans Receivable | 24000 | MNT | False | False | False |
| 5 | L17 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 5 | L17 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 6 | L20 | CREDIT | 2 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 6 | L20 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 6 | L21 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 1000 | MNT | False | False | False |
| 6 | L21 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 8 | L26 | CREDIT | 2 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 8 | L26 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 4000 | MNT | False | False | False |
| 8 | L26 | DEBIT | 6 | 145023 | Suspense/Clearing account | 104000 | MNT | False | False | False |
| 12 | L46 | CREDIT | 2 | 112601 | Loans Receivable | 15503 | MNT | False | False | False |
| 12 | L46 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 3181 | MNT | False | False | False |
| 12 | L46 | DEBIT | 6 | 145023 | Suspense/Clearing account | 18684 | MNT | False | False | False |
| 12 | L50 | CREDIT | 13 | 744008 | Recoveries | 49161 | MNT | False | True | False |
| 12 | L50 | DEBIT | 6 | 145023 | Suspense/Clearing account | 49161 | MNT | False | True | False |
| 13 | L65 | CREDIT | 2 | 112601 | Loans Receivable | 1983 | MNT | False | False | False |
| 13 | L65 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L65 | DEBIT | 2 | 112601 | Loans Receivable | 1983 | MNT | False | False | False |
| 13 | L65 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L66 | CREDIT | 2 | 112601 | Loans Receivable | 1983 | MNT | False | False | False |
| 13 | L66 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L67 | CREDIT | 2 | 112601 | Loans Receivable | 1865 | MNT | False | False | False |
| 13 | L67 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 118 | MNT | False | False | False |
| 13 | L67 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L67 | DEBIT | 2 | 112601 | Loans Receivable | 1865 | MNT | False | False | False |
| 13 | L67 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 118 | MNT | False | False | False |
| 13 | L67 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L68 | CREDIT | 2 | 112601 | Loans Receivable | 1843 | MNT | False | False | False |
| 13 | L68 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 140 | MNT | False | False | False |
| 13 | L68 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L68 | DEBIT | 2 | 112601 | Loans Receivable | 1843 | MNT | False | False | False |
| 13 | L68 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 140 | MNT | False | False | False |
| 13 | L68 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L69 | CREDIT | 2 | 112601 | Loans Receivable | 1812 | MNT | False | False | False |
| 13 | L69 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 171 | MNT | False | False | False |
| 13 | L69 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L69 | DEBIT | 2 | 112601 | Loans Receivable | 1812 | MNT | False | False | False |
| 13 | L69 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 171 | MNT | False | False | False |
| 13 | L69 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L70 | CREDIT | 2 | 112601 | Loans Receivable | 1761 | MNT | False | False | False |
| 13 | L70 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 222 | MNT | False | False | False |
| 13 | L70 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L70 | DEBIT | 2 | 112601 | Loans Receivable | 1761 | MNT | False | False | False |
| 13 | L70 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 222 | MNT | False | False | False |
| 13 | L70 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L71 | CREDIT | 2 | 112601 | Loans Receivable | 1708 | MNT | False | False | False |
| 13 | L71 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 275 | MNT | False | False | False |
| 13 | L71 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L71 | DEBIT | 2 | 112601 | Loans Receivable | 1708 | MNT | False | False | False |
| 13 | L71 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 275 | MNT | False | False | False |
| 13 | L71 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L72 | CREDIT | 2 | 112601 | Loans Receivable | 1657 | MNT | False | False | False |
| 13 | L72 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 326 | MNT | False | False | False |
| 13 | L72 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L72 | DEBIT | 2 | 112601 | Loans Receivable | 1657 | MNT | False | False | False |
| 13 | L72 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 326 | MNT | False | False | False |
| 13 | L72 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L73 | CREDIT | 2 | 112601 | Loans Receivable | 1604 | MNT | False | False | False |
| 13 | L73 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 379 | MNT | False | False | False |
| 13 | L73 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L73 | DEBIT | 2 | 112601 | Loans Receivable | 1604 | MNT | False | False | False |
| 13 | L73 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 379 | MNT | False | False | False |
| 13 | L73 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 13 | L77 | CREDIT | 13 | 744008 | Recoveries | 1992 | MNT | False | True | False |
| 13 | L77 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1992 | MNT | False | True | False |
| 14 | L83 | CREDIT | 2 | 112601 | Loans Receivable | 1918 | MNT | False | False | False |
| 14 | L83 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 65 | MNT | False | False | False |
| 14 | L83 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L83 | DEBIT | 2 | 112601 | Loans Receivable | 1918 | MNT | False | False | False |
| 14 | L83 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 65 | MNT | False | False | False |
| 14 | L83 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L84 | CREDIT | 2 | 112601 | Loans Receivable | 1896 | MNT | False | False | False |
| 14 | L84 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 87 | MNT | False | False | False |
| 14 | L84 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L85 | CREDIT | 2 | 112601 | Loans Receivable | 1951 | MNT | False | False | False |
| 14 | L85 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 32 | MNT | False | False | False |
| 14 | L85 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L85 | DEBIT | 2 | 112601 | Loans Receivable | 1951 | MNT | False | False | False |
| 14 | L85 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 32 | MNT | False | False | False |
| 14 | L85 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L86 | CREDIT | 2 | 112601 | Loans Receivable | 1929 | MNT | False | False | False |
| 14 | L86 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 54 | MNT | False | False | False |
| 14 | L86 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L86 | DEBIT | 2 | 112601 | Loans Receivable | 1929 | MNT | False | False | False |
| 14 | L86 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 54 | MNT | False | False | False |
| 14 | L86 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L87 | CREDIT | 2 | 112601 | Loans Receivable | 1897 | MNT | False | False | False |
| 14 | L87 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 86 | MNT | False | False | False |
| 14 | L87 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L87 | DEBIT | 2 | 112601 | Loans Receivable | 1897 | MNT | False | False | False |
| 14 | L87 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 86 | MNT | False | False | False |
| 14 | L87 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L88 | CREDIT | 2 | 112601 | Loans Receivable | 1845 | MNT | False | False | False |
| 14 | L88 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 138 | MNT | False | False | False |
| 14 | L88 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L88 | DEBIT | 2 | 112601 | Loans Receivable | 1845 | MNT | False | False | False |
| 14 | L88 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 138 | MNT | False | False | False |
| 14 | L88 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L89 | CREDIT | 2 | 112601 | Loans Receivable | 1791 | MNT | False | False | False |
| 14 | L89 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 192 | MNT | False | False | False |
| 14 | L89 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L89 | DEBIT | 2 | 112601 | Loans Receivable | 1791 | MNT | False | False | False |
| 14 | L89 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 192 | MNT | False | False | False |
| 14 | L89 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L90 | CREDIT | 2 | 112601 | Loans Receivable | 1739 | MNT | False | False | False |
| 14 | L90 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 244 | MNT | False | False | False |
| 14 | L90 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L90 | DEBIT | 2 | 112601 | Loans Receivable | 1739 | MNT | False | False | False |
| 14 | L90 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 244 | MNT | False | False | False |
| 14 | L90 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L91 | CREDIT | 2 | 112601 | Loans Receivable | 1685 | MNT | False | False | False |
| 14 | L91 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 298 | MNT | False | False | False |
| 14 | L91 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 14 | L91 | DEBIT | 2 | 112601 | Loans Receivable | 1685 | MNT | False | False | False |
| 14 | L91 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 298 | MNT | False | False | False |
| 14 | L91 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L102 | CREDIT | 2 | 112601 | Loans Receivable | 1894 | MNT | False | False | False |
| 15 | L102 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 89 | MNT | False | False | False |
| 15 | L102 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L102 | DEBIT | 2 | 112601 | Loans Receivable | 1894 | MNT | False | False | False |
| 15 | L102 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 89 | MNT | False | False | False |
| 15 | L102 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L103 | CREDIT | 2 | 112601 | Loans Receivable | 1872 | MNT | False | False | False |
| 15 | L103 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 111 | MNT | False | False | False |
| 15 | L103 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L104 | CREDIT | 2 | 112601 | Loans Receivable | 1952 | MNT | False | False | False |
| 15 | L104 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 31 | MNT | False | False | False |
| 15 | L104 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L104 | DEBIT | 2 | 112601 | Loans Receivable | 1952 | MNT | False | False | False |
| 15 | L104 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 31 | MNT | False | False | False |
| 15 | L104 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L105 | CREDIT | 2 | 112601 | Loans Receivable | 1930 | MNT | False | False | False |
| 15 | L105 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 53 | MNT | False | False | False |
| 15 | L105 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L105 | DEBIT | 2 | 112601 | Loans Receivable | 1930 | MNT | False | False | False |
| 15 | L105 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 53 | MNT | False | False | False |
| 15 | L105 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L106 | CREDIT | 2 | 112601 | Loans Receivable | 1898 | MNT | False | False | False |
| 15 | L106 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 85 | MNT | False | False | False |
| 15 | L106 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L106 | DEBIT | 2 | 112601 | Loans Receivable | 1898 | MNT | False | False | False |
| 15 | L106 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 85 | MNT | False | False | False |
| 15 | L106 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L107 | CREDIT | 2 | 112601 | Loans Receivable | 1846 | MNT | False | False | False |
| 15 | L107 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 137 | MNT | False | False | False |
| 15 | L107 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L107 | DEBIT | 2 | 112601 | Loans Receivable | 1846 | MNT | False | False | False |
| 15 | L107 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 137 | MNT | False | False | False |
| 15 | L107 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L108 | CREDIT | 2 | 112601 | Loans Receivable | 1846 | MNT | False | False | False |
| 15 | L108 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 137 | MNT | False | False | False |
| 15 | L108 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L108 | DEBIT | 2 | 112601 | Loans Receivable | 1846 | MNT | False | False | False |
| 15 | L108 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 137 | MNT | False | False | False |
| 15 | L108 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L109 | CREDIT | 2 | 112601 | Loans Receivable | 1846 | MNT | False | False | False |
| 15 | L109 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 137 | MNT | False | False | False |
| 15 | L109 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L109 | DEBIT | 2 | 112601 | Loans Receivable | 1846 | MNT | False | False | False |
| 15 | L109 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 137 | MNT | False | False | False |
| 15 | L109 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L110 | CREDIT | 2 | 112601 | Loans Receivable | 1846 | MNT | False | False | False |
| 15 | L110 | CREDIT | 4 | 112603 | Interest/Fee Receivable | 137 | MNT | False | False | False |
| 15 | L110 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |
| 15 | L110 | DEBIT | 2 | 112601 | Loans Receivable | 1846 | MNT | False | False | False |
| 15 | L110 | DEBIT | 4 | 112603 | Interest/Fee Receivable | 137 | MNT | False | False | False |
| 15 | L110 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1983 | MNT | False | False | False |

## `None`

loans: 14; transactions: L98; legs: 2

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | L98 | DEBIT | 17 | l1 | Overpayment account | 459 | MNT | False | True | False |
| 14 | L98 | CREDIT | 6 | 145023 | Suspense/Clearing account | 459 | MNT | False | True | False |

## Type x charged-off -- refund / goodwill arms (OH-TIERD13-CI step 6)

Charged-off rule: a NON-REVERSED chargeOff loan transaction dated on or before the leg transaction date.

| type | present | legs | loans | legs on charged-off loan | loans on charged-off |
| --- | --- | ---: | --- | ---: | --- |
| `loanTransactionType.merchantIssuedRefund` | True | 10 | 12, 13, 14, 15 | 0 | - |
| `loanTransactionType.payoutRefund` | True | 2 | 14 | 2 | 14 |
| `loanTransactionType.goodwillCredit` | True | 3 | 15 | 3 | 15 |

### Legs on a CHARGED-OFF loan -- required listing

| type | loan | tx | entry | account id | account name | amount (minor) | fraud | currency |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `loanTransactionType.payoutRefund` | 14 | L95 | CREDIT | 11 | Credit Loss/Bad Debt | 6742 | False | MNT |
| `loanTransactionType.payoutRefund` | 14 | L95 | DEBIT | 6 | Suspense/Clearing account | 6742 | False | MNT |
| `loanTransactionType.goodwillCredit` | 15 | L113 | CREDIT | 13 | Recoveries | 6654 | False | MNT |
| `loanTransactionType.goodwillCredit` | 15 | L113 | DEBIT | 19 | Goodwill Expense Account | 6307 | False | MNT |
| `loanTransactionType.goodwillCredit` | 15 | L113 | DEBIT | 20 | Interest Income Charge Off | 347 | False | MNT |

### Per-loan charge-off / fraud state

| loan | currency | fraud | non-reversed chargeOff transactions |
| --- | --- | --- | --- |
| 1 | MNT | False | - |
| 2 | MNT | False | - |
| 3 | MNT | False | - |
| 4 | MNT | False | - |
| 5 | MNT | False | - |
| 6 | MNT | False | - |
| 7 | MNT | False | - |
| 8 | MNT | False | - |
| 9 | MNT | False | - |
| 10 | MNT | False | L38@2024-02-02 |
| 11 | MNT | False | L41@2024-01-15 |
| 12 | MNT | False | L48@2022-09-24 |
| 13 | MNT | False | L75@2022-09-16 |
| 14 | MNT | False | L93@2022-09-16 |
| 15 | MNT | False | L112@2022-09-16 |

## Unmatched legs -- inferred classification (NOT a read-back type)

1 transactions / 2 legs on loans 14 have no entry in any `transactions`
read-back.  Reason: net-zero 4-leg interest accrual + exact reversal; loan transaction absent from every `transactions` read-back (superseded/reverted by the accrual-activity replay).  Type inferred from posting shape, NOT confirmed by read-back.

Inferred type: unknown

| loan | tx | legs | accounts | net-zero | inferred type |
| --- | --- | ---: | --- | --- | --- |
| 14 | L98 | 2 | 6, 17 | True | `None` |

