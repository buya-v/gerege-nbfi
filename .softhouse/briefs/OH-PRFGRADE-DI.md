# OH-PRFGRADE-DI — grade PAYOUT REFUNDS on loans NOT charged off, on the EXISTING repayment seam. NO NEW PORT. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-prfgrade` (branch `feat/OHPRFGRADEDI`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow — READ THIS FIRST
A payout refund on a loan NOT charged off posts through the SAME method as an ordinary repayment:
`isRepaymentType()` includes `isPayoutRefund()` [`fineract-loan/.../LoanTransactionType.java:193-196`], the dispatch
sends every repayment type to `createJournalEntriesForRepayments` [`AccrualBasedAccountingProcessorForLoan.java:87-90`],
and for a loan not charged off that calls `createJournalEntriesForLoanRepayments` [:1369-1376] — already ported as
`CreateRepaymentJournalEntryLegs` and graded on seam `loan-repayment-journal-entries` (repayments `LN-TD-RP-*`, merchant
refunds `LN-TD-MIR-*`, OH-MIRNCO-DD). (Java under `/Users/buv/fineract`, read-only, pinned 426a23544.)

**So you write NO port code and NO harness code.** You add three VECTORS on the existing seam and widen the capability
text to name payout refunds too [:87-90, :193-196]. Template: copy `.softhouse/vectors/loan/LN-TD-MIR-loan-1-merged-receivable.json`
for shape. Read nothing else in the harness. If the seam refuses a vector, that is a finding — record it and stop.
**No new drive:** the non-charged-off payout posting is identical to a merchant refund's, so no wrong port separates them
from the existing vectors. Instead REPORT the three existing repayment drives' kill counts WITHOUT and WITH your vectors
(`bash .softhouse/briefs/tools/kills.sh loan <drive> <worktree>` for `loan-wrong-repayment-journal-one-debit-per-portion`,
`loan-wrong-repayment-omits-principal`, `loan-wrong-repayment-credits-not-merged`) — none may drop.

**Order of work — commit after each:** (1) vector 1 passing; (2) the other two + the capability text + the measurements.
**Git:** every commit as `git commit -F <file> </dev/null`, message file inside the worktree, deleted after. Do NOT
create or edit `AGENTS.md` or any file outside the loan context.

## The property (one)
Credits merged by GL account in slot order (principal → LOAN_PORTFOLIO, interest → INTEREST_RECEIVABLE, fee →
FEES_RECEIVABLE, penalty → PENALTIES_RECEIVABLE, overpayment → OVERPAYMENT), then ONE debit of the total to the RESOLVED
fund source. These refunds use paymentType 11; the product's channel mapping covers only paymentType 1 (→ 17), so the
fund source resolves to the product's `fundSourceAccountId` 8 — state that in each vector's provenance.

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/emi-calculation-p2-mnt/`, product
LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_FULL
(`product-mappings/create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_FULL.json`,
5eb39f95…9c5a): loanPortfolio 1, receivableInterest/Fee/Penalty 5, overpayment 15, fundSource 8, channel paymentType 1 →
17. Portions from the payoutRefund transaction in the loan read-back; legs from the SWEEP (that `transactionId`, `id`
order, account = `glAccountId`). Every loan is chargedOff false (latest read-back), fraud false; the payout refund is not
reversed.

| vector | loan read-back (sha256) | sweep (sha256) | tx | portions → legs |
| --- | --- | --- | --- | --- |
| LN-TD-PRF-loan-26-principal-interest-overpayment | `loans/loan-26/loan-26-detail-associations-transactions-6.json` (a1132b53…2108) | `journalentries-sweep/loan-26.json` (a0b7702a…41f2) | L215 | principal 753.25, interest 1.63, overpayment 245.12 → C1 753.25, C5 1.63, C15 245.12, D8 1000.00 |
| LN-TD-PRF-loan-28-principal-interest | `loans/loan-28/loan-28-detail-associations-transactions-4.json` (ea57e687…8b4c) | `journalentries-sweep/loan-28.json` (0a244295…b437) | L226 | principal 994.93, interest 5.07 → C1 994.93, C5 5.07, D8 1000.00 |
| LN-TD-PRF-loan-34-overpayment | `loans/loan-34/loan-34-detail-associations-transactions-10.json` (ca27bb6c…681b) | `journalentries-sweep/loan-34.json` (b3976cb7…f3f1) | L270 | overpayment 500.00 → C15 500.00, D8 500.00 |

Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
Three vectors, the widened capability text, the three existing drives' counts without/with. `capcount.sh <worktree> loan
loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. Never commit TASK.md.
