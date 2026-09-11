# OH-IPWGRADE-CT — port + grade the loan INTEREST-PAYMENT-WAIVER journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-ipwgrade` (branch `feat/OHIPWGRADECT`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Eleven sibling runs did this shape by COPYING a merged seam. **Read only what is listed. Start writing within 20
iterations. Commit after the first vector passes.** The host is under heavy memory pressure: if the bar trips a
guard-cost CEILING, say so in the commit message and do not loop re-running it — the driver re-runs it.

## The property (one)
`createJournalEntriesForInterestPaymentWaiverOrInterestRefund` [`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:793-889`,
read-only, pinned 426a23544] for transaction type INTEREST_PAYMENT_WAIVER (the interest-refund arm shares the method but is
NOT graded here). Through GLAccountBalanceHolder (merge by account; credits posted first in insertion order, then debits):
* loan NOT charged off: principal → CREDIT LOAN_PORTFOLIO; interest → INTEREST_RECEIVABLE; fees → FEES_RECEIVABLE;
  penalties → PENALTIES_RECEIVABLE; overpayment → OVERPAYMENT; every portion DEBITS INTEREST_ON_LOANS;
* loan CHARGED OFF: principal, interest, fees AND penalties all → CREDIT INCOME_FROM_CHARGE_OFF_INTEREST; overpayment →
  OVERPAYMENT; every portion DEBITS INTEREST_ON_LOANS.
Port the whole method for the waiver type.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/chargeoffjournal.go` (`CreateChargeOffJournalEntryLegs` — read it whole: same
GLAccountBalanceHolder merge, credits then debits). New file `nexus/internal/apps/loan/interestpaymentwaiverjournal.go`:
`CreateInterestPaymentWaiverJournalEntryLegs(transactionID string, portions RepaymentPortions, chargedOff bool, mapping InterestPaymentWaiverAccountMapping) ([]JournalEntryLeg, error)`.
Integer minor units only; refuse a negative portion or a positive portion with no account.

## The seam you add — copy the CHARGE-OFF journal seam line for line
Its exact entry points are generated in `.softhouse/maps/loan.md` § "Seam entry points", row
`loan-chargeoff-journal-entries`, and its drive in § "Drives registered", row `loan-wrong-chargeoff-journal-ignores-fraud`.
Read ONLY those two rows of the map. Add `SeamLoanInterestPaymentWaiverJournalEntries = "loan-interest-payment-waiver-journal-entries"`,
the twins, and ONE drive `loan-wrong-ipw-ignores-charge-off` (always the not-charged-off accounts). Capability:
`.softhouse/capabilities-loan.json` → `interest-payment-waiver-journal-entry`, `in_graded_domain: true`. Vector to copy for
shape + provenance: `.softhouse/vectors/loan/LN-TD-CO-loan-7-chargeoff-merged-legs.json`.

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Under `.softhouse/capture/tierd-feasibility/interest-payment-waiver-mnt/` (read its OWNER.md, ~60 lines). Portions from the loan read-back (the interestPaymentWaiver transaction's
`principalPortion`/`interestPortion`/`feeChargesPortion`/`penaltyChargesPortion`/`overpaymentPortion`), the charged-off
state from the loan's LATEST read-back; legs from the SWEEP `journalentries-sweep/loan-<id>.json` (that `transactionId`,
`id` order, accounts = `glAccountId`); accounts from `product-mappings/create-request-<product>.json` (sha256 in its
manifest.json): loanPortfolio 2, receivable interest/fee/penalty 4, overpayment 17, interestOnLoan 9,
incomeFromChargeOffInterest 20 — both products agree (LP1_INTEREST_FLAT af7c2cde…f13d;
LP2_ADV_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OF_ACCRUAL 8e8b8d5a…28a1).
| vector | loan read-back (sha256) | sweep (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-IPW-loan-2-principal-interest-fee | `loans/loan-2/loan-2-detail-associations-transactions-2.json` (908f8899…a916) | `journalentries-sweep/loan-2.json` (e59582c4…c5cc) | L4 | P10 I10 F20: C2 10, C4 30 (interest + fee merged), D9 40 |
| LN-TD-IPW-loan-7-principal-interest-overpayment | `loans/loan-7/loan-7-detail-associations-transactions-2.json` (420dddf8…ef12) | `journalentries-sweep/loan-7.json` (0b63ccaf…b2af) | L23 | P1000 I40 O60: C2, C4, C17, D9 1100 |
| LN-TD-IPW-loan-11-chargedoff | `loans/loan-11/loan-11-detail-associations-transactions-5.json` (d3bc4ec6…9f18) | `journalentries-sweep/loan-11.json` (41b89590…a241) | L42 | CHARGED OFF, P250 I10: ONE C20 260 (merged), D9 260 |
| LN-TD-IPW-loan-13-chargedoff-principal | `loans/loan-13/loan-13-detail-associations-transactions-31.json` (cb3bf529…dd84) | `journalentries-sweep/loan-13.json` (8e0d4434…9a9c) | L76 | CHARGED OFF, P46.56: C20 4656, D9 4656 (other product) |
Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, four vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-ipw-ignores-charge-off <worktree>`: ≥1 with, 0 without). Coverage of
the port from the committed-store test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
