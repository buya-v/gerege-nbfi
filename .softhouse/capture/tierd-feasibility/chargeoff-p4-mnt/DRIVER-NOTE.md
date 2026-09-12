# Driver note — the charged-off column of OWNER.md / journalentry-type-join.md is WRONG for loans 4-7

Written by the driver at merge time (12 Sep 2026). The capture bodies, manifests and teardown are sound; only the
run's CHARGED-OFF classification is corrected here. Do not cite the run's "legs on charged-off loan" figures for
merchantIssuedRefund or repayment.

## What the run claimed
merchantIssuedRefund on charged-off loans: 39 legs on loans 1, 2, 3, 4, 5. repayment on charged-off loans: 16 legs on
loans 4, 5, 6, 7, 8, 13.

## What the ledger shows
The product accounts (same in all 10 products): loanPortfolio 1, receivableInterest 2, fundSource 8, incomeFromRecovery
11, chargeOffExpense 12, incomeFromChargeOffFees 13, overpayment 16, chargeOffFraudExpense 19,
incomeFromChargeOffInterest 20. A posting made while the loan was charged off credits the charge-off accounts
(12/13/20) or recovery (11); a posting on a loan not charged off credits the portfolio 1 and the receivable 2.

| loan | charge-offs seen (ids) | latest read-back chargedOff | leg shapes (sweep) | verdict |
| --- | --- | --- | --- | --- |
| 1, 2, 3 | 4/6, 11/13, 18/20 | true | MIR L7, L14, L21: C12 C20 D8 (L21: C12 D8) | charged off — agrees |
| 4 | 24, 27 | **false** | repayment L26: C1 C2 D8; MIR L28: C1 C2 C16 D8 | **NOT charged off** |
| 5 | 32, 35 | **false** | repayment L33: C1 C2 D8; MIR L36: C1 C16 D8 | **NOT charged off** |
| 6 | 42 | **false** | repayments L39, L40, L43: C1 C2 D8 | **NOT charged off** |
| 7 | 48 | **false** | repayments L46, L49: C1 C2 D8 | **NOT charged off** |
| 8 | 53 | true | repayment L61: C11 D8 | charged off — agrees |
| 13 | 334 | true | repayment L335: C11 D8 (L319, L321, L329 precede 334: portfolio shapes) | charged off — agrees |

The charge-offs on loans 4-7 were UNDONE (latest read-back `chargedOff` false); the run counted them because the
`manuallyReversed` flag is not set on those chargeOff transactions in the earlier read-backs it used. The rule that
agrees with the ledger is the one in the brief: each loan's LATEST read-back. Same lesson as OH-TIERD17
(F-2026-09-11-tierd-chargeoff-branch-mislabel.md).

Loan 1 L5 (and L12, L19 on loans 2 and 3) is the one exception to the latest-state rule: it was posted in the
charged-off shape (C12 C20 C16 D8) and then reversed in full (D12 D20 D16 C8) when its charge-off was undone. Grade
from the ledger shape, not from either rule, when a transaction carries its own reversal legs.

## Unmatched legs
383 legs (the run says 370) match no read-back transaction: 189 on loan 10 and 188 on loan 9 are daily interest
accruals (D2 receivable / C5 income, one pair per day from 15 May 2025), whose transactions no read-back lists; 6 on
loan 12. None is a merchant refund or a repayment.
