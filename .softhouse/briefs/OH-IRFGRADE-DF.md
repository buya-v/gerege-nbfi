# OH-IRFGRADE-DF — grade INTEREST REFUNDS on the EXISTING interest-payment-waiver seam. NO NEW PORT. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-irfgrade` (branch `feat/OHIRFGRADEDF`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow — READ THIS FIRST
The Java posts an interest refund through the SAME method as an interest-payment waiver: the dispatch sends
`isInterestPaymentWaiver() || isInterestRefund()` to `createJournalEntriesForInterestPaymentWaiverOrInterestRefund`
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:134-135`,
body :793-880, read-only, pinned 426a23544] — already ported as `CreateInterestPaymentWaiverJournalEntryLegs`
(`nexus/internal/apps/loan/interestpaymentwaiverjournal.go`) and graded on seam
`loan-interest-payment-waiver-journal-entries` with four WAIVER vectors (`LN-TD-IPW-*`). The seam request carries no
transaction type (`transaction_id`, `portions`, `charged_off`, `accounts`), so an interest-refund vector fits unchanged.

**So you write NO port code.** You add four VECTORS on the existing seam, widen the capability
`interest-payment-waiver-journal-entry` text to "interest-payment waivers AND interest refunds [:134-135]", and add ONE
drive. Template: copy `.softhouse/vectors/loan/LN-TD-IPW-loan-2-principal-interest-fee.json` for shape; for the drive,
copy how `loan-wrong-ipw-ignores-charge-off` is registered (`impl.go`, grep the name). Read nothing else in the harness.

**Order of work — commit after each:** (1) vector 1 passing; (2) the other three; (3) the drive + measurements +
capability text. If you are past 150 events with nothing committed, commit what passes and continue.

## The property (one)
Not charged off: principal → LOAN_PORTFOLIO, interest → INTEREST_RECEIVABLE, fee → FEES_RECEIVABLE, penalty →
PENALTIES_RECEIVABLE, overpayment → OVERPAYMENT; charged off: principal, interest, fee, penalty →
INCOME_FROM_CHARGE_OFF_INTEREST, overpayment → OVERPAYMENT. Every slot's debit goes to INTEREST_ON_LOANS; credits and
debits each MERGE by GL account (GLAccountBalanceHolder, a LinkedHashMap), credits first, then debits.
**New for this seam:** loan 3 L33 is CHARGED OFF with principal 41.76 AND interest 0.15 — both credit
INCOME_FROM_CHARGE_OFF_INTEREST 17, so they MERGE into ONE credit C17 41.91 (and one debit D9 41.91).

## The drive (one)
`loan-wrong-ipw-charged-off-credits-not-merged`: in the CHARGED-OFF arm, posts one credit per positive slot instead of
merging slots that resolve to the same account (the debits stay the oracle's). Measure WITHOUT and WITH your vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-ipw-charged-off-credits-not-merged <worktree>`: ≥1 with, 0
without). If it already kills without your vectors, say so — that is a finding, not a failure. Also report
`loan-wrong-ipw-ignores-charge-off` with your vectors (must not drop).

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/merchant-refund-mnt/`. Portions from the interestRefund transaction in
the loan read-back; legs from the SWEEP `journalentries-sweep/loan-<id>.json` (that `transactionId`, `id` order, account =
`glAccountId`); accounts from `product-mappings/create-request-<product>.json` (sha256 in `product-mappings/manifest.json`):
loanPortfolio 7, receivableInterest/Fee/Penalty 4, overpayment 16, interestOnLoan 9, incomeFromChargeOffInterest 17 (the
same in all three products). Charged-off state from the loan's LATEST read-back: loans 5, 14, 15 `chargedOff` false;
loan 3 `chargedOff` true with chargeOff transaction 31 before L33. Pick transactions whose legs carry NO reversal pair.

| vector | loan read-back (sha256) | sweep (sha256) | tx | portions → legs | product (sha256) |
| --- | --- | --- | --- | --- | --- |
| LN-TD-IRF-loan-5-interest | `loans/loan-5/loan-5-detail-associations-transactions-5.json` (dee1b350…a6a9) | `journalentries-sweep/loan-5.json` (32431641…4786) | L39 | interest 0.19 → C4 0.19, D9 0.19 | LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL (53246a7b…ed15) |
| LN-TD-IRF-loan-14-overpayment | `loans/loan-14/loan-14-detail-associations-transactions-5.json` (6b4e50d3…930e) | `journalentries-sweep/loan-14.json` (9ef03751…a0c4) | L73 | overpayment 17.07 → C16 17.07, D9 17.07 | same as loan 5 |
| LN-TD-IRF-loan-15-principal | `loans/loan-15/loan-15-detail-associations-transactions-13.json` (46600b5c…4a83) | `journalentries-sweep/loan-15.json` (75b26ef9…cb7c) | L87 | principal 1.46 → C7 1.46, D9 1.46 | LP2_ADV_PMT_ALLOC_ACTUAL_ACTUAL_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL (d55b8ed2…ad20) |
| LN-TD-IRF-loan-3-chargedoff-merged | `loans/loan-3/loan-3-detail-associations-transactions-4.json` (673010a7…3fcc) | `journalentries-sweep/loan-3.json` (41f7cd91…c52e) | L33 | CHARGED OFF, principal 41.76 + interest 0.15 → **ONE C17 41.91**, D9 41.91 | LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF (bade51ab…9b43) |

Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
Four vectors, the widened capability text, the one drive, its with/without measurement, the existing drive's count.
`capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
