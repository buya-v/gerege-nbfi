# Journal-entry type join — required payout-refund arms (OH-TIERD24-DE step 6)

89 swept legs across 4 transaction types; 0 legs unmatched to a read-back.

Charged-off rule: the loan's LATEST read-back (highest index) lists a NON-REVERSED chargeOff transaction with a LOWER transaction id than the leg's transaction AND its `chargedOff` is true.  Charged-off latest = the loan `chargedOff` flag in its LATEST read-back.

## Type x charged-off -> legs -> loans (every type)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 33 | 0 | - |
| `loanTransactionType.payoutRefund` | 22 | 0 | - |
| `loanTransactionType.disbursement` | 18 | 0 | - |
| `loanTransactionType.interestRefund` | 16 | 0 | - |

## Target arms (required)

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.payoutRefund` | True | 22 | 8 | 1, 2, 3, 4, 5, 6, 7, 8 | 0 | - | 22 | 1, 2, 3, 4, 5, 6, 7, 8 |
| `loanTransactionType.interestRefund` | True | 16 | 6 | 2, 3, 4, 5, 6, 7 | 0 | - | 16 | 2, 3, 4, 5, 6, 7 |
| `loanTransactionType.merchantIssuedRefund` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.repayment` | True | 33 | 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 0 | - | 33 | 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| `loanTransactionType.accrualAdjustment` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.chargeOff` | False | 0 | 0 | - | 0 | - | 0 | - |

**FINDING:** target type(s) with NO journal-entry legs at all: loanTransactionType.merchantIssuedRefund, loanTransactionType.accrualAdjustment, loanTransactionType.chargeOff.  The arm was NOT exercised by this feature.

**FINDING:** no non-reversed `chargeOff` loan transaction appears in ANY read-back: no leg is on a charged-off loan.

**FINDING:** no loan's LATEST read-back has `chargedOff=true`: the charged-off dimension is empty (every leg charged-off=no).

## Distinct leg shapes per required arm

### `loanTransactionType.payoutRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:3 DEBIT:9` | 3, 9 | 5 | 1, 2, 3, 5, 7 | loan 1 tx L3 |
| `CREDIT:3 CREDIT:9 DEBIT:3 DEBIT:9` | 3, 9 | 3 | 4, 6, 8 | loan 4 tx L13 |

### `loanTransactionType.interestRefund`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:4 DEBIT:7` | 4, 7 | 4 | 2, 3, 5, 7 | loan 2 tx L7 |
| `CREDIT:4 CREDIT:7 DEBIT:4 DEBIT:7` | 4, 7 | 2 | 4, 6 | loan 4 tx L14 |

### `loanTransactionType.merchantIssuedRefund`

_no legs._

### `loanTransactionType.repayment`

| shape (side:account) | account ids | transactions | loans | example |
| --- | --- | ---: | --- | --- |
| `CREDIT:3 CREDIT:4 DEBIT:9` | 3, 4, 9 | 9 | 1, 2, 3, 4, 5, 6, 7, 8, 9 | loan 1 tx L2 |
| `CREDIT:3 CREDIT:4 CREDIT:9 DEBIT:3 DEBIT:4 DEBIT:9` | 3, 4, 9 | 1 | 4 | loan 4 tx L15 |

### `loanTransactionType.accrualAdjustment`

_no legs._

### `loanTransactionType.chargeOff`

_no legs._

