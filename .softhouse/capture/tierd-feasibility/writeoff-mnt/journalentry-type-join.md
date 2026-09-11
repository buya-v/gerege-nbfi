# Journal-entry leg -> loan transaction TYPE join

Every `/journalentries` leg carries only `transactionId` = `L<loanTransactionId>`; the
transaction **type** comes only from the loan read-backs
(`loans/loan-<id>/loan-<id>-detail-associations-transactions-*.json`,
`transactions[].id -> transactions[].type.code`).  Amounts are integer minor units (MNT).

Legs joined: 64; unmatched: 0.

## `loanTransactionType.chargeOff` — Charge-off

loans: 4, 6, 7, 8, 9; transactions: L15, L21, L26, L30, L35, L36; legs: 33

| loan | tx | entry | account code | account name | amount (minor) | reversed |
| --- | --- | --- | --- | --- | --- | --- |
| 4 | L15 | CREDIT | 112601 | Loans Receivable | 100000 | False |
| 4 | L15 | CREDIT | 112603 | Interest/Fee Receivable | 14300 | False |
| 4 | L15 | DEBIT | 744007 | Credit Loss/Bad Debt | 100000 | False |
| 4 | L15 | DEBIT | 404001 | Interest Income Charge Off | 3000 | False |
| 4 | L15 | DEBIT | 404008 | Fee Charge Off | 11300 | False |
| 6 | L21 | CREDIT | 112601 | Loans Receivable | 100000 | False |
| 6 | L21 | CREDIT | 112603 | Interest/Fee Receivable | 1222 | False |
| 6 | L21 | DEBIT | 744007 | Credit Loss/Bad Debt | 100000 | False |
| 6 | L21 | DEBIT | 404001 | Interest Income Charge Off | 1222 | False |
| 7 | L26 | CREDIT | 112601 | Loans Receivable | 8357 | False |
| 7 | L26 | CREDIT | 112603 | Interest/Fee Receivable | 49 | False |
| 7 | L26 | DEBIT | 744007 | Credit Loss/Bad Debt | 8357 | False |
| 7 | L26 | DEBIT | 404001 | Interest Income Charge Off | 49 | False |
| 8 | L30 | CREDIT | 112601 | Loans Receivable | 10000 | False |
| 8 | L30 | CREDIT | 112603 | Interest/Fee Receivable | 61 | False |
| 8 | L30 | DEBIT | 744007 | Credit Loss/Bad Debt | 10000 | False |
| 8 | L30 | DEBIT | 404001 | Interest Income Charge Off | 61 | False |
| 8 | L30 | CREDIT | 112601 | Loans Receivable | 10000 | False |
| 8 | L30 | CREDIT | 112603 | Interest/Fee Receivable | 61 | False |
| 8 | L30 | DEBIT | 744007 | Credit Loss/Bad Debt | 10000 | False |
| 8 | L30 | DEBIT | 404001 | Interest Income Charge Off | 61 | False |
| 8 | L30 | DEBIT | 112601 | Loans Receivable | 10000 | False |
| 8 | L30 | DEBIT | 112603 | Interest/Fee Receivable | 61 | False |
| 8 | L30 | CREDIT | 744007 | Credit Loss/Bad Debt | 10000 | False |
| 8 | L30 | CREDIT | 404001 | Interest Income Charge Off | 61 | False |
| 9 | L35 | CREDIT | 112601 | Loans Receivable | 65000 | False |
| 9 | L35 | DEBIT | 744037 | Credit Loss/Bad Debt-Fraud | 65000 | False |
| 9 | L35 | CREDIT | 112601 | Loans Receivable | 65000 | False |
| 9 | L35 | DEBIT | 744037 | Credit Loss/Bad Debt-Fraud | 65000 | False |
| 9 | L35 | DEBIT | 112601 | Loans Receivable | 65000 | False |
| 9 | L35 | CREDIT | 744037 | Credit Loss/Bad Debt-Fraud | 65000 | False |
| 9 | L36 | CREDIT | 112601 | Loans Receivable | 75000 | False |
| 9 | L36 | DEBIT | 744037 | Credit Loss/Bad Debt-Fraud | 75000 | False |

## `loanTransactionType.disbursement` — Disbursement

loans: 4, 5; transactions: L13, L17; legs: 4

| loan | tx | entry | account code | account name | amount (minor) | reversed |
| --- | --- | --- | --- | --- | --- | --- |
| 4 | L13 | DEBIT | 112601 | Loans Receivable | 100000 | False |
| 4 | L13 | CREDIT | 145023 | Suspense/Clearing account | 100000 | False |
| 5 | L17 | DEBIT | 112601 | Loans Receivable | 100000 | False |
| 5 | L17 | CREDIT | 145023 | Suspense/Clearing account | 100000 | False |

## `loanTransactionType.writeOff` — Close (as written-off)

loans: 4, 5, 6, 7, 8, 9, 10, 11, 12; transactions: L16, L18, L22, L27, L31, L37, L39, L41, L43; legs: 27

| loan | tx | entry | account code | account name | amount (minor) | reversed |
| --- | --- | --- | --- | --- | --- | --- |
| 4 | L16 | CREDIT | 744007 | Credit Loss/Bad Debt | 100000 | False |
| 4 | L16 | CREDIT | 404001 | Interest Income Charge Off | 3000 | False |
| 4 | L16 | CREDIT | 404008 | Fee Charge Off | 11300 | False |
| 4 | L16 | DEBIT | e4 | Written off | 114300 | False |
| 5 | L18 | CREDIT | 112601 | Loans Receivable | 100000 | False |
| 5 | L18 | CREDIT | 112603 | Interest/Fee Receivable | 14300 | False |
| 5 | L18 | DEBIT | e4 | Written off | 114300 | False |
| 6 | L22 | CREDIT | 744007 | Credit Loss/Bad Debt | 100000 | False |
| 6 | L22 | CREDIT | 404001 | Interest Income Charge Off | 1222 | False |
| 6 | L22 | DEBIT | e4 | Written off | 101222 | False |
| 7 | L27 | CREDIT | 744007 | Credit Loss/Bad Debt | 8357 | False |
| 7 | L27 | CREDIT | 404001 | Interest Income Charge Off | 147 | False |
| 7 | L27 | DEBIT | e4 | Written off | 8504 | False |
| 8 | L31 | CREDIT | 112601 | Loans Receivable | 10000 | False |
| 8 | L31 | CREDIT | 112603 | Interest/Fee Receivable | 205 | False |
| 8 | L31 | DEBIT | e4 | Written off | 10205 | False |
| 9 | L37 | CREDIT | 744037 | Credit Loss/Bad Debt-Fraud | 75000 | False |
| 9 | L37 | DEBIT | e4 | Written off | 75000 | False |
| 10 | L39 | CREDIT | 112601 | Loans Receivable | 100000 | False |
| 10 | L39 | CREDIT | 112603 | Interest/Fee Receivable | 2513 | False |
| 10 | L39 | DEBIT | e4 | Written off | 102513 | False |
| 11 | L41 | CREDIT | 112601 | Loans Receivable | 100000 | False |
| 11 | L41 | CREDIT | 112603 | Interest/Fee Receivable | 2513 | False |
| 11 | L41 | DEBIT | 744007 | Credit Loss/Bad Debt | 102513 | False |
| 12 | L43 | CREDIT | 112601 | Loans Receivable | 100000 | False |
| 12 | L43 | CREDIT | 112603 | Interest/Fee Receivable | 2513 | False |
| 12 | L43 | DEBIT | e4 | Written off | 102513 | False |

## `writeOff` transactions with journal-entry legs

| loan | tx | date | amount (minor) | reverses a charge-off |
| --- | --- | --- | --- | --- |
| 4 | L16 | 2023-3-1 | 114300 | yes |
| 5 | L18 | 2023-3-1 | 114300 | no |
| 6 | L22 | 2024-3-1 | 101222 | yes |
| 7 | L27 | 2024-3-1 | 8504 | yes |
| 8 | L31 | 2024-2-3 | 10205 | no |
| 9 | L37 | 2024-2-3 | 75000 | yes |
| 10 | L39 | 2025-1-2 | 102513 | no |
| 11 | L41 | 2025-1-2 | 102513 | no |
| 12 | L43 | 2025-1-2 | 102513 | no |

## `writeOff` on a charged-off loan (the `:1616` branch)

Observed for 4 loans; each lists the loan, the `writeOff` transaction id and the legs that reverse the earlier charge-off (CREDIT to Credit Loss/Bad Debt, DEBIT to Written off).

### loan 4 — `writeOff` transaction `L16` — 2023-3-1 — 114300 minor

| entry | account code | account name | amount (minor) |
| --- | --- | --- | --- |
| CREDIT | 744007 | Credit Loss/Bad Debt | 100000 |
| CREDIT | 404001 | Interest Income Charge Off | 3000 |
| CREDIT | 404008 | Fee Charge Off | 11300 |
| DEBIT | e4 | Written off | 114300 |

### loan 6 — `writeOff` transaction `L22` — 2024-3-1 — 101222 minor

| entry | account code | account name | amount (minor) |
| --- | --- | --- | --- |
| CREDIT | 744007 | Credit Loss/Bad Debt | 100000 |
| CREDIT | 404001 | Interest Income Charge Off | 1222 |
| DEBIT | e4 | Written off | 101222 |

### loan 7 — `writeOff` transaction `L27` — 2024-3-1 — 8504 minor

| entry | account code | account name | amount (minor) |
| --- | --- | --- | --- |
| CREDIT | 744007 | Credit Loss/Bad Debt | 8357 |
| CREDIT | 404001 | Interest Income Charge Off | 147 |
| DEBIT | e4 | Written off | 8504 |

### loan 9 — `writeOff` transaction `L37` — 2024-2-3 — 75000 minor

| entry | account code | account name | amount (minor) |
| --- | --- | --- | --- |
| CREDIT | 744037 | Credit Loss/Bad Debt-Fraud | 75000 |
| DEBIT | e4 | Written off | 75000 |

