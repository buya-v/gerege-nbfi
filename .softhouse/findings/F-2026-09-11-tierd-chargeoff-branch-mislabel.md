# F-2026-09-11 — the ChargeOff capture reached the charge-off POSTING, not the charged-off WRITE-OFF

**Found by:** the driver, re-reading `tierd-feasibility/chargeoff-mnt/` after merging OH-TIERD8-BW
(merge `77697e49`).  **Severity:** a false coverage claim, corrected before anything was graded on it.

## What was claimed
The run's commit ("capture the charge-off write-off GL branch"), the capture's OWNER.md and the
driver's own merge message all said the replay exercised
`createJournalEntriesForWriteOffsWhenLoanIsChargedOff`
[AccrualBasedAccountingProcessorForLoan.java:1616].  The driver repeated the claim without
checking which transaction types the legs belong to.

## What the capture holds
Joining every `/journalentries` leg to its transaction (`transactionId` → the loan read-backs
under `loans/`):

| transaction type | legs | loans | Java branch |
| --- | --- | --- | --- |
| chargeOff | 118 | 30 | `createJournalEntriesForChargeOff` :890 |
| disbursement | 66 | 32 | — |
| repayment | 37 | 12 | incl. `createJournalEntriesForRepaymentWhenLoanIsChargedOff` :1388 (5 credit `Recoveries`) |
| merchantIssuedRefund / payoutRefund | 19 | 5 | — |

No `writeOff` transaction appears in any read-back (types seen: disbursement 50, chargeOff 59,
accrual 70, repayment 25, downPayment 7, merchantIssuedRefund 3, payoutRefund 2,
accrualActivity 2, goodwillCredit 2).  **The charged-off write-off branch (:1616) is still
UNOBSERVED.**  `LoanChargeOff-Part1.feature` never writes a loan off.

## What it does give us (new)
The charge-off posting is observed for the first time, discriminatingly:
* fraud vs non-fraud expense (`Credit Loss/Bad Debt-Fraud` 13 vs `Credit Loss/Bad Debt` 14);
* the GLAccountBalanceHolder merge — interest (30), fee (103) and penalty (10) receivables all
  map to account 10 and post ONE credit of 143; fee and penalty charge-off income both map to
  account 11 and post ONE debit of 113 (loan 7, `L19`);
* order: every credit (insertion order) before every debit (insertion order);
* a reversed charge-off (loan 20, `L64`) appending the mirror legs.
The product accounting mappings those legs resolve through are now committed as observed
bodies under `chargeoff-mnt/product-mappings/` (the oracle's `retrieveOneLoanProduct` echo plus
the accepted create requests for LP1 and LP1_INTEREST_FLAT; ids agree).

## Corrected
OWNER.md (top correction note, evidence section, failures section), `owner.py` and
`extract-journalentries.py` text.  No hash-manifested body changed.

## Lesson
A branch claim is verified by the TRANSACTION TYPE of the legs, not by the GL account names
("Credit Loss/Bad Debt" is the charge-off expense AND a plausible write-off account).  The
driver's review now checks the type join before repeating a branch claim in a merge message.
