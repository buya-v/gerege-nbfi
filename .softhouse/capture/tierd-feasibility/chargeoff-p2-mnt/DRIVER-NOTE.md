# Driver note — BACKDATED repayments: charged-off state follows transaction DATE, not transaction id

Written by the driver at merge time (12 Sep 2026). The capture bodies, manifests and teardown are sound. Only the
charged-off classification of three repayments is corrected here, and with it the rule every capture brief has used.

## What the run (and the driver's own re-join) claimed
Repayments on charged-off loans: 17 legs on loans 1, 12, 14, 28, 30, 37, 39. The rule was: a leg is charged off when the
loan's LATEST read-back lists a lower-id chargeOff and `chargedOff` is true.

## What the ledger shows

| loan | charge-off (latest read-back) | repayment | legs (sweep, glAccountName) | posted as |
| --- | --- | --- | --- | --- |
| 12 | 127, dated 2024-03-31 (125 replaced) | L128, dated **2024-03-01** | C5 Loans Receivable 16.52, C1 Interest/Fee Receivable 0.49, D6 Suspense/Clearing 17.01 | **NOT charged off** |
| 28 | 205, dated 2024-03-31 (204 replaced) | L207, dated **2024-03-01** | C5 16.52, C1 0.49, D6 17.01 | **NOT charged off** |
| 37 | 250, dated 2024-03-31 (249 replaced) | L251, dated **2024-03-01** | C5 16.52, C1 0.49, D6 17.01 | **NOT charged off** |
| 1 | 3, dated 2024-02-28 | L4, dated 2024-02-28 (same day, later id) | C15 Recoveries 500.00, D6 500.00 | charged off (recovery) |
| 30 | 217, dated 2024-02-29 | L218, dated 2024-03-01 | C15 Recoveries 17.01, D6 17.01 | charged off (recovery) |

Loans 14 and 39 carry the same recovery shape (C15 D6), after the charge-off date.

These are "Charge-off with backdated repayment" scenarios. The repayment is entered AFTER the charge-off (a higher id),
but it is dated BEFORE it. Fineract replays the loan in date order: it replaces the charge-off (125 → 127, 204 → 205,
249 → 250) and posts the backdated repayment in the portfolio shape. **Correct rule:** a transaction is on a charged-off
loan when a non-undone charge-off in the loan's LATEST read-back has an EARLIER transaction date, or the same date and a
lower id. Under that rule, charged-off repayments here are 8 legs on loans 1, 14, 30 and 39 (the recovery shape C15 D6).
The 9 legs on loans 12, 28 and 37 are ordinary repayments.

The accrual on loan 13 (D1 C7) and the accrual adjustment on loan 28 (D7 C1) labelled charged-off are NOT re-verified here
by ledger shape. Do not grade a charged-off accrual from them without checking their dates.

## Unmatched legs
180 legs match no read-back transaction (the run says 152 "unmapped"): mostly daily interest accruals (D1 Interest/Fee
Receivable 78, C7 Interest Income 76), plus the legs of charge-offs that were later replaced and no longer appear in any
read-back (e.g. D13 Credit Loss/Bad Debt, D19 Interest Income Charge Off). None is a repayment.
