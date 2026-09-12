# Journal-entry type join — required charge-off arms (OH-TIERD26-DJ step 6)

853 swept legs across 7 transaction types; 152 legs unmatched to a read-back.

Charged-off rule: a leg's transaction is on a charged-off loan ONLY if the loan's LATEST read-back (highest manifest source_line) has `chargedOff=true` and lists a NON-REVERSED `chargeOff` transaction with a LOWER transaction id.  Charged-off latest = the loan `chargedOff` flag in its LATEST read-back.

## Type x charged-off -> legs -> loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.chargeOff` | 275 | 0 | - |
| `loanTransactionType.repayment` | 212 | 17 | 1, 12, 14, 28, 30, 37, 39 |
| `(unmapped)` | 152 | 0 | - |
| `loanTransactionType.accrual` | 102 | 2 | 13 |
| `loanTransactionType.disbursement` | 96 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 12 | 0 | - |
| `loanTransactionType.accrualAdjustment` | 4 | 2 | 28 |

## Target arms (required)

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.repayment` | True | 212 | 66 | 1, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47 | 17 | 1, 12, 14, 28, 30, 37, 39 | 195 | 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47 |
| `loanTransactionType.chargeOff` | True | 275 | 54 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48 | 0 | - | 275 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48 |
| `loanTransactionType.accrual` | True | 102 | 51 | 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48 | 2 | 13 | 100 | 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48 |
| `loanTransactionType.accrualAdjustment` | True | 4 | 2 | 12, 28 | 2 | 28 | 2 | 12 |
| `loanTransactionType.waiver` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.recoveryRepayment` | False | 0 | 0 | - | 0 | - | 0 | - |

**FINDING:** target type(s) with NO journal-entry legs at all: loanTransactionType.waiver, loanTransactionType.recoveryRepayment.  The arm was NOT exercised by this feature.

**FINDING:** chargeOff supplement (NOT a read-back): loan 4 tx L54, loan 6 tx L98, loan 17 tx L151, loan 42 tx L273.  For these loans the feature charged the loan off AFTER its last read-back, so the charge-off transaction id is in no read-back; the charge-off command response (`charge-off-response.json` `resourceId`) is the evidence and it is injected as the `chargeOff` transaction so the arm type is complete.  It is NOT used for the charged-off rule (which reads the latest read-back).

**FINDING:** undone charge-off(s): loan 3 L12 (listed as manuallyReversed/reversed in the LATEST read-back), loan 12 L125 (present in an earlier read-back, absent from the LATEST read-back), loan 13 L132 (present in an earlier read-back, absent from the LATEST read-back), loan 22 L177 (listed as manuallyReversed/reversed in the LATEST read-back), loan 23 L181 (listed as manuallyReversed/reversed in the LATEST read-back), loan 28 L204 (present in an earlier read-back, absent from the LATEST read-back), loan 29 L211 (present in an earlier read-back, absent from the LATEST read-back), loan 37 L249 (present in an earlier read-back, absent from the LATEST read-back), loan 38 L255 (present in an earlier read-back, absent from the LATEST read-back), loan 48 L303 (listed as manuallyReversed/reversed in the LATEST read-back).  Each is excluded from the charged-off dimension because it does not appear as a NON-REVERSED chargeOff in the loan's latest read-back; the evidence and the transactions posted before and after the undo are listed under `undone_chargeoffs` and in OWNER.md.

**FINDING:** (unmapped): 152 swept legs on 76 transactions have no read-back type: loan 4 (38 legs, L16-L53); that loan's chargeOff is L54; loan 6 (38 legs, L60-L97); that loan's chargeOff is L98.  These are postings made AFTER the loan read-backs were last captured (predominantly the daily accruals), so they cannot be typed from a read-back.  They are a join gap, reported as a finding; they are NOT missing required arms.

## Undone charge-offs

For each undone charge-off: the evidence it was undone, and the transactions the loan posted before and after it. An undone charge-off is EXCLUDED from the charged-off dimension.

### loan 3 — `L12` — listed as manuallyReversed/reversed in the LATEST read-back

- evidence: `loans/loan-3/loan-3-detail-associations-transactions-5.json` (manifest source_line 26528); ordering read-back `loans/loan-3/loan-3-detail-associations-transactions-5.json` (source_line 26528).
- transactions posted BEFORE the undo: L9 loanTransactionType.disbursement 25000, L10 loanTransactionType.accrual 7, L11 loanTransactionType.accrual 7
- the undone charge-off: `L12`
- transactions posted AFTER the undo: L13 loanTransactionType.accrual 14, L14 loanTransactionType.accrual 7

### loan 12 — `L125` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-12/loan-12-detail-associations-transactions-3.json` (manifest source_line 39646); ordering read-back `loans/loan-12/loan-12-detail-associations-transactions-5.json` (source_line 39795).
- transactions posted BEFORE the undo: L122 loanTransactionType.disbursement 10000, L123 loanTransactionType.repayment 1701, L124 loanTransactionType.accrual 154
- the undone charge-off: `L125`
- transactions posted AFTER the undo: L126 loanTransactionType.accrualAdjustment 9, L127 loanTransactionType.chargeOff 6743, L128 loanTransactionType.repayment 1701

### loan 13 — `L132` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-13/loan-13-detail-associations-transactions-3.json` (manifest source_line 41244); ordering read-back `loans/loan-13/loan-13-detail-associations-transactions-6.json` (source_line 41417).
- transactions posted BEFORE the undo: L129 loanTransactionType.disbursement 10000, L130 loanTransactionType.repayment 1701, L131 loanTransactionType.accrual 105
- the undone charge-off: `L132`
- transactions posted AFTER the undo: L133 loanTransactionType.chargeOff 10114, L134 loanTransactionType.accrual 9

### loan 22 — `L177` — listed as manuallyReversed/reversed in the LATEST read-back

- evidence: `loans/loan-22/loan-22-detail-associations-transactions-3.json` (manifest source_line 56160); ordering read-back `loans/loan-22/loan-22-detail-associations-transactions-3.json` (source_line 56160).
- transactions posted BEFORE the undo: L175 loanTransactionType.disbursement 10000, L176 loanTransactionType.accrual 85
- the undone charge-off: `L177`
- transactions posted AFTER the undo: _(none)_

### loan 23 — `L181` — listed as manuallyReversed/reversed in the LATEST read-back

- evidence: `loans/loan-23/loan-23-detail-associations-transactions-6.json` (manifest source_line 57813); ordering read-back `loans/loan-23/loan-23-detail-associations-transactions-6.json` (source_line 57813).
- transactions posted BEFORE the undo: L178 loanTransactionType.disbursement 10000, L179 loanTransactionType.repayment 1701, L180 loanTransactionType.accrual 107
- the undone charge-off: `L181`
- transactions posted AFTER the undo: _(none)_

### loan 28 — `L204` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-28/loan-28-detail-associations-transactions-5.json` (manifest source_line 66119); ordering read-back `loans/loan-28/loan-28-detail-associations-transactions-7.json` (source_line 66267).
- transactions posted BEFORE the undo: L201 loanTransactionType.disbursement 10000, L202 loanTransactionType.repayment 1701, L203 loanTransactionType.accrual 154
- the undone charge-off: `L204`
- transactions posted AFTER the undo: L205 loanTransactionType.chargeOff 6743, L206 loanTransactionType.accrualAdjustment 9, L207 loanTransactionType.repayment 1701

### loan 29 — `L211` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-29/loan-29-detail-associations-transactions-5.json` (manifest source_line 67927); ordering read-back `loans/loan-29/loan-29-detail-associations-transactions-7.json` (source_line 68076).
- transactions posted BEFORE the undo: L208 loanTransactionType.disbursement 10000, L209 loanTransactionType.repayment 1701, L210 loanTransactionType.accrual 105
- the undone charge-off: `L211`
- transactions posted AFTER the undo: L212 loanTransactionType.accrual 9, L213 loanTransactionType.chargeOff 10114

### loan 37 — `L249` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-37/loan-37-detail-associations-transactions-3.json` (manifest source_line 80572); ordering read-back `loans/loan-37/loan-37-detail-associations-transactions-5.json` (source_line 80721).
- transactions posted BEFORE the undo: L246 loanTransactionType.disbursement 10000, L247 loanTransactionType.repayment 1701, L248 loanTransactionType.accrual 145
- the undone charge-off: `L249`
- transactions posted AFTER the undo: L250 loanTransactionType.chargeOff 6743, L251 loanTransactionType.repayment 1701

### loan 38 — `L255` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-38/loan-38-detail-associations-transactions-3.json` (manifest source_line 82171); ordering read-back `loans/loan-38/loan-38-detail-associations-transactions-6.json` (source_line 82344).
- transactions posted BEFORE the undo: L252 loanTransactionType.disbursement 10000, L253 loanTransactionType.repayment 1701, L254 loanTransactionType.accrual 105
- the undone charge-off: `L255`
- transactions posted AFTER the undo: L256 loanTransactionType.chargeOff 10105

### loan 48 — `L303` — listed as manuallyReversed/reversed in the LATEST read-back

- evidence: `loans/loan-48/loan-48-detail-associations-transactions-3.json` (manifest source_line 98665); ordering read-back `loans/loan-48/loan-48-detail-associations-transactions-3.json` (source_line 98665).
- transactions posted BEFORE the undo: L301 loanTransactionType.disbursement 10000, L302 loanTransactionType.accrual 81
- the undone charge-off: `L303`
- transactions posted AFTER the undo: _(none)_

## Distinct leg shapes per required arm

### `loanTransactionType.repayment`

| shape (side:account) | account ids | transactions | loans | example (loan, tx, amount minor, portions, paymentType) |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:5 DEBIT:6` | 1, 5, 6 | 56 | 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 39, 40, 41, 42, 43, 44, 45, 46, 47 | loan 7 tx L100, amt 1701, portions {'principal_minor': '1643', 'interest_minor': '58', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 9/AUTOPAY |
| `CREDIT:15 DEBIT:6` | 6, 15 | 4 | 1, 14, 30, 39 | loan 1 tx L4, amt 50000, portions {'principal_minor': '31285', 'interest_minor': '2167', 'fee_minor': '10548', 'penalty_minor': '6000', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 9/AUTOPAY |
| `CREDIT:1 CREDIT:5 CREDIT:6 DEBIT:1 DEBIT:5 DEBIT:6` | 1, 5, 6 | 3 | 13, 29, 38 | loan 13 tx L130, amt 1701, portions {'principal_minor': '1643', 'interest_minor': '58', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 9/AUTOPAY |
| `CREDIT:1 CREDIT:5 CREDIT:6 CREDIT:17 DEBIT:1 DEBIT:5 DEBIT:6 DEBIT:17` | 1, 5, 6, 17 | 2 | 20, 45 | loan 20 tx L166, amt 2000, portions {'principal_minor': '1690', 'interest_minor': '10', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '300', 'unrecognized_income_minor': '0'}, payType 9/AUTOPAY |
| `CREDIT:5 DEBIT:6` | 5, 6 | 1 | 21 | loan 21 tx L172, amt 1701, portions {'principal_minor': '1701', 'interest_minor': '0', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType 9/AUTOPAY |

### `loanTransactionType.chargeOff`

| shape (side:account) | account ids | transactions | loans | example (loan, tx, amount minor, portions, paymentType) |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 CREDIT:5 DEBIT:13 DEBIT:19` | 1, 5, 13, 19 | 35 | 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17, 20, 21, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 42, 45, 46, 47 | loan 2 tx L8, amt 25523, portions {'principal_minor': '25000', 'interest_minor': '523', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |
| `CREDIT:1 CREDIT:5 CREDIT:13 CREDIT:19 DEBIT:1 DEBIT:5 DEBIT:13 DEBIT:19` | 1, 5, 13, 19 | 10 | 3, 12, 13, 22, 23, 28, 29, 37, 38, 48 | loan 3 tx L12, amt 25523, portions {'principal_minor': '25000', 'interest_minor': '523', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |
| `CREDIT:1 CREDIT:5 DEBIT:11 DEBIT:13 DEBIT:19` | 1, 5, 11, 13, 19 | 7 | 1, 15, 16, 18, 40, 41, 43 | loan 1 tx L3, amt 122023, portions {'principal_minor': '100000', 'interest_minor': '5475', 'fee_minor': '10548', 'penalty_minor': '6000', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |
| `CREDIT:1 CREDIT:5 CREDIT:11 CREDIT:13 CREDIT:19 DEBIT:1 DEBIT:5 DEBIT:11 DEBIT:13 DEBIT:19` | 1, 5, 11, 13, 19 | 2 | 17, 42 | loan 17 tx L151, amt 17408, portions {}, payType None/None |

### `loanTransactionType.accrual`

| shape (side:account) | account ids | transactions | loans | example (loan, tx, amount minor, portions, paymentType) |
| --- | --- | ---: | --- | --- |
| `CREDIT:7 DEBIT:1` | 1, 7 | 51 | 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48 | loan 1 tx L2, amt 3696, portions {'principal_minor': '0', 'interest_minor': '3696', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |

### `loanTransactionType.accrualAdjustment`

| shape (side:account) | account ids | transactions | loans | example (loan, tx, amount minor, portions, paymentType) |
| --- | --- | ---: | --- | --- |
| `CREDIT:1 DEBIT:7` | 1, 7 | 2 | 12, 28 | loan 12 tx L126, amt 9, portions {'principal_minor': '0', 'interest_minor': '9', 'fee_minor': '0', 'penalty_minor': '0', 'overpayment_minor': '0', 'unrecognized_income_minor': '0'}, payType None/None |

### `loanTransactionType.waiver`

_no legs._

### `loanTransactionType.recoveryRepayment`

_no legs._

