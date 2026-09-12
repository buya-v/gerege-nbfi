# Journal-entry type join — required charge-off arms (OH-TIERD23-DC step 6)

800 swept legs across 9 transaction types; 370 legs unmatched to a read-back.

Charged-off rule: a NON-REVERSED chargeOff loan transaction with a LOWER transaction id than the leg's transaction.  Charged-off latest = the loan `chargedOff` flag in its LATEST read-back.

## Type x charged-off -> legs -> loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `(unmapped)` | 370 | 0 | - |
| `loanTransactionType.chargeOff` | 107 | 24 | 1, 2, 3, 4, 5 |
| `loanTransactionType.merchantIssuedRefund` | 87 | 39 | 1, 2, 3, 4, 5 |
| `loanTransactionType.repayment` | 76 | 16 | 4, 5, 6, 7, 8, 13 |
| `loanTransactionType.accrual` | 56 | 2 | 4 |
| `loanTransactionType.disbursement` | 44 | 0 | - |
| `loanTransactionType.interestRefund` | 36 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 14 | 0 | - |
| `loanTransactionType.accrualAdjustment` | 10 | 10 | 4, 5, 6, 7 |

## Target arms (required)

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.interestRefund` | True | 36 | 16 | 9, 10, 13, 14 | 0 | - | 36 | 9, 10, 13, 14 |
| `loanTransactionType.merchantIssuedRefund` | True | 87 | 24 | 1, 2, 3, 4, 5, 9, 10, 13, 14 | 39 | 1, 2, 3, 4, 5 | 48 | 9, 10, 13, 14 |
| `loanTransactionType.payoutRefund` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.repayment` | True | 76 | 22 | 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14 | 16 | 4, 5, 6, 7, 8, 13 | 60 | 1, 2, 3, 6, 7, 11, 12, 13, 14 |
| `loanTransactionType.accrualAdjustment` | True | 10 | 5 | 4, 5, 6, 7 | 10 | 4, 5, 6, 7 | 0 | - |
| `loanTransactionType.chargeOff` | True | 107 | 19 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 | 24 | 1, 2, 3, 4, 5 | 83 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 |

**FINDING:** target type(s) with NO journal-entry legs at all: loanTransactionType.payoutRefund.  The arm was NOT exercised by this feature.

**FINDING:** chargeOff supplement (NOT a read-back): loan 9 tx L179, loan 10 tx L296, loan 12 tx L317.  For these loans the feature charged the loan off AFTER its last read-back, so the charge-off transaction id is in no read-back; the charge-off command response (`charge-off-response.json` `resourceId`) is the evidence and it is injected as the `chargeOff` transaction so the arm is complete.  The charge-off is non-reversed (no reversal transaction/command is captured for these loans).

**FINDING:** (unmapped): 370 swept legs on 185 transactions have no read-back type: loan 9 (92 legs, L84-L107, L109-L138, L140-L170, L172-L178); that loan's chargeOff is L179; loan 10 (92 legs, L201-L224, L226-L255, L257-L287, L289-L295); that loan's chargeOff is L296; loan 12 (1 legs, L316); that loan's chargeOff is L317.  These are postings made AFTER the loan read-backs were last captured (predominantly the daily accruals), so they cannot be typed from a read-back.  They are a join gap, reported as a finding; they are NOT missing required arms.

## Distinct leg shapes per required arm

### `loanTransactionType.interestRefund`

| shape (side:account) | account ids | transactions | loans | example (loan, tx, amount minor, portions, paymentType) |
| --- | --- | ---: | --- | --- |
| `CREDIT:2 DEBIT:5` | 2, 5 | 10 | 9, 10 | loan 9 tx L67, amt 24, portions {'principal_minor': '0', 'interest_minor': '24', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |
| `CREDIT:1 DEBIT:5` | 1, 5 | 2 | 14 | loan 14 tx L339, amt 44, portions {'principal_minor': '44', 'interest_minor': '0', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |
| `CREDIT:16 DEBIT:5` | 5, 16 | 2 | 13, 14 | loan 13 tx L328, amt 145, portions {'principal_minor': '0', 'interest_minor': '0', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '145', 'unrecognized_income_minor': '0'}, payType None/None |
| `CREDIT:5 CREDIT:16 DEBIT:5 DEBIT:16` | 5, 16 | 2 | 13, 14 | loan 13 tx L320, amt 144, portions {'principal_minor': '0', 'interest_minor': '0', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '144', 'unrecognized_income_minor': '0'}, payType None/None |

### `loanTransactionType.merchantIssuedRefund`

| shape (side:account) | account ids | transactions | loans | example (loan, tx, amount minor, portions, paymentType) |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 DEBIT:8` | 1, 8 | 12 | 9, 10, 14 | loan 9 tx L68, amt 6119, portions {'principal_minor': '6119', 'interest_minor': '0', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |
| `CREDIT:1 CREDIT:2 CREDIT:16 DEBIT:8` | 1, 2, 8, 16 | 3 | 4, 13, 14 | loan 4 tx L28, amt 50000, portions {'principal_minor': '977', 'interest_minor': '49', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '48974', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |
| `CREDIT:8 CREDIT:12 CREDIT:16 CREDIT:20 DEBIT:8 DEBIT:12 DEBIT:16 DEBIT:20` | 8, 12, 16, 20 | 3 | 1, 2, 3 | loan 1 tx L5, amt 90000, portions {'principal_minor': '80000', 'interest_minor': '1875', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '8125', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |
| `CREDIT:1 CREDIT:2 CREDIT:8 CREDIT:16 DEBIT:1 DEBIT:2 DEBIT:8 DEBIT:16` | 1, 2, 8, 16 | 2 | 13, 14 | loan 13 tx L321, amt 14500, portions {'principal_minor': '12216', 'interest_minor': '45', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '2239', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |
| `CREDIT:12 CREDIT:20 DEBIT:8` | 8, 12, 20 | 2 | 1, 2 | loan 1 tx L7, amt 90000, portions {'principal_minor': '88310', 'interest_minor': '1690', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |
| `CREDIT:1 CREDIT:16 DEBIT:8` | 1, 8, 16 | 1 | 5 | loan 5 tx L36, amt 50000, portions {'principal_minor': '311', 'interest_minor': '0', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '49689', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |
| `CREDIT:12 DEBIT:8` | 8, 12 | 1 | 3 | loan 3 tx L21, amt 90000, portions {'principal_minor': '90000', 'interest_minor': '0', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |

### `loanTransactionType.payoutRefund`

_no legs._

### `loanTransactionType.repayment`

| shape (side:account) | account ids | transactions | loans | example (loan, tx, amount minor, portions, paymentType) |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:2 DEBIT:8` | 1, 2, 8 | 14 | 4, 5, 6, 7, 11, 12, 14 | loan 4 tx L26, amt 50000, portions {'principal_minor': '49023', 'interest_minor': '977', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |
| `CREDIT:1 CREDIT:2 CREDIT:8 DEBIT:1 DEBIT:2 DEBIT:8` | 1, 2, 8 | 3 | 13, 14 | loan 13 tx L319, amt 600, portions {'principal_minor': '501', 'interest_minor': '99', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |
| `CREDIT:1 CREDIT:8 DEBIT:1 DEBIT:8` | 1, 8 | 3 | 1, 2, 3 | loan 1 tx L2, amt 10000, portions {'principal_minor': '10000', 'interest_minor': '0', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |
| `CREDIT:11 DEBIT:8` | 8, 11 | 2 | 8, 13 | loan 8 tx L61, amt 114248, portions {'principal_minor': '100000', 'interest_minor': '14248', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 10/AUTOPAY |

### `loanTransactionType.accrualAdjustment`

| shape (side:account) | account ids | transactions | loans | example (loan, tx, amount minor, portions, paymentType) |
| --- | --- | ---: | --- | --- |
| `CREDIT:2 DEBIT:5` | 2, 5 | 5 | 4, 5, 6, 7 | loan 4 tx L25, amt 24, portions {'principal_minor': '0', 'interest_minor': '24', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |

### `loanTransactionType.chargeOff`

| shape (side:account) | account ids | transactions | loans | example (loan, tx, amount minor, portions, paymentType) |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:2 CREDIT:12 CREDIT:20 DEBIT:1 DEBIT:2 DEBIT:12 DEBIT:20` | 1, 2, 12, 20 | 8 | 1, 2, 3, 4, 5, 6, 7 | loan 1 tx L4, amt 81875, portions {'principal_minor': '80000', 'interest_minor': '1875', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |
| `CREDIT:1 CREDIT:2 DEBIT:12 DEBIT:20` | 1, 2, 12, 20 | 8 | 1, 2, 3, 8, 9, 11, 12, 14 | loan 1 tx L6, amt 91875, portions {'principal_minor': '90000', 'interest_minor': '1875', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |
| `CREDIT:1 CREDIT:12 DEBIT:1 DEBIT:12` | 1, 12 | 1 | 4 | loan 4 tx L27, amt 977, portions {'principal_minor': '977', 'interest_minor': '0', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |
| `CREDIT:1 CREDIT:2 DEBIT:12 DEBIT:13 DEBIT:20` | 1, 2, 12, 13, 20 | 1 | 10 | loan 10 tx L296, amt 27224, portions {}, payType None/None |
| `CREDIT:1 DEBIT:12` | 1, 12 | 1 | 13 | loan 13 tx L334, amt 600, portions {'principal_minor': '600', 'interest_minor': '0', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |

